#!/usr/bin/env python3
"""Deterministic safety boundary for the Hermes /sdd-validate skill."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import time
from typing import Callable, Mapping, Sequence


def discover_repo_root(module_path: Path | str) -> Path:
    """Find the nearest source or profile root that publishes Hermes runtime."""

    resolved = Path(module_path).resolve(strict=True)
    for candidate in resolved.parents:
        runtime_guard = candidate / "hermes" / "runtime" / "sdd_runtime_guard.py"
        if runtime_guard.is_file() and not runtime_guard.is_symlink():
            return candidate
    raise RuntimeError(
        "cannot locate hermes/runtime/sdd_runtime_guard.py from validation guard"
    )


REPO_ROOT = discover_repo_root(Path(__file__))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from hermes.runtime import sdd_runtime_guard as canonical_runtime  # noqa: E402


FEATURE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
FRESHNESS_SECONDS = 600.0
FORBIDDEN_ARGUMENTS = frozenset(
    {
        "--no-verify",
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
HEAVY_GATES = ("maven", "next", "pit", "owasp")
ALLOWED_REPORTS = ("07-validation-report.md", "07a-traceability.md")
SPRING_SUFFIXES = frozenset({".java", ".kt", ".kts"})
REACT_SUFFIXES = frozenset({".js", ".jsx", ".ts", ".tsx"})
SECRET_PATTERNS = (
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
)


class GuardError(RuntimeError):
    """A validation safety or contract check failed."""


class Decision(str, Enum):
    """Closed workflow decision vocabulary."""

    APPROVE = "approve"
    REQUEST_CHANGES = "request-changes"


class TechnicalVerdict(str, Enum):
    """Closed technical verdict vocabulary."""

    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class GateResult:
    name: str
    argv: tuple[str, ...]
    returncode: int
    output: str

    @property
    def verdict(self) -> TechnicalVerdict:
        return TechnicalVerdict.PASS if self.returncode == 0 else TechnicalVerdict.FAIL


@dataclass(frozen=True)
class ValidatorResult:
    stack: str
    gates: Mapping[str, str]
    coverage: float | None
    mutation_score: float | None
    traceability: Mapping[str, str]


@dataclass(frozen=True)
class AggregateResult:
    validators: tuple[ValidatorResult, ...]
    technical_verdict: TechnicalVerdict
    decision: Decision


@dataclass(frozen=True)
class Proof:
    path: str
    test_method: str


PROOF_CATALOG = {
    "AC-210": Proof(
        "hermes/runtime/test_sdd_github_bridge.py",
        "test_admitted_job_creates_and_records_issue_and_draft_pull_request",
    ),
    "AC-211": Proof(
        "hermes/runtime/test_sdd_github_bridge.py",
        "test_correction_stays_on_branch_replies_to_exact_thread_and_rewaits",
    ),
    "AC-212": Proof(
        "hermes/runtime/test_sdd_github_bridge.py",
        "test_correction_stays_on_branch_replies_to_exact_thread_and_rewaits",
    ),
    "AC-213": Proof(
        "hermes/runtime/test_sdd_wave_synthesizer.py",
        "test_t012_t3_only_explicitly_approved_observed_merge_becomes_done",
    ),
    "AC-214": Proof(
        "hermes/runtime/test_sdd_runtime_guard.py",
        "test_worker_can_only_touch_scope_and_its_task_local_journal",
    ),
    "AC-215": Proof(
        "hermes/runtime/test_sdd_wave_synthesizer.py",
        "test_t012_t5_only_synthesizer_writes_three_shared_artifacts",
    ),
    "AC-216": Proof(
        "hermes/runtime/test_sdd_runtime_guard.py",
        "test_crash_before_marker_rolls_back_complete_old_set",
    ),
    "AC-217": Proof(
        "hermes/runtime/test_sdd_wave_synthesizer.py",
        "test_t012_t8_runtime_recovery_returns_only_complete_old_or_new_set",
    ),
}


def _load_object(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GuardError(f"{label} is unavailable or invalid: {error}") from error
    if not isinstance(value, dict):
        raise GuardError(f"{label} must be a JSON object")
    return value


def _feature_directory(root: Path, feature_id: str) -> Path:
    if FEATURE_ID.fullmatch(feature_id) is None:
        raise GuardError("invalid feature ID")
    feature = root / ".specs" / feature_id
    if feature.is_symlink():
        raise GuardError("symbolic feature directory refused")
    try:
        resolved = feature.resolve(strict=True)
    except FileNotFoundError as error:
        raise GuardError("feature directory is unavailable") from error
    if resolved.parent != (root / ".specs").resolve(strict=True):
        raise GuardError("feature directory escapes repository")
    return resolved


def validate_argv(argv: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(argv)
    if not normalized or any(not isinstance(item, str) or not item for item in normalized):
        raise GuardError("gate argv must be a non-empty string sequence")
    if FORBIDDEN_ARGUMENTS.intersection(normalized):
        raise GuardError("test bypass argument refused")
    return normalized


def validate_preconditions(
    repo_root: Path | str,
    feature_id: str,
    *,
    now: float | None = None,
) -> dict[str, object]:
    root = Path(repo_root).resolve(strict=True)
    harness = root / ".github" / "scripts" / "harness.sh"
    if harness.is_symlink() or not harness.is_file() or not (harness.stat().st_mode & 0o111):
        raise GuardError("executable harness is unavailable")
    feature = _feature_directory(root, feature_id)
    state = _load_object(feature / ".tdd-state.json", "TDD state")
    tasks = state.get("tasks")
    if not isinstance(tasks, dict) or not tasks:
        raise GuardError("TDD state has no tasks")
    unfinished = [
        task_id
        for task_id, task in tasks.items()
        if not isinstance(task, dict) or task.get("phase") != "done"
    ]
    if unfinished:
        raise GuardError("tasks are not done: " + ", ".join(sorted(unfinished)))
    summary = _load_object(root / "target" / "harness-summary.json", "harness summary")
    if summary.get("bypassed", False) is not False:
        raise GuardError("harness bypass detected")
    generated_at = _parse_timestamp(summary.get("generated_at", summary.get("started_at")))
    if generated_at is None:
        raise GuardError("harness summary has no freshness timestamp")
    current_time = time.time() if now is None else now
    if generated_at > current_time or current_time - generated_at > FRESHNESS_SECONDS:
        raise GuardError("harness results are stale")
    status = summary.get("status")
    if status is None:
        gates = summary.get("gates")
        if not isinstance(gates, dict) or not gates:
            raise GuardError("harness summary has no gate results")
        gate_statuses = {
            gate.get("status")
            for gate in gates.values()
            if isinstance(gate, dict)
        }
        status = "FAIL" if "fail" in gate_statuses else "PASS"
        summary = {**summary, "status": status}
    if status not in {item.value for item in TechnicalVerdict}:
        raise GuardError("harness status must be PASS or FAIL")
    return summary


def _parse_timestamp(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _safe_relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise GuardError(f"unsafe changed path: {value}")
    return path


def route_validators(changed_paths: Sequence[str]) -> tuple[str, ...]:
    spring = False
    react = False
    for value in changed_paths:
        path = _safe_relative_path(value)
        spring = spring or path.suffix.lower() in SPRING_SUFFIXES or str(path) == "pom.xml"
        react = react or path.suffix.lower() in REACT_SUFFIXES or str(path) == "package.json"
    validators = []
    if spring:
        validators.append("spring")
    if react:
        validators.append("react-nextjs")
    if not validators:
        raise GuardError("no Spring or React source changes detected")
    return tuple(validators)


def delegation_requests(
    validators: Sequence[str], changed_paths: Sequence[str]
) -> tuple[dict[str, object], ...]:
    paths = tuple(str(_safe_relative_path(path)) for path in changed_paths)
    allowed = {"spring", "react-nextjs"}
    if not validators or not set(validators).issubset(allowed):
        raise GuardError("unknown validator")
    return tuple({"stack": validator, "changed_paths": paths} for validator in validators)


def _default_runner(argv: tuple[str, ...]) -> GateResult:
    result = subprocess.run(argv, check=False, capture_output=True, text=True)
    output = (result.stdout + result.stderr)[-20_000:]
    return GateResult(argv[0], argv, result.returncode, output)


def sanitize_output(output: str, repo_root: Path) -> str:
    sanitized = output.replace(str(repo_root), "[REPOSITORY]")
    sanitized = sanitized.replace(str(repo_root.resolve()), "[REPOSITORY]")
    for pattern in SECRET_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)
    return sanitized


def execute_heavy_gates(
    repo_root: Path | str,
    commands: Mapping[str, Sequence[str]],
    *,
    runner: Callable[[tuple[str, ...]], GateResult] = _default_runner,
    runtime: object = canonical_runtime,
) -> dict[str, GateResult]:
    if set(commands) != set(HEAVY_GATES):
        raise GuardError("commands must define Maven, Next, PIT and OWASP gates exactly")
    results: dict[str, GateResult] = {}
    for gate_name in HEAVY_GATES:
        argv = validate_argv(commands[gate_name])
        with runtime.global_lock(Path(repo_root)):
            result = runner(argv)
        if not isinstance(result, GateResult):
            raise GuardError(f"{gate_name} runner returned an unstructured result")
        results[gate_name] = GateResult(
            gate_name,
            result.argv,
            result.returncode,
            sanitize_output(result.output, Path(repo_root)),
        )
    return results


def fan_in(results: Sequence[ValidatorResult]) -> AggregateResult:
    validators = tuple(results)
    if not validators or any(not isinstance(result, ValidatorResult) for result in validators):
        raise GuardError("fan-in requires structured validator results")
    stacks = [result.stack for result in validators]
    if len(stacks) != len(set(stacks)) or not set(stacks).issubset({"spring", "react-nextjs"}):
        raise GuardError("fan-in validator stacks are invalid or duplicated")
    passed = all(
        result.gates
        and set(result.gates.values()) == {TechnicalVerdict.PASS.value}
        and result.coverage is not None
        and result.coverage >= 95.0
        and bool(result.traceability)
        for result in validators
    )
    verdict = TechnicalVerdict.PASS if passed else TechnicalVerdict.FAIL
    decision = Decision.APPROVE if passed else Decision.REQUEST_CHANGES
    return AggregateResult(validators, verdict, decision)


def write_reports(
    repo_root: Path | str,
    feature_id: str,
    validation_report: str,
    traceability_report: str,
    *,
    runtime: object = canonical_runtime,
) -> tuple[Path, Path]:
    if not validation_report.strip() or not traceability_report.strip():
        raise GuardError("reports must not be empty")
    root = Path(repo_root).resolve(strict=True)
    feature = _feature_directory(root, feature_id)
    targets = tuple(feature / name for name in ALLOWED_REPORTS)
    for target in targets:
        if target.is_symlink():
            raise GuardError(f"symbolic report target refused: {target.name}")
    with runtime.global_lock(root):
        for target, content in zip(
            targets, (validation_report, traceability_report), strict=True
        ):
            runtime.atomic_replace(target, content.encode("utf-8"))
    return targets
