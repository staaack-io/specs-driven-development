#!/usr/bin/env python3
"""Deterministic state, scope and transaction guard for Hermes SDD jobs.

The module deliberately contains no LLM or Hermes API calls.  Skills call these
primitives before and after delegated work so correctness does not depend on a
prompt being followed.  Repository-wide coordination lives in the Git common
directory, which is shared by every worktree.
"""

from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
import copy
import ctypes
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
import time
from typing import Iterator, Mapping, Sequence


STATE_SCHEMA_VERSION = 2
MAX_WORKERS = 2
TASK_ID = re.compile(r"^T-[0-9]{3}$")
TEST_ID = re.compile(r"^(T-[0-9]{3})-T[1-9][0-9]*$")
TASK_HEADER = re.compile(r"^###\s+(T-[0-9]{3})(?:\s*[:—-].*)?\s*$")
FEATURE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
EVENT_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
BRANCH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,199}$")
GLOB_CHARACTERS = frozenset("*?[]{}")
FORBIDDEN_STATE_KEY_PARTS = (
    "absolute_path",
    "credential",
    "password",
    "secret",
    "token",
    "transcript",
)
SECRET_VALUE_PATTERNS = (
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]{20,}=*"),
)
FORBIDDEN_COMMAND_ARGUMENTS = frozenset(
    {
        "--no-verify",
        "--yolo",
        "-DskipTests",
        "-DskipTests=true",
        "-Dpit.skip",
        "-Dpit.skip=true",
        "-Dcheckstyle.skip",
        "-Dcheckstyle.skip=true",
        "-Dspotbugs.skip",
        "-Dspotbugs.skip=true",
    }
)
SHARED_ARTIFACTS = frozenset(
    {"04-tasks.md", ".tdd-state.json", "05-implementation-log.md"}
)
PHASES = frozenset(
    {"pending", "red", "green", "refactor", "simplify", "done", "blocked"}
)
STATUSES = frozenset(
    {
        "pending",
        "ready",
        "in_progress",
        "blocked",
        "needs_input",
        "awaiting_go",
        "failed",
        "done",
    }
)


class GuardError(RuntimeError):
    """A deterministic contract or safety check failed."""


class InjectedCrash(RuntimeError):
    """Test-only interruption after a durable transaction boundary."""


class DarwinBsdInfo(ctypes.Structure):
    """Prefix-complete proc_bsdinfo layout through process birth time."""

    _fields_ = [
        ("pbi_flags", ctypes.c_uint32),
        ("pbi_status", ctypes.c_uint32),
        ("pbi_xstatus", ctypes.c_uint32),
        ("pbi_pid", ctypes.c_uint32),
        ("pbi_ppid", ctypes.c_uint32),
        ("pbi_uid", ctypes.c_uint32),
        ("pbi_gid", ctypes.c_uint32),
        ("pbi_ruid", ctypes.c_uint32),
        ("pbi_rgid", ctypes.c_uint32),
        ("pbi_svuid", ctypes.c_uint32),
        ("pbi_svgid", ctypes.c_uint32),
        ("rfu_1", ctypes.c_uint32),
        ("pbi_comm", ctypes.c_char * 16),
        ("pbi_name", ctypes.c_char * 32),
        ("pbi_nfiles", ctypes.c_uint32),
        ("pbi_pgid", ctypes.c_uint32),
        ("pbi_pjobc", ctypes.c_uint32),
        ("e_tdev", ctypes.c_uint32),
        ("e_tpgid", ctypes.c_uint32),
        ("pbi_nice", ctypes.c_int32),
        ("pbi_start_tvsec", ctypes.c_uint64),
        ("pbi_start_tvusec", ctypes.c_uint64),
    ]


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def token_for(data: bytes | None) -> str:
    if data is None:
        return "absent"
    return "sha256:" + hashlib.sha256(data).hexdigest()


