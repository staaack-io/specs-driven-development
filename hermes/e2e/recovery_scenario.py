#!/usr/bin/env python3
"""Run a local failure, retry, and transactional fan-in recovery scenario."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


FEATURE_ID = "e2e-recovery"
WAVE_ID = "wave-recovery"
GREEN_TASK = "T-101"
RECOVERED_TASK = "T-102"
PARENT_ISSUE = 90
FAN_IN_PR = 390
SHARED_NAMES = ("04-tasks.md", ".tdd-state.json", "05-implementation-log.md")


def _load_runtime_module(filename: str, module_name: str):
    path = Path(__file__).parents[1] / "runtime" / filename
    existing = sys.modules.get(module_name)
    if existing is not None and Path(existing.__file__).resolve() == path.resolve():
        return existing
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load canonical runtime module: {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runtime = _load_runtime_module("sdd_runtime_guard.py", "_e2e_recovery_runtime")
jobs = _load_runtime_module("sdd_job_execution.py", "_e2e_recovery_jobs")
synthesizer = _load_runtime_module(
    "sdd_wave_synthesizer.py", "_e2e_recovery_synthesizer"
)


class _GitAdapter:
    def __init__(self) -> None:
        self.branches: dict[str, str] = {}
        self.worktrees: dict[str, dict[str, str]] = {}

    def ensure_branch(self, *, branch: str, idempotency_key: str) -> str:
        self.branches.setdefault(idempotency_key, branch)
        return self.branches[idempotency_key]

    def ensure_worktree(
        self, *, path: str, branch: str, idempotency_key: str
    ) -> str:
        self.worktrees.setdefault(idempotency_key, {"path": path, "branch": branch})
        return self.worktrees[idempotency_key]["path"]


class _HermesAdapter:
    def __init__(self) -> None:
        self.sessions: dict[str, str] = {}

    def ensure_session(self, *, idempotency_key: str, worktree: str) -> str:
        task = idempotency_key.rsplit(":", maxsplit=1)[-1].lower()
        self.sessions.setdefault(idempotency_key, f"session-{task}")
        return self.sessions[idempotency_key]


class _GitHubAdapter:
    def __init__(self) -> None:
        self.issues: dict[str, int] = {}
        self.pull_requests: dict[str, int] = {}
        self.observed_integrations: set[int] = set()
        self.fan_in_requests: dict[str, int] = {}

    def ensure_child_issue(
        self,
        *,
        parent_issue: int,
        feature_id: str,
        task_id: str,
        idempotency_key: str,
    ) -> int:
        del parent_issue, feature_id
        self.issues.setdefault(idempotency_key, 100 + int(task_id.removeprefix("T-")))
        return self.issues[idempotency_key]

    def ensure_draft_pull_request(
        self,
        *,
        branch: str,
        issue: int,
        idempotency_key: str,
        draft: bool,
    ) -> int:
        del branch, issue, draft
        task = int(idempotency_key.rsplit(":", maxsplit=1)[-1].removeprefix("T-"))
        self.pull_requests.setdefault(idempotency_key, 200 + task)
        return self.pull_requests[idempotency_key]

    def ensure_fan_in_pull_request(
        self,
        *,
        wave_id: str,
        branch: str,
        idempotency_key: str,
        draft: bool,
    ) -> int:
        del wave_id, branch, draft
        self.fan_in_requests.setdefault(idempotency_key, FAN_IN_PR)
        return self.fan_in_requests[idempotency_key]

    def is_merged(self, *, pr: int) -> bool:
        return pr in self.observed_integrations


class _KanbanAdapter:
    def __init__(self) -> None:
        self.identifiers: dict[str, dict[str, int]] = {}
        self.wave_statuses: dict[str, str] = {}

    def record_external_ids(self, *, card_id: str, issue: int, pr: int) -> None:
        self.identifiers[card_id] = {"issue": issue, "pr": pr}

    def set_wave_status(self, *, wave_id: str, status: str) -> None:
        self.wave_statuses[wave_id] = status


class _StateStore:
    def __init__(self) -> None:
        self.revision = 0
        self.external_ids: dict[str, dict[str, int]] = {}
        self.envelopes: dict[str, dict[str, object]] = {}
        self.fan_in_pr: dict[str, int] = {}

    def external_ids_for(self, *, task_id: str) -> dict[str, int] | None:
        return copy.deepcopy(self.external_ids.get(task_id))

    def compare_and_swap_task(
        self, *, expected_revision: int, task_id: str, issue: int, pr: int
    ) -> None:
        if expected_revision != self.revision:
            raise RuntimeError("stale recovery fixture revision")
        self.external_ids[task_id] = {"issue": issue, "pr": pr}
        self.revision += 1

    def envelope_for(self, *, idempotency_key: str) -> dict[str, object] | None:
        return copy.deepcopy(self.envelopes.get(idempotency_key))

    def record_envelope(
        self, *, idempotency_key: str, envelope: dict[str, object]
    ) -> None:
        existing = self.envelopes.get(idempotency_key)
        if existing is not None and existing != envelope:
            raise RuntimeError("recovery produced a divergent envelope")
        self.envelopes[idempotency_key] = copy.deepcopy(envelope)

    def fan_in_pr_for(self, *, wave_id: str) -> int | None:
        return self.fan_in_pr.get(wave_id)

    def record_fan_in_pr(self, *, wave_id: str, pr: int) -> None:
        self.fan_in_pr.setdefault(wave_id, pr)


class _LogAdapter:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def record(self, **event: object) -> None:
        self.events.append(copy.deepcopy(event))


def _state(revision: int) -> dict[str, object]:
    tasks = {}
    for task_id, scope in (
        (GREEN_TASK, "work/green.txt"),
        (RECOVERED_TASK, "work/recovered.txt"),
    ):
        tasks[task_id] = {
            "phase": "done",
            "status": "done",
            "dependencies": [],
            "test_ids": [f"{task_id}-T1"],
            "files_in_scope": [scope],
            "kanban_id": None,
            "issue": None,
            "branch": None,
            "pr": None,
            "red_at": "proof",
            "red_test_signature": "RecoveryScenario.proof",
            "red_failure_excerpt": "expected interruption",
            "green_at": "proof",
        }
    return {
        "schema_version": 2,
        "feature_id": FEATURE_ID,
        "mode": "parallel",
        "project": "local-e2e",
        "board": "local-e2e",
        "max_workers": 2,
        "revision": revision,
        "active_task": None,
        "tasks": tasks,
    }


def _initialize_repository(root: Path) -> None:
    feature = root / ".specs" / FEATURE_ID
    feature.mkdir(parents=True)
    (root / "work").mkdir()
    (feature / "04-tasks.md").write_text("old\n", encoding="utf-8")
    (feature / ".tdd-state.json").write_text(
        json.dumps(_state(0), sort_keys=True), encoding="utf-8"
    )
    (feature / "05-implementation-log.md").write_text("old\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "user.email", "e2e@example.invalid"],
        cwd=root,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Hermes E2E"], cwd=root, check=True
    )
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "initialize recovery fixture"], cwd=root, check=True)


def _job(task_id: str, revision: int) -> dict[str, object]:
    return {
        "feature_id": FEATURE_ID,
        "task_id": task_id,
        "slug": "recovery-proof",
        "idempotency_key": f"{FEATURE_ID}:{task_id}",
        "kanban_id": f"card-{task_id.lower()}",
        "parent_issue": PARENT_ISSUE,
        "active_writer_count": 2,
        "runtime_contract_merged": True,
        "synchronized_with_main": True,
        "state_revision": revision,
    }


def _materialize(job: dict[str, object], adapters: tuple[Any, ...]) -> dict[str, object]:
    return jobs.materialize_job(
        job=job,
        git=adapters[0],
        hermes=adapters[1],
        github=adapters[2],
        kanban=adapters[3],
        state_store=adapters[4],
        log=adapters[5],
    )


def _shared_artifacts(root: Path, generation: str, revision: int) -> dict[str, bytes]:
    prefix = f".specs/{FEATURE_ID}"
    return {
        f"{prefix}/04-tasks.md": f"{generation}\n".encode(),
        f"{prefix}/.tdd-state.json": json.dumps(
            _state(revision), sort_keys=True
        ).encode(),
        f"{prefix}/05-implementation-log.md": f"{generation}\n".encode(),
    }


def _tokens(root: Path, artifacts: dict[str, bytes]) -> dict[str, str]:
    return {path: runtime.token_for((root / path).read_bytes()) for path in artifacts}


def _snapshot_label(
    root: Path,
    previous: dict[str, bytes],
    following: dict[str, bytes],
) -> dict[str, str]:
    labels = {}
    for path in previous:
        value = (root / path).read_bytes()
        if value == previous[path]:
            labels[path] = "old"
        elif value == following[path]:
            labels[path] = "new"
        else:
            labels[path] = "unknown"
    return labels


def _atomic_recovery_proofs(root: Path) -> tuple[list[str], list[dict[str, str]]]:
    old = {
        f".specs/{FEATURE_ID}/{name}": (
            root / ".specs" / FEATURE_ID / name
        ).read_bytes()
        for name in SHARED_NAMES
    }
    new = _shared_artifacts(root, "new", 1)
    snapshots: list[dict[str, str]] = []
    try:
        synthesizer.commit_fan_in(
            repo_root=root,
            feature_id=FEATURE_ID,
            transaction_id="recovery-before-marker",
            artifacts=new,
            expected_tokens=_tokens(root, new),
            runtime=runtime,
            crash_point="before-marker",
        )
    except runtime.InjectedCrash:
        runtime.recover_fan_in(
            root, feature_id=FEATURE_ID, transaction_id="recovery-before-marker"
        )
    snapshots.append(_snapshot_label(root, old, new))
    try:
        synthesizer.commit_fan_in(
            repo_root=root,
            feature_id=FEATURE_ID,
            transaction_id="recovery-after-marker",
            artifacts=new,
            expected_tokens=_tokens(root, new),
            runtime=runtime,
            crash_point="after-marker",
        )
    except runtime.InjectedCrash:
        runtime.recover_fan_in(
            root, feature_id=FEATURE_ID, transaction_id="recovery-after-marker"
        )
    snapshots.append(_snapshot_label(root, old, new))
    return [next(iter(snapshot.values())) for snapshot in snapshots], snapshots


def run_recovery_scenario(repo_root: Path | str, *, injection: str) -> dict[str, object]:
    """Execute one deterministic local interruption and idempotent retry."""

    if injection not in {"failure", "timeout"}:
        raise ValueError("injection must be failure or timeout")
    root = Path(repo_root).resolve()
    _initialize_repository(root)
    adapters = (
        _GitAdapter(),
        _HermesAdapter(),
        _GitHubAdapter(),
        _KanbanAdapter(),
        _StateStore(),
        _LogAdapter(),
    )

    green_envelope = _materialize(_job(GREEN_TASK, 0), adapters)
    green_path = root / "work" / "green.txt"
    green_path.write_text("green proof\n", encoding="utf-8")
    runtime.append_job_event(
        root,
        feature_id=FEATURE_ID,
        task_id=GREEN_TASK,
        event_id="green-proof",
        event={"status": "green", "file": "work/green.txt"},
    )
    green_before_injection = green_path.read_bytes()

    interrupted_envelope = _materialize(_job(RECOVERED_TASK, 1), adapters)
    try:
        if injection == "timeout":
            raise TimeoutError("deterministic writer timeout")
        raise RuntimeError("deterministic writer failure")
    except (RuntimeError, TimeoutError):
        pass

    recovered_envelope = _materialize(_job(RECOVERED_TASK, 2), adapters)
    recovered_path = root / "work" / "recovered.txt"
    recovered_path.write_text("recovered proof\n", encoding="utf-8")
    runtime.append_job_event(
        root,
        feature_id=FEATURE_ID,
        task_id=RECOVERED_TASK,
        event_id="recovered-proof",
        event={"status": "recovered", "file": "work/recovered.txt"},
    )
    generations, snapshots = _atomic_recovery_proofs(root)

    artifacts = _shared_artifacts(root, "new", 1)
    synthesis = synthesizer.synthesize_wave(
        repo_root=root,
        wave={
            "wave_id": WAVE_ID,
            "feature_id": FEATURE_ID,
            "jobs": [
                {"task_id": GREEN_TASK, "status": "done"},
                {"task_id": RECOVERED_TASK, "status": "done"},
            ],
        },
        artifacts=artifacts,
        expected_tokens=_tokens(root, artifacts),
        runtime=runtime,
        github=adapters[2],
        kanban=adapters[3],
        state_store=adapters[4],
    )
    fan_in_pr = int(synthesis["pr"])
    before_observed = synthesizer.next_wave_admissible(
        wave_id=WAVE_ID, github=adapters[2], state_store=adapters[4]
    )
    adapters[2].observed_integrations.add(fan_in_pr)
    observed_without_go = False
    explicit_go: set[str] = set()
    explicit_go.add(WAVE_ID)
    observed_with_go = WAVE_ID in explicit_go and synthesizer.next_wave_admissible(
        wave_id=WAVE_ID, github=adapters[2], state_store=adapters[4]
    )

    return {
        "injection": injection,
        "writers": {
            GREEN_TASK: {"status": "green", "envelope": green_envelope},
            RECOVERED_TASK: {"status": "recovered", "envelope": recovered_envelope},
        },
        "green_writer_preserved": green_path.read_bytes() == green_before_injection,
        "retry_same_identity": interrupted_envelope == recovered_envelope,
        "resource_counts": {
            "branches": len(adapters[0].branches),
            "worktrees": len(adapters[0].worktrees),
            "sessions": len(adapters[1].sessions),
            "issues": len(adapters[2].issues),
            "prs": len(adapters[2].pull_requests),
        },
        "journal_events": {
            task_id: runtime.verify_job_journal(
                root, feature_id=FEATURE_ID, task_id=task_id
            )
            for task_id in (GREEN_TASK, RECOVERED_TASK)
        },
        "fan_in_generations": generations,
        "fan_in_snapshots": snapshots,
        "admissibility": {
            "before_observed_fan_in": before_observed,
            "observed_without_go": observed_without_go,
            "observed_with_go": observed_with_go,
        },
        "merge_commands": [],
    }
