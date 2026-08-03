#!/usr/bin/env python3
"""Executable contract for the Hermes ``/sdd-review`` guard."""

from __future__ import annotations

from contextlib import contextmanager
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "review_guard.py"
SKILL_PATH = HERE.parent / "SKILL.md"
FEATURE_ID = "checkout-review"
BASE_REF = "origin/main"
SPRING_PATH = "src/main/java/example/Checkout.java"
REACT_PATH = "app/checkout/page.tsx"
BASE_ARGUMENT = "--base"
SPRING_STACK = "spring"
REACT_STACK = "react-nextjs"
LOCK_ENTER = "lock:enter"
LOCK_EXIT = "lock:exit"
REPORT_NAME = "08-code-review.md"


def load_guard():
    """Load the guard only after a test can report a missing publication clearly."""

    if not MODULE_PATH.is_file():
        raise AssertionError("review_guard.py must publish the /sdd-review guard")
    spec = importlib.util.spec_from_file_location("review_guard", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("review_guard.py must be importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeRuntime:
    def __init__(self) -> None:
        self.events: list[str] = []

    @contextmanager
    def global_lock(self, _root: Path):
        self.events.append(LOCK_ENTER)
        try:
            yield
        finally:
            self.events.append(LOCK_EXIT)

    def atomic_replace(self, path: Path, data: bytes) -> None:
        self.events.append(f"write:{path.name}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def validate_worker_changes(self, **kwargs) -> None:
        self.events.append(f"validate:{kwargs}")


class ReviewGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.feature = self.root / ".specs" / FEATURE_ID
        self.feature.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_t_021_t1_review_skill_and_guard_are_published(self) -> None:
        """T-021-T1 / AC-150, AC-151: the public skill and guard exist."""

        self.assertTrue(SKILL_PATH.is_file(), "SKILL.md must publish /sdd-review")
        self.assertTrue(MODULE_PATH.is_file(), "review_guard.py must publish /sdd-review")

    def test_t_021_t2_arguments_are_structured_without_shell_evaluation(self) -> None:
        """T-021-T2 / AC-150: feature and base are parsed as inert values."""

        guard = load_guard()
        invocation = guard.parse_invocation([FEATURE_ID, BASE_ARGUMENT, BASE_REF])
        self.assertEqual(FEATURE_ID, invocation.feature_id)
        self.assertEqual(BASE_REF, invocation.base_ref)
        with self.assertRaisesRegex(guard.GuardError, "feature|argument"):
            guard.parse_invocation(["bad; touch /tmp/review-owned"])
        with self.assertRaisesRegex(guard.GuardError, "base|argument"):
            guard.parse_invocation([FEATURE_ID, BASE_ARGUMENT, "main && deploy"])

    def test_t_021_t2_optional_arguments_have_deterministic_defaults(self) -> None:
        """T-021-T2 / AC-150: both documented arguments remain optional."""

        guard = load_guard()
        self.assertEqual(guard.Invocation(None, BASE_REF), guard.parse_invocation([]))
        self.assertEqual(
            guard.Invocation(None, "main"),
            guard.parse_invocation([BASE_ARGUMENT, "main"]),
        )

    def test_t_021_t3_routes_spring_react_or_both_from_the_diff(self) -> None:
        """T-021-T3 / AC-150: changed sources select specialized reviewers."""

        guard = load_guard()
        self.assertEqual((SPRING_STACK,), guard.route_reviewers([SPRING_PATH]))
        self.assertEqual((REACT_STACK,), guard.route_reviewers([REACT_PATH]))
        self.assertEqual(
            (SPRING_STACK, REACT_STACK),
            guard.route_reviewers([SPRING_PATH, REACT_PATH]),
        )
        with self.assertRaisesRegex(guard.GuardError, "Spring or React"):
            guard.route_reviewers(["README.md"])

    def test_t_021_t4_delegates_receive_read_only_inputs_without_report_handle(self) -> None:
        """T-021-T4 / AC-150: delegates receive diff and artifacts, never a writer."""

        guard = load_guard()
        requests = guard.delegation_requests(
            (SPRING_STACK, REACT_STACK),
            (SPRING_PATH, REACT_PATH),
            ("01-spec.md", "03-design.md", "07-validation-report.md"),
        )
        self.assertEqual(
            {"stack", "changed_paths", "artifacts"},
            set(requests[0]),
        )
        serialized = repr(requests).lower()
        for forbidden in ("08-code-review", "callback", "writer", "handle"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, serialized)

    def test_t_021_t4_read_only_delegates_validate_an_empty_change_set(self) -> None:
        """T-021-T4 / AC-150: the runtime proves delegates changed nothing."""

        guard = load_guard()
        runtime = FakeRuntime()
        guard.validate_delegate_changes(
            feature_id=FEATURE_ID,
            task_id="T-021",
            runtime=runtime,
        )
        self.assertEqual(1, len(runtime.events))
        self.assertIn("'changed_paths': ()", runtime.events[0])
        self.assertIn("'files_in_scope': ()", runtime.events[0])

    def test_t_021_t5_fan_in_deduplicates_structured_findings(self) -> None:
        """T-021-T5 / AC-151: fan-in emits each structured finding once."""

        guard = load_guard()
        duplicate = guard.Finding(
            SPRING_STACK,
            "must-fix",
            SPRING_PATH,
            42,
            "unchecked authorization",
            "enforce ownership before mutation",
        )
        react = guard.Finding(
            REACT_STACK,
            "nit",
            REACT_PATH,
            8,
            "ambiguous label",
            "name the checkout action",
        )
        findings = guard.fan_in(((duplicate,), (duplicate, react)))
        self.assertEqual((duplicate, react), findings)

    def test_t_021_t6_one_atomic_writer_targets_only_the_review_report(self) -> None:
        """T-021-T6 / AC-151: one writer atomically publishes only 08-code-review.md."""

        guard = load_guard()
        runtime = FakeRuntime()
        token = "github_pat_abcdefghijklmnopqrstuvwxyz123456"
        written = guard.write_report(
            self.root,
            FEATURE_ID,
            (
                "# Code review\n\n"
                f"Evidence: {self.root}/src/App.java {token} customer@example.com\n"
                "Informative verdict: approve\n"
            ),
            runtime=runtime,
        )
        expected = (self.feature / REPORT_NAME).resolve()
        self.assertEqual(expected, written)
        self.assertTrue(runtime.events[0].startswith("validate:"))
        self.assertEqual(
            [LOCK_ENTER, f"write:{REPORT_NAME}", LOCK_EXIT],
            runtime.events[1:],
        )
        self.assertEqual([REPORT_NAME], [path.name for path in self.feature.iterdir()])
        published = written.read_text(encoding="utf-8")
        for forbidden in (str(self.root), token, "customer@example.com"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, published)

    def test_t_021_t7_verdict_vocabulary_is_closed_and_informative(self) -> None:
        """T-021-T7 / AC-151: review verdicts are closed and never workflow gates."""

        guard = load_guard()
        self.assertEqual(
            {"approve", "request-changes"},
            {item.value for item in guard.ReviewVerdict},
        )
        for verdict in guard.ReviewVerdict:
            with self.subTest(verdict=verdict.value):
                result = guard.ReviewResult(verdict, ())
                self.assertFalse(result.blocking)

    def test_t_021_t8_evidence_redacts_secrets_business_data_and_absolute_paths(self) -> None:
        """T-021-T8 / AC-150, AC-151: retained evidence contains no sensitive data."""

        guard = load_guard()
        secret = "github_pat_abcdefghijklmnopqrstuvwxyz123456"
        business_data = "customer@example.com"
        raw = f"{self.root}/src/App.java {secret} {business_data}"
        redacted = guard.redact_evidence(raw, repo_root=self.root)
        for forbidden in (str(self.root), secret, business_data):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, redacted)
        self.assertIn("[REDACTED]", redacted)


if __name__ == "__main__":
    unittest.main()
