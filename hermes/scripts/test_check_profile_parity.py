from __future__ import annotations

import contextlib
import io
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from check_profile_parity import compare_directories, compare_profile_trees, main


class ProfileParityTest(unittest.TestCase):
    def test_identical_directories_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            published = root / "published"
            source.mkdir()
            published.mkdir()
            (source / "SKILL.md").write_text("same\n", encoding="utf-8")
            (published / "SKILL.md").write_text("same\n", encoding="utf-8")

            self.assertEqual(compare_directories(source, published), [])

    def test_content_drift_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            published = root / "published"
            source.mkdir()
            published.mkdir()
            (source / "SKILL.md").write_text("canonical\n", encoding="utf-8")
            (published / "SKILL.md").write_text("drifted\n", encoding="utf-8")

            self.assertEqual(
                compare_directories(source, published),
                ["content differs: SKILL.md"],
            )

    def test_missing_and_unexpected_files_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            published = root / "published"
            source.mkdir()
            published.mkdir()
            (source / "required.md").write_text("required\n", encoding="utf-8")
            (published / "extra.md").write_text("extra\n", encoding="utf-8")

            self.assertEqual(
                compare_directories(source, published),
                [
                    "missing from profile: required.md",
                    "unexpected in profile: extra.md",
                ],
            )

    def test_profile_parity_reports_runtime_missing_unexpected_and_content_drift(
        self,
    ) -> None:
        """T-006-T3 / AC-058-AC-060, AC-278: runtime drift is explicit."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            profile = root / "profile"
            (source / "skills").mkdir(parents=True)
            (profile / "skills").mkdir(parents=True)
            (source / "runtime").mkdir(parents=True)
            (profile / "hermes" / "runtime").mkdir(parents=True)
            (source / "skills" / "SKILL.md").write_text("same\n", encoding="utf-8")
            (profile / "skills" / "SKILL.md").write_text("same\n", encoding="utf-8")
            (source / "runtime" / "missing.py").write_text(
                "canonical\n", encoding="utf-8"
            )
            (source / "runtime" / "changed.py").write_text(
                "canonical\n", encoding="utf-8"
            )
            (profile / "hermes" / "runtime" / "changed.py").write_text(
                "drifted\n", encoding="utf-8"
            )
            (profile / "hermes" / "runtime" / "extra.py").write_text(
                "extra\n", encoding="utf-8"
            )

            self.assertEqual(
                [
                    "runtime: missing from profile: missing.py",
                    "runtime: unexpected in profile: extra.py",
                    "runtime: content differs: changed.py",
                ],
                compare_profile_trees(source, profile),
            )

    def test_cli_preserves_success_drift_and_invalid_profile_exit_codes(self) -> None:
        """T-006-T3: CLI keeps 0/1/2 while checking skills and runtime."""
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary) / "profile"
            source_root = Path(__file__).resolve().parents[1]
            shutil.copytree(source_root / "skills", profile / "skills")
            shutil.copytree(source_root / "runtime", profile / "hermes" / "runtime")

            with mock.patch.object(
                sys,
                "argv",
                ["check_profile_parity.py", str(profile)],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main())

            (profile / "hermes" / "runtime" / "README.md").unlink()
            with mock.patch.object(
                sys,
                "argv",
                ["check_profile_parity.py", str(profile)],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(1, main())

            shutil.rmtree(profile / "hermes" / "runtime")
            with mock.patch.object(
                sys,
                "argv",
                ["check_profile_parity.py", str(profile)],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(1, main())

            shutil.rmtree(profile / "skills")
            with mock.patch.object(
                sys,
                "argv",
                ["check_profile_parity.py", str(profile)],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(2, main())


if __name__ == "__main__":
    unittest.main()
