#!/usr/bin/env python3
"""Deterministic source contract for the complete S-002 fan-in."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FEATURE_ROOT = REPOSITORY_ROOT / ".specs/2026-07-31-hermes-parallel-sdd"
TASKS = FEATURE_ROOT / "04-tasks.md"
ROADMAP = FEATURE_ROOT / "03a-epic-roadmap.md"
HELP_SKILL = REPOSITORY_ROOT / "hermes/skills/sdd-help/SKILL.md"
HERMES_README = REPOSITORY_ROOT / "hermes/README.md"
ARTIFACT_CONTRACT = REPOSITORY_ROOT / "docs/artifact-contract.md"
CODEX_MIGRATION = REPOSITORY_ROOT / "docs/codex-migration.md"
EPIC_PLAN_COMMAND = "/sdd-epic-plan"
WIRE_HARNESS_COMMAND = "/sdd-wire-harness"
ROLES_COMMAND = "/sdd-roles"
CONVERTED_STATUS = "converti"
EXTERNAL_T008 = "external:T-008"
PENDING_EXTERNAL = "pending-external"
SATISFIED = "satisfied"
TABLE_DELIMITER = "|"
STEP_COLUMN = 0
COMMAND_COLUMN = 1
STATUS_OR_COMMANDS_COLUMN = 2
TABLE_COLUMN_COUNT = 3
STEP_HEADER = "Étape"
UTF8 = "utf-8"
AC_PATTERN = re.compile(r"AC-(\d{3})(?:\s*[–-]\s*AC-(\d{3}))?")
LOCAL_PATH_PATTERN = re.compile(r"(?:/Users/|/home/[^/<\s]+/|/private/tmp/|[A-Z]:\\Users\\)")
CREDENTIAL_PATTERN = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
    r"AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
)
FORBIDDEN_SCHEDULER_MODULES = {"apscheduler", "sched", "schedule"}
FORBIDDEN_RUNTIME_NAMES = {
    "auto_merge",
    "enable_auto_merge",
    "merge_pull_request",
    "run_pending",
    "schedule_job",
}
PRODUCTION_PYTHON = (
    "hermes/runtime/sdd_runtime_guard.py",
    "hermes/runtime/sdd_github_bridge.py",
    "hermes/skills/sdd-epic-plan/scripts/epic_plan_guard.py",
    "hermes/skills/sdd-wire-harness/scripts/harness_guard.py",
    "hermes/skills/sdd-status/scripts/status_guard.py",
)
PUBLIC_RELEASE_DOCUMENTS = (
    "hermes/README.md",
    "hermes/skills/sdd-help/SKILL.md",
    "docs/artifact-contract.md",
    "docs/codex-migration.md",
)


@dataclass(frozen=True)
class Evidence:
    ac_ids: tuple[str, ...]
    relative_path: str
    marker: str
    status: str = SATISFIED


def expand_ac_ranges(*ranges: tuple[int, int]) -> tuple[str, ...]:
    return tuple(
        f"AC-{number:03d}"
        for first, last in ranges
        for number in range(first, last + 1)
    )


def evidence(
    first: int,
    last: int,
    relative_path: str,
    marker: str,
    status: str = SATISFIED,
) -> Evidence:
    return Evidence(expand_ac_ranges((first, last)), relative_path, marker, status)


EXPECTED_S002_ACS = set(
    expand_ac_ranges(
        (1, 7),
        (11, 12),
        (25, 26),
        (48, 80),
        (101, 123),
        (243, 249),
        (252, 256),
        (276, 280),
    )
)


EVIDENCE_GROUPS = (
    evidence(1, 1, "hermes/runtime/github-bridge-contract.md", "Kanban natif Hermes 0.19"),
    evidence(2, 2, "hermes/runtime/github-bridge-contract.md", "ni boucle d'admission"),
    evidence(3, 3, "hermes/skills/sdd-epic-plan/SKILL.md", "`delegate_task`"),
    evidence(4, 4, "hermes/runtime/sdd_runtime_guard.py", "MAX_WORKERS = 2"),
    evidence(5, 5, "docs/artifact-contract.md", "`max_read_only_analyses`"),
    evidence(6, 6, "docs/artifact-contract.md", "`max_heavy_gates`"),
    evidence(7, 7, ".github/ISSUE_TEMPLATE/feature_request.yml", "name:"),
    evidence(11, 11, "hermes/skills/sdd-wire-harness/SKILL.md", "name: sdd-wire-harness"),
    evidence(12, 12, "hermes/skills/sdd-epic-plan/SKILL.md", "name: sdd-epic-plan"),
    evidence(25, 25, "hermes/skills/sdd-help/SKILL.md", "n'est pas une commande publique `/sdd-roles`"),
    evidence(26, 26, "hermes/README.md", "bibliothèque interne"),
    evidence(48, 57, "hermes/runtime/sdd_runtime_guard.py", "def validate_state("),
    evidence(58, 60, "hermes/runtime/test_sdd_runtime_guard.py", "test_unknown_version_and_sensitive_fields_fail_closed"),
    evidence(61, 67, "hermes/runtime/test_sdd_runtime_guard.py", "test_dag_and_test_id_failures_are_explicit"),
    evidence(68, 72, "hermes/runtime/test_sdd_runtime_guard.py", "test_fan_in_commits_once_and_retry_is_idempotent"),
    evidence(73, 74, "hermes/runtime/test_sdd_runtime_guard.py", "test_fingerprint_detects_out_of_scope_changes"),
    evidence(75, 77, "hermes/runtime/test_sdd_runtime_guard.py", "test_explicit_question_red_and_command_gates_replace_prompt_assumptions"),
    evidence(78, 79, "hermes/runtime/sdd_runtime_guard.py", "def append_job_event("),
    evidence(80, 80, "hermes/skills/sdd-wire-harness/references/plan-contract.md", "Le garde les exécute séquentiellement"),
    evidence(101, 105, "hermes/runtime/sdd_runtime_guard.py", "def migrate_state_v1("),
    evidence(106, 106, "hermes/scripts/test_sdd_s002_contract.py", "test_merged_runtime_epic_plan_and_wire_harness_baselines"),
    evidence(107, 107, "hermes/skills/sdd-epic-plan/scripts/test_epic_plan_guard.py", "test_approve_requires_exact_explicit_evidence"),
    evidence(108, 108, "hermes/skills/sdd-wire-harness/scripts/test_harness_guard.py", "test_validate_dry_run_returns_structured_plan_without_writes"),
    evidence(109, 109, "hermes/skills/sdd-wire-harness/scripts/test_harness_guard.py", "test_commit_is_transactional_and_same_plan_is_idempotent"),
    evidence(110, 122, "hermes/runtime/test_sdd_github_bridge.py", "class GitHubBridgeLifecycleTest"),
    evidence(123, 123, EXTERNAL_T008, "profile 0.5.0 publication gate", PENDING_EXTERNAL),
    evidence(243, 249, "hermes/skills/sdd-status/scripts/test_status_guard.py", "test_v2_task_local_view_exposes_all_proven_fields"),
    evidence(252, 252, "hermes/runtime/sdd_runtime_guard.py", "def global_lock("),
    evidence(253, 256, "hermes/runtime/test_sdd_github_bridge.py", "test_retry_after_kanban_failure_recovers_without_duplicate_objects"),
    evidence(276, 280, "hermes/scripts/test_sdd_runtime_profile_contract.py", "class SddRuntimeProfileContractTest"),
)


MERGED_BASELINES = (
    (
        "257ce11",
        "hermes/runtime/sdd_runtime_guard.py",
        "validate_state",
        "hermes/runtime/test_sdd_runtime_guard.py",
        "test_valid_v2_state_is_additive_for_legacy_consumers",
    ),
    (
        "d583bb5",
        "hermes/skills/sdd-epic-plan/scripts/epic_plan_guard.py",
        "decide_command",
        "hermes/skills/sdd-epic-plan/scripts/test_epic_plan_guard.py",
        "test_validate_and_promote_approved_epic",
    ),
    (
        "a5815b1",
        "hermes/skills/sdd-wire-harness/scripts/harness_guard.py",
        "commit_plan",
        "hermes/skills/sdd-wire-harness/scripts/test_harness_guard.py",
        "test_commit_is_transactional_and_same_plan_is_idempotent",
    ),
)


def read_repository_file(relative_path: str) -> str:
    return (REPOSITORY_ROOT / relative_path).read_text(encoding=UTF8)


def section_between(document: Path, start: str, end: str) -> str:
    text = document.read_text(encoding=UTF8)
    section = text.partition(start)[2].partition(end)[0]
    if not section:
        raise AssertionError(f"section not found between {start!r} and {end!r}")
    return section


def parse_ac_expression(value: str) -> set[str]:
    identifiers: set[str] = set()
    for match in AC_PATTERN.finditer(value):
        first = int(match.group(1))
        last = int(match.group(2) or match.group(1))
        identifiers.update(expand_ac_ranges((first, last)))
    return identifiers


def table_rows(
    document: Path,
    start: str | None = None,
    end: str | None = None,
) -> list[list[str]]:
    text = document.read_text(encoding=UTF8)
    if start is not None:
        text = text.partition(start)[2]
    if end is not None:
        text = text.partition(end)[0]

    rows = []
    for line in text.splitlines():
        if line.startswith(TABLE_DELIMITER) and line.endswith(TABLE_DELIMITER):
            cells = [
                cell.strip().strip("`")
                for cell in line.strip(TABLE_DELIMITER).split(TABLE_DELIMITER)
            ]
            if not all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
                rows.append(cells)
    return rows


def command_name(value: str) -> str | None:
    match = re.search(r"/sdd-[a-z-]+", value)
    return match.group(0) if match else None


def declared_python_symbols(relative_path: str) -> set[str]:
    tree = ast.parse(read_repository_file(relative_path), filename=relative_path)
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }


def task_scope(task_id: str, next_task_id: str) -> set[str]:
    task = section_between(TASKS, f"#### {task_id} :", f"#### {next_task_id} :")
    scope = task.partition("- **Files in scope :**")[2].partition("- **Dépendances :**")[0]
    return set(re.findall(r"^  - `([^`]+)`$", scope, flags=re.MULTILINE))


class SddS002ContractTest(unittest.TestCase):
    def test_s002_acceptance_manifest_matches_task_roadmap_and_evidence(self) -> None:
        """T-007-T1: task, roadmap and concrete evidence agree on 84 ACs."""
        task = section_between(TASKS, "#### T-007 :", "#### T-008 :")
        task_ac_block = task.partition("- **AC-IDs :**")[2].partition("- **Test-IDs :**")[0]
        task_ac_ids = parse_ac_expression(task_ac_block)

        roadmap_row = next(
            line for line in ROADMAP.read_text(encoding=UTF8).splitlines()
            if line.startswith("| S-002 |")
        )
        roadmap_ac_ids = parse_ac_expression(roadmap_row.split(TABLE_DELIMITER)[3])

        evidence_by_ac: dict[str, Evidence] = {}
        for evidence in EVIDENCE_GROUPS:
            for ac_id in evidence.ac_ids:
                self.assertNotIn(ac_id, evidence_by_ac, f"duplicate evidence for {ac_id}")
                evidence_by_ac[ac_id] = evidence
            if evidence.status == SATISFIED:
                self.assertIn(evidence.marker, read_repository_file(evidence.relative_path))
            else:
                self.assertEqual(EXTERNAL_T008, evidence.relative_path)
                self.assertEqual(("AC-123",), evidence.ac_ids)

        self.assertEqual(84, len(EXPECTED_S002_ACS))
        self.assertEqual(EXPECTED_S002_ACS, task_ac_ids)
        self.assertEqual(EXPECTED_S002_ACS, roadmap_ac_ids)
        self.assertEqual(EXPECTED_S002_ACS, set(evidence_by_ac))
        self.assertEqual(PENDING_EXTERNAL, evidence_by_ac["AC-123"].status)

    def test_merged_runtime_epic_plan_and_wire_harness_baselines(self) -> None:
        """T-007-T2: merged #61/#57/#59 files, symbols and tests are real."""
        planning_evidence = TASKS.read_text(encoding=UTF8) + ROADMAP.read_text(
            encoding=UTF8
        )
        for commit, source, symbol, tests, test_name in MERGED_BASELINES:
            self.assertIn(commit, planning_evidence)
            self.assertIn(symbol, declared_python_symbols(source))
            self.assertIn(test_name, declared_python_symbols(tests))

    def test_help_and_documentation_publish_converted_s002_commands(self) -> None:
        """T-007-T3 / AC-011, AC-012, AC-025: commands are public."""
        expected_commands = (EPIC_PLAN_COMMAND, WIRE_HARNESS_COMMAND)
        migration_statuses = {
            command_name(row[COMMAND_COLUMN]): row[STATUS_OR_COMMANDS_COLUMN]
            for row in table_rows(CODEX_MIGRATION)
            if len(row) == TABLE_COLUMN_COUNT and command_name(row[COMMAND_COLUMN])
        }

        for command in expected_commands:
            self.assertEqual(
                CONVERTED_STATUS,
                migration_statuses.get(command),
                f"{command} must be marked converted in docs/codex-migration.md",
            )

        help_rows = table_rows(
            HELP_SKILL,
            start="Les commandes actuellement disponibles sont :",
            end="Signaler séparément",
        )
        available_help_commands = {
            command_name(row[COMMAND_COLUMN])
            for row in help_rows
            if len(row) == TABLE_COLUMN_COUNT and row[STEP_COLUMN] != STEP_HEADER
        }
        readme_commands = {
            command_name(row[STATUS_OR_COMMANDS_COLUMN])
            for row in table_rows(HERMES_README)
            if len(row) == TABLE_COLUMN_COUNT and row[STEP_COLUMN] != STEP_HEADER
        }
        public_commands = available_help_commands | readme_commands | set(migration_statuses)

        self.assertTrue(set(expected_commands) <= available_help_commands)
        self.assertTrue(set(expected_commands) <= readme_commands)
        self.assertNotIn(ROLES_COMMAND, public_commands)

    def test_bridge_status_contracts_are_deterministic_and_scopes_are_disjoint(self) -> None:
        """T-007-T4: bridge/status expose proved behavior in disjoint scopes."""
        bridge_symbols = declared_python_symbols("hermes/runtime/sdd_github_bridge.py")
        bridge_tests = declared_python_symbols("hermes/runtime/test_sdd_github_bridge.py")
        status_symbols = declared_python_symbols("hermes/skills/sdd-status/scripts/status_guard.py")
        status_tests = declared_python_symbols("hermes/skills/sdd-status/scripts/test_status_guard.py")

        self.assertTrue({"start_job", "mark_ready", "poll_pull_request", "apply_review_correction"} <= bridge_symbols)
        self.assertIn("test_retry_after_kanban_failure_recovers_without_duplicate_objects", bridge_tests)
        self.assertEqual({"task_local_rows", "task_local_rows_from_file"}, status_symbols)
        self.assertIn("test_reading_task_local_rows_does_not_change_repository_fingerprint", status_tests)
        self.assertFalse(task_scope("T-004", "T-005") & task_scope("T-005", "T-006"))

    def test_capacity_contract_proves_two_writers_three_analyses_and_one_gate(self) -> None:
        """T-007-T5: source contracts state every VPS capacity limit."""
        rows = table_rows(
            ARTIFACT_CONTRACT,
            start="## Contrat de capacité Hermes",
            end="## Écrivains parallèles et fan-in",
        )
        limits = {
            row[0]: int(row[1])
            for row in rows
            if len(row) == TABLE_COLUMN_COUNT and row[0] != "Ressource"
        }
        self.assertEqual(
            {"max_writers": 2, "max_read_only_analyses": 3, "max_heavy_gates": 1},
            limits,
        )

        runtime_tree = ast.parse(read_repository_file("hermes/runtime/sdd_runtime_guard.py"))
        worker_limit = next(
            node.value.value
            for node in runtime_tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "MAX_WORKERS" for target in node.targets)
            and isinstance(node.value, ast.Constant)
        )
        self.assertEqual(limits["max_writers"], worker_limit)
        self.assertIn(
            "Le garde les exécute séquentiellement",
            read_repository_file("hermes/skills/sdd-wire-harness/references/plan-contract.md"),
        )

    def test_release_candidate_has_no_runtime_secret_auto_merge_scheduler_or_local_path(self) -> None:
        """T-007-T6: scan executable constructs, not explanatory prose/tests."""
        violations: list[str] = []
        for relative_path in PRODUCTION_PYTHON:
            tree = ast.parse(read_repository_file(relative_path), filename=relative_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = {alias.name.split(".")[0] for alias in node.names}
                    if modules & FORBIDDEN_SCHEDULER_MODULES:
                        violations.append(f"{relative_path}: scheduler import")
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.split(".")[0] in FORBIDDEN_SCHEDULER_MODULES:
                        violations.append(f"{relative_path}: scheduler import")
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name in FORBIDDEN_RUNTIME_NAMES:
                        violations.append(f"{relative_path}: forbidden function {node.name}")
                if isinstance(node, ast.Call):
                    call_name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
                    if call_name in FORBIDDEN_RUNTIME_NAMES:
                        violations.append(f"{relative_path}: forbidden call {call_name}")
                    literals = [
                        value.value
                        for value in ast.walk(node)
                        if isinstance(value, ast.Constant) and isinstance(value.value, str)
                    ]
                    command = " ".join(literals).lower()
                    if re.search(r"(?:^|\s)gh\s+pr\s+merge(?:\s|$)", command):
                        violations.append(f"{relative_path}: gh pr merge command")
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if CREDENTIAL_PATTERN.search(node.value):
                        violations.append(f"{relative_path}: embedded credential literal")

        for relative_path in (*PRODUCTION_PYTHON, *PUBLIC_RELEASE_DOCUMENTS):
            if LOCAL_PATH_PATTERN.search(read_repository_file(relative_path)):
                violations.append(f"{relative_path}: versioned machine-local path")

        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
