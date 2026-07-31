#!/usr/bin/env python3
"""Forward tests for the repository-local Hermes skill validator."""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import validate_skills as validator


class ValidateSkillsTest(unittest.TestCase):
    def repository(self, destination: Path) -> Path:
        root = destination / "repository"
        (root / "hermes/skills").mkdir(parents=True)
        (root / ".gitignore").write_text(
            "__pycache__/\nhermes/skills/*/ignored/\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", ".gitignore"], cwd=root, check=True)
        return root

    def add_skill(self, root: Path, name: str = "demo-skill") -> Path:
        skill = root / "hermes/skills" / name
        references = skill / "references"
        references.mkdir(parents=True)
        (references / "contract.md").write_text("# Contract\n\nInstructions.\n", encoding="utf-8")
        (skill / "SKILL.md").write_text(
            "---\n"
            f"name: {name}\n"
            'description: "A portable demonstration skill."\n'
            "---\n\n"
            "# Demo\n\n"
            "Read the [contract](references/contract.md).\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "hermes/skills"], cwd=root, check=True)
        return skill

    def validate(self, root: Path) -> tuple[int, list[str]]:
        count, errors = validator.validate_skills(root / "hermes/skills", root)
        return count, [error.message for error in errors]

    def replace_skill(self, skill: Path, content: str) -> None:
        (skill / "SKILL.md").write_text(content, encoding="utf-8")

    def test_current_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            self.add_skill(root)

            count, errors = self.validate(root)

            self.assertEqual(1, count)
            self.assertEqual([], errors)

    def test_tracked_and_untracked_nonignored_resources_are_distributed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            untracked = skill / "references/new.md"
            untracked.write_text("# New\n\nContent.\n", encoding="utf-8")
            (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\n[New](references/new.md)\n",
                encoding="utf-8",
            )

            _count, errors = self.validate(root)

            self.assertEqual([], errors)

    def test_malformed_yaml_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            self.replace_skill(skill, "---\nname: [unterminated\n---\n# Demo\n\nText.\n")

            _count, errors = self.validate(root)

            self.assertTrue(any("invalid YAML" in error for error in errors))

    def test_duplicate_yaml_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            self.replace_skill(
                skill,
                "---\nname: demo-skill\nname: duplicate\ndescription: demo\n---\n"
                "# Demo\n\nText.\n",
            )

            _count, errors = self.validate(root)

            self.assertTrue(any("duplicate key" in error for error in errors))

    def test_non_mapping_yaml_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            self.replace_skill(skill, "---\n- name\n- description\n---\n# Demo\n\nText.\n")

            _count, errors = self.validate(root)

            self.assertIn("YAML frontmatter must be a mapping", errors)

    def test_non_string_yaml_value_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            self.replace_skill(
                skill,
                "---\nname: demo-skill\ndescription: true\n---\n# Demo\n\nText.\n",
            )

            _count, errors = self.validate(root)

            self.assertTrue(any("must be a non-empty string" in error for error in errors))

    def test_empty_yaml_value_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            self.replace_skill(
                skill,
                "---\nname: demo-skill\ndescription: ''\n---\n# Demo\n\nText.\n",
            )

            _count, errors = self.validate(root)

            self.assertTrue(any("must be a non-empty string" in error for error in errors))

    def test_frontmatter_name_must_match_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8").replace(
                    "name: demo-skill", "name: other-skill", 1
                ),
                encoding="utf-8",
            )

            _count, errors = self.validate(root)

            self.assertTrue(any("does not match folder" in error for error in errors))

    def test_body_requires_h1_and_instructions(self) -> None:
        cases = (
            ("Text only.\n", "level-one title"),
            ("# Demo\n", "must contain instructions"),
        )
        for body, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temporary:
                root = self.repository(Path(temporary))
                skill = self.add_skill(root)
                self.replace_skill(
                    skill,
                    "---\nname: demo-skill\ndescription: demo\n---\n" + body,
                )

                _count, errors = self.validate(root)

                self.assertTrue(any(expected in error for error in errors), errors)

    def test_missing_inline_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\n[Missing](references/missing.md)\n",
                encoding="utf-8",
            )

            _count, errors = self.validate(root)

            self.assertTrue(any("missing local reference" in error for error in errors))

    def test_balanced_and_escaped_parentheses_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            reference = skill / "references/API(v2).md"
            reference.write_text("# API\n\nText.\n", encoding="utf-8")
            (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\n[Balanced](references/API(v2).md)\n"
                + "[Escaped](references/API\\(v2\\).md)\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "hermes/skills"], cwd=root, check=True)

            _count, errors = self.validate(root)

            self.assertEqual([], errors)

    def test_reference_definition_and_multiline_destination_are_validated(self) -> None:
        cases = (
            "[Guide][docs]\n\n[docs]: references/missing.md\n",
            "[Guide][docs]\n\n[docs]:\n  references/missing.md\n",
            "[Guide][doc\\]s]\n\n[doc\\]s]: references/missing.md\n",
        )
        for addition in cases:
            with self.subTest(addition=addition), tempfile.TemporaryDirectory() as temporary:
                root = self.repository(Path(temporary))
                skill = self.add_skill(root)
                (skill / "SKILL.md").write_text(
                    (skill / "SKILL.md").read_text(encoding="utf-8") + "\n" + addition,
                    encoding="utf-8",
                )

                _count, errors = self.validate(root)

                self.assertTrue(any("missing local reference" in error for error in errors))

    def test_html_href_and_src_are_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + '\n<a href="references/missing.md">Guide</a>\n'
                + '<img src="references/image.png">\n',
                encoding="utf-8",
            )

            _count, errors = self.validate(root)

            self.assertEqual(2, sum("missing local reference" in error for error in errors))

    def test_nested_markdown_is_recursive_and_cycles_terminate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            a = skill / "references/a.md"
            b = skill / "references/b.md"
            a.write_text("# A\n\n[B](b.md)\n", encoding="utf-8")
            b.write_text("# B\n\n[A](a.md)\n", encoding="utf-8")
            (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\n[A](references/a.md)\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "hermes/skills"], cwd=root, check=True)

            _count, errors = self.validate(root)

            self.assertEqual([], errors)

    def test_nested_markdown_missing_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            nested = skill / "references/nested.md"
            nested.write_text("# Nested\n\n[Missing](deeper.md)\n", encoding="utf-8")
            (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\n[Nested](references/nested.md)\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "hermes/skills"], cwd=root, check=True)

            _count, errors = self.validate(root)

            self.assertTrue(any("missing local reference: deeper.md" in error for error in errors))

    def test_reference_cannot_escape_its_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            sibling = self.add_skill(root, "sibling-skill")
            (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\n[Sibling](../sibling-skill/SKILL.md)\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "hermes/skills"], cwd=root, check=True)

            _count, errors = self.validate(root)

            self.assertTrue(any("escapes the skill" in error for error in errors))
            self.assertTrue((sibling / "SKILL.md").is_file())

    def test_markdown_recursion_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            a = skill / "references/a.md"
            a.write_text("# A\n\nText.\n", encoding="utf-8")
            (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\n[A](references/a.md)\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "hermes/skills"], cwd=root, check=True)

            with mock.patch.object(validator, "MAX_MARKDOWN_FILES", 1):
                _count, errors = self.validate(root)

            self.assertTrue(any("traversal exceeds" in error for error in errors))

    def test_ignored_reference_does_not_enter_distribution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            ignored = skill / "ignored/reference.md"
            ignored.parent.mkdir()
            ignored.write_text("# Ignored\n\nText.\n", encoding="utf-8")
            (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\n[Ignored](ignored/reference.md)\n",
                encoding="utf-8",
            )

            _count, errors = self.validate(root)

            self.assertTrue(any("local reference is ignored" in error for error in errors))

    def test_distributed_resource_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            outside = root / "outside.md"
            outside.write_text("# Outside\n", encoding="utf-8")
            link = skill / "references/external.md"
            try:
                link.symlink_to(outside)
            except (NotImplementedError, OSError) as error:
                self.skipTest(f"symbolic links unavailable: {error}")
            subprocess.run(["git", "add", "hermes/skills"], cwd=root, check=True)

            _count, errors = self.validate(root)

            self.assertTrue(any("symbolic links are not allowed" in error for error in errors))

    def test_distributed_skill_directory_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            outside = root / "outside-skill"
            outside.mkdir()
            (outside / "SKILL.md").write_text("# Outside\n", encoding="utf-8")
            link = root / "hermes/skills/linked-skill"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except (NotImplementedError, OSError) as error:
                self.skipTest(f"symbolic links unavailable: {error}")
            subprocess.run(["git", "add", "hermes/skills/linked-skill"], cwd=root, check=True)

            _count, errors = self.validate(root)

            self.assertTrue(any("symbolic links are not allowed" in error for error in errors))

    def test_ignored_symlink_has_no_effect(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            ignored = skill / "ignored/link"
            ignored.parent.mkdir()
            try:
                ignored.symlink_to(root / "outside")
            except (NotImplementedError, OSError) as error:
                self.skipTest(f"symbolic links unavailable: {error}")

            _count, errors = self.validate(root)

            self.assertEqual([], errors)

    def test_nonembedded_codex_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            skill = self.add_skill(root)
            (skill / "references/contract.md").write_text(
                "# Contract\n\nRead `.codex/agents/reviewer.toml`.\n",
                encoding="utf-8",
            )

            _count, errors = self.validate(root)

            self.assertTrue(any("non-embedded Codex path" in error for error in errors))

    def test_distributed_skill_without_skill_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            resource = root / "hermes/skills/incomplete/references/readme.md"
            resource.parent.mkdir(parents=True)
            resource.write_text("# Incomplete\n", encoding="utf-8")
            subprocess.run(["git", "add", "hermes/skills"], cwd=root, check=True)

            count, errors = self.validate(root)

            self.assertEqual(1, count)
            self.assertTrue(any("distributed SKILL.md is required" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
