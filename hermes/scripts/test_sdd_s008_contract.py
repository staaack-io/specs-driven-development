#!/usr/bin/env python3
"""Executable local audit for S-008 and the Epic's 286 acceptance criteria."""

from __future__ import annotations

import ast
import json
from pathlib import Path, PurePosixPath
import unittest


ROOT = Path(__file__).resolve().parents[2]
FEATURE = ROOT / ".specs" / "2026-07-31-hermes-parallel-sdd"
STATE = FEATURE / ".tdd-state.json"
RUNBOOK = ROOT / "hermes/operations/vps-pilot-runbook.md"
PUBLIC_DOCUMENTS = (
    ROOT / "hermes/README.md",
    ROOT / "docs/codex-migration.md",
)
LOCAL_TASKS = ("T-030", "T-031")
EXTERNAL_TASKS = tuple(f"T-{number:03d}" for number in range(33, 39))
FORBIDDEN_AUDIT_IMPORTS = {
    "http",
    "paramiko",
    "requests",
    "socket",
    "subprocess",
    "urllib",
}


def ac_ids(*numbers: int) -> set[str]:
    return {f"AC-{number:03d}" for number in numbers}


def ac_range(first: int, last: int) -> set[str]:
    return ac_ids(*range(first, last + 1))


S008_PRODUCER_GROUPS = (
    (
        "T-030",
        ac_ids(
            163,
            169,
            *range(175, 178),
            181,
            187,
            *range(190, 195),
            *range(266, 269),
        ),
    ),
    ("T-031", ac_ids(*range(170, 175), 183)),
    ("T-032", ac_ids(232)),
    ("T-033", ac_ids(161, 162, *range(164, 169), 240, 264)),
    ("T-034", ac_ids(8, *range(178, 181), 182, 238, 239, 241, 242)),
    ("T-035", ac_ids(*range(184, 187), 229, 230, 265)),
    ("T-036", ac_ids(188, 189)),
    ("T-037", ac_ids(*range(220, 225), *range(269, 272))),
    ("T-038", ac_ids(160)),
)


def primary_producer_occurrences() -> list[tuple[str, str]]:
    return [
        (criterion, producer)
        for producer, criteria in S008_PRODUCER_GROUPS
        for criterion in criteria
    ]


EPIC_SLICES = {
    "S-001": ac_ids(9, 10)
    | ac_range(81, 100)
    | ac_ids(195, 237, 250, 251)
    | ac_range(272, 275)
    | ac_range(281, 286),
    "S-002": ac_range(1, 7)
    | ac_ids(11, 12, 25, 26)
    | ac_range(48, 80)
    | ac_range(101, 123)
    | ac_range(243, 249)
    | ac_range(252, 256)
    | ac_range(276, 280),
    "S-003": ac_ids(13)
    | ac_range(19, 24)
    | ac_range(27, 47)
    | ac_range(124, 138)
    | ac_ids(231, 233, 234, 236)
    | ac_range(257, 260),
    "S-004": ac_ids(14, 139),
    "S-005": ac_ids(15, 16)
    | ac_range(140, 147)
    | ac_range(196, 217),
    "S-006": ac_ids(17, 18)
    | ac_range(148, 154)
    | ac_ids(235)
    | ac_range(261, 263),
    "S-007": ac_ids(155, 156, 157, 158, 159, 218, 219, 225, 226, 227, 228),
    "S-008": {
        criterion for criterion, _producer in primary_producer_occurrences()
    },
}


def loaded_state() -> dict[str, object]:
    return json.loads(STATE.read_text(encoding="utf-8"))


