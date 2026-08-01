#!/usr/bin/env python3
"""Unit and disposable-sandbox tests for the Hermes onboarding guard."""

from __future__ import annotations

import contextlib
import fcntl
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).with_name("onboarding_guard.py")
SPEC = importlib.util.spec_from_file_location("onboarding_guard", MODULE_PATH)
assert SPEC and SPEC.loader
GUARD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GUARD
SPEC.loader.exec_module(GUARD)


class OnboardingGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="sdd-onboarding-test-")
        self.root = Path(self.temporary.name) / "project"
        self.root.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "user.name", "SDD tests")
        (self.root / "README.md").write_text("# Disposable project\n", encoding="utf-8")
        self.git("add", "README.md")
        self.git("commit", "-qm", "initial")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.root), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    @property
    def head(self) -> str:
        return self.git("rev-parse", "HEAD")

    def invoke(self, *args: str, expected: int = 0) -> dict:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = GUARD.main(list(args))
        self.assertEqual(expected, result, stdout.getvalue())
        return json.loads(stdout.getvalue())

    def inspect(self, expected: int = 0) -> dict:
        return self.invoke(
            "inspect", "--project-root", str(self.root), expected=expected
        )

    def write_candidates(
        self,
        inspection: dict,
        *,
        directory: Path | None = None,
        suffix: str = "",
    ) -> Path:
        candidate = directory or Path(self.temporary.name) / "candidates"
        candidate.mkdir(parents=True, exist_ok=True)
        head = inspection["git_sha"]
        probe = inspection["inspection"]
        stack = {
            "schema_version": 1,
            "git_sha": head,
            "classification": probe["classification"],
            "modules": probe["modules"],
            "confidence": probe["confidence"],
        }
        baseline = {
            "schema_version": 1,
            "git_sha": head,
            "heavy_gates_executed": False,
            "validation_commands": probe["validation_commands"],
            "status": "not-run",
        }
        (candidate / "_stack.json").write_text(
            json.dumps(stack, indent=2) + "\n", encoding="utf-8"
        )
        (candidate / "_baseline.json").write_text(
            json.dumps(baseline, indent=2) + "\n", encoding="utf-8"
        )
        (candidate / "_starter-design.md").write_text(
            f"""# Starter design{suffix}

## Git Reference

{head}

## Modules

- root

## Architecture

- Evidence-based only.

## Conventions

- Preserve existing conventions.

## Evidence

- `README.md`

## Confidence and Limits

- Static inspection only.
""",
            encoding="utf-8",
        )
        (candidate / "_known-debt.md").write_text(
            f"""# Known debt{suffix}

## Observed Debt

- None proved.

## Unknowns

- Heavy gates were not run.

## Non-Regression Guidance

- Run `/sdd-wire-harness` separately.
""",
            encoding="utf-8",
        )
        (candidate / "_onboarding.md").write_text(
            f"""# Onboarding{suffix}

## Git Reference

{head}

## Classification

{probe["classification"]}

## Confidence and Limits

- Static inspection only.

## Next Step

`/sdd-spec`
""",
            encoding="utf-8",
        )
        return candidate

    def commit(self, inspection: dict, candidate: Path, expected: int = 0) -> dict:
        return self.invoke(
            "commit",
            "--project-root",
            str(self.root),
            "--expected-head",
            inspection["git_sha"],
            "--expected-token",
            inspection["snapshot_token"],
            "--candidate-dir",
            str(candidate),
            expected=expected,
        )

    def add_spring_and_next_fixture(self) -> None:
        backend = self.root / "backend"
        backend.mkdir()
        (backend / "pom.xml").write_text(
            """<project>
  <parent>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>4.0.1</version>
  </parent>
  <properties><java.version>25</java.version></properties>
  <dependencies>
    <dependency><artifactId>spring-boot-starter-webmvc</artifactId></dependency>
    <dependency><artifactId>flyway-core</artifactId></dependency>
  </dependencies>
</project>
""",
            encoding="utf-8",
        )
        (backend / "src/main/java").mkdir(parents=True)
        (backend / "src/main/java/App.java").write_text(
            "class App {}\n", encoding="utf-8"
        )
        (backend / "mvnw").write_text("#!/bin/sh\n", encoding="utf-8")
        frontend = self.root / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text(
            json.dumps(
                {
                    "engines": {"node": ">=22"},
                    "dependencies": {"next": "16.1.0", "react": "19.2.0"},
                    "scripts": {
                        "test": "vitest",
                        "build": "next build",
                        "unsafe": "TOKEN=secret command",
                    },
                }
            ),
            encoding="utf-8",
        )
        (frontend / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
        self.git("add", "backend", "frontend")
        self.git("commit", "-qm", "add full-stack fixture")

    def test_inspection_detects_sha_stacks_versions_and_commands(self) -> None:
        self.add_spring_and_next_fixture()
        before = self.git("status", "--porcelain=v1", "--untracked-files=all")

        result = self.inspect()

        self.assertEqual(self.head, result["git_sha"])
        modules = result["inspection"]["modules"]
        self.assertEqual(["spring", "nextjs"], [module["kind"] for module in modules])
        self.assertEqual("4.0.1", modules[0]["versions"]["spring_boot"])
        self.assertEqual("16.1.0", modules[1]["versions"]["next"])
        commands = [
            command["command"]
            for command in result["inspection"]["validation_commands"]
        ]
        self.assertIn("./mvnw verify", commands)
        self.assertIn("pnpm test", commands)
        self.assertNotIn("secret", json.dumps(result))
        self.assertFalse(result["inspection"]["scan_policy"]["heavy_gates_executed"])
        self.assertEqual(
            before,
            self.git("status", "--porcelain=v1", "--untracked-files=all"),
        )

    def test_generic_package_json_does_not_prove_react_or_next(self) -> None:
        (self.root / "package.json").write_text(
            '{"dependencies":{"express":"5.0.0"},"scripts":{"build":"node build.js"}}\n',
            encoding="utf-8",
        )
        self.git("add", "package.json")
        self.git("commit", "-qm", "generic node")

        module = self.inspect()["inspection"]["modules"][0]

        self.assertEqual("node", module["kind"])
        self.assertEqual("limited", module["confidence"])
        self.assertEqual(
            "<package-manager> run build",
            module["validation_commands"][0]["command"],
        )

    def test_build_manifest_alone_remains_greenfield(self) -> None:
        (self.root / "build.gradle.kts").write_text(
            'plugins { id("org.springframework.boot") version "4.0.1" }\n',
            encoding="utf-8",
        )
        self.git("add", "build.gradle.kts")
        self.git("commit", "-qm", "empty spring skeleton")

        result = self.inspect()

        self.assertEqual("greenfield", result["inspection"]["classification"])

    def test_multiple_package_manager_locks_remain_ambiguous(self) -> None:
        (self.root / "package.json").write_text(
            '{"dependencies":{"next":"16.1.0"}}\n', encoding="utf-8"
        )
        (self.root / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
        (self.root / "yarn.lock").write_text("# yarn\n")
        self.git("add", "package.json", "pnpm-lock.yaml", "yarn.lock")
        self.git("commit", "-qm", "ambiguous package manager")

        module = self.inspect()["inspection"]["modules"][0]

        self.assertEqual("unknown", module["package_manager"])
        self.assertEqual("limited", module["confidence"])
        self.assertIn("multiple package manager", module["ambiguities"][0])

    def test_flyway_and_liquibase_in_one_spring_module_are_refused(self) -> None:
        (self.root / "pom.xml").write_text(
            """<project><dependencies>
<dependency><artifactId>spring-boot-starter-web</artifactId></dependency>
<dependency><artifactId>flyway-core</artifactId></dependency>
<dependency><artifactId>liquibase-core</artifactId></dependency>
</dependencies></project>
""",
            encoding="utf-8",
        )
        self.git("add", "pom.xml")
        self.git("commit", "-qm", "conflicting migrations")

        result = self.inspect(expected=2)

        self.assertIn("Flyway and Liquibase", result["error"])

    def test_dirty_product_worktree_is_refused_without_artifacts(self) -> None:
        (self.root / "README.md").write_text("changed\n", encoding="utf-8")

        result = self.inspect(expected=2)

        self.assertIn("outside prior onboarding artifacts", result["error"])
        self.assertFalse((self.root / ".specs").exists())

    def test_commit_writes_exact_artifact_set_without_product_changes(self) -> None:
        inspection = self.inspect()
        candidate = self.write_candidates(inspection)
        readme = (self.root / "README.md").read_bytes()

        result = self.commit(inspection, candidate)

        self.assertTrue(result["committed"])
        self.assertFalse(result["unchanged"])
        self.assertEqual(
            set(GUARD.ARTIFACT_NAMES),
            {path.name for path in (self.root / ".specs").iterdir()},
        )
        self.assertEqual(readme, (self.root / "README.md").read_bytes())
        status_paths = {
            line[3:]
            for line in self.git(
                "status", "--porcelain=v1", "--untracked-files=all"
            ).splitlines()
        }
        self.assertEqual(
            {f".specs/{name}" for name in GUARD.ARTIFACT_NAMES}, status_paths
        )

    def test_same_artifacts_are_idempotent_before_git_commit(self) -> None:
        first = self.inspect()
        candidate = self.write_candidates(first)
        self.commit(first, candidate)
        second = self.inspect()

        result = self.commit(second, candidate)

        self.assertTrue(result["committed"])
        self.assertTrue(result["unchanged"])
        self.assertFalse(
            (Path(self.git("rev-parse", "--absolute-git-dir"))
             / "sdd-onboarding.transaction.json").exists()
        )

    def test_concurrent_artifact_change_is_rejected_by_snapshot_token(self) -> None:
        inspection = self.inspect()
        candidate = self.write_candidates(inspection)
        (self.root / ".specs").mkdir()
        (self.root / ".specs/_onboarding.md").write_text("concurrent\n")

        result = self.commit(inspection, candidate, expected=2)

        self.assertIn("do not match the last completion receipt", result["error"])

    def test_candidate_sha_and_unexpected_file_are_rejected(self) -> None:
        inspection = self.inspect()
        candidate = self.write_candidates(inspection)
        stack = json.loads((candidate / "_stack.json").read_text())
        stack["git_sha"] = "0" * 40
        (candidate / "_stack.json").write_text(json.dumps(stack))

        result = self.commit(inspection, candidate, expected=2)

        self.assertIn("does not match current HEAD", result["error"])

    def test_lock_contention_refuses_a_second_writer(self) -> None:
        git_dir = Path(self.git("rev-parse", "--absolute-git-dir"))
        lock_path = git_dir / "sdd-onboarding.lock"
        with lock_path.open("a+b") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.inspect(expected=2)

        self.assertIn("another onboarding writer", result["error"])

    def test_interruption_before_commit_marker_rolls_back_all_artifacts(self) -> None:
        inspection = self.inspect()
        candidate = self.write_candidates(inspection)
        original = GUARD.atomic_replace_with_mode
        writes = 0

        def fail_during_targets(path: Path, data: bytes, mode: int) -> None:
            nonlocal writes
            writes += 1
            if writes == 3:
                raise OSError("simulated interruption before marker")
            original(path, data, mode)

        with mock.patch.object(
            GUARD, "atomic_replace_with_mode", side_effect=fail_during_targets
        ):
            with self.assertRaisesRegex(OSError, "simulated interruption"):
                GUARD.commit(
                    GUARD.build_parser().parse_args(
                        [
                            "commit",
                            "--project-root",
                            str(self.root),
                            "--expected-head",
                            inspection["git_sha"],
                            "--expected-token",
                            inspection["snapshot_token"],
                            "--candidate-dir",
                            str(candidate),
                        ]
                    )
                )

        recovered = self.inspect()
        self.assertTrue(recovered["recovered"])
        self.assertEqual("rolled-back", recovered["recovery_outcome"])
        self.assertEqual(
            [], list((self.root / ".specs").glob("_*"))
        )

    def test_interruption_after_commit_marker_rolls_forward_and_receipts(self) -> None:
        inspection = self.inspect()
        candidate = self.write_candidates(inspection)
        root, git_dir = GUARD.resolve_project(str(self.root))
        paths = GUARD.technical_paths(root, git_dir)
        original = GUARD.atomic_replace

        def fail_before_receipt(path: Path, data: bytes, mode: int = 0o644) -> None:
            if path == paths["receipt"]:
                raise OSError("simulated interruption after marker")
            original(path, data, mode)

        with mock.patch.object(GUARD, "atomic_replace", side_effect=fail_before_receipt):
            with self.assertRaisesRegex(OSError, "simulated interruption"):
                GUARD.commit(
                    GUARD.build_parser().parse_args(
                        [
                            "commit",
                            "--project-root",
                            str(self.root),
                            "--expected-head",
                            inspection["git_sha"],
                            "--expected-token",
                            inspection["snapshot_token"],
                            "--candidate-dir",
                            str(candidate),
                        ]
                    )
                )

        recovered = self.inspect()
        self.assertTrue(recovered["recovered"])
        self.assertEqual("committed", recovered["recovery_outcome"])
        self.assertTrue(paths["receipt"].is_file())
        self.assertTrue(
            all((self.root / ".specs" / name).is_file() for name in GUARD.ARTIFACT_NAMES)
        )

    def test_ambiguous_transaction_is_preserved_for_manual_recovery(self) -> None:
        root, git_dir = GUARD.resolve_project(str(self.root))
        paths = GUARD.technical_paths(root, git_dir)
        paths["journal"].write_text(
            json.dumps(
                {
                    "version": 1,
                    "operation": "commit-onboarding",
                    "expected_marker": "same",
                    "target_marker": "same",
                }
            )
        )

        result = self.inspect(expected=2)

        self.assertIn("markers are ambiguous", result["error"])
        self.assertTrue(paths["journal"].exists())

    def test_existing_artifact_mode_is_preserved(self) -> None:
        first = self.inspect()
        candidate = self.write_candidates(first)
        self.commit(first, candidate)
        onboarding = self.root / ".specs/_onboarding.md"
        os.chmod(onboarding, 0o600)
        self.git("add", ".specs")
        self.git("commit", "-qm", "onboard")
        second = self.inspect()
        revised = self.write_candidates(
            second,
            directory=Path(self.temporary.name) / "revised",
            suffix=" revised",
        )

        self.commit(second, revised)

        self.assertEqual(0o600, stat_mode(onboarding))


def stat_mode(path: Path) -> int:
    return path.stat().st_mode & 0o777


if __name__ == "__main__":
    unittest.main()
