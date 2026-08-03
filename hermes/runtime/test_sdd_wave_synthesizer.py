#!/usr/bin/env python3
"""Behavioral tests for the single-writer SDD wave synthesizer."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("sdd_wave_synthesizer.py")
RUNTIME_PATH = Path(__file__).with_name("sdd_runtime_guard.py")
FEATURE_ID = "wave-feature"
WAVE_ID = "wave-001"
FAN_IN_PR = 312


def load_module(path: Path, name: str):
    if not path.is_file():
        raise AssertionError(f"T-012-T1: {path.name} must implement wave synthesis")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_synthesizer():
    return load_module(MODULE_PATH, "sdd_wave_synthesizer")


class RecordingKanban:
    def __init__(self) -> None:
        self.card_statuses: list[dict[str, str]] = []
        self.wave_statuses: list[dict[str, str]] = []

    def set_status(self, *, card_id: str, status: str) -> None:
        self.card_statuses.append({"card_id": card_id, "status": status})

    def set_wave_status(self, *, wave_id: str, status: str) -> None:
        self.wave_statuses.append({"wave_id": wave_id, "status": status})


class RecordingGitHub:
    def __init__(self) -> None:
        self.merged: set[int] = set()
        self.fan_in_calls: list[dict[str, object]] = []

    def is_merged(self, *, pr: int) -> bool:
        return pr in self.merged

    def ensure_fan_in_pull_request(
        self,
        *,
        wave_id: str,
        branch: str,
        idempotency_key: str,
        draft: bool,
    ) -> int:
        self.fan_in_calls.append(
            {
                "wave_id": wave_id,
                "branch": branch,
                "idempotency_key": idempotency_key,
                "draft": draft,
            }
        )
        return FAN_IN_PR


class RecordingHumanGate:
    def __init__(self, approved: set[str] | None = None) -> None:
        self.approved = set() if approved is None else approved

    def explicitly_approved(self, *, task_id: str, pr: int) -> bool:
        return task_id in self.approved


class RecordingStateStore:
    def __init__(self) -> None:
        self.statuses: list[dict[str, str]] = []
        self.fan_in_pr: int | None = None

    def set_status(self, *, task_id: str, status: str) -> None:
        self.statuses.append({"task_id": task_id, "status": status})

    def fan_in_pr_for(self, *, wave_id: str) -> int | None:
        return self.fan_in_pr

    def record_fan_in_pr(self, *, wave_id: str, pr: int) -> None:
        self.fan_in_pr = pr


class RecordingRuntime:
    def __init__(self) -> None:
        self.journals: list[str] = []
        self.fan_ins: list[dict[str, object]] = []

    def verify_job_journal(
        self, repo_root: Path | str, *, feature_id: str, task_id: str
    ) -> int:
        self.journals.append(task_id)
        return 4

    def transactional_fan_in(self, repo_root: Path | str, **arguments: object):
        self.fan_ins.append(arguments)
        return {"committed": True, "idempotent": False}


def job(task_id: str, *, status: str = "done") -> dict[str, object]:
    return {
        "task_id": task_id,
        "card_id": f"card-{task_id.lower()}",
        "pr": 200 + int(task_id.removeprefix("T-")),
        "pr_ready": True,
        "checks_green": True,
        "review_approved": True,
        "status": status,
    }


def wave(*, second_status: str = "done") -> dict[str, object]:
    return {
        "wave_id": WAVE_ID,
        "feature_id": FEATURE_ID,
        "jobs": [job("T-010"), job("T-011", status=second_status)],
    }


def shared_artifacts() -> dict[str, bytes]:
    return {
        f".specs/{FEATURE_ID}/04-tasks.md": b"tasks\n",
        f".specs/{FEATURE_ID}/.tdd-state.json": b"{}\n",
        f".specs/{FEATURE_ID}/05-implementation-log.md": b"log\n",
    }


class WaveSynthesizerTest(unittest.TestCase):
    def test_t012_t1_completed_wave_has_one_synthesis_surface(self) -> None:
        """T-012-T1/AC-045: the synthesizer exposes one wave entry point."""

        synthesizer = load_synthesizer()
        self.assertTrue(callable(synthesizer.synthesize_wave))

    def test_t012_t2_green_approved_pr_only_moves_to_awaiting_go(self) -> None:
        """T-012-T2/AC-046: technical gates never imply human go."""

        synthesizer = load_synthesizer()
        kanban = RecordingKanban()
        result = synthesizer.observe_job_gate(job=job("T-010"), kanban=kanban)

        self.assertEqual("awaiting_go", result["status"])
        self.assertEqual(
            [{"card_id": "card-t-010", "status": "awaiting_go"}],
            kanban.card_statuses,
        )

    def test_t012_t3_only_explicitly_approved_observed_merge_becomes_done(self) -> None:
        """T-012-T3/AC-047: go and observed human merge are both required."""

        synthesizer = load_synthesizer()
        selected = job("T-010")
        github = RecordingGitHub()
        kanban = RecordingKanban()
        store = RecordingStateStore()
        gate = RecordingHumanGate()

        self.assertFalse(
            synthesizer.observe_human_merge(
                job=selected,
                human_gate=gate,
                github=github,
                kanban=kanban,
                state_store=store,
            )
        )
        gate.approved.add("T-010")
        self.assertFalse(
            synthesizer.observe_human_merge(
                job=selected,
                human_gate=gate,
                github=github,
                kanban=kanban,
                state_store=store,
            )
        )
        github.merged.add(selected["pr"])
        self.assertTrue(
            synthesizer.observe_human_merge(
                job=selected,
                human_gate=gate,
                github=github,
                kanban=kanban,
                state_store=store,
            )
        )
        self.assertEqual([{"task_id": "T-010", "status": "done"}], store.statuses)

    def test_t012_t4_all_cards_done_and_journals_verified_before_fan_in(self) -> None:
        """T-012-T4/AC-134: incomplete waves and invalid journals block fan-in."""

        synthesizer = load_synthesizer()
        with self.assertRaises(synthesizer.WaveSynthesisError):
            synthesizer.synthesize_wave(
                repo_root=".",
                wave=wave(second_status="awaiting_go"),
                artifacts={"x": b"x"},
                expected_tokens={"x": "token"},
                runtime=RecordingRuntime(),
                github=RecordingGitHub(),
                kanban=RecordingKanban(),
                state_store=RecordingStateStore(),
            )

    def test_t012_t5_only_synthesizer_writes_three_shared_artifacts(self) -> None:
        """T-012-T5/AC-135: runtime fan-in receives the sole writer and targets."""

        synthesizer = load_synthesizer()
        runtime = RecordingRuntime()
        artifacts = shared_artifacts()
        synthesizer.synthesize_wave(
            repo_root=".",
            wave=wave(),
            artifacts=artifacts,
            expected_tokens={path: "token" for path in artifacts},
            runtime=runtime,
            github=RecordingGitHub(),
            kanban=RecordingKanban(),
            state_store=RecordingStateStore(),
        )

        self.assertEqual("synthesizer", runtime.fan_ins[0]["actor"])
        self.assertEqual(set(artifacts), set(runtime.fan_ins[0]["artifacts"]))
        self.assertEqual(["T-010", "T-011"], runtime.journals)

    def test_t012_t6_fan_in_pr_is_idempotent_and_never_merged(self) -> None:
        """T-012-T6/AC-136: one fan-in PR is created without a merge call."""

        synthesizer = load_synthesizer()
        github = RecordingGitHub()
        store = RecordingStateStore()
        artifacts = shared_artifacts()
        arguments = {
            "repo_root": ".",
            "wave": wave(),
            "artifacts": artifacts,
            "expected_tokens": {path: "token" for path in artifacts},
            "runtime": RecordingRuntime(),
            "github": github,
            "kanban": RecordingKanban(),
            "state_store": store,
        }
        first = synthesizer.synthesize_wave(**arguments)
        second = synthesizer.synthesize_wave(**arguments)

        self.assertEqual(FAN_IN_PR, first["pr"])
        self.assertEqual(first["pr"], second["pr"])
        self.assertEqual(1, len(github.fan_in_calls))
        self.assertNotIn("merge_pull_request", MODULE_PATH.read_text(encoding="utf-8"))

    def test_t012_t7_next_wave_waits_for_observed_fan_in_merge(self) -> None:
        """T-012-T7/AC-137: the next wave remains blocked before fan-in merge."""

        synthesizer = load_synthesizer()
        github = RecordingGitHub()
        store = RecordingStateStore()
        store.fan_in_pr = FAN_IN_PR

        self.assertFalse(
            synthesizer.next_wave_admissible(
                wave_id=WAVE_ID,
                github=github,
                state_store=store,
            )
        )
        github.merged.add(FAN_IN_PR)
        self.assertTrue(
            synthesizer.next_wave_admissible(
                wave_id=WAVE_ID,
                github=github,
                state_store=store,
            )
        )

    def test_t012_t8_runtime_recovery_returns_only_complete_old_or_new_set(self) -> None:
        """T-012-T8/AC-231: crash recovery delegates to atomic runtime fan-in."""

        synthesizer = load_synthesizer()
        runtime = load_module(RUNTIME_PATH, "sdd_wave_runtime_guard")
        with tempfile.TemporaryDirectory(prefix="sdd-wave-recovery-") as temporary:
            root = self._create_repository(Path(temporary))
            feature = root / ".specs" / FEATURE_ID
            paths = ["04-tasks.md", ".tdd-state.json", "05-implementation-log.md"]
            next_state = json.loads((feature / ".tdd-state.json").read_text())
            next_state["revision"] = 1
            artifacts = {}
            for name in paths:
                path = f".specs/{FEATURE_ID}/{name}"
                if name == ".tdd-state.json":
                    artifacts[path] = json.dumps(next_state).encode("utf-8")
                else:
                    artifacts[path] = (feature / name).read_bytes() + b"next\n"
            expected = {
                path: runtime.token_for((root / path).read_bytes()) for path in artifacts
            }
            previous = {path: (root / path).read_bytes() for path in artifacts}
            with self.assertRaises(runtime.InjectedCrash):
                synthesizer.commit_fan_in(
                    repo_root=root,
                    feature_id=FEATURE_ID,
                    transaction_id="wave-crash",
                    artifacts=artifacts,
                    expected_tokens=expected,
                    runtime=runtime,
                    crash_point="before-marker",
                )
            runtime.recover_fan_in(
                root,
                feature_id=FEATURE_ID,
                transaction_id="wave-crash",
            )
            self.assertEqual(previous, {path: (root / path).read_bytes() for path in artifacts})
            with self.assertRaises(runtime.InjectedCrash):
                synthesizer.commit_fan_in(
                    repo_root=root,
                    feature_id=FEATURE_ID,
                    transaction_id="wave-crash-after",
                    artifacts=artifacts,
                    expected_tokens=expected,
                    runtime=runtime,
                    crash_point="after-marker",
                )
            runtime.recover_fan_in(
                root,
                feature_id=FEATURE_ID,
                transaction_id="wave-crash-after",
            )
            self.assertEqual(artifacts, {path: (root / path).read_bytes() for path in artifacts})

    @staticmethod
    def _create_repository(temporary: Path) -> Path:
        root = temporary / "repository"
        feature = root / ".specs" / FEATURE_ID
        feature.mkdir(parents=True)
        state = {
            "schema_version": 2,
            "feature_id": FEATURE_ID,
            "mode": "sequential",
            "project": "wave",
            "board": "wave",
            "max_workers": 1,
            "revision": 0,
            "active_task": None,
            "tasks": {
                "T-001": {
                    "phase": "done",
                    "status": "done",
                    "dependencies": [],
                    "test_ids": ["T-001-T1"],
                    "files_in_scope": ["work.txt"],
                    "kanban_id": None,
                    "issue": None,
                    "branch": None,
                    "pr": None,
                    "red_at": "proof",
                    "red_test_signature": "Test.done",
                    "red_failure_excerpt": "expected",
                    "green_at": "proof",
                }
            },
        }
        (feature / ".tdd-state.json").write_text(json.dumps(state), encoding="utf-8")
        (feature / "04-tasks.md").write_text("old tasks\n", encoding="utf-8")
        (feature / "05-implementation-log.md").write_text("old log\n", encoding="utf-8")
        (root / "work.txt").write_text("scope\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(
            ["git", "-C", str(root), "config", "user.email", "t@example.test"],
            check=True,
        )
        subprocess.run(["git", "-C", str(root), "config", "user.name", "T"], check=True)
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
        return root


if __name__ == "__main__":
    unittest.main()
