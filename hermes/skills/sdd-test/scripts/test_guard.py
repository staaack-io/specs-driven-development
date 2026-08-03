#!/usr/bin/env python3
"""Deterministic safety boundary for ``/sdd-test``."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import os
import re
import tempfile
from typing import Callable, Sequence


FEATURE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
AC_ID = re.compile(r"^AC-[0-9]{3}$")
GAP_ID = re.compile(r"^Gap-[0-9]{3}$")
SECRET = re.compile(
    r"(?i)(token|secret|password|authorization|api[-_]?key)\s*[:=]\s*\S+"
)
ABSOLUTE_PATH = re.compile(r"(?<![\w.])/(?:[^/\s]+/)+[^/\s]+")
BYPASS_ARGUMENTS = ("skiptests", "skip.test", "maven.test.skip", "pit.skip")

RUNTIME_TEST_CATALOG = {
    "AC-196": (
        "hermes/runtime/test_sdd_runtime_guard.py",
        "test_dag_and_test_id_failures_are_explicit",
    ),
    "AC-197": (
        "hermes/runtime/test_sdd_runtime_guard.py",
        "test_unordered_overlap_is_rejected_but_dependency_serializes_it",
    ),
    "AC-198": (
        "hermes/runtime/test_sdd_runtime_guard.py",
        "test_cas_actor_and_target_guards_fail_before_writing",
    ),
    "AC-199": (
        "hermes/runtime/test_sdd_runtime_guard.py",
        "test_linked_worktrees_share_the_runtime_lock_directory",
    ),
    "AC-200": (
        "hermes/runtime/test_sdd_runtime_guard.py",
        "test_globs_parent_traversal_and_symlink_chains_are_rejected",
    ),
    "AC-201": (
        "hermes/runtime/test_sdd_runtime_guard.py",
        "test_crash_before_marker_rolls_back_complete_old_set",
    ),
    "AC-202": (
        "hermes/runtime/test_sdd_runtime_guard.py",
        "test_crash_after_marker_rolls_forward_complete_new_set",
    ),
    "AC-203": (
        "hermes/runtime/test_sdd_runtime_guard.py",
        "test_fan_in_commits_once_and_retry_is_idempotent",
    ),
    "AC-204": (
        "hermes/runtime/test_sdd_runtime_guard.py",
        "test_fan_in_commits_once_and_retry_is_idempotent",
    ),
    "AC-205": (
        "hermes/runtime/test_sdd_runtime_guard.py",
        "test_disjoint_writers_overlap_but_conflict_waits_for_release",
    ),
    "AC-206": (
        "hermes/runtime/test_sdd_build_orchestrator.py",
        "test_t010_t2_worker_bounds_default_and_cap_are_two",
    ),
    "AC-207": (
        "hermes/runtime/test_sdd_build_orchestrator.py",
        "test_t010_t3_admits_only_ready_tasks_with_merged_dependencies",
    ),
    "AC-208": (
        "hermes/runtime/test_sdd_build_orchestrator.py",
        "test_t010_t4_disjoint_scopes_share_wave_and_conflicts_serialize",
    ),
    "AC-209": (
        "hermes/runtime/test_sdd_build_orchestrator.py",
        "test_t010_t9_dispatch_failure_does_not_revoke_another_job",
    ),
}


def parse_arguments(argv: Sequence[str]) -> dict[str, object]:
    """Accept exactly ``<feature-id> [--gap]``."""

    if isinstance(argv, (str, bytes)) or len(argv) not in {1, 2}:
        raise ValueError("expected <feature-id> [--gap]")
    feature_id = argv[0]
    if not isinstance(feature_id, str) or not FEATURE_ID.fullmatch(feature_id):
        raise ValueError("feature-id must be a safe identifier")
    gap = len(argv) == 2
    if gap and argv[1] != "--gap":
        raise ValueError("the only optional argument is --gap")
    return {"feature_id": feature_id, "gap": gap}


def _has_symlink_component(root: Path, relative: PurePosixPath) -> bool:
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def validate_scope(
    feature_id: str,
    changed_paths: Sequence[str],
    *,
    repo_root: Path | str | None = None,
) -> list[str]:
    """Allow only concrete tests and this feature's test plan."""

    plan_path = f".specs/{feature_id}/06-test-plan.md"
    validated: list[str] = []
    for value in changed_paths:
        path = PurePosixPath(value)
        test_path = len(path.parts) > 2 and path.parts[:2] == ("src", "test")
        canonical = not path.is_absolute() and ".." not in path.parts
        if not canonical or (value != plan_path and not test_path):
            raise ValueError(f"path outside /sdd-test writer scope: {value}")
        if repo_root is not None:
            root = Path(repo_root).resolve(strict=True)
            if _has_symlink_component(root, path):
                raise ValueError(f"symbolic path outside /sdd-test scope: {value}")
        validated.append(value)
    return validated


def _test_row(test: dict[str, str]) -> str:
    required = ("ac", "type", "path", "name", "tag")
    if any(not test.get(key) for key in required):
        raise ValueError("each planned test needs AC, type, path, name and tag")
    if test["tag"] != test["ac"] or not AC_ID.fullmatch(test["ac"]):
        raise ValueError("each test tag must equal its AC-NNN")
    return (
        f"| {test['ac']} | {test['type']} | {test['path']} | "
        f"{test['name']} | `{test['tag']}` |"
    )


