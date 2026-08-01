#!/usr/bin/env python3

from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("sdd_runtime_guard.py")
MODULE_SPEC = importlib.util.spec_from_file_location("sdd_runtime_guard", SCRIPT)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
guard = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(guard)


class RepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Runtime Test")
        self.git("config", "user.email", "runtime@example.invalid")
        (self.root / "README.md").write_text("runtime fixture\n", encoding="utf-8")
        self.git("add", "README.md")
        self.git("commit", "-qm", "fixture")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )

    def state(self) -> dict:
        return {
            "schema_version": 2,
            "feature_id": "feature-one",
            "mode": "parallel",
            "project": "fixture",
            "board": "fixture",
            "max_workers": 2,
            "revision": 0,
            "active_task": None,
            "tasks": {
                "T-001": {
                    "phase": "pending",
                    "status": "ready",
                    "dependencies": [],
                    "test_ids": ["T-001-T1"],
                    "files_in_scope": ["backend/src/One.java"],
                    "kanban_id": None,
                    "issue": None,
                    "branch": None,
                    "pr": None,
                    "red_at": None,
                    "red_test_signature": None,
                    "red_failure_excerpt": None,
                    "green_at": None,
                },
                "T-002": {
                    "phase": "pending",
                    "status": "ready",
                    "dependencies": [],
                    "test_ids": ["T-002-T1"],
                    "files_in_scope": ["frontend/app/page.tsx"],
                    "kanban_id": "card-2",
                    "issue": 12,
                    "branch": "sdd/feature-one/t-002-page",
                    "pr": 13,
                    "red_at": None,
                    "red_test_signature": None,
                    "red_failure_excerpt": None,
                    "green_at": None,
                },
            },
        }