class SddS008ContractTest(unittest.TestCase):
    def test_t032_t1_contract_and_runbook_are_installed(self) -> None:
        self.assertTrue(RUNBOOK.is_file(), str(RUNBOOK.relative_to(ROOT)))
        text = RUNBOOK.read_text(encoding="utf-8")
        for marker in ("S-008", "57/57", "286/286", "T-032-T1", "T-032-T7"):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_t032_t2_s008_has_exactly_57_unique_primary_producers(self) -> None:
        occurrences = primary_producer_occurrences()
        producer_by_ac = dict(occurrences)
        expected = ac_ids(
            8,
            *range(160, 195),
            *range(220, 225),
            229,
            230,
            232,
            *range(238, 243),
            *range(264, 272),
        )
        self.assertEqual(expected, set(producer_by_ac))
        self.assertEqual(57, len(occurrences))
        self.assertEqual(len(occurrences), len(producer_by_ac))

    def test_t032_t3_eight_slices_partition_all_286_epic_criteria(self) -> None:
        occurrences = [criterion for criteria in EPIC_SLICES.values() for criterion in criteria]
        self.assertEqual(8, len(EPIC_SLICES))
        self.assertEqual(ac_range(1, 286), set(occurrences))
        self.assertEqual(286, len(occurrences), "a primary AC must occur in one slice")

    def test_t032_t4_dag_has_two_local_writers_then_external_sequence(self) -> None:
        tasks = loaded_state()["tasks"]
        self.assertEqual(["T-029"], tasks["T-030"]["dependencies"])
        self.assertEqual(["T-029"], tasks["T-031"]["dependencies"])
        self.assertEqual(["T-030", "T-031"], tasks["T-032"]["dependencies"])
        previous = "T-032"
        for task_id in EXTERNAL_TASKS:
            with self.subTest(task_id=task_id):
                self.assertEqual([previous], tasks[task_id]["dependencies"])
                self.assertEqual("pending", tasks[task_id]["phase"])
                self.assertEqual("pending", tasks[task_id]["status"])
                self.assertEqual("external-blocked", tasks[task_id]["admission"])
            previous = task_id

    def test_t032_t5_vps_update_requires_release_gate_and_explicit_go(self) -> None:
        tasks = loaded_state()["tasks"]
        preconditions = set(tasks["T-033"]["external_preconditions"])
        self.assertTrue(
            {
                "profile-0.9.0-merged",
                "profile-0.9.0-published",
                "publication-gate-green",
                "explicit-go",
            }.issubset(preconditions)
        )
        text = RUNBOOK.read_text(encoding="utf-8")
        for marker in ("0.9.0 fusionnée", "0.9.0 publiée", "gate verte", "go explicite"):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_t032_t6_local_scopes_are_literal_relative_and_disjoint(self) -> None:
        tasks = loaded_state()["tasks"]
        scopes = []
        for task_id in LOCAL_TASKS:
            paths = set(tasks[task_id]["files_in_scope"])
            self.assertTrue(paths)
            for path in paths:
                with self.subTest(task_id=task_id, path=path):
                    self.assertFalse(PurePosixPath(path).is_absolute())
                    self.assertFalse({"*", "?", "[", "]"}.intersection(path))
                    self.assertNotIn("..", PurePosixPath(path).parts)
            scopes.append(paths)
        self.assertTrue(scopes[0].isdisjoint(scopes[1]))

    def test_t032_t7_audit_is_inert_and_metadata_is_reconciled(self) -> None:
        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"), filename=__file__)
        imported = {
            alias.name.split(".", maxsplit=1)[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertTrue(FORBIDDEN_AUDIT_IMPORTS.isdisjoint(imported))

        tasks = loaded_state()["tasks"]
        expected_metadata = {
            "T-016": ("pending", None, None, None),
            "T-027": ("done", 112, "agent/build-t027-e2e-full-flow", 113),
            "T-030": ("done", 119, "agent/build-t030-vps-policy", 121),
            "T-031": ("done", 118, "agent/build-t031-vps-dry-run", 120),
        }
        for task_id, expected in expected_metadata.items():
            task = tasks[task_id]
            actual = (task["status"], task["issue"], task["branch"], task["pr"])
            with self.subTest(task_id=task_id):
                self.assertEqual(expected, actual)

        safety_text = "\n".join(
            document.read_text(encoding="utf-8")
            for document in (RUNBOOK, *PUBLIC_DOCUMENTS)
        )
        for marker in (
            "aucun reviewer humain",
            "aucune fusion",
            "aucun SSH",
            "aucun gateway",
            "aucun déploiement",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, safety_text)


if __name__ == "__main__":
    unittest.main()
