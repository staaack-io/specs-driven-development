#!/usr/bin/env python3
"""Executable source audit for the 11 acceptance criteria in S-007."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
FEATURE = ROOT / ".specs" / "2026-07-31-hermes-parallel-sdd"
STATE = FEATURE / ".tdd-state.json"
HELP = ROOT / "hermes/skills/sdd-help/SKILL.md"
PARALLEL = ROOT / "hermes/e2e/parallel_scenario.py"
RECOVERY = ROOT / "hermes/e2e/recovery_scenario.py"
RUNNER = ROOT / "hermes/e2e/run_sdd_e2e.py"
PUBLICATION_DOCS = (
    ROOT / "hermes/README.md",
    ROOT / "docs/artifact-contract.md",
    ROOT / "docs/codex-migration.md",
)
SCENARIO_PATHS = (PARALLEL, RECOVERY, RUNNER)

COMMANDS = (
    "help",
    "status",
    "onboard",
    "wire-harness",
    "spec",
    "spec-review",
    "epic-plan",
    "plan",
    "build",
    "code-simplify",
    "test",
    "validate",
    "review",
    "ship",
)

PRIMARY_PRODUCERS = {
    **{f"AC-{number:03d}": "T-025" for number in (156, 219, 227)},
    **{f"AC-{number:03d}": "T-026" for number in (157, 158, 228)},
    **{f"AC-{number:03d}": "T-027" for number in (155, 218, 226)},
    "AC-225": "T-028",
    "AC-159": "T-029",
}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }


class SddS007ContractTest(unittest.TestCase):
    def test_t028_t1_manifest_has_exactly_11_primary_producers(self) -> None:
        expected = {155, 156, 157, 158, 159, 218, 219, 225, 226, 227, 228}
        self.assertEqual(
            {f"AC-{number:03d}" for number in expected},
            set(PRIMARY_PRODUCERS),
        )
        self.assertEqual(11, len(PRIMARY_PRODUCERS))
        self.assertEqual(
            {"T-025", "T-026", "T-027", "T-028", "T-029"},
            set(PRIMARY_PRODUCERS.values()),
        )

    def test_t028_t2_every_command_from_onboard_to_ship_is_installed(self) -> None:
        help_text = HELP.read_text(encoding="utf-8")
        installed, _, roadmap = help_text.partition("Signaler séparément")
        for command in COMMANDS:
            skill = ROOT / "hermes/skills" / f"sdd-{command}" / "SKILL.md"
            with self.subTest(command=command):
                self.assertTrue(skill.is_file(), str(skill))
                self.assertIn(f"`/sdd-{command}", installed)
                self.assertNotIn(f"`/sdd-{command}", roadmap)

    def test_t028_t3_dag_keeps_parallel_pair_then_sequential_fan_in(self) -> None:
        tasks = json.loads(STATE.read_text(encoding="utf-8"))["tasks"]
        self.assertEqual(["T-024"], tasks["T-025"]["dependencies"])
        self.assertEqual(["T-024"], tasks["T-026"]["dependencies"])
        self.assertEqual(["T-025", "T-026"], tasks["T-027"]["dependencies"])
        self.assertEqual(["T-027"], tasks["T-028"]["dependencies"])
        self.assertEqual(["T-024", "T-028"], tasks["T-029"]["dependencies"])

    def test_t028_t4_all_parallel_and_recovery_proofs_are_executable(self) -> None:
        tests = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                PARALLEL.with_name("test_parallel_scenario.py"),
                RECOVERY.with_name("test_recovery_scenario.py"),
            )
        )
        proof_markers = {
            "overlap": "overlap",
            "capacity": "capacity",
            "conflict": "conflict",
            "dependency": "dependent",
            "failure": "failure",
            "fan-in": "fan_in",
        }
        for proof, marker in proof_markers.items():
            with self.subTest(proof=proof):
                self.assertIn(marker, tests)
        self.assertIn("run_parallel_scenario", PARALLEL.read_text(encoding="utf-8"))
        self.assertIn("run_recovery_scenario", RECOVERY.read_text(encoding="utf-8"))

    def test_t028_t5_runner_publishes_each_task_lifecycle_envelope(self) -> None:
        runner_source = RUNNER.read_text(encoding="utf-8")
        self.assertIn('"task_envelopes"', runner_source)
        for field in ("issue", "card", "branch", "worktree", "session", "pr"):
            with self.subTest(field=field):
                self.assertIn(f'"{field}"', runner_source)

    def test_t028_t6_publication_is_local_redacted_and_non_deploying(self) -> None:
        forbidden_imports = {"paramiko", "requests", "socket", "urllib"}
        for path in SCENARIO_PATHS:
            with self.subTest(path=path):
                self.assertTrue(forbidden_imports.isdisjoint(imported_modules(path)))

        runner_source = RUNNER.read_text(encoding="utf-8")
        for forbidden in ("/Users/", "ghp_", "github_pat_", "ssh "):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, runner_source)

        for document in PUBLICATION_DOCS:
            content = document.read_text(encoding="utf-8")
            with self.subTest(document=document):
                self.assertIn("S-007", content)
                self.assertIn("onboard→ship", content)
                self.assertIn("sans reviewer humain", content)
                self.assertIn("sans fusion ni déploiement", content)


if __name__ == "__main__":
    unittest.main()
