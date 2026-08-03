#!/usr/bin/env python3
"""Executable contract for the Hermes /sdd-validate guard."""

from __future__ import annotations

from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "validation_guard.py"
SPEC = importlib.util.spec_from_file_location("validation_guard", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load validation guard")
guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = guard
SPEC.loader.exec_module(guard)


def repository_root() -> Path:
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "hermes/runtime").is_dir():
            return ancestor
    raise AssertionError("repository root with hermes/runtime is unavailable")


class FakeRuntime:
    def __init__(self) -> None:
        self.events: list[str] = []

    @contextmanager
    def global_lock(self, _root: Path):
        self.events.append("lock:enter")
        try:
            yield
        finally:
            self.events.append("lock:exit")

    @staticmethod
    def atomic_replace(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


class ValidationGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.feature_id = "checkout-validation"
        self.feature = self.root / ".specs" / self.feature_id
        self.feature.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_ready_project(self) -> None:
        harness = self.root / ".github" / "scripts" / "harness.sh"
        harness.parent.mkdir(parents=True, exist_ok=True)
        harness.write_text("#!/bin/sh\n", encoding="utf-8")
        harness.chmod(0o700)
        state = {"tasks": {"T-001": {"phase": "done"}}}
        (self.feature / ".tdd-state.json").write_text(json.dumps(state), encoding="utf-8")
        summary = {"generated_at": 2_000.0, "bypassed": False, "status": "PASS"}
        target = self.root / "target"
        target.mkdir(exist_ok=True)
        (target / "harness-summary.json").write_text(json.dumps(summary), encoding="utf-8")

    def test_t_018_t1_validation_guard_is_published(self) -> None:
        """T-018-T1: the public validation guard must exist."""

        self.assertTrue(MODULE_PATH.is_file())
        expected_root = repository_root()
        self.assertEqual(expected_root, guard.discover_repo_root(MODULE_PATH))

    def test_t_018_t2_requires_harness_done_tasks_and_fresh_unbypassed_results(self) -> None:
        """T-018-T2 / AC-143: fail closed on every validation precondition."""

        with self.assertRaisesRegex(guard.GuardError, "harness"):
            guard.validate_preconditions(self.root, self.feature_id, now=2_010.0)
        self.make_ready_project()
        result = guard.validate_preconditions(self.root, self.feature_id, now=2_010.0)
        self.assertEqual("PASS", result["status"])

        state_path = self.feature / ".tdd-state.json"
        state_path.write_text(
            json.dumps({"tasks": {"T-001": {"phase": "green"}}}), encoding="utf-8"
        )
        with self.assertRaisesRegex(guard.GuardError, "not done"):
            guard.validate_preconditions(self.root, self.feature_id, now=2_010.0)
        self.make_ready_project()
        summary_path = self.root / "target" / "harness-summary.json"
        summary_path.write_text(
            json.dumps({"generated_at": 2_000.0, "bypassed": True, "status": "PASS"}),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(guard.GuardError, "bypass"):
            guard.validate_preconditions(self.root, self.feature_id, now=2_010.0)
        summary_path.write_text(
            json.dumps({"generated_at": 1_000.0, "bypassed": False, "status": "PASS"}),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(guard.GuardError, "stale"):
            guard.validate_preconditions(self.root, self.feature_id, now=2_010.0)

        for forbidden in ("-DskipTests", "-Dpit.skip=true", "--no-verify"):
            with self.subTest(forbidden=forbidden):
                with self.assertRaisesRegex(guard.GuardError, "bypass"):
                    guard.validate_argv(["mvn", "verify", forbidden])

    def test_t_018_t3_routes_spring_react_or_both_from_modified_sources(self) -> None:
        """T-018-T3 / AC-144: route only validators justified by source paths."""

        self.assertEqual(("spring",), guard.route_validators(["src/main/java/App.java"]))
        self.assertEqual(("react-nextjs",), guard.route_validators(["app/page.tsx"]))
        self.assertEqual(
            ("spring", "react-nextjs"),
            guard.route_validators(["pom.xml", "components/Button.jsx"]),
        )
        with self.assertRaisesRegex(guard.GuardError, "no Spring or React"):
            guard.route_validators(["README.md"])

    def test_t_018_t4_serializes_every_heavy_gate_with_canonical_lock(self) -> None:
        """T-018-T4: Maven, Next, PIT and OWASP execute inside global_lock."""

        runtime = FakeRuntime()

        def runner(argv: tuple[str, ...]) -> guard.GateResult:
            runtime.events.append("run:" + argv[0])
            return guard.GateResult(argv[0], argv, 0, "ok")

        results = guard.execute_heavy_gates(
            self.root,
            {
                "maven": ("mvn", "verify"),
                "next": ("npm", "run", "build"),
                "pit": ("mvn", "pitest:mutationCoverage"),
                "owasp": ("mvn", "dependency-check:check"),
            },
            runner=runner,
            runtime=runtime,
        )
        self.assertEqual({"maven", "next", "pit", "owasp"}, set(results))
        self.assertEqual(
            [
                "lock:enter", "run:mvn", "lock:exit",
                "lock:enter", "run:npm", "lock:exit",
                "lock:enter", "run:mvn", "lock:exit",
                "lock:enter", "run:mvn", "lock:exit",
            ],
            runtime.events,
        )

    def test_t_018_t4_gate_evidence_is_redacted(self) -> None:
        """T-018-T4: gate evidence never retains repository paths or tokens."""

        runtime = FakeRuntime()

        def runner(argv: tuple[str, ...]) -> guard.GateResult:
            output = f"{self.root}/target github_pat_abcdefghijklmnopqrstuvwxyz123456"
            return guard.GateResult(argv[0], argv, 0, output)

        commands = {
            "maven": ("mvn", "verify"),
            "next": ("npm", "run", "build"),
            "pit": ("mvn", "pitest:mutationCoverage"),
            "owasp": ("mvn", "dependency-check:check"),
        }
        results = guard.execute_heavy_gates(
            self.root, commands, runner=runner, runtime=runtime
        )
        for result in results.values():
            self.assertNotIn(str(self.root), result.output)
            self.assertNotIn("github_pat_", result.output)
            self.assertIn("[REDACTED]", result.output)

    def test_t_018_t5_fan_in_accepts_structured_results_without_report_handles(self) -> None:
        """T-018-T5 / AC-144: delegates return data and never receive report handles."""

        requests = guard.delegation_requests(
            ("spring", "react-nextjs"), ("src/main/java/App.java", "app/page.tsx")
        )
        self.assertEqual({"stack", "changed_paths"}, set(requests[0]))
        self.assertNotIn("report", repr(requests).lower())
        results = [
            guard.ValidatorResult("spring", {"maven": "PASS"}, 96.0, 91.0, {"AC-143": "test"}),
            guard.ValidatorResult("react-nextjs", {"next": "FAIL"}, 98.0, None, {"AC-144": "test"}),
        ]
        aggregate = guard.fan_in(results)
        self.assertEqual(guard.TechnicalVerdict.FAIL, aggregate.technical_verdict)
        self.assertEqual(guard.Decision.REQUEST_CHANGES, aggregate.decision)

    def test_t_018_t6_writer_is_limited_to_two_common_reports(self) -> None:
        """T-018-T6 / AC-144: one writer publishes exactly the two allowed reports."""

        runtime = FakeRuntime()
        written = guard.write_reports(
            self.root,
            self.feature_id,
            "# Validation\n\nPASS\n",
            "# Traceability\n\nAC-143\n",
            runtime=runtime,
        )
        self.assertEqual(
            {
                (self.feature / "07-validation-report.md").resolve(),
                (self.feature / "07a-traceability.md").resolve(),
            },
            set(written),
        )
        self.assertEqual(
            ["07-validation-report.md", "07a-traceability.md"],
            sorted(path.name for path in self.feature.iterdir()),
        )

    def test_t_018_t7_verdict_enums_are_closed_and_pass_requires_every_gate(self) -> None:
        """T-018-T7 / AC-145 / AC-146: verdict vocabulary is deterministic."""

        self.assertEqual({"approve", "request-changes"}, {item.value for item in guard.Decision})
        self.assertEqual({"PASS", "FAIL"}, {item.value for item in guard.TechnicalVerdict})
        passing = guard.ValidatorResult("spring", {"maven": "PASS"}, 95.0, 90.0, {"AC-143": "test"})
        self.assertEqual(guard.TechnicalVerdict.PASS, guard.fan_in([passing]).technical_verdict)
        missing_trace = guard.ValidatorResult("spring", {"maven": "PASS"}, 95.0, 90.0, {})
        self.assertEqual(
            guard.TechnicalVerdict.FAIL,
            guard.fan_in([missing_trace]).technical_verdict,
        )

    def test_t_018_t8_catalog_maps_ac_210_to_217_to_executable_proofs(self) -> None:
        """T-018-T8: GitHub and transactional criteria reference real test methods."""

        self.assertEqual({f"AC-{number}" for number in range(210, 218)}, set(guard.PROOF_CATALOG))
        repo_root = repository_root()
        for ac_id, proof in guard.PROOF_CATALOG.items():
            with self.subTest(ac_id=ac_id):
                proof_path = repo_root / proof.path
                self.assertTrue(proof_path.is_file(), proof.path)
                self.assertIn(f"def {proof.test_method}(", proof_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
