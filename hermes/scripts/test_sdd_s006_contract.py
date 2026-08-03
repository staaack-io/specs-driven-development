#!/usr/bin/env python3
"""Executable source audit for the 13 acceptance criteria in S-006."""

from __future__ import annotations

import ast
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
FEATURE = ROOT / ".specs" / "2026-07-31-hermes-parallel-sdd"
TASKS = FEATURE / "04-tasks.md"
STATE = FEATURE / ".tdd-state.json"
HELP = ROOT / "hermes/skills/sdd-help/SKILL.md"
REVIEW_GUARD = ROOT / "hermes/skills/sdd-review/scripts/review_guard.py"
SHIP_GUARD = ROOT / "hermes/skills/sdd-ship/scripts/ship_guard.py"


def expected_acceptance_criteria() -> set[str]:
    numbers = {17, 18, *range(148, 155), 235, *range(261, 264)}
    return {f"AC-{number:03d}" for number in numbers}


PRIMARY_PRODUCERS = {
    "AC-150": "T-021",
    "AC-151": "T-021",
    **{f"AC-{number:03d}": "T-022" for number in (152, 153, 235, 261, 262, 263)},
    "AC-148": "T-023",
    "AC-149": "T-023",
    "AC-017": "T-024",
    "AC-018": "T-024",
    "AC-154": "T-024",
}


class SddS006ContractTest(unittest.TestCase):
    def test_t023_t1_manifest_has_exactly_13_primary_producers(self) -> None:
        self.assertEqual(expected_acceptance_criteria(), set(PRIMARY_PRODUCERS))
        self.assertEqual(13, len(PRIMARY_PRODUCERS))
        self.assertEqual(
            {"T-021", "T-022", "T-023", "T-024"},
            set(PRIMARY_PRODUCERS.values()),
        )

    def test_t023_t2_both_source_skills_and_suites_exist(self) -> None:
        required = (
            REVIEW_GUARD,
            REVIEW_GUARD.with_name("test_review_guard.py"),
            REVIEW_GUARD.with_name("test_skill_contract.py"),
            SHIP_GUARD,
            SHIP_GUARD.with_name("test_ship_guard.py"),
            SHIP_GUARD.with_name("test_skill_contract.py"),
        )
        for path in required:
            with self.subTest(path=path):
                self.assertTrue(path.is_file(), str(path))

    def test_t023_t3_t4_dag_order_and_disjoint_scopes_are_explicit(self) -> None:
        tasks = TASKS.read_text(encoding="utf-8")
        state = STATE.read_text(encoding="utf-8")
        self.assertIn('"dependencies": ["T-021", "T-022"]', state)
        self.assertIn("T-022 n'est jamais fusionnée avant T-021", tasks)
        review_scope = set(
            re.findall(r'"(hermes/skills/sdd-review/[^\"]+)"', state)
        )
        ship_scope = set(
            re.findall(r'"(hermes/skills/sdd-ship/[^\"]+)"', state)
        )
        self.assertTrue(review_scope)
        self.assertTrue(ship_scope)
        self.assertTrue(review_scope.isdisjoint(ship_scope))

    def test_t023_t5_review_has_readers_and_ship_has_no_execution_capacity(self) -> None:
        review_source = REVIEW_GUARD.read_text(encoding="utf-8")
        self.assertIn("delegation_requests", review_source)
        self.assertIn("08-code-review.md", review_source)

        tree = ast.parse(SHIP_GUARD.read_text(encoding="utf-8"))
        forbidden_imports = {"subprocess", "socket", "urllib", "http", "requests", "paramiko"}
        imported = {
            alias.name.split(".", maxsplit=1)[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertTrue(forbidden_imports.isdisjoint(imported))

    def test_t023_t5_help_and_docs_publish_both_commands_as_installed(self) -> None:
        help_text = HELP.read_text(encoding="utf-8")
        installed, _, roadmap = help_text.partition("Signaler séparément")
        for invocation in (
            "`/sdd-review [<feature-id>] [--base <ref>]`",
            "`/sdd-ship [<feature-id>] [--base <ref>]`",
        ):
            self.assertIn(invocation, installed)
            self.assertNotIn(invocation.split(" ", 1)[0], roadmap)
        for document in (ROOT / "hermes/README.md", ROOT / "docs/codex-migration.md"):
            content = document.read_text(encoding="utf-8")
            self.assertIn("/sdd-review", content)
            self.assertIn("/sdd-ship", content)

    def test_t023_t6_source_has_no_merge_vps_secret_or_local_path(self) -> None:
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                REVIEW_GUARD,
                SHIP_GUARD,
                ROOT / "hermes/skills/sdd-review/SKILL.md",
                ROOT / "hermes/skills/sdd-ship/SKILL.md",
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
