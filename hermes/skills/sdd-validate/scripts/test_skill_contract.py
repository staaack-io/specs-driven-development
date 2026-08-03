#!/usr/bin/env python3
"""Static publication contract for ``/sdd-validate``."""

from __future__ import annotations

import ast
from pathlib import Path
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
REFERENCES = (
    "delegation-contract.md",
    "validation-contract.md",
    "role-spring-validator.md",
    "role-react-nextjs-validator.md",
)
TEMPLATES = ("validation-report.template.md", "traceability.template.md")


class SkillContractTests(unittest.TestCase):
    def test_t_018_t1_t2_publication_and_preconditions_are_explicit(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("/sdd-validate [<feature-id>]", skill)
        for term in ("harness", "tâches `done`", "résultats frais", "contournement"):
            with self.subTest(term=term):
                self.assertIn(term, skill)

    def test_t_018_t3_t5_specialized_roles_have_no_shared_report_handle(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for name in REFERENCES + TEMPLATES:
            directory = "templates" if name in TEMPLATES else "references"
            with self.subTest(name=name):
                self.assertIn(name, skill)
                self.assertTrue((SKILL_ROOT / directory / name).is_file())
        delegation = (SKILL_ROOT / "references" / "delegation-contract.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("aucun handle", delegation)
        self.assertIn("07-validation-report.md", delegation)
        self.assertIn("07a-traceability.md", delegation)

    def test_t_018_t4_t6_guard_composes_runtime_lock_and_atomic_writer(self) -> None:
        guard_source = (SKILL_ROOT / "scripts" / "validation_guard.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(guard_source)
        runtime_calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "runtime"
        }
        self.assertTrue({"global_lock", "atomic_replace"}.issubset(runtime_calls))
        self.assertNotIn("parents[4]", guard_source)
        self.assertIn('"hermes" / "runtime" / "sdd_runtime_guard.py"', guard_source)

    def test_t_018_t7_t8_contract_has_closed_verdicts_and_complete_catalog(self) -> None:
        contract = (SKILL_ROOT / "references" / "validation-contract.md").read_text(
            encoding="utf-8"
        )
        for term in ("approve", "request-changes", "PASS", "FAIL"):
            with self.subTest(term=term):
                self.assertIn(term, contract)
        for number in range(210, 218):
            with self.subTest(ac=number):
                self.assertIn(f"AC-{number}", contract)


if __name__ == "__main__":
    unittest.main()
