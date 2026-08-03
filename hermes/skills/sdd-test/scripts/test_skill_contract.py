#!/usr/bin/env python3
"""Static publication contract for ``/sdd-test``."""

from __future__ import annotations

import ast
from pathlib import Path
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]


class SkillContractTest(unittest.TestCase):
    def test_t017_t1_t2_publishes_exact_command(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("/sdd-test <feature-id> [--gap]", skill)

    def test_t017_t3_t7_declares_exact_writer_scope_and_order(self) -> None:
        contract = (SKILL_ROOT / "references" / "delegation-contract.md").read_text(
            encoding="utf-8"
        )
        for term in ("src/test/**", "06-test-plan.md", "src/main/**", "atomique", "traçabilité"):
            with self.subTest(term=term):
                self.assertIn(term, contract)

    def test_t017_t4_t5_plan_contract_requires_gaps_tags_and_names(self) -> None:
        contract = (SKILL_ROOT / "references" / "test-plan-contract.md").read_text(
            encoding="utf-8"
        )
        for term in ("Gap-NNN", "Won't fix", "@Tag(\"AC-NNN\")", "@DisplayName", "Testcontainers"):
            with self.subTest(term=term):
                self.assertIn(term, contract)

    def test_t017_t6_guard_composes_canonical_global_lock(self) -> None:
        tree = ast.parse(
            (SKILL_ROOT / "scripts" / "guard.py").read_text(encoding="utf-8")
        )
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "runtime"
        }
        self.assertIn("global_lock", calls)
        self.assertIn("validate_worker_changes", calls)


if __name__ == "__main__":
    unittest.main()