def read_bytes(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_replace(path: Path, data: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def remove_durably(path: Path) -> None:
    path.unlink(missing_ok=True)
    fsync_directory(path.parent)


def _run_git(repo_root: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *arguments],
        check=False,
        capture_output=True,
    )
    if result.returncode:
        detail = os.fsdecode(result.stderr).strip() or "git command failed"
        raise GuardError(detail)
    return result.stdout


def repository_root(path: Path | str) -> Path:
    supplied = Path(path)
    output = _run_git(supplied, "rev-parse", "--show-toplevel")
    root = Path(os.fsdecode(output).strip())
    if not root.is_absolute():
        root = supplied / root
    if root.is_symlink():
        raise GuardError(f"repository root is a symlink: {root}")
    return root.resolve(strict=True)


def git_common_dir(path: Path | str) -> Path:
    root = repository_root(path)
    output = _run_git(root, "rev-parse", "--git-common-dir")
    common = Path(os.fsdecode(output).strip())
    if not common.is_absolute():
        common = root / common
    common = common.resolve(strict=True)
    if not common.is_dir():
        raise GuardError(f"Git common directory is invalid: {common}")
    return common


def git_head(path: Path | str) -> str:
    root = repository_root(path)
    head = os.fsdecode(_run_git(root, "rev-parse", "HEAD")).strip()
    if re.fullmatch(r"[0-9a-f]{40,64}", head) is None:
        raise GuardError("Git HEAD is not a full object ID")
    return head


def ensure_directory_chain(base: Path, *parts: str) -> Path:
    current = base
    for part in parts:
        if part in {"", ".", ".."} or "/" in part:
            raise GuardError(f"unsafe runtime directory component: {part!r}")
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            current.mkdir(mode=0o700)
            fsync_directory(current.parent)
            metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise GuardError(f"runtime directory chain is unsafe: {current}")
    return current


def worktree_identity(path: Path | str) -> dict[str, str]:
    root = repository_root(path)
    common = git_common_dir(root)
    return {
        "repository_id": hashlib.sha256(os.fsencode(common)).hexdigest()[:24],
        "worktree_id": hashlib.sha256(os.fsencode(root)).hexdigest()[:24],
        "head": git_head(root),
    }


def runtime_directory(repo_root: Path | str) -> Path:
    return ensure_directory_chain(git_common_dir(repo_root), "sdd-runtime")


def worktree_runtime_directory(repo_root: Path | str) -> tuple[Path, dict[str, str]]:
    root = repository_root(repo_root)
    identity = worktree_identity(root)
    directory = ensure_directory_chain(
        runtime_directory(root), "worktrees", identity["worktree_id"]
    )
    return directory, identity


@contextmanager
def global_lock(repo_root: Path | str, *, blocking: bool = True) -> Iterator[None]:
    lock_path = runtime_directory(repo_root) / "writer.lock"
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(lock_path, flags, 0o600)
    except OSError as error:
        raise GuardError(f"cannot open repository writer lock: {error}") from error
    locked = False
    try:
        mode = os.fstat(descriptor).st_mode
        if not stat.S_ISREG(mode):
            raise GuardError(f"repository writer lock is not regular: {lock_path}")
        operation = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
        try:
            fcntl.flock(descriptor, operation)
        except BlockingIOError as error:
            raise GuardError("another SDD writer holds the repository lock") from error
        locked = True
        yield
    finally:
        try:
            if locked:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _validate_identifier(value: object, pattern: re.Pattern[str], label: str) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise GuardError(f"invalid {label}: {value!r}")
    return value


def normalize_scope_path(value: object) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise GuardError(f"scope path must be a non-empty normalized string: {value!r}")
    if "\x00" in value or "\\" in value:
        raise GuardError(f"ambiguous scope path refused: {value!r}")
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise GuardError(f"absolute scope path refused: {value}")
    if value.endswith("/") or any(character in value for character in GLOB_CHARACTERS):
        raise GuardError(f"glob or directory scope refused: {value}")
    path = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise GuardError(f"non-canonical scope path refused: {value}")
    normalized = path.as_posix()
    if normalized != value:
        raise GuardError(f"non-canonical scope path refused: {value}")
    if normalized == ".git" or normalized.startswith(".git/"):
        raise GuardError(f"Git metadata cannot be in scope: {value}")
    return normalized


def validate_scope_path(repo_root: Path | str, value: object) -> str:
    relative = normalize_scope_path(value)
    root = repository_root(repo_root)
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(metadata.st_mode):
            raise GuardError(f"symlink chain refused in scope: {relative}")
        if current == root / relative and stat.S_ISDIR(metadata.st_mode):
            raise GuardError(f"directory scope refused: {relative}")
    try:
        current.resolve(strict=False).relative_to(root)
    except (OSError, ValueError) as error:
        raise GuardError(f"scope path escapes repository: {relative}") from error
    return relative


def paths_overlap(left: str, right: str) -> bool:
    left_path = PurePosixPath(left)
    right_path = PurePosixPath(right)
    return left_path == right_path or left_path in right_path.parents or right_path in left_path.parents


def _assert_no_forbidden_state_fields(value: object, location: str = "state") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise GuardError(f"{location} contains a non-string key")
            lowered = key.lower().replace("-", "_")
            if any(part in lowered for part in FORBIDDEN_STATE_KEY_PARTS):
                raise GuardError(f"forbidden state field {location}.{key}")
            _assert_no_forbidden_state_fields(nested, f"{location}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _assert_no_forbidden_state_fields(nested, f"{location}[{index}]")
    elif isinstance(value, str) and any(
        pattern.search(value) for pattern in SECRET_VALUE_PATTERNS
    ):
        raise GuardError(f"secret-like value refused at {location}")


def validate_command_arguments(arguments: Sequence[str]) -> list[str]:
    """Validate an already-tokenized command; never parse a shell string."""

    if isinstance(arguments, (str, bytes)):
        raise GuardError("command arguments must be a structured string list")
    validated: list[str] = []
    for argument in arguments:
        if not isinstance(argument, str) or "\x00" in argument:
            raise GuardError("command arguments must be NUL-free strings")
        normalized = argument.strip().lower()
        forbidden = {value.lower() for value in FORBIDDEN_COMMAND_ARGUMENTS}
        property_name, separator, property_value = normalized.partition("=")
        bypass_property = property_name in {
            "-dskiptests",
            "-dskip.tests",
            "-dmaven.test.skip",
            "-dpit.skip",
            "-dcheckstyle.skip",
            "-dspotbugs.skip",
        } and (not separator or property_value not in {"false", "0", "no"})
        if normalized in forbidden or normalized.startswith("--no-verify=") or bypass_property:
            raise GuardError(f"test or safety bypass argument refused: {argument}")
        validated.append(argument)
    return validated


def open_question_ids(markdown: str) -> list[str]:
    """Return Q-IDs in the exact Open Questions section of an artifact."""

    in_section = False
    found_section = False
    result: list[str] = []
    for line in markdown.splitlines():
        if re.match(r"^##\s+Open Questions\s*$", line, flags=re.IGNORECASE):
            in_section = True
            found_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            result.extend(re.findall(r"\bQ-[0-9]{3}\b", line))
    if not found_section:
        raise GuardError("required Open Questions section is missing")
    return sorted(set(result))


def assert_no_open_questions(artifacts: Mapping[str, str]) -> None:
    open_by_artifact = {
        name: open_question_ids(markdown)
        for name, markdown in artifacts.items()
    }
    blocked = [
        f"{name}: {', '.join(question_ids)}"
        for name, question_ids in open_by_artifact.items()
        if question_ids
    ]
    if blocked:
        raise GuardError("open questions block phase transition; " + "; ".join(blocked))


def validate_red_gate(
    state: object,
    *,
    task_id: str,
    changed_paths: Sequence[str],
    production_paths: Sequence[str],
    repo_root: Path | str | None = None,
) -> None:
    """Require durable RED proof before an explicitly classified production edit."""

    validated = validate_state(state, repo_root=repo_root)
    migration = validated.get("migration")
    if isinstance(migration, dict) and not migration.get("contract_complete"):
        raise GuardError("incomplete migrated state cannot pass the RED/build gate")
    _validate_identifier(task_id, TASK_ID, "task ID")
    tasks = validated["tasks"]
    assert isinstance(tasks, dict)
    task = tasks.get(task_id)
    if not isinstance(task, dict):
        raise GuardError(f"unknown active task: {task_id}")
    if validated.get("active_task") != task_id:
        raise GuardError(f"task {task_id} is not the active task")
    changes = {normalize_scope_path(path) for path in changed_paths}
    production = {normalize_scope_path(path) for path in production_paths}
    if not changes <= set(task.get("files_in_scope", [])):
        raise GuardError("RED gate received a changed path outside task scope")
    if not changes & production:
        return
    if task.get("phase") not in {"red", "green", "refactor", "simplify"}:
        raise GuardError("production edit requires a completed RED transition")
    for field in ("red_at", "red_test_signature", "red_failure_excerpt"):
        value = task.get(field)
        if not isinstance(value, str) or not value.strip():
            raise GuardError(f"production edit requires non-empty {field}")


def migrate_state_v1(state: Mapping[str, object]) -> dict[str, object]:
    """Return an additive v2 representation without mutating a legacy state."""

    if state.get("schema_version", 1) != 1:
        raise GuardError("only schema v1 can be migrated")
    tasks = state.get("tasks")
    if not isinstance(tasks, dict) or not tasks:
        raise GuardError("legacy state must contain at least one task")
    migrated: dict[str, object] = {
        "schema_version": STATE_SCHEMA_VERSION,
        "feature_id": copy.deepcopy(state.get("feature_id")),
        "mode": "sequential",
        "project": None,
        "board": None,
        "max_workers": 1,
        "revision": 0,
        "active_task": copy.deepcopy(state.get("active_task")),
        "tasks": copy.deepcopy(tasks),
    }
    migrated["migration"] = {"from_schema_version": 1, "contract_complete": False}
    for task in migrated["tasks"].values():  # type: ignore[union-attr]
        if not isinstance(task, dict):
            raise GuardError("legacy state contains a non-object task")
        legacy_phase = task.get("phase")
        legacy_status = {
            "pending": "pending",
            "red": "in_progress",
            "green": "in_progress",
            "refactor": "in_progress",
            "simplify": "in_progress",
            "done": "done",
            "blocked": "blocked",
        }.get(legacy_phase, "pending")
        task.setdefault("status", legacy_status)
        task.setdefault("dependencies", [])
        task.setdefault("test_ids", [])
        task.setdefault("kanban_id", None)
        task.setdefault("issue", None)
        task.setdefault("branch", None)
        task.setdefault("pr", None)
        allowed_legacy_task_fields = {
            "phase",
            "red_at",
            "red_test_signature",
            "red_failure_excerpt",
            "green_at",
            "files_in_scope",
            "status",
            "dependencies",
            "test_ids",
            "kanban_id",
            "issue",
            "branch",
            "pr",
        }
        for field in set(task) - allowed_legacy_task_fields:
            del task[field]
    return migrated


def _validate_optional_slug(value: object, label: str) -> None:
    if value is not None and (not isinstance(value, str) or SLUG.fullmatch(value) is None):
        raise GuardError(f"invalid {label}: {value!r}")


def _validate_optional_branch(value: object, label: str) -> None:
    if value is None:
        return
    if not isinstance(value, str) or BRANCH.fullmatch(value) is None:
        raise GuardError(f"invalid {label}: {value!r}")
    if value.endswith("/") or "//" in value or any(
        part in {"", ".", ".."} for part in value.split("/")
    ):
        raise GuardError(f"branch traversal or empty segment refused: {value!r}")


def _validate_task_metadata(task_id: str, task: dict[str, object]) -> None:
    if task.get("phase") not in PHASES:
        raise GuardError(f"task {task_id} has invalid phase")
    if task.get("status") not in STATUSES:
        raise GuardError(f"task {task_id} has invalid status")
    _validate_optional_slug(task.get("kanban_id"), f"{task_id}.kanban_id")
    _validate_optional_branch(task.get("branch"), f"{task_id}.branch")
    for field in ("issue", "pr"):
        value = task.get(field)
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value <= 0
        ):
            raise GuardError(f"{task_id}.{field} must be a positive integer or null")


def _dependency_reachability(tasks: Mapping[str, dict[str, object]]) -> dict[str, set[str]]:
    visiting: set[str] = set()
    complete: set[str] = set()
    ancestors: dict[str, set[str]] = {}

    def visit(task_id: str) -> set[str]:
        if task_id in visiting:
            raise GuardError(f"task dependency cycle includes {task_id}")
        if task_id in complete:
            return ancestors[task_id]
        visiting.add(task_id)
        result: set[str] = set()
        dependencies = tasks[task_id].get("dependencies")
        if not isinstance(dependencies, list) or any(
            not isinstance(dependency, str) for dependency in dependencies
        ):
            raise GuardError(f"task {task_id} dependencies must be a string list")
        if len(dependencies) != len(set(dependencies)):
            raise GuardError(f"task {task_id} has duplicate dependencies")
        for dependency in dependencies:
            if dependency not in tasks:
                raise GuardError(f"task {task_id} depends on unknown task {dependency}")
            if dependency == task_id:
                raise GuardError(f"task {task_id} depends on itself")
            result.add(dependency)
            result.update(visit(dependency))
        visiting.remove(task_id)
        complete.add(task_id)
        ancestors[task_id] = result
        return result

    for task_id in tasks:
        visit(task_id)
    return ancestors


def validate_state(
    state: object,
    *,
    repo_root: Path | str | None = None,
    allow_legacy: bool = True,
) -> dict[str, object]:
    if not isinstance(state, dict):
        raise GuardError("state must be an object")
    _assert_no_forbidden_state_fields(state)
    version = state.get("schema_version", 1)
    if version == 1:
        if not allow_legacy:
            raise GuardError("legacy schema v1 state requires migration")
        state = migrate_state_v1(state)
    elif version != STATE_SCHEMA_VERSION:
        raise GuardError(f"unsupported state schema version: {version!r}")
    else:
        state = copy.deepcopy(state)

    allowed_state_fields = {
        "schema_version",
        "feature_id",
        "mode",
        "project",
        "board",
        "max_workers",
        "revision",
        "active_task",
        "tasks",
        "migration",
    }
    unexpected_state_fields = set(state) - allowed_state_fields
    if unexpected_state_fields:
        raise GuardError(
            "state contains unsupported fields: "
            + ", ".join(sorted(unexpected_state_fields))
        )

    feature_id = _validate_identifier(state.get("feature_id"), FEATURE_ID, "feature_id")
    del feature_id
    mode = state.get("mode")
    if mode not in {"sequential", "parallel"}:
        raise GuardError("mode must be sequential or parallel")
    maximum = state.get("max_workers")
    if not isinstance(maximum, int) or isinstance(maximum, bool) or not 1 <= maximum <= MAX_WORKERS:
        raise GuardError(f"max_workers must be between 1 and {MAX_WORKERS}")
    if mode == "sequential" and maximum != 1:
        raise GuardError("sequential mode requires max_workers=1")
    revision = state.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise GuardError("revision must be a non-negative integer")
    _validate_optional_slug(state.get("project"), "project")
    _validate_optional_slug(state.get("board"), "board")

    tasks_value = state.get("tasks")
    if not isinstance(tasks_value, dict) or not tasks_value:
        raise GuardError("state must contain at least one task")
    tasks: dict[str, dict[str, object]] = {}
    for task_id, task_value in tasks_value.items():
        _validate_identifier(task_id, TASK_ID, "task ID")
        if not isinstance(task_value, dict):
            raise GuardError(f"task {task_id} must be an object")
        task = task_value
        allowed_task_fields = {
            "phase",
            "status",
            "dependencies",
            "test_ids",
            "files_in_scope",
            "kanban_id",
            "issue",
            "branch",
            "pr",
            "red_at",
            "red_test_signature",
            "red_failure_excerpt",
            "green_at",
        }
        unexpected_task_fields = set(task) - allowed_task_fields
        if unexpected_task_fields:
            raise GuardError(
                f"task {task_id} contains unsupported fields: "
                + ", ".join(sorted(unexpected_task_fields))
            )
        _validate_task_metadata(task_id, task)
        tasks[task_id] = task

    active_task = state.get("active_task")
    if active_task is not None and active_task not in tasks:
        raise GuardError("active_task must reference an existing task")

    ancestors = _dependency_reachability(tasks)
    migration = state.get("migration")
    legacy_incomplete = isinstance(migration, dict) and migration == {
        "from_schema_version": 1,
        "contract_complete": False,
    }
    if legacy_incomplete and (mode != "sequential" or maximum != 1):
        raise GuardError("incomplete v1 migration cannot enter parallel execution")
    all_test_ids: set[str] = set()
    normalized_scopes: dict[str, list[str]] = {}
    unique_metadata: dict[str, dict[object, str]] = {
        field: {} for field in ("kanban_id", "branch", "issue", "pr")
    }
    for task_id, task in tasks.items():
        tests = task.get("test_ids")
        if not isinstance(tests, list) or any(not isinstance(test, str) for test in tests):
            raise GuardError(f"task {task_id} test_ids must be a string list")
        if not tests and not legacy_incomplete:
            raise GuardError(f"task {task_id} must contain at least one Test-ID")
        for test_id in tests:
            match = TEST_ID.fullmatch(test_id)
            if match is None or match.group(1) != task_id:
                raise GuardError(f"invalid Test-ID {test_id!r} for task {task_id}")
            if test_id in all_test_ids:
                raise GuardError(f"duplicate Test-ID: {test_id}")
            all_test_ids.add(test_id)

        scope = task.get("files_in_scope")
        if not isinstance(scope, list) or any(not isinstance(path, str) for path in scope):
            raise GuardError(f"task {task_id} files_in_scope must be a string list")
        if not scope and not legacy_incomplete:
            raise GuardError(f"task {task_id} must contain at least one concrete scope file")
        normalized: list[str] = []
        for path in scope:
            checked = (
                validate_scope_path(repo_root, path)
                if repo_root is not None
                else normalize_scope_path(path)
            )
            if checked in normalized:
                raise GuardError(f"task {task_id} has duplicate scope path {checked}")
            normalized.append(checked)
        normalized_scopes[task_id] = normalized
        for field, seen in unique_metadata.items():
            value = task.get(field)
            if value is None:
                continue
            if value in seen:
                raise GuardError(
                    f"tasks {seen[value]} and {task_id} reuse {field} {value!r}"
                )
            seen[value] = task_id

        phase = task.get("phase")
        status = task.get("status")
        allowed_statuses = {
            "pending": {"pending", "ready", "blocked", "needs_input"},
            "red": {"in_progress"},
            "green": {"in_progress"},
            "refactor": {"in_progress"},
            "simplify": {"in_progress"},
            "done": {"done", "awaiting_go"},
            "blocked": {"blocked", "needs_input", "failed"},
        }
        if status not in allowed_statuses[phase]:
            raise GuardError(f"task {task_id} phase/status combination is inconsistent")
        red_fields = (
            task.get("red_at"),
            task.get("red_test_signature"),
            task.get("red_failure_excerpt"),
        )
        green_at = task.get("green_at")
        if phase == "pending" and any(value is not None for value in (*red_fields, green_at)):
            raise GuardError(f"pending task {task_id} cannot contain TDD proof")
        if phase in {"red", "green", "refactor", "simplify", "done"} and any(
            not isinstance(value, str) or not value.strip() for value in red_fields
        ):
            raise GuardError(f"task {task_id} phase {phase} requires complete RED proof")
        if phase == "red" and green_at is not None:
            raise GuardError(f"red task {task_id} cannot contain green_at")
        if phase in {"green", "refactor", "simplify", "done"} and (
            not isinstance(green_at, str) or not green_at.strip()
        ):
            raise GuardError(f"task {task_id} phase {phase} requires green_at")

    in_progress = {
        task_id for task_id, task in tasks.items() if task.get("status") == "in_progress"
    }
    if mode == "sequential" and len(in_progress) > 1:
        raise GuardError("sequential state cannot contain multiple in-progress tasks")
    if active_task is not None and active_task not in in_progress:
        raise GuardError("active_task must identify an in-progress task")
    if mode == "sequential" and in_progress and active_task not in in_progress:
        raise GuardError("sequential in-progress state requires active_task")

    task_ids = sorted(tasks)
    for index, left in enumerate(task_ids):
        for right in task_ids[index + 1 :]:
            conflicts = sorted(
                left_path
                for left_path in normalized_scopes[left]
                for right_path in normalized_scopes[right]
                if paths_overlap(left_path, right_path)
            )
            if conflicts and left not in ancestors[right] and right not in ancestors[left]:
                raise GuardError(
                    f"unordered tasks {left} and {right} have overlapping file scopes"
                )
    return state


def task_contract_from_markdown(markdown: str) -> dict[str, dict[str, list[str]]]:
    """Extract the machine contract from canonical 04-tasks Markdown."""

    lines = markdown.splitlines()
    headers: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = TASK_HEADER.fullmatch(line.strip())
        if match:
            task_id = match.group(1)
            if any(existing == task_id for _, existing in headers):
                raise GuardError(f"duplicate task heading in 04-tasks.md: {task_id}")
            headers.append((index, task_id))
    if not headers:
        raise GuardError("04-tasks.md contains no canonical task headings")

    result: dict[str, dict[str, list[str]]] = {}
    field_names = {
        "test-ids": "test_ids",
        "files in scope": "files_in_scope",
        "dépendances": "dependencies",
        "dependencies": "dependencies",
    }
    for position, (start, task_id) in enumerate(headers):
        end = headers[position + 1][0] if position + 1 < len(headers) else len(lines)
        section = lines[start + 1 : end]
        fields: dict[str, list[str]] = {}
        cursor = 0
        while cursor < len(section):
            plain = section[cursor].replace("**", "").strip()
            match = re.match(
                r"^-\s*(Test-IDs|Files in scope|Dépendances|Dependencies)\s*:\s*(.*)$",
                plain,
                flags=re.IGNORECASE,
            )
            if match is None:
                cursor += 1
                continue
            field = field_names[match.group(1).lower()]
            fragments = [match.group(2).strip()] if match.group(2).strip() else []
            cursor += 1
            while cursor < len(section):
                next_plain = section[cursor].replace("**", "").strip()
                if re.match(
                    r"^-\s*[A-Za-zÀ-ÿ][^:]*\s*:", next_plain
                ):
                    break
                if next_plain.startswith("-"):
                    fragments.append(next_plain.removeprefix("-").strip())
                elif next_plain:
                    break
                cursor += 1
            if field in fields:
                raise GuardError(f"task {task_id} repeats field {field}")
            if field == "test_ids":
                values = [
                    test_id
                    for fragment in fragments
                    for test_id in re.findall(r"\bT-[0-9]{3}-T[1-9][0-9]*\b", fragment)
                ]
            elif field == "dependencies":
                values = [
                    dependency
                    for fragment in fragments
                    for dependency in re.findall(r"\bT-[0-9]{3}\b", fragment)
                ]
            else:
                values = []
                for fragment in fragments:
                    code_paths = re.findall(r"`([^`]+)`", fragment)
                    if code_paths:
                        values.extend(code_paths)
                    elif fragment:
                        values.extend(
                            value.strip() for value in fragment.split(",") if value.strip()
                        )
            fields[field] = values
        missing = {"test_ids", "files_in_scope", "dependencies"} - set(fields)
        if missing:
            raise GuardError(
                f"task {task_id} is missing contract fields: {', '.join(sorted(missing))}"
            )
        result[task_id] = fields
    return result


def assert_state_matches_tasks(
    state: object,
    tasks_markdown: str,
    *,
    repo_root: Path | str | None = None,
) -> None:
    validated = validate_state(state, repo_root=repo_root, allow_legacy=False)
    contract = task_contract_from_markdown(tasks_markdown)
    tasks = validated["tasks"]
    assert isinstance(tasks, dict)
    if set(contract) != set(tasks):
        raise GuardError("04-tasks.md and state contain different Task-IDs")
    for task_id, task in tasks.items():
        assert isinstance(task, dict)
        expected = contract[task_id]
        for field in ("test_ids", "files_in_scope", "dependencies"):
            if task.get(field) != expected[field]:
                raise GuardError(
                    f"04-tasks.md and state disagree for {task_id}.{field}"
                )


def _validate_feature_and_task(feature_id: str, task_id: str) -> None:
    _validate_identifier(feature_id, FEATURE_ID, "feature_id")
    _validate_identifier(task_id, TASK_ID, "task ID")


def _load_object(path: Path, label: str, *, absent: dict[str, object]) -> dict[str, object]:
    if path.is_symlink():
        raise GuardError(f"{label} is a symlink")
    data = read_bytes(path)
    if data is None:
        return copy.deepcopy(absent)
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GuardError(f"{label} is invalid JSON: {error}") from error
    if not isinstance(value, dict):
        raise GuardError(f"{label} must be an object")
    return value


def process_start_token(process_id: int) -> str:
    if not isinstance(process_id, int) or isinstance(process_id, bool) or process_id <= 1:
        raise GuardError("process ID must be greater than one")
    if sys.platform.startswith("linux"):
        proc_stat = Path("/proc") / str(process_id) / "stat"
        try:
            value = proc_stat.read_text(encoding="ascii")
            closing = value.rfind(")")
            fields = value[closing + 2 :].split()
            token = fields[19]
        except (OSError, IndexError, UnicodeError) as error:
            raise GuardError(f"cannot read process birth for PID {process_id}") from error
        token = f"linux:{token}"
    elif sys.platform == "darwin":
        info = DarwinBsdInfo()
        libproc = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        proc_pidinfo = libproc.proc_pidinfo
        proc_pidinfo.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint64,
            ctypes.c_void_p,
            ctypes.c_int,
        ]
        proc_pidinfo.restype = ctypes.c_int
        ctypes.set_errno(0)
        returned = proc_pidinfo(
            process_id,
            3,
            0,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if returned <= 0:
            raise GuardError(f"cannot read process birth for PID {process_id}")
        if returned < ctypes.sizeof(info):
            raise GuardError("incomplete Darwin process birth record")
        token = f"darwin:{info.pbi_start_tvsec}:{info.pbi_start_tvusec}"
    else:
        raise GuardError("stable process identity is unavailable on this platform")
    if len(token) > 96:
        raise GuardError("process birth token is unexpectedly long")
    return token


def process_identity_alive(process_id: object, start_token: object) -> bool:
    if not isinstance(process_id, int) or isinstance(process_id, bool):
        return False
    if not isinstance(start_token, str) or not start_token:
        return False
    try:
        return process_start_token(process_id) == start_token
    except GuardError:
        return False


def _lease_registry(root: Path) -> tuple[Path, dict[str, object]]:
    leases_path = runtime_directory(root) / "leases.json"
    registry = _load_object(
        leases_path,
        "scope lease registry",
        absent={"version": 2, "leases": {}},
    )
    if registry.get("version") != 2 or not isinstance(registry.get("leases"), dict):
        raise GuardError("scope lease registry format is unsupported")
    return leases_path, registry


def _prune_stale_leases(registry: dict[str, object], now: float) -> list[str]:
    leases = registry["leases"]
    assert isinstance(leases, dict)
    removed: list[str] = []
    for lease_id, lease in list(leases.items()):
        if not isinstance(lease, dict):
            raise GuardError(f"invalid existing scope lease: {lease_id}")
        expires_at = lease.get("expires_at")
        stale = (
            not isinstance(expires_at, (int, float))
            or isinstance(expires_at, bool)
            or expires_at <= now
            or not process_identity_alive(
                lease.get("process_id"), lease.get("process_start")
            )
        )
        if stale:
            del leases[lease_id]
            removed.append(lease_id)
    return removed


def acquire_scope_lease(
    repo_root: Path | str,
    *,
    feature_id: str,
    task_id: str,
    owner: str,
    session_id: str,
    files_in_scope: Sequence[str],
    state: object,
    process_id: int | None = None,
    process_start: str | None = None,
    ttl_seconds: float = 300.0,
    _now: float | None = None,
) -> dict[str, object]:
    _validate_feature_and_task(feature_id, task_id)
    _validate_identifier(owner, EVENT_ID, "lease owner")
    _validate_identifier(session_id, EVENT_ID, "session ID")
    root = repository_root(repo_root)
    validated_state = validate_state(state, repo_root=root, allow_legacy=False)
    if isinstance(validated_state.get("migration"), dict):
        raise GuardError("incomplete migrated state cannot acquire a worker lease")
    tasks = validated_state["tasks"]
    assert isinstance(tasks, dict)
    task = tasks.get(task_id)
    if not isinstance(task, dict):
        raise GuardError(f"state does not contain task {task_id}")
    scope = sorted({validate_scope_path(root, path) for path in files_in_scope})
    if len(scope) != len(files_in_scope) or not scope:
        raise GuardError("scope lease requires unique concrete paths")
    if scope != sorted(task.get("files_in_scope", [])):
        raise GuardError("scope lease must match the validated task scope exactly")
    if not isinstance(ttl_seconds, (int, float)) or isinstance(ttl_seconds, bool) or not 1 <= ttl_seconds <= 2700:
        raise GuardError("scope lease TTL must be between 1 and 2700 seconds")
    process_id = os.getpid() if process_id is None else process_id
    process_start = process_start_token(process_id) if process_start is None else process_start
    if not process_identity_alive(process_id, process_start):
        raise GuardError("scope lease process identity is not alive")
    now = time.time() if _now is None else _now
    worktree = worktree_identity(root)
    identity = canonical_json(
        {
            "feature_id": feature_id,
            "task_id": task_id,
            "owner": owner,
            "session_id": session_id,
            "process_id": process_id,
            "process_start": process_start,
            **worktree,
            "scope": scope,
        }
    )
    lease_id = "lease-" + hashlib.sha256(identity).hexdigest()[:24]
    with global_lock(root):
        leases_path, registry = _lease_registry(root)
        removed = _prune_stale_leases(registry, now)
        leases = registry["leases"]
        assert isinstance(leases, dict)
        existing = leases.get(lease_id)
        requested = {
            "feature_id": feature_id,
            "task_id": task_id,
            "owner": owner,
            "session_id": session_id,
            "process_id": process_id,
            "process_start": process_start,
            **worktree,
            "files_in_scope": scope,
            "expires_at": now + ttl_seconds,
        }
        if existing is not None:
            stable_fields = {key: value for key, value in requested.items() if key != "expires_at"}
            if not isinstance(existing, dict) or any(existing.get(key) != value for key, value in stable_fields.items()):
                raise GuardError("scope lease identity collision")
            existing["expires_at"] = requested["expires_at"]
            atomic_replace(leases_path, canonical_json(registry))
            return {"lease_id": lease_id, **existing, "idempotent": True, "reclaimed": removed}
        for other_id, other in leases.items():
            if not isinstance(other, dict) or not isinstance(other.get("files_in_scope"), list):
                raise GuardError(f"invalid existing scope lease: {other_id}")
            if any(
                paths_overlap(left, right)
                for left in scope
                for right in other["files_in_scope"]
            ):
                raise GuardError(
                    f"scope conflicts with active lease {other_id} for task {other.get('task_id')}"
                )
        active_for_feature = sum(
            1
            for other in leases.values()
            if isinstance(other, dict) and other.get("feature_id") == feature_id
        )
        maximum = validated_state["max_workers"]
        assert isinstance(maximum, int)
        if active_for_feature >= maximum:
            raise GuardError(
                f"feature {feature_id} already holds its {maximum} allowed worker leases"
            )
        leases[lease_id] = requested
        atomic_replace(leases_path, canonical_json(registry))
    return {"lease_id": lease_id, **requested, "idempotent": False, "reclaimed": removed}


def heartbeat_scope_lease(
    repo_root: Path | str,
    *,
    lease_id: str,
    owner: str,
    session_id: str,
    process_id: int,
    process_start: str,
    ttl_seconds: float = 300.0,
    _now: float | None = None,
) -> float:
    _validate_identifier(lease_id.removeprefix("lease-"), re.compile(r"^[a-f0-9]{24}$"), "lease ID")
    _validate_identifier(owner, EVENT_ID, "lease owner")
    _validate_identifier(session_id, EVENT_ID, "session ID")
    if not process_identity_alive(process_id, process_start):
        raise GuardError("scope lease process identity is not alive")
    if not isinstance(ttl_seconds, (int, float)) or isinstance(ttl_seconds, bool) or not 1 <= ttl_seconds <= 2700:
        raise GuardError("scope lease TTL must be between 1 and 2700 seconds")
    now = time.time() if _now is None else _now
    root = repository_root(repo_root)
    with global_lock(root):
        leases_path, registry = _lease_registry(root)
        leases = registry["leases"]
        assert isinstance(leases, dict)
        lease = leases.get(lease_id)
        if not isinstance(lease, dict):
            raise GuardError("scope lease no longer exists")
        identity = {
            "owner": owner,
            "session_id": session_id,
            "process_id": process_id,
            "process_start": process_start,
        }
        if any(lease.get(key) != value for key, value in identity.items()):
            raise GuardError("scope lease heartbeat identity mismatch")
        if not isinstance(lease.get("expires_at"), (int, float)) or lease["expires_at"] <= now:
            raise GuardError("scope lease expired before heartbeat")
        lease["expires_at"] = now + ttl_seconds
        atomic_replace(leases_path, canonical_json(registry))
        return lease["expires_at"]


def release_scope_lease(
    repo_root: Path | str, *, lease_id: str, owner: str, session_id: str
) -> bool:
    _validate_identifier(lease_id.removeprefix("lease-"), re.compile(r"^[a-f0-9]{24}$"), "lease ID")
    _validate_identifier(owner, EVENT_ID, "lease owner")
    _validate_identifier(session_id, EVENT_ID, "session ID")
    root = repository_root(repo_root)
    leases_path = runtime_directory(root) / "leases.json"
    with global_lock(root):
        registry = _load_object(leases_path, "scope lease registry", absent={"version": 2, "leases": {}})
        leases = registry.get("leases")
        if registry.get("version") != 2 or not isinstance(leases, dict):
            raise GuardError("scope lease registry format is unsupported")
        existing = leases.get(lease_id)
        if existing is None:
            return False
        if (
            not isinstance(existing, dict)
            or existing.get("owner") != owner
            or existing.get("session_id") != session_id
        ):
            raise GuardError("only the lease owner can release a scope")
        del leases[lease_id]
        atomic_replace(leases_path, canonical_json(registry))
    return True


def append_job_event(
    repo_root: Path | str,
    *,
    feature_id: str,
    task_id: str,
    event_id: str,
    event: Mapping[str, object],
) -> Path:
    _validate_feature_and_task(feature_id, task_id)
    _validate_identifier(event_id, EVENT_ID, "event ID")
    _assert_no_forbidden_state_fields(event, "event")
    root = repository_root(repo_root)
    directory = root / ".specs" / feature_id / "jobs" / task_id
    expected_parent = root / ".specs" / feature_id
    current = root
    for part in expected_parent.relative_to(root).parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise GuardError(f"job journal parent is a symlink: {current}")
    data = canonical_json(
        {"schema_version": 1, "feature_id": feature_id, "task_id": task_id, "event_id": event_id, "event": dict(event)}
    )
    runtime, identity = worktree_runtime_directory(root)
    manifest_directory = ensure_directory_chain(runtime, "journals", feature_id)
    manifest_path = manifest_directory / f"{task_id}.json"
    with global_lock(root):
        directory = ensure_directory_chain(
            root, ".specs", feature_id, "jobs", task_id
        )
        manifest = _load_object(
            manifest_path,
            "job journal manifest",
            absent={
                "schema_version": 1,
                **identity,
                "feature_id": feature_id,
                "task_id": task_id,
                "events": {},
            },
        )
        _verify_job_manifest(
            directory,
            manifest,
            identity,
            feature_id,
            task_id,
            allowed_unmanifested=f"{event_id}.json",
        )
        events = manifest["events"]
        assert isinstance(events, dict)
        path = directory / f"{event_id}.json"
        digest = token_for(data)
        existing_digest = events.get(event_id)
        if existing_digest is not None:
            if existing_digest == digest and read_bytes(path) == data and not path.is_symlink():
                return path
            raise GuardError(f"immutable job event was mutated: {path.name}")
        if path.exists() or path.is_symlink():
            if path.is_file() and not path.is_symlink() and read_bytes(path) == data:
                # Recover an interruption after the immutable file reached disk
                # but before its common-dir manifest was synchronized.
                events[event_id] = digest
                atomic_replace(manifest_path, canonical_json(manifest))
                return path
            raise GuardError(f"unmanifested job event has different content: {path.name}")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            fsync_directory(directory)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        events[event_id] = digest
        atomic_replace(manifest_path, canonical_json(manifest))
        return path


def _verify_job_manifest(
    directory: Path,
    manifest: dict[str, object],
    identity: Mapping[str, str],
    feature_id: str,
    task_id: str,
    allowed_unmanifested: str | None = None,
) -> None:
    expected_identity: dict[str, object] = {
        "schema_version": 1,
        **identity,
        "feature_id": feature_id,
        "task_id": task_id,
    }
    if any(manifest.get(key) != value for key, value in expected_identity.items()):
        raise GuardError("job journal manifest identity mismatch")
    events = manifest.get("events")
    if not isinstance(events, dict) or any(
        not isinstance(event_id, str) or not isinstance(digest, str)
        for event_id, digest in events.items()
    ):
        raise GuardError("job journal manifest events are invalid")
    actual_names = {path.name for path in directory.glob("*.json")}
    expected_names = {f"{event_id}.json" for event_id in events}
    extra = actual_names - expected_names
    allowed = set() if allowed_unmanifested is None else {allowed_unmanifested}
    if extra - allowed:
        raise GuardError(
            "job journal contains unmanifested events: "
            + ", ".join(sorted(extra - allowed))
        )
    missing = expected_names - actual_names
    if missing:
        raise GuardError("immutable job events were deleted: " + ", ".join(sorted(missing)))
    for event_id, digest in events.items():
        path = directory / f"{event_id}.json"
        if path.is_symlink() or not path.is_file() or token_for(read_bytes(path)) != digest:
            raise GuardError(f"immutable job event was mutated: {path.name}")


def verify_job_journal(
    repo_root: Path | str, *, feature_id: str, task_id: str
) -> int:
    _validate_feature_and_task(feature_id, task_id)
    root = repository_root(repo_root)
    directory = root / ".specs" / feature_id / "jobs" / task_id
    runtime, identity = worktree_runtime_directory(root)
    manifest_path = runtime / "journals" / feature_id / f"{task_id}.json"
    with global_lock(root):
        manifest = _load_object(manifest_path, "job journal manifest", absent={})
        if not manifest:
            raise GuardError("job journal manifest does not exist")
        _verify_job_manifest(directory, manifest, identity, feature_id, task_id)
        events = manifest["events"]
        assert isinstance(events, dict)
        return len(events)


def shared_artifact_path(feature_id: str, path: str) -> bool:
    normalized = normalize_scope_path(path)
    prefix = f".specs/{feature_id}/"
    return normalized.startswith(prefix) and normalized.removeprefix(prefix) in SHARED_ARTIFACTS


def validate_worker_changes(
    *,
    feature_id: str,
    task_id: str,
    changed_paths: Sequence[str],
    files_in_scope: Sequence[str],
) -> list[str]:
    _validate_identifier(feature_id, FEATURE_ID, "feature_id")
    _validate_identifier(task_id, TASK_ID, "task ID")
    scope = [normalize_scope_path(path) for path in files_in_scope]
    allowed_journal = f".specs/{feature_id}/jobs/{task_id}/"
    normalized_changes: list[str] = []
    for changed in changed_paths:
        path = normalize_scope_path(changed)
        if shared_artifact_path(feature_id, path):
            raise GuardError(f"worker cannot modify shared artifact: {path}")
        if not path.startswith(allowed_journal) and path not in scope:
            raise GuardError(f"worker changed a file outside its scope: {path}")
        normalized_changes.append(path)
    return normalized_changes


def repository_fingerprint(
    repo_root: Path | str, *, excluded_paths: Sequence[str] = ()
) -> dict[str, str]:
    root = repository_root(repo_root)
    excluded = [validate_scope_path(root, path) for path in excluded_paths]
    result: dict[str, str] = {}

    index_by_path: dict[str, list[bytes]] = {}
    index = _run_git(root, "ls-files", "--stage", "-z")
    for raw in index.split(b"\0"):
        if not raw:
            continue
        try:
            metadata, raw_path = raw.split(b"\t", 1)
        except ValueError as error:
            raise GuardError("Git index record is malformed") from error
        path = os.fsdecode(raw_path)
        normalized = normalize_scope_path(path)
        if any(paths_overlap(normalized, allowed) for allowed in excluded):
            continue
        index_by_path.setdefault(normalized, []).append(metadata)
    for path, records in index_by_path.items():
        result[f"index:{path}"] = hashlib.sha256(b"\0".join(sorted(records))).hexdigest()

    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as stream:
                entries = sorted(stream, key=lambda entry: entry.name)
        except OSError as error:
            raise GuardError(f"cannot enumerate repository path: {directory}") from error
        for entry in entries:
            target = Path(entry.path)
            relative = target.relative_to(root).as_posix()
            if relative == ".git" or relative.startswith(".git/"):
                continue
            normalized = normalize_scope_path(relative)
            if any(paths_overlap(normalized, allowed) for allowed in excluded):
                continue
            try:
                before = target.lstat()
            except FileNotFoundError:
                raise GuardError(f"repository changed during fingerprint: {normalized}")
            if stat.S_ISDIR(before.st_mode):
                stack.append(target)
                continue
            identity_before = (
                before.st_dev,
                before.st_ino,
                before.st_mode,
                before.st_size,
                before.st_mtime_ns,
            )
            if stat.S_ISLNK(before.st_mode):
                payload = b"symlink\0" + os.fsencode(os.readlink(target))
            elif stat.S_ISREG(before.st_mode):
                payload = b"file\0" + target.read_bytes()
            else:
                raise GuardError(f"unsupported repository path type: {normalized}")
            try:
                after = target.lstat()
            except FileNotFoundError as error:
                raise GuardError(f"repository changed during fingerprint: {normalized}") from error
            identity_after = (
                after.st_dev,
                after.st_ino,
                after.st_mode,
                after.st_size,
                after.st_mtime_ns,
            )
            if identity_before != identity_after:
                raise GuardError(f"repository changed during fingerprint: {normalized}")
            mode = stat.S_IMODE(after.st_mode)
            result[f"working:{normalized}"] = hashlib.sha256(
                f"{mode:o}\0".encode("ascii") + payload
            ).hexdigest()
    return result


def assert_fingerprint_unchanged(
    before: Mapping[str, str], after: Mapping[str, str]
) -> None:
    if dict(before) != dict(after):
        changed = sorted(set(before) ^ set(after) | {path for path in set(before) & set(after) if before[path] != after[path]})
        raise GuardError("files outside the active wave changed: " + ", ".join(changed))


def _artifact_record(data: bytes | None, mode: int | None) -> dict[str, object]:
    if data is None:
        return {"exists": False}
    return {
        "exists": True,
        "data_b64": base64.b64encode(data).decode("ascii"),
        "mode": mode,
        "digest": token_for(data),
    }


def _decode_artifact(record: object, label: str) -> tuple[bytes | None, int | None]:
    if not isinstance(record, dict) or not isinstance(record.get("exists"), bool):
        raise GuardError(f"invalid transaction artifact {label}")
    if not record["exists"]:
        return None, None
    encoded = record.get("data_b64")
    mode = record.get("mode")
    digest = record.get("digest")
    if not isinstance(encoded, str) or not isinstance(mode, int) or not isinstance(digest, str):
        raise GuardError(f"invalid transaction artifact {label}")
    try:
        data = base64.b64decode(encoded, validate=True)
    except ValueError as error:
        raise GuardError(f"invalid transaction artifact base64 {label}") from error
    if token_for(data) != digest:
        raise GuardError(f"transaction artifact digest mismatch {label}")
    return data, mode


def _validate_fan_in_path(root: Path, feature_id: str, path: object) -> str:
    normalized = validate_scope_path(root, path)
    if not shared_artifact_path(feature_id, normalized):
        raise GuardError(f"fan-in target is not a shared SDD artifact: {normalized}")
    return normalized


def _materialize(root: Path, relative: str, data: bytes | None, mode: int | None) -> None:
    target = root / relative
    if data is None:
        target.unlink(missing_ok=True)
        fsync_directory(target.parent)
        return
    atomic_replace(target, data, 0o600 if mode is None else mode)


def _transaction_paths(
    root: Path, feature_id: str, transaction_id: str
) -> tuple[Path, Path, dict[str, str]]:
    _validate_identifier(transaction_id, EVENT_ID, "transaction ID")
    runtime, identity = worktree_runtime_directory(root)
    directory = ensure_directory_chain(runtime, "transactions", feature_id)
    return (
        directory / f"{transaction_id}.json",
        directory / f"{transaction_id}.commit.json",
        identity,
    )


def _validate_completed_marker(
    marker: object,
    *,
    identity: Mapping[str, str],
    feature_id: str,
    transaction_id: str,
    targets: Mapping[str, str],
) -> dict[str, object]:
    required = {
        "schema_version",
        "operation",
        "repository_id",
        "worktree_id",
        "head",
        "feature_id",
        "transaction_id",
        "journal_digest",
        "targets",
    }
    if not isinstance(marker, dict) or set(marker) != required:
        raise GuardError("fan-in marker fields are invalid")
    expected: dict[str, object] = {
        "schema_version": 1,
        "operation": "fan-in",
        **identity,
        "feature_id": feature_id,
        "transaction_id": transaction_id,
        "targets": dict(targets),
    }
    if any(marker.get(key) != value for key, value in expected.items()):
        raise GuardError("fan-in marker identity or targets mismatch")
    digest = marker.get("journal_digest")
    if not isinstance(digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None:
        raise GuardError("fan-in marker journal digest is invalid")
    return marker


def recover_fan_in(
    repo_root: Path | str, *, feature_id: str, transaction_id: str
) -> str | None:
    _validate_identifier(feature_id, FEATURE_ID, "feature_id")
    root = repository_root(repo_root)
    journal_path, marker_path, identity = _transaction_paths(
        root, feature_id, transaction_id
    )
    with global_lock(root):
        if journal_path.is_symlink() or marker_path.is_symlink():
            raise GuardError("fan-in journal or marker is a symlink")
        journal_data = read_bytes(journal_path)
        if journal_data is None:
            return None
        try:
            journal = json.loads(journal_data)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise GuardError(f"fan-in journal is invalid JSON: {error}") from error
        if not isinstance(journal, dict) or journal.get("schema_version") != 1 or journal.get("operation") != "fan-in":
            raise GuardError("fan-in journal format is unsupported")
        expected_identity: dict[str, object] = {
            **identity,
            "feature_id": feature_id,
            "transaction_id": transaction_id,
        }
        if any(journal.get(key) != value for key, value in expected_identity.items()):
            raise GuardError("fan-in journal identity mismatch")
        artifacts = journal.get("artifacts")
        if not isinstance(artifacts, dict) or not artifacts:
            raise GuardError("fan-in journal has no artifacts")
        decoded: list[tuple[str, bytes | None, int | None, bytes | None, int | None]] = []
        targets: dict[str, str] = {}
        for path_value, versions in artifacts.items():
            path = _validate_fan_in_path(root, feature_id, path_value)
            if not isinstance(versions, dict):
                raise GuardError(f"invalid fan-in versions for {path}")
            previous_data, previous_mode = _decode_artifact(versions.get("previous"), f"{path}.previous")
            next_data, next_mode = _decode_artifact(versions.get("next"), f"{path}.next")
            current = token_for(read_bytes(root / path))
            if current not in {token_for(previous_data), token_for(next_data)}:
                raise GuardError(f"cannot recover fan-in after concurrent change: {path}")
            decoded.append((path, previous_data, previous_mode, next_data, next_mode))
            targets[path] = token_for(next_data)
        marker_data = read_bytes(marker_path)
        committed = marker_data is not None
        if committed:
            try:
                marker = json.loads(marker_data)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise GuardError(f"fan-in marker is invalid JSON: {error}") from error
            validated_marker = _validate_completed_marker(
                marker,
                identity=identity,
                feature_id=feature_id,
                transaction_id=transaction_id,
                targets=targets,
            )
            if validated_marker.get("journal_digest") != token_for(journal_data):
                raise GuardError("fan-in marker does not authenticate this journal and targets")
        for path, previous_data, previous_mode, next_data, next_mode in decoded:
            _materialize(
                root,
                path,
                next_data if committed else previous_data,
                next_mode if committed else previous_mode,
            )
        remove_durably(journal_path)
        if not committed:
            marker_path.unlink(missing_ok=True)
        return "committed" if committed else "rolled-back"


def transactional_fan_in(
    repo_root: Path | str,
    *,
    feature_id: str,
    transaction_id: str,
    actor: str,
    artifacts: Mapping[str, bytes],
    expected_tokens: Mapping[str, str],
    _crash_point: str | None = None,
) -> dict[str, object]:
    if actor != "synthesizer":
        raise GuardError("only the synthesizer can update shared SDD artifacts")
    _validate_identifier(feature_id, FEATURE_ID, "feature_id")
    root = repository_root(repo_root)
    if not artifacts:
        raise GuardError("fan-in requires at least one artifact")
    normalized_artifacts = {
        _validate_fan_in_path(root, feature_id, path): data for path, data in artifacts.items()
    }
    if any(not isinstance(data, bytes) for data in normalized_artifacts.values()):
        raise GuardError("fan-in artifacts must be bytes")
    for path, data in normalized_artifacts.items():
        if not data.strip():
            raise GuardError(f"fan-in artifact is empty: {path}")
        if path.endswith("/.tdd-state.json"):
            try:
                candidate_state = json.loads(data)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise GuardError(f"fan-in state is invalid JSON: {error}") from error
            validated_state = validate_state(candidate_state, repo_root=root)
            if validated_state.get("feature_id") != feature_id:
                raise GuardError("fan-in state feature_id mismatch")
            migration = validated_state.get("migration")
            if isinstance(migration, dict) and not migration.get("contract_complete"):
                raise GuardError(
                    "fan-in refuses an incomplete v1 migration; complete task contracts first"
                )
    if set(expected_tokens) != set(normalized_artifacts):
        raise GuardError("fan-in expected token set does not match its artifacts")
    journal_path, marker_path, identity = _transaction_paths(
        root, feature_id, transaction_id
    )

    recovery = recover_fan_in(root, feature_id=feature_id, transaction_id=transaction_id)
    if recovery == "committed":
        marker = _load_object(marker_path, "fan-in commit marker", absent={})
        targets = {path: token_for(data) for path, data in normalized_artifacts.items()}
        _validate_completed_marker(
            marker,
            identity=identity,
            feature_id=feature_id,
            transaction_id=transaction_id,
            targets=targets,
        )
        return {"committed": True, "idempotent": True, "transaction_id": transaction_id}

    with global_lock(root):
        marker = _load_object(marker_path, "fan-in commit marker", absent={})
        targets = {path: token_for(data) for path, data in normalized_artifacts.items()}
        if marker:
            _validate_completed_marker(
                marker,
                identity=identity,
                feature_id=feature_id,
                transaction_id=transaction_id,
                targets=targets,
            )
            if all(token_for(read_bytes(root / path)) == digest for path, digest in targets.items()):
                return {"committed": True, "idempotent": True, "transaction_id": transaction_id}
            raise GuardError("fan-in receipt exists but target artifacts differ")
        records: dict[str, object] = {}
        for path, next_data in normalized_artifacts.items():
            target = root / path
            current_data = read_bytes(target)
            current_token = token_for(current_data)
            if expected_tokens[path] != current_token:
                raise GuardError(
                    f"fan-in CAS failed for {path}: expected {expected_tokens[path]}, found {current_token}"
                )
            try:
                current_mode = stat.S_IMODE(target.stat().st_mode)
            except FileNotFoundError:
                current_mode = 0o600
            records[path] = {
                "previous": _artifact_record(current_data, current_mode if current_data is not None else None),
                "next": _artifact_record(next_data, current_mode),
            }
        journal = {
            "schema_version": 1,
            "operation": "fan-in",
            **identity,
            "feature_id": feature_id,
            "transaction_id": transaction_id,
            "artifacts": records,
        }
        journal_data = canonical_json(journal)
        atomic_replace(journal_path, journal_data)
        for path, data in normalized_artifacts.items():
            previous = records[path]
            assert isinstance(previous, dict)
            _, target_mode = _decode_artifact(previous["next"], f"{path}.next")
            _materialize(root, path, data, target_mode)
        if _crash_point == "before-marker":
            raise InjectedCrash("interrupted before fan-in commit marker")
        marker_data = {
            "schema_version": 1,
            "operation": "fan-in",
            **identity,
            "feature_id": feature_id,
            "transaction_id": transaction_id,
            "journal_digest": token_for(journal_data),
            "targets": targets,
        }
        atomic_replace(marker_path, canonical_json(marker_data))
        if _crash_point == "after-marker":
            raise InjectedCrash("interrupted after fan-in commit marker")
        remove_durably(journal_path)
    return {"committed": True, "idempotent": False, "transaction_id": transaction_id}


def _load_state_file(path: Path) -> dict[str, object]:
    data = read_bytes(path)
    if data is None:
        raise GuardError(f"state file does not exist: {path}")
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GuardError(f"state file is invalid JSON: {error}") from error
    if not isinstance(value, dict):
        raise GuardError("state file must contain an object")
    return value


def command_validate_state(args: argparse.Namespace) -> None:
    root = repository_root(args.repo_root)
    state = validate_state(_load_state_file(Path(args.state)), repo_root=root)
    print(json.dumps({"valid": True, "schema_version": state["schema_version"], "tasks": len(state["tasks"])}))


def command_migrate_state(args: argparse.Namespace) -> None:
    root = repository_root(args.repo_root)

    def relative_argument(value: str, label: str) -> str:
        supplied = Path(value)
        candidate = supplied if supplied.is_absolute() else root / supplied
        if candidate.is_symlink():
            raise GuardError(f"{label} is a symlink")
        if supplied.is_absolute():
            try:
                relative = supplied.resolve(strict=False).relative_to(root).as_posix()
            except ValueError as error:
                raise GuardError(f"{label} escapes repository") from error
        else:
            relative = supplied.as_posix()
        return validate_scope_path(root, relative)

    source_relative = relative_argument(args.state, "migration source")
    source_parts = PurePosixPath(source_relative).parts
    if (
        len(source_parts) != 3
        or source_parts[0] != ".specs"
        or source_parts[2] != ".tdd-state.json"
    ):
        raise GuardError("migration source must be canonical .specs/<feature>/.tdd-state.json")
    feature_id = _validate_identifier(source_parts[1], FEATURE_ID, "feature_id")
    expected_output = f".specs/{feature_id}/.tdd-state.candidate.json"
    output_relative = relative_argument(args.output, "migration output")
    if output_relative != expected_output:
        raise GuardError(f"migration output must be canonical {expected_output}")
    source = root / source_relative
    output = root / output_relative
    with global_lock(root):
        source_data = read_bytes(source)
        if source_data is None:
            raise GuardError("migration source does not exist")
        source_token = token_for(source_data)
        if source_token != args.expected_token:
            raise GuardError(
                f"migration source CAS failed: expected {args.expected_token}, found {source_token}"
            )
        output_token = token_for(read_bytes(output))
        if output_token != args.expected_output_token:
            raise GuardError(
                "migration output CAS failed: "
                f"expected {args.expected_output_token}, found {output_token}"
            )
        try:
            source_state = json.loads(source_data)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise GuardError(f"migration source is invalid JSON: {error}") from error
        if not isinstance(source_state, dict):
            raise GuardError("migration source must contain an object")
        if source_state.get("feature_id") != feature_id:
            raise GuardError("migration source feature_id does not match its directory")
        state = migrate_state_v1(source_state)
        validate_state(state, repo_root=root)
        atomic_replace(output, canonical_json(state))
    print(
        json.dumps(
            {
                "migrated": True,
                "schema_version": STATE_SCHEMA_VERSION,
                "source_token": source_token,
                "output_token": token_for(canonical_json(state)),
            }
        )
    )


def command_migration_snapshot(args: argparse.Namespace) -> None:
    root = repository_root(args.repo_root)
    feature_id = _validate_identifier(args.feature_id, FEATURE_ID, "feature_id")
    source_relative = f".specs/{feature_id}/.tdd-state.json"
    output_relative = f".specs/{feature_id}/.tdd-state.candidate.json"
    validate_scope_path(root, source_relative)
    validate_scope_path(root, output_relative)
    with global_lock(root):
        source_token = token_for(read_bytes(root / source_relative))
        output_token = token_for(read_bytes(root / output_relative))
    print(
        json.dumps(
            {
                "feature_id": feature_id,
                "source": source_relative,
                "source_token": source_token,
                "output": output_relative,
                "output_token": output_token,
            }
        )
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate-state")
    validate.add_argument("--repo-root", required=True)
    validate.add_argument("--state", required=True)
    validate.set_defaults(handler=command_validate_state)
    migrate = commands.add_parser("migrate-state")
    migrate.add_argument("--repo-root", required=True)
    migrate.add_argument("--state", required=True)
    migrate.add_argument("--output", required=True)
    migrate.add_argument("--expected-token", required=True)
    migrate.add_argument("--expected-output-token", required=True)
    migrate.set_defaults(handler=command_migrate_state)
    migration_snapshot = commands.add_parser("migration-snapshot")
    migration_snapshot.add_argument("--repo-root", required=True)
    migration_snapshot.add_argument("--feature-id", required=True)
    migration_snapshot.set_defaults(handler=command_migration_snapshot)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        args.handler(args)
    except (GuardError, OSError) as error:
        print(json.dumps({"valid": False, "error": str(error)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
