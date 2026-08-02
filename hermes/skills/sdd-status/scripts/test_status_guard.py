#!/usr/bin/env python3

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("status_guard.py")
TASK_ID = "T-005"
ISSUE = 63
BRANCH = "sdd/hermes-parallel-sdd/t-005-status"
PULL_REQUEST = 64
CHECKS = "PASS"
REVIEW = "approve"
BLOCKING = "—"
NEXT_ACTION = "/sdd-build 2026-07-31-hermes-parallel-sdd T-005"


def load_guard():
    module_spec = importlib.util.spec_from_file_location("status_guard", SCRIPT)
    if module_spec is None or module_spec.loader is None:
        raise AssertionError("status_guard.py cannot be loaded")
    guard = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(guard)
    return guard


def repository_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(file for file in root.rglob("*") if file.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


class StatusGuardTest(unittest.TestCase):
    def test_v2_task_local_view_exposes_all_proven_fields(self) -> None:
        """T-005-T1 / AC-243, AC-244, AC-245, AC-246, AC-247, AC-248, AC-249."""
        if not SCRIPT.is_file():
            self.fail(
                "T-005-T1: task-local status view is absent because "
                "status_guard.py does not exist"
            )

        module_spec = importlib.util.spec_from_file_location("status_guard", SCRIPT)
        self.assertIsNotNone(module_spec)
        self.assertIsNotNone(module_spec.loader)
        guard = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(guard)
        state = {
            "schema_version": 2,
            "tasks": {
                TASK_ID: {
                    "issue": ISSUE,
                    "branch": BRANCH,
                    "pr": PULL_REQUEST,
                    "checks": CHECKS,
                    "review": REVIEW,
                    "blocking": BLOCKING,
                    "next_action": NEXT_ACTION,
                }
            },
        }

        self.assertEqual(
            [
                {
                    "task_id": TASK_ID,
                    "issue": ISSUE,
                    "branch": BRANCH,
                    "pr": PULL_REQUEST,
                    "checks": CHECKS,
                    "review": REVIEW,
                    "blocking": BLOCKING,
                    "next_action": NEXT_ACTION,
                }
            ],
            guard.task_local_rows(state),
        )

    def test_v2_complete_state_renders_every_task_in_stable_order(self) -> None:
        """T-005-T2 / AC-243, AC-244, AC-245, AC-246, AC-247, AC-248, AC-249."""
        guard = load_guard()
        state = {
            "schema_version": 2,
            "tasks": {
                "T-010": {
                    "issue": 110,
                    "branch": "sdd/feature/t-010",
                    "pr": 210,
                    "checks": "PENDING",
                    "review": "pending",
                    "blocking": "checks",
                    "next_action": "wait for checks",
                },
                "T-002": {
                    "issue": 102,
                    "branch": "sdd/feature/t-002",
                    "pr": 202,
                    "checks": "PASS",
                    "review": "approve",
                    "blocking": "—",
                    "next_action": "/sdd-build feature T-002",
                },
            },
        }

        rows = guard.task_local_rows(state)

        self.assertEqual(["T-002", "T-010"], [row["task_id"] for row in rows])
        self.assertEqual(
            state["tasks"]["T-002"],
            {key: rows[0][key] for key in state["tasks"]["T-002"]},
        )
        self.assertEqual(
            state["tasks"]["T-010"],
            {key: rows[1][key] for key in state["tasks"]["T-010"]},
        )

    def test_v1_missing_task_local_fields_render_as_em_dash(self) -> None:
        """T-005-T3 / AC-243, AC-244, AC-245, AC-246, AC-247, AC-248, AC-249."""
        guard = load_guard()
        state = {
            "schema_version": 1,
            "tasks": {TASK_ID: {"phase": "red", "files_in_scope": ["file.py"]}},
        }

        [row] = guard.task_local_rows(state)

        self.assertEqual(TASK_ID, row["task_id"])
        self.assertEqual(
            {field: "—" for field in guard.TASK_LOCAL_FIELDS},
            {field: row[field] for field in guard.TASK_LOCAL_FIELDS},
        )

    def test_reading_task_local_rows_does_not_change_repository_fingerprint(self) -> None:
        """T-005-T4 / AC-243, AC-244, AC-245, AC-246, AC-247, AC-248, AC-249."""
        guard = load_guard()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_path = root / ".specs" / "feature" / ".tdd-state.json"
            state_path.parent.mkdir(parents=True)
            state = {"schema_version": 2, "tasks": {TASK_ID: {"issue": ISSUE}}}
            state_path.write_text(
                json.dumps(state),
                encoding="utf-8",
            )
            (root / "tracked.txt").write_text("unchanged\n", encoding="utf-8")
            before = repository_fingerprint(root)

            rows = guard.task_local_rows_from_file(state_path)

            self.assertEqual(ISSUE, rows[0]["issue"])
            self.assertEqual(before, repository_fingerprint(root))

    def test_next_action_is_read_from_evidence_not_inferred(self) -> None:
        """T-005-T5 / AC-249."""
        guard = load_guard()
        proven_next_action = "wait for the requested review"
        state = {
            "schema_version": 2,
            "tasks": {
                TASK_ID: {
                    "phase": "done",
                    "status": "blocked",
                    "blocking": "review requested",
                    "next_action": proven_next_action,
                },
                "T-006": {
                    "phase": "red",
                    "status": "in_progress",
                    "blocking": "—",
                },
            },
        }

        rows = {row["task_id"]: row for row in guard.task_local_rows(state)}

        self.assertEqual(proven_next_action, rows[TASK_ID]["next_action"])
        self.assertEqual("—", rows["T-006"]["next_action"])


if __name__ == "__main__":
    unittest.main()
