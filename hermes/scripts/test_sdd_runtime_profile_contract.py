#!/usr/bin/env python3
"""Regression test for the shared SDD runtime in a profile layout."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


HERMES_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PLAN_SKILL = HERMES_ROOT / "skills" / "sdd-plan"
SOURCE_RUNTIME = HERMES_ROOT / "runtime"
PLAN_GUARD_RELATIVE = Path("skills/sdd-plan/scripts/tdd_state_guard.py")
FIXTURE_FEATURE_NAME = "fixture-feature"
SYMBOLIC_RUNTIME_ERROR = "distributed runtime path must not be symbolic"


class SddRuntimeProfileContractTest(unittest.TestCase):
    def install_profile(self, root: Path) -> tuple[Path, Path]:
        profile_root = root / "profile"
        shutil.copytree(SOURCE_PLAN_SKILL, profile_root / "skills" / "sdd-plan")
        shutil.copytree(SOURCE_RUNTIME, profile_root / "hermes" / "runtime")
        feature = profile_root / FIXTURE_FEATURE_NAME
        feature.mkdir()
        return profile_root, feature

    def run_snapshot(
        self, profile_root: Path, feature: Path, guard: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        selected_guard = guard or profile_root / PLAN_GUARD_RELATIVE
        return subprocess.run(
            [
                sys.executable,
                str(selected_guard),
                "snapshot",
                "--feature-dir",
                str(feature),
                "--allow-non-git-test-fixture",
            ],
            cwd=profile_root,
            capture_output=True,
            text=True,
            check=False,
        )

    def run_test_script(
        self, profile_root: Path, test_script: Path
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(test_script), "-v"],
            cwd=profile_root,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_distributed_plan_guard_loads_shared_runtime(self) -> None:
        """T-006-T1 / AC-048, AC-101, AC-276-AC-280: profile import works."""
        with tempfile.TemporaryDirectory(prefix="sdd-runtime-profile-") as temporary:
            profile_root, feature = self.install_profile(Path(temporary))
            completed = self.run_snapshot(profile_root, feature)

            self.assertEqual(
                0,
                completed.returncode,
                completed.stdout + completed.stderr,
            )

    def test_plan_guard_loads_runtime_in_source_and_profile_layouts(self) -> None:
        """T-006-T2 / AC-048, AC-101, AC-276-AC-280: both layouts work."""
        with tempfile.TemporaryDirectory(prefix="sdd-runtime-layouts-") as temporary:
            root = Path(temporary)
            profile_root, profile_feature = self.install_profile(root)
            profile_result = self.run_snapshot(profile_root, profile_feature)

            source_feature = root / "source-feature"
            source_feature.mkdir()
            source_result = self.run_snapshot(
                HERMES_ROOT.parent,
                source_feature,
                HERMES_ROOT / PLAN_GUARD_RELATIVE,
            )

            self.assertEqual(0, source_result.returncode, source_result.stderr)
            self.assertEqual(0, profile_result.returncode, profile_result.stderr)

    def test_distributed_layout_preserves_runtime_and_plan_regressions(self) -> None:
        """T-006-T4 / AC-048, AC-101, AC-276-AC-280: migrations stay safe."""
        with tempfile.TemporaryDirectory(prefix="sdd-runtime-regression-") as temporary:
            profile_root, _ = self.install_profile(Path(temporary))
            plan_tests = (
                profile_root
                / "skills"
                / "sdd-plan"
                / "scripts"
                / "test_tdd_state_guard.py"
            )
            runtime_tests = (
                profile_root
                / "hermes"
                / "runtime"
                / "test_sdd_runtime_guard.py"
            )

            for test_script in (plan_tests, runtime_tests):
                with self.subTest(test_script=test_script.name):
                    completed = self.run_test_script(profile_root, test_script)
                    self.assertEqual(
                        0,
                        completed.returncode,
                        completed.stdout + completed.stderr,
                    )

    def test_runtime_resolution_rejects_symbolic_or_external_roots(self) -> None:
        """T-006-T5 / AC-276-AC-280: symbolic and escaping roots fail closed."""
        with tempfile.TemporaryDirectory(prefix="sdd-runtime-isolation-") as temporary:
            root = Path(temporary)
            profile_root, feature = self.install_profile(root)
            runtime = profile_root / "hermes" / "runtime"
            shutil.rmtree(runtime)
            runtime.symlink_to(SOURCE_RUNTIME, target_is_directory=True)

            symbolic_runtime = self.run_snapshot(profile_root, feature)
            self.assertNotEqual(0, symbolic_runtime.returncode)
            self.assertIn(
                SYMBOLIC_RUNTIME_ERROR,
                symbolic_runtime.stdout + symbolic_runtime.stderr,
            )

            external_profile = root / "external-profile"
            shutil.copytree(profile_root / "skills", external_profile / "skills")
            shutil.copytree(SOURCE_RUNTIME, external_profile / "hermes" / "runtime")
            external_feature = external_profile / FIXTURE_FEATURE_NAME
            external_feature.mkdir()
            linked_profile = root / "linked-profile"
            linked_profile.symlink_to(external_profile, target_is_directory=True)

            symbolic_root = self.run_snapshot(
                linked_profile,
                linked_profile / FIXTURE_FEATURE_NAME,
            )
            self.assertNotEqual(0, symbolic_root.returncode)
            self.assertIn(
                SYMBOLIC_RUNTIME_ERROR,
                symbolic_root.stdout + symbolic_root.stderr,
            )

            outside_root = root / "outside-root"
            outside_profile = outside_root / "profile"
            shutil.copytree(
                SOURCE_PLAN_SKILL,
                outside_profile / "skills" / "sdd-plan",
            )
            shutil.copytree(SOURCE_RUNTIME, outside_root / "hermes" / "runtime")
            outside_feature = outside_profile / FIXTURE_FEATURE_NAME
            outside_feature.mkdir()

            external_runtime = self.run_snapshot(outside_profile, outside_feature)
            self.assertNotEqual(0, external_runtime.returncode)
            self.assertIn(
                "distributed runtime module is missing from root",
                external_runtime.stdout + external_runtime.stderr,
            )


if __name__ == "__main__":
    unittest.main()
