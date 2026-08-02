#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


BRIDGE_SCRIPT = Path(__file__).with_name("sdd_github_bridge.py")
FEATURE_ID = "feature-one"
TASK_ID = "T-004"
KANBAN_ID = "card-004"
BRANCH = "sdd/feature-one/t-004-github-bridge"
IDEMPOTENCY_KEY = "feature-one:T-004"
ISSUE_NUMBER = 104
PULL_REQUEST_NUMBER = 204
STATE_REVISION = 7
FEATURE_ID_FIELD = "feature_id"
TASK_ID_FIELD = "task_id"
BRANCH_FIELD = "branch"
ISSUE_FIELD = "issue"
PULL_REQUEST_FIELD = "pr"
EXPECTED_REVISION_FIELD = "expected_revision"
ACTIVE_WRITER_COUNT = 2
STARTED_AT = 1_000.0
POLL_INTERVAL_SECONDS = 300.0
REVIEW_TIMEOUT_SECONDS = 1_800.0
AWAITING_REVIEW = "awaiting_review"
NEEDS_INPUT = "needs_input"


def load_bridge():
    module_spec = importlib.util.spec_from_file_location(
        "sdd_github_bridge", BRIDGE_SCRIPT
    )
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


class FakeGitHubAdapter:
    def __init__(self, *, reviews: list[str] | None = None) -> None:
        self.issue_calls: list[dict[str, object]] = []
        self.pull_request_calls: list[dict[str, object]] = []
        self.ready_calls: list[int] = []
        self.check_calls: list[int] = []
        self.review_calls: list[int] = []
        self.thread_calls: list[int] = []
        self.thread_reply_calls: list[dict[str, object]] = []
        self.new_review_calls: list[int] = []
        self.reviews = [] if reviews is None else reviews

    def create_issue(self, *, feature_id: str, task_id: str) -> int:
        self.issue_calls.append(
            {FEATURE_ID_FIELD: feature_id, TASK_ID_FIELD: task_id}
        )
        return ISSUE_NUMBER

    def create_pull_request(
        self, *, branch: str, issue: int, draft: bool
    ) -> int:
        self.pull_request_calls.append(
            {BRANCH_FIELD: branch, ISSUE_FIELD: issue, "draft": draft}
        )
        return PULL_REQUEST_NUMBER

    def mark_pull_request_ready(self, *, pr: int) -> None:
        self.ready_calls.append(pr)

    def get_checks(self, *, pr: int) -> list[str]:
        self.check_calls.append(pr)
        return ["success"]

    def get_reviews(self, *, pr: int) -> list[str]:
        self.review_calls.append(pr)
        return self.reviews

    def get_review_threads(self, *, pr: int) -> list[str]:
        self.thread_calls.append(pr)
        return []

    def reply_to_review_thread(
        self, *, pr: int, thread_id: str, body: str
    ) -> None:
        self.thread_reply_calls.append(
            {PULL_REQUEST_FIELD: pr, "thread_id": thread_id, "body": body}
        )

    def request_new_review(self, *, pr: int) -> None:
        self.new_review_calls.append(pr)


class FakeKanbanAdapter:
    def __init__(self, *, fail_first_record: bool = False) -> None:
        self.cards = {
            KANBAN_ID: {
                ISSUE_FIELD: None,
                PULL_REQUEST_FIELD: None,
                "status": "in_progress",
            }
        }
        self.fail_first_record = fail_first_record
        self.record_calls = 0
        self.status_calls: list[dict[str, str]] = []

    def record_external_ids(self, *, card_id: str, issue: int, pr: int) -> None:
        self.record_calls += 1
        if self.fail_first_record and self.record_calls == 1:
            raise RuntimeError("injected Kanban write failure")
        self.cards[card_id][ISSUE_FIELD] = issue
        self.cards[card_id][PULL_REQUEST_FIELD] = pr

    def set_status(self, *, card_id: str, status: str) -> None:
        self.status_calls.append({"card_id": card_id, "status": status})
        self.cards[card_id]["status"] = status


