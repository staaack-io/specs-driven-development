#!/usr/bin/env python3
"""Inspect a repository and atomically commit the five SDD onboarding artifacts."""

from __future__ import annotations

import argparse
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any


ARTIFACT_NAMES = (
    "_stack.json",
    "_baseline.json",
    "_starter-design.md",
    "_known-debt.md",
    "_onboarding.md",
)
JSON_ARTIFACTS = {"_stack.json", "_baseline.json"}
IGNORED_DIRECTORIES = {
    ".git",
    ".next",
    ".gradle",
    ".idea",
    ".mvn",
    ".vscode",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
    "vendor",
}
SOURCE_SUFFIXES = {
    ".java",
    ".kt",
    ".kts",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".py",
    ".go",
    ".rs",
}
TEST_MARKERS = ("/test/", "/tests/", ".test.", ".spec.", "test_", "_test.")
NON_PRODUCT_FILES = {
    "build.gradle.kts",
    "next.config.js",
    "next.config.mjs",
    "next.config.ts",
    "postcss.config.js",
    "postcss.config.mjs",
    "tailwind.config.js",
    "tailwind.config.ts",
    "vitest.config.js",
    "vitest.config.ts",
}


class GuardError(RuntimeError):
    """Expected refusal with a user-readable explanation."""


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


def token_for(data: bytes | None) -> str:
    if data is None:
        return "absent"
    return "sha256:" + hashlib.sha256(data).hexdigest()


