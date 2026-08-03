#!/usr/bin/env python3
"""Generate an inspectable VPS pilot plan without executing any operation."""

from __future__ import annotations

import json
from pathlib import Path
import re


TEMPLATE_PATH = Path(__file__).parent / "templates" / "vps-pilot-plan.template.json"
BOARD_PLACEHOLDER = "{{BOARD_SLUG}}"
BOARD_SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SCHEMA_VERSION = 1
PROFILE_NAME = "staaack"
DRY_RUN_MODE = "dry-run"
BOUNDED_VALUE = 2
BOUNDED_VALUE_TEXT = "2"
DELEGATION_DEPTH = 1
EXPECTED_COMMAND_IDS = (
    "set-max-spawn",
    "set-max-in-progress",
    "set-max-in-progress-per-profile",
    "set-failure-limit",
    "set-delegation-depth",
    "disable-subagent-auto-approve",
    "dry-run-dispatch",
    "verify-configuration",
)
EXPECTED_KANBAN_CONFIGURATION = {
    "max_spawn": BOUNDED_VALUE,
    "max_in_progress": BOUNDED_VALUE,
    "max_in_progress_per_profile": BOUNDED_VALUE,
    "failure_limit": BOUNDED_VALUE,
}
EXPECTED_CONFIGURATION_CHECK = ["hermes", "config", "check"]
EXPECTED_DRY_RUN_DISPATCH = [
    "hermes",
    "kanban",
    "dispatch",
    "--board",
    BOARD_PLACEHOLDER,
    "--dry-run",
    "--max",
    BOUNDED_VALUE_TEXT,
    "--max-workers",
    BOUNDED_VALUE_TEXT,
]
EXPECTED_TEMPLATE_FIELDS = {
    "schema_version",
    "profile",
    "mode",
    "configuration",
    "dry_run",
    "commands",
    "execution",
    "evidence",
}


def validate_template(template: object) -> None:
    """Reject a template that could weaken or execute the bounded dry-run."""

    if (
        not isinstance(template, dict)
        or template.get("schema_version") != SCHEMA_VERSION
    ):
        raise ValueError("pilot template must use schema version 1")
    if set(template) != EXPECTED_TEMPLATE_FIELDS:
        raise ValueError("pilot template fields must match the closed schema")
    if (
        template.get("profile") != PROFILE_NAME
        or template.get("mode") != DRY_RUN_MODE
    ):
        raise ValueError("pilot template must target the staaack dry-run")

    configuration = template.get("configuration")
    if not isinstance(configuration, dict):
        raise ValueError("pilot template configuration is required")
    if configuration.get("kanban") != EXPECTED_KANBAN_CONFIGURATION:
        raise ValueError("pilot template Kanban limits must all equal two")
    if configuration.get("delegation") != {
        "max_spawn_depth": DELEGATION_DEPTH
    }:
        raise ValueError("pilot template delegation depth must equal one")
    if configuration.get("subagent_auto_approve") is not False:
        raise ValueError("pilot template must disable subagent auto-approve")

    dry_run = template.get("dry_run")
    if not isinstance(dry_run, dict):
        raise ValueError("pilot template dry-run configuration is required")
    if dry_run != {
        "board": BOARD_PLACEHOLDER,
        "max_workers": BOUNDED_VALUE,
        "requested": True,
        "dispatched": False,
    }:
        raise ValueError("pilot template must describe an inert two-worker dry-run")

    commands = template.get("commands")
    if not isinstance(commands, list) or len(commands) != len(EXPECTED_COMMAND_IDS):
        raise ValueError("pilot template must contain the complete command sequence")
    for command in commands:
        if not isinstance(command, dict) or set(command) != {
            "order",
            "id",
            "argv",
            "execute",
        }:
            raise ValueError("pilot template commands must use structured argv")
        argv = command.get("argv")
        if not isinstance(argv, list) or any(
            not isinstance(argument, str) for argument in argv
        ):
            raise ValueError("pilot template commands must use structured argv")
    if [command.get("order") for command in commands] != list(
        range(1, len(commands) + 1)
    ):
        raise ValueError("pilot template commands must be strictly ordered")
    if tuple(command.get("id") for command in commands) != EXPECTED_COMMAND_IDS:
        raise ValueError("pilot template command identifiers are invalid")
    if any(command.get("execute") is not False for command in commands):
        raise ValueError("pilot template commands must remain inert")
    if commands[-1].get("argv") != EXPECTED_CONFIGURATION_CHECK:
        raise ValueError("pilot template must finish with configuration verification")

    dispatch = commands[-2].get("argv")
    if dispatch != EXPECTED_DRY_RUN_DISPATCH:
        raise ValueError("pilot template dispatch must be board-explicit and bounded")
    if template.get("execution") != {"performed": False, "external_access": False}:
        raise ValueError("pilot template must prohibit execution and external access")
    if template.get("evidence") != "redacted":
        raise ValueError("pilot template evidence must be redacted")


def generate_pilot_dry_run(board_slug: str) -> dict[str, object]:
    """Materialize the validated plan for one explicit board slug."""

    if not isinstance(board_slug, str) or not BOARD_SLUG_PATTERN.fullmatch(board_slug):
        raise ValueError("board slug must contain lowercase letters, digits and hyphens")

    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    validate_template(template)
    encoded = json.dumps(template)
    return json.loads(encoded.replace(BOARD_PLACEHOLDER, board_slug))
