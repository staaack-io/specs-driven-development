#!/usr/bin/env python3
"""Validate and transactionally publish SDD harness configuration candidates."""

from __future__ import annotations

import argparse
import base64
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from typing import Any, Iterator
import xml.etree.ElementTree as ET
import io


MAX_FILE_BYTES = 2_000_000
FEATURE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GLOB_RE = re.compile(r"[*?\[\]{}]")
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bnpm_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bpypi-[A-Za-z0-9_-]{20,}\b"),
    re.compile(
        r"(?im)^\s*(?:password|passwd|token|api[_-]?key|client[_-]?secret|credentials?)\s*[:=]\s*"
        r"(?!\$\{|<|REDACTED\b|CHANGEME\b)[\"']?[^\s\"']{8,}"
    ),
    re.compile(
        r"(?is)(?:name|key)\s*=\s*[\"'](?:password|passwd|token|api[_-]?key|"
        r"client[_-]?secret|credentials?)[\"'][^>]{0,200}value\s*=\s*[\"'](?!\$\{|<|REDACTED|CHANGEME)[^\"']{8,}"
    ),
    re.compile(
        r"(?i)\b(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis|amqps?|"
        r"mssql|jdbc:[a-z0-9]+)://[^\s:/@]+:(?!\$\{|<|REDACTED|CHANGEME)[^\s/@]{4,}@"
    ),
    re.compile(
        r"(?i)https?://[^\s?#]+[?&](?:password|passwd|token|api[_-]?key|"
        r"client[_-]?secret|credentials?)=(?!\$\{|<|REDACTED|CHANGEME)[^\s&#]{4,}"
    ),
)
DEPLOY_WORDS = re.compile(
    r"(?:^|[/\s])(kubectl|helm|terraform|ansible-playbook|flyctl|vercel|deploy)(?:$|\s)",
    re.IGNORECASE,
)
FORBIDDEN_COMMAND_PARTS = {
    "--no-verify",
    "-dskiptests",
    "-dpit.skip",
    "-dcheckstyle.skip",
    "-dspotbugs.skip",
}
DANGEROUS_HARNESS_RE = re.compile(
    r"(?im)(?:\bsudo\b|\brm\s+-[^\n]*r|\bcurl\b|\bwget\b|\bssh\b|\bscp\b|"
    r"\bnc\b|\bnetcat\b|\bchmod\s+(?:777|a\+w)|\beval\b|"
    r"(?:curl|wget)[^\n|]*\|\s*(?:sh|bash)\b)"
)
SENSITIVE_KEY_RE = re.compile(
    r"^(?:password|passwd|token|api[_-]?key|apikey|secret|client[_-]?secret|"
    r"clientsecret|private[_-]?key|privatekey|access[_-]?(?:key|token)|"
    r"access(?:key|token)|credential)s?$",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(r"^(?:\$\{[^}]+\}|<[^>]+>|REDACTED|CHANGEME)$", re.IGNORECASE)
SCRIPT_SECRET_RE = re.compile(
    r"(?i)\b(password|passwd|token|api[_-]?key|apikey|secret|client[_-]?secret|"
    r"private[_-]?key|access[_-]?(?:key|token)|credentials?)\b\s*[:=]\s*[\"']"
    r"(?!\$\{|<|REDACTED|CHANGEME)([^\"']{8,})[\"']"
)
SAFE_NODE_SCRIPT_COMMANDS = {
    "eslint",
    "jest",
    "next",
    "react-scripts",
    "tsc",
    "vitest",
}
NODE_SCRIPT_RUNNERS = {"npm", "pnpm", "yarn", "bun"}
SAFE_MAVEN_ARGUMENTS = {
    "verify",
    "--offline",
    "-o",
    "--batch-mode",
    "-B",
    "--no-transfer-progress",
    "-ntp",
    "--show-version",
    "-V",
    "--quiet",
    "-q",
}
SPRING_FILES = {
    "pom.xml",
    "checkstyle.xml",
    "dependency-check-suppressions.xml",
    "config/checkstyle/checkstyle.xml",
}
NEXT_FILES = {
    "package.json",
    "eslint.config.js",
    "eslint.config.mjs",
    "eslint.config.ts",
    "vitest.config.js",
    "vitest.config.mjs",
    "vitest.config.ts",
    "jest.config.js",
    "jest.config.mjs",
    "jest.config.ts",
    "tsconfig.json",
    "next.config.js",
    "next.config.mjs",
    "next.config.ts",
}
GLOBAL_FILES = {".github/scripts/harness.sh"}
ONBOARDING_ARTIFACTS = (
    "_stack.json",
    "_baseline.json",
    "_starter-design.md",
    "_known-debt.md",
    "_onboarding.md",
)


class GuardError(RuntimeError):
    """Expected refusal with a user-readable explanation."""


def sha256(data: bytes | None) -> str:
    if data is None:
        return "absent"
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def run_git(root: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=False,
        capture_output=True,
        timeout=20,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise GuardError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout


def resolve_project(project_root: str) -> tuple[Path, Path]:
    supplied = Path(project_root).expanduser()
    if supplied.is_symlink():
        raise GuardError("symbolic project root refused")
    root = supplied.resolve(strict=True)
    if not root.is_dir():
        raise GuardError("project root must be a real directory")
    top = Path(run_git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if top != root:
        raise GuardError(f"project root must be the Git top-level directory: {top}")
    common_text = run_git(root, "rev-parse", "--git-common-dir").decode().strip()
    common = Path(common_text)
    if not common.is_absolute():
        common = root / common
    common = common.resolve(strict=True)
    if not common.is_dir():
        raise GuardError("Git common directory must be a real directory")
    return root, common


def worktree_namespace(root: Path) -> str:
    worktree_git_dir = Path(
        run_git(root, "rev-parse", "--absolute-git-dir").decode().strip()
    ).resolve(strict=True)
    return hashlib.sha256(
        canonical_json({"root": str(root.resolve(strict=True)), "git_dir": str(worktree_git_dir)})
    ).hexdigest()[:24]


def technical_paths(root: Path, git_dir: Path) -> dict[str, Path]:
    root = root.resolve(strict=True)
    state = git_dir / "sdd-wire-harness-state" / worktree_namespace(root)
    return {
        "lock": git_dir / "sdd-wire-harness.lock",
        "journal": state / "transaction.json",
        "receipt": state / "commit.json",
    }


def read_bytes(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GuardError(f"{label} is not valid JSON: {error}") from error
    if not isinstance(value, dict):
        raise GuardError(f"{label} must be a JSON object")
    return value


def load_optional_json(path: Path, label: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if path.is_symlink():
        raise GuardError(f"symbolic {label} refused")
    return load_json(path, label)


def fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_replace(path: Path, data: bytes, mode: int = 0o644) -> None:
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


def remove_file(path: Path) -> None:
    path.unlink(missing_ok=True)
    fsync_directory(path.parent)


def encode_payload(data: bytes | None, mode: int | None) -> dict[str, Any]:
    if data is None:
        return {"exists": False}
    return {
        "exists": True,
        "data_b64": base64.b64encode(data).decode("ascii"),
        "mode": mode,
    }


def decode_payload(value: object, label: str) -> tuple[bytes | None, int | None]:
    if not isinstance(value, dict) or not isinstance(value.get("exists"), bool):
        raise GuardError(f"{label} is invalid")
    if not value["exists"]:
        return None, None
    encoded, mode = value.get("data_b64"), value.get("mode")
    if not isinstance(encoded, str) or not isinstance(mode, int):
        raise GuardError(f"{label} is invalid")
    try:
        return base64.b64decode(encoded, validate=True), mode
    except ValueError as error:
        raise GuardError(f"{label} contains invalid base64") from error


@contextlib.contextmanager
def exclusive_lock(lock_path: Path) -> Iterator[None]:
    if lock_path.is_symlink():
        raise GuardError("symbolic wire-harness lock refused")
    flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(lock_path, flags, 0o600)
    except OSError as error:
        raise GuardError(f"cannot safely open wire-harness lock: {error}") from error
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise GuardError("another wire-harness transaction holds the lock") from error
        yield
    finally:
        os.close(descriptor)


def safe_relative(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise GuardError(f"{label} must be a non-empty POSIX relative path")
    if GLOB_RE.search(value):
        raise GuardError(f"ambiguous glob refused in {label}: {value}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise GuardError(f"path outside repository refused in {label}: {value}")
    normalized = path.as_posix()
    if normalized != value or normalized.startswith(".git/") or normalized == ".git":
        raise GuardError(f"unsafe path refused in {label}: {value}")
    return normalized


def reject_symlink_chain(root: Path, relative_path: str, *, allow_missing: bool) -> Path:
    root = root.resolve(strict=True)
    current = root
    parts = PurePosixPath(relative_path).parts
    for index, part in enumerate(parts):
        current = current / part
        if current.is_symlink():
            raise GuardError(f"symbolic path refused: {relative_path}")
        if not current.exists():
            if allow_missing:
                break
            raise GuardError(f"missing evidence path: {relative_path}")
        if index < len(parts) - 1 and not current.is_dir():
            raise GuardError(f"non-directory path component: {relative_path}")
    resolved_parent = current.parent.resolve(strict=True) if current.parent.exists() else root
    try:
        resolved_parent.relative_to(root)
    except ValueError as error:
        raise GuardError(f"path outside repository refused: {relative_path}") from error
    return root / relative_path


def parse_status(root: Path) -> list[tuple[str, str]]:
    raw = run_git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = raw.split(b"\0")
    changes: list[tuple[str, str]] = []
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        if len(entry) < 4:
            raise GuardError("unexpected Git status entry")
        status_code = entry[:2].decode("ascii", "replace")
        path = entry[3:].decode("utf-8", "surrogateescape")
        changes.append((status_code, path))
        if "R" in status_code or "C" in status_code:
            if index >= len(entries) or not entries[index]:
                raise GuardError("incomplete Git rename status")
            old_path = entries[index].decode("utf-8", "surrogateescape")
            index += 1
            changes.append((status_code, old_path))
    return changes


def validate_feature_id(value: str | None) -> str | None:
    if value is None:
        return None
    if not FEATURE_RE.fullmatch(value) or len(value) > 100:
        raise GuardError("feature-id must use lower-case letters, digits and hyphens")
    return value


def evidence_strings(module: dict[str, Any]) -> list[str]:
    evidence = module.get("evidence")
    if not isinstance(evidence, list):
        raise GuardError("each proved stack module must contain an evidence list")
    values: list[str] = []
    for item in evidence:
        if isinstance(item, str):
            values.append(item.split("#", 1)[0].split(" and ", 1)[0])
        elif isinstance(item, dict) and isinstance(item.get("path"), str):
            values.append(item["path"])
        else:
            raise GuardError("stack evidence entries must contain relative paths")
    if not values:
        raise GuardError("proved stack module has no evidence")
    return values


def detect_stacks(
    root: Path, *, require_current_head: bool = True
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    specs = root / ".specs"
    if specs.is_symlink() or not specs.is_dir():
        raise GuardError(".specs must be a real directory created by /sdd-onboard")
    stack_path = specs / "_stack.json"
    if stack_path.is_symlink() or not stack_path.is_file():
        raise GuardError(".specs/_stack.json is required and must not be a symlink")
    stack = load_json(stack_path, "_stack.json")
    if stack.get("schema_version") != 1 or not isinstance(stack.get("modules"), list):
        raise GuardError("_stack.json must follow onboarding schema_version 1")
    confidence = stack.get("confidence")
    if (
        not isinstance(confidence, dict)
        or confidence.get("level") != "proved"
        or not isinstance(confidence.get("limitations"), list)
    ):
        raise GuardError("wire-harness requires proved onboarding confidence")
    head = run_git(root, "rev-parse", "HEAD").decode().strip()
    if require_current_head and stack.get("git_sha") != head:
        raise GuardError("_stack.json does not describe the current Git HEAD")

    detected: list[dict[str, Any]] = []
    for raw_module in stack["modules"]:
        if not isinstance(raw_module, dict):
            raise GuardError("_stack.json modules must be objects")
        kind = raw_module.get("kind")
        if kind not in {"spring", "nextjs", "react"}:
            continue
        if raw_module.get("confidence") != "proved":
            raise GuardError(f"wire-harness refuses unproved {kind} module")
        ambiguities = raw_module.get("ambiguities", [])
        if not isinstance(ambiguities, list) or ambiguities:
            raise GuardError(f"wire-harness refuses ambiguous {kind} module")
        module_path = raw_module.get("module", ".")
        if not isinstance(module_path, str):
            raise GuardError("stack module path must be a string")
        module_path = "." if module_path == "." else safe_relative(module_path, "module")
        manifest = safe_relative(raw_module.get("path"), "module manifest")
        manifest_parent = PurePosixPath(manifest).parent.as_posix()
        if manifest_parent == "":
            manifest_parent = "."
        if manifest_parent != module_path:
            raise GuardError("module manifest must live directly in its declared module")
        proofs = [safe_relative(item, "stack evidence") for item in evidence_strings(raw_module)]
        if manifest not in proofs:
            proofs.append(manifest)
        proof_text = "\n".join(
            reject_symlink_chain(root, item, allow_missing=False)
            .read_text(encoding="utf-8", errors="replace")[:MAX_FILE_BYTES]
            for item in proofs
        )
        if kind == "spring":
            if not manifest.endswith("pom.xml"):
                raise GuardError("Spring wire-harness currently requires a proved Maven pom.xml")
            if "spring-boot-" not in proof_text:
                raise GuardError("Spring evidence does not contain a Spring Boot marker")
            migration = raw_module.get("migration", [])
            if not isinstance(migration, list):
                raise GuardError("Spring migration evidence must be a list")
            if {"flyway", "liquibase"}.issubset(set(migration)):
                raise GuardError("Spring module with both Flyway and Liquibase is refused")
            stack_name = "spring"
        else:
            if not manifest.endswith("package.json"):
                raise GuardError("React/Next.js evidence must be a package.json")
            marker = '"next"' if kind == "nextjs" else '"react"'
            if marker not in proof_text:
                raise GuardError(f"{kind} evidence does not contain {marker}")
            stack_name = "nextjs" if kind == "nextjs" else "react"
            manager = raw_module.get("package_manager")
            if manager not in {"npm", "pnpm", "yarn", "bun"}:
                raise GuardError(f"{kind} module requires one proved package manager")
        detected.append(
            {
                "stack": stack_name,
                "module": module_path,
                "manifest": manifest,
                "evidence": sorted(set(proofs)),
                "versions": raw_module.get("versions", {}),
                "package_manager": raw_module.get("package_manager"),
            }
        )
    if not detected:
        raise GuardError("no proved Spring, React or Next.js stack is available to wire")
    return stack, detected


def join_module(module: str, filename: str) -> str:
    return filename if module == "." else f"{module}/{filename}"


def allowed_targets(stacks: list[dict[str, Any]]) -> dict[str, set[str]]:
    allowed: dict[str, set[str]] = {}
    for stack in stacks:
        names = SPRING_FILES if stack["stack"] == "spring" else NEXT_FILES
        for name in names:
            allowed.setdefault(join_module(stack["module"], name), set()).add(stack["stack"])
    for name in GLOBAL_FILES:
        allowed[name] = {stack["stack"] for stack in stacks}
    return allowed


def receipt_allowed_changes(root: Path, paths: dict[str, Path]) -> set[str]:
    receipt = load_optional_json(paths["receipt"], "wire-harness receipt")
    if receipt is None:
        return set()
    if receipt.get("version") != 1 or receipt.get("operation") != "wire-harness-commit":
        raise GuardError("wire-harness receipt has an unsupported schema")
    targets = receipt.get("targets")
    if not isinstance(targets, list):
        raise GuardError("wire-harness receipt targets are invalid")
    allowed: set[str] = set()
    for item in targets:
        if not isinstance(item, dict):
            raise GuardError("wire-harness receipt target is invalid")
        relative = safe_relative(item.get("path"), "receipt target")
        if sha256(read_bytes(reject_symlink_chain(root, relative, allow_missing=True))) != item.get("sha256"):
            raise GuardError("modified harness files do not match the last receipt")
        allowed.add(relative)
    return allowed


def onboarding_artifact_token(root: Path) -> str:
    digest = hashlib.sha256()
    for name in ONBOARDING_ARTIFACTS:
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update(sha256(read_bytes(root / ".specs" / name)).encode())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def onboarding_allowed_changes(root: Path, paths: dict[str, Path]) -> set[str]:
    del paths
    worktree_git_dir = Path(
        run_git(root, "rev-parse", "--absolute-git-dir").decode().strip()
    ).resolve(strict=True)
    receipt_path = worktree_git_dir / "sdd-onboarding.commit.json"
    receipt = load_optional_json(receipt_path, "onboarding receipt")
    if receipt is None:
        return set()
    if (
        receipt.get("version") != 1
        or receipt.get("operation") != "commit-onboarding"
        or receipt.get("target_artifact_token") != onboarding_artifact_token(root)
    ):
        raise GuardError("pending onboarding artifacts do not match their receipt")
    return {f".specs/{name}" for name in ONBOARDING_ARTIFACTS}


def validate_workspace(root: Path, paths: dict[str, Path]) -> list[dict[str, str]]:
    changes = parse_status(root)
    staged = [path for status, path in changes if status[0] not in {" ", "?"}]
    if staged:
        raise GuardError("staged worktree changes are refused: " + ", ".join(staged))
    if not changes:
        return []
    allowed = receipt_allowed_changes(root, paths) | onboarding_allowed_changes(root, paths)
    unrelated = [path for _status, path in changes if path not in allowed]
    if unrelated:
        raise GuardError("worktree contains changes outside the last harness receipt: " + ", ".join(unrelated))
    return [{"status": status, "path": path} for status, path in changes]


def snapshot_token(root: Path, stack: dict[str, Any]) -> str:
    head = run_git(root, "rev-parse", "HEAD").decode().strip()
    status = run_git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    return sha256(head.encode() + b"\0" + canonical_json(stack) + b"\0" + status)


def inspect(root: Path, paths: dict[str, Path], feature_id: str | None) -> dict[str, Any]:
    if feature_id is not None:
        feature_path = root / ".specs" / feature_id
        if feature_path.is_symlink() or not feature_path.is_dir():
            raise GuardError(f"feature artefact directory is missing or symbolic: .specs/{feature_id}")
    stack, detected = detect_stacks(root)
    changes = validate_workspace(root, paths)
    return {
        "status": "inspected",
        "git_sha": run_git(root, "rev-parse", "HEAD").decode().strip(),
        "snapshot_token": snapshot_token(root, stack),
        "feature_id": feature_id,
        "stacks": detected,
        "allowed_targets": sorted(allowed_targets(detected)),
        "workspace_changes": changes,
    }


def check_secrets(data: bytes, label: str) -> str:
    if len(data) > MAX_FILE_BYTES or b"\0" in data:
        raise GuardError(f"{label} must be UTF-8 text smaller than {MAX_FILE_BYTES} bytes")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise GuardError(f"{label} must be UTF-8 text") from error
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            raise GuardError(f"potential secret refused in {label}")
    if SCRIPT_SECRET_RE.search(text):
        raise GuardError(f"potential script credential refused in {label}")
    reject_indirect_script_secrets(text, label)
    return text


def reject_indirect_script_secrets(text: str, label: str) -> None:
    """Reject simple JavaScript/TypeScript credential aliases without executing code."""
    if not re.search(r"(?:\.m?[cm]?[jt]sx?$|package\.json#scripts\.)", label):
        return
    literals: dict[str, str] = {}
    literal_assignment = re.compile(
        r"(?m)\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*"
        r"((?:[\"'][^\"'\r\n]*[\"'])(?:\s*\+\s*[\"'][^\"'\r\n]*[\"'])*)\s*;?"
    )
    for match in literal_assignment.finditer(text):
        pieces = re.findall(r"[\"']([^\"'\r\n]*)[\"']", match.group(2))
        literals[match.group(1)] = "".join(pieces)
    sensitive = (
        r"(?:password|passwd|token|api[_-]?key|apikey|secret|client[_-]?secret|"
        r"private[_-]?key|access[_-]?(?:key|token)|credentials?)"
    )
    alias_patterns = (
        re.compile(
            rf"(?i)\b(?:const|let|var)?\s*{sensitive}\s*=\s*"
            r"([A-Za-z_$][\w$]*)\b"
        ),
        re.compile(
            rf"(?i)[\"']?{sensitive}[\"']?\s*:\s*([A-Za-z_$][\w$]*)\b"
        ),
    )
    for pattern in alias_patterns:
        for match in pattern.finditer(text):
            value = literals.get(match.group(1))
            if value and len(value) >= 8 and not PLACEHOLDER_RE.fullmatch(value):
                raise GuardError(f"potential indirect script credential refused in {label}")


def reject_xml_secrets(root: ET.Element, relative: str) -> None:
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        sensitive = bool(SENSITIVE_KEY_RE.fullmatch(tag))
        for key, value in element.attrib.items():
            local_key = key.rsplit("}", 1)[-1]
            if local_key.casefold() in {"name", "key"} and SENSITIVE_KEY_RE.fullmatch(value):
                sensitive = True
            elif SENSITIVE_KEY_RE.fullmatch(local_key):
                if not PLACEHOLDER_RE.fullmatch(value):
                    raise GuardError(f"potential XML secret refused in {relative}")
        if sensitive:
            values = [element.text or ""] + [
                value
                for key, value in element.attrib.items()
                if key.rsplit("}", 1)[-1].casefold() in {"value", "content"}
            ]
            for value in values:
                stripped = value.strip()
                if stripped and not PLACEHOLDER_RE.fullmatch(stripped):
                    raise GuardError(f"potential XML secret refused in {relative}")


def json_added_paths(previous: object, candidate: object, trail: str = "$") -> list[str]:
    if not isinstance(previous, dict) or not isinstance(candidate, dict):
        return []
    additions: list[str] = []
    for key, value in candidate.items():
        path = f"{trail}.{key}"
        if key not in previous:
            additions.append(path)
        else:
            additions.extend(json_added_paths(previous[key], value, path))
    return additions


def xml_inventory(root: ET.Element) -> dict[str, set[tuple[str, ...]]]:
    def local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    dependencies: set[tuple[str, ...]] = set()
    plugins: set[tuple[str, ...]] = set()
    properties: set[tuple[str, ...]] = set()
    profiles: set[tuple[str, ...]] = set()
    modules: set[tuple[str, ...]] = set()
    xml_properties: set[tuple[str, ...]] = set()
    parents: set[tuple[str, ...]] = set()
    leaf_elements: set[tuple[str, ...]] = set()
    for element in root.iter():
        name = local(element.tag)
        children = {local(child.tag): (child.text or "").strip() for child in element}
        if name == "dependency" and children.get("artifactId"):
            dependencies.add((children.get("groupId", ""), children["artifactId"], children.get("version", "")))
        elif name == "plugin" and children.get("artifactId"):
            plugins.add((children.get("groupId", ""), children["artifactId"], children.get("version", "")))
        elif name == "profile" and children.get("id"):
            profiles.add((children["id"],))
        elif name == "parent" and children.get("artifactId"):
            parents.add((children.get("groupId", ""), children["artifactId"], children.get("version", "")))
        elif name == "module" and (element.text or "").strip():
            modules.add(((element.text or "").strip(),))
        elif name == "property" and children.get("name"):
            xml_properties.add((children["name"], children.get("value", "")))
        if len(element) == 0:
            leaf_elements.add(
                (
                    name,
                    json.dumps(sorted(element.attrib.items()), separators=(",", ":")),
                    (element.text or "").strip(),
                )
            )
    for properties_node in root.iter():
        if local(properties_node.tag) == "properties":
            for child in properties_node:
                properties.add((local(child.tag), (child.text or "").strip()))
    return {
        "dependencies": dependencies,
        "plugins": plugins,
        "properties": properties,
        "profiles": profiles,
        "modules": modules,
        "xml_properties": xml_properties,
        "parents": parents,
        "leaf_elements": leaf_elements,
    }


def maven_added_coordinates(before: bytes | None, after_root: ET.Element) -> list[str]:
    if before is None:
        previous = {"dependencies": set(), "plugins": set()}
    else:
        try:
            before_root = ET.fromstring(before.decode("utf-8"))
        except (UnicodeDecodeError, ET.ParseError) as error:
            raise GuardError(f"existing Maven XML cannot be compared safely: {error}") from error
        previous = xml_inventory(before_root)
    candidate = xml_inventory(after_root)
    additions: list[str] = []
    for category in ("dependencies", "plugins"):
        for coordinate in candidate[category] - previous[category]:
            additions.append(f"maven.{category}[{':'.join(coordinate)}]")
    return sorted(additions)


def preserve_xml_configuration(relative: str, before: bytes, after_root: ET.Element) -> None:
    try:
        before_root = ET.fromstring(before.decode("utf-8"))
    except (UnicodeDecodeError, ET.ParseError) as error:
        raise GuardError(f"existing XML cannot be safely preserved for {relative}: {error}") from error
    previous = xml_inventory(before_root)
    candidate = xml_inventory(after_root)
    for category, values in previous.items():
        missing = values - candidate[category]
        if missing:
            raise GuardError(f"candidate removes or changes existing {category} in {relative}")
    before_text = before.decode("utf-8", "replace")
    after_text = ET.tostring(after_root, encoding="unicode")
    for migration in ("flyway", "liquibase"):
        if migration in before_text.casefold() and migration not in after_text.casefold():
            raise GuardError(f"candidate removes existing {migration} configuration in {relative}")


def preserve_package_json(relative: str, before: bytes, candidate: dict[str, Any]) -> None:
    try:
        previous = json.loads(before)
    except json.JSONDecodeError as error:
        raise GuardError(f"existing package.json is invalid: {error}") from error
    if not isinstance(previous, dict):
        raise GuardError("existing package.json must be an object")
    for section in (
        "dependencies",
        "devDependencies",
        "peerDependencies",
        "optionalDependencies",
        "scripts",
        "engines",
    ):
        old = previous.get(section, {})
        new = candidate.get(section, {})
        if old is None:
            old = {}
        if not isinstance(old, dict) or not isinstance(new, dict):
            raise GuardError(f"candidate changes {section} shape in {relative}")
        for key, value in old.items():
            if key not in new or new[key] != value:
                raise GuardError(f"candidate removes or changes existing {section}.{key}")
    for scalar in ("name", "version", "private", "type", "packageManager"):
        if scalar in previous and candidate.get(scalar) != previous[scalar]:
            raise GuardError(f"candidate changes existing {scalar} in {relative}")


def preserve_json_value(relative: str, previous: object, candidate: object, trail: str = "$") -> None:
    if isinstance(previous, dict):
        if not isinstance(candidate, dict):
            raise GuardError(f"candidate changes JSON shape at {relative}:{trail}")
        for key, value in previous.items():
            if key not in candidate:
                raise GuardError(f"candidate removes JSON key at {relative}:{trail}.{key}")
            preserve_json_value(relative, value, candidate[key], f"{trail}.{key}")
    elif candidate != previous:
        raise GuardError(f"candidate changes existing JSON value at {relative}:{trail}")


def preserve_text_configuration(relative: str, before: bytes, after: str) -> None:
    try:
        previous = before.decode("utf-8")
    except UnicodeDecodeError as error:
        raise GuardError(f"existing configuration is not UTF-8: {relative}") from error
    required_lines = [
        line.strip()
        for line in previous.splitlines()
        if line.strip() and not line.lstrip().startswith(("#", "//"))
    ]
    candidate_lines = [line.strip() for line in after.splitlines()]
    position = 0
    for required in required_lines:
        try:
            position = candidate_lines.index(required, position) + 1
        except ValueError as error:
            raise GuardError(f"candidate removes or reorders existing configuration in {relative}") from error


def validate_harness_script(text: str) -> None:
    """Accept only declarative, single-command build/test lines in harness.sh."""
    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            tokens = shlex.split(line, posix=True)
        except ValueError as error:
            raise GuardError(f"unparseable harness.sh line {number}") from error
        if not tokens:
            continue
        if any(
            any(character in token for character in (";", "|", "&", "`", "<", ">", "$", "(", ")"))
            for token in tokens
        ):
            raise GuardError(f"shell composition refused in harness.sh line {number}")
        if any(
            PurePosixPath(token).is_absolute()
            or re.match(r"^[A-Za-z]:[\\/]", token)
            or ".." in PurePosixPath(token).parts
            or "://" in token
            for token in tokens[1:]
        ):
            raise GuardError(f"absolute, escaping, or network token refused in harness.sh line {number}")
        executable = tokens[0]
        if executable == "set" and all(re.fullmatch(r"-[euxo]+", item) or item == "pipefail" for item in tokens[1:]):
            continue
        if executable == "cd" and len(tokens) == 2:
            continue
        if executable in {"mvn", "./mvnw"}:
            if "verify" in tokens and ({"--offline", "-o"} & set(tokens)) and all(
                item in SAFE_MAVEN_ARGUMENTS for item in tokens[1:]
            ):
                continue
        elif executable == "npm":
            if len(tokens) == 3 and tokens[1] == "run" and tokens[2] in {"lint", "typecheck", "test", "build"}:
                continue
        elif executable in {"pnpm", "yarn"}:
            if (len(tokens) == 2 or (len(tokens) == 3 and tokens[1] == "run")) and tokens[-1] in {
                "lint", "typecheck", "test", "build"
            }:
                continue
        elif executable == "bun":
            if len(tokens) == 3 and tokens[1] == "run" and tokens[2] in {"lint", "typecheck", "test", "build"}:
                continue
        raise GuardError(f"harness.sh line {number} is outside the command allowlist")


def validate_config(relative: str, before: bytes | None, data: bytes) -> None:
    text = check_secrets(data, relative)
    name = PurePosixPath(relative).name
    if name in {"pom.xml", "checkstyle.xml", "dependency-check-suppressions.xml"}:
        try:
            parsed_xml = ET.fromstring(text)
        except ET.ParseError as error:
            raise GuardError(f"invalid XML candidate {relative}: {error}") from error
        reject_xml_secrets(parsed_xml, relative)
        if before is not None:
            preserve_xml_configuration(relative, before, parsed_xml)
    elif name in {"package.json", "tsconfig.json"}:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as error:
            raise GuardError(f"invalid JSON candidate {relative}: {error}") from error
        if not isinstance(parsed, dict):
            raise GuardError(f"JSON candidate {relative} must be an object")
        if name == "package.json" and before is not None:
            preserve_package_json(relative, before, parsed)
            preserve_json_value(relative, json.loads(before), parsed)
        elif name == "tsconfig.json" and before is not None:
            preserve_json_value(relative, json.loads(before), parsed)
        def reject_sensitive(value: object, trail: str = "$") -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if isinstance(key, str) and SENSITIVE_KEY_RE.search(key):
                        if not isinstance(child, str) or not PLACEHOLDER_RE.fullmatch(child):
                            raise GuardError(f"potential secret refused at {relative}:{trail}.{key}")
                    reject_sensitive(child, f"{trail}.{key}")
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    reject_sensitive(child, f"{trail}[{index}]")
        reject_sensitive(parsed)
    elif name == "harness.sh":
        if not text.startswith("#!/"):
            raise GuardError("harness.sh candidate must start with a shebang")
        if DEPLOY_WORDS.search(text):
            raise GuardError("deployment command refused in harness.sh")
        if DANGEROUS_HARNESS_RE.search(text):
            raise GuardError("dangerous or network command refused in harness.sh")
        validate_harness_script(text)
        if before is not None:
            preserve_text_configuration(relative, before, text)
    elif before is not None:
        preserve_text_configuration(relative, before, text)


def validate_command(command: object, detected: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(command, dict):
        raise GuardError("validation entries must be objects")
    stack = command.get("stack")
    argv = command.get("argv")
    workdir = command.get("working_directory", ".")
    phase = command.get("phase")
    timeout_seconds = command.get("timeout_seconds", 900)
    if phase not in {"pre-commit", "post-commit"}:
        raise GuardError("validation phase must be pre-commit or post-commit")
    if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 3600:
        raise GuardError("validation timeout_seconds must be between 1 and 3600")
    if stack not in {item["stack"] for item in detected}:
        raise GuardError("validation command references an unproved stack")
    if not isinstance(argv, list) or not argv or not all(isinstance(item, str) and item for item in argv):
        raise GuardError("validation argv must be a non-empty string array")
    if not isinstance(workdir, str):
        raise GuardError("validation working_directory must be a string")
    normalized_workdir = "." if workdir == "." else safe_relative(workdir, "validation working_directory")
    for index, argument in enumerate(argv):
        lowered = argument.casefold()
        if any(value in lowered for value in FORBIDDEN_COMMAND_PARTS):
            raise GuardError(f"test-bypass argument refused: {argument}")
        if any(
            character in argument
            for character in ("\n", "\r", "\0", ";", "|", "&", "`", "<", ">", "$", "(", ")")
        ):
            raise GuardError(f"shell metacharacter refused in argv: {argument!r}")
        if index > 0 and (
            PurePosixPath(argument).is_absolute()
            or re.match(r"^[A-Za-z]:[\\/]", argument)
            or ".." in PurePosixPath(argument).parts
            or "://" in argument
        ):
            raise GuardError(f"absolute, escaping, or network argument refused: {argument}")
    rendered = " ".join(argv)
    if DEPLOY_WORDS.search(rendered):
        raise GuardError("deployment command refused")
    executable = PurePosixPath(argv[0]).name
    matching_modules = {
        item["module"] for item in detected if item["stack"] == stack
    }
    if normalized_workdir not in matching_modules:
        raise GuardError("validation working_directory does not match its proved module")
    if stack == "spring":
        if argv[0] not in {"mvn", "./mvnw"} or executable not in {"mvn", "mvnw"}:
            raise GuardError("Spring validation must use mvn or the local ./mvnw")
        if "verify" not in argv or not ({"--offline", "-o"} & set(argv)):
            raise GuardError("Spring validation must run Maven verify in offline mode")
        unexpected = [argument for argument in argv[1:] if argument not in SAFE_MAVEN_ARGUMENTS]
        if unexpected:
            raise GuardError(f"unsupported Maven validation arguments: {unexpected}")
    else:
        matching_managers = {
            item.get("package_manager")
            for item in detected
            if item["stack"] == stack and item["module"] == normalized_workdir
        }
        if argv[0] not in matching_managers or executable != argv[0]:
            raise GuardError("React/Next.js validation must use its proved package manager")
        if argv[0] == "npm":
            valid_shape = len(argv) == 3 and argv[1] == "run"
            script_name = argv[2] if valid_shape else None
        elif argv[0] in {"pnpm", "yarn"}:
            valid_shape = len(argv) == 2 or (len(argv) == 3 and argv[1] == "run")
            script_name = argv[-1] if valid_shape else None
        else:
            valid_shape = len(argv) == 3 and argv[1] == "run"
            script_name = argv[2] if valid_shape else None
        if not valid_shape or script_name not in {"lint", "typecheck", "test", "build"}:
            raise GuardError("React/Next.js validation must name a configured gate")
    return {
        "stack": stack,
        "phase": phase,
        "argv": argv,
        "working_directory": normalized_workdir,
        "timeout_seconds": timeout_seconds,
    }


def validate_plan(
    root: Path,
    inspection: dict[str, Any],
    plan_path: Path,
    candidate_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], str]:
    if plan_path.is_symlink() or not plan_path.is_file():
        raise GuardError("plan must be a real JSON file")
    if candidate_dir.is_symlink() or not candidate_dir.is_dir():
        raise GuardError("candidate-dir must be a real directory")
    candidate_dir = candidate_dir.resolve(strict=True)
    try:
        candidate_dir.relative_to(root)
    except ValueError:
        pass
    else:
        raise GuardError("candidate-dir must be outside the project repository")
    plan = load_json(plan_path, "harness plan")
    if plan.get("schema_version") != 1:
        raise GuardError("harness plan schema_version must be 1")
    for key in ("git_sha", "snapshot_token", "feature_id"):
        if plan.get(key) != inspection.get(key):
            raise GuardError(f"harness plan {key} does not match the inspection")
    changes = plan.get("changes")
    if not isinstance(changes, list) or not changes:
        raise GuardError("harness plan must contain at least one change")
    allowed = allowed_targets(inspection["stacks"])
    validated: list[dict[str, Any]] = []
    seen: set[str] = set()
    for change in changes:
        if not isinstance(change, dict):
            raise GuardError("plan changes must be objects")
        relative = safe_relative(change.get("path"), "change path")
        candidate_relative = safe_relative(change.get("candidate"), "candidate path")
        if relative in seen:
            raise GuardError(f"duplicate target refused: {relative}")
        seen.add(relative)
        stack_name = change.get("stack")
        if relative not in allowed or stack_name not in allowed[relative]:
            raise GuardError(f"target is outside the authorized harness configuration: {relative}")
        if change.get("action") not in {"create", "replace"}:
            raise GuardError("only create and replace actions are allowed")
        purpose = change.get("purpose")
        if not isinstance(purpose, str) or not purpose.strip():
            raise GuardError("every change requires a non-empty purpose")
        target = reject_symlink_chain(root, relative, allow_missing=True)
        before = read_bytes(target)
        expected_before = change.get("expected_before_sha256")
        if expected_before != sha256(before):
            raise GuardError(f"CAS fingerprint changed for {relative}")
        if change["action"] == "create" and before is not None:
            raise GuardError(f"create target already exists: {relative}")
        if change["action"] == "replace" and before is None:
            raise GuardError(f"replace target is absent: {relative}")
        candidate = reject_symlink_chain(candidate_dir, candidate_relative, allow_missing=False)
        if not candidate.is_file():
            raise GuardError(f"candidate must be a real file: {candidate_relative}")
        after = candidate.read_bytes()
        validate_config(relative, before, after)
        additions: list[str] = []
        addition_kind: str | None = None
        if relative.endswith("package.json") and before is not None:
            additions = sorted(json_added_paths(json.loads(before), json.loads(after)))
            addition_kind = "package.json"
        elif PurePosixPath(relative).name == "pom.xml":
            try:
                after_xml = ET.fromstring(after.decode("utf-8"))
            except (UnicodeDecodeError, ET.ParseError) as error:
                raise GuardError(f"invalid Maven XML candidate {relative}: {error}") from error
            additions = maven_added_coordinates(before, after_xml)
            addition_kind = "Maven dependency/plugin"
        if addition_kind is not None:
            declared_additions = change.get("approved_additions", [])
            if not isinstance(declared_additions, list) or not all(
                isinstance(item, str) for item in declared_additions
            ):
                raise GuardError("approved_additions must be a string array")
            if sorted(declared_additions) != additions:
                raise GuardError(
                    f"{addition_kind} additions require an exact approved_additions list"
                )
            if additions:
                evidence = change.get("approval_evidence")
                if not isinstance(evidence, str) or not evidence.startswith("user:"):
                    raise GuardError(
                        f"{addition_kind} additions require explicit user approval evidence"
                    )
        if change.get("expected_after_sha256") != sha256(after):
            raise GuardError(f"candidate fingerprint mismatch for {relative}")
        mode = 0o755 if relative == ".github/scripts/harness.sh" else 0o644
        validated.append(
            {
                "path": relative,
                "target": target,
                "before": before,
                "before_mode": stat.S_IMODE(target.stat().st_mode) if before is not None else None,
                "after": after,
                "after_mode": mode,
                "stack": stack_name,
                "purpose": purpose.strip(),
            }
        )
    validations = plan.get("validation")
    if not isinstance(validations, list) or not validations:
        raise GuardError("harness plan must contain structured validation commands")
    normalized_commands = [validate_command(item, inspection["stacks"]) for item in validations]
    required_gates = {
        (item["stack"], item["module"], phase)
        for item in inspection["stacks"]
        for phase in ("pre-commit", "post-commit")
    }
    actual_gates = {
        (item["stack"], item["working_directory"], item["phase"])
        for item in normalized_commands
    }
    missing_gates = sorted(required_gates - actual_gates)
    if missing_gates:
        raise GuardError(f"missing serialized validation gates: {missing_gates}")
    for stack_item in inspection["stacks"]:
        signatures: dict[str, list[tuple[tuple[str, ...], str, int]]] = {
            "pre-commit": [],
            "post-commit": [],
        }
        for command in normalized_commands:
            if (
                command["stack"] == stack_item["stack"]
                and command["working_directory"] == stack_item["module"]
            ):
                signatures[command["phase"]].append(
                    (
                        tuple(command["argv"]),
                        command["working_directory"],
                        command["timeout_seconds"],
                    )
                )
        if signatures["pre-commit"] != signatures["post-commit"]:
            raise GuardError("pre-commit and post-commit gate commands must be identical")
    plan_digest = sha256(canonical_json(plan))
    return plan, validated, normalized_commands, plan_digest


def receipt_matches(paths: dict[str, Path], plan_digest: str, entries: list[dict[str, Any]]) -> bool:
    receipt = load_optional_json(paths["receipt"], "wire-harness receipt")
    if receipt is None or receipt.get("plan_digest") != plan_digest:
        return False
    return all(sha256(read_bytes(entry["target"])) == sha256(entry["after"]) for entry in entries)


def idempotent_replay(
    root: Path,
    paths: dict[str, Path],
    plan_path: Path,
    candidate_dir: Path,
    expected_head: str,
    feature_id: str | None,
) -> dict[str, Any] | None:
    if plan_path.is_symlink() or not plan_path.is_file():
        raise GuardError("plan must be a real JSON file")
    if candidate_dir.is_symlink() or not candidate_dir.is_dir():
        raise GuardError("candidate-dir must be a real directory")
    candidate_dir = candidate_dir.resolve(strict=True)
    plan = load_json(plan_path, "harness plan")
    if (
        plan.get("schema_version") != 1
        or plan.get("git_sha") != expected_head
        or plan.get("feature_id") != feature_id
    ):
        return None
    plan_digest = sha256(canonical_json(plan))
    receipt = load_optional_json(paths["receipt"], "wire-harness receipt")
    if receipt is None or receipt.get("plan_digest") != plan_digest:
        return None
    changes = plan.get("changes")
    targets = receipt.get("targets")
    if not isinstance(changes, list) or not isinstance(targets, list) or len(changes) != len(targets):
        raise GuardError("idempotent receipt does not match plan targets")
    receipt_map = {
        safe_relative(item.get("path"), "receipt target"): item.get("sha256")
        for item in targets
        if isinstance(item, dict)
    }
    summaries: list[dict[str, Any]] = []
    for change in changes:
        if not isinstance(change, dict):
            raise GuardError("idempotent plan change is invalid")
        relative = safe_relative(change.get("path"), "change path")
        candidate_relative = safe_relative(change.get("candidate"), "candidate path")
        expected_after = change.get("expected_after_sha256")
        if receipt_map.get(relative) != expected_after:
            raise GuardError("idempotent receipt hash does not match plan")
        target = reject_symlink_chain(root, relative, allow_missing=False)
        candidate = reject_symlink_chain(candidate_dir, candidate_relative, allow_missing=False)
        current, proposed = target.read_bytes(), candidate.read_bytes()
        if sha256(current) != expected_after or sha256(proposed) != expected_after:
            raise GuardError("idempotent replay target or candidate changed")
        validate_config(relative, current, proposed)
        summaries.append(
            {
                "path": relative,
                "stack": change.get("stack"),
                "purpose": change.get("purpose"),
                "before_sha256": change.get("expected_before_sha256"),
                "after_sha256": expected_after,
            }
        )
    return {
        "status": "committed",
        "unchanged": True,
        "git_sha": expected_head,
        "feature_id": feature_id,
        "plan_digest": plan_digest,
        "changes": summaries,
        "targets": sorted(receipt_map),
    }


def restore_entry(
    entry: dict[str, Any], payload_key: str, root: Path | None = None
) -> None:
    path = Path(entry["absolute_path"])
    data, mode = decode_payload(entry[payload_key], f"journal {payload_key}")
    if path.is_symlink():
        raise GuardError(f"symbolic transaction target refused: {entry['path']}")
    if data is None:
        remove_file(path)
        if payload_key == "before" and root is not None:
            for relative in entry.get("created_parents", []):
                directory = reject_symlink_chain(root, relative, allow_missing=True)
                try:
                    directory.rmdir()
                except FileNotFoundError:
                    continue
                except OSError:
                    break
                fsync_directory(directory.parent)
    else:
        atomic_replace(path, data, mode or 0o644)


def write_receipt(paths: dict[str, Path], journal: dict[str, Any]) -> None:
    target_map: dict[str, str] = {}
    previous = load_optional_json(paths["receipt"], "wire-harness receipt")
    if previous is not None and isinstance(previous.get("targets"), list):
        for item in previous["targets"]:
            if isinstance(item, dict) and isinstance(item.get("path"), str) and isinstance(item.get("sha256"), str):
                target_map[item["path"]] = item["sha256"]
    for entry in journal["entries"]:
        if sha256(read_bytes(Path(entry["absolute_path"]))) != entry["after_sha256"]:
            raise GuardError(f"cannot receipt mismatched target: {entry['path']}")
        target_map[entry["path"]] = entry["after_sha256"]
    receipt = {
        "version": 1,
        "operation": "wire-harness-commit",
        "git_sha": journal["git_sha"],
        "feature_id": journal.get("feature_id"),
        "plan_digest": journal["plan_digest"],
        "targets": [
            {"path": path, "sha256": digest}
            for path, digest in sorted(target_map.items())
        ],
    }
    atomic_replace(paths["receipt"], json.dumps(receipt, indent=2).encode() + b"\n", 0o600)


def recover(root: Path, paths: dict[str, Path], *, dry_run: bool) -> str | None:
    journal = load_optional_json(paths["journal"], "wire-harness journal")
    if journal is None:
        return None
    if dry_run:
        raise GuardError("pending transaction requires non-dry recovery before dry-run")
    if journal.get("version") != 1 or journal.get("operation") != "wire-harness-commit":
        raise GuardError("wire-harness journal has an unsupported schema")
    entries = journal.get("entries")
    if not isinstance(entries, list) or not entries:
        raise GuardError("wire-harness journal entries are invalid")
    _stack, detected = detect_stacks(root, require_current_head=False)
    allowed = allowed_targets(detected)
    seen_targets: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise GuardError("wire-harness journal entry is invalid")
        relative = safe_relative(entry.get("path"), "journal target")
        stack_name = entry.get("stack")
        if relative in seen_targets:
            raise GuardError("duplicate wire-harness journal target")
        seen_targets.add(relative)
        if relative not in allowed or stack_name not in allowed[relative]:
            raise GuardError("wire-harness journal target is outside the current stack allowlist")
        expected_path = reject_symlink_chain(root, relative, allow_missing=True)
        if Path(entry.get("absolute_path", "")) != expected_path:
            raise GuardError("wire-harness journal target does not match this worktree")
        created_parents = entry.get("created_parents", [])
        if not isinstance(created_parents, list):
            raise GuardError("wire-harness journal created_parents is invalid")
        valid_parents = {
            parent.as_posix()
            for parent in PurePosixPath(relative).parents
            if parent.as_posix() != "."
        }
        for relative_parent in created_parents:
            normalized_parent = safe_relative(relative_parent, "journal created parent")
            if normalized_parent not in valid_parents:
                raise GuardError("journal created parent is not an ancestor of its target")
        before_data, _before_mode = decode_payload(entry.get("before"), "journal before")
        after_data, _after_mode = decode_payload(entry.get("after"), "journal after")
        if sha256(before_data) != entry.get("before_sha256"):
            raise GuardError("wire-harness journal before payload hash is invalid")
        if sha256(after_data) != entry.get("after_sha256"):
            raise GuardError("wire-harness journal after payload hash is invalid")
    if journal.get("state") == "committed":
        for entry in entries:
            restore_entry(entry, "after")
        journal["state"] = "committed"
        atomic_replace(paths["journal"], json.dumps(journal, indent=2).encode() + b"\n", 0o600)
        write_receipt(paths, journal)
        remove_file(paths["journal"])
        return "committed"
    for entry in entries:
        restore_entry(entry, "before", root)
    remove_file(paths["journal"])
    return "rolled-back"


def archive_checkout(root: Path, destination: Path) -> None:
    archive = run_git(root, "archive", "--format=tar", "HEAD")
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as stream:
        for member in stream.getmembers():
            relative = safe_relative(member.name.rstrip("/"), "Git archive member")
            target = destination / relative
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise GuardError(f"symbolic or special Git archive member refused: {relative}")
            source = stream.extractfile(member)
            if source is None:
                raise GuardError(f"cannot read Git archive member: {relative}")
            data = source.read(MAX_FILE_BYTES + 1)
            if len(data) > MAX_FILE_BYTES:
                raise GuardError(f"Git archive file exceeds safety limit: {relative}")
            atomic_replace(target, data, stat.S_IMODE(member.mode) or 0o644)


def copy_node_dependencies(
    root: Path, workspace: Path, commands: list[dict[str, Any]]
) -> None:
    modules = {
        command["working_directory"]
        for command in commands
        if command["stack"] in {"nextjs", "react"}
    }
    for module in modules:
        source_module = root if module == "." else root / module
        source = source_module / "node_modules"
        if source.is_symlink() or not source.is_dir():
            raise GuardError(
                f"existing dependencies are required before Node gates: {module}/node_modules"
            )
        source_real = source.resolve(strict=True)
        for directory, directory_names, file_names in os.walk(source, followlinks=False):
            for name in directory_names + file_names:
                path = Path(directory) / name
                if not path.is_symlink():
                    continue
                target = path.resolve(strict=True)
                try:
                    target.relative_to(source_real)
                except ValueError as error:
                    raise GuardError(
                        f"node_modules symlink escapes dependency tree: {path.relative_to(root)}"
                    ) from error
        destination_module = workspace if module == "." else workspace / module
        destination = destination_module / "node_modules"
        shutil.copytree(source, destination, symlinks=True, dirs_exist_ok=True)


def validate_node_script(workspace: Path, command: dict[str, Any]) -> None:
    if command["stack"] not in {"nextjs", "react"}:
        return
    package_path = workspace / command["working_directory"] / "package.json"
    package = load_json(package_path, "gate package.json")
    argv = command["argv"]
    script_name: str | None = None
    if PurePosixPath(argv[0]).name == "npm" and len(argv) >= 3 and argv[1] == "run":
        script_name = argv[2]
    elif len(argv) >= 2:
        script_name = argv[1]
    scripts = package.get("scripts")
    if not isinstance(scripts, dict) or not isinstance(scripts.get(script_name), str):
        raise GuardError(f"configured Node gate script is absent: {script_name}")
    visited: set[str] = set()

    def inspect_script(name: str) -> None:
        if name in visited:
            return
        visited.add(name)
        script_value = scripts.get(name)
        if not isinstance(script_value, str):
            return
        if DEPLOY_WORDS.search(script_value) or DANGEROUS_HARNESS_RE.search(script_value):
            raise GuardError(f"dangerous or network command refused in package script {name}")
        check_secrets(script_value.encode(), f"package.json#scripts.{name}")
        try:
            tokens = shlex.split(script_value, posix=True)
        except ValueError as error:
            raise GuardError(f"unparseable package script refused: {name}") from error
        if not tokens:
            raise GuardError(f"empty package script refused: {name}")
        for token in tokens:
            if (
                any(character in token for character in (";", "|", "&", "`", "<", ">", "$", "(", ")"))
                or PurePosixPath(token).is_absolute()
                or re.match(r"^[A-Za-z]:[\\/]", token)
                or ".." in PurePosixPath(token).parts
                or "://" in token
            ):
                raise GuardError(f"shell, absolute, escaping, or network token refused in package script {name}")
        executable = tokens[0]
        if "/" in executable or "\\" in executable:
            raise GuardError(f"path-based package script executable refused: {name}")
        if executable in NODE_SCRIPT_RUNNERS:
            if executable == "npm":
                valid_shape = len(tokens) == 3 and tokens[1] == "run"
                nested = tokens[2] if valid_shape else None
            elif executable in {"pnpm", "yarn"}:
                valid_shape = len(tokens) == 2 or (len(tokens) == 3 and tokens[1] == "run")
                nested = tokens[-1] if valid_shape else None
            else:
                valid_shape = len(tokens) == 3 and tokens[1] == "run"
                nested = tokens[2] if valid_shape else None
            if not valid_shape or not re.fullmatch(r"[A-Za-z0-9:._-]+", nested or ""):
                raise GuardError(f"unsupported nested package script invocation: {name}")
            inspect_script(nested)
        elif executable not in SAFE_NODE_SCRIPT_COMMANDS:
            raise GuardError(
                f"package script executable is outside the validation allowlist: {executable}"
            )

    for lifecycle_name in (f"pre{script_name}", script_name, f"post{script_name}"):
        inspect_script(lifecycle_name)


def execute_gates(
    workspace: Path,
    commands: list[dict[str, Any]],
    phase: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="sdd-wire-harness-home-") as gate_home:
        environment = {
            key: value
            for key, value in os.environ.items()
            if key in {"PATH", "JAVA_HOME", "MAVEN_HOME", "LANG", "LC_ALL"}
        }
        environment["CI"] = "true"
        environment["HOME"] = gate_home
        environment["SDD_HARNESS_GATE_PHASE"] = phase
        for command in commands:
            if command["phase"] != phase:
                continue
            validate_node_script(workspace, command)
            directory = workspace if command["working_directory"] == "." else workspace / command["working_directory"]
            if directory.is_symlink() or not directory.is_dir():
                raise GuardError("gate working directory is missing or symbolic")
            executable = command["argv"][0]
            if executable.startswith("./"):
                executable_path = directory / executable[2:]
                if executable_path.is_symlink() or not executable_path.is_file():
                    raise GuardError(f"gate executable is missing or symbolic: {executable}")
            elif shutil.which(executable, path=environment.get("PATH")) is None:
                raise GuardError(f"gate executable is not available on PATH: {executable}")
            before = time.monotonic()
            try:
                completed = subprocess.run(
                    command["argv"],
                    cwd=directory,
                    env=environment,
                    check=False,
                    capture_output=True,
                    timeout=command["timeout_seconds"],
                )
            except (OSError, subprocess.TimeoutExpired) as error:
                raise GuardError(f"{phase} gate could not complete: {error}") from error
            output = completed.stdout + completed.stderr
            result = {
                "stack": command["stack"],
                "working_directory": command["working_directory"],
                "phase": phase,
                "argv": command["argv"],
                "exit_code": completed.returncode,
                "duration_ms": int((time.monotonic() - before) * 1000),
                "output_sha256": sha256(output),
            }
            results.append(result)
            if completed.returncode != 0:
                raise GuardError(
                    f"{phase} gate failed for {command['stack']} in "
                    f"{command['working_directory']} with exit {completed.returncode}; "
                    f"output {result['output_sha256']}"
                )
    return results


def run_sandbox_gates(
    root: Path,
    paths: dict[str, Path],
    entries: list[dict[str, Any]],
    commands: list[dict[str, Any]],
    phase: str,
) -> list[dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="sdd-wire-harness-gate-") as temporary:
        workspace = Path(temporary) / "project"
        workspace.mkdir()
        archive_checkout(root, workspace)
        pending = receipt_allowed_changes(root, paths) | onboarding_allowed_changes(root, paths)
        for relative in sorted(pending):
            source = reject_symlink_chain(root, relative, allow_missing=False)
            data = source.read_bytes()
            if len(data) > MAX_FILE_BYTES:
                raise GuardError(f"pending safe file exceeds size limit: {relative}")
            target = reject_symlink_chain(workspace, relative, allow_missing=True)
            atomic_replace(target, data, stat.S_IMODE(source.stat().st_mode))
        for entry in entries:
            target = reject_symlink_chain(workspace, entry["path"], allow_missing=True)
            atomic_replace(target, entry["after"], entry["after_mode"])
        copy_node_dependencies(root, workspace, commands)
        return execute_gates(workspace, commands, phase)


def filesystem_snapshot(root: Path, target_paths: set[str]) -> str:
    excluded_directories = {".git/sdd-wire-harness-state"}
    excluded_files = {".git/sdd-wire-harness.lock"}
    excluded = set(target_paths)
    for target in target_paths:
        for parent in PurePosixPath(target).parents:
            if parent.as_posix() != ".":
                excluded.add(parent.as_posix())
    digest = hashlib.sha256()
    for current, directories, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        relative_current = current_path.relative_to(root).as_posix()
        kept_directories: list[str] = []
        for name in sorted(directories):
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if any(
                relative == prefix or relative.startswith(prefix + "/")
                for prefix in excluded_directories
            ):
                continue
            kept_directories.append(name)
            if relative not in excluded:
                digest.update(f"dir\0{relative}\0{stat.S_IMODE(path.lstat().st_mode)}\0".encode())
        directories[:] = kept_directories
        for name in sorted(files):
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if relative in excluded or relative in excluded_files:
                continue
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                payload = os.readlink(path).encode("utf-8", "surrogateescape")
                kind = "symlink"
            elif stat.S_ISREG(metadata.st_mode):
                payload = path.read_bytes()
                kind = "file"
            else:
                payload = b""
                kind = f"special-{stat.S_IFMT(metadata.st_mode)}"
            digest.update(
                kind.encode()
                + b"\0"
                + relative.encode("utf-8", "surrogateescape")
                + b"\0"
                + str(stat.S_IMODE(metadata.st_mode)).encode()
                + b"\0"
                + hashlib.sha256(payload).digest()
            )
        if relative_current == ".":
            continue
    return "sha256:" + digest.hexdigest()


def commit_plan(
    root: Path,
    paths: dict[str, Path],
    inspection: dict[str, Any],
    entries: list[dict[str, Any]],
    commands: list[dict[str, Any]],
    plan_digest: str,
) -> dict[str, Any]:
    if receipt_matches(paths, plan_digest, entries):
        return {"status": "committed", "unchanged": True, "targets": [e["path"] for e in entries]}
    stack, _detected = detect_stacks(root)
    if run_git(root, "rev-parse", "HEAD").decode().strip() != inspection["git_sha"]:
        raise GuardError("Git HEAD changed after inspection")
    if snapshot_token(root, stack) != inspection["snapshot_token"]:
        raise GuardError("workspace snapshot changed after inspection")
    validate_workspace(root, paths)
    protected_snapshot = filesystem_snapshot(
        root, {entry["path"] for entry in entries}
    )
    pre_gates = run_sandbox_gates(root, paths, entries, commands, "pre-commit")
    if filesystem_snapshot(root, {entry["path"] for entry in entries}) != protected_snapshot:
        raise GuardError("pre-commit sandbox escaped into repository content")
    journal = {
        "version": 1,
        "operation": "wire-harness-commit",
        "state": "prepared",
        "git_sha": inspection["git_sha"],
        "feature_id": inspection["feature_id"],
        "plan_digest": plan_digest,
        "entries": [],
    }
    for entry in entries:
        missing_parents: list[str] = []
        parent = entry["target"].parent
        while parent != root and not parent.exists():
            missing_parents.append(parent.relative_to(root).as_posix())
            parent = parent.parent
        journal["entries"].append(
            {
                "path": entry["path"],
                "stack": entry["stack"],
                "absolute_path": str(entry["target"]),
                "before": encode_payload(entry["before"], entry["before_mode"]),
                "before_sha256": sha256(entry["before"]),
                "after": encode_payload(entry["after"], entry["after_mode"]),
                "after_sha256": sha256(entry["after"]),
                "created_parents": missing_parents,
            }
        )
    atomic_replace(paths["journal"], json.dumps(journal, indent=2).encode() + b"\n", 0o600)
    crash_after = int(os.environ.get("SDD_WIRE_HARNESS_CRASH_AFTER_REPLACE", "0"))
    for index, entry in enumerate(journal["entries"], start=1):
        restore_entry(entry, "after")
        if crash_after == index:
            os._exit(86)
    journal["state"] = "applied"
    atomic_replace(paths["journal"], json.dumps(journal, indent=2).encode() + b"\n", 0o600)
    try:
        post_gates = run_sandbox_gates(
            root, paths, entries, commands, "post-commit"
        )
        if filesystem_snapshot(root, {entry["path"] for entry in entries}) != protected_snapshot:
            raise GuardError("repository content outside transaction scope changed")
    except GuardError:
        for entry in journal["entries"]:
            restore_entry(entry, "before", root)
        remove_file(paths["journal"])
        raise
    journal["state"] = "committed"
    atomic_replace(paths["journal"], json.dumps(journal, indent=2).encode() + b"\n", 0o600)
    write_receipt(paths, journal)
    remove_file(paths["journal"])
    return {
        "status": "committed",
        "unchanged": False,
        "targets": [e["path"] for e in entries],
        "gates": pre_gates + post_gates,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subcommands = root.add_subparsers(dest="command", required=True)
    inspect_parser = subcommands.add_parser("inspect")
    inspect_parser.add_argument("--project-root", required=True)
    inspect_parser.add_argument("--feature-id")
    inspect_parser.add_argument("--dry-run", action="store_true")
    for name in ("validate", "commit"):
        command = subcommands.add_parser(name)
        command.add_argument("--project-root", required=True)
        command.add_argument("--feature-id")
        command.add_argument("--expected-head", required=True)
        command.add_argument("--expected-token", required=True)
        command.add_argument("--plan", required=True)
        command.add_argument("--candidate-dir", required=True)
        if name == "validate":
            command.add_argument("--dry-run", action="store_true")
    return root


def execute_with_state(
    arguments: argparse.Namespace,
    root: Path,
    paths: dict[str, Path],
    feature_id: str | None,
    dry_run: bool,
) -> dict[str, Any]:
    recovery = recover(root, paths, dry_run=dry_run)
    inspection = inspect(root, paths, feature_id)
    if arguments.command == "inspect":
        inspection["dry_run"] = dry_run
        inspection["recovery"] = recovery
        return inspection
    replay = idempotent_replay(
        root,
        paths,
        Path(arguments.plan),
        Path(arguments.candidate_dir),
        arguments.expected_head,
        feature_id,
    )
    if arguments.command == "commit" and replay is not None:
        return replay
    if arguments.expected_head != inspection["git_sha"] or arguments.expected_token != inspection["snapshot_token"]:
        raise GuardError("expected HEAD or snapshot token no longer matches")
    _plan, entries, commands, plan_digest = validate_plan(
        root, inspection, Path(arguments.plan), Path(arguments.candidate_dir)
    )
    result = {
        "status": "validated",
        "dry_run": arguments.command == "validate" and dry_run,
        "git_sha": inspection["git_sha"],
        "feature_id": feature_id,
        "plan_digest": plan_digest,
        "changes": [
            {
                "path": entry["path"],
                "stack": entry["stack"],
                "purpose": entry["purpose"],
                "before_sha256": sha256(entry["before"]),
                "after_sha256": sha256(entry["after"]),
            }
            for entry in entries
        ],
        "recovery": recovery,
    }
    if arguments.command == "commit":
        result.update(commit_plan(root, paths, inspection, entries, commands, plan_digest))
    return result


def execute(arguments: argparse.Namespace) -> dict[str, Any]:
    root, git_dir = resolve_project(arguments.project_root)
    paths = technical_paths(root, git_dir)
    feature_id = validate_feature_id(arguments.feature_id)
    dry_run = bool(getattr(arguments, "dry_run", False))
    if dry_run:
        return execute_with_state(arguments, root, paths, feature_id, True)
    with exclusive_lock(paths["lock"]):
        return execute_with_state(arguments, root, paths, feature_id, False)


def main(argv: list[str] | None = None) -> int:
    try:
        result = execute(parser().parse_args(argv))
    except (GuardError, FileNotFoundError, ValueError) as error:
        print(json.dumps({"status": "refused", "error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