class FakeStateStore:
    def __init__(self) -> None:
        self.revision = STATE_REVISION
        self.tasks = {
            TASK_ID: {ISSUE_FIELD: None, PULL_REQUEST_FIELD: None}
        }
        self.cas_calls: list[dict[str, object]] = []
        self.tracking = {
            TASK_ID: {
                "review_wait_started_at": STARTED_AT,
                "last_polled_at": None,
            }
        }
        self.status_calls: list[dict[str, str]] = []
        self.restart_calls: list[dict[str, object]] = []

    def external_ids_for(self, *, task_id: str) -> dict[str, int] | None:
        task = self.tasks[task_id]
        if task[ISSUE_FIELD] is None or task[PULL_REQUEST_FIELD] is None:
            return None
        return {
            ISSUE_FIELD: task[ISSUE_FIELD],
            PULL_REQUEST_FIELD: task[PULL_REQUEST_FIELD],
        }

    def compare_and_swap_task(
        self,
        *,
        expected_revision: int,
        task_id: str,
        issue: int,
        pr: int,
    ) -> None:
        self.cas_calls.append(
            {
                EXPECTED_REVISION_FIELD: expected_revision,
                TASK_ID_FIELD: task_id,
                ISSUE_FIELD: issue,
                PULL_REQUEST_FIELD: pr,
            }
        )
        if expected_revision != self.revision:
            raise AssertionError("stale state revision")
        self.tasks[task_id] = {
            ISSUE_FIELD: issue,
            PULL_REQUEST_FIELD: pr,
        }
        self.revision += 1

    def review_tracking(self, *, task_id: str) -> dict[str, float | None]:
        return dict(self.tracking[task_id])

    def record_poll(self, *, task_id: str, polled_at: float) -> None:
        self.tracking[task_id]["last_polled_at"] = polled_at

    def set_status(self, *, task_id: str, status: str) -> None:
        self.status_calls.append({TASK_ID_FIELD: task_id, "status": status})

    def restart_review_wait(
        self, *, task_id: str, branch: str, started_at: float
    ) -> None:
        self.restart_calls.append(
            {
                TASK_ID_FIELD: task_id,
                BRANCH_FIELD: branch,
                "started_at": started_at,
            }
        )
        self.tracking[task_id] = {
            "review_wait_started_at": started_at,
            "last_polled_at": None,
        }


