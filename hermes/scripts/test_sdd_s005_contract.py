#!/usr/bin/env python3
"""Executable source audit for the 32 acceptance criteria in S-005."""

from __future__ import annotations

import ast
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
FEATURE = ROOT / ".specs" / "2026-07-31-hermes-parallel-sdd"
TASKS = FEATURE / "04-tasks.md"
HELP = ROOT / "hermes/skills/sdd-help/SKILL.md"
TEST_GUARD = ROOT / "hermes/skills/sdd-test/scripts/guard.py"
VALIDATE_GUARD = ROOT / "hermes/skills/sdd-validate/scripts/validation_guard.py"


def expected_acceptance_criteria() -> set[str]:
    numbers = {15, 16, *range(140, 148), *range(196, 218)}
    return {f"AC-{number:03d}" for number in numbers}


PRIMARY_PRODUCERS = {
    **{f"AC-{number:03d}": "T-017" for number in (142, *range(196, 210))},
    **{f"AC-{number:03d}": "T-018" for number in (*range(143, 147), *range(210, 218))},
    "AC-140": "T-019",
    "AC-141": "T-019",
    "AC-015": "T-020",
    "AC-016": "T-020",
    "AC-147": "T-020",
}


class SddS005ContractTest(unittest.TestCase):
    def test_t019_t1_manifest_has_exactly_32_primary_producers(self) -> None:
        self.assertEqual(expected_acceptance_criteria(), set(PRIMARY_PRODUCERS))
        self.assertEqual(32, len(PRIMARY_PRODUCERS))
        self.assertEqual(
            {"T-017", "T-018", "T-019", "T-020"},
            set(PRIMARY_PRODUCERS.values()),
        )

    def test_t019_t2_both_source_skills_and_executable_catalogs_exist(self) -> None:
        self.assertTrue(TEST_GUARD.is_file())
        self.assertTrue(VALIDATE_GUARD.is_file())
        test_source = TEST_GUARD.read_text(encoding="utf-8")
        validate_source = VALIDATE_GUARD.read_text(encoding="utf-8")
        for number in range(196, 210):
            self.assertIn(f'"AC-{number}"', test_source)
        for number in range(210, 218):
            self.assertIn(f'"AC-{number}"', validate_source)

    def test_t019_t3_t4_dag_merge_order_and_scopes_are_explicit(self) -> None:
        tasks = TASKS.read_text(encoding="utf-8")
        state = (FEATURE / ".tdd-state.json").read_text(encoding="utf-8")
        self.assertIn('"T-019": {', state)
        self.assertIn('"dependencies": ["T-017", "T-018"]', state)
        self.assertIn("T-018 n'est jamais fusionnée avant T-017", tasks)
        test_scope = set(re.findall(r'"(hermes/skills/sdd-test/[^\"]+)"', state))
        validate_scope = set(
            re.findall(r'"(hermes/skills/sdd-validate/[^\"]+)"', state)
        )
        self.assertTrue(test_scope)
        self.assertTrue(validate_scope)
        self.assertTrue(test_scope.isdisjoint(validate_scope))

    def test_t019_t5_both_commands_compose_one_canonical_gate_lock(self) -> None:
        for path in (TEST_GUARD, VALIDATE_GUARD):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            locks = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "global_lock"
            ]
            self.assertTrue(locks, str(path))
        runtime_files = list((ROOT / "hermes/runtime").glob("*orchestrator*.py"))
        self.assertEqual(2, len(runtime_files), "no S-005 scheduler may be added")

    def test_t019_t6_help_and_docs_publish_both_commands_as_installed(self) -> None:
        help_text = HELP.read_text(encoding="utf-8")
        installed, _, roadmap = help_text.partition("Signaler séparément")
        for invocation in (
            "`/sdd-test <feature-id> [--gap]`",
            "`/sdd-validate [<feature-id>]`",
        ):
            self.assertIn(invocation, installed)
            self.assertNotIn(invocation.split(" ", 1)[0], roadmap)
        readme = (ROOT / "hermes/README.md").read_text(encoding="utf-8")
        migration = (ROOT / "docs/codex-migration.md").read_text(encoding="utf-8")
        for command in ("/sdd-test", "/sdd-validate"):
            self.assertIn(command, readme)
            self.assertIn(command, migration)

    def test_t019_t7_source_has_no_merge_vps_secret_or_absolute_path(self) -> None:
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                TEST_GUARD,
                VALIDATE_GUARD,
                ROOT / "hermes/skills/sdd-test/SKILL.md",
                ROOT / "hermes/skills/sdd-validate/SKILL.md",
            )
        )
        for forbidden in (
            "git merge",
            "git reset --hard",
            "git push --force",
            "hermes profile update",
            "ssh ",
            "/Users/",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
