#!/usr/bin/env python3
"""Deterministic safety boundary for the Hermes ``/sdd-review`` skill."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Sequence


def discover_repo_root(module_path: Path | str) -> Path:
    """Find the nearest source or profile root that publishes Hermes runtime."""

    resolved = Path(module_path).resolve(strict=True)
    for candidate in resolved.parents:
        runtime_guard = candidate / "hermes" / "runtime" / "sdd_runtime_guard.py"
        if runtime_guard.is_file() and not runtime_guard.is_symlink():
            return candidate
    raise RuntimeError("cannot locate hermes/runtime/sdd_runtime_guard.py from review guard")


REPO_ROOT = discover_repo_root(Path(__file__))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from hermes.runtime import sdd_runtime_guard as canonical_runtime  # noqa: E402


FEATURE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
BASE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")
SPRING_SUFFIXES = frozenset({".java", ".kt", ".kts", ".sql"})
REACT_SUFFIXES = frozenset({".js", ".jsx", ".ts", ".tsx"})
SPRING_STACK = "spring"
REACT_STACK = "react-nextjs"
ALLOWED_STACKS = frozenset({SPRING_STACK, REACT_STACK})
ALLOWED_SEVERITIES = frozenset({"must-fix", "should-fix", "nit", "praise"})
BASE_OPTION = "--base"
SPECS_DIRECTORY = ".specs"
REPORT_NAME = "08-code-review.md"
REDACTED = "[REDACTED]"
SECRET_PATTERNS = (
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)\b(?:token|secret|password|api[-_]?key)\s*[:=]\s*\S+"),
)
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
ABSOLUTE_PATH = re.compile(r"(?<![\w.])/(?:[^/\s]+/)+[^/\s]+")


class GuardError(RuntimeError):
    """A review safety or contract check failed."""


class ReviewVerdict(str, Enum):
    """Closed, informative review vocabulary."""

    APPROVE = "approve"
    REQUEST_CHANGES = "request-changes"


@dataclass(frozen=True)
class Invocation:
    feature_id: str | None
    base_ref: str


@dataclass(frozen=True)
class Finding:
    stack: str
    severity: str
    path: str
    line: int
    evidence: str
    suggested_fix: str


@dataclass(frozen=True)
class ReviewResult:
    verdict: ReviewVerdict
    findings: tuple[Finding, ...]

    @property
    def blocking(self) -> bool:
        """A technical review informs the workflow and never gates Git actions."""

        return False


def parse_invocation(argv: Sequence[str]) -> Invocation:
    """Parse optional feature and base values without evaluating a shell."""

    values = tuple(argv)
    feature_id: str | None = None
    base_ref = "origin/main"
    index = 0
    if index < len(values) and values[index] != BASE_OPTION:
        feature_id = values[index]
        if FEATURE_ID.fullmatch(feature_id) is None:
            raise GuardError("invalid feature argument")
        index += 1
    if index < len(values):
        if values[index] != BASE_OPTION or index + 1 >= len(values):
            raise GuardError("invalid argument order")
        base_ref = values[index + 1]
        index += 2
    if index != len(values) or BASE_REF.fullmatch(base_ref) is None or ".." in base_ref:
        raise GuardError("invalid base argument")
    return Invocation(feature_id, base_ref)


def _safe_relative_path(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise GuardError(f"unsafe changed path: {value}")
    return str(path)


def route_reviewers(changed_paths: Sequence[str]) -> tuple[str, ...]:
    """Select specialized read-only reviewers from the changed source paths."""

    spring = False
    react = False
    for value in changed_paths:
        path = PurePosixPath(_safe_relative_path(value))
        suffix = path.suffix.lower()
        spring = spring or suffix in SPRING_SUFFIXES or str(path) == "pom.xml"
        react = react or suffix in REACT_SUFFIXES or str(path) == "package.json"
    reviewers = []
    if spring:
        reviewers.append(SPRING_STACK)
    if react:
        reviewers.append(REACT_STACK)
    if not reviewers:
        raise GuardError("no Spring or React source changes detected")
    return tuple(reviewers)


def delegation_requests(
    reviewers: Sequence[str],
    changed_paths: Sequence[str],
    artifacts: Sequence[str],
) -> tuple[dict[str, object], ...]:
    """Build immutable read inputs without exposing the shared report writer."""

    stacks = tuple(reviewers)
    valid_stacks = set(stacks).issubset(ALLOWED_STACKS)
    if not stacks or len(stacks) != len(set(stacks)) or not valid_stacks:
        raise GuardError("unknown or duplicate reviewer")
    paths = tuple(_safe_relative_path(path) for path in changed_paths)
    readable_artifacts = tuple(_safe_relative_path(path) for path in artifacts)
    return tuple(
        {"stack": stack, "changed_paths": paths, "artifacts": readable_artifacts}
        for stack in stacks
    )


def validate_delegate_changes(
    *, feature_id: str, task_id: str, runtime: object = canonical_runtime
) -> None:
    """Prove that read-only delegates returned no filesystem changes."""

    runtime.validate_worker_changes(
        feature_id=feature_id,
        task_id=task_id,
        changed_paths=(),
        files_in_scope=(),
    )


def _validate_finding(finding: Finding) -> None:
    if finding.stack not in ALLOWED_STACKS:
        raise GuardError("finding has an unknown stack")
    if finding.severity not in ALLOWED_SEVERITIES:
        raise GuardError("finding has an unknown severity")
    _safe_relative_path(finding.path)
    complete = (
        finding.line >= 1
        and bool(finding.evidence.strip())
        and bool(finding.suggested_fix.strip())
    )
    if not complete:
        raise GuardError("finding is incomplete")


def fan_in(batches: Sequence[Sequence[Finding]]) -> tuple[Finding, ...]:
    """Validate and deduplicate structured findings in stable arrival order."""

    findings: list[Finding] = []
    seen: set[Finding] = set()
    for batch in batches:
        for finding in batch:
            if not isinstance(finding, Finding):
                raise GuardError("fan-in requires structured findings")
            _validate_finding(finding)
            if finding not in seen:
                seen.add(finding)
                findings.append(finding)
    return tuple(findings)


def redact_evidence(value: str, *, repo_root: Path | str) -> str:
    """Remove local paths, credentials, personal data and business identifiers."""

    root = str(Path(repo_root).resolve(strict=True))
    redacted = value.replace(root, "[REPOSITORY]")
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(REDACTED, redacted)
    redacted = EMAIL_PATTERN.sub(REDACTED, redacted)
    return ABSOLUTE_PATH.sub(REDACTED, redacted)


def _feature_directory(root: Path, feature_id: str) -> Path:
    if FEATURE_ID.fullmatch(feature_id) is None:
        raise GuardError("invalid feature ID")
    feature = root / SPECS_DIRECTORY / feature_id
    if feature.is_symlink():
        raise GuardError("symbolic feature directory refused")
    try:
        resolved = feature.resolve(strict=True)
    except FileNotFoundError as error:
        raise GuardError("feature directory is unavailable") from error
    if resolved.parent != (root / SPECS_DIRECTORY).resolve(strict=True):
        raise GuardError("feature directory escapes repository")
    return resolved


def write_report(
    repo_root: Path | str,
    feature_id: str,
    content: str,
    *,
    runtime: object = canonical_runtime,
) -> Path:
    """Atomically publish the sole shared review report."""

    if not content.strip():
        raise GuardError("review report must not be empty")
    root = Path(repo_root).resolve(strict=True)
    relative = f"{SPECS_DIRECTORY}/{feature_id}/{REPORT_NAME}"
    target = _feature_directory(root, feature_id) / REPORT_NAME
    if target.is_symlink():
        raise GuardError("symbolic report target refused")
    runtime.validate_worker_changes(
        feature_id=feature_id,
        task_id="T-021",
        changed_paths=[relative],
        files_in_scope=[relative],
    )
    redacted_content = redact_evidence(content, repo_root=root)
    with runtime.global_lock(root):
        runtime.atomic_replace(target, redacted_content.encode("utf-8"))
    return target
