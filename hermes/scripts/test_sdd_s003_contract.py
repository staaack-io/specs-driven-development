#!/usr/bin/env python3
"""Deterministic source contract for the complete S-003 build slice."""

from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
import importlib.util
from pathlib import Path
import re
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FEATURE_ROOT = REPOSITORY_ROOT / ".specs/2026-07-31-hermes-parallel-sdd"
TASKS = FEATURE_ROOT / "04-tasks.md"
ROADMAP = FEATURE_ROOT / "03a-epic-roadmap.md"
HELP_SKILL = REPOSITORY_ROOT / "hermes/skills/sdd-help/SKILL.md"
HERMES_README = REPOSITORY_ROOT / "hermes/README.md"
ARTIFACT_CONTRACT = REPOSITORY_ROOT / "docs/artifact-contract.md"
CODEX_MIGRATION = REPOSITORY_ROOT / "docs/codex-migration.md"
UTF8 = "utf-8"
AC_PATTERN = re.compile(r"AC-(\d{3})(?:\s*[–-]\s*AC-(\d{3}))?")
TEST_ID_PATTERN = re.compile(r"T-\d{3}-T\d+")
LOCAL_PATH_PATTERN = re.compile(r"(?:/Users/|/home/[^/<\s]+/|/private/tmp/|[A-Z]:\\Users\\)")
CREDENTIAL_PATTERN = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
    r"AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
)
FORBIDDEN_MODULES = {"apscheduler", "sched", "schedule"}
FORBIDDEN_SYMBOLS = {
    "auto_merge",
    "enable_auto_merge",
    "force_push",
    "merge_pull_request",
    "reset_hard",
    "schedule_job",
}
PRODUCTION_PYTHON = (
    "hermes/runtime/sdd_runtime_guard.py",
    "hermes/runtime/sdd_github_bridge.py",
    "hermes/runtime/sdd_build_orchestrator.py",
    "hermes/runtime/sdd_job_execution.py",
    "hermes/runtime/sdd_wave_synthesizer.py",
    "hermes/skills/sdd-build/scripts/build_guard.py",
    "hermes/skills/sdd-status/scripts/status_guard.py",
)
PUBLIC_DOCUMENTS = (
    "hermes/runtime/README.md",
    "hermes/skills/sdd-help/SKILL.md",
    "hermes/README.md",
    "docs/artifact-contract.md",
    "docs/codex-migration.md",
)


@dataclass(frozen=True)
class Evidence:
    first: int
    last: int
    producer: str
    relative_path: str
    marker: str

    @property
    def ac_ids(self) -> tuple[str, ...]:
        return expand_ac_range(self.first, self.last)


def expand_ac_range(first: int, last: int) -> tuple[str, ...]:
    return tuple(f"AC-{number:03d}" for number in range(first, last + 1))


EXPECTED_S003_ACS = set(
    expand_ac_range(13, 13)
    + expand_ac_range(19, 24)
    + expand_ac_range(27, 47)
    + expand_ac_range(124, 138)
    + expand_ac_range(231, 231)
    + expand_ac_range(233, 234)
    + expand_ac_range(236, 236)
    + expand_ac_range(257, 260)
)


