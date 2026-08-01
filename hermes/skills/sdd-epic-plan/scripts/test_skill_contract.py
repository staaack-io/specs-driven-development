#!/usr/bin/env python3
"""Static contract checks for the Hermes sdd-epic-plan skill."""

from pathlib import Path
import re
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]


class SkillContractTest(unittest.TestCase):
    def skill_text(self) -> str:
        return (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_frontmatter_contains_only_name_and_description(self) -> None:
        lines = self.skill_text().splitlines()
        self.assertEqual("---", lines[0])
        closing = lines.index("---", 1)
        keys = {line.split(":", 1)[0] for line in lines[1:closing]}
        self.assertEqual({"name", "description"}, keys)
        self.assertIn("name: sdd-epic-plan", lines[1:closing])

    def test_referenced_resources_exist(self) -> None:
        skill = self.skill_text()
        resources = (
            "references/delegation-contract.md",
            "references/epic-contract.md",
            "references/stack-evidence.md",
            "references/transaction-atomicity.md",
            "references/role-spring-architect.md",
            "references/role-react-nextjs-architect.md",
            "templates/epic-design.template.md",
            "templates/epic-roadmap.template.md",
            "scripts/epic_plan_guard.py",
        )
        for relative in resources:
            with self.subTest(relative=relative):
                self.assertIn(relative, skill)
                self.assertTrue((SKILL_ROOT / relative).is_file())

    def test_delegation_is_read_only_and_single_writer(self) -> None:
        skill = self.skill_text()
        delegation = (SKILL_ROOT / "references/delegation-contract.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("unique écrivain", skill)
        self.assertIn("delegate_task", skill)
        self.assertIn("max_iterations: 30", skill)
        self.assertIn("files_modified: []", skill)
        self.assertIn('"files_modified": []', delegation)
        self.assertIn("lecture seule", delegation)

    def test_stack_and_local_id_namespacing_are_explicit(self) -> None:
        skill = self.skill_text()
        contract = (SKILL_ROOT / "references/epic-contract.md").read_text(
            encoding="utf-8"
        )
        stack = (SKILL_ROOT / "references/stack-evidence.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("stack: unknown", skill)
        self.assertIn("spring-architect:Q-NNN", contract)
        self.assertIn("react-nextjs-architect:Q-NNN", contract)
        self.assertIn("package.json", stack)
        self.assertIn("org.springframework.boot", stack)

    def test_design_owns_the_only_decision_and_roadmap_targets_final(self) -> None:
        design = (SKILL_ROOT / "templates/epic-design.template.md").read_text(
            encoding="utf-8"
        )
        roadmap = (SKILL_ROOT / "templates/epic-roadmap.template.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("- decision: en attente", design)
        self.assertNotIn("- decision:", roadmap)
        self.assertIn("03-epic-design.md", roadmap)
        self.assertNotIn("03-epic-design.candidate.md", roadmap)

    def test_no_vps_kanban_or_deployment_command_is_required(self) -> None:
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in SKILL_ROOT.rglob("*.md")
        )
        forbidden = (
            r"hermes\s+.*kanban",
            r"gateway\s+install",
            r"profile\s+update",
            r"ssh\s+.*ubuntu@",
            r"--yolo",
        )
        for pattern in forbidden:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, text, flags=re.IGNORECASE))


if __name__ == "__main__":
    unittest.main()
