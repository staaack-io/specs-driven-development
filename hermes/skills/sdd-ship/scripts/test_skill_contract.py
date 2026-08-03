#!/usr/bin/env python3
"""Static publication contract for ``/sdd-ship``."""

from __future__ import annotations

import ast
from pathlib import Path
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "references/delegation-contract.md",
    "references/shipping-contract.md",
    "templates/ship-plan.template.md",
    "scripts/ship_guard.py",
)


class SkillContractTests(unittest.TestCase):
    def test_t_022_t1_t2_publication_and_arguments_are_explicit(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("/sdd-ship [<feature-id>] [--base <ref>]", skill)
        for path in REQUIRED_FILES:
            with self.subTest(path=path):
                self.assertIn(Path(path).name, skill)
                self.assertTrue((SKILL_ROOT / path).is_file())

    def test_t_022_t3_to_t7_contract_covers_complete_plan(self) -> None:
        contract = (SKILL_ROOT / "references" / "shipping-contract.md").read_text(
            encoding="utf-8"
        )
        for term in (
            "validation",
            "review",
            "questions",
            "baseline",
            "scope",
            "rollback",
            "observability",
            "feature flag",
            "release notes",
            "AC-152",
            "AC-153",
            "AC-235",
            "AC-261",
            "AC-262",
            "AC-263",
        ):
            with self.subTest(term=term):
                self.assertIn(term, contract)

    def test_t_022_t8_skill_has_no_execution_or_remote_capability(self) -> None:
        guard_path = SKILL_ROOT / "scripts" / "ship_guard.py"
        tree = ast.parse(guard_path.read_text(encoding="utf-8"))
        forbidden = {"subprocess", "socket", "urllib", "http", "requests", "paramiko"}
        imports = {
            alias.name.split(".", maxsplit=1)[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertTrue(forbidden.isdisjoint(imports))
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "aucune primitive shell",
            "aucun accès réseau",
            "aucun accès VPS",
            "commande affichée uniquement",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill)


if __name__ == "__main__":
    unittest.main()
