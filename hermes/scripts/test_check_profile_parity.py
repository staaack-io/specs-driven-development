from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from check_profile_parity import compare_directories


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


if __name__ == "__main__":
    unittest.main()
