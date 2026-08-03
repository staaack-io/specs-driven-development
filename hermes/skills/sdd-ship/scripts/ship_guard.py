#!/usr/bin/env python3
"""Deterministic, non-deploying safety boundary for Hermes ``/sdd-ship``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import NamedTuple, Sequence


def discover_repo_root(module_path: Path | str) -> Path:
    """Find the nearest source or profile root publishing the Hermes runtime."""

    resolved = Path(module_path).resolve(strict=True)
    for candidate in resolved.parents:
        runtime_guard = candidate / "hermes" / "runtime" / "sdd_runtime_guard.py"
        if runtime_guard.is_file() and not runtime_guard.is_symlink():
            return candidate
    raise RuntimeError("cannot locate hermes/runtime/sdd_runtime_guard.py from ship guard")


REPO_ROOT = discover_repo_root(Path(__file__))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from hermes.runtime import sdd_runtime_guard as canonical_runtime  # noqa: E402


FEATURE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
BASE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,199}$")
SECRET_PATTERNS = (
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)
SENSITIVE_PATH = re.compile(r"(?:^|\s)(?:/|[A-Za-z]:\\\\)")
AC_IDS = ("AC-152", "AC-153", "AC-235", "AC-261", "AC-262", "AC-263")
PASSING_REVIEWS = frozenset({"Approve", "Approve with waivers"})
GATE_NAMES = ("validation", "review", "questions", "baseline", "scope", "diff")


class GuardError(RuntimeError):
    """A ship-plan safety or completeness check failed."""


class ShipRequest(NamedTuple):
    feature_id: str | None
    base_ref: str


@dataclass(frozen=True)
class PreShipEvidence:
    validation: str
    review: str
    open_questions: tuple[str, ...]
    baseline_regressions: tuple[str, ...]
    out_of_scope_paths: tuple[str, ...]
    diff_nonempty: bool


@dataclass(frozen=True)
class RollbackPlan:
    detection: str
    limit_damage: str
    restore_state: str
    limit_within_minutes: int = 5


@dataclass(frozen=True)
class ObservabilitySurface:
    surface: str
    metric: str
    log_keys: tuple[str, ...]
    alert: str
    dashboard: str
    justification: str = ""


@dataclass(frozen=True)
class FeatureFlag:
    name: str
    default: str
    emergency_stop: str
    owner: str
    removal: str


@dataclass(frozen=True)
class ShipPlan:
    rollback: RollbackPlan
    observability: tuple[ObservabilitySurface, ...]
    feature_flag: FeatureFlag
    external_notes: tuple[str, ...]
    internal_notes: tuple[str, ...]
    deployment_command: str


def parse_invocation(arguments: Sequence[str]) -> ShipRequest:
    """Parse the optional feature and base reference without interpreting either."""

    values = tuple(arguments)
    feature_id: str | None = None
    base_ref = "origin/main"
    index = 0
    if values and values[0] != "--base":
        feature_id = values[0]
        index = 1
    if index < len(values):
        if values[index] != "--base" or index + 2 != len(values):
            raise GuardError("invalid /sdd-ship arguments")
        base_ref = values[index + 1]
    if feature_id is not None and FEATURE_ID.fullmatch(feature_id) is None:
        raise GuardError("invalid feature ID")
    if BASE_REF.fullmatch(base_ref) is None or ".." in base_ref:
        raise GuardError("invalid base reference")
    return ShipRequest(feature_id, base_ref)


def validate_preconditions(evidence: PreShipEvidence) -> tuple[str, ...]:
    """Fail closed at the first incomplete pre-ship gate."""

    if evidence.validation != "PASS":
        raise GuardError("validation gate is not PASS")
    if evidence.review not in PASSING_REVIEWS:
        raise GuardError("review gate is not approved")
    if evidence.open_questions:
        raise GuardError("question gate contains unresolved Q-NNN")
    if evidence.baseline_regressions:
        raise GuardError("baseline gate contains regressions")
    if evidence.out_of_scope_paths:
        raise GuardError("scope gate contains out-of-scope paths")
    if evidence.diff_nonempty is not True:
        raise GuardError("diff gate is empty")
    return GATE_NAMES


def _require_text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GuardError(f"{field} must be explicit")
    return value.strip()


def validate_rollback(rollback: RollbackPlan) -> RollbackPlan:
    detection = _require_text(rollback.detection, "detection")
    limit_damage = _require_text(rollback.limit_damage, "limit_damage")
    restore_state = _require_text(rollback.restore_state, "restore_state")
    normalized_restore = restore_state.casefold()
    if normalized_restore in {"revert commit", "annuler le commit"}:
        raise GuardError("restore_state must describe state restoration")
    if not 1 <= rollback.limit_within_minutes <= 5:
        raise GuardError("limit_damage must act within five minutes")
    return RollbackPlan(
        detection,
        limit_damage,
        restore_state,
        rollback.limit_within_minutes,
    )


def validate_observability(
    surfaces: Sequence[ObservabilitySurface],
) -> tuple[ObservabilitySurface, ...]:
    normalized = tuple(surfaces)
    if not normalized:
        raise GuardError("observability inventory must not be empty")
    for surface in normalized:
        _require_text(surface.surface, "observability surface")
        if surface.justification.strip():
            continue
        _require_text(surface.metric, "metric")
        if not {"feature_id", "ac_id"}.issubset(surface.log_keys):
            raise GuardError("log keys must include feature_id and ac_id")
        _require_text(surface.alert, "alert")
        _require_text(surface.dashboard, "dashboard")
    return normalized


def validate_feature_flag(flag: FeatureFlag) -> FeatureFlag:
    values = {
        "name": flag.name,
        "default": flag.default,
        "emergency_stop": flag.emergency_stop,
        "owner": flag.owner,
        "removal": flag.removal,
    }
    for field, value in values.items():
        _require_text(value, field)
    return flag


def _contains_secret(value: str) -> bool:
    return any(pattern.search(value) is not None for pattern in SECRET_PATTERNS)


def _contains_sensitive_path(value: str) -> bool:
    return SENSITIVE_PATH.search(value) is not None


def validate_release_notes(
    external_notes: Sequence[str], internal_notes: Sequence[str]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    external = tuple(external_notes)
    internal = tuple(internal_notes)
    if not external or len(external) > 3 or any(not note.strip() for note in external):
        raise GuardError("external release notes require one to three entries")
    if not internal or any(not note.strip() for note in internal):
        raise GuardError("internal release notes must not be empty")
    if any(_contains_secret(note) for note in external + internal):
        raise GuardError("secret detected in release notes")
    if any(_contains_sensitive_path(note) for note in external + internal):
        raise GuardError("sensitive local path detected in release notes")
    return external, internal


def validate_plan(plan: ShipPlan) -> ShipPlan:
    validate_rollback(plan.rollback)
    validate_observability(plan.observability)
    validate_feature_flag(plan.feature_flag)
    validate_release_notes(plan.external_notes, plan.internal_notes)
    command = _require_text(plan.deployment_command, "deployment command data")
    if (
        "\n" in command
        or "\r" in command
        or "```" in command
        or _contains_secret(command)
        or _contains_sensitive_path(command)
    ):
        raise GuardError("deployment command data is unsafe to display")
    return plan


def _render_plan(feature_id: str, plan: ShipPlan) -> str:
    observability_rows = "\n".join(
        "| "
        + " | ".join(
            (
                surface.surface,
                surface.metric,
                ", ".join(surface.log_keys) or "n/a",
                surface.alert,
                surface.dashboard,
                surface.justification or "n/a",
            )
        )
        + " |"
        for surface in plan.observability
    )
    external_notes = "\n".join(f"- {note}" for note in plan.external_notes)
    internal_notes = "\n".join(f"- {note}" for note in plan.internal_notes)
    flag = plan.feature_flag
    rollback = plan.rollback
    return f"""# Plan de livraison : {feature_id}