class StateContractTest(RepositoryTest):
    def test_valid_v2_state_is_additive_for_legacy_consumers(self) -> None:
        state = self.state()
        validated = guard.validate_state(state, repo_root=self.root)

        self.assertEqual(2, validated["schema_version"])
        self.assertIsNone(validated["active_task"])
        self.assertEqual("pending", validated["tasks"]["T-001"]["phase"])
        self.assertEqual(state, validated)

    def test_v1_migration_is_backward_compatible_and_does_not_mutate_input(self) -> None:
        legacy = {
            "feature_id": "feature-one",
            "active_task": None,
            "tasks": {
                "T-001": {
                    "phase": "pending",
                    "red_at": None,
                    "red_test_signature": None,
                    "red_failure_excerpt": None,
                    "green_at": None,
                    "files_in_scope": ["backend/src/One.java"],
                }
            },
        }
        original = copy.deepcopy(legacy)

        migrated = guard.validate_state(legacy, repo_root=self.root)

        self.assertEqual(original, legacy)
        self.assertEqual(2, migrated["schema_version"])
        self.assertEqual("sequential", migrated["mode"])
        self.assertEqual(1, migrated["max_workers"])
        self.assertEqual([], migrated["tasks"]["T-001"]["test_ids"])
        self.assertEqual(
            {"from_schema_version": 1, "contract_complete": False},
            migrated["migration"],
        )

    def test_unknown_version_and_sensitive_fields_fail_closed(self) -> None:
        unknown = self.state()
        unknown["schema_version"] = 99
        with self.assertRaisesRegex(guard.GuardError, "unsupported"):
            guard.validate_state(unknown)

        for field in ("access_token", "transcript", "client_secret", "absolute_path"):
            unsafe = self.state()
            unsafe[field] = "must-not-be-persisted"
            with self.subTest(field=field), self.assertRaisesRegex(
                guard.GuardError, "forbidden state field"
            ):
                guard.validate_state(unsafe)

        secret = self.state()
        secret["tasks"]["T-001"]["branch"] = "ghp_abcdefghijklmnopqrstuvwxyz"
        with self.assertRaisesRegex(guard.GuardError, "secret-like"):
            guard.validate_state(secret)

    def test_explicit_question_red_and_command_gates_replace_prompt_assumptions(self) -> None:
        guard.assert_no_open_questions(
            {"01-spec.md": "# Spec\n\n## Open Questions\n\n- (none)\n"}
        )
        with self.assertRaisesRegex(guard.GuardError, "Q-007"):
            guard.assert_no_open_questions(
                {"03-design.md": "# Design\n\n## Open Questions\n\n- Q-007: choose storage\n"}
            )
        with self.assertRaisesRegex(guard.GuardError, "missing"):
            guard.assert_no_open_questions({"03-design.md": "# Design\n"})

        state = self.state()
        state["mode"] = "sequential"
        state["max_workers"] = 1
        state["active_task"] = "T-001"
        state["tasks"]["T-001"]["phase"] = "red"
        state["tasks"]["T-001"]["status"] = "in_progress"
        with self.assertRaisesRegex(guard.GuardError, "RED proof"):
            guard.validate_red_gate(
                state,
                task_id="T-001",
                changed_paths=["backend/src/One.java"],
                production_paths=["backend/src/One.java"],
                repo_root=self.root,
            )
        state["tasks"]["T-001"].update(
            {
                "red_at": "2026-08-01T00:00:00Z",
                "red_test_signature": "OneTest.failsBeforeImplementation",
                "red_failure_excerpt": "expected operational but was missing",
            }
        )
        guard.validate_red_gate(
            state,
            task_id="T-001",
            changed_paths=["backend/src/One.java"],
            production_paths=["backend/src/One.java"],
            repo_root=self.root,
        )

        self.assertEqual(["mvn", "verify"], guard.validate_command_arguments(["mvn", "verify"]))
        with self.assertRaisesRegex(guard.GuardError, "bypass"):
            guard.validate_command_arguments(["git", "commit", "--no-verify"])
        with self.assertRaisesRegex(guard.GuardError, "structured"):
            guard.validate_command_arguments("mvn -DskipTests verify")

    def test_mode_worker_limit_and_absolute_scope_are_rejected(self) -> None:
        invalid = self.state()
        invalid["mode"] = "sequential"
        with self.assertRaisesRegex(guard.GuardError, "max_workers=1"):
            guard.validate_state(invalid)

        invalid = self.state()
        invalid["tasks"]["T-001"]["files_in_scope"] = ["/etc/passwd"]
        with self.assertRaisesRegex(guard.GuardError, "absolute"):
            guard.validate_state(invalid, repo_root=self.root)

        empty = self.state()
        empty["tasks"]["T-001"]["files_in_scope"] = []
        with self.assertRaisesRegex(guard.GuardError, "concrete scope"):
            guard.validate_state(empty, repo_root=self.root)

        directory = self.root / "backend"
        directory.mkdir()
        directory_scope = self.state()
        directory_scope["tasks"]["T-001"]["files_in_scope"] = ["backend"]
        with self.assertRaisesRegex(guard.GuardError, "directory scope"):
            guard.validate_state(directory_scope, repo_root=self.root)

    def test_phase_status_active_task_and_external_ids_are_consistent(self) -> None:
        inconsistent = self.state()
        inconsistent["tasks"]["T-001"]["phase"] = "red"
        with self.assertRaisesRegex(guard.GuardError, "phase/status"):
            guard.validate_state(inconsistent)

        active = self.state()
        active["active_task"] = "T-001"
        with self.assertRaisesRegex(guard.GuardError, "in-progress"):
            guard.validate_state(active)

        for field, duplicate in (
            ("kanban_id", "card-2"),
            ("branch", "sdd/feature-one/t-002-page"),
            ("issue", 12),
            ("pr", 13),
        ):
            state = self.state()
            state["tasks"]["T-001"][field] = duplicate
            with self.subTest(field=field), self.assertRaisesRegex(
                guard.GuardError, f"reuse {field}"
            ):
                guard.validate_state(state)

        traversal = self.state()
        traversal["tasks"]["T-001"]["branch"] = "sdd/../main"
        with self.assertRaisesRegex(guard.GuardError, "traversal"):
            guard.validate_state(traversal)

    def test_dag_and_test_id_failures_are_explicit(self) -> None:
        cyclic = self.state()
        cyclic["tasks"]["T-001"]["dependencies"] = ["T-002"]
        cyclic["tasks"]["T-002"]["dependencies"] = ["T-001"]
        with self.assertRaisesRegex(guard.GuardError, "cycle"):
            guard.validate_state(cyclic)

        missing = self.state()
        missing["tasks"]["T-001"]["dependencies"] = ["T-999"]
        with self.assertRaisesRegex(guard.GuardError, "unknown task"):
            guard.validate_state(missing)

        duplicate = self.state()
        duplicate["tasks"]["T-002"]["test_ids"] = ["T-001-T1"]
        with self.assertRaisesRegex(guard.GuardError, "for task T-002"):
            guard.validate_state(duplicate)

    def test_markdown_task_contract_must_match_state_exactly(self) -> None:
        markdown = """# Tasks

### T-001 : Backend

- **Test-IDs :**
  - T-001-T1 — backend test
- **Files in scope :**
  - `backend/src/One.java`
- **Dépendances :** aucune

### T-002 : Frontend

- **Test-IDs :** T-002-T1
- **Files in scope :** `frontend/app/page.tsx`
- **Dependencies :** none
"""
        guard.assert_state_matches_tasks(
            self.state(), markdown, repo_root=self.root
        )
        mismatched = self.state()
        mismatched["tasks"]["T-002"]["test_ids"] = ["T-002-T2"]
        with self.assertRaisesRegex(guard.GuardError, "T-002.test_ids"):
            guard.assert_state_matches_tasks(mismatched, markdown)

    def test_globs_parent_traversal_and_symlink_chains_are_rejected(self) -> None:
        for path in ("src/**/*.java", "../outside", "src/[ab].java", "src/"):
            with self.subTest(path=path), self.assertRaises(guard.GuardError):
                guard.normalize_scope_path(path)

        outside = self.root.parent / "outside-runtime-target"
        link = self.root / "linked"
        link.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(guard.GuardError, "symlink chain"):
            guard.validate_scope_path(self.root, "linked/file.txt")

    def test_unordered_overlap_is_rejected_but_dependency_serializes_it(self) -> None:
        state = self.state()
        state["tasks"]["T-002"]["files_in_scope"] = ["backend/src/One.java"]
        with self.assertRaisesRegex(guard.GuardError, "overlapping"):
            guard.validate_state(state, repo_root=self.root)

        state["tasks"]["T-002"]["dependencies"] = ["T-001"]
        guard.validate_state(state, repo_root=self.root)


