#!/usr/bin/env python3
"""Observe human gates and synthesize one completed SDD wave transactionally."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


AWAITING_GO = "awaiting_go"
DONE = "done"
AWAITING_FAN_IN_MERGE = "awaiting_fan_in_merge"
SYNTHESIZER = "synthesizer"
SHARED_ARTIFACTS = (
    "04-tasks.md",
    ".tdd-state.json",
    "05-implementation-log.md",
)


class WaveSynthesisError(RuntimeError):
    """The wave cannot advance without violating its human or atomic gate."""


def observe_job_gate(*, job: Mapping[str, object], kanban: Any) -> dict[str, str]:
    """Record technical readiness without inferring human authorization."""

    required = ("pr_ready", "checks_green", "review_approved")
    if any(job.get(field) is not True for field in required):
        raise WaveSynthesisError("job technical gates are incomplete")
    card_id = job.get("card_id")
    if not isinstance(card_id, str) or not card_id:
        raise WaveSynthesisError("job card_id is required")
    kanban.set_status(card_id=card_id, status=AWAITING_GO)
    return {"status": AWAITING_GO}


def observe_human_merge(
    *,
    job: Mapping[str, object],
    human_gate: Any,
    github: Any,
    kanban: Any,
    state_store: Any,
) -> bool:
    """Mark only an explicitly approved contribution already merged by a human."""

    task_id = job.get("task_id")
    card_id = job.get("card_id")
    pull_request = job.get("pr")
    if not isinstance(task_id, str) or not isinstance(card_id, str):
        raise WaveSynthesisError("job task and card identifiers are required")
    if not isinstance(pull_request, int) or isinstance(pull_request, bool):
        raise WaveSynthesisError("job PR identifier is required")
    if not human_gate.explicitly_approved(task_id=task_id, pr=pull_request):
        return False
    if not github.is_merged(pr=pull_request):
        return False
    kanban.set_status(card_id=card_id, status=DONE)
    state_store.set_status(task_id=task_id, status=DONE)
    return True


def _validated_wave(wave: object) -> tuple[str, str, list[Mapping[str, object]]]:
    if not isinstance(wave, Mapping):
        raise WaveSynthesisError("wave must be an object")
    wave_id = wave.get("wave_id")
    feature_id = wave.get("feature_id")
    jobs = wave.get("jobs")
    if not isinstance(wave_id, str) or not wave_id:
        raise WaveSynthesisError("wave_id is required")
    if not isinstance(feature_id, str) or not feature_id:
        raise WaveSynthesisError("feature_id is required")
    if not isinstance(jobs, list) or not jobs or any(
        not isinstance(job, Mapping) for job in jobs
    ):
        raise WaveSynthesisError("wave jobs must be a non-empty object list")
    return wave_id, feature_id, jobs


def _validate_shared_artifacts(
    feature_id: str, artifacts: Mapping[str, bytes]
) -> None:
    expected = {f".specs/{feature_id}/{name}" for name in SHARED_ARTIFACTS}
    if set(artifacts) != expected:
        raise WaveSynthesisError("fan-in must update exactly the three shared artifacts")


def commit_fan_in(
    *,
    repo_root: Path | str,
    feature_id: str,
    transaction_id: str,
    artifacts: Mapping[str, bytes],
    expected_tokens: Mapping[str, str],
    runtime: Any,
    crash_point: str | None = None,
) -> dict[str, object]:
    """Delegate the only shared-artifact write to the canonical runtime."""

    _validate_shared_artifacts(feature_id, artifacts)
    arguments: dict[str, object] = {
        "feature_id": feature_id,
        "transaction_id": transaction_id,
        "actor": SYNTHESIZER,
        "artifacts": artifacts,
        "expected_tokens": expected_tokens,
    }
    if crash_point is not None:
        arguments["_crash_point"] = crash_point
    return runtime.transactional_fan_in(repo_root, **arguments)


def _ensure_fan_in_pr(
    *,
    wave_id: str,
    feature_id: str,
    github: Any,
    state_store: Any,
) -> int:
    pull_request = state_store.fan_in_pr_for(wave_id=wave_id)
    if pull_request is not None:
        return pull_request
    pull_request = github.ensure_fan_in_pull_request(
        wave_id=wave_id,
        branch=f"sdd/{feature_id}/fan-in-{wave_id}",
        idempotency_key=f"{feature_id}:{wave_id}:fan-in",
        draft=True,
    )
    state_store.record_fan_in_pr(wave_id=wave_id, pr=pull_request)
    return pull_request


def synthesize_wave(
    *,
    repo_root: Path | str,
    wave: object,
    artifacts: Mapping[str, bytes],
    expected_tokens: Mapping[str, str],
    runtime: Any,
    github: Any,
    kanban: Any,
    state_store: Any,
) -> dict[str, object]:
    """Verify a completed wave, commit its artifacts, and ensure one fan-in PR."""

    wave_id, feature_id, jobs = _validated_wave(wave)
    if any(job.get("status") != DONE for job in jobs):
        raise WaveSynthesisError("all wave cards must be done before fan-in")
    for job in jobs:
        task_id = job.get("task_id")
        if not isinstance(task_id, str):
            raise WaveSynthesisError("wave job task_id is required")
        event_count = runtime.verify_job_journal(
            repo_root,
            feature_id=feature_id,
            task_id=task_id,
        )
        if not isinstance(event_count, int) or event_count <= 0:
            raise WaveSynthesisError(f"job journal is empty: {task_id}")

    transaction_id = f"{wave_id}-fan-in"
    transaction = commit_fan_in(
        repo_root=repo_root,
        feature_id=feature_id,
        transaction_id=transaction_id,
        artifacts=artifacts,
        expected_tokens=expected_tokens,
        runtime=runtime,
    )
    pull_request = _ensure_fan_in_pr(
        wave_id=wave_id,
        feature_id=feature_id,
        github=github,
        state_store=state_store,
    )
    kanban.set_wave_status(wave_id=wave_id, status=AWAITING_FAN_IN_MERGE)
    return {"pr": pull_request, "transaction": transaction}


def next_wave_admissible(*, wave_id: str, github: Any, state_store: Any) -> bool:
    """Open the next wave only after observing the fan-in PR merged elsewhere."""

    pull_request = state_store.fan_in_pr_for(wave_id=wave_id)
    if pull_request is None:
        return False
    return github.is_merged(pr=pull_request)
