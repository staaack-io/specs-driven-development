#!/usr/bin/env python3
"""Static publication contract for ``/sdd-review``."""

from __future__ import annotations

import ast
from pathlib import Path
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
ENCODING = "utf-8"
SKILL_FILE = "SKILL.md"
GUARD_FILE = "review_guard.py"
REFERENCES_DIRECTORY = "references"
DELEGATION_CONTRACT = "delegation-contract.md"
REVIEW_CONTRACT = "review-contract.md"
REPORT_NAME = "08-code-review.md"
REFERENCES = (
    DELEGATION_CONTRACT,
    REVIEW_CONTRACT,
    "role-spring-code-reviewer.md",
    "role-react-nextjs-code-reviewer.md",
)
TEMPLATE = "code-review.template.md"


class SkillContractTests(unittest.TestCase):
    def test_t_021_t1_t2_public_command_and_arguments_are_documented(self) -> None:
        """T-021-T1/T2 / AC-150: publication exposes inert structured arguments."""

        skill = (SKILL_ROOT / SKILL_FILE).read_text(encoding=ENCODING)
        self.assertIn("/sdd-review [<feature-id>] [--base <ref>]", skill)
        self.assertIn(GUARD_FILE, skill)

    def test_t_021_t3_t4_roles_are_specialized_and_read_only(self) -> None:
        """T-021-T3/T4 / AC-150: both role contracts deny the shared writer."""

        skill = (SKILL_ROOT / SKILL_FILE).read_text(encoding=ENCODING)
        for name in REFERENCES:
            with self.subTest(name=name):
                self.assertIn(name, skill)
                self.assertTrue((SKILL_ROOT / REFERENCES_DIRECTORY / name).is_file())
        delegation = (SKILL_ROOT / REFERENCES_DIRECTORY / DELEGATION_CONTRACT).read_text(
            encoding=ENCODING
        )
        self.assertIn("aucun handle", delegation)
        self.assertIn(REPORT_NAME, delegation)

    def test_t_021_t5_t6_fan_in_and_single_atomic_writer_are_structural(self) -> None:
        """T-021-T5/T6 / AC-151: the guard composes canonical atomic publication."""

        guard_source = (SKILL_ROOT / "scripts" / GUARD_FILE).read_text(
            encoding=ENCODING
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
        self.assertIn(REPORT_NAME, guard_source)
        self.assertTrue((SKILL_ROOT / "templates" / TEMPLATE).is_file())

    def test_t_021_t7_t8_contract_is_informative_and_redacted(self) -> None:
        """T-021-T7/T8 / AC-151: verdict and redaction rules are explicit."""

        contract = (SKILL_ROOT / REFERENCES_DIRECTORY / REVIEW_CONTRACT).read_text(
            encoding=ENCODING
        )
        for term in (
            "approve",
            "request-changes",
            "informatif",
            "non bloquant",
            "secrets",
            "chemins absolus",
            "données métier",
        ):
            with self.subTest(term=term):
                self.assertIn(term, contract)


if __name__ == "__main__":
    unittest.main()
