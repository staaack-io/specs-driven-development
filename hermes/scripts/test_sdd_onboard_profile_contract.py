#!/usr/bin/env python3
"""Regression test for the sdd-onboard contract in a profile layout."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


HERMES_SKILLS = Path(__file__).resolve().parents[1] / "skills"


class SddOnboardProfileContractTest(unittest.TestCase):
    def test_distributed_contract_runs_from_profile_skills_layout(self) -> None:
        """T-001-T1 / AC-098, AC-099: the distributed contract is portable."""
        with tempfile.TemporaryDirectory(prefix="sdd-onboard-profile-") as temporary:
            profile_root = Path(temporary) / "profile"
            profile_skills = profile_root / "skills"
            shutil.copytree(HERMES_SKILLS, profile_skills)
            contract = (
                profile_skills
                / "sdd-onboard"
                / "scripts"
                / "test_skill_contract.py"
            )

            completed = subprocess.run(
                [sys.executable, str(contract)],
                cwd=profile_root,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(
                0,
                completed.returncode,
                completed.stdout + completed.stderr,
            )


if __name__ == "__main__":
    unittest.main()