EVIDENCE = (
    Evidence(
        13,
        13,
        "T-014",
        "hermes/scripts/test_sdd_s003_contract.py",
        "test_s003_manifest_has_exactly_51_unique_primary_producers",
    ),
    Evidence(
        19,
        19,
        "T-009",
        "hermes/skills/sdd-build/scripts/test_build_guard.py",
        "test_t009_t1_public_arguments_are_validated_before_mutation",
    ),
    Evidence(
        20,
        23,
        "T-010",
        "hermes/runtime/test_sdd_build_orchestrator.py",
        "test_t010_t2_worker_bounds_default_and_cap_are_two",
    ),
    Evidence(
        24,
        24,
        "T-013",
        "hermes/scripts/test_sdd_s003_contract.py",
        "test_t010_card_is_rendered_by_status_without_mutation_or_inference",
    ),
    Evidence(
        27,
        29,
        "T-010",
        "hermes/runtime/test_sdd_build_orchestrator.py",
        "test_t010_t3_admits_only_ready_tasks_with_merged_dependencies",
    ),
    Evidence(
        30,
        30,
        "T-011",
        "hermes/runtime/test_sdd_job_execution.py",
        "test_t011_t3_session_child_issue_and_draft_pr_are_unique",
    ),
    Evidence(
        31,
        31,
        "T-010",
        "hermes/runtime/test_sdd_build_orchestrator.py",
        "test_t010_t5_cards_carry_complete_durable_metadata",
    ),
    Evidence(
        32,
        36,
        "T-011",
        "hermes/runtime/test_sdd_job_execution.py",
        "test_t011_t4_failure_logs_exclude_sensitive_and_business_content",
    ),
    Evidence(
        37,
        44,
        "T-009",
        "hermes/skills/sdd-build/scripts/test_build_guard.py",
        "test_t009_t6_one_job_enforces_the_complete_phase_order",
    ),
    Evidence(
        45,
        47,
        "T-012",
        "hermes/runtime/test_sdd_wave_synthesizer.py",
        "test_t012_t4_all_cards_done_and_journals_verified_before_fan_in",
    ),
    Evidence(
        124,
        127,
        "T-009",
        "hermes/skills/sdd-build/scripts/test_skill_contract.py",
        "test_t009_t2_all_stack_specific_role_contracts_are_published",
    ),
    Evidence(
        128,
        128,
        "T-010",
        "hermes/runtime/test_sdd_build_orchestrator.py",
        "test_t010_t7_refuses_until_t009_is_observed_merged",
    ),
    Evidence(
        129,
        133,
        "T-010",
        "hermes/runtime/test_sdd_build_orchestrator.py",
        "test_t010_t5_cards_carry_complete_durable_metadata",
    ),
    Evidence(
        134,
        137,
        "T-012",
        "hermes/runtime/test_sdd_wave_synthesizer.py",
        "test_t012_t6_fan_in_pr_is_idempotent_and_never_merged",
    ),
    Evidence(
        138,
        138,
        "T-014",
        "hermes/scripts/test_sdd_s003_contract.py",
        "test_s003_manifest_has_exactly_51_unique_primary_producers",
    ),
    Evidence(
        231,
        231,
        "T-012",
        "hermes/runtime/test_sdd_wave_synthesizer.py",
        "test_t012_t3_only_explicitly_approved_observed_merge_becomes_done",
    ),
    Evidence(
        233,
        234,
        "T-011",
        "hermes/runtime/test_sdd_job_execution.py",
        "test_t011_t7_no_adapter_exposes_destructive_git_or_merge",
    ),
    Evidence(
        236,
        236,
        "T-010",
        "hermes/runtime/test_sdd_build_orchestrator.py",
        "test_t010_t5_cards_carry_complete_durable_metadata",
    ),
    Evidence(
        257,
        259,
        "T-009",
        "hermes/skills/sdd-build/scripts/test_build_guard.py",
        "test_t009_t7_each_event_has_structured_sanitized_evidence",
    ),
    Evidence(
        260,
        260,
        "T-010",
        "hermes/runtime/test_sdd_build_orchestrator.py",
        "test_t010_t5_cards_carry_complete_durable_metadata",
    ),
)


def read(relative_path: str) -> str:
    return (REPOSITORY_ROOT / relative_path).read_text(encoding=UTF8)


def section(start: str, end: str) -> str:
    text = TASKS.read_text(encoding=UTF8)
    value = text.partition(start)[2].partition(end)[0]
    if not value:
        raise AssertionError(f"missing section {start!r}")
    return value


def parse_ac_ids(value: str) -> set[str]:
    identifiers: set[str] = set()
    for match in AC_PATTERN.finditer(value):
        first = int(match.group(1))
        last = int(match.group(2) or match.group(1))
        identifiers.update(expand_ac_range(first, last))
    return identifiers


def task_block(task_id: str, next_task_id: str) -> str:
    return section(f"### {task_id} :", f"### {next_task_id} :")


def task_dependencies(task_id: str, next_task_id: str) -> set[str]:
    block = task_block(task_id, next_task_id)
    value = block.partition("- **Dépendances :**")[2].splitlines()[0]
    return set(re.findall(r"T-\d{3}", value))


def task_scope(task_id: str, next_task_id: str) -> set[str]:
    block = task_block(task_id, next_task_id)
    scope = block.partition("- **Files in scope :**")[2].partition("- **Dépendances :**")[0]
    return set(re.findall(r"^  - `([^`]+)`$", scope, flags=re.MULTILINE))


