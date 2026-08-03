#!/usr/bin/env python3
"""Behavioral tests for parallel ``/sdd-build`` admission through Hermes."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("sdd_build_orchestrator.py")
CONTRACT_PATH = Path(__file__).with_name("build-orchestrator-contract.md")
FEATURE_ID = "parallel-feature"
OWNER = "owner-t010"
SESSION_ID = "session-t010"
PARENT_CARD_ID = "card-parent"


def load_orchestrator():
    """Load production lazily so the absent module is the intentional RED."""

    if not MODULE_PATH.is_file():
        raise AssertionError(
            "T-010-T1: sdd_build_orchestrator.py must implement parallel admission"
        )
    spec = importlib.util.spec_from_file_location("sdd_build_orchestrator", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def task(
    task_id: str,
    *,
    phase: str = "pending",
    status: str = "pending",
    dependencies: list[str] | None = None,
    scope: list[str] | None = None,
) -> dict[str, object]:
    return {
        "phase": phase,
        "status": status,
        "dependencies": [] if dependencies is None else dependencies,
        "test_ids": [f"{task_id}-T1"],
        "files_in_scope": [f"work/{task_id.lower()}.txt"] if scope is None else scope,
        "kanban_id": None,
        "issue": None,
        "branch": None,
        "pr": None,
        "red_at": "proof" if phase == "done" else None,
        "red_test_signature": "FixtureTest.test_done" if phase == "done" else None,
        "red_failure_excerpt": "expected failure" if phase == "done" else None,
        "green_at": "proof" if phase == "done" else None,
    }


def runtime_state() -> dict[str, object]:
    return {
        "schema_version": 2,
        "feature_id": FEATURE_ID,
        "mode": "parallel",
        "project": "parallel-project",
        "board": "parallel-board",
        "max_workers": 2,
        "revision": 7,
        "active_task": None,
        "tasks": {
            "T-009": task("T-009", phase="done", status="done"),
            "T-010": task(
                "T-010",
                phase="done",
                status="done",
                dependencies=["T-009"],
            ),
            "T-011": task("T-011", dependencies=["T-010"]),
            "T-012": task("T-012", status="ready", dependencies=["T-010"]),
            "T-013": task("T-013", dependencies=["T-011"]),
            "T-014": task(
                "T-014",
                dependencies=["T-010", "T-011"],
                scope=["work/t-011.txt"],
            ),
            "T-015": task("T-015", dependencies=["T-010"]),
        },
    }


def create_repository(temporary: str, state: dict[str, object]) -> Path:
    root = Path(temporary) / "repository"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "t@example.test"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "T"], check=True)
    for task_state in state["tasks"].values():
        assert isinstance(task_state, dict)
        for relative in task_state["files_in_scope"]:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(relative, encoding="utf-8")
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
    return root


class RecordingKanban:
    def __init__(self, *, failing_task: str | None = None) -> None:
        self.failing_task = failing_task
        self.cards: list[dict[str, object]] = []
        self.dispatches: list[dict[str, str]] = []
        self.statuses: list[dict[str, str]] = []

    def create_card(self, **metadata: object) -> str:
        self.cards.append(copy.deepcopy(metadata))
        return f"card-{metadata['task_id'].lower()}"

    def dispatch(self, *, card_id: str, lease_id: str) -> None:
        task_id = card_id.removeprefix("card-").upper()
        if task_id == self.failing_task:
            raise RuntimeError("injected dispatch failure")
        self.dispatches.append({"card_id": card_id, "lease_id": lease_id})

    def set_status(self, *, card_id: str, status: str) -> None:
        self.statuses.append({"card_id": card_id, "status": status})


def admit(
    root: Path,
    state: dict[str, object],
    kanban: RecordingKanban,
    *,
    argv: list[str] | None = None,
    merged_tasks: set[str] | None = None,
) -> dict[str, object]:
    orchestrator = load_orchestrator()
    return orchestrator.admit_parallel_wave(
        repo_root=root,
        argv=[FEATURE_ID, "--parallel"] if argv is None else argv,
        state=state,
        kanban=kanban,
        parent_card_id=PARENT_CARD_ID,
        owner=OWNER,
        session_id=SESSION_ID,
        merged_tasks={"T-009", "T-010"} if merged_tasks is None else merged_tasks,
    )


class ParallelBuildOrchestratorTest(unittest.TestCase):
    def test_t010_t1_parallel_cli_requires_structured_parallel_arguments(self) -> None:
        """T-010-T1/AC-020: --parallel is explicit and options are structured."""

        orchestrator = load_orchestrator()
        self.assertEqual(
            {"feature_id": FEATURE_ID, "max_workers": 2},
            orchestrator.parse_parallel_arguments([FEATURE_ID, "--parallel"]),
        )
        with self.assertRaises(orchestrator.BuildOrchestratorError):
            orchestrator.parse_parallel_arguments([FEATURE_ID])
        with self.assertRaises(orchestrator.BuildOrchestratorError):
            orchestrator.parse_parallel_arguments(
                f"{FEATURE_ID} --parallel --max-workers 2"
            )

    def test_t010_t2_worker_bounds_default_and_cap_are_two(self) -> None:
        """T-010-T2/AC-021/AC-022/AC-023: only one or two workers are valid."""

        orchestrator = load_orchestrator()
        for maximum in (1, 2):
            parsed = orchestrator.parse_parallel_arguments(
                [FEATURE_ID, "--parallel", "--max-workers", str(maximum)]
            )
            self.assertEqual(maximum, parsed["max_workers"])
        for invalid in ("0", "3", "two"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(orchestrator.BuildOrchestratorError):
                    orchestrator.parse_parallel_arguments(
                        [FEATURE_ID, "--parallel", "--max-workers", invalid]
                    )

    def test_t010_t3_admits_only_ready_tasks_with_merged_dependencies(self) -> None:
        """T-010-T3/AC-027/AC-128: dependencies must be done and merged."""

        state = runtime_state()
        with tempfile.TemporaryDirectory(prefix="sdd-parallel-admission-") as temporary:
            root = create_repository(temporary, state)
            kanban = RecordingKanban()
            result = admit(root, state, kanban)

        self.assertEqual(["T-011", "T-012", "T-015"], result["admitted_task_ids"])
        self.assertNotIn("T-013", result["admitted_task_ids"])

    def test_t010_t4_disjoint_scopes_share_wave_and_conflicts_serialize(self) -> None:
        """T-010-T4/AC-028/AC-029: overlapping concrete paths serialize."""

        state = runtime_state()
        with tempfile.TemporaryDirectory(prefix="sdd-parallel-scope-") as temporary:
            root = create_repository(temporary, state)
            result = admit(root, state, RecordingKanban())

        self.assertIn("T-011", result["admitted_task_ids"])
        self.assertIn("T-012", result["admitted_task_ids"])
        self.assertIn("T-014", result["serialized_task_ids"])

    def test_t010_t5_cards_carry_complete_durable_metadata(self) -> None:
        """T-010-T5/AC-031/AC-129/AC-130/AC-260: cards are fully identified."""

        state = runtime_state()
        with tempfile.TemporaryDirectory(prefix="sdd-parallel-card-") as temporary:
            root = create_repository(temporary, state)
            kanban = RecordingKanban()
            admit(root, state, kanban)

        first = kanban.cards[0]
        self.assertEqual("parallel-project", first["project"])
        self.assertEqual("parallel-board", first["board"])
        self.assertEqual(PARENT_CARD_ID, first["parent_card_id"])
        self.assertEqual(f"{FEATURE_ID}:T-011", first["idempotency_key"])
        self.assertEqual("sdd-build", first["skill"])
        self.assertEqual("45m", first["max_runtime"])
        self.assertEqual(2, first["retries"])
        self.assertEqual(f"sdd/{FEATURE_ID}/t-011", first["branch"])

    def test_t010_t6_all_cards_exist_but_only_two_writer_leases_are_active(self) -> None:
        """T-010-T6/AC-131: queued cards do not mutate beyond two writers."""

        state = runtime_state()
        with tempfile.TemporaryDirectory(prefix="sdd-parallel-capacity-") as temporary:
            root = create_repository(temporary, state)
            kanban = RecordingKanban()
            result = admit(root, state, kanban)
            leases_path = root / ".git" / "sdd-runtime" / "leases.json"
            active_leases = json.loads(leases_path.read_text(encoding="utf-8"))["leases"]

        self.assertEqual(3, len(kanban.cards))
        self.assertEqual(2, len(kanban.dispatches))
        self.assertEqual(2, len(active_leases))
        self.assertEqual(["T-015"], result["queued_task_ids"])

    def test_t010_t7_refuses_until_t009_is_observed_merged(self) -> None:
        """T-010-T7/AC-128: the mono-task contribution is a hard barrier."""

        state = runtime_state()
        with tempfile.TemporaryDirectory(prefix="sdd-parallel-barrier-") as temporary:
            root = create_repository(temporary, state)
            with self.assertRaisesRegex(Exception, "T-009.*merged"):
                admit(root, state, RecordingKanban(), merged_tasks={"T-010"})

    def test_t010_t8_kanban_is_the_only_dispatch_surface(self) -> None:
        """T-010-T8/AC-132/AC-236: admission dispatches only through Kanban."""

        state = runtime_state()
        with tempfile.TemporaryDirectory(prefix="sdd-parallel-authority-") as temporary:
            root = create_repository(temporary, state)
            kanban = RecordingKanban()
            admit(root, state, kanban)

        self.assertEqual(2, len(kanban.dispatches))
        source = MODULE_PATH.read_text(encoding="utf-8")
        contract = CONTRACT_PATH.read_text(encoding="utf-8")
        self.assertNotIn("delegate_task", source)
        self.assertNotIn("ThreadPool", source)
        self.assertNotIn("asyncio", source)
        self.assertIn("Kanban Hermes est l'unique surface de dispatch", contract)
        self.assertIn("`max-runtime=45m`", contract)
        self.assertIn("deux retries", contract)

    def test_t010_t9_dispatch_failure_does_not_revoke_another_job(self) -> None:
        """T-010-T9/AC-133: one failed card leaves the other writer progressing."""

        state = runtime_state()
        with tempfile.TemporaryDirectory(prefix="sdd-parallel-failure-") as temporary:
            root = create_repository(temporary, state)
            kanban = RecordingKanban(failing_task="T-011")
            result = admit(root, state, kanban)
            leases_path = root / ".git" / "sdd-runtime" / "leases.json"
            active_leases = json.loads(leases_path.read_text(encoding="utf-8"))["leases"]

        self.assertEqual(["T-011"], result["failed_task_ids"])
        self.assertEqual(2, len(active_leases))
        self.assertTrue(any(call["card_id"] == "card-t-012" for call in kanban.dispatches))
        self.assertEqual(
            [{"card_id": "card-t-011", "status": "failed"}],
            kanban.statuses,
        )


if __name__ == "__main__":
    unittest.main()
