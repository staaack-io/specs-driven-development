#!/usr/bin/env python3
"""Deterministic, sequential RED-to-SIMPLIFY orchestration for ``/sdd-build``."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Callable, Mapping, Sequence, TypedDict


RUNTIME_PATH = Path("hermes/runtime/sdd_runtime_guard.py")
ORCHESTRATOR_PATH = Path("hermes/runtime/sdd_build_orchestrator.py")


def _load_runtime():
    """Load the shared runtime from source or distributed profile layout."""

    script = Path(__file__).resolve(strict=True)
    for root in script.parents:
        runtime_path = root / RUNTIME_PATH
        protected = (root / "hermes", root / "hermes/runtime", runtime_path)
        symbolic_path = next((path for path in protected if path.is_symlink()), None)
        if not runtime_path.is_file() or symbolic_path is not None:
            continue
        resolved_root = root.resolve(strict=True)
        resolved_runtime = runtime_path.resolve(strict=True)
        try:
            resolved_runtime.relative_to(resolved_root)
        except ValueError:
            continue
        module_name = "_sdd_build_runtime_guard"
        existing = sys.modules.get(module_name)
        existing_file = getattr(existing, "__file__", None)
        if existing_file and Path(existing_file).resolve() == resolved_runtime:
            return existing
        spec = importlib.util.spec_from_file_location(module_name, resolved_runtime)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    raise ImportError("shared Hermes runtime is missing from the skill layout")


runtime = _load_runtime()


def _load_orchestrator():
    """Load parallel admission from the same verified source/profile root."""

    script = Path(__file__).resolve(strict=True)
    for root in script.parents:
        orchestrator_path = root / ORCHESTRATOR_PATH
        protected = (root / "hermes", root / "hermes/runtime", orchestrator_path)
        symbolic_path = next((path for path in protected if path.is_symlink()), None)
        if not orchestrator_path.is_file() or symbolic_path is not None:
            continue
        resolved_root = root.resolve(strict=True)
        resolved_orchestrator = orchestrator_path.resolve(strict=True)
        try:
            resolved_orchestrator.relative_to(resolved_root)
        except ValueError:
            continue
        module_name = "_sdd_build_orchestrator"
        existing = sys.modules.get(module_name)
        existing_file = getattr(existing, "__file__", None)
        if existing_file and Path(existing_file).resolve() == resolved_orchestrator:
            return existing
        spec = importlib.util.spec_from_file_location(module_name, resolved_orchestrator)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    raise ImportError("parallel build orchestrator is missing from the skill layout")


orchestrator = _load_orchestrator()


RED_PHASE = "RED"
PHASES = (RED_PHASE, "GREEN", "REFACTOR", "SIMPLIFY")
SPRING_ROLES = ("spring-test-engineer", "spring-implementer")
REACT_ROLES = ("react-nextjs-test-engineer", "react-nextjs-implementer")
REQUIRED_RED_FIELDS = (
    "test_signature",
    "argv",
    "returncode",
    "expected_failure",
    "output",
)


class TaskContract(TypedDict):
    """Validated task data shared by the injected and runtime entry points."""

    test_ids: list[str]
    test_files: list[str]
    production_files: list[str]
    test_argv: list[str]


BuildGuardError = runtime.GuardError


def parse_build_arguments(argv: Sequence[str]) -> dict[str, object]:
    """Select the sequential task or parallel admission command contract."""

    if not isinstance(argv, (str, bytes)) and len(argv) >= 2 and argv[1] == "--parallel":
        return {"mode": "parallel", **orchestrator.parse_parallel_arguments(argv)}
    if isinstance(argv, (str, bytes)) or len(argv) != 2:
        raise BuildGuardError(
            "usage: /sdd-build <feature-id> <T-NNN> | "
            "<feature-id> --parallel [--max-workers 1|2]"
        )
    feature_id = _identifier(argv[0], runtime.FEATURE_ID, "feature ID")
    task_id = _identifier(argv[1], runtime.TASK_ID, "task ID")
    return {"mode": "sequential", "feature_id": feature_id, "task_id": task_id}


def run_parallel_build(**arguments: object) -> dict[str, object]:
    """Hand one admission pass to the canonical Hermes orchestrator."""

    return orchestrator.admit_parallel_wave(**arguments)


def _identifier(value: object, pattern: re.Pattern[str], label: str) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise BuildGuardError(f"invalid {label}: {value!r}")
    return value


def _string_list(
    value: object, label: str, *, allow_empty: bool = False
) -> list[str]:
    error_message = f"{label} must be a non-empty string list"
    if not isinstance(value, list):
        raise BuildGuardError(error_message)
    if not value and not allow_empty:
        raise BuildGuardError(error_message)
    if any(not isinstance(item, str) or not item for item in value):
        raise BuildGuardError(error_message)
    return list(value)


def _validated_command(value: object) -> list[str]:
    if not isinstance(value, list):
        raise BuildGuardError("command must use structured argv")
    command = runtime.validate_command_arguments(value)
    if not command:
        raise BuildGuardError("command argv must not be empty")
    return command


def _validated_paths(
    value: object, label: str, *, allow_empty: bool = False
) -> list[str]:
    paths = _string_list(value, label, allow_empty=allow_empty)
    return [runtime.normalize_scope_path(path) for path in paths]


def _role_pair(stack_evidence: object) -> tuple[str, str]:
    if not isinstance(stack_evidence, Mapping):
        raise BuildGuardError("stack evidence must be an object")
    modules = stack_evidence.get("modules")
    if not isinstance(modules, list) or not modules:
        raise BuildGuardError("stack evidence must contain proved modules")
    kinds = {
        module.get("kind")
        for module in modules
        if isinstance(module, Mapping) and isinstance(module.get("kind"), str)
    }
    if kinds == {"spring"}:
        return SPRING_ROLES
    if kinds and kinds <= {"react", "nextjs"}:
        return REACT_ROLES
    raise BuildGuardError("stack evidence is unsupported or ambiguous")


def _redact(text: str) -> str:
    redacted = text
    for pattern in runtime.SECRET_VALUE_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _validated_changed_files(
    result: Mapping[str, object], phase: str, allowed_files: set[str]
) -> list[str]:
    changed = _validated_paths(
        result.get("files_changed"),
        f"{phase} files_changed",
        allow_empty=True,
    )
    shared_change = any(
        PurePosixPath(path).name in runtime.SHARED_ARTIFACTS for path in changed
    )
    if shared_change:
        raise BuildGuardError("delegated role reported a shared artifact change")
    if not set(changed) <= allowed_files:
        raise BuildGuardError(f"{phase} reported a file outside its delegated scope")
    return changed


def _phase_event(
    phase: str, test_ids: list[str], evidence: Mapping[str, object]
) -> dict[str, object]:
    return {
        "phase": phase,
        "test_ids": copy.deepcopy(test_ids),
        **evidence,
    }


def _validate_result(
    result: object,
    *,
    phase: str,
    allowed_files: set[str],
) -> dict[str, object]:
    if not isinstance(result, Mapping):
        raise BuildGuardError(f"{phase} result must be an object")
    if phase == RED_PHASE:
        missing = [field for field in REQUIRED_RED_FIELDS if field not in result]
        if missing:
            raise BuildGuardError(f"RED proof is incomplete: missing {', '.join(missing)}")

    command = _validated_command(result.get("argv"))
    returncode = result.get("returncode")
    output = result.get("output")
    if not isinstance(returncode, int) or isinstance(returncode, bool):
        raise BuildGuardError(f"{phase} returncode must be an integer")
    if not isinstance(output, str):
        raise BuildGuardError(f"{phase} output must be a string")
    changed = _validated_changed_files(result, phase, allowed_files)
    if phase == RED_PHASE:
        signature = result.get("test_signature")
        expected = result.get("expected_failure")
        if not isinstance(signature, str) or not signature.strip():
            raise BuildGuardError("RED proof requires a test signature")
        if not isinstance(expected, str) or not expected.strip():
            raise BuildGuardError("RED proof requires an expected failure")
        if returncode == 0:
            raise BuildGuardError("RED proof requires a failing test command")
    elif returncode != 0:
        raise BuildGuardError(f"{phase} must keep the tests green")

    evidence: dict[str, object] = {
        "argv": command,
        "returncode": returncode,
        "output": _redact(output),
        "files_changed": changed,
    }
    if phase == RED_PHASE:
        evidence["test_signature"] = result["test_signature"]
        evidence["expected_failure"] = _redact(str(result["expected_failure"]))
    return evidence


def _validate_inputs(
    argv: Sequence[str], task: object, stack_evidence: object
) -> tuple[str, str, TaskContract, tuple[str, str]]:
    if isinstance(argv, (str, bytes)) or len(argv) != 2:
        raise BuildGuardError("usage: /sdd-build <feature-id> <T-NNN>")
    feature_id = _identifier(argv[0], runtime.FEATURE_ID, "feature ID")
    task_id = _identifier(argv[1], runtime.TASK_ID, "task ID")
    if not isinstance(task, Mapping) or task.get("task_id") != task_id:
        raise BuildGuardError("task contract does not match the requested task")
    test_ids = _string_list(task.get("test_ids"), "test_ids")
    if any(runtime.TEST_ID.fullmatch(test_id) is None for test_id in test_ids):
        raise BuildGuardError("task contract contains an invalid Test-ID")
    test_files = _validated_paths(task.get("test_files"), "test_files")
    production_files = _validated_paths(task.get("production_files"), "production_files")
    if set(test_files) & set(production_files):
        raise BuildGuardError("test and production scopes must be disjoint")
    contract: TaskContract = {
        "test_ids": test_ids,
        "test_files": test_files,
        "production_files": production_files,
        "test_argv": _validated_command(task.get("test_argv")),
    }
    return feature_id, task_id, contract, _role_pair(stack_evidence)


def run_single_task(
    *,
    argv: Sequence[str],
    task: Mapping[str, object],
    stack_evidence: Mapping[str, object],
    role_executor: Callable[..., Mapping[str, object]],
    event_writer: Callable[..., bool],
) -> dict[str, object]:
    """Run exactly one proved task through all four ordered TDD phases."""

    _, task_id, contract, roles = _validate_inputs(argv, task, stack_evidence)
    test_ids = contract["test_ids"]
    test_files = contract["test_files"]
    production_files = contract["production_files"]
    test_argv = contract["test_argv"]

    red_context = {
        "task_id": task_id,
        "test_ids": copy.deepcopy(test_ids),
        "files_in_scope": copy.deepcopy(test_files),
        "test_argv": copy.deepcopy(test_argv),
    }
    red_result = role_executor(role=roles[0], phase=RED_PHASE, context=red_context)
    red_proof = _validate_result(
        red_result,
        phase=RED_PHASE,
        allowed_files=set(test_files),
    )
    red_event = _phase_event(RED_PHASE, test_ids, red_proof)
    if event_writer(event_id=f"{task_id.lower()}-red", event=red_event) is not True:
        raise BuildGuardError("durable RED evidence is required before production")

    for phase in PHASES[1:]:
        context = {
            "task_id": task_id,
            "test_ids": copy.deepcopy(test_ids),
            "files_in_scope": copy.deepcopy(production_files),
            "test_argv": copy.deepcopy(test_argv),
            "red_proof": copy.deepcopy(red_event),
        }
        result = role_executor(role=roles[1], phase=phase, context=context)
        proof = _validate_result(
            result,
            phase=phase,
            allowed_files=set(production_files),
        )
        event = _phase_event(phase, test_ids, proof)
        event_id = f"{task_id.lower()}-{phase.lower()}"
        if event_writer(event_id=event_id, event=event) is not True:
            raise BuildGuardError(f"{phase} evidence was not durably recorded")

    return {"task_id": task_id, "phase": PHASES[-1]}


def _red_gate_state(
    state: Mapping[str, object], task_id: str, red_event: Mapping[str, object]
) -> dict[str, object]:
    """Represent the RED journal proof in the shape required by runtime v2."""

    gated = copy.deepcopy(dict(state))
    tasks = gated["tasks"]
    assert isinstance(tasks, dict)
    task_state = tasks[task_id]
    assert isinstance(task_state, dict)
    task_state.update(
        {
            "phase": "red",
            "status": "in_progress",
            "red_at": f"job-event:{task_id.lower()}-red",
            "red_test_signature": red_event["test_signature"],
            "red_failure_excerpt": red_event["expected_failure"],
        }
    )
    gated["active_task"] = task_id
    return gated


def run_runtime_task(
    *,
    repo_root: Path | str,
    argv: Sequence[str],
    task: Mapping[str, object],
    stack_evidence: Mapping[str, object],
    role_executor: Callable[..., Mapping[str, object]],
    owner: str,
    session_id: str,
) -> dict[str, object]:
    """Run one task behind the canonical runtime state, lease and journal gates."""

    feature_id, task_id, contract, _ = _validate_inputs(argv, task, stack_evidence)
    root = runtime.repository_root(repo_root)
    state_path = root / ".specs" / feature_id / ".tdd-state.json"
    try:
        loaded = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BuildGuardError(f"cannot load target TDD state: {error}") from error
    state = runtime.validate_state(loaded, repo_root=root, allow_legacy=False)
    state_tasks = state["tasks"]
    assert isinstance(state_tasks, dict)
    state_task = state_tasks.get(task_id)
    if not isinstance(state_task, dict):
        raise BuildGuardError(f"validated state does not contain {task_id}")

    delegated_scope = [*contract["test_files"], *contract["production_files"]]
    delegated_files = set(delegated_scope)
    production_files = contract["production_files"]
    state_scope = state_task.get("files_in_scope")
    scope_mismatch = "task contract does not match the validated runtime scope"
    if not isinstance(state_scope, list):
        raise BuildGuardError(scope_mismatch)
    if sorted(delegated_scope) != sorted(state_scope):
        raise BuildGuardError(scope_mismatch)

    lease: dict[str, object] | None = None
    try:
        lease = runtime.acquire_scope_lease(
            root,
            feature_id=feature_id,
            task_id=task_id,
            owner=owner,
            session_id=session_id,
            files_in_scope=delegated_scope,
            state=state,
        )
        event_paths = [
            f".specs/{feature_id}/jobs/{task_id}/{task_id.lower()}-{phase.lower()}.json"
            for phase in PHASES
        ]
        fingerprint_exclusions = [*delegated_scope, *event_paths]
        fingerprint_before = runtime.repository_fingerprint(
            root, excluded_paths=fingerprint_exclusions
        )

        def durable_event_writer(*, event_id: str, event: dict[str, object]) -> bool:
            phase = event.get("phase")
            if not isinstance(phase, str):
                raise BuildGuardError("journal event phase must be a string")
            changed_files = _validated_changed_files(
                event,
                phase,
                delegated_files,
            )
            runtime.validate_worker_changes(
                feature_id=feature_id,
                task_id=task_id,
                changed_paths=changed_files,
                files_in_scope=delegated_scope,
            )
            runtime.append_job_event(
                root,
                feature_id=feature_id,
                task_id=task_id,
                event_id=event_id,
                event=event,
            )
            if phase == RED_PHASE:
                red_state = _red_gate_state(state, task_id, event)
                runtime.validate_red_gate(
                    red_state,
                    task_id=task_id,
                    changed_paths=production_files,
                    production_paths=production_files,
                    repo_root=root,
                )
            return True

        result = run_single_task(
            argv=argv,
            task=task,
            stack_evidence=stack_evidence,
            role_executor=role_executor,
            event_writer=durable_event_writer,
        )
        fingerprint_after = runtime.repository_fingerprint(
            root, excluded_paths=fingerprint_exclusions
        )
        runtime.assert_fingerprint_unchanged(fingerprint_before, fingerprint_after)
        return result
    finally:
        if lease is not None:
            runtime.release_scope_lease(
                root,
                lease_id=str(lease["lease_id"]),
                owner=owner,
                session_id=session_id,
            )