def load_module(relative_path: str, name: str):
    path = REPOSITORY_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class SddS003ContractTest(unittest.TestCase):
    def test_s003_manifest_has_exactly_51_unique_primary_producers(self) -> None:
        """T-013-T1/T2: roadmap, task matrix and executable evidence agree."""

        roadmap_row = next(
            line for line in ROADMAP.read_text(encoding=UTF8).splitlines()
            if line.startswith("| S-003 |")
        )
        matrix = section(
            "### S-003 Primary AC Coverage Matrix",
            "### S-003 Dependency and Capacity Validation",
        )
        matrix_producers: dict[str, str] = {}
        for line in matrix.splitlines():
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) != 3 or not cells[0].startswith("AC-"):
                continue
            self.assertTrue(TEST_ID_PATTERN.search(cells[2]), line)
            for ac_id in parse_ac_ids(cells[0]):
                self.assertNotIn(ac_id, matrix_producers, f"duplicate producer: {ac_id}")
                matrix_producers[ac_id] = cells[1]

        evidence_by_ac: dict[str, Evidence] = {}
        for item in EVIDENCE:
            self.assertIn(item.marker, read(item.relative_path))
            for ac_id in item.ac_ids:
                self.assertNotIn(ac_id, evidence_by_ac, f"duplicate evidence: {ac_id}")
                evidence_by_ac[ac_id] = item
                self.assertEqual(item.producer, matrix_producers.get(ac_id))

        self.assertEqual(51, len(EXPECTED_S003_ACS))
        self.assertEqual(EXPECTED_S003_ACS, parse_ac_ids(roadmap_row.split("|")[3]))
        self.assertEqual(EXPECTED_S003_ACS, set(matrix_producers))
        self.assertEqual(EXPECTED_S003_ACS, set(evidence_by_ac))

    def test_s003_dag_is_acyclic_ordered_and_scopes_are_disjoint(self) -> None:
        """T-013-T3: production precedes the unique T-012 fan-in."""

        successors = {"T-009": "T-010", "T-010": "T-011", "T-011": "T-012", "T-012": "T-013"}
        dependencies = {
            task_id: task_dependencies(task_id, next_task)
            for task_id, next_task in successors.items()
        }
        self.assertEqual({"T-009"}, dependencies["T-010"])
        self.assertEqual({"T-010"}, dependencies["T-011"])
        self.assertEqual({"T-010", "T-011"}, dependencies["T-012"])

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            self.assertNotIn(task_id, visiting, f"cycle through {task_id}")
            if task_id in visited:
                return
            visiting.add(task_id)
            for dependency in dependencies.get(task_id, set()):
                visit(dependency)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in successors:
            visit(task_id)

        scopes = {
            task_id: task_scope(task_id, next_task)
            for task_id, next_task in successors.items()
        }
        # A dependency serializes an intentional overlap. The independent
        # envelopes and the fan-in remain disjoint from their predecessors.
        for left, right in (("T-010", "T-011"), ("T-011", "T-012")):
            self.assertFalse(scopes[left] & scopes[right], f"overlap: {left}/{right}")
        self.assertIn("sdd_wave_synthesizer.py", " ".join(scopes["T-012"]))

    def test_t010_card_is_rendered_by_status_without_mutation_or_inference(self) -> None:
        """T-013-T4/AC-024: status exposes only persisted task-local evidence."""

        orchestrator = load_module("hermes/runtime/sdd_build_orchestrator.py", "_s003_orchestrator")
        status = load_module("hermes/skills/sdd-status/scripts/status_guard.py", "_s003_status")
        task = {"branch": "sdd/feature/T-010-admission"}
        metadata = orchestrator._card_metadata(
            feature_id="feature",
            task_id="T-010",
            task=task,
            state={"project": "project", "board": "board"},
            parent_card_id="parent",
        )
        state = {
            "tasks": {
                "T-010": {
                    "branch": metadata["branch"],
                    "issue": 80,
                    "pr": 81,
                    "checks": "green",
                    "review": "—",
                    "blocking": [],
                    "next_action": "awaiting_go",
                }
            }
        }
        before = copy.deepcopy(state)
        rows = status.task_local_rows(state)
        self.assertEqual(before, state)
        self.assertEqual("T-010", rows[0]["task_id"])
        self.assertEqual(metadata["branch"], rows[0]["branch"])
        self.assertEqual("awaiting_go", rows[0]["next_action"])
        self.assertEqual([], rows[0]["blocking"])

        missing = status.task_local_rows({"tasks": {"T-010": {}}})[0]
        self.assertTrue(all(value == "—" for key, value in missing.items() if key != "task_id"))

    def test_capacity_contract_is_two_writers_three_analyses_one_gate(self) -> None:
        """T-013-T5: documentation and runtime publish the VPS limits."""

        contract = ARTIFACT_CONTRACT.read_text(encoding=UTF8)
        for name, maximum in (
            ("max_writers", 2),
            ("max_read_only_analyses", 3),
            ("max_heavy_gates", 1),
        ):
            self.assertRegex(contract, rf"\| `{name}` \| {maximum} \|")

        tree = ast.parse(read("hermes/runtime/sdd_build_orchestrator.py"))
        constants = {
            target.id: node.value.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance((target := node.targets[0]), ast.Name)
            and isinstance(node.value, ast.Constant)
        }
        self.assertEqual(2, constants["MAX_WORKERS"])
        self.assertIn("trois analyses en lecture seule", read("hermes/runtime/README.md"))
        self.assertIn("une gate lourde", read("hermes/runtime/README.md"))

    def test_source_suites_and_public_build_documentation_are_complete(self) -> None:
        """T-013-T1/T6: every source suite and public build marker exists."""

        suites = (
            "hermes/skills/sdd-onboard/scripts/test_skill_contract.py",
            "hermes/skills/sdd-build/scripts/test_build_guard.py",
            "hermes/skills/sdd-build/scripts/test_skill_contract.py",
            "hermes/runtime/test_sdd_build_orchestrator.py",
            "hermes/runtime/test_sdd_job_execution.py",
            "hermes/runtime/test_sdd_wave_synthesizer.py",
            "hermes/runtime/test_sdd_runtime_guard.py",
            "hermes/runtime/test_sdd_github_bridge.py",
            "hermes/skills/sdd-status/scripts/test_status_guard.py",
        )
        for suite in suites:
            tree = ast.parse(read(suite), filename=suite)
            has_test = any(
                isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
                for node in ast.walk(tree)
            )
            self.assertTrue(has_test, suite)

        help_text = HELP_SKILL.read_text(encoding=UTF8)
        installed, _, planned = help_text.partition("Signaler séparément")
        self.assertIn("`/sdd-build <feature-id> <T-NNN>`", installed)
        self.assertNotIn("`/sdd-build", planned)
        self.assertIn("`/sdd-code-simplify <path> [--dry-run]`", installed)
        self.assertNotIn("`/sdd-code-simplify", planned)
        self.assertRegex(
            CODEX_MIGRATION.read_text(encoding=UTF8),
            r"\| `\$build` \| `/sdd-build` \| converti \|",
        )
        for relative_path in PUBLIC_DOCUMENTS:
            self.assertIn("/sdd-build", read(relative_path), relative_path)

    def test_release_source_has_no_destructive_git_secret_path_or_scheduler(self) -> None:
        """T-013-T7: executable source contains no forbidden automation."""

        violations: list[str] = []
        for relative_path in PRODUCTION_PYTHON:
            tree = ast.parse(read(relative_path), filename=relative_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = {alias.name.split(".")[0] for alias in node.names}
                    if modules & FORBIDDEN_MODULES:
                        violations.append(f"{relative_path}: scheduler import")
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.split(".")[0] in FORBIDDEN_MODULES:
                        violations.append(f"{relative_path}: scheduler import")
                is_function = isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                if is_function and node.name in FORBIDDEN_SYMBOLS:
                    violations.append(f"{relative_path}: forbidden function {node.name}")
                if isinstance(node, ast.Call):
                    name = (
                        node.func.attr
                        if isinstance(node.func, ast.Attribute)
                        else getattr(node.func, "id", "")
                    )
                    if name in FORBIDDEN_SYMBOLS:
                        violations.append(f"{relative_path}: forbidden call {name}")
                    literals = [
                        value.value
                        for value in ast.walk(node)
                        if isinstance(value, ast.Constant) and isinstance(value.value, str)
                    ]
                    command = " ".join(literals).lower()
                    destructive = re.search(
                        r"(?:^|\s)(?:git\s+push\s+--force(?:-with-lease)?|"
                        r"git\s+reset\s+--hard|gh\s+pr\s+merge)(?:\s|$)",
                        command,
                    )
                    if destructive:
                        violations.append(f"{relative_path}: destructive command")
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if CREDENTIAL_PATTERN.search(node.value):
                        violations.append(f"{relative_path}: credential literal")

        for relative_path in (*PRODUCTION_PYTHON, *PUBLIC_DOCUMENTS):
            if LOCAL_PATH_PATTERN.search(read(relative_path)):
                violations.append(f"{relative_path}: machine-local path")
        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
