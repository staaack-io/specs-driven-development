#!/usr/bin/env python3
"""Static contract checks for the published ``/sdd-build`` skill."""

from __future__ import annotations

import ast
from pathlib import Path
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SHARED_ARTIFACTS = (
    "04-tasks.md",
    ".tdd-state.json",
    "05-implementation-log.md",
)
ROLE_REFERENCES = (
    "role-spring-test-engineer.md",
    "role-spring-implementer.md",
    "role-react-nextjs-test-engineer.md",
    "role-react-nextjs-implementer.md",
)
RUNTIME_PRIMITIVES = (
    "validate_state",
    "acquire_scope_lease",
    "validate_red_gate",
    "repository_fingerprint",
    "validate_worker_changes",
    "append_job_event",
    "release_scope_lease",
)


class SkillContractTest(unittest.TestCase):
    def test_t009_t1_skill_publishes_the_exact_single_task_invocation(self) -> None:
        """T-009-T1: the skill exposes two required structured arguments."""

        skill_path = SKILL_ROOT / "SKILL.md"
        self.assertTrue(skill_path.is_file(), "sdd-build/SKILL.md must be published")
        skill = skill_path.read_text(encoding="utf-8")
        self.assertIn("/sdd-build <feature-id> <T-NNN>", skill)
        self.assertIn("scripts/build_guard.py", skill)

    def test_t009_t2_all_stack_specific_role_contracts_are_published(self) -> None:
        """T-009-T2: Spring and React each publish RED and implementation roles."""

        skill_path = SKILL_ROOT / "SKILL.md"
        self.assertTrue(skill_path.is_file(), "sdd-build/SKILL.md must be published")
        skill = skill_path.read_text(encoding="utf-8")
        for name in ROLE_REFERENCES:
            with self.subTest(name=name):
                self.assertIn(name, skill)
                self.assertTrue((SKILL_ROOT / "references" / name).is_file())

    def test_t009_t3_t5_role_contracts_separate_red_and_production_ownership(
        self,
    ) -> None:
        """T-009-T3/T5: role docs preserve the RED/GREEN ownership split."""

        references = SKILL_ROOT / "references"
        red_names = ROLE_REFERENCES[::2]
        implementer_names = ROLE_REFERENCES[1::2]
        for name in red_names:
            with self.subTest(role=name):
                path = references / name
                self.assertTrue(path.is_file())
                text = path.read_text(encoding="utf-8")
                self.assertIn("Test-IDs", text)
                self.assertIn("fichiers de test", text)
                self.assertNotIn("04-tasks.md en écriture", text)
        for name in implementer_names:
            with self.subTest(role=name):
                path = references / name
                self.assertTrue(path.is_file())
                text = path.read_text(encoding="utf-8")
                self.assertIn("preuve RED", text)
                self.assertIn("minimum", text)

    def test_t009_t4_t6_t7_cycle_contract_defines_gates_order_and_evidence(
        self,
    ) -> None:
        """T-009-T4/T6/T7: the cycle contract makes every transition auditable."""

        path = SKILL_ROOT / "references" / "tdd-cycle-contract.md"
        self.assertTrue(path.is_file())
        contract = path.read_text(encoding="utf-8")
        self.assertIn("RED → GREEN → REFACTOR → SIMPLIFY", contract)
        for term in (
            "signature",
            "argv",
            "échec attendu",
            "Test-IDs",
            "sortie expurgée",
            "fichiers concernés",
            "append_job_event",
        ):
            with self.subTest(term=term):
                self.assertIn(term, contract)

    def test_t009_t8_delegation_forbids_every_shared_artifact(self) -> None:
        """T-009-T8: the worker contract denies all shared artifact writes."""

        path = SKILL_ROOT / "references" / "delegation-contract.md"
        self.assertTrue(path.is_file())
        contract = path.read_text(encoding="utf-8")
        for artifact in SHARED_ARTIFACTS:
            with self.subTest(artifact=artifact):
                self.assertIn(artifact, contract)
        self.assertIn("aucun handle", contract)

    def test_t009_t9_cycle_contract_requires_immutable_idempotent_events(self) -> None:
        """T-009-T9: replay semantics are explicit in the published contract."""

        path = SKILL_ROOT / "references" / "tdd-cycle-contract.md"
        self.assertTrue(path.is_file())
        contract = path.read_text(encoding="utf-8")
        self.assertIn("event-id", contract)
        self.assertIn("idempotent", contract)
        self.assertIn("divergent", contract)

    def test_t009_t4_t8_t9_guard_composes_canonical_runtime_primitives(self) -> None:
        """T-009-T4/T8/T9: the guard calls runtime v2 instead of copying it."""

        guard_path = SKILL_ROOT / "scripts" / "build_guard.py"
        tree = ast.parse(guard_path.read_text(encoding="utf-8"))
        runtime_calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "runtime"
        }
        missing = [name for name in RUNTIME_PRIMITIVES if name not in runtime_calls]

        self.assertEqual(
            [],
            missing,
            "build_guard.py must call every canonical runtime primitive",
        )


if __name__ == "__main__":
    unittest.main()