## Pre-ship gates

Toutes les portes sont `PASS` : validation, review, questions, baseline, scope et diff.

## Feature flag

- Nom : `{flag.name}`
- Valeur par défaut : `{flag.default}`
- Arrêt d'urgence : {flag.emergency_stop}
- Responsable : {flag.owner}
- Retrait : {flag.removal}

## Observability

| Surface | Métrique | Clés de journal | Alerte | Dashboard | Justification |
| --- | --- | --- | --- | --- | --- |
{observability_rows}

## Rollback

1. Détection : {rollback.detection}
2. Limitation en {rollback.limit_within_minutes} minute(s) maximum : {rollback.limit_damage}
3. Restauration : {rollback.restore_state}

## Release notes externes

{external_notes}

## Release notes internes

{internal_notes}

## Commande de déploiement

commande affichée uniquement, jamais exécutée par Hermes :

```text
{plan.deployment_command}
```

## Traçabilité

{', '.join(AC_IDS)}
"""


def _feature_directory(root: Path, feature_id: str) -> Path:
    if FEATURE_ID.fullmatch(feature_id) is None:
        raise GuardError("invalid feature ID")
    specs = root / ".specs"
    feature = specs / feature_id
    if feature.is_symlink():
        raise GuardError("symbolic feature directory refused")
    try:
        resolved = feature.resolve(strict=True)
        specs_resolved = specs.resolve(strict=True)
    except FileNotFoundError as error:
        raise GuardError("feature directory is unavailable") from error
    if resolved.parent != specs_resolved:
        raise GuardError("feature directory escapes repository")
    return resolved


def publish_ship_plan(
    repo_root: Path | str,
    feature_id: str,
    evidence: PreShipEvidence,
    plan: ShipPlan,
    *,
    runtime: object = canonical_runtime,
) -> Path:
    """Publish one atomic plan after validation; never execute its command data."""

    validate_preconditions(evidence)
    validate_plan(plan)
    root = Path(repo_root).resolve(strict=True)
    feature = _feature_directory(root, feature_id)
    target = feature / "09-ship-plan.md"
    if target.is_symlink():
        raise GuardError("symbolic ship plan target refused")
    content = _render_plan(feature_id, plan).encode("utf-8")
    relative_target = f".specs/{feature_id}/09-ship-plan.md"
    runtime.validate_worker_changes(
        feature_id=feature_id,
        task_id="T-022",
        files_in_scope=[relative_target],
        changed_paths=[relative_target],
    )
    with runtime.global_lock(root):
        runtime.atomic_replace(target, content)
    return target
