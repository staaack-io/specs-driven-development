#!/usr/bin/env python3

"""Render the task-local fields proved by an SDD state."""

import json
from pathlib import Path


MISSING_VALUE = "—"
TASK_LOCAL_FIELDS = (
    "issue",
    "branch",
    "pr",
    "checks",
    "review",
    "blocking",
    "next_action",
)


def task_local_rows(state: dict[str, object]) -> list[dict[str, object]]:
    """Return task-local status rows without deriving missing evidence."""
    tasks = state.get("tasks", {})
    if not isinstance(tasks, dict):
        return []

    rows = []
    for task_id in sorted(tasks):
        task = tasks[task_id]
        if not isinstance(task, dict):
            continue
        row = {"task_id": task_id}
        for field in TASK_LOCAL_FIELDS:
            row[field] = task.get(field, MISSING_VALUE)
        rows.append(row)
    return rows


def task_local_rows_from_file(state_path: Path) -> list[dict[str, object]]:
    """Read an SDD state without modifying the repository."""
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        return []
    return task_local_rows(state)
