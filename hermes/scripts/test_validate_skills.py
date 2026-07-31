#!/usr/bin/env python3
"""Tests for the repository-local Hermes skill validator."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import validate_skills as validator


class ValidateSkillsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.skills = Path(self.temporary.name) / "skills"
        self.skills.mkdir()

    def add_skill(
        self,
        folder: str = "demo-skill",
        *,
        name: str = "demo-skill",
        description: str = "A portable demonstration skill.",
    ) -> Path:
        root = self.skills / folder
        (root / "references").mkdir(parents=True)
        (root / "references/contract.md").write_text("# Contract\n", encoding="utf-8")
        (root / "SKILL.md").write_text(
            "---\n"
            f"name: {name}\n"
            f'description: "{description}"\n'
            "---\n\n"
            "# Demo\n\n"
            "Read the [contract](references/contract.md).\n",
            encoding="utf-8",
        )
        return root

    def messages(self) -> list[str]:
        _count, errors = validator.validate_skills(self.skills)
        return [error.message for error in errors]

    def test_valid_embedded_skill_passes(self) -> None:
        self.add_skill()

        count, errors = validator.validate_skills(self.skills)

        self.assertEqual(1, count)
        self.assertEqual([], errors)

    def test_name_must_match_folder(self) -> None:
        self.add_skill(name="different-name")

        self.assertTrue(any("does not match folder" in message for message in self.messages()))

    def test_description_is_required(self) -> None:
        self.add_skill(description="")

        self.assertIn("frontmatter description is required", self.messages())

    def test_missing_local_link_is_reported(self) -> None:
        root = self.add_skill()
        (root / "references/contract.md").unlink()

        self.assertTrue(any("missing local link target" in message for message in self.messages()))

    def test_local_link_cannot_escape_the_skill(self) -> None:
        root = self.add_skill()
        (self.skills / "outside.md").write_text("outside\n", encoding="utf-8")
        (root / "SKILL.md").write_text(
            "---\nname: demo-skill\ndescription: demo\n---\n\n"
            "[outside](../outside.md)\n",
            encoding="utf-8",
        )

        self.assertTrue(any("escapes the skill" in message for message in self.messages()))

    def test_codex_path_in_embedded_resource_is_reported(self) -> None:
        root = self.add_skill()
        (root / "references/contract.md").write_text(
            "Read `.codex/agents/reviewer.toml`.\n", encoding="utf-8"
        )

        self.assertTrue(any("Codex path" in message for message in self.messages()))

    def test_each_skill_directory_requires_skill_file(self) -> None:
        (self.skills / "incomplete").mkdir()

        count, errors = validator.validate_skills(self.skills)

        self.assertEqual(1, count)
        self.assertTrue(any("regular SKILL.md" in error.message for error in errors))


if __name__ == "__main__":
    unittest.main()
