#!/usr/bin/env python3
"""Single-pass admission of parallel SDD jobs into the native Hermes Kanban."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


def _load_runtime():
    runtime_path = Path(__file__).with_name("sdd_runtime_guard.py")
    if not runtime_path.is_file() or runtime_path.is_symlink():
        raise ImportError("the canonical SDD runtime is missing")
    module_name = "_sdd_parallel_runtime_guard"
    existing = sys.modules.get(module_name)
    existing_file = getattr(existing, "__file__", None)
    if existing_file and Path(existing_file).resolve() == runtime_path.resolve():
        return existing
    spec = importlib.util.spec_from_file_location(module_name, runtime_path)
    if spec is None or spec.loader is None:
        raise ImportError("the canonical SDD runtime cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runtime = _load_runtime()


DEFAULT_MAX_WORKERS = 2
MAX_WORKERS = 2
MAX_RUNTIME = "45m"
LEASE_TTL_SECONDS = 45 * 60
MAX_RETRIES = 2
BUILD_SKILL = "sdd-build"
FAILED_STATUS = "failed"
PARALLEL_FLAG = "--parallel"
MAX_WORKERS_FLAG = "--max-workers"
MERGE_BARRIER_TASK = "T-009"


class BuildOrchestratorError(RuntimeError):
    """Parallel admission would violate the SDD orchestration contract."""


def parse_parallel_arguments(argv: Sequence[str]) -> dict[str, object]:
    """Validate the exact parallel command form without shell parsing."""

    if isinstance(argv, (str, bytes)):
        raise BuildOrchestratorError("parallel build arguments must be structured argv")
    arguments = list(argv)
    if len(arguments) not in {2, 4} or arguments[1] != PARALLEL_FLAG:
        raise BuildOrchestratorError(
            "usage: /sdd-build <feature-id> --parallel [--max-workers 1|2]"
        )
    feature_id = arguments[0]
    if not isinstance(feature_id, str) or runtime.FEATURE_ID.fullmatch(feature_id) is None:
        raise BuildOrchestratorError(f"invalid feature ID: {feature_id!r}")
    maximum = DEFAULT_MAX_WORKERS
    if len(arguments) == 4:
        allowed_worker_counts = {str(value) for value in range(1, MAX_WORKERS + 1)}
        if (
            arguments[2] != MAX_WORKERS_FLAG
            or arguments[3] not in allowed_worker_counts
        ):
            raise BuildOrchestratorError("--max-workers must be 1 or 2")
        maximum = int(arguments[3])
    return {"feature_id": feature_id, "max_workers": maximum}


def _dependencies_are_merged(
    task: Mapping[str, object],
    tasks: Mapping[str, Mapping[str, object]],
    merged_tasks: set[str],
) -> bool:
    dependencies = task["dependencies"]
    assert isinstance(dependencies, list)
    return all(
        dependency in merged_tasks
        and tasks[dependency]["phase"] == "done"
        and tasks[dependency]["status"] == "done"
        for dependency in dependencies
    )


def _scopes_overlap(left: Sequence[str], right: Sequence[str]) -> bool:
    return any(
        runtime.paths_overlap(left_path, right_path)
        for left_path in left
        for right_path in right
    )


def _select_wave(
    tasks: Mapping[str, Mapping[str, object]], merged_tasks: set[str]
) -> tuple[list[str], list[str]]:
    admitted: list[str] = []
    serialized: list[str] = []
    admitted_scopes: list[list[str]] = []
    for task_id in sorted(tasks):
        task = tasks[task_id]
        if task["phase"] != "pending" or task["status"] not in {"pending", "ready"}:
            continue
        scope = task["files_in_scope"]
        assert isinstance(scope, list)
        if any(_scopes_overlap(scope, existing) for existing in admitted_scopes):
            serialized.append(task_id)
            continue
        if not _dependencies_are_merged(task, tasks, merged_tasks):
            continue
        admitted.append(task_id)
        admitted_scopes.append(scope)
    return admitted, serialized


def _card_metadata(
    *,
    feature_id: str,
    task_id: str,
    task: Mapping[str, object],
    state: Mapping[str, object],
    parent_card_id: str,
) -> dict[str, object]:
    branch = task.get("branch")
    if not isinstance(branch, str) or not branch:
        branch = f"sdd/{feature_id}/{task_id.lower()}"
    return {
        "feature_id": feature_id,
        "task_id": task_id,
        "project": state["project"],
        "board": state["board"],
        "parent_card_id": parent_card_id,
        "branch": branch,
        "idempotency_key": f"{feature_id}:{task_id}",
        "skill": BUILD_SKILL,
        "max_runtime": MAX_RUNTIME,
        "retries": MAX_RETRIES,
    }


def _dispatch_admitted_card(
    *,
    root: Path,
    feature_id: str,
    task_id: str,
    task: Mapping[str, object],
    state: Mapping[str, object],
    card_id: str,
    kanban: Any,
    owner: str,
    session_id: str,
) -> dict[str, str] | None:
    job_session_id = f"{session_id}-{task_id.lower()}"
    lease = runtime.acquire_scope_lease(
        root,
        feature_id=feature_id,
        task_id=task_id,
        owner=owner,
        session_id=job_session_id,
        files_in_scope=task["files_in_scope"],
        state=state,
        ttl_seconds=LEASE_TTL_SECONDS,
    )
    lease_id = str(lease["lease_id"])
    try:
        kanban.dispatch(card_id=card_id, lease_id=lease_id)
    except Exception:
        runtime.release_scope_lease(
            root,
            lease_id=lease_id,
            owner=owner,
            session_id=job_session_id,
        )
        kanban.set_status(card_id=card_id, status=FAILED_STATUS)
        return None
    return {"task_id": task_id, "card_id": card_id, "lease_id": lease_id}


def admit_parallel_wave(
    *,
    repo_root: Path | str,
    argv: Sequence[str],
    state: object,
    kanban: Any,
    parent_card_id: str,
    owner: str,
    session_id: str,
    merged_tasks: set[str],
) -> dict[str, object]:
    """Create one deterministic wave and hand each runnable card to Hermes."""

    parsed = parse_parallel_arguments(argv)
    feature_id = str(parsed["feature_id"])
    maximum = int(parsed["max_workers"])
    if MERGE_BARRIER_TASK not in merged_tasks:
        raise BuildOrchestratorError("T-009 must be observed merged before parallel build")

    root = runtime.repository_root(repo_root)
    execution_state = copy.deepcopy(state)
    if not isinstance(execution_state, dict):
        raise BuildOrchestratorError("state must be an object")
    execution_state["mode"] = "parallel"
    execution_state["max_workers"] = maximum
    validated = runtime.validate_state(
        execution_state,
        repo_root=root,
        allow_legacy=False,
    )
    if validated["feature_id"] != feature_id:
        raise BuildOrchestratorError("parallel arguments do not match state feature_id")
    tasks = validated["tasks"]
    assert isinstance(tasks, dict)
    barrier = tasks.get(MERGE_BARRIER_TASK)
    if not isinstance(barrier, dict) or (
        barrier.get("phase"), barrier.get("status")
    ) != ("done", "done"):
        raise BuildOrchestratorError("T-009 must be done and merged before parallel build")

    admitted, serialized = _select_wave(tasks, merged_tasks)
    queued: list[str] = []
    failed: list[str] = []
    active: list[dict[str, str]] = []
    for task_id in admitted:
        task = tasks[task_id]
        metadata = _card_metadata(
            feature_id=feature_id,
            task_id=task_id,
            task=task,
            state=validated,
            parent_card_id=parent_card_id,
        )
        card_id = kanban.create_card(**metadata)
        if len(active) >= maximum:
            queued.append(task_id)
            continue
        active_job = _dispatch_admitted_card(
            root=root,
            feature_id=feature_id,
            task_id=task_id,
            task=task,
            state=validated,
            card_id=card_id,
            kanban=kanban,
            owner=owner,
            session_id=session_id,
        )
        if active_job is None:
            failed.append(task_id)
            continue
        active.append(active_job)

    return {
        "admitted_task_ids": admitted,
        "serialized_task_ids": serialized,
        "queued_task_ids": queued,
        "failed_task_ids": failed,
        "active_jobs": active,
    }
