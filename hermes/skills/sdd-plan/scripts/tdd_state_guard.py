#!/usr/bin/env python3
"""Atomic compare-and-swap operations for SDD TDD state files."""

from __future__ import annotations

import argparse
import base64
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


def atomic_replace_with_mode(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def path_mode(path: Path, fallback: int) -> int:
    try:
        return stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        return fallback


def feature_paths(feature_dir: str) -> tuple[Path, Path, Path, Path, Path]:
    directory = Path(feature_dir).resolve()
    return (
        directory / ".tdd-state.lock",
        directory / ".tdd-state.json",
        directory / "03-design.md",
        directory / "04-tasks.md",
        directory / ".tdd-state.transaction.json",
    )


def encode_artifact(data: bytes | None, mode: int | None) -> dict:
    if data is None:
        return {"exists": False}
    return {
        "exists": True,
        "data_b64": base64.b64encode(data).decode("ascii"),
        "mode": mode,
    }


def decode_artifact(value: object, label: str) -> tuple[bytes | None, int | None]:
    if not isinstance(value, dict) or not isinstance(value.get("exists"), bool):
        raise GuardError(f"{label} is invalid")
    if not value["exists"]:
        return None, None
    encoded = value.get("data_b64")
    mode = value.get("mode")
    if not isinstance(encoded, str) or not isinstance(mode, int):
        raise GuardError(f"{label} is invalid")
    try:
        return base64.b64decode(encoded, validate=True), mode
    except ValueError as error:
        raise GuardError(f"{label} contains invalid base64") from error


def recover_transaction(
    state_path: Path,
    design_path: Path,
    tasks_path: Path,
    transaction_path: Path,
) -> str | None:
    transaction_data = read_bytes(transaction_path)
    if transaction_data is None:
        return None
    try:
        transaction = json.loads(transaction_data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GuardError(f"{transaction_path} is not valid JSON: {error}") from error
    if (
        not isinstance(transaction, dict)
        or transaction.get("version") != 1
        or transaction.get("operation") != "commit-plan"
    ):
        raise GuardError(f"{transaction_path} is not a supported transaction")
    expected_token = transaction.get("expected_state_token")
    target_token = transaction.get("target_state_token")
    if not isinstance(expected_token, str) or not isinstance(target_token, str):
        raise GuardError(f"{transaction_path} has invalid state tokens")
    if expected_token == target_token:
        raise GuardError(
            f"{transaction_path} is ambiguous because its state tokens are identical"
        )

    previous_data, previous_mode = decode_artifact(
        transaction.get("previous_design"), "previous_design"
    )
    next_data, next_mode = decode_artifact(
        transaction.get("next_design"), "next_design"
    )
    has_previous_tasks = "previous_tasks" in transaction
    has_next_tasks = "next_tasks" in transaction
    if has_previous_tasks != has_next_tasks:
        raise GuardError(f"{transaction_path} has incomplete task artifacts")
    legacy_tasks = not has_previous_tasks
    if has_previous_tasks:
        previous_tasks_data, previous_tasks_mode = decode_artifact(
            transaction.get("previous_tasks"), "previous_tasks"
        )
        next_tasks_data, next_tasks_mode = decode_artifact(
            transaction.get("next_tasks"), "next_tasks"
        )
    else:
        # Journals created before tasks joined the transaction never touched
        # 04-tasks.md. Leave the path itself untouched, including links and ACLs.
        previous_tasks_data = next_tasks_data = None
        previous_tasks_mode = next_tasks_mode = None
    current_token = token_for(read_bytes(state_path))
    if current_token == target_token:
        if (
            next_data is None
            or next_mode is None
            or (
                not legacy_tasks
                and (next_tasks_data is None or next_tasks_mode is None)
            )
        ):
            raise GuardError(f"{transaction_path} has incomplete target artifacts")
        atomic_replace_with_mode(design_path, next_data, next_mode)
        if next_tasks_data is not None and next_tasks_mode is not None:
            atomic_replace_with_mode(tasks_path, next_tasks_data, next_tasks_mode)
        outcome = "committed"
    elif current_token == expected_token:
        if previous_data is None:
            design_path.unlink(missing_ok=True)
        elif previous_mode is not None:
            atomic_replace_with_mode(design_path, previous_data, previous_mode)
        if not legacy_tasks:
            if previous_tasks_data is None:
                tasks_path.unlink(missing_ok=True)
            elif previous_tasks_mode is not None:
                atomic_replace_with_mode(
                    tasks_path, previous_tasks_data, previous_tasks_mode
                )
        outcome = "rolled-back"
    else:
        raise GuardError(
            "cannot recover plan transaction: state matches neither the expected "
            "nor the committed token"
        )
    fsync_directory(state_path.parent)
    transaction_path.unlink()
    fsync_directory(state_path.parent)
    return outcome


def snapshot(args: argparse.Namespace) -> None:
    lock_path, state_path, design_path, tasks_path, transaction_path = feature_paths(
        args.feature_dir
    )
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        recovery_outcome = recover_transaction(
            state_path, design_path, tasks_path, transaction_path
        )
        data = read_bytes(state_path)
    pristine = None
    if data is not None:
        state = parse_state(data, str(state_path))
        try:
            require_pristine(state, str(state_path))
            pristine = True
        except GuardError:
            pristine = False
    print(
        json.dumps(
            {
                "token": token_for(data),
                "pristine": pristine,
                "recovered": recovery_outcome is not None,
                "recovery_outcome": recovery_outcome,
            }
        )
    )


def commit_plan(args: argparse.Namespace) -> None:
    lock_path, state_path, design_path, tasks_path, transaction_path = feature_paths(
        args.feature_dir
    )
    design_candidate = Path(args.design_candidate).resolve()
    tasks_candidate = Path(args.tasks_candidate).resolve()
    state_candidate = Path(args.state_candidate).resolve()
    design_data = design_candidate.read_bytes()
    design_mode = stat.S_IMODE(design_candidate.stat().st_mode)
    if not design_data.strip():
        raise GuardError("approved design candidate is empty")
    tasks_data = tasks_candidate.read_bytes()
    tasks_mode = stat.S_IMODE(tasks_candidate.stat().st_mode)
    if not tasks_data.strip():
        raise GuardError("approved tasks candidate is empty")
    candidate_data = state_candidate.read_bytes()
    state_mode = stat.S_IMODE(state_candidate.stat().st_mode)
    candidate_state = parse_state(candidate_data, str(state_candidate))
    require_pristine(candidate_state, str(state_candidate))
    if candidate_state.get("feature_id") != state_path.parent.name:
        raise GuardError("candidate feature_id does not match the feature directory")

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        recovery_outcome = recover_transaction(
            state_path, design_path, tasks_path, transaction_path
        )
        if recovery_outcome == "committed":
            recovered_matches = (
                token_for(read_bytes(state_path)) == token_for(candidate_data)
                and read_bytes(design_path) == design_data
                and read_bytes(tasks_path) == tasks_data
            )
            if not recovered_matches:
                raise GuardError(
                    "recovered commit does not match the supplied plan candidates"
                )
            design_candidate.unlink(missing_ok=True)
            tasks_candidate.unlink(missing_ok=True)
            state_candidate.unlink(missing_ok=True)
            print(json.dumps({"token": token_for(candidate_data), "committed": True}))
            return
        current_data = read_bytes(state_path)
        current_token = token_for(current_data)
        if current_token != args.expected_token:
            committed_without_journal = (
                current_token == token_for(candidate_data)
                and read_bytes(design_path) == design_data
                and read_bytes(tasks_path) == tasks_data
            )
            if committed_without_journal:
                atomic_replace_with_mode(
                    design_path, design_data, path_mode(design_path, design_mode)
                )
                atomic_replace_with_mode(
                    tasks_path, tasks_data, path_mode(tasks_path, tasks_mode)
                )
                atomic_replace_with_mode(
                    state_path, candidate_data, path_mode(state_path, state_mode)
                )
                fsync_directory(state_path.parent)
                design_candidate.unlink(missing_ok=True)
                tasks_candidate.unlink(missing_ok=True)
                state_candidate.unlink(missing_ok=True)
                print(
                    json.dumps(
                        {"token": token_for(candidate_data), "committed": True}
                    )
                )
                return
            raise GuardError(
                f"state changed concurrently: expected {args.expected_token}, "
                f"found {current_token}"
            )
        if current_token == token_for(candidate_data):
            raise GuardError(
                "candidate state is identical to the current state; transaction "
                "recovery requires distinct state tokens"
            )
        if current_data is not None:
            require_pristine(parse_state(current_data, str(state_path)), str(state_path))

        previous_design = read_bytes(design_path)
        previous_design_mode = (
            path_mode(design_path, design_mode) if previous_design is not None else None
        )
        target_design_mode = path_mode(design_path, design_mode)
        previous_tasks = read_bytes(tasks_path)
        previous_tasks_mode = (
            path_mode(tasks_path, tasks_mode) if previous_tasks is not None else None
        )
        target_tasks_mode = path_mode(tasks_path, tasks_mode)
        target_state_mode = path_mode(state_path, state_mode)
        transaction = {
            "version": 1,
            "operation": "commit-plan",
            "expected_state_token": current_token,
            "target_state_token": token_for(candidate_data),
            "previous_design": encode_artifact(previous_design, previous_design_mode),
            "next_design": encode_artifact(design_data, target_design_mode),
            "previous_tasks": encode_artifact(previous_tasks, previous_tasks_mode),
            "next_tasks": encode_artifact(tasks_data, target_tasks_mode),
        }
        transaction_data = json.dumps(transaction, sort_keys=True).encode("utf-8")
        transaction_written = False
        try:
            atomic_replace(transaction_path, transaction_data, 0o600)
            fsync_directory(state_path.parent)
            transaction_written = True
            atomic_replace_with_mode(design_path, design_data, target_design_mode)
            fsync_directory(state_path.parent)
            atomic_replace_with_mode(tasks_path, tasks_data, target_tasks_mode)
            fsync_directory(state_path.parent)
            atomic_replace_with_mode(state_path, candidate_data, target_state_mode)
            fsync_directory(state_path.parent)
            transaction_path.unlink()
            fsync_directory(state_path.parent)
            transaction_written = False
        except Exception:
            recovery_outcome = None
            if transaction_written:
                recovery_outcome = recover_transaction(
                    state_path, design_path, tasks_path, transaction_path
                )
            if recovery_outcome != "committed":
                raise

    design_candidate.unlink(missing_ok=True)
    tasks_candidate.unlink(missing_ok=True)
    state_candidate.unlink(missing_ok=True)

    print(json.dumps({"token": token_for(candidate_data), "committed": True}))


def write_state(args: argparse.Namespace) -> None:
    lock_path, state_path, design_path, tasks_path, transaction_path = feature_paths(
        args.feature_dir
    )
    candidate_path = Path(args.state_candidate).resolve()
    candidate_data = candidate_path.read_bytes()
    candidate_mode = stat.S_IMODE(candidate_path.stat().st_mode)
    candidate_state = parse_state(candidate_data, str(candidate_path))
    if candidate_state.get("feature_id") != state_path.parent.name:
        raise GuardError("candidate feature_id does not match the feature directory")

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        recover_transaction(state_path, design_path, tasks_path, transaction_path)
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
    commit_command.add_argument("--tasks-candidate", required=True)
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
