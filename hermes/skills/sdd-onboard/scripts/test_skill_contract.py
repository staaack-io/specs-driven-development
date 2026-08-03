#!/usr/bin/env python3
"""Static integration checks for the published sdd-onboard surface."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
HERMES_SKILLS = SKILL_ROOT.parent
ARTIFACTS = (
    "_onboarding.md",
    "_stack.json",
    "_baseline.json",
    "_starter-design.md",
    "_known-debt.md",
)


class SkillContractTest(unittest.TestCase):
    def test_all_referenced_resources_exist(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        expected = (
            "references/artifact-contract.md",
            "references/classification.md",
            "references/delegation-contract.md",
            "references/transaction-atomicity.md",
            "references/role-spring-onboarding.md",
            "references/role-react-nextjs-onboarding.md",
            "templates/onboarding.template.md",
            "templates/stack.template.json",
            "templates/baseline.template.json",
            "templates/starter-design.template.md",
            "templates/known-debt.template.md",
            "scripts/onboarding_guard.py",
        )
        for relative in expected:
            with self.subTest(relative=relative):
                self.assertIn(relative.split("/")[-1], skill)
                self.assertTrue((SKILL_ROOT / relative).is_file())

    def test_single_writer_and_read_only_delegation_are_explicit(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        delegation = (SKILL_ROOT / "references/delegation-contract.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("unique écrivain", skill)
        self.assertIn("delegate_task", skill)
        self.assertIn("max_iterations: 30", skill)
        self.assertIn("files_modified", skill)
        self.assertIn('"files_modified": []', delegation)
        self.assertIn("Aucun build, test, lint", delegation)
        self.assertNotIn("/sdd-roles", skill)

    def test_all_five_artifacts_are_shared_by_skill_help_status_and_docs(self) -> None:
        surfaces = {
            "skill": (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8"),
            "status": (HERMES_SKILLS / "sdd-status/SKILL.md").read_text(
                encoding="utf-8"
            ),
            "artifact contract": (
                SKILL_ROOT / "references/artifact-contract.md"
            ).read_text(encoding="utf-8"),
        }
        for surface, text in surfaces.items():
            for artifact in ARTIFACTS:
                with self.subTest(surface=surface, artifact=artifact):
                    self.assertIn(artifact, text)

        help_text = (HERMES_SKILLS / "sdd-help/SKILL.md").read_text(
            encoding="utf-8"
        )
        installed, roadmap = help_text.split(
            "Signaler séparément que les commandes suivantes", maxsplit=1
        )
        self.assertIn("/sdd-onboard", installed)
        self.assertNotIn("/sdd-onboard", roadmap)

    def test_json_templates_are_valid_and_versioned(self) -> None:
        for name in ("stack.template.json", "baseline.template.json"):
            value = json.loads((SKILL_ROOT / "templates" / name).read_text())
            self.assertEqual(1, value["schema_version"])
            self.assertEqual("<git_sha>", value["git_sha"])

    def test_mapping_marks_only_converted_commands_as_converted(self) -> None:
        help_text = (HERMES_SKILLS / "sdd-help/SKILL.md").read_text(
            encoding="utf-8"
        )
        installed, roadmap = help_text.split(
            "Signaler séparément que les commandes suivantes", maxsplit=1
        )
        self.assertIn("/sdd-onboard", installed)
        self.assertNotIn("/sdd-onboard", roadmap)
        self.assertIn("/sdd-build", installed)
        self.assertNotIn("/sdd-build", roadmap)
        self.assertIn("/sdd-code-simplify", installed)
        self.assertNotIn("/sdd-code-simplify", roadmap)


if __name__ == "__main__":
    unittest.main()