class FakeClock:
    def __init__(self, now: float = STARTED_AT) -> None:
        self.current = now

    def now(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


class FakeWorker:
    def __init__(self) -> None:
        self.correction_calls: list[dict[str, str]] = []

    def apply_correction(self, *, branch: str, instruction: str) -> None:
        self.correction_calls.append(
            {BRANCH_FIELD: branch, "instruction": instruction}
        )


def admitted_job(**overrides: object) -> dict[str, object]:
    job: dict[str, object] = {
        FEATURE_ID_FIELD: FEATURE_ID,
        TASK_ID_FIELD: TASK_ID,
        "kanban_id": KANBAN_ID,
        BRANCH_FIELD: BRANCH,
        "idempotency_key": IDEMPOTENCY_KEY,
        "state_revision": STATE_REVISION,
        "active_writer_count": ACTIVE_WRITER_COUNT,
        "runtime_contract_merged": True,
        "synchronized_with_main": True,
        PULL_REQUEST_FIELD: PULL_REQUEST_NUMBER,
    }
    job.update(overrides)
    return job


class GitHubBridgeLifecycleTest(unittest.TestCase):
    def test_admitted_job_creates_and_records_issue_and_draft_pull_request(
        self,
    ) -> None:
        """T-004-T1/T-004-T2 / AC-110–AC-113, AC-253–AC-254."""
        bridge = load_bridge()
        github = FakeGitHubAdapter()
        kanban = FakeKanbanAdapter()
        state_store = FakeStateStore()
        job = admitted_job()

        bridge.start_job(
            job=job,
            gh=github,
            kanban=kanban,
            state_store=state_store,
        )

        self.assertEqual(
            [{FEATURE_ID_FIELD: FEATURE_ID, TASK_ID_FIELD: TASK_ID}],
            github.issue_calls,
        )
        self.assertEqual(
            [{BRANCH_FIELD: BRANCH, ISSUE_FIELD: ISSUE_NUMBER, "draft": True}],
            github.pull_request_calls,
        )
        identifiers = {
            ISSUE_FIELD: ISSUE_NUMBER,
            PULL_REQUEST_FIELD: PULL_REQUEST_NUMBER,
        }
        self.assertEqual(
            identifiers,
            {
                ISSUE_FIELD: kanban.cards[KANBAN_ID][ISSUE_FIELD],
                PULL_REQUEST_FIELD: kanban.cards[KANBAN_ID][PULL_REQUEST_FIELD],
            },
        )
        self.assertEqual(identifiers, state_store.tasks[TASK_ID])
        self.assertEqual(
            [
                {
                    EXPECTED_REVISION_FIELD: STATE_REVISION,
                    TASK_ID_FIELD: TASK_ID,
                    **identifiers,
                }
            ],
            state_store.cas_calls,
        )

    def test_green_tests_make_only_the_draft_pull_request_ready(self) -> None:
        """T-004-T3 / AC-114, AC-120."""
        bridge = load_bridge()
        github = FakeGitHubAdapter()
        kanban = FakeKanbanAdapter()

        bridge.mark_ready(job=admitted_job(), gh=github, kanban=kanban)

        self.assertEqual([PULL_REQUEST_NUMBER], github.ready_calls)
        self.assertEqual(AWAITING_REVIEW, kanban.cards[KANBAN_ID]["status"])
        self.assertFalse(hasattr(github, "merge_pull_request"))

    def test_due_poll_reads_checks_reviews_and_exact_threads_every_five_minutes(
        self,
    ) -> None:
        """T-004-T4 / AC-115, AC-255, AC-256."""
        bridge = load_bridge()
        github = FakeGitHubAdapter()
        kanban = FakeKanbanAdapter()
        state_store = FakeStateStore()
        clock = FakeClock()
        job = admitted_job()

        first = bridge.poll_pull_request(
            job=job,
            gh=github,
            kanban=kanban,
            state_store=state_store,
            clock=clock,
        )
        clock.advance(POLL_INTERVAL_SECONDS - 1)
        early = bridge.poll_pull_request(
            job=job,
            gh=github,
            kanban=kanban,
            state_store=state_store,
            clock=clock,
        )
        clock.advance(1)
        due = bridge.poll_pull_request(
            job=job,
            gh=github,
            kanban=kanban,
            state_store=state_store,
            clock=clock,
        )

        self.assertTrue(first["polled"])
        self.assertFalse(early["polled"])
        self.assertTrue(due["polled"])
        self.assertEqual([PULL_REQUEST_NUMBER] * 2, github.check_calls)
        self.assertEqual([PULL_REQUEST_NUMBER] * 2, github.review_calls)
        self.assertEqual([PULL_REQUEST_NUMBER] * 2, github.thread_calls)

    def test_correction_stays_on_branch_replies_to_exact_thread_and_rewaits(
        self,
    ) -> None:
        """T-004-T5 / AC-116–AC-118."""
        bridge = load_bridge()
        github = FakeGitHubAdapter()
        kanban = FakeKanbanAdapter()
        state_store = FakeStateStore()
        worker = FakeWorker()
        clock = FakeClock(STARTED_AT + POLL_INTERVAL_SECONDS)
        correction = {
            "thread_id": "thread-17",
            "instruction": "handle the stale revision",
            "reply": "Corrected on the existing branch.",
        }

        bridge.apply_review_correction(
            job=admitted_job(),
            correction=correction,
            worker=worker,
            gh=github,
            kanban=kanban,
            state_store=state_store,
            clock=clock,
        )

        self.assertEqual(
            [{BRANCH_FIELD: BRANCH, "instruction": correction["instruction"]}],
            worker.correction_calls,
        )
        self.assertEqual(
            [
                {
                    PULL_REQUEST_FIELD: PULL_REQUEST_NUMBER,
                    "thread_id": correction["thread_id"],
                    "body": correction["reply"],
                }
            ],
            github.thread_reply_calls,
        )
        self.assertEqual([PULL_REQUEST_NUMBER], github.new_review_calls)
        self.assertEqual(AWAITING_REVIEW, kanban.cards[KANBAN_ID]["status"])
        self.assertEqual(BRANCH, state_store.restart_calls[0][BRANCH_FIELD])

    def test_thirty_minutes_without_review_moves_card_to_needs_input(self) -> None:
        """T-004-T6 / AC-119."""
        bridge = load_bridge()
        github = FakeGitHubAdapter()
        kanban = FakeKanbanAdapter()
        state_store = FakeStateStore()
        clock = FakeClock(STARTED_AT + REVIEW_TIMEOUT_SECONDS)

        result = bridge.poll_pull_request(
            job=admitted_job(),
            gh=github,
            kanban=kanban,
            state_store=state_store,
            clock=clock,
        )

        self.assertEqual({"status": NEEDS_INPUT}, result)
        self.assertEqual(NEEDS_INPUT, kanban.cards[KANBAN_ID]["status"])
        self.assertEqual(
            [{TASK_ID_FIELD: TASK_ID, "status": NEEDS_INPUT}],
            state_store.status_calls,
        )
        self.assertEqual([PULL_REQUEST_NUMBER], github.review_calls)

    def test_review_available_at_deadline_does_not_move_card_to_needs_input(
        self,
    ) -> None:
        """T-004-T6 / AC-119 boundary triangulation."""
        bridge = load_bridge()
        github = FakeGitHubAdapter(reviews=["approved"])
        kanban = FakeKanbanAdapter()
        state_store = FakeStateStore()
        clock = FakeClock(STARTED_AT + REVIEW_TIMEOUT_SECONDS)

        result = bridge.poll_pull_request(
            job=admitted_job(),
            gh=github,
            kanban=kanban,
            state_store=state_store,
            clock=clock,
        )

        self.assertEqual(["approved"], result["reviews"])
        self.assertNotEqual(NEEDS_INPUT, result["status"])
        self.assertEqual("in_progress", kanban.cards[KANBAN_ID]["status"])
        self.assertEqual([], state_store.status_calls)

    def test_safety_gates_reject_third_writer_and_unready_dependencies(self) -> None:
        """T-004-T7 / AC-001, AC-002, AC-004, AC-106, AC-120–AC-122."""
        bridge = load_bridge()

        unsafe_jobs = (
            admitted_job(idempotency_key="another-feature:T-004"),
            admitted_job(active_writer_count=3),
            admitted_job(runtime_contract_merged=False),
            admitted_job(synchronized_with_main=False),
        )
        for job in unsafe_jobs:
            with self.subTest(job=job):
                github = FakeGitHubAdapter()
                with self.assertRaises(bridge.BridgeError):
                    bridge.start_job(
                        job=job,
                        gh=github,
                        kanban=FakeKanbanAdapter(),
                        state_store=FakeStateStore(),
                    )
                self.assertEqual([], github.issue_calls)
                self.assertEqual([], github.pull_request_calls)

        source = BRIDGE_SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("while True", source)
        self.assertNotIn("merge_pull_request", source)
        self.assertFalse(hasattr(bridge, "run_scheduler"))

    def test_retry_after_kanban_failure_recovers_without_duplicate_objects(
        self,
    ) -> None:
        """T-004-T8 / AC-112–AC-113, AC-253–AC-254."""
        bridge = load_bridge()
        github = FakeGitHubAdapter()
        kanban = FakeKanbanAdapter(fail_first_record=True)
        state_store = FakeStateStore()
        job = admitted_job()

        with self.assertRaisesRegex(RuntimeError, "Kanban write failure"):
            bridge.start_job(
                job=job,
                gh=github,
                kanban=kanban,
                state_store=state_store,
            )
        recovered = bridge.start_job(
            job=job,
            gh=github,
            kanban=kanban,
            state_store=state_store,
        )

        self.assertEqual(
            {ISSUE_FIELD: ISSUE_NUMBER, PULL_REQUEST_FIELD: PULL_REQUEST_NUMBER},
            recovered,
        )
        self.assertEqual(1, len(github.issue_calls))
        self.assertEqual(1, len(github.pull_request_calls))
        self.assertEqual(1, len(state_store.cas_calls))
        self.assertEqual(2, kanban.record_calls)


if __name__ == "__main__":
    unittest.main()
