#!/usr/bin/env python3
"""Behavioral tests for the sequential ``/sdd-build`` guard."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("build_guard.py")
FEATURE_ID = "sample-feature"
TASK_ID = "T-009"
TEST_ID = "T-009-T1"
TEST_FILE = "tests/SampleServiceTest.java"
PRODUCTION_FILE = "src/main/java/SampleService.java"
TEST_COMMAND = ["mvn", "-Dtest=SampleServiceTest", "test"]
SHARED_ARTIFACTS = (
    "04-tasks.md",
    ".tdd-state.json",
    "05-implementation-log.md",
)
PHASES = ("RED", "GREEN", "REFACTOR", "SIMPLIFY")
SPRING_ROLES = ("spring-test-engineer", "spring-implementer")
REACT_ROLES = (
    "react-nextjs-test-engineer",
    "react-nextjs-implementer",
)
OWNER = "owner-t009"
SESSION_ID = "session-t009"


def load_guard():
    """Load production lazily so a missing guard is an intentional RED."""

    if not MODULE_PATH.is_file():
        raise AssertionError(
            "build_guard.py must implement the /sdd-build sequential guard"
        )
    spec = importlib.util.spec_from_file_location("sdd_build_guard", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RecordingJournal:
    """Small immutable event writer with the runtime journal semantics."""

    def __init__(self) -> None:
        self.events: dict[str, dict[str, object]] = {}
        self.calls: list[tuple[str, str]] = []

    def __call__(self, *, event_id: str, event: dict[str, object]) -> bool:
        phase = str(event["phase"])
        self.calls.append(("event", phase))
        existing = self.events.get(event_id)
        if existing is not None and existing != event:
            raise RuntimeError("immutable event has divergent content")
        self.events[event_id] = copy.deepcopy(event)
        return True


class RecordingRoles:
    def __init__(self, *, stack: str = "spring") -> None:
        self.stack = stack
        self.calls: list[tuple[str, str, dict[str, object]]] = []
        self.timeline: list[tuple[str, str]] = []
        self.overrides: dict[str, dict[str, object]] = {}

    @property
    def roles(self) -> tuple[str, str]:
        return SPRING_ROLES if self.stack == "spring" else REACT_ROLES

    def __call__(
        self, *, role: str, phase: str, context: dict[str, object]
    ) -> dict[str, object]:
        self.calls.append((role, phase, copy.deepcopy(context)))
        self.timeline.append(("role", phase))
        if phase in self.overrides:
            return copy.deepcopy(self.overrides[phase])
        if phase == "RED":
            result: dict[str, object] = {
                "test_signature": "SampleServiceTest.test_missing_behavior",
                "argv": list(TEST_COMMAND),
                "returncode": 1,
                "expected_failure": "service behavior is absent",
                "output": "AssertionError: expected READY but was missing",
                "files_changed": [TEST_FILE],
            }
        else:
            result = {
                "argv": list(TEST_COMMAND),
                "returncode": 0,
                "output": f"{phase.lower()} tests passed",
                "files_changed": [PRODUCTION_FILE] if phase == "GREEN" else [],
            }
        return result


def task_contract() -> dict[str, object]:
    return {
        "task_id": TASK_ID,
        "test_ids": [TEST_ID],
        "test_files": [TEST_FILE],
        "production_files": [PRODUCTION_FILE],
        "test_argv": list(TEST_COMMAND),
    }


def stack_evidence(kind: str = "spring") -> dict[str, object]:
    return {"modules": [{"kind": kind, "evidence": ["pom.xml"]}]}


def runtime_state() -> dict[str, object]:
    return {
        "schema_version": 2,
        "feature_id": FEATURE_ID,
        "mode": "sequential",
        "project": "fixture",
        "board": "fixture",
        "max_workers": 1,
        "revision": 0,
        "active_task": None,
        "tasks": {
            "T-008": {
                "phase": "done",
                "status": "done",
                "dependencies": [],
                "test_ids": ["T-008-T1"],
                "files_in_scope": ["docs/completed.md"],
                "red_at": "2026-08-03T08:00:00Z",
                "red_test_signature": "CompletedTest.test_done",
                "red_failure_excerpt": "expected failure",
                "green_at": "2026-08-03T08:01:00Z",
            },
            TASK_ID: {
                "phase": "pending",
                "status": "ready",
                "dependencies": ["T-008"],
                "test_ids": [TEST_ID],
                "files_in_scope": [TEST_FILE, PRODUCTION_FILE],
                "red_at": None,
                "red_test_signature": None,
                "red_failure_excerpt": None,
                "green_at": None,
            },
        },
    }


def create_runtime_repository(temporary: str) -> Path:
    root = Path(temporary) / "project"
    feature = root / ".specs" / FEATURE_ID
    feature.mkdir(parents=True)
    (feature / ".tdd-state.json").write_text(
        json.dumps(runtime_state(), indent=2) + "\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("runtime fixture\n", encoding="utf-8")
    for arguments in (
        ("init", "-q"),
        ("config", "user.name", "Build Guard Test"),
        ("config", "user.email", "build-guard@example.invalid"),
        ("add", "."),
        ("commit", "-qm", "runtime fixture"),
    ):
        subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    return root


def run_cycle(
    roles: RecordingRoles,
    journal: RecordingJournal,
    *,
    arguments: list[str] | None = None,
    evidence: dict[str, object] | None = None,
) -> object:
    guard = load_guard()
    return guard.run_single_task(
        argv=arguments or [FEATURE_ID, TASK_ID],
        task=task_contract(),
        stack_evidence=evidence or stack_evidence(roles.stack),
        role_executor=roles,
        event_writer=journal,
    )


class BuildGuardTest(unittest.TestCase):
    def test_t009_t1_public_arguments_are_validated_before_mutation(self) -> None:
        """T-009-T1: malformed public arguments fail before mutation."""

        guard = load_guard()
        roles = RecordingRoles()
        journal = RecordingJournal()

        for invalid in ([FEATURE_ID], [FEATURE_ID, "9"], ["../escape", TASK_ID]):
            with self.subTest(argv=invalid), self.assertRaises(guard.BuildGuardError):
                guard.run_single_task(
                    argv=invalid,
                    task=task_contract(),
                    stack_evidence=stack_evidence(),
                    role_executor=roles,
                    event_writer=journal,
                )

        self.assertEqual([], roles.calls)
        self.assertEqual({}, journal.events)

    def test_t009_t2_stack_evidence_routes_to_the_matching_role_pair(self) -> None:
        """T-009-T2: proved Spring and React stacks select their own roles."""

        for kind, expected_roles in (
            ("spring", SPRING_ROLES),
            ("nextjs", REACT_ROLES),
            ("react", REACT_ROLES),
        ):
            with self.subTest(kind=kind):
                roles = RecordingRoles(stack="spring" if kind == "spring" else "react")
                journal = RecordingJournal()

                run_cycle(roles, journal, evidence=stack_evidence(kind))

                self.assertEqual(expected_roles[0], roles.calls[0][0])
                self.assertEqual(
                    [expected_roles[1]] * 3,
                    [role for role, _, _ in roles.calls[1:]],
                )

    def test_t009_t3_red_context_contains_only_tests_and_no_shared_handles(
        self,
    ) -> None:
        """T-009-T3: RED owns only Test-IDs, test files and test argv."""

        roles = RecordingRoles()
        run_cycle(roles, RecordingJournal())

        _, phase, context = roles.calls[0]
        self.assertEqual("RED", phase)
        self.assertEqual(
            {"task_id", "test_ids", "files_in_scope", "test_argv"},
            set(context),
        )
        self.assertEqual([TEST_ID], context["test_ids"])
        self.assertEqual([TEST_FILE], context["files_in_scope"])
        serialized = json.dumps(context)
        self.assertNotIn(PRODUCTION_FILE, serialized)
        for artifact in SHARED_ARTIFACTS:
            self.assertNotIn(artifact, serialized)

    def test_t009_t4_production_requires_complete_durable_red_proof(self) -> None:
        """T-009-T4: incomplete or non-durable RED cannot unlock production."""

        guard = load_guard()
        required_fields = (
            "test_signature",
            "argv",
            "returncode",
            "expected_failure",
            "output",
        )
        for missing in required_fields:
            with self.subTest(missing=missing):
                roles = RecordingRoles()
                proof = roles(role=SPRING_ROLES[0], phase="RED", context={})
                proof.pop(missing)
                roles.calls.clear()
                roles.timeline.clear()
                roles.overrides["RED"] = proof
                journal = RecordingJournal()

                with self.assertRaises(guard.BuildGuardError):
                    run_cycle(roles, journal)

                self.assertFalse(
                    any(role == SPRING_ROLES[1] for role, _, _ in roles.calls)
                )

        roles = RecordingRoles()
        unstructured = roles(role=SPRING_ROLES[0], phase="RED", context={})
        unstructured["argv"] = "mvn -Dtest=SampleServiceTest test"
        roles.calls.clear()
        roles.timeline.clear()
        roles.overrides["RED"] = unstructured
        with self.assertRaisesRegex(guard.BuildGuardError, "structured argv"):
            run_cycle(roles, RecordingJournal())

        roles = RecordingRoles()

        def nondurable_writer(*, event_id: str, event: dict[str, object]) -> bool:
            return False

        with self.assertRaisesRegex(guard.BuildGuardError, "durable RED"):
            guard.run_single_task(
                argv=[FEATURE_ID, TASK_ID],
                task=task_contract(),
                stack_evidence=stack_evidence(),
                role_executor=roles,
                event_writer=nondurable_writer,
            )
        self.assertEqual(["RED"], [phase for _, phase, _ in roles.calls])

    def test_t009_t5_green_follows_red_and_receives_only_production_scope(self) -> None:
        """T-009-T5: GREEN starts after RED persistence with minimal scope."""

        roles = RecordingRoles()
        journal = RecordingJournal()

        def ordered_writer(*, event_id: str, event: dict[str, object]) -> bool:
            journal(event_id=event_id, event=event)
            roles.timeline.append(("event", str(event["phase"])))
            return True

        guard = load_guard()
        guard.run_single_task(
            argv=[FEATURE_ID, TASK_ID],
            task=task_contract(),
            stack_evidence=stack_evidence(),
            role_executor=roles,
            event_writer=ordered_writer,
        )

        green_call = roles.calls[1]
        self.assertEqual(("event", "RED"), roles.timeline[1])
        self.assertEqual(("role", "GREEN"), roles.timeline[2])
        self.assertEqual([PRODUCTION_FILE], green_call[2]["files_in_scope"])
        self.assertIn("red_proof", green_call[2])
        self.assertNotIn(TEST_FILE, json.dumps(green_call[2]["files_in_scope"]))

    def test_t009_t6_one_job_enforces_the_complete_phase_order(self) -> None:
        """T-009-T6: one invocation runs RED, GREEN, REFACTOR, SIMPLIFY."""

        roles = RecordingRoles()
        journal = RecordingJournal()

        result = run_cycle(roles, journal)

        self.assertEqual(list(PHASES), [phase for _, phase, _ in roles.calls])
        self.assertEqual(
            list(PHASES),
            [event["phase"] for event in journal.events.values()],
        )
        self.assertEqual("SIMPLIFY", result["phase"])
        self.assertEqual(TASK_ID, result["task_id"])

    def test_t009_t7_each_event_has_structured_sanitized_evidence(self) -> None:
        """T-009-T7: transition evidence is complete, structured and redacted."""

        secret = "ghp_abcdefghijklmnopqrstuvwxyz123456"
        roles = RecordingRoles()
        roles.overrides["RED"] = {
            "test_signature": "SampleServiceTest.test_missing_behavior",
            "argv": list(TEST_COMMAND),
            "returncode": 1,
            "expected_failure": "service behavior is absent",
            "output": f"failure token={secret}",
            "files_changed": [TEST_FILE],
        }
        journal = RecordingJournal()

        run_cycle(roles, journal)

        for phase, event in zip(PHASES, journal.events.values(), strict=True):
            with self.subTest(phase=phase):
                self.assertEqual([TEST_ID], event["test_ids"])
                self.assertIsInstance(event["argv"], list)
                self.assertIsInstance(event["output"], str)
                self.assertIsInstance(event["files_changed"], list)
        serialized = json.dumps(journal.events)
        self.assertNotIn(secret, serialized)
        self.assertIn("[REDACTED]", serialized)

    def test_t009_t8_roles_cannot_change_shared_artifacts(self) -> None:
        """T-009-T8: role-reported shared artifact writes fail closed."""

        guard = load_guard()
        for artifact in SHARED_ARTIFACTS:
            with self.subTest(artifact=artifact):
                roles = RecordingRoles()
                invalid = roles(role=SPRING_ROLES[0], phase="RED", context={})
                invalid["files_changed"] = [f".specs/{FEATURE_ID}/{artifact}"]
                roles.calls.clear()
                roles.timeline.clear()
                roles.overrides["RED"] = invalid
                journal = RecordingJournal()

                with self.assertRaisesRegex(guard.BuildGuardError, "shared artifact"):
                    run_cycle(roles, journal)

                self.assertEqual({}, journal.events)

    def test_t009_t9_replay_is_idempotent_and_divergence_is_refused(self) -> None:
        """T-009-T9: stable event IDs replay; changed evidence is rejected."""

        journal = RecordingJournal()
        run_cycle(RecordingRoles(), journal)
        first = copy.deepcopy(journal.events)

        run_cycle(RecordingRoles(), journal)

        self.assertEqual(first, journal.events)
        self.assertEqual(4, len(journal.events))
        divergent = RecordingRoles()
        divergent.overrides["GREEN"] = {
            "argv": list(TEST_COMMAND),
            "returncode": 0,
            "output": "different green proof",
            "files_changed": [PRODUCTION_FILE],
        }
        with self.assertRaisesRegex(RuntimeError, "divergent content"):
            run_cycle(divergent, journal)

    def test_t009_t4_t6_t8_t9_runtime_facade_gates_journals_and_releases(
        self,
    ) -> None:
        """T-009-T4/T6/T8/T9: runtime gates wrap one complete leased cycle."""

        guard = load_guard()
        with tempfile.TemporaryDirectory(prefix="sdd-build-runtime-") as temporary:
            root = create_runtime_repository(temporary)

            def execute(roles: RecordingRoles) -> dict[str, object]:
                return guard.run_runtime_task(
                    repo_root=root,
                    argv=[FEATURE_ID, TASK_ID],
                    task=task_contract(),
                    stack_evidence=stack_evidence(),
                    role_executor=roles,
                    owner=OWNER,
                    session_id=SESSION_ID,
                )

            result = execute(RecordingRoles())

            self.assertEqual("SIMPLIFY", result["phase"])
            self.assertEqual(
                4,
                guard.runtime.verify_job_journal(
                    root,
                    feature_id=FEATURE_ID,
                    task_id=TASK_ID,
                ),
            )
            journal = root / ".specs" / FEATURE_ID / "jobs" / TASK_ID
            phases = {
                json.loads(path.read_text(encoding="utf-8"))["event"]["phase"]
                for path in journal.glob("*.json")
            }
            self.assertEqual(set(PHASES), phases)

            outside = RecordingRoles()
            outside_proof = outside(
                role=SPRING_ROLES[0], phase="RED", context={}
            )
            outside_proof["files_changed"] = ["src/main/java/Outside.java"]
            outside.calls.clear()
            outside.timeline.clear()
            outside.overrides["RED"] = outside_proof
            with self.assertRaisesRegex(
                guard.BuildGuardError,
                "outside its delegated scope",
            ):
                execute(outside)

            shared = RecordingRoles()
            shared_proof = shared(
                role=SPRING_ROLES[0], phase="RED", context={}
            )
            shared_proof["files_changed"] = [
                f".specs/{FEATURE_ID}/.tdd-state.json"
            ]
            shared.calls.clear()
            shared.timeline.clear()
            shared.overrides["RED"] = shared_proof
            with self.assertRaisesRegex(
                guard.BuildGuardError,
                "shared artifact",
            ):
                execute(shared)

            failing = RecordingRoles()
            failing.overrides["GREEN"] = {
                "argv": list(TEST_COMMAND),
                "returncode": 1,
                "output": "GREEN regression",
                "files_changed": [PRODUCTION_FILE],
            }
            with self.assertRaisesRegex(
                guard.BuildGuardError,
                "keep the tests green",
            ):
                execute(failing)

            lease_registry = (
                guard.runtime.runtime_directory(root) / "leases.json"
            )
            self.assertEqual(
                {},
                json.loads(lease_registry.read_text(encoding="utf-8"))["leases"],
            )
            self.assertEqual("SIMPLIFY", execute(RecordingRoles())["phase"])


if __name__ == "__main__":
    unittest.main()
