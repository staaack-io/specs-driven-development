#!/usr/bin/env python3
"""Event-driven bridge between an admitted Hermes job and GitHub.

Hermes remains the only scheduler.  Callers invoke these functions for one
already-admitted job and provide adapters for every external side effect.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


MAX_ACTIVE_WRITERS = 2
POLL_INTERVAL_SECONDS = 5 * 60
REVIEW_TIMEOUT_SECONDS = 30 * 60
NEEDS_INPUT = "needs_input"
AWAITING_REVIEW = "awaiting_review"
TASK_ID_FIELD = "task_id"
KANBAN_ID_FIELD = "kanban_id"
BRANCH_FIELD = "branch"
PULL_REQUEST_FIELD = "pr"
STATUS_FIELD = "status"


class BridgeError(RuntimeError):
    """The requested transition would violate the bridge contract."""


def start_job(
    *, job: Mapping[str, Any], gh: Any, kanban: Any, state_store: Any
) -> dict[str, int]:
    """Create or recover the GitHub identifiers for one admitted job."""

    _validate_admitted_job(job)
    task_id = job[TASK_ID_FIELD]
    card_id = job[KANBAN_ID_FIELD]
    existing = state_store.external_ids_for(task_id=task_id)
    if existing is not None:
        kanban.record_external_ids(card_id=card_id, **existing)
        return existing

    issue = gh.create_issue(feature_id=job["feature_id"], task_id=task_id)
    pull_request = gh.create_pull_request(
        branch=job[BRANCH_FIELD], issue=issue, draft=True
    )
    identifiers = {"issue": issue, PULL_REQUEST_FIELD: pull_request}
    state_store.compare_and_swap_task(
        expected_revision=job["state_revision"],
        task_id=task_id,
        **identifiers,
    )
    kanban.record_external_ids(card_id=card_id, **identifiers)
    return identifiers


def mark_ready(*, job: Mapping[str, Any], gh: Any, kanban: Any) -> None:
    """Move a tested contribution from draft to review wait."""

    gh.mark_pull_request_ready(pr=job[PULL_REQUEST_FIELD])
    kanban.set_status(card_id=job[KANBAN_ID_FIELD], status=AWAITING_REVIEW)


def poll_pull_request(
    *,
    job: Mapping[str, Any],
    gh: Any,
    kanban: Any,
    state_store: Any,
    clock: Any,
) -> dict[str, Any]:
    """Perform at most one due five-minute observation for a pull request."""

    now = clock.now()
    task_id = job[TASK_ID_FIELD]
    card_id = job[KANBAN_ID_FIELD]
    tracking = state_store.review_tracking(task_id=task_id)
    last_polled_at = tracking.get("last_polled_at")
    if (
        last_polled_at is not None
        and now - last_polled_at < POLL_INTERVAL_SECONDS
    ):
        return {STATUS_FIELD: AWAITING_REVIEW, "polled": False}

    pull_request = job[PULL_REQUEST_FIELD]
    observation = {
        STATUS_FIELD: AWAITING_REVIEW,
        "polled": True,
        "checks": gh.get_checks(pr=pull_request),
        "reviews": gh.get_reviews(pr=pull_request),
        "threads": gh.get_review_threads(pr=pull_request),
    }
    state_store.record_poll(task_id=task_id, polled_at=now)
    review_wait_seconds = now - tracking["review_wait_started_at"]
    if (
        not observation["reviews"]
        and review_wait_seconds >= REVIEW_TIMEOUT_SECONDS
    ):
        kanban.set_status(card_id=card_id, status=NEEDS_INPUT)
        state_store.set_status(task_id=task_id, status=NEEDS_INPUT)
        return {STATUS_FIELD: NEEDS_INPUT}
    return observation


def apply_review_correction(
    *,
    job: Mapping[str, Any],
    correction: Mapping[str, str],
    worker: Any,
    gh: Any,
    kanban: Any,
    state_store: Any,
    clock: Any,
) -> None:
    """Apply one requested correction and wait for a new review."""

    task_id = job[TASK_ID_FIELD]
    card_id = job[KANBAN_ID_FIELD]
    pull_request = job[PULL_REQUEST_FIELD]
    branch = job[BRANCH_FIELD]
    worker.apply_correction(branch=branch, instruction=correction["instruction"])
    gh.reply_to_review_thread(
        pr=pull_request,
        thread_id=correction["thread_id"],
        body=correction["reply"],
    )
    gh.request_new_review(pr=pull_request)
    kanban.set_status(card_id=card_id, status=AWAITING_REVIEW)
    state_store.restart_review_wait(
        task_id=task_id,
        branch=branch,
        started_at=clock.now(),
    )


def _validate_admitted_job(job: Mapping[str, Any]) -> None:
    expected_key = f"{job['feature_id']}:{job[TASK_ID_FIELD]}"
    if job["idempotency_key"] != expected_key:
        raise BridgeError("the idempotency key does not identify this job")
    if job["active_writer_count"] > MAX_ACTIVE_WRITERS:
        raise BridgeError("Hermes admitted more than two active writers")
    if job["runtime_contract_merged"] is not True:
        raise BridgeError("the runtime contract must be merged first")
    if job["synchronized_with_main"] is not True:
        raise BridgeError("the contribution must be synchronized with main")
