#!/usr/bin/env python3

import json
import os
from pathlib import Path
import stat
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

    def test_commit_plan_preserves_existing_artifact_modes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "feature-three"
            feature.mkdir()
            design_path = feature / "03-design.md"
            state_path = feature / ".tdd-state.json"
            design_path.write_text("decision: pending\n", encoding="utf-8")
            state_path.write_text(json.dumps(state(feature.name)), encoding="utf-8")
            os.chmod(design_path, 0o644)
            os.chmod(state_path, 0o640)
            snapshot = self.run_guard("snapshot", "--feature-dir", str(feature))

            design = feature / "03-design.approved.candidate.md"
            candidate = feature / ".tdd-state.candidate.json"
            design.write_text("decision: approve\n", encoding="utf-8")
            candidate.write_text(json.dumps(state(feature.name)), encoding="utf-8")
            os.chmod(design, 0o600)
            os.chmod(candidate, 0o600)

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
            self.assertEqual(0o644, stat.S_IMODE(design_path.stat().st_mode))
            self.assertEqual(0o640, stat.S_IMODE(state_path.stat().st_mode))

    def test_write_state_rejects_a_different_feature_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "feature-four"
            feature.mkdir()
            candidate = feature / ".tdd-state.candidate.json"
            candidate.write_text(json.dumps(state("another-feature")), encoding="utf-8")

            self.run_guard(
                "write-state",
                "--feature-dir",
                str(feature),
                "--expected-token",
                "absent",
                "--state-candidate",
                str(candidate),
                expected=2,
            )
            self.assertFalse((feature / ".tdd-state.json").exists())

    def test_commit_plan_rejects_an_empty_task_map(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "feature-five"
            feature.mkdir()
            design = feature / "03-design.approved.candidate.md"
            candidate = feature / ".tdd-state.candidate.json"
            design.write_text("decision: approve\n", encoding="utf-8")
            candidate.write_text(
                json.dumps({"feature_id": feature.name, "active_task": None, "tasks": {}}),
                encoding="utf-8",
            )

            self.run_guard(
                "commit-plan",
                "--feature-dir",
                str(feature),
                "--expected-token",
                "absent",
                "--design-candidate",
                str(design),
                "--state-candidate",
                str(candidate),
                expected=2,
            )
            self.assertFalse((feature / "03-design.md").exists())
            self.assertFalse((feature / ".tdd-state.json").exists())


if __name__ == "__main__":
    unittest.main()
