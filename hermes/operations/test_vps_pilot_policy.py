from __future__ import annotations

import ast
import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("vps_pilot_policy.py")


def load_policy_module():
    if not MODULE_PATH.is_file():
        raise AssertionError("T-030-T1: the VPS pilot policy validator is absent")
    spec = importlib.util.spec_from_file_location("vps_pilot_policy", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def compliant_policy() -> dict[str, object]:
    return {
        "evidence": {
            "contains_secret": False,
            "contains_token": False,
            "contains_credential": False,
            "contains_transcript": False,
            "paths": ["jobs/T-035/001-sandbox.json"],
        },
        "hermes": {
            "login_shell": True,
            "binary": "/home/ubuntu/.local/bin/hermes",
            "board": "super-lily",
            "yolo": False,
        },
        "delegation": {
            "max_spawn_depth": 1,
            "subagent_auto_approve": False,
        },
        "sandbox": {"successful_parallel_jobs": 2},
        "gateway": {
            "install_requested": True,
            "scope": "user",
            "uses_sudo": False,
        },
        "retention": {
            "proofs_complete": False,
            "card_retained": True,
            "branch_retained": True,
            "worktree_retained": True,
            "logs_retained": True,
            "journal_retained": True,
        },
    }


class VpsPilotPolicyTest(unittest.TestCase):
    """Executable contract for T-030-T1 through T-030-T7."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_module = load_policy_module()

    def validate(self, policy: dict[str, object]) -> tuple[str, ...]:
        return self.policy_module.validate_vps_pilot_policy(policy)

    def test_t030_t1_accepts_a_compliant_structured_policy(self) -> None:
        self.assertEqual((), self.validate(compliant_policy()))
        self.assertTrue(self.validate({}))

    def test_t030_t2_rejects_secrets_transcripts_and_absolute_evidence_paths(self) -> None:
        policy = compliant_policy()
        policy["evidence"] = {
            "contains_secret": True,
            "contains_token": True,
            "contains_credential": True,
            "contains_transcript": True,
            "paths": ["/tmp/hermes-transcript.txt"],
        }

        self.assertEqual(
            (
                "evidence.secret_forbidden",
                "evidence.token_forbidden",
                "evidence.credential_forbidden",
                "evidence.transcript_forbidden",
                "evidence.absolute_path_forbidden",
            ),
            self.validate(policy),
        )

    def test_t030_t3_requires_safe_hermes_invocation_and_explicit_board(self) -> None:
        absolute_binary_policy = compliant_policy()
        absolute_binary_hermes = dict(absolute_binary_policy["hermes"])
        absolute_binary_hermes["login_shell"] = False
        absolute_binary_policy["hermes"] = absolute_binary_hermes
        self.assertEqual((), self.validate(absolute_binary_policy))

        unsafe_cases = (
            ("login_shell", False, "hermes.login_shell_or_absolute_binary_required"),
            ("board", "", "hermes.explicit_board_required"),
            ("yolo", True, "hermes.yolo_forbidden"),
        )

        for field, value, expected in unsafe_cases:
            with self.subTest(field=field):
                policy = compliant_policy()
                hermes = dict(policy["hermes"])
                hermes[field] = value
                if field == "login_shell":
                    hermes["binary"] = "hermes"
                policy["hermes"] = hermes
                self.assertIn(expected, self.validate(policy))

    def test_t030_t4_enforces_capacity_and_two_success_gateway_barrier(self) -> None:
        policy = compliant_policy()
        policy["delegation"] = {
            "max_spawn_depth": 2,
            "subagent_auto_approve": True,
        }
        policy["sandbox"] = {"successful_parallel_jobs": 1}

        self.assertEqual(
            (
                "delegation.max_spawn_depth_must_equal_one",
                "delegation.auto_approve_forbidden",
                "gateway.two_successful_jobs_required",
            ),
            self.validate(policy),
        )

        policy["delegation"] = {
            "max_spawn_depth": 1,
            "subagent_auto_approve": False,
        }
        policy["sandbox"] = {"successful_parallel_jobs": "2"}
        self.assertEqual(
            ("gateway.two_successful_jobs_required",),
            self.validate(policy),
        )

    def test_t030_t5_rejects_system_gateway_and_sudo(self) -> None:
        policy = compliant_policy()
        policy["gateway"] = {
            "install_requested": True,
            "scope": "system",
            "uses_sudo": True,
        }

        self.assertEqual(
            ("gateway.system_scope_forbidden", "gateway.sudo_forbidden"),
            self.validate(policy),
        )

    def test_t030_t6_retains_every_resource_until_proofs_are_complete(self) -> None:
        for resource in ("card", "branch", "worktree", "logs", "journal"):
            with self.subTest(resource=resource):
                policy = compliant_policy()
                retention = dict(policy["retention"])
                retention[f"{resource}_retained"] = False
                policy["retention"] = retention
                self.assertIn(
                    f"retention.{resource}_must_be_retained",
                    self.validate(policy),
                )

    def test_t030_t7_module_has_no_execution_or_network_primitive(self) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        forbidden_roots = {
            "asyncio",
            "http",
            "paramiko",
            "requests",
            "socket",
            "subprocess",
            "urllib",
        }
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }

        self.assertTrue(forbidden_roots.isdisjoint(imports))
        self.assertTrue({"exec", "eval", "compile", "system", "popen"}.isdisjoint(calls))


if __name__ == "__main__":
    unittest.main()