def _gap_row(gap: dict[str, str]) -> str:
    gap_id = gap.get("id", "")
    ac_id = gap.get("ac", "")
    if not GAP_ID.fullmatch(gap_id) or not AC_ID.fullmatch(ac_id):
        raise ValueError("gaps require Gap-NNN and AC-NNN identifiers")
    resolution = gap.get("test")
    if resolution:
        outcome = f"Test: {resolution}"
    elif gap.get("wont_fix"):
        outcome = f"Won't fix: {gap['wont_fix']}"
    else:
        raise ValueError("every gap needs a test or a Won't fix justification")
    return f"| {gap_id} | {ac_id} | {outcome} |"


def render_test_plan(
    *,
    feature_id: str,
    acceptance_criteria: Sequence[str],
    tests: Sequence[dict[str, str]],
    gaps: Sequence[dict[str, str]],
) -> str:
    """Render the AC/type matrix and gap resolutions deterministically."""

    criteria = list(acceptance_criteria)
    invalid_criteria = any(not AC_ID.fullmatch(value) for value in criteria)
    if not criteria or invalid_criteria or len(criteria) != len(set(criteria)):
        raise ValueError("the plan needs unique AC-NNN acceptance criteria")
    test_rows = [_test_row(test) for test in tests]
    covered = {test["ac"] for test in tests}
    gap_rows = [_gap_row(gap) for gap in gaps]
    covered.update(gap["ac"] for gap in gaps)
    if set(criteria) != covered:
        raise ValueError("each acceptance criterion needs a test or resolved gap")
    lines = [
        f"# Plan de test : {feature_id}",
        "",
        "## Matrice critères × types",
        "",
        "| AC | Type | Test | Nom descriptif | Tag |",
        "|---|---|---|---|---|",
        *test_rows,
        "",
        "## Testcontainers",
        "",
        "Les tests d'intégration déclarent explicitement leur besoin Testcontainers.",
        "",
        "## Gaps",
        "",
        "| Gap | AC | Résolution |",
        "|---|---|---|",
        *(gap_rows or ["| Aucun | — | — |"]),
        "",
    ]
    return "\n".join(lines)


def _redact(output: object, root: Path) -> str:
    text = str(output).replace(str(root), "<repo>")
    text = SECRET.sub(r"\1=<redacted>", text)
    return ABSOLUTE_PATH.sub("<absolute-path>", text)


def _evidence(result: dict[str, object], root: Path) -> dict[str, object]:
    argv = result.get("argv")
    if not isinstance(argv, list) or not all(isinstance(item, str) for item in argv):
        raise ValueError("runner evidence must contain structured argv")
    returncode = int(result.get("returncode", 1))
    return {
        "argv": list(argv),
        "returncode": returncode,
        "result": "PASS" if returncode == 0 else "FAIL",
        "output": _redact(result.get("output", ""), root),
    }


def _validate_gate_argv(argv: Sequence[str]) -> list[str]:
    if isinstance(argv, (str, bytes)) or not argv:
        raise ValueError("gate argv must be a non-empty structured list")
    structured = [str(item) for item in argv]
    lowered = " ".join(structured).casefold()
    if any(argument in lowered for argument in BYPASS_ARGUMENTS):
        raise ValueError("test bypass arguments are forbidden")
    return structured


def run_test_gate(
    *,
    repo_root: Path | str,
    argv: Sequence[str],
    runner: Callable[[list[str]], dict[str, object]],
    runtime: object,
) -> dict[str, object]:
    """Run one heavy test gate under the canonical global lock."""

    root = Path(repo_root).resolve(strict=True)
    structured = _validate_gate_argv(argv)
    with runtime.global_lock(root):
        result = runner(structured)
    return _evidence(result, root)


def publish_test_plan(
    *,
    repo_root: Path | str,
    feature_id: str,
    task_id: str,
    content: str,
    runtime: object,
) -> Path:
    """Atomically publish only this feature's ``06-test-plan.md``."""

    root = Path(repo_root).resolve(strict=True)
    relative = f".specs/{feature_id}/06-test-plan.md"
    validate_scope(feature_id, [relative], repo_root=root)
    target = root / relative
    if target.parent.is_symlink() or not target.parent.is_dir():
        raise ValueError("feature artifact directory must be a real directory")
    runtime.validate_worker_changes(
        feature_id=feature_id,
        task_id=task_id,
        changed_paths=[relative],
        files_in_scope=[relative],
    )
    descriptor, temporary = tempfile.mkstemp(
        prefix=".06-test-plan.", suffix=".tmp", dir=target.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target


def regenerate_traceability(
    *,
    repo_root: Path | str,
    feature_id: str,
    runner: Callable[[list[str]], dict[str, object]],
) -> dict[str, object]:
    """Regenerate traceability only after the plan has been published."""

    root = Path(repo_root).resolve(strict=True)
    argv = [".github/scripts/traceability.sh", feature_id]
    return _evidence(runner(argv), root)


def validate_runtime_catalog(repo_root: Path | str) -> dict[str, dict[str, str]]:
    """Prove AC-196..209 with concrete executable runtime test methods."""

    root = Path(repo_root).resolve(strict=True)
    expected = {f"AC-{number}" for number in range(196, 210)}
    if set(RUNTIME_TEST_CATALOG) != expected:
        raise ValueError("runtime catalog must cover exactly AC-196 through AC-209")
    validated: dict[str, dict[str, str]] = {}
    for ac_id, (relative, method) in RUNTIME_TEST_CATALOG.items():
        path = root / relative
        if not path.is_file() or f"def {method}(" not in path.read_text(encoding="utf-8"):
            raise ValueError(f"missing executable runtime proof for {ac_id}")
        validated[ac_id] = {"path": relative, "test": method}
    return validated
