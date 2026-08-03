#!/usr/bin/env python3
"""Behavioral tests for one isolated Hermes SDD job envelope."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(__file__).with_name("sdd_job_execution.py")
CONTRACT_PATH = Path(__file__).with_name("job-execution-contract.md")
FEATURE_ID = "parallel-feature"
TASK_ID = "T-011"
JOB_KEY = f"{FEATURE_ID}:{TASK_ID}"
BRANCH = f"sdd/{FEATURE_ID}/t-011-job-envelope"
WORKTREE = ".worktrees/t-011-job-envelope"
SESSION_ID = "session-t-011"
ISSUE = 111
PULL_REQUEST = 211
PARENT_ISSUE = 74
KANBAN_ID = "card-t-011"


def load_execution():
    if not MODULE_PATH.is_file():
        raise AssertionError(
            "T-011-T1: sdd_job_execution.py must materialize an admitted job"
        )
    spec = importlib.util.spec_from_file_location("sdd_job_execution", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def admitted_job() -> dict[str, object]:
    return {
        "feature_id": FEATURE_ID,
        "task_id": TASK_ID,
        "slug": "job-envelope",
        "idempotency_key": JOB_KEY,
        "kanban_id": KANBAN_ID,
        "parent_issue": PARENT_ISSUE,
        "active_writer_count": 2,
        "runtime_contract_merged": True,
        "synchronized_with_main": True,
        "state_revision": 7,
    }


class RecordingGit:
    def __init__(self) -> None:
        self.branches: dict[str, str] = {}
        self.worktrees: dict[str, dict[str, str]] = {}
        self.calls: list[dict[str, str]] = []

    def ensure_branch(self, *, branch: str, idempotency_key: str) -> str:
        self.calls.append({"operation": "branch", "branch": branch})
        self.branches.setdefault(idempotency_key, branch)
        return self.branches[idempotency_key]

    def ensure_worktree(
        self, *, path: str, branch: str, idempotency_key: str
    ) -> str:
        self.calls.append({"operation": "worktree", "path": path})
        self.worktrees.setdefault(
            idempotency_key,
            {"path": path, "branch": branch},
        )
        return self.worktrees[idempotency_key]["path"]


class RecordingHermes:
    def __init__(self) -> None:
        self.sessions: dict[str, str] = {}
        self.calls: list[dict[str, str]] = []

    def ensure_session(self, *, idempotency_key: str, worktree: str) -> str:
        self.calls.append(
            {"idempotency_key": idempotency_key, "worktree": worktree}
        )
        self.sessions.setdefault(idempotency_key, SESSION_ID)
        return self.sessions[idempotency_key]


class RecordingGitHub:
    def __init__(self) -> None:
        self.issues: dict[str, int] = {}
        self.pull_requests: dict[str, int] = {}
        self.issue_calls: list[dict[str, object]] = []
        self.pull_request_calls: list[dict[str, object]] = []
        self.fail_pull_request = False

    def ensure_child_issue(
        self,
        *,
        parent_issue: int,
        feature_id: str,
        task_id: str,
        idempotency_key: str,
    ) -> int:
        self.issue_calls.append(
            {
                "parent_issue": parent_issue,
                "feature_id": feature_id,
                "task_id": task_id,
                "idempotency_key": idempotency_key,
            }
        )
        self.issues.setdefault(idempotency_key, ISSUE)
        return self.issues[idempotency_key]

    def ensure_draft_pull_request(
        self,
        *,
        branch: str,
        issue: int,
        idempotency_key: str,
        draft: bool,
    ) -> int:
        self.pull_request_calls.append(
            {
                "branch": branch,
                "issue": issue,
                "idempotency_key": idempotency_key,
                "draft": draft,
            }
        )
        if self.fail_pull_request:
            raise RuntimeError(
                "token=ghp_abcdefghijklmnopqrstuvwxyz123456 "
                "person@example.test /Users/person/private customer-order-42"
            )
        self.pull_requests.setdefault(idempotency_key, PULL_REQUEST)
        return self.pull_requests[idempotency_key]


class RecordingKanban:
    def __init__(self) -> None:
        self.external_ids: list[dict[str, int | str]] = []

    def record_external_ids(self, *, card_id: str, issue: int, pr: int) -> None:
        self.external_ids.append({"card_id": card_id, "issue": issue, "pr": pr})


class RecordingStateStore:
    def __init__(self) -> None:
        self.revision = 7
        self.external_ids: dict[str, dict[str, int]] = {}
        self.envelopes: dict[str, dict[str, object]] = {}

    def external_ids_for(self, *, task_id: str) -> dict[str, int] | None:
        return copy.deepcopy(self.external_ids.get(task_id))

    def compare_and_swap_task(
        self,
        *,
        expected_revision: int,
        task_id: str,
        issue: int,
        pr: int,
    ) -> None:
        if expected_revision != self.revision:
            raise AssertionError("stale state revision")
        self.external_ids[task_id] = {"issue": issue, "pr": pr}
        self.revision += 1

    def envelope_for(self, *, idempotency_key: str) -> dict[str, object] | None:
        return copy.deepcopy(self.envelopes.get(idempotency_key))

    def record_envelope(
        self, *, idempotency_key: str, envelope: dict[str, object]
    ) -> None:
        existing = self.envelopes.get(idempotency_key)
        if existing is not None and existing != envelope:
            raise AssertionError("divergent envelope")
        self.envelopes[idempotency_key] = copy.deepcopy(envelope)


class RecordingLog:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def record(self, **event: object) -> None:
        self.events.append(copy.deepcopy(event))


def execute(
    *,
    job: dict[str, object] | None = None,
    git: RecordingGit | None = None,
    hermes: RecordingHermes | None = None,
    github: RecordingGitHub | None = None,
    kanban: RecordingKanban | None = None,
    state_store: RecordingStateStore | None = None,
    log: RecordingLog | None = None,
) -> tuple[dict[str, object], tuple[object, ...]]:
    adapters = (
        RecordingGit() if git is None else git,
        RecordingHermes() if hermes is None else hermes,
        RecordingGitHub() if github is None else github,
        RecordingKanban() if kanban is None else kanban,
        RecordingStateStore() if state_store is None else state_store,
        RecordingLog() if log is None else log,
    )
    execution = load_execution()
    envelope = execution.materialize_job(
        job=admitted_job() if job is None else job,
        git=adapters[0],
        hermes=adapters[1],
        github=adapters[2],
        kanban=adapters[3],
        state_store=adapters[4],
        log=adapters[5],
    )
    return envelope, adapters


class JobExecutionTest(unittest.TestCase):
    def test_t011_t1_materializes_the_complete_job_envelope(self) -> None:
        """T-011-T1/AC-030: one admitted job gets every isolated surface."""

        envelope, _ = execute()

        self.assertEqual(
            {
                "idempotency_key": JOB_KEY,
                "task_id": TASK_ID,
                "branch": BRANCH,
                "worktree": WORKTREE,
                "session_id": SESSION_ID,
                "issue": ISSUE,
                "pr": PULL_REQUEST,
            },
            envelope,
        )

    def test_t011_t2_branch_and_native_worktree_follow_the_contract(self) -> None:
        """T-011-T2/AC-032: branch and worktree names are deterministic."""

        envelope, adapters = execute()
        git = adapters[0]

        self.assertEqual(BRANCH, envelope["branch"])
        self.assertEqual(WORKTREE, envelope["worktree"])
        self.assertEqual(
            {"path": WORKTREE, "branch": BRANCH},
            git.worktrees[JOB_KEY],
        )

    def test_t011_t3_session_child_issue_and_draft_pr_are_unique(self) -> None:
        """T-011-T3/AC-033/AC-034: Hermes and GitHub objects stay job-local."""

        envelope, adapters = execute()
        hermes, github, kanban = adapters[1:4]

        self.assertEqual(SESSION_ID, hermes.sessions[JOB_KEY])
        self.assertEqual(PARENT_ISSUE, github.issue_calls[0]["parent_issue"])
        self.assertTrue(github.pull_request_calls[0]["draft"])
        self.assertEqual(
            [{"card_id": KANBAN_ID, "issue": ISSUE, "pr": PULL_REQUEST}],
            kanban.external_ids,
        )
        self.assertEqual(ISSUE, envelope["issue"])

    def test_t011_t4_failure_logs_exclude_sensitive_and_business_content(self) -> None:
        """T-011-T4/AC-233: raw errors never enter durable logs."""

        github = RecordingGitHub()
        github.fail_pull_request = True
        log = RecordingLog()

        with self.assertRaises(RuntimeError):
            execute(github=github, log=log)

        serialized = json.dumps(log.events)
        for forbidden in (
            "ghp_abcdefghijklmnopqrstuvwxyz123456",
            "person@example.test",
            "/Users/person/private",
            "customer-order-42",
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertIn("RuntimeError", serialized)

    def test_t011_t5_replay_reuses_every_surface_without_duplicates(self) -> None:
        """T-011-T5/AC-035: one job key always recovers the same envelope."""

        git = RecordingGit()
        hermes = RecordingHermes()
        github = RecordingGitHub()
        kanban = RecordingKanban()
        state_store = RecordingStateStore()
        log = RecordingLog()
        first, _ = execute(
            git=git,
            hermes=hermes,
            github=github,
            kanban=kanban,
            state_store=state_store,
            log=log,
        )
        second, _ = execute(
            git=git,
            hermes=hermes,
            github=github,
            kanban=kanban,
            state_store=state_store,
            log=log,
        )

        self.assertEqual(first, second)
        self.assertEqual(1, len(github.issues))
        self.assertEqual(1, len(github.pull_requests))
        self.assertEqual(1, len(git.branches))
        self.assertEqual(1, len(git.worktrees))
        self.assertEqual(1, len(hermes.sessions))

    def test_t011_t6_failure_preserves_resources_and_retry_recovers(self) -> None:
        """T-011-T6/AC-036: failure keeps all completed surfaces for retry."""

        git = RecordingGit()
        hermes = RecordingHermes()
        github = RecordingGitHub()
        github.fail_pull_request = True
        state_store = RecordingStateStore()
        log = RecordingLog()

        with self.assertRaises(RuntimeError):
            execute(
                git=git,
                hermes=hermes,
                github=github,
                state_store=state_store,
                log=log,
            )

        self.assertEqual(BRANCH, git.branches[JOB_KEY])
        self.assertEqual(WORKTREE, git.worktrees[JOB_KEY]["path"])
        self.assertEqual(SESSION_ID, hermes.sessions[JOB_KEY])
        self.assertEqual(ISSUE, github.issues[JOB_KEY])
        github.fail_pull_request = False
        recovered, _ = execute(
            git=git,
            hermes=hermes,
            github=github,
            state_store=state_store,
            log=log,
        )
        self.assertEqual(PULL_REQUEST, recovered["pr"])
        self.assertEqual(1, len(github.issues))

    def test_t011_t7_no_adapter_exposes_destructive_git_or_merge(self) -> None:
        """T-011-T7/AC-234: the job API has no destructive lifecycle method."""

        source = MODULE_PATH.read_text(encoding="utf-8")
        contract = CONTRACT_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "force_push",
            "reset_hard",
            "delete_branch",
            "remove_worktree",
            "merge_pull_request",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("un worktree natif sous `.worktrees/`", contract)
        self.assertIn("une pull request brouillon", contract)
        self.assertIn("Aucun nettoyage automatique", contract)


if __name__ == "__main__":
    unittest.main()
