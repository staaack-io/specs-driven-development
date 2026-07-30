#!/usr/bin/env python3

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("tdd_state_guard.py")


def state(feature_id: str, phase: str = "pending") -> dict:
    return {
        "feature_id": feature_id,
        "active_task": None,
        "tasks": {
            "T-001": {
                "phase": phase,
                "red_at": None,
                "red_test_signature": None,
                "red_failure_excerpt": None,
                "green_at": None,
                "files_in_scope": [],
            }
        },
    }


class GuardTest(unittest.TestCase):
    def run_guard(self, *arguments: str, expected: int = 0) -> dict:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(expected, result.returncode, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_commit_plan_from_absent_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "feature-one"
            feature.mkdir()
            design = feature / "03-design.approved.candidate.md"
            candidate = feature / ".tdd-state.candidate.json"
            design.write_text("decision: approve\n", encoding="utf-8")
            candidate.write_text(json.dumps(state(feature.name)), encoding="utf-8")

            snapshot = self.run_guard("snapshot", "--feature-dir", str(feature))
            self.assertEqual("absent", snapshot["token"])
            self.run_guard(
                "commit-plan",
                "--feature-dir",
                str(feature),
                "--expected-token",
                snapshot["token"],
                "--design-candidate",
                str(design),
                "--state-candidate",
                str(candidate),
            )
            self.assertEqual("decision: approve\n", (feature / "03-design.md").read_text())
            self.assertEqual(state(feature.name), json.loads((feature / ".tdd-state.json").read_text()))

    def test_concurrent_change_rejects_both_plan_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "feature-two"
            feature.mkdir()
            original_design = feature / "03-design.md"
            original_design.write_text("decision: pending\n", encoding="utf-8")
            snapshot = self.run_guard("snapshot", "--feature-dir", str(feature))

            concurrent = state(feature.name, phase="red")
            (feature / ".tdd-state.json").write_text(json.dumps(concurrent), encoding="utf-8")
            design = feature / "03-design.approved.candidate.md"
            candidate = feature / ".tdd-state.candidate.json"
            design.write_text("decision: approve\n", encoding="utf-8")
            candidate.write_text(json.dumps(state(feature.name)), encoding="utf-8")

            self.run_guard(
                "commit-plan",
                "--feature-dir",
                str(feature),
                "--expected-token",
                snapshot["token"],
                "--design-candidate",
                str(design),
                "--state-candidate",
                str(candidate),
                expected=2,
            )
            self.assertEqual("decision: pending\n", original_design.read_text())
            self.assertEqual(concurrent, json.loads((feature / ".tdd-state.json").read_text()))


if __name__ == "__main__":
    unittest.main()