class LeaseAndJournalTest(RepositoryTest):
    def test_disjoint_writers_overlap_but_conflict_waits_for_release(self) -> None:
        state = self.state()
        process_id = os.getpid()
        process_start = guard.process_start_token(process_id)
        first = guard.acquire_scope_lease(
            self.root,
            feature_id="feature-one",
            task_id="T-001",
            owner="worker-a",
            session_id="session-a",
            files_in_scope=["backend/src/One.java"],
            state=state,
            process_id=process_id,
            process_start=process_start,
            _now=100.0,
        )
        second = guard.acquire_scope_lease(
            self.root,
            feature_id="feature-one",
            task_id="T-002",
            owner="worker-b",
            session_id="session-b",
            files_in_scope=["frontend/app/page.tsx"],
            state=state,
            process_id=process_id,
            process_start=process_start,
            _now=100.0,
        )
        self.assertNotEqual(first["lease_id"], second["lease_id"])

        retry = guard.acquire_scope_lease(
            self.root,
            feature_id="feature-one",
            task_id="T-001",
            owner="worker-a",
            session_id="session-a",
            files_in_scope=["backend/src/One.java"],
            state=state,
            process_id=process_id,
            process_start=process_start,
            _now=101.0,
        )
        self.assertTrue(retry["idempotent"])
        with self.assertRaisesRegex(guard.GuardError, "conflicts"):
            guard.acquire_scope_lease(
                self.root,
                feature_id="feature-one",
                task_id="T-001",
                owner="worker-c",
                session_id="session-c",
                files_in_scope=["backend/src/One.java"],
                state=state,
                process_id=process_id,
                process_start=process_start,
                _now=102.0,
            )

        self.assertTrue(
            guard.release_scope_lease(
                self.root,
                lease_id=first["lease_id"],
                owner="worker-a",
                session_id="session-a",
            )
        )
        third = guard.acquire_scope_lease(
            self.root,
            feature_id="feature-one",
            task_id="T-001",
            owner="worker-c",
            session_id="session-c",
            files_in_scope=["backend/src/One.java"],
            state=state,
            process_id=process_id,
            process_start=process_start,
            _now=103.0,
        )
        self.assertEqual("T-001", third["task_id"])

    def test_lease_requires_matching_feature_ready_task_and_done_dependencies(
        self,
    ) -> None:
        state = self.state()
        state["tasks"]["T-003"] = copy.deepcopy(state["tasks"]["T-001"])
        state["tasks"]["T-003"].update(
            {
                "dependencies": ["T-001"],
                "test_ids": ["T-003-T1"],
                "files_in_scope": ["docs/three.md"],
                "kanban_id": None,
                "issue": None,
                "branch": None,
                "pr": None,
            }
        )
        arguments = {
            "repo_root": self.root,
            "task_id": "T-003",
            "owner": "worker-c",
            "session_id": "session-c",
            "files_in_scope": ["docs/three.md"],
            "state": state,
        }

        with self.assertRaisesRegex(guard.GuardError, "does not match"):
            guard.acquire_scope_lease(feature_id="other-feature", **arguments)

        with self.assertRaisesRegex(guard.GuardError, "dependencies are not done"):
            guard.acquire_scope_lease(feature_id="feature-one", **arguments)

        state["tasks"]["T-003"].update({"phase": "blocked", "status": "blocked"})
        with self.assertRaisesRegex(guard.GuardError, "not lease-ready"):
            guard.acquire_scope_lease(feature_id="feature-one", **arguments)

        state["tasks"]["T-003"].update({"phase": "pending", "status": "ready"})
        state["tasks"]["T-001"].update(
            {
                "phase": "done",
                "status": "done",
                "red_at": "2026-08-01T00:00:00Z",
                "red_test_signature": "OneTest.red",
                "red_failure_excerpt": "expected failure before implementation",
                "green_at": "2026-08-01T00:01:00Z",
            }
        )
        acquired = guard.acquire_scope_lease(feature_id="feature-one", **arguments)
        self.assertEqual("T-003", acquired["task_id"])

    def test_lease_heartbeat_and_stale_reclaim_bind_session_and_process_birth(self) -> None:
        state = self.state()
        process_id = os.getpid()
        process_start = guard.process_start_token(process_id)
        lease = guard.acquire_scope_lease(
            self.root,
            feature_id="feature-one",
            task_id="T-001",
            owner="worker-a",
            session_id="session-a",
            files_in_scope=["backend/src/One.java"],
            state=state,
            process_id=process_id,
            process_start=process_start,
            ttl_seconds=10,
            _now=100.0,
        )
        expiry = guard.heartbeat_scope_lease(
            self.root,
            lease_id=lease["lease_id"],
            owner="worker-a",
            session_id="session-a",
            process_id=process_id,
            process_start=process_start,
            ttl_seconds=10,
            _now=105.0,
        )
        self.assertEqual(115.0, expiry)
        with self.assertRaisesRegex(guard.GuardError, "identity mismatch"):
            guard.heartbeat_scope_lease(
                self.root,
                lease_id=lease["lease_id"],
                owner="worker-a",
                session_id="other-session",
                process_id=process_id,
                process_start=process_start,
                _now=106.0,
            )

        reclaimed = guard.acquire_scope_lease(
            self.root,
            feature_id="feature-one",
            task_id="T-001",
            owner="worker-b",
            session_id="session-b",
            files_in_scope=["backend/src/One.java"],
            state=state,
            process_id=process_id,
            process_start=process_start,
            _now=116.0,
        )
        self.assertIn(lease["lease_id"], reclaimed["reclaimed"])

    def test_state_max_workers_caps_disjoint_runtime_leases(self) -> None:
        state = self.state()
        state["tasks"]["T-003"] = copy.deepcopy(state["tasks"]["T-001"])
        state["tasks"]["T-003"].update(
            {
                "test_ids": ["T-003-T1"],
                "files_in_scope": ["docs/three.md"],
            }
        )
        process_id = os.getpid()
        process_start = guard.process_start_token(process_id)
        for task_id, owner, session, scope in (
            ("T-001", "worker-a", "session-a", "backend/src/One.java"),
            ("T-002", "worker-b", "session-b", "frontend/app/page.tsx"),
        ):
            guard.acquire_scope_lease(
                self.root,
                feature_id="feature-one",
                task_id=task_id,
                owner=owner,
                session_id=session,
                files_in_scope=[scope],
                state=state,
                process_id=process_id,
                process_start=process_start,
            )
        with self.assertRaisesRegex(guard.GuardError, "2 allowed worker leases"):
            guard.acquire_scope_lease(
                self.root,
                feature_id="feature-one",
                task_id="T-003",
                owner="worker-c",
                session_id="session-c",
                files_in_scope=["docs/three.md"],
                state=state,
                process_id=process_id,
                process_start=process_start,
            )

    def test_incomplete_v1_migration_cannot_acquire_lease_or_pass_red_gate(self) -> None:
        legacy = {
            "feature_id": "feature-one",
            "active_task": None,
            "tasks": {
                "T-001": {
                    "phase": "pending",
                    "files_in_scope": ["backend/src/One.java"],
                    "red_at": None,
                    "red_test_signature": None,
                    "red_failure_excerpt": None,
                    "green_at": None,
                }
            },
        }
        migrated = guard.migrate_state_v1(legacy)
        with self.assertRaisesRegex(guard.GuardError, "incomplete migrated"):
            guard.acquire_scope_lease(
                self.root,
                feature_id="feature-one",
                task_id="T-001",
                owner="worker-a",
                session_id="session-a",
                files_in_scope=["backend/src/One.java"],
                state=migrated,
            )
        with self.assertRaisesRegex(guard.GuardError, "RED/build"):
            guard.validate_red_gate(
                migrated,
                task_id="T-001",
                changed_paths=["backend/src/One.java"],
                production_paths=["backend/src/One.java"],
                repo_root=self.root,
            )

    def test_linked_worktrees_share_the_runtime_lock_directory(self) -> None:
        linked = self.root.parent / f"{self.root.name}-linked"
        try:
            self.git("worktree", "add", "-q", "-b", "linked-test", str(linked))
            self.assertEqual(
                guard.git_common_dir(self.root), guard.git_common_dir(linked)
            )
            self.assertEqual(
                guard.runtime_directory(self.root), guard.runtime_directory(linked)
            )
        finally:
            if linked.exists():
                self.git("worktree", "remove", "--force", str(linked))

    def test_runtime_metadata_directory_symlink_is_rejected(self) -> None:
        common = guard.git_common_dir(self.root)
        target = self.root / "metadata-target"
        target.mkdir()
        (common / "sdd-runtime").symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(guard.GuardError, "directory chain is unsafe"):
            guard.runtime_directory(self.root)

    def test_task_journal_is_immutable_and_idempotent(self) -> None:
        event = {"phase": "red", "result": "FAIL", "files_modified": []}
        path = guard.append_job_event(
            self.root,
            feature_id="feature-one",
            task_id="T-001",
            event_id="001-red",
            event=event,
        )
        retry = guard.append_job_event(
            self.root,
            feature_id="feature-one",
            task_id="T-001",
            event_id="001-red",
            event=event,
        )
        self.assertEqual(path, retry)
        self.assertEqual(
            1,
            guard.verify_job_journal(
                self.root, feature_id="feature-one", task_id="T-001"
            ),
        )
        with self.assertRaisesRegex(guard.GuardError, "mutated"):
            guard.append_job_event(
                self.root,
                feature_id="feature-one",
                task_id="T-001",
                event_id="001-red",
                event={"phase": "green"},
            )

        path.write_text("tampered\n", encoding="utf-8")
        with self.assertRaisesRegex(guard.GuardError, "mutated"):
            guard.verify_job_journal(
                self.root, feature_id="feature-one", task_id="T-001"
            )

    def test_task_journal_detects_deleted_and_foreign_events(self) -> None:
        path = guard.append_job_event(
            self.root,
            feature_id="feature-one",
            task_id="T-001",
            event_id="001-red",
            event={"phase": "red"},
        )
        path.unlink()
        with self.assertRaisesRegex(guard.GuardError, "deleted"):
            guard.verify_job_journal(
                self.root, feature_id="feature-one", task_id="T-001"
            )

        # Restore a clean fixture in another task, then prove an unmanifested
        # file cannot be smuggled into its immutable journal.
        guard.append_job_event(
            self.root,
            feature_id="feature-one",
            task_id="T-002",
            event_id="001-red",
            event={"phase": "red"},
        )
        foreign = self.root / ".specs/feature-one/jobs/T-002/foreign.json"
        foreign.write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(guard.GuardError, "unmanifested"):
            guard.verify_job_journal(
                self.root, feature_id="feature-one", task_id="T-002"
            )

    def test_worker_can_only_touch_scope_and_its_task_local_journal(self) -> None:
        allowed = guard.validate_worker_changes(
            feature_id="feature-one",
            task_id="T-001",
            changed_paths=[
                "backend/src/One.java",
                ".specs/feature-one/jobs/T-001/001-red.json",
            ],
            files_in_scope=["backend/src/One.java"],
        )
        self.assertEqual(2, len(allowed))
        for shared in (
            ".specs/feature-one/04-tasks.md",
            ".specs/feature-one/.tdd-state.json",
            ".specs/feature-one/05-implementation-log.md",
        ):
            with self.subTest(path=shared), self.assertRaisesRegex(
                guard.GuardError, "shared artifact"
            ):
                guard.validate_worker_changes(
                    feature_id="feature-one",
                    task_id="T-001",
                    changed_paths=[shared],
                    files_in_scope=["backend/src/One.java"],
                )

        with self.assertRaisesRegex(guard.GuardError, "outside its scope"):
            guard.validate_worker_changes(
                feature_id="feature-one",
                task_id="T-001",
                changed_paths=["frontend/app/page.tsx"],
                files_in_scope=["backend/src/One.java"],
            )

        with self.assertRaisesRegex(guard.GuardError, "outside its scope"):
            guard.validate_worker_changes(
                feature_id="feature-one",
                task_id="T-001",
                changed_paths=[".specs/feature-one/jobs/T-002/001-red.json"],
                files_in_scope=["backend/src/One.java"],
            )

    def test_fingerprint_detects_out_of_scope_changes(self) -> None:
        allowed = self.root / "backend/src/One.java"
        allowed.parent.mkdir(parents=True)
        allowed.write_text("one\n", encoding="utf-8")
        other = self.root / "notes.txt"
        other.write_text("before\n", encoding="utf-8")
        before = guard.repository_fingerprint(
            self.root, excluded_paths=["backend/src/One.java"]
        )
        allowed.write_text("two\n", encoding="utf-8")
        after_allowed = guard.repository_fingerprint(
            self.root, excluded_paths=["backend/src/One.java"]
        )
        guard.assert_fingerprint_unchanged(before, after_allowed)

        other.write_text("after\n", encoding="utf-8")
        after_other = guard.repository_fingerprint(
            self.root, excluded_paths=["backend/src/One.java"]
        )
        with self.assertRaisesRegex(guard.GuardError, "notes.txt"):
            guard.assert_fingerprint_unchanged(before, after_other)

    def test_fingerprint_includes_ignored_files_modes_and_staged_index(self) -> None:
        (self.root / ".gitignore").write_text("ignored.log\n", encoding="utf-8")
        ignored = self.root / "ignored.log"
        ignored.write_text("before\n", encoding="utf-8")
        executable = self.root / "script.sh"
        executable.write_text("#!/bin/sh\n", encoding="utf-8")
        executable.chmod(0o644)
        before = guard.repository_fingerprint(self.root)

        ignored.write_text("after\n", encoding="utf-8")
        executable.chmod(0o755)
        (self.root / "README.md").write_text("staged\n", encoding="utf-8")
        before_stage = guard.repository_fingerprint(self.root)
        self.git("add", "README.md")
        after = guard.repository_fingerprint(self.root)

        with self.assertRaisesRegex(guard.GuardError, "working:ignored.log"):
            guard.assert_fingerprint_unchanged(before, after)
        with self.assertRaisesRegex(guard.GuardError, "index:README.md"):
            guard.assert_fingerprint_unchanged(before_stage, after)
        self.assertNotEqual(
            before["working:script.sh"], after["working:script.sh"]
        )


