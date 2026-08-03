#!/usr/bin/env python3
"""Materialize one admitted SDD job without owning its scheduling lifecycle."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, Mapping


def _load_github_bridge():
    bridge_path = Path(__file__).with_name("sdd_github_bridge.py")
    if not bridge_path.is_file() or bridge_path.is_symlink():
        raise ImportError("the canonical SDD GitHub bridge is missing")
    module_name = "_sdd_job_github_bridge"
    existing = sys.modules.get(module_name)
    existing_file = getattr(existing, "__file__", None)
    if existing_file and Path(existing_file).resolve() == bridge_path.resolve():
        return existing
    spec = importlib.util.spec_from_file_location(module_name, bridge_path)
    if spec is None or spec.loader is None:
        raise ImportError("the canonical SDD GitHub bridge cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


github_bridge = _load_github_bridge()


SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TASK_ID = re.compile(r"^T-[0-9]{3}$")
FEATURE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
WORKTREE_ROOT = ".worktrees"


class JobExecutionError(RuntimeError):
    """An admitted job cannot be materialized without breaking isolation."""


class _ChildIssueGitHubAdapter:
    """Translate the canonical bridge calls to idempotent child resources."""

    def __init__(
        self,
        *,
        github: Any,
        parent_issue: int,
        idempotency_key: str,
    ) -> None:
        self.github = github
        self.parent_issue = parent_issue
        self.idempotency_key = idempotency_key

    def create_issue(self, *, feature_id: str, task_id: str) -> int:
        return self.github.ensure_child_issue(
            parent_issue=self.parent_issue,
            feature_id=feature_id,
            task_id=task_id,
            idempotency_key=self.idempotency_key,
        )

    def create_pull_request(self, *, branch: str, issue: int, draft: bool) -> int:
        return self.github.ensure_draft_pull_request(
            branch=branch,
            issue=issue,
            idempotency_key=self.idempotency_key,
            draft=draft,
        )


def _required_string(job: Mapping[str, object], field: str) -> str:
    value = job.get(field)
    if not isinstance(value, str) or not value:
        raise JobExecutionError(f"job {field} must be a non-empty string")
    return value


def _validated_job(job: object) -> tuple[dict[str, object], str, str]:
    if not isinstance(job, Mapping):
        raise JobExecutionError("job must be an object")
    validated = copy.deepcopy(dict(job))
    feature_id = _required_string(job, "feature_id")
    task_id = _required_string(job, "task_id")
    slug = _required_string(job, "slug")
    idempotency_key = _required_string(job, "idempotency_key")
    if FEATURE_ID.fullmatch(feature_id) is None:
        raise JobExecutionError("job feature_id is invalid")
    if TASK_ID.fullmatch(task_id) is None:
        raise JobExecutionError("job task_id is invalid")
    if SLUG.fullmatch(slug) is None:
        raise JobExecutionError("job slug is invalid")
    if idempotency_key != f"{feature_id}:{task_id}":
        raise JobExecutionError("job idempotency key does not match the task")
    parent_issue = job.get("parent_issue")
    if (
        not isinstance(parent_issue, int)
        or isinstance(parent_issue, bool)
        or parent_issue <= 0
    ):
        raise JobExecutionError("job parent_issue must be a positive integer")
    branch = f"sdd/{feature_id}/{task_id.lower()}-{slug}"
    worktree = str(PurePosixPath(WORKTREE_ROOT, f"{task_id.lower()}-{slug}"))
    return validated, branch, worktree


def _validated_external_id(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise JobExecutionError(f"{label} must be a positive integer")
    return value


def _ensure_local_surfaces(
    *,
    git: Any,
    hermes: Any,
    branch: str,
    worktree: str,
    idempotency_key: str,
) -> str:
    ensured_branch = git.ensure_branch(
        branch=branch,
        idempotency_key=idempotency_key,
    )
    if ensured_branch != branch:
        raise JobExecutionError("job key resolves to a different branch")
    ensured_worktree = git.ensure_worktree(
        path=worktree,
        branch=branch,
        idempotency_key=idempotency_key,
    )
    if ensured_worktree != worktree:
        raise JobExecutionError("job key resolves to a different worktree")
    session_id = hermes.ensure_session(
        idempotency_key=idempotency_key,
        worktree=worktree,
    )
    if not isinstance(session_id, str) or not session_id:
        raise JobExecutionError("Hermes session ID must be a non-empty string")
    return session_id


def _create_github_surfaces(
    *,
    job: Mapping[str, object],
    github: Any,
    kanban: Any,
    state_store: Any,
    branch: str,
    idempotency_key: str,
) -> tuple[int, int]:
    bridge_job = {**job, "branch": branch}
    bridge_github = _ChildIssueGitHubAdapter(
        github=github,
        parent_issue=int(job["parent_issue"]),
        idempotency_key=idempotency_key,
    )
    identifiers = github_bridge.start_job(
        job=bridge_job,
        gh=bridge_github,
        kanban=kanban,
        state_store=state_store,
    )
    issue = _validated_external_id(identifiers.get("issue"), "issue ID")
    pull_request = _validated_external_id(identifiers.get("pr"), "PR ID")
    return issue, pull_request


def materialize_job(
    *,
    job: object,
    git: Any,
    hermes: Any,
    github: Any,
    kanban: Any,
    state_store: Any,
    log: Any,
) -> dict[str, object]:
    """Create or recover every isolated surface for one already-admitted job."""

    validated, branch, worktree = _validated_job(job)
    feature_id = str(validated["feature_id"])
    task_id = str(validated["task_id"])
    idempotency_key = str(validated["idempotency_key"])
    existing = state_store.envelope_for(idempotency_key=idempotency_key)
    if existing is not None:
        log.record(event="job_recovered", task_id=task_id)
        return existing

    log.record(event="job_materialization_started", task_id=task_id)
    try:
        session_id = _ensure_local_surfaces(
            git=git,
            hermes=hermes,
            branch=branch,
            worktree=worktree,
            idempotency_key=idempotency_key,
        )
        issue, pull_request = _create_github_surfaces(
            job=validated,
            github=github,
            kanban=kanban,
            state_store=state_store,
            branch=branch,
            idempotency_key=idempotency_key,
        )
        envelope = {
            "idempotency_key": idempotency_key,
            "task_id": task_id,
            "branch": branch,
            "worktree": worktree,
            "session_id": session_id,
            "issue": issue,
            "pr": pull_request,
        }
        state_store.record_envelope(
            idempotency_key=idempotency_key,
            envelope=envelope,
        )
    except Exception as error:
        log.record(
            event="job_materialization_failed",
            task_id=task_id,
            error_type=type(error).__name__,
        )
        raise

    log.record(event="job_materialized", task_id=task_id)
    return envelope
