#!/usr/bin/env python3
"""Atomic compare-and-swap operations for SDD TDD state files."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile


PROOF_FIELDS = (
    "red_at",
    "red_test_signature",
    "red_failure_excerpt",
    "green_at",
)


class GuardError(RuntimeError):
    pass


def read_bytes(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def token_for(data: bytes | None) -> str:
    if data is None:
        return "absent"
    return "sha256:" + hashlib.sha256(data).hexdigest()


def parse_state(data: bytes, label: str) -> dict:
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GuardError(f"{label} is not valid JSON: {error}") from error
    if not isinstance(value, dict) or not isinstance(value.get("tasks"), dict):
        raise GuardError(f"{label} must be an object with a tasks object")
    if not value["tasks"]:
        raise GuardError(f"{label} must contain at least one task")
    return value


def require_pristine(state: dict, label: str) -> None:
    if state.get("active_task") is not None:
        raise GuardError(f"{label} has an active task")
    for task_id, task in state["tasks"].items():
        if not isinstance(task, dict):
            raise GuardError(f"{label} task {task_id} is not an object")
        if task.get("phase") != "pending":
            raise GuardError(f"{label} task {task_id} is not pending")
        for field in PROOF_FIELDS:
            if task.get(field) is not None:
                raise GuardError(f"{label} task {task_id} contains {field}")


def atomic_replace(path: Path, data: bytes, fallback_mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        artifact_mode = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        artifact_mode = fallback_mode
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, artifact_mode)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def feature_paths(feature_dir: str) -> tuple[Path, Path, Path]:
    directory = Path(feature_dir).resolve()
    return (
        directory / ".tdd-state.lock",
        directory / ".tdd-state.json",
        directory / "03-design.md",
    )


def snapshot(args: argparse.Namespace) -> None:
    _, state_path, _ = feature_paths(args.feature_dir)
    data = read_bytes(state_path)
    pristine = None
    if data is not None:
        state = parse_state(data, str(state_path))
        try:
            require_pristine(state, str(state_path))
            pristine = True
        except GuardError:
            pristine = False
    print(json.dumps({"token": token_for(data), "pristine": pristine}))


def commit_plan(args: argparse.Namespace) -> None:
    lock_path, state_path, design_path = feature_paths(args.feature_dir)
    design_candidate = Path(args.design_candidate).resolve()
    state_candidate = Path(args.state_candidate).resolve()
    design_data = design_candidate.read_bytes()
    design_mode = stat.S_IMODE(design_candidate.stat().st_mode)
    if not design_data.strip():
        raise GuardError("approved design candidate is empty")
    candidate_data = state_candidate.read_bytes()
    state_mode = stat.S_IMODE(state_candidate.stat().st_mode)
    candidate_state = parse_state(candidate_data, str(state_candidate))
    require_pristine(candidate_state, str(state_candidate))
    if candidate_state.get("feature_id") != state_path.parent.name:
        raise GuardError("candidate feature_id does not match the feature directory")

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        current_data = read_bytes(state_path)
        current_token = token_for(current_data)
        if current_token != args.expected_token:
            raise GuardError(
                f"state changed concurrently: expected {args.expected_token}, "
                f"found {current_token}"
            )
        if current_data is not None:
            require_pristine(parse_state(current_data, str(state_path)), str(state_path))

        previous_design = read_bytes(design_path)
        atomic_replace(design_path, design_data, design_mode)
        try:
            atomic_replace(state_path, candidate_data, state_mode)
        except Exception:
            if previous_design is None:
                design_path.unlink(missing_ok=True)
            else:
                atomic_replace(design_path, previous_design)
            raise

    design_candidate.unlink(missing_ok=True)
    state_candidate.unlink(missing_ok=True)

    print(json.dumps({"token": token_for(candidate_data), "committed": True}))


def write_state(args: argparse.Namespace) -> None:
    lock_path, state_path, _ = feature_paths(args.feature_dir)
    candidate_path = Path(args.state_candidate).resolve()
    candidate_data = candidate_path.read_bytes()
    candidate_mode = stat.S_IMODE(candidate_path.stat().st_mode)
    candidate_state = parse_state(candidate_data, str(candidate_path))
    if candidate_state.get("feature_id") != state_path.parent.name:
        raise GuardError("candidate feature_id does not match the feature directory")

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        current_token = token_for(read_bytes(state_path))
        if current_token != args.expected_token:
            raise GuardError(
                f"state changed concurrently: expected {args.expected_token}, "
                f"found {current_token}"
            )
        atomic_replace(state_path, candidate_data, candidate_mode)

    print(json.dumps({"token": token_for(candidate_data), "committed": True}))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    commands = root.add_subparsers(dest="command", required=True)

    snapshot_command = commands.add_parser("snapshot")
    snapshot_command.add_argument("--feature-dir", required=True)
    snapshot_command.set_defaults(handler=snapshot)

    commit_command = commands.add_parser("commit-plan")
    commit_command.add_argument("--feature-dir", required=True)
    commit_command.add_argument("--expected-token", required=True)
    commit_command.add_argument("--design-candidate", required=True)
    commit_command.add_argument("--state-candidate", required=True)
    commit_command.set_defaults(handler=commit_plan)

    write_command = commands.add_parser("write-state")
    write_command.add_argument("--feature-dir", required=True)
    write_command.add_argument("--expected-token", required=True)
    write_command.add_argument("--state-candidate", required=True)
    write_command.set_defaults(handler=write_state)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        args.handler(args)
    except (GuardError, OSError) as error:
        print(json.dumps({"committed": False, "error": str(error)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