def atomic_replace(path: Path, data: bytes, fallback_mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        mode = fallback_mode
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
    finally:
        temporary.unlink(missing_ok=True)


def atomic_replace_with_mode(path: Path, data: bytes, mode: int) -> None:
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
    finally:
        temporary.unlink(missing_ok=True)


def fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def read_bytes(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def encode_artifact(data: bytes | None, mode: int | None) -> dict[str, Any]:
    if data is None:
        return {"exists": False}
    return {
        "exists": True,
        "data_b64": base64.b64encode(data).decode("ascii"),
        "mode": mode,
    }


def decode_artifact(value: object, label: str) -> tuple[bytes | None, int | None]:
    if not isinstance(value, dict) or not isinstance(value.get("exists"), bool):
        raise GuardError(f"{label} is invalid")
    if not value["exists"]:
        return None, None
    encoded = value.get("data_b64")
    mode = value.get("mode")
    if not isinstance(encoded, str) or not isinstance(mode, int):
        raise GuardError(f"{label} is invalid")
    try:
        return base64.b64decode(encoded, validate=True), mode
    except ValueError as error:
        raise GuardError(f"{label} contains invalid base64") from error


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
    git_dir_text = run_git(root, "rev-parse", "--absolute-git-dir").decode().strip()
    git_dir = Path(git_dir_text).resolve(strict=True)
    return root, git_dir


def technical_paths(root: Path, git_dir: Path) -> dict[str, Path]:
    specs = root / ".specs"
    if specs.exists() and (specs.is_symlink() or not specs.is_dir()):
        raise GuardError(".specs must be a real directory when it exists")
    return {
        "specs": specs,
        "lock": git_dir / "sdd-onboarding.lock",
        "journal": git_dir / "sdd-onboarding.transaction.json",
        "marker": git_dir / "sdd-onboarding.marker",
        "receipt": git_dir / "sdd-onboarding.commit.json",
    }


def artifact_paths(specs: Path) -> dict[str, Path]:
    return {name: specs / name for name in ARTIFACT_NAMES}


def artifact_payload(paths: dict[str, Path]) -> dict[str, bytes | None]:
    payload: dict[str, bytes | None] = {}
    for name, path in paths.items():
        if path.is_symlink():
            raise GuardError(f"symbolic onboarding artifact refused: {path}")
        payload[name] = read_bytes(path)
    return payload


def artifact_set_token(payload: dict[str, bytes | None]) -> str:
    digest = hashlib.sha256()
    for name in ARTIFACT_NAMES:
        data = payload[name]
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update(token_for(data).encode())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def snapshot_token(head: str, payload: dict[str, bytes | None]) -> str:
    return token_for(
        json.dumps(
            {"head": head, "artifacts": artifact_set_token(payload)},
            sort_keys=True,
        ).encode()
    )


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


def load_json(path: Path, label: str) -> dict[str, Any] | None:
    data = read_bytes(path)
    if data is None:
        return None
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GuardError(f"{label} is not valid JSON: {error}") from error
    if not isinstance(value, dict):
        raise GuardError(f"{label} must be a JSON object")
    return value


def allowed_workspace_state(
    root: Path,
    paths: dict[str, Path],
    current_payload: dict[str, bytes | None],
) -> dict[str, Any]:
    changes = parse_status(root)
    if not changes:
        return {"clean": True, "onboarding_artifacts_pending": False, "changes": []}

    allowed_names = {f".specs/{name}" for name in ARTIFACT_NAMES}
    staged = [path for status_code, path in changes if status_code[0] not in {" ", "?"}]
    unrelated = [path for _status_code, path in changes if path not in allowed_names]
    if staged:
        raise GuardError(
            "staged worktree changes are not safe for onboarding: " + ", ".join(staged)
        )
    if unrelated:
        raise GuardError(
            "worktree contains changes outside prior onboarding artifacts: "
            + ", ".join(unrelated)
        )

    receipt = load_json(paths["receipt"], "onboarding receipt")
    current_set_token = artifact_set_token(current_payload)
    if (
        receipt is None
        or receipt.get("version") != 1
        or receipt.get("operation") != "commit-onboarding"
        or receipt.get("target_artifact_token") != current_set_token
    ):
        raise GuardError(
            "modified onboarding artifacts do not match the last completion receipt"
        )
    return {
        "clean": False,
        "onboarding_artifacts_pending": True,
        "changes": [{"status": code, "path": path} for code, path in changes],
    }


def current_head(root: Path) -> str:
    return run_git(root, "rev-parse", "HEAD").decode().strip()


def relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def project_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        try:
            parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(part in IGNORED_DIRECTORIES for part in parts):
            continue
        if path.is_symlink() or not path.is_file():
            continue
        files.append(path)
    return sorted(files)


def read_text_limited(path: Path, limit: int = 1_000_000) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    if len(data) > limit or b"\0" in data:
        return ""
    return data.decode("utf-8", "replace")


def package_info(root: Path, package_path: Path) -> dict[str, Any]:
    relative_path = relative(root, package_path)
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "path": relative_path,
            "kind": "node",
            "confidence": "limited",
            "error": "package.json is invalid or unreadable",
        }
    if not isinstance(package, dict):
        return {
            "path": relative_path,
            "kind": "node",
            "confidence": "limited",
            "error": "package.json is not an object",
        }
    dependencies: dict[str, str] = {}
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        values = package.get(section)
        if isinstance(values, dict):
            for name in ("next", "react", "react-dom", "typescript"):
                version = values.get(name)
                if isinstance(version, str):
                    dependencies[name] = version
    scripts = package.get("scripts") if isinstance(package.get("scripts"), dict) else {}
    manager = "unknown"
    module = package_path.parent
    declared_manager = package.get("packageManager")
    if isinstance(declared_manager, str) and declared_manager:
        manager = declared_manager.split("@", maxsplit=1)[0]
    detected_locks: list[str] = []
    for lock, name in (
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("package-lock.json", "npm"),
        ("bun.lockb", "bun"),
        ("bun.lock", "bun"),
    ):
        if (module / lock).is_file():
            detected_locks.append(name)
    distinct_locks = sorted(set(detected_locks))
    ambiguities: list[str] = []
    if manager == "unknown" and len(distinct_locks) == 1:
        manager = distinct_locks[0]
    elif len(distinct_locks) > 1:
        ambiguities.append(
            "multiple package manager lockfiles: " + ", ".join(distinct_locks)
        )
        manager = "unknown"
    elif (
        manager != "unknown"
        and distinct_locks
        and manager not in distinct_locks
    ):
        ambiguities.append(
            f"packageManager declares {manager}, lockfile proves {distinct_locks[0]}"
        )
    framework = "nextjs" if "next" in dependencies else "react" if "react" in dependencies else "node"
    commands = []
    for name in ("lint", "typecheck", "test", "test:e2e", "build"):
        if name in scripts and isinstance(scripts[name], str):
            prefix = {
                "pnpm": "pnpm",
                "yarn": "yarn",
                "bun": "bun run",
                "npm": "npm run",
            }.get(manager, "<package-manager> run")
            commands.append(
                {
                    "command": f"{prefix} {name}",
                    "evidence": f"{relative_path}#scripts.{name}",
                }
            )
    return {
        "path": relative_path,
        "module": relative(root, module) or ".",
        "kind": framework,
        "confidence": (
            "proved"
            if framework in {"nextjs", "react"} and not ambiguities
            else "limited"
        ),
        "versions": dependencies,
        "package_manager": manager,
        "package_manager_evidence": detected_locks,
        "ambiguities": ambiguities,
        "node_engine": package.get("engines", {}).get("node")
        if isinstance(package.get("engines"), dict)
        else None,
        "validation_commands": commands,
        "evidence": [relative_path],
    }


def pom_info(root: Path, pom_path: Path) -> dict[str, Any]:
    text = read_text_limited(pom_path)
    relative_path = relative(root, pom_path)
    spring_specific = bool(
        re.search(
            r"<artifactId>spring-boot-(?:starter-parent|dependencies|maven-plugin|starter-[^<]+)</artifactId>",
            text,
        )
    )
    properties = {
        name: match.group(1).strip()
        for name in ("java.version", "maven.compiler.release", "spring-boot.version")
        if (
            match := re.search(
                rf"<{re.escape(name)}>\s*([^<]+?)\s*</{re.escape(name)}>", text
            )
        )
    }
    boot_match = re.search(
        r"<artifactId>spring-boot-starter-parent</artifactId>\s*"
        r"<version>\s*([^<]+?)\s*</version>",
        text,
        re.DOTALL,
    )
    boot_version = properties.get("spring-boot.version")
    if boot_match:
        boot_version = boot_match.group(1).strip()
    module = pom_path.parent
    migration = []
    if (
        "flyway-core" in text
        or "db/migration" in text
        or (module / "src/main/resources/db/migration").is_dir()
    ):
        migration.append("flyway")
    if (
        "liquibase-core" in text
        or "db/changelog" in text
        or (module / "src/main/resources/db/changelog").is_dir()
    ):
        migration.append("liquibase")
    wrapper = (module / "mvnw").is_file()
    commands = (
        [{"command": "./mvnw verify", "evidence": f"{relative_path} and mvnw"}]
        if wrapper
        else []
    )
    return {
        "path": relative_path,
        "module": relative(root, module) or ".",
        "kind": "spring" if spring_specific else "maven",
        "confidence": "proved" if spring_specific else "limited",
        "versions": {
            "java": properties.get("java.version")
            or properties.get("maven.compiler.release"),
            "spring_boot": boot_version,
        },
        "migration": migration or ["none-detected"],
        "validation_commands": commands,
        "suggested_commands": []
        if wrapper
        else [{"command": "mvn verify", "evidence": relative_path, "confidence": "inferred"}],
        "evidence": [relative_path],
    }


def gradle_info(root: Path, build_path: Path) -> dict[str, Any]:
    text = read_text_limited(build_path)
    relative_path = relative(root, build_path)
    spring_specific = bool(
        re.search(
            r"""(?:id\s*\(?\s*['"]org\.springframework\.boot['"]|"""
            r"""org\.springframework\.boot|spring-boot-starter-|"""
            r"""org\.springframework\.boot:spring-boot-dependencies)""",
            text,
        )
    )
    boot_match = re.search(
        r"""org\.springframework\.boot['"]?\s*(?:version)?\s*['"]([^'"]+)""",
        text,
    )
    module = build_path.parent
    wrapper = (module / "gradlew").is_file()
    commands = (
        [{"command": "./gradlew check", "evidence": f"{relative_path} and gradlew"}]
        if wrapper
        else []
    )
    return {
        "path": relative_path,
        "module": relative(root, module) or ".",
        "kind": "spring" if spring_specific else "gradle",
        "confidence": "proved" if spring_specific else "limited",
        "versions": {"spring_boot": boot_match.group(1) if boot_match else None},
        "validation_commands": commands,
        "suggested_commands": []
        if wrapper
        else [{"command": "gradle check", "evidence": relative_path, "confidence": "inferred"}],
        "evidence": [relative_path],
    }


def inspect_project(root: Path, head: str) -> dict[str, Any]:
    files = project_files(root)
    modules: list[dict[str, Any]] = []
    for path in files:
        if path.name == "package.json":
            modules.append(package_info(root, path))
        elif path.name == "pom.xml":
            modules.append(pom_info(root, path))
        elif path.name in {"build.gradle", "build.gradle.kts"}:
            modules.append(gradle_info(root, path))
    conflicting_migrations = [
        module["path"]
        for module in modules
        if module.get("kind") == "spring"
        and set(module.get("migration", [])) == {"flyway", "liquibase"}
    ]
    if conflicting_migrations:
        raise GuardError(
            "Flyway and Liquibase are both detected in the same Spring module: "
            + ", ".join(conflicting_migrations)
        )

    source_files = [
        path
        for path in files
        if path.suffix.lower() in SOURCE_SUFFIXES
        and path.name not in NON_PRODUCT_FILES
        and not path.name.endswith(".config.ts")
        and not path.name.endswith(".config.js")
    ]
    tests = [
        path
        for path in source_files
        if any(marker in f"/{relative(root, path).lower()}" for marker in TEST_MARKERS)
    ]
    production = [path for path in source_files if path not in tests]
    validation_commands: list[dict[str, str]] = []
    for module in modules:
        validation_commands.extend(module.get("validation_commands", []))
    architecture_evidence = [
        relative(root, path)
        for path in files
        if path.name
        in {
            "README.md",
            "AGENTS.md",
            "settings.gradle",
            "settings.gradle.kts",
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        }
        or path.name.startswith("next.config.")
    ][:100]
    proved = [module for module in modules if module.get("confidence") == "proved"]
    limitations: list[str] = []
    if not modules:
        limitations.append("No supported build manifest was found.")
    if modules and not proved:
        limitations.append(
            "Build manifests exist, but no Spring, React or Next.js framework dependency was proved."
        )
    if not validation_commands:
        limitations.append("No configured validation command was found.")
    return {
        "schema_version": 1,
        "git_sha": head,
        "classification": "brownfield" if production else "greenfield",
        "modules": modules,
        "source_counts": {
            "production": len(production),
            "tests": len(tests),
        },
        "validation_commands": validation_commands,
        "architecture_evidence": architecture_evidence,
        "confidence": {
            "level": "proved" if proved else "limited",
            "limitations": limitations,
        },
        "scan_policy": {
            "executed_commands": ["git rev-parse", "git status"],
            "heavy_gates_executed": False,
            "ignored_directories": sorted(IGNORED_DIRECTORIES),
        },
    }


def lock_nonblocking(lock_path: Path):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock = lock_path.open("a+b")
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        lock.close()
        raise GuardError(
            "another onboarding writer holds the explicit repository lock"
        ) from error
    return lock


def marker_value(path: Path) -> str:
    data = read_bytes(path)
    if data is None:
        return "absent"
    try:
        return data.decode("ascii").strip()
    except UnicodeDecodeError as error:
        raise GuardError("onboarding marker is not valid ASCII") from error


def restore_artifacts(
    targets: dict[str, Path], encoded: object, label: str
) -> None:
    if not isinstance(encoded, dict) or set(encoded) != set(ARTIFACT_NAMES):
        raise GuardError(f"{label} artifact set is invalid")
    for name in ARTIFACT_NAMES:
        data, mode = decode_artifact(encoded[name], f"{label}.{name}")
        target = targets[name]
        if data is None:
            target.unlink(missing_ok=True)
        elif mode is not None:
            atomic_replace_with_mode(target, data, mode)


def recover_transaction(
    paths: dict[str, Path], targets: dict[str, Path]
) -> str | None:
    journal = load_json(paths["journal"], "onboarding transaction")
    if journal is None:
        return None
    if (
        journal.get("version") != 1
        or journal.get("operation") != "commit-onboarding"
    ):
        raise GuardError("onboarding transaction format is unsupported")
    expected_marker = journal.get("expected_marker")
    target_marker = journal.get("target_marker")
    if (
        not isinstance(expected_marker, str)
        or not isinstance(target_marker, str)
        or expected_marker == target_marker
    ):
        raise GuardError("onboarding transaction markers are ambiguous")
    current_marker = marker_value(paths["marker"])
    if current_marker == target_marker:
        restore_artifacts(targets, journal.get("next_artifacts"), "next")
        next_receipt = journal.get("next_receipt")
        if not isinstance(next_receipt, dict):
            raise GuardError("onboarding transaction receipt is invalid")
        atomic_replace(
            paths["receipt"],
            json.dumps(next_receipt, sort_keys=True).encode(),
            0o600,
        )
        outcome = "committed"
    elif current_marker == expected_marker:
        restore_artifacts(targets, journal.get("previous_artifacts"), "previous")
        outcome = "rolled-back"
    else:
        raise GuardError(
            "cannot recover onboarding transaction: commit marker is ambiguous"
        )
    fsync_directory(paths["specs"])
    paths["journal"].unlink()
    fsync_directory(paths["journal"].parent)
    return outcome


def inspect(args: argparse.Namespace) -> None:
    root, git_dir = resolve_project(args.project_root)
    paths = technical_paths(root, git_dir)
    targets = artifact_paths(paths["specs"])
    with lock_nonblocking(paths["lock"]) as lock:
        del lock
        recovery = recover_transaction(paths, targets)
        head = current_head(root)
        payload = artifact_payload(targets)
        workspace = allowed_workspace_state(root, paths, payload)
        inspection = inspect_project(root, head)
    print(
        json.dumps(
            {
                "project_root": str(root),
                "git_sha": head,
                "snapshot_token": snapshot_token(head, payload),
                "artifact_token": artifact_set_token(payload),
                "recovered": recovery is not None,
                "recovery_outcome": recovery,
                "workspace": workspace,
                "inspection": inspection,
            },
            indent=2,
        )
    )


def contains_absolute_path(value: object) -> bool:
    if isinstance(value, str):
        return value.startswith("/") or bool(re.match(r"^[A-Za-z]:[\\/]", value))
    if isinstance(value, list):
        return any(contains_absolute_path(item) for item in value)
    if isinstance(value, dict):
        return any(contains_absolute_path(item) for item in value.values())
    return False


def validate_json_artifact(name: str, data: bytes, head: str) -> None:
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GuardError(f"{name} is not valid JSON: {error}") from error
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise GuardError(f"{name} must be an object with schema_version 1")
    if contains_absolute_path(value):
        raise GuardError(f"{name} contains an absolute path")
    if value.get("git_sha") != head:
        raise GuardError(f"{name} git_sha does not match current HEAD")
    if name == "_stack.json":
        if value.get("classification") not in {"greenfield", "brownfield"}:
            raise GuardError("_stack.json classification is invalid")
        if not isinstance(value.get("modules"), list):
            raise GuardError("_stack.json must contain a modules array")
        confidence = value.get("confidence")
        if (
            not isinstance(confidence, dict)
            or confidence.get("level") not in {"proved", "limited", "unknown"}
            or not isinstance(confidence.get("limitations"), list)
        ):
            raise GuardError("_stack.json must state confidence and limitations")
    else:
        if value.get("status") != "not-run":
            raise GuardError("_baseline.json must state status: not-run")
        if value.get("heavy_gates_executed") is not False:
            raise GuardError("_baseline.json must state heavy_gates_executed: false")
        if not isinstance(value.get("validation_commands"), list):
            raise GuardError("_baseline.json must contain validation_commands")


def validate_markdown_artifact(
    name: str, data: bytes, head: str, project_root: Path
) -> None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise GuardError(f"{name} must be UTF-8") from error
    if not text.strip():
        raise GuardError(f"{name} is empty")
    if str(project_root) in text:
        raise GuardError(f"{name} contains the absolute project path")
    required = {
        "_onboarding.md": (
            "# ",
            "## Git Reference",
            "## Classification",
            "## Confidence and Limits",
            "## Next Step",
        ),
        "_starter-design.md": (
            "# ",
            "## Modules",
            "## Architecture",
            "## Conventions",
            "## Evidence",
            "## Confidence and Limits",
        ),
        "_known-debt.md": (
            "# ",
            "## Observed Debt",
            "## Unknowns",
            "## Non-Regression Guidance",
        ),
    }[name]
    missing = [section for section in required if section not in text]
    if missing:
        raise GuardError(f"{name} is missing sections: {', '.join(missing)}")
    if name in {"_onboarding.md", "_starter-design.md"} and head not in text:
        raise GuardError(f"{name} must contain the inspected Git SHA")


def load_candidates(
    candidate_dir_text: str, head: str, project_root: Path
) -> tuple[dict[str, bytes], dict[str, int]]:
    supplied = Path(candidate_dir_text).expanduser()
    if supplied.is_symlink():
        raise GuardError("symbolic candidate directory refused")
    candidate_dir = supplied.resolve(strict=True)
    if not candidate_dir.is_dir():
        raise GuardError("candidate directory must be a real directory")
    data: dict[str, bytes] = {}
    modes: dict[str, int] = {}
    for name in ARTIFACT_NAMES:
        path = candidate_dir / name
        if path.is_symlink() or not path.is_file():
            raise GuardError(f"candidate missing or symbolic: {path}")
        value = path.read_bytes()
        if name in JSON_ARTIFACTS:
            validate_json_artifact(name, value, head)
        else:
            validate_markdown_artifact(name, value, head, project_root)
        data[name] = value
        modes[name] = stat.S_IMODE(path.stat().st_mode)
    unexpected = sorted(
        path.name for path in candidate_dir.iterdir() if path.name not in ARTIFACT_NAMES
    )
    if unexpected:
        raise GuardError(
            "candidate directory contains unexpected files: " + ", ".join(unexpected)
        )
    return data, modes


def encode_set(
    payload: dict[str, bytes | None], modes: dict[str, int | None]
) -> dict[str, Any]:
    return {
        name: encode_artifact(payload[name], modes[name]) for name in ARTIFACT_NAMES
    }


def commit(args: argparse.Namespace) -> None:
    root, git_dir = resolve_project(args.project_root)
    paths = technical_paths(root, git_dir)
    targets = artifact_paths(paths["specs"])
    with lock_nonblocking(paths["lock"]) as lock:
        del lock
        recovery = recover_transaction(paths, targets)
        head = current_head(root)
        if head != args.expected_head:
            raise GuardError(
                f"HEAD changed concurrently: expected {args.expected_head}, found {head}"
            )
        current_payload = artifact_payload(targets)
        allowed_workspace_state(root, paths, current_payload)
        current_snapshot = snapshot_token(head, current_payload)
        if current_snapshot != args.expected_token:
            raise GuardError(
                f"onboarding artifacts changed concurrently: expected "
                f"{args.expected_token}, found {current_snapshot}"
            )
        candidate_data, candidate_modes = load_candidates(
            args.candidate_dir, head, root
        )
        next_payload = {name: candidate_data[name] for name in ARTIFACT_NAMES}
        current_set_token = artifact_set_token(current_payload)
        next_set_token = artifact_set_token(next_payload)
        if current_set_token == next_set_token:
            print(
                json.dumps(
                    {
                        "committed": True,
                        "unchanged": True,
                        "artifact_token": current_set_token,
                        "recovered": recovery is not None,
                    }
                )
            )
            return

        previous_modes: dict[str, int | None] = {}
        for name, target in targets.items():
            previous_modes[name] = (
                stat.S_IMODE(target.stat().st_mode)
                if current_payload[name] is not None
                else None
            )
        expected_marker = marker_value(paths["marker"])
        target_marker = next_set_token
        if target_marker == expected_marker:
            raise GuardError("new artifact set collides with the current commit marker")
        next_receipt = {
            "version": 1,
            "operation": "commit-onboarding",
            "git_sha": head,
            "previous_snapshot_token": args.expected_token,
            "target_artifact_token": next_set_token,
        }
        journal = {
            "version": 1,
            "operation": "commit-onboarding",
            "expected_marker": expected_marker,
            "target_marker": target_marker,
            "previous_artifacts": encode_set(current_payload, previous_modes),
            "next_artifacts": encode_set(next_payload, candidate_modes),
            "next_receipt": next_receipt,
        }
        paths["specs"].mkdir(parents=True, exist_ok=True)
        atomic_replace(
            paths["journal"],
            json.dumps(journal, sort_keys=True).encode(),
            0o600,
        )
        fsync_directory(paths["journal"].parent)
        for name in ARTIFACT_NAMES:
            mode = previous_modes[name] or candidate_modes[name]
            atomic_replace_with_mode(targets[name], candidate_data[name], mode)
            fsync_directory(paths["specs"])
        atomic_replace(paths["marker"], target_marker.encode(), 0o600)
        fsync_directory(paths["marker"].parent)
        atomic_replace(
            paths["receipt"],
            json.dumps(next_receipt, sort_keys=True).encode(),
            0o600,
        )
        fsync_directory(paths["receipt"].parent)
        paths["journal"].unlink()
        fsync_directory(paths["journal"].parent)
    print(
        json.dumps(
            {
                "committed": True,
                "unchanged": False,
                "artifact_token": next_set_token,
                "git_sha": head,
                "files": [f".specs/{name}" for name in ARTIFACT_NAMES],
            }
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("--project-root", required=True)
    inspect_parser.set_defaults(handler=inspect)
    commit_parser = subparsers.add_parser("commit")
    commit_parser.add_argument("--project-root", required=True)
    commit_parser.add_argument("--expected-head", required=True)
    commit_parser.add_argument("--expected-token", required=True)
    commit_parser.add_argument("--candidate-dir", required=True)
    commit_parser.set_defaults(handler=commit)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        args.handler(args)
        return 0
    except (GuardError, FileNotFoundError, NotADirectoryError) as error:
        print(json.dumps({"error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
