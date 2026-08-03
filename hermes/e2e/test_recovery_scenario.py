#!/usr/bin/env python3
"""Executable recovery and transactional fan-in proofs for T-026."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("recovery_scenario.py")


def load_scenario():
    if not MODULE_PATH.is_file():
        raise AssertionError(
            "T-026-T1: recovery_scenario.py must implement interruption recovery"
        )
    spec = importlib.util.spec_from_file_location("recovery_scenario", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run(injection: str) -> dict[str, object]:
    scenario = load_scenario()
    with tempfile.TemporaryDirectory(prefix="hermes-recovery-e2e-") as temporary:
        return scenario.run_recovery_scenario(Path(temporary), injection=injection)


class RecoveryScenarioTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.failure_result = run("failure")
        cls.timeout_result = run("timeout")

    def test_t026_t1_exposes_the_recovery_scenario(self) -> None:
        """T-026-T1/AC-157: the executable recovery entry point exists."""

        self.assertTrue(callable(load_scenario().run_recovery_scenario))

    def test_t026_t2_dependent_waits_for_observed_fan_in_and_explicit_go(self) -> None:
        """T-026-T2/AC-157: neither technical success nor merge alone opens fan-in."""

        result = self.failure_result

        self.assertFalse(result["admissibility"]["before_observed_fan_in"])
        self.assertFalse(result["admissibility"]["observed_without_go"])
        self.assertTrue(result["admissibility"]["observed_with_go"])

    def test_t026_t3_failure_and_timeout_are_writer_local(self) -> None:
        """T-026-T3/AC-158: both deterministic injections leave the peer green."""

        results = {
            "failure": self.failure_result,
            "timeout": self.timeout_result,
        }
        for injection, result in results.items():
            with self.subTest(injection=injection):
                self.assertEqual(injection, result["injection"])
                self.assertEqual("green", result["writers"]["T-101"]["status"])
                self.assertEqual("recovered", result["writers"]["T-102"]["status"])

    def test_t026_t4_green_writer_changes_and_proofs_survive_peer_failure(self) -> None:
        """T-026-T4/AC-158: a failed peer cannot revoke green output or journal."""

        result = self.failure_result

        self.assertTrue(result["green_writer_preserved"])
        self.assertGreater(result["journal_events"]["T-101"], 0)

    def test_t026_t5_retry_reuses_identical_surfaces_without_duplicates(self) -> None:
        """T-026-T5/AC-228: retry uses one job key and one envelope."""

        result = self.timeout_result

        self.assertTrue(result["retry_same_identity"])
        self.assertEqual(
            {"branches": 2, "worktrees": 2, "sessions": 2, "issues": 2, "prs": 2},
            result["resource_counts"],
        )

    def test_t026_t6_recovery_returns_a_complete_old_or_new_generation(self) -> None:
        """T-026-T6/AC-228: canonical recovery chooses one complete generation."""

        result = self.failure_result

        self.assertEqual(["old", "new"], result["fan_in_generations"])

    def test_t026_t7_no_shared_artifact_generation_is_mixed(self) -> None:
        """T-026-T7/AC-228: all three shared artifacts move atomically."""

        result = self.timeout_result

        for values in result["fan_in_snapshots"]:
            self.assertEqual(1, len(set(values.values())))

    def test_t026_t8_scenario_has_no_merge_operation(self) -> None:
        """T-026-T8/AC-157: the sandbox observes authorization but never merges."""

        result = self.failure_result
        source = MODULE_PATH.read_text(encoding="utf-8")

        self.assertEqual([], result["merge_commands"])
        self.assertNotIn("merge_pull_request", source)
        self.assertNotIn('"merge"', source)


if __name__ == "__main__":
    unittest.main()
