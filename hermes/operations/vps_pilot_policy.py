"""Pure validation of the VPS pilot policy.

The module receives structured in-memory data and returns stable violation
codes. It deliberately owns no execution, network, SSH, or persistence
primitive.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


HERMES_ABSOLUTE_BINARY = "/home/ubuntu/.local/bin/hermes"
RETAINED_RESOURCES = ("card", "branch", "worktree", "logs", "journal")


def validate_vps_pilot_policy(policy: Mapping[str, Any]) -> tuple[str, ...]:
    """Return every VPS pilot policy violation in a stable domain order."""

    violations: list[str] = []
    _validate_evidence(_section(policy, "evidence"), violations)
    _validate_hermes(_section(policy, "hermes"), violations)
    _validate_delegation(_section(policy, "delegation"), violations)
    sandbox = _section(policy, "sandbox")
    gateway = _section(policy, "gateway")
    _validate_gateway(sandbox, gateway, violations)
    _validate_retention(_section(policy, "retention"), violations)
    return tuple(violations)


def _section(policy: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = policy.get(name)
    if isinstance(value, Mapping):
        return value
    return {}


def _validate_evidence(evidence: Mapping[str, Any], violations: list[str]) -> None:
    forbidden_flags = (
        ("contains_secret", "evidence.secret_forbidden"),
        ("contains_token", "evidence.token_forbidden"),
        ("contains_credential", "evidence.credential_forbidden"),
        ("contains_transcript", "evidence.transcript_forbidden"),
    )
    for field, violation in forbidden_flags:
        if evidence.get(field) is not False:
            violations.append(violation)

    paths = evidence.get("paths")
    if not _has_only_relative_paths(paths):
        violations.append("evidence.absolute_path_forbidden")


def _has_only_relative_paths(paths: object) -> bool:
    if not isinstance(paths, Sequence) or isinstance(paths, (str, bytes)):
        return False
    return all(
        isinstance(path, str)
        and bool(path)
        and not path.startswith("/")
        and not (len(path) >= 3 and path[1:3] in (":/", ":\\"))
        for path in paths
    )


def _validate_hermes(hermes: Mapping[str, Any], violations: list[str]) -> None:
    uses_login_shell = hermes.get("login_shell") is True
    uses_absolute_binary = hermes.get("binary") == HERMES_ABSOLUTE_BINARY
    if not uses_login_shell and not uses_absolute_binary:
        violations.append("hermes.login_shell_or_absolute_binary_required")
    if not isinstance(hermes.get("board"), str) or not hermes["board"].strip():
        violations.append("hermes.explicit_board_required")
    if hermes.get("yolo") is not False:
        violations.append("hermes.yolo_forbidden")


def _validate_delegation(
    delegation: Mapping[str, Any], violations: list[str]
) -> None:
    if delegation.get("max_spawn_depth") != 1:
        violations.append("delegation.max_spawn_depth_must_equal_one")
    if delegation.get("subagent_auto_approve") is not False:
        violations.append("delegation.auto_approve_forbidden")


def _validate_gateway(
    sandbox: Mapping[str, Any],
    gateway: Mapping[str, Any],
    violations: list[str],
) -> None:
    installation_requested = gateway.get("install_requested") is True
    successful_jobs = sandbox.get("successful_parallel_jobs")
    has_two_successful_jobs = (
        isinstance(successful_jobs, int)
        and not isinstance(successful_jobs, bool)
        and successful_jobs >= 2
    )
    if installation_requested and not has_two_successful_jobs:
        violations.append("gateway.two_successful_jobs_required")
    if gateway.get("scope") != "user":
        violations.append("gateway.system_scope_forbidden")
    if gateway.get("uses_sudo") is not False:
        violations.append("gateway.sudo_forbidden")


def _validate_retention(
    retention: Mapping[str, Any], violations: list[str]
) -> None:
    if retention.get("proofs_complete") is True:
        return
    for resource in RETAINED_RESOURCES:
        if retention.get(f"{resource}_retained") is not True:
            violations.append(f"retention.{resource}_must_be_retained")
