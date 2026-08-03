#!/usr/bin/env python3
"""Deterministic safety boundary for ``/sdd-code-simplify``."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import re
from typing import Callable, Sequence


GLOB_CHARACTERS = "*?[]{}"
SECRET_LINE = re.compile(
    r"(?i)(token|secret|password|authorization|api[-_]?key)\s*[:=]\s*\S+"
)
ABSOLUTE_PATH = re.compile(r"(?<![\w.])/(?:[^/\s]+/)+[^/\s]+")


class BaselineTestsFailed(RuntimeError):
    """Raised before mutation when the validated test command is not green."""


def parse_arguments(argv: Sequence[str]) -> dict[str, object]:
    """Accept only one literal path and an optional trailing ``--dry-run``."""

    if isinstance(argv, (str, bytes)) or len(argv) not in {1, 2}:
        raise ValueError("expected <path> [--dry-run]")
    target = argv[0]
    if not isinstance(target, str) or not target:
        raise ValueError("target must be a non-empty string")
    dry_run = len(argv) == 2
    if dry_run and argv[1] != "--dry-run":
        raise ValueError("the only optional argument is --dry-run")
    return {"target": target, "dry_run": dry_run}


def _has_symlink_component(root: Path, relative: PurePosixPath) -> bool:
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def resolve_target(repo_root: Path | str, target: str) -> list[str]:
    """Resolve a literal production path into sorted concrete regular files."""

    root = Path(repo_root).resolve(strict=True)
    if not target or any(character in target for character in GLOB_CHARACTERS):
        raise ValueError("target must be a literal path without glob characters")
    relative = PurePosixPath(target)
    invalid_parts = any(part in {"", ".", ".."} for part in relative.parts)
    if relative.is_absolute() or invalid_parts:
        raise ValueError("target must be a canonical repository-relative path")
    if relative.parts[:2] != ("src", "main"):
        raise ValueError("target must be under src/main/** and never src/test/**")
    if _has_symlink_component(root, relative):
        raise ValueError("symbolic links are not valid simplification targets")
    candidate = root.joinpath(*relative.parts)
    try:
        candidate.resolve(strict=True).relative_to(root)
    except (FileNotFoundError, OSError, ValueError) as error:
        raise ValueError("target is absent or outside the repository") from error
    if candidate.is_file():
        return [relative.as_posix()]
    if not candidate.is_dir():
        raise ValueError("target must be a regular file or directory")

    files: list[str] = []
    for path in sorted(candidate.rglob("*")):
        child = PurePosixPath(path.relative_to(root).as_posix())
        if _has_symlink_component(root, child):
            raise ValueError("symbolic links are not valid simplification targets")
        if path.is_file():
            files.append(child.as_posix())
    if not files:
        raise ValueError("target directory contains no production files")
    return files


def _redact(output: object, repo_root: Path) -> str:
    text = str(output).replace(str(repo_root), "<repo>")
    redacted = SECRET_LINE.sub(r"\1=<redacted>", text)
    return ABSOLUTE_PATH.sub("<absolute-path>", redacted)


def _test_evidence(result: dict[str, object], repo_root: Path) -> dict[str, object]:
    argv = result.get("argv")
    if not isinstance(argv, list) or not all(isinstance(item, str) for item in argv):
        raise ValueError("test runner must return structured argv")
    return {
        "argv": list(argv),
        "returncode": int(result.get("returncode", 1)),
        "output": _redact(result.get("output", ""), repo_root),
    }


def _runtime_lease(
    runtime: object,
    root: Path,
    context: dict[str, object],
    files: list[str],
) -> dict[str, object]:
    return runtime.acquire_scope_lease(
        root,
        feature_id=context["feature_id"],
        task_id=context["task_id"],
        owner=context["owner"],
        session_id=context["session_id"],
        files_in_scope=files,
        state=context["state"],
    )


def run_simplification(
    *,
    repo_root: Path | str,
    argv: Sequence[str],
    test_argv: Sequence[str],
    test_runner: Callable[[list[str]], dict[str, object]],
    role_executor: Callable[..., dict[str, object]],
    runtime: object,
    lease_context: dict[str, object],
) -> dict[str, object]:
    """Run the green-preserving, file-isolated clarity pass."""

    root = Path(repo_root).resolve(strict=True)
    arguments = parse_arguments(argv)
    files = resolve_target(root, str(arguments["target"]))
    dry_run = bool(arguments["dry_run"])
    baseline = _test_evidence(test_runner(list(test_argv)), root)
    if baseline["returncode"] != 0:
        raise BaselineTestsFailed("the validated baseline test command is not green")

    summary: dict[str, object] = {
        "dry_run": dry_run,
        "files": files,
        "categories": [],
        "tests": [baseline],
        "regressions": [],
        "results": [],
        "details": [],
    }
    lease: dict[str, object] | None = None
    outside_before: object | None = None
    try:
        if not dry_run:
            lease = _runtime_lease(runtime, root, lease_context, files)
            outside_before = runtime.repository_fingerprint(root, excluded_paths=files)
        for relative in files:
            absolute = root / relative
            before_files = {path: (root / path).read_bytes() for path in files}
            original = before_files[relative]
            role_result = role_executor(
                path=relative,
                absolute_path=str(absolute),
                dry_run=dry_run,
                checklist="references/clarity-checklist.md",
                test_argv=list(test_argv),
            )
            categories = [str(value) for value in role_result.get("categories", [])]
            for category in categories:
                if category not in summary["categories"]:
                    summary["categories"].append(category)

            result = "simplified" if role_result.get("changed", False) else "ignored"
            modified = [
                path
                for path, previous in before_files.items()
                if (root / path).read_bytes() != previous
            ]
            collateral = [path for path in modified if path != relative]
            if (dry_run and modified) or collateral:
                for path in modified:
                    (root / path).write_bytes(before_files[path])
                raise RuntimeError("the role modified files outside its current-file contract")
            if not dry_run:
                changed_paths = [relative] if relative in modified else []
                runtime.validate_worker_changes(
                    feature_id=lease_context["feature_id"],
                    task_id=lease_context["task_id"],
                    changed_paths=changed_paths,
                    files_in_scope=files,
                )
                after = runtime.repository_fingerprint(root, excluded_paths=files)
                if after != outside_before:
                    raise RuntimeError("a file outside the exact lease changed")
                evidence = _test_evidence(test_runner(list(test_argv)), root)
                summary["tests"].append(evidence)
                if evidence["returncode"] != 0:
                    absolute.write_bytes(original)
                    summary["regressions"].append(relative)
                    result = "ignored"
            summary["results"].append(result)
            summary["details"].append(
                {"path": relative, "categories": categories, "result": result}
            )
    finally:
        if lease is not None:
            runtime.release_scope_lease(
                root,
                lease_id=lease["lease_id"],
                owner=lease_context["owner"],
                session_id=lease_context["session_id"],
            )
    return summary
