#!/usr/bin/env python3
"""Behavioral contract for ``/sdd-code-simplify``."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("code_simplify_guard.py")
TEST_ARGV = ["mvn", "-q", "test"]


def load_guard():
    if not MODULE_PATH.is_file():
        raise AssertionError(
            "T-015-T1: code_simplify_guard.py must publish the command guard"
        )
    spec = importlib.util.spec_from_file_location("code_simplify_guard", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RecordingRuntime:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def acquire_scope_lease(self, root, **kwargs):
        self.calls.append(("acquire", kwargs))
        return {"lease_id": "lease-t015"}

    def repository_fingerprint(self, root, *, excluded_paths=()):
        excluded = tuple(sorted(str(path) for path in excluded_paths))
        self.calls.append(("fingerprint", excluded))
        return "outside-scope-stable"

    def validate_worker_changes(self, **kwargs):
        self.calls.append(("validate", kwargs))

    def release_scope_lease(self, root, **kwargs):
        self.calls.append(("release", kwargs))


class FailingFingerprintRuntime(RecordingRuntime):
    def repository_fingerprint(self, root, *, excluded_paths=()):
        self.calls.append(("fingerprint", tuple(excluded_paths)))
        raise RuntimeError("fingerprint unavailable")


class RecordingRunner:
    def __init__(self, returncodes: list[int]) -> None:
        self.returncodes = list(returncodes)
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str]) -> dict[str, object]:
        self.calls.append(list(argv))
        returncode = self.returncodes.pop(0)
        output = "token=top-secret\n/private/project/src/main/App.java\nBUILD"
        return {"argv": list(argv), "returncode": returncode, "output": output}


class RecordingRole:
    def __init__(self, replacements: dict[str, str]) -> None:
        self.replacements = replacements
        self.calls: list[dict[str, object]] = []

    def __call__(self, **context) -> dict[str, object]:
        self.calls.append(context)
        path = Path(str(context["absolute_path"]))
        if not context["dry_run"]:
            path.write_text(self.replacements[path.name], encoding="utf-8")
        return {
            "categories": ["conditions", "noms"],
            "changed": self.replacements[path.name] != path.read_text(encoding="utf-8")
            if context["dry_run"]
            else True,
        }


def lease_context(files: list[str]) -> dict[str, object]:
    return {
        "feature_id": "sample-feature",
        "task_id": "T-015",
        "owner": "owner-t015",
        "session_id": "session-t015",
        "files_in_scope": files,
        "state": {"schema_version": 2},
    }


class CodeSimplifyGuardTest(unittest.TestCase):
    def create_project(self, temporary: str) -> tuple[Path, Path, Path]:
        root = Path(temporary) / "project"
        source = root / "src" / "main" / "java"
        source.mkdir(parents=True)
        alpha = source / "Alpha.java"
        beta = source / "Beta.java"
        alpha.write_text("alpha original\n", encoding="utf-8")
        beta.write_text("beta original\n", encoding="utf-8")
        return root, alpha, beta

    def test_t015_t2_accepts_exact_arguments_and_rejects_unsafe_targets(self) -> None:
        guard = load_guard()
        self.assertEqual(
            {"target": "src/main/java", "dry_run": False},
            guard.parse_arguments(["src/main/java"]),
        )
        self.assertEqual(
            {"target": "src/main/java", "dry_run": True},
            guard.parse_arguments(["src/main/java", "--dry-run"]),
        )
        for argv in ([], ["src/main/java", "--unknown"], ["a", "b"]):
            with self.subTest(argv=argv), self.assertRaises(ValueError):
                guard.parse_arguments(argv)

        with tempfile.TemporaryDirectory() as temporary:
            root, alpha, _ = self.create_project(temporary)
            (root / "src" / "test").mkdir(parents=True)
            (root / "src" / "test" / "A.java").write_text("test\n")
            symlink = root / "src" / "main" / "java" / "Alias.java"
            symlink.symlink_to(alpha)
            unsafe = (
                "src/test/A.java",
                "src/main/**/*.java",
                "src/main/java/Alias.java",
                "../outside.java",
            )
            for target in unsafe:
                with self.subTest(target=target), self.assertRaises(ValueError):
                    guard.resolve_target(root, target)

    def test_t015_t3_refuses_mutation_when_baseline_is_red(self) -> None:
        guard = load_guard()
        with tempfile.TemporaryDirectory() as temporary:
            root, alpha, _ = self.create_project(temporary)
            runtime = RecordingRuntime()
            role = RecordingRole({"Alpha.java": "changed\n"})
            with self.assertRaises(guard.BaselineTestsFailed):
                guard.run_simplification(
                    repo_root=root,
                    argv=["src/main/java/Alpha.java"],
                    test_argv=TEST_ARGV,
                    test_runner=RecordingRunner([1]),
                    role_executor=role,
                    runtime=runtime,
                    lease_context=lease_context(["src/main/java/Alpha.java"]),
                )
            self.assertEqual("alpha original\n", alpha.read_text())
            self.assertEqual([], role.calls)
            self.assertEqual([], runtime.calls)

    def test_t015_t5_restores_only_the_regressing_file_under_exact_lease(self) -> None:
        guard = load_guard()
        with tempfile.TemporaryDirectory() as temporary:
            root, alpha, beta = self.create_project(temporary)
            files = ["src/main/java/Alpha.java", "src/main/java/Beta.java"]
            runtime = RecordingRuntime()
            summary = guard.run_simplification(
                repo_root=root,
                argv=["src/main/java"],
                test_argv=TEST_ARGV,
                test_runner=RecordingRunner([0, 0, 1]),
                role_executor=RecordingRole(
                    {"Alpha.java": "alpha clear\n", "Beta.java": "beta broken\n"}
                ),
                runtime=runtime,
                lease_context=lease_context(files),
            )
            self.assertEqual("alpha clear\n", alpha.read_text())
            self.assertEqual("beta original\n", beta.read_text())
            self.assertEqual(["simplified", "ignored"], summary["results"])
            acquire = next(value for name, value in runtime.calls if name == "acquire")
            self.assertEqual(files, acquire["files_in_scope"])
            self.assertEqual("release", runtime.calls[-1][0])

    def test_t015_t5_releases_the_lease_when_fingerprinting_fails(self) -> None:
        guard = load_guard()
        with tempfile.TemporaryDirectory() as temporary:
            root, _, _ = self.create_project(temporary)
            runtime = FailingFingerprintRuntime()
            with self.assertRaisesRegex(RuntimeError, "fingerprint unavailable"):
                guard.run_simplification(
                    repo_root=root,
                    argv=["src/main/java/Alpha.java"],
                    test_argv=TEST_ARGV,
                    test_runner=RecordingRunner([0]),
                    role_executor=RecordingRole({"Alpha.java": "clear\n"}),
                    runtime=runtime,
                    lease_context=lease_context(["src/main/java/Alpha.java"]),
                )
            self.assertEqual("release", runtime.calls[-1][0])

    def test_t015_t6_records_redacted_structured_evidence_without_commit(self) -> None:
        guard = load_guard()
        with tempfile.TemporaryDirectory() as temporary:
            root, _, _ = self.create_project(temporary)
            summary = guard.run_simplification(
                repo_root=root,
                argv=["src/main/java/Alpha.java"],
                test_argv=TEST_ARGV,
                test_runner=RecordingRunner([0, 0]),
                role_executor=RecordingRole({"Alpha.java": "clear\n"}),
                runtime=RecordingRuntime(),
                lease_context=lease_context(["src/main/java/Alpha.java"]),
            )
            self.assertEqual(TEST_ARGV, summary["tests"][0]["argv"])
            self.assertNotIn("top-secret", str(summary))
            self.assertNotIn(str(root), str(summary))
            self.assertNotIn("/private/project", str(summary))
            self.assertEqual(["conditions", "noms"], summary["categories"])
            self.assertEqual([], summary["regressions"])

    def test_t015_t7_dry_run_returns_plan_without_any_mutation(self) -> None:
        guard = load_guard()
        with tempfile.TemporaryDirectory() as temporary:
            root, alpha, beta = self.create_project(temporary)
            runtime = RecordingRuntime()
            runner = RecordingRunner([0])
            summary = guard.run_simplification(
                repo_root=root,
                argv=["src/main/java", "--dry-run"],
                test_argv=TEST_ARGV,
                test_runner=runner,
                role_executor=RecordingRole(
                    {"Alpha.java": "alpha clear\n", "Beta.java": "beta clear\n"}
                ),
                runtime=runtime,
                lease_context=lease_context(
                    ["src/main/java/Alpha.java", "src/main/java/Beta.java"]
                ),
            )
            self.assertEqual("alpha original\n", alpha.read_text())
            self.assertEqual("beta original\n", beta.read_text())
            self.assertEqual(["simplified", "simplified"], summary["results"])
            self.assertTrue(summary["dry_run"])
            self.assertEqual(1, len(runner.calls))
            self.assertEqual([], runtime.calls)

    def test_t015_t5_rejects_a_role_that_touches_the_next_file(self) -> None:
        guard = load_guard()
        with tempfile.TemporaryDirectory() as temporary:
            root, alpha, beta = self.create_project(temporary)

            def collateral_role(**context):
                Path(str(context["absolute_path"])).write_text("alpha clear\n")
                beta.write_text("collateral change\n")
                return {"categories": ["noms"], "changed": True}

            files = ["src/main/java/Alpha.java", "src/main/java/Beta.java"]
            with self.assertRaises(RuntimeError):
                guard.run_simplification(
                    repo_root=root,
                    argv=["src/main/java"],
                    test_argv=TEST_ARGV,
                    test_runner=RecordingRunner([0]),
                    role_executor=collateral_role,
                    runtime=RecordingRuntime(),
                    lease_context=lease_context(files),
                )
            self.assertEqual("alpha original\n", alpha.read_text())
            self.assertEqual("beta original\n", beta.read_text())

    def test_t015_t7_restores_and_refuses_a_mutating_dry_run_role(self) -> None:
        guard = load_guard()
        with tempfile.TemporaryDirectory() as temporary:
            root, alpha, _ = self.create_project(temporary)

            def mutating_role(**context):
                Path(str(context["absolute_path"])).write_text("forbidden\n")
                return {"categories": ["noms"], "changed": True}

            with self.assertRaises(RuntimeError):
                guard.run_simplification(
                    repo_root=root,
                    argv=["src/main/java/Alpha.java", "--dry-run"],
                    test_argv=TEST_ARGV,
                    test_runner=RecordingRunner([0]),
                    role_executor=mutating_role,
                    runtime=RecordingRuntime(),
                    lease_context=lease_context(["src/main/java/Alpha.java"]),
                )
            self.assertEqual("alpha original\n", alpha.read_text())


if __name__ == "__main__":
    unittest.main()
