#!/usr/bin/env python3
"""Behavioral contract for the inert VPS pilot dry-run plan."""

from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(__file__).with_name("vps_pilot_dry_run.py")
TEMPLATE_PATH = Path(__file__).parent / "templates" / "vps-pilot-plan.template.json"
BOARD_SLUG = "super-lily"
BOUNDED_VALUE = 2
DRY_RUN_COMMAND_ID = "dry-run-dispatch"
BOARD_OPTION = "--board"
MAXIMUM_OPTION = "--max"


def load_dry_run_module():
    if not MODULE_PATH.is_file():
        raise AssertionError(
            "T-031-T1: vps_pilot_dry_run.py must generate an inert pilot plan"
        )
    spec = importlib.util.spec_from_file_location("vps_pilot_dry_run", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class VpsPilotDryRunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_dry_run_module()
        cls.plan = cls.module.generate_pilot_dry_run(BOARD_SLUG)

    def test_t031_t2_uses_bounded_kanban_and_delegation_configuration(self) -> None:
        """T-031-T2/AC-170..173: all operational limits are fail-closed."""

        configuration = self.plan["configuration"]
        self.assertEqual(
            {
                "max_spawn": BOUNDED_VALUE,
                "max_in_progress": BOUNDED_VALUE,
                "max_in_progress_per_profile": BOUNDED_VALUE,
                "failure_limit": BOUNDED_VALUE,
            },
            configuration["kanban"],
        )
        self.assertEqual({"max_spawn_depth": 1}, configuration["delegation"])
        self.assertIs(False, configuration["subagent_auto_approve"])

    def test_t031_t3_plan_ends_with_configuration_verification(self) -> None:
        """T-031-T3/AC-174: verification is the final ordered command."""

        commands = self.plan["commands"]
        self.assertEqual(
            list(range(1, len(commands) + 1)),
            [item["order"] for item in commands],
        )
        self.assertEqual("verify-configuration", commands[-1]["id"])
        self.assertEqual(["hermes", "config", "check"], commands[-1]["argv"])

    def test_t031_t4_prepares_super_lily_dry_run_without_dispatch(self) -> None:
        """T-031-T4/AC-183: Super Lily is bounded to two without dispatch."""

        dry_run = self.plan["dry_run"]
        self.assertEqual(BOARD_SLUG, dry_run["board"])
        self.assertEqual(BOUNDED_VALUE, dry_run["max_workers"])
        self.assertIs(True, dry_run["requested"])
        self.assertIs(False, dry_run["dispatched"])
        dispatch = next(
            item
            for item in self.plan["commands"]
            if item["id"] == DRY_RUN_COMMAND_ID
        )
        self.assertIn("--dry-run", dispatch["argv"])
        self.assertEqual(
            str(BOUNDED_VALUE),
            dispatch["argv"][dispatch["argv"].index(MAXIMUM_OPTION) + 1],
        )

    def test_t031_t5_module_is_pure_and_every_command_is_inert(self) -> None:
        """T-031-T5: no process or network primitive exists in the generator."""

        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertTrue(
            imported.isdisjoint(
                {"subprocess", "socket", "urllib", "http", "requests", "paramiko"}
            )
        )
        self.assertTrue(
            all(item["execute"] is False for item in self.plan["commands"])
        )
        self.assertEqual(
            {"performed": False, "external_access": False},
            self.plan["execution"],
        )

    def test_t031_t6_commands_name_board_and_expose_no_sensitive_value(self) -> None:
        """T-031-T6: argv are ordered, board-explicit and safe to persist."""

        dispatch = next(
            item
            for item in self.plan["commands"]
            if item["id"] == DRY_RUN_COMMAND_ID
        )
        self.assertEqual(
            BOARD_SLUG,
            dispatch["argv"][dispatch["argv"].index(BOARD_OPTION) + 1],
        )
        encoded = json.dumps(self.plan, sort_keys=True)
        for forbidden in (
            "/Users/",
            "/home/",
            "ghp_",
            "github_pat_",
            "token=",
            "@example",
        ):
            self.assertNotIn(forbidden, encoded)
        self.assertEqual("redacted", self.plan["evidence"])

    def test_t031_template_is_validated_before_materialization(self) -> None:
        """T-031-T2..T6: the versioned JSON template has the validated shape."""

        template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
        self.module.validate_template(template)
        invalid = dict(template)
        invalid["schema_version"] = 99
        with self.assertRaises(ValueError):
            self.module.validate_template(invalid)

    def test_t031_rejects_an_unsafe_board_slug_before_materialization(self) -> None:
        """T-031-T6: board input cannot become a shell fragment or local path."""

        for board in ("Super-Lily", "super lily", "../super-lily", "super-lily;id"):
            with self.subTest(board=board), self.assertRaises(ValueError):
                self.module.generate_pilot_dry_run(board)

    def test_t031_rejects_extra_or_sensitive_template_fields(self) -> None:
        """T-031-T5/T-031-T6: templates are closed and persist no secrets."""

        template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
        template["token"] = "ghp_sensitive"
        with self.assertRaises(ValueError):
            self.module.validate_template(template)


if __name__ == "__main__":
    unittest.main()