class MigrationCliTest(RepositoryTest):
    def legacy(self) -> dict:
        return {
            "feature_id": "feature-one",
            "active_task": None,
            "tasks": {
                "T-001": {
                    "phase": "pending",
                    "red_at": None,
                    "red_test_signature": None,
                    "red_failure_excerpt": None,
                    "green_at": None,
                    "files_in_scope": ["backend/src/One.java"],
                }
            },
        }

    def run_migration(
        self,
        *,
        output: str = ".specs/feature-one/.tdd-state.candidate.json",
        expected_output_token: str = "absent",
        expected: int = 0,
    ) -> dict:
        source = self.root / ".specs/feature-one/.tdd-state.json"
        result = subprocess.run(
            [
                sys.executable,
                str(Path(guard.__file__)),
                "migrate-state",
                "--repo-root",
                str(self.root),
                "--state",
                str(source),
                "--output",
                output,
                "--expected-token",
                guard.token_for(source.read_bytes()),
                "--expected-output-token",
                expected_output_token,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(expected, result.returncode, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def setUp(self) -> None:
        super().setUp()
        source = self.root / ".specs/feature-one/.tdd-state.json"
        source.parent.mkdir(parents=True)
        source.write_bytes(guard.canonical_json(self.legacy()))

    def test_migration_writes_only_canonical_candidate_under_lock_and_cas(self) -> None:
        result = self.run_migration()
        self.assertTrue(result["migrated"])
        output = self.root / ".specs/feature-one/.tdd-state.candidate.json"
        migrated = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(2, migrated["schema_version"])
        self.assertFalse(migrated["migration"]["contract_complete"])

        failed = self.run_migration(expected=2)
        self.assertIn("output CAS failed", failed["error"])

    def test_migration_refuses_noncanonical_or_symlink_output(self) -> None:
        outside = self.run_migration(output="/tmp/state-v2.json", expected=2)
        self.assertIn("escapes repository", outside["error"])

        target = self.root / ".specs/feature-one/.tdd-state.candidate.json"
        target.symlink_to(self.root / "README.md")
        unsafe = self.run_migration(expected=2)
        self.assertIn("is a symlink", unsafe["error"])


class FanInTransactionTest(RepositoryTest):
    feature_id = "feature-one"

    def setUp(self) -> None:
        super().setUp()
        self.feature = self.root / ".specs" / self.feature_id
        self.feature.mkdir(parents=True)
        self.state_path = self.feature / ".tdd-state.json"
        self.tasks_path = self.feature / "04-tasks.md"
        previous_state = self.state()
        previous_state["mode"] = "sequential"
        previous_state["max_workers"] = 1
        self.state_path.write_bytes(guard.canonical_json(previous_state))
        self.tasks_path.write_text("old tasks\n", encoding="utf-8")
        next_state = self.state()
        next_state["revision"] = 1
        self.previous_state_data = guard.canonical_json(previous_state)
        self.next_state_data = guard.canonical_json(next_state)
        self.artifacts = {
            f".specs/{self.feature_id}/.tdd-state.json": self.next_state_data,
            f".specs/{self.feature_id}/04-tasks.md": b"new tasks\n",
        }
        self.expected = {
            path: guard.token_for((self.root / path).read_bytes())
            for path in self.artifacts
        }

    def call(self, transaction_id: str, crash: str | None = None) -> dict:
        return guard.transactional_fan_in(
            self.root,
            feature_id=self.feature_id,
            transaction_id=transaction_id,
            actor="synthesizer",
            artifacts=self.artifacts,
            expected_tokens=self.expected,
            _crash_point=crash,
        )

    def test_fan_in_commits_once_and_retry_is_idempotent(self) -> None:
        result = self.call("wave-001")
        self.assertTrue(result["committed"])
        self.assertFalse(result["idempotent"])
        retry = self.call("wave-001")
        self.assertTrue(retry["idempotent"])
        self.assertEqual(self.next_state_data, self.state_path.read_bytes())
        self.assertEqual(b"new tasks\n", self.tasks_path.read_bytes())

    def test_crash_before_marker_rolls_back_complete_old_set(self) -> None:
        with self.assertRaises(guard.InjectedCrash):
            self.call("wave-before", "before-marker")

        outcome = guard.recover_fan_in(
            self.root,
            feature_id=self.feature_id,
            transaction_id="wave-before",
        )
        self.assertEqual("rolled-back", outcome)
        self.assertEqual(self.previous_state_data, self.state_path.read_bytes())
        self.assertEqual(b"old tasks\n", self.tasks_path.read_bytes())

    def test_crash_after_marker_rolls_forward_complete_new_set(self) -> None:
        with self.assertRaises(guard.InjectedCrash):
            self.call("wave-after", "after-marker")

        outcome = guard.recover_fan_in(
            self.root,
            feature_id=self.feature_id,
            transaction_id="wave-after",
        )
        self.assertEqual("committed", outcome)
        self.assertEqual(self.next_state_data, self.state_path.read_bytes())
        self.assertEqual(b"new tasks\n", self.tasks_path.read_bytes())

    def test_cas_actor_and_target_guards_fail_before_writing(self) -> None:
        with self.assertRaisesRegex(guard.GuardError, "synthesizer"):
            guard.transactional_fan_in(
                self.root,
                feature_id=self.feature_id,
                transaction_id="bad-actor",
                actor="worker",
                artifacts=self.artifacts,
                expected_tokens=self.expected,
            )
        wrong = dict(self.expected)
        wrong[f".specs/{self.feature_id}/04-tasks.md"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(guard.GuardError, "CAS failed"):
            guard.transactional_fan_in(
                self.root,
                feature_id=self.feature_id,
                transaction_id="bad-cas",
                actor="synthesizer",
                artifacts=self.artifacts,
                expected_tokens=wrong,
            )
        self.assertEqual(b"old tasks\n", self.tasks_path.read_bytes())

    def test_fan_in_recovery_is_namespaced_per_worktree(self) -> None:
        linked = self.root.parent / f"{self.root.name}-fan-in-linked"
        try:
            self.git("worktree", "add", "-q", "-b", "fan-in-linked", str(linked))
            with self.assertRaises(guard.InjectedCrash):
                self.call("same-id", "after-marker")
            self.assertIsNone(
                guard.recover_fan_in(
                    linked,
                    feature_id=self.feature_id,
                    transaction_id="same-id",
                )
            )
            self.assertFalse((linked / ".specs" / self.feature_id).exists())
            self.assertEqual(
                "committed",
                guard.recover_fan_in(
                    self.root,
                    feature_id=self.feature_id,
                    transaction_id="same-id",
                ),
            )
        finally:
            if linked.exists():
                self.git("worktree", "remove", "--force", str(linked))

    def test_fan_in_refuses_tampered_marker_and_changed_head(self) -> None:
        with self.assertRaises(guard.InjectedCrash):
            self.call("tampered", "after-marker")
        _, marker_path, _ = guard._transaction_paths(
            self.root, self.feature_id, "tampered"
        )
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        marker["targets"][f".specs/{self.feature_id}/04-tasks.md"] = (
            "sha256:" + "0" * 64
        )
        marker_path.write_bytes(guard.canonical_json(marker))
        with self.assertRaisesRegex(guard.GuardError, "targets"):
            guard.recover_fan_in(
                self.root,
                feature_id=self.feature_id,
                transaction_id="tampered",
            )

        # Use a fresh transaction fixture to prove that recovery is also bound
        # to the exact worktree HEAD observed during preparation.
        self.tearDown()
        self.setUp()
        with self.assertRaises(guard.InjectedCrash):
            self.call("old-head", "before-marker")
        (self.root / "README.md").write_text("new head\n", encoding="utf-8")
        self.git("add", "README.md")
        self.git("commit", "-qm", "move head")
        with self.assertRaisesRegex(guard.GuardError, "identity mismatch"):
            guard.recover_fan_in(
                self.root,
                feature_id=self.feature_id,
                transaction_id="old-head",
            )

    def test_fan_in_rejects_symlink_target_and_incomplete_migration(self) -> None:
        outside = self.root / "outside-tasks"
        outside.write_text("outside\n", encoding="utf-8")
        self.tasks_path.unlink()
        self.tasks_path.symlink_to(outside)
        with self.assertRaisesRegex(guard.GuardError, "symlink chain"):
            self.call("symlink")

        self.tasks_path.unlink()
        self.tasks_path.write_text("old tasks\n", encoding="utf-8")
        legacy = {
            "feature_id": self.feature_id,
            "active_task": None,
            "tasks": {
                "T-001": {
                    "phase": "pending",
                    "files_in_scope": ["backend/src/One.java"],
                    "red_at": None,
                    "red_test_signature": None,
                    "red_failure_excerpt": None,
                    "green_at": None,
                }
            },
        }
        migrated = guard.canonical_json(guard.migrate_state_v1(legacy))
        artifacts = dict(self.artifacts)
        artifacts[f".specs/{self.feature_id}/.tdd-state.json"] = migrated
        with self.assertRaisesRegex(guard.GuardError, "incomplete v1 migration"):
            guard.transactional_fan_in(
                self.root,
                feature_id=self.feature_id,
                transaction_id="incomplete",
                actor="synthesizer",
                artifacts=artifacts,
                expected_tokens=self.expected,
            )


if __name__ == "__main__":
    unittest.main()
