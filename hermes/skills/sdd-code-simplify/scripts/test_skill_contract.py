#!/usr/bin/env python3
"""Static publication contract for ``/sdd-code-simplify``."""

from __future__ import annotations

import ast
from pathlib import Path
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
CLARITY_CATEGORIES = (
    "conditions",
    "boucles lisibles",
    "helpers",
    "options",
    "noms",
    "abstractions",
    "retours anticipés",
    "code mort",
    "littéraux répétés",
)
RUNTIME_PRIMITIVES = (
    "acquire_scope_lease",
    "repository_fingerprint",
    "validate_worker_changes",
    "release_scope_lease",
)


class SkillContractTest(unittest.TestCase):
    def test_t015_t1_t2_publishes_exact_command_and_refusals(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("/sdd-code-simplify <path> [--dry-run]", skill)
        for term in ("src/main/**", "src/test/**", "glob", "lien symbolique"):
            with self.subTest(term=term):
                self.assertIn(term, skill)

    def test_t015_t4_embeds_all_clarity_categories(self) -> None:
        checklist = (
            SKILL_ROOT / "references" / "clarity-checklist.md"
        ).read_text(encoding="utf-8")
        for category in CLARITY_CATEGORIES:
            with self.subTest(category=category):
                self.assertIn(category, checklist.lower())

    def test_t015_t5_t6_delegation_is_bounded_and_never_commits(self) -> None:
        contract = (
            SKILL_ROOT / "references" / "delegation-contract.md"
        ).read_text(encoding="utf-8")
        for term in (
            "un fichier à la fois",
            "04-tasks.md",
            ".tdd-state.json",
            "05-implementation-log.md",
            "aucun commit",
        ):
            with self.subTest(term=term):
                self.assertIn(term, contract)

    def test_t015_t5_guard_composes_canonical_runtime_primitives(self) -> None:
        guard_path = SKILL_ROOT / "scripts" / "code_simplify_guard.py"
        tree = ast.parse(guard_path.read_text(encoding="utf-8"))
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "runtime"
        }
        self.assertEqual([], [name for name in RUNTIME_PRIMITIVES if name not in calls])


if __name__ == "__main__":
    unittest.main()
