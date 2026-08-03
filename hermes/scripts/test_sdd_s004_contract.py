#!/usr/bin/env python3
"""Source-level acceptance contract for S-004."""

from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
FEATURE = ROOT / ".specs" / "2026-07-31-hermes-parallel-sdd"


class SddS004ContractTest(unittest.TestCase):
    def test_t015_t8_help_and_docs_publish_the_installed_command(self) -> None:
        help_text = (ROOT / "hermes/skills/sdd-help/SKILL.md").read_text()
        readme = (ROOT / "hermes/README.md").read_text()
        migration = (ROOT / "docs/codex-migration.md").read_text()
        installed = help_text.split("commandes suivantes", 1)[0]
        self.assertIn("/sdd-code-simplify <path> [--dry-run]", installed)
        self.assertIn("/sdd-code-simplify", readme)
        self.assertNotIn("reste planifiée", readme)
        self.assertIn("| `$code-simplify` | `/sdd-code-simplify` | converti |", migration)
        self.assertNotIn("/sdd-code-simplify` reste sur la feuille de route", migration)

    def test_t015_t8_manifest_has_exact_s004_coverage_and_primary_producers(self) -> None:
        tasks = (FEATURE / "04-tasks.md").read_text(encoding="utf-8")
        section = tasks.split("### S-004 Primary AC Coverage Matrix", 1)[1]
        section = section.split("### S-004 Dependency", 1)[0]
        rows = re.findall(r"^\| (AC-\d{3}) \| (T-\d{3}) \|", section, re.MULTILINE)
        self.assertEqual([("AC-014", "T-016"), ("AC-139", "T-016")], rows)


if __name__ == "__main__":
    unittest.main()
