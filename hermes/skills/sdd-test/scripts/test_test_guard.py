#!/usr/bin/env python3
"""Behavioral contract for ``/sdd-test``."""

from __future__ import annotations

from contextlib import contextmanager
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("test_guard.py")


def load_guard():
    if not MODULE_PATH.is_file():
        raise AssertionError("T-017-T1: test_guard.py must publish /sdd-test")
    spec = importlib.util.spec_from_file_location("sdd_test_guard", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RecordingRuntime:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    @contextmanager
    def global_lock(self, root):
        self.calls.append(("lock-enter", str(root)))
        yield
        self.calls.append(("lock-exit", str(root)))

    def validate_worker_changes(self, **kwargs):
        self.calls.append(("validate", kwargs))


class TestGuardTest(unittest.TestCase):
    def test_t017_t1_guard_is_published(self) -> None:
        load_guard()

    def test_t017_t2_accepts_exact_arguments_only(self) -> None:
        guard = load_guard()
        self.assertEqual(
            {"feature_id": "2026-08-03-sample", "gap": False},
            guard.parse_arguments(["2026-08-03-sample"]),
        )
        self.assertEqual(
            {"feature_id": "2026-08-03-sample", "gap": True},
            guard.parse_arguments(["2026-08-03-sample", "--gap"]),
        )
        for argv in ([], ["sample", "--dry-run"], ["a", "b"], ["../escape"]):
            with self.subTest(argv=argv), self.assertRaises(ValueError):
                guard.parse_arguments(argv)

    def test_t017_t3_allows_only_tests_and_feature_test_plan(self) -> None:
        guard = load_guard()
        feature = "2026-08-03-sample"
        allowed = [
            "src/test/java/example/ExampleTest.java",
            f".specs/{feature}/06-test-plan.md",
        ]
        self.assertEqual(allowed, guard.validate_scope(feature, allowed))
        refused = (
            "src/main/java/example/App.java",
            "src/test-link/ExampleTest.java",
            ".specs/other/06-test-plan.md",
            "../src/test/ExampleTest.java",
        )
        for path in refused:
            with self.subTest(path=path), self.assertRaises(ValueError):
                guard.validate_scope(feature, [path])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src").mkdir()
            (root / "real-tests").mkdir()
            (root / "src" / "test").symlink_to(root / "real-tests")
            with self.assertRaises(ValueError):
                guard.validate_scope(
                    feature,
                    ["src/test/ExampleTest.java"],
                    repo_root=root,
                )

    def test_t017_t4_plan_contains_matrix_testcontainers_and_resolved_gaps(self) -> None:
        guard = load_guard()
        plan = guard.render_test_plan(
            feature_id="2026-08-03-sample",
            acceptance_criteria=["AC-001", "AC-002"],
            tests=[
                {
                    "ac": "AC-001",
                    "type": "intégration Testcontainers",
                    "path": "src/test/java/AIT.java",
                    "name": "given db, when read, then return row",
                    "tag": "AC-001",
                }
            ],
            gaps=[
                {"id": "Gap-001", "ac": "AC-002", "wont_fix": "hors périmètre"}
            ],
        )
        for value in (
            "AC-001",
            "AC-002",
            "Testcontainers",
            "Gap-001",
            "Won't fix: hors périmètre",
        ):
            self.assertIn(value, plan)
        with self.assertRaises(ValueError):
            guard.render_test_plan(
                feature_id="sample",
                acceptance_criteria=["AC-001"],
                tests=[],
                gaps=[{"id": "Gap-001", "ac": "AC-001"}],
            )

    def test_t017_t5_gate_keeps_structured_redacted_evidence(self) -> None:
        guard = load_guard()
        runtime = RecordingRuntime()

        def runner(argv):
            return {
                "argv": argv,
                "returncode": 0,
                "output": "token=top-secret /private/project/src/test/A.java PASS",
            }

        with tempfile.TemporaryDirectory() as temporary:
            evidence = guard.run_test_gate(
                repo_root=temporary,
                argv=["mvn", "test"],
                runner=runner,
                runtime=runtime,
            )
        self.assertEqual(["mvn", "test"], evidence["argv"])
        self.assertEqual("PASS", evidence["result"])
        self.assertNotIn("top-secret", evidence["output"])
        self.assertNotIn("/private/project", evidence["output"])
        with self.assertRaises(ValueError):
            guard.run_test_gate(
                repo_root=".",
                argv=["mvn", "-DskipTests", "test"],
                runner=runner,
                runtime=runtime,
            )

    def test_t017_t6_serializes_the_test_gate_with_global_runtime_lock(self) -> None:
        guard = load_guard()
        runtime = RecordingRuntime()
        with tempfile.TemporaryDirectory() as temporary:
            guard.run_test_gate(
                repo_root=temporary,
                argv=["npm", "run", "test"],
                runner=lambda argv: {"argv": argv, "returncode": 1, "output": "FAIL"},
                runtime=runtime,
            )
        self.assertEqual(["lock-enter", "lock-exit"], [name for name, _ in runtime.calls])

    def test_t017_t7_publishes_plan_atomically_then_regenerates_traceability(self) -> None:
        guard = load_guard()
        runtime = RecordingRuntime()
        trace_calls: list[list[str]] = []
        feature = "2026-08-03-sample"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".specs" / feature).mkdir(parents=True)
            target = guard.publish_test_plan(
                repo_root=root,
                feature_id=feature,
                task_id="T-042",
                content="# Plan\n",
                runtime=runtime,
            )
            evidence = guard.regenerate_traceability(
                repo_root=root,
                feature_id=feature,
                runner=lambda argv: trace_calls.append(argv)
                or {"argv": argv, "returncode": 0, "output": "PASS"},
            )
            self.assertEqual("# Plan\n", target.read_text(encoding="utf-8"))
            temporary_plans = [
                path
                for path in target.parent.iterdir()
                if path.name.startswith(".06-test-plan")
            ]
            self.assertEqual([], temporary_plans)
        self.assertEqual(
            [[".github/scripts/traceability.sh", feature]], trace_calls
        )
        self.assertEqual("PASS", evidence["result"])
        self.assertEqual("validate", runtime.calls[-1][0])
        self.assertEqual("T-042", runtime.calls[-1][1]["task_id"])

    def test_t017_t8_catalog_links_every_ac_to_an_executable_runtime_test(self) -> None:
        guard = load_guard()
        repository = Path(__file__).resolve().parents[4]
        catalog = guard.validate_runtime_catalog(repository)
        self.assertEqual(
            {f"AC-{number}" for number in range(196, 210)}, set(catalog)
        )


if __name__ == "__main__":
    unittest.main()
