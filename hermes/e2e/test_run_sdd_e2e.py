#!/usr/bin/env python3
"""Unit tests for the Hermes SDD E2E runner; no real LLM is called."""

from __future__ import annotations

import contextlib
import ast
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import textwrap
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).with_name("run_sdd_e2e.py")
SPEC = importlib.util.spec_from_file_location("run_sdd_e2e", MODULE_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)

FEATURE_ID = "2026-07-30-service-state-e2e"


FAKE_HERMES = r'''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import re
import sys
import time

args = sys.argv[1:]
state_dir = Path(os.environ["FAKE_HERMES_STATE"])
state_dir.mkdir(parents=True, exist_ok=True)
with (state_dir / "calls.jsonl").open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(args) + "\n")

if args == ["--version"]:
    print("Hermes Agent v0.19.0 (2026.7.20)")
    raise SystemExit(0)

if "profile" in args and "info" in args:
    version = os.environ.get("FAKE_PROFILE_VERSION", "0.4.7")
    print(f"Distribution: staaack-sdd\nVersion:      {version}\nRequires:     Hermes >=0.19.0")
    raise SystemExit(0)

if "sessions" in args and "export" in args:
    output = Path(args[args.index("export") + 1])
    session_id = args[args.index("--session-id") + 1]
    if session_id == "fake-plan-1":
        record = {
            "id": session_id,
            "messages": [
                {"role": "assistant", "tool_calls": [{"function": {"name": "delegate_task", "arguments": "spring-architect react-nextjs-architect"}}]},
                {"role": "tool", "content": "spring-architect ready; react-nextjs-architect ready; files_modified: []"},
            ],
        }
    else:
        record = {"id": session_id, "messages": [{"role": "user", "content": "approve"}]}
    output.write_text(json.dumps(record) + "\n", encoding="utf-8")
    print(f"Exported 1 session to {output}")
    raise SystemExit(0)

project = Path.cwd()
feature_match = re.search(r"(\d{4}-\d{2}-\d{2}-service-state-e2e)", " ".join(args))
feature_id = feature_match.group(1) if feature_match else os.environ.get("FAKE_FEATURE_ID", "2026-07-30-service-state-e2e")
feature = project / ".specs" / feature_id

if "chat" in args:
    prompt = args[args.index("-q") + 1]
    if os.environ.get("FAKE_SLEEP_ON") and os.environ["FAKE_SLEEP_ON"] in prompt:
        time.sleep(60)
    if prompt.startswith("/sdd-spec "):
        feature.mkdir(parents=True, exist_ok=True)
        (feature / "01-spec.md").write_text("""# Spec\n\n## Acceptance Criteria\n\n- AC-001: backend state\n- AC-002: frontend state\n\n## Open Questions\n\n- (aucune)\n""", encoding="utf-8")
        if os.environ.get("FAKE_MUTATE_APP") == "1":
            (project / "frontend/app/page.tsx").write_text("mutated\n", encoding="utf-8")
    elif prompt.startswith("/sdd-spec-review "):
        feature.mkdir(parents=True, exist_ok=True)
        (feature / "02-spec-review.md").write_text("""# Review\n\n## Summary\n\n- verdict: ready-for-approval\n- acs_total: 2\n- acs_failed: 0\n- open_questions: 0\n- reviewer: en attente\n- reviewed_at: en attente\n- decision_evidence: en attente\n- decision_evidence_mode: en attente\n""", encoding="utf-8")
    elif prompt == "approve":
        review = feature / "02-spec-review.md"
        review.write_text("""# Review\n\n## Summary\n\n- verdict: approve\n- acs_total: 2\n- acs_failed: 0\n- open_questions: 0\n- reviewer: automated-e2e\n- reviewed_at: 2026-07-30T12:00:00Z\n- decision_evidence: approve\n- decision_evidence_mode: direct-response\n""", encoding="utf-8")
    print("fake response")
    print("\nsession_id: fake-chat-1", file=sys.stderr)
    raise SystemExit(0)

if "-z" in args:
    feature.mkdir(parents=True, exist_ok=True)
    (feature / "03-design.candidate.md").write_text("""# Design\n\n## Summary\n\n- status: draft\n- stacks: full-stack\n- architect_roles: spring-architect, react-nextjs-architect\n\n## Delegation Record\n\n| spring-architect | ready | backend | aucun |\n| react-nextjs-architect | ready | frontend | aucun |\n""", encoding="utf-8")
    (feature / "04-tasks.candidate.md").write_text("""# Tasks\n\n### T-001: Backend\n- Origine: spring-architect:T-001\n- AC-IDs: AC-001\n- Test-IDs: T-001-T1\n\n### T-002: Frontend\n- Origine: react-nextjs-architect:T-001\n- AC-IDs: AC-002\n- Test-IDs: T-002-T1\n""", encoding="utf-8")
    usage_file = Path(args[args.index("--usage-file") + 1])
    usage_file.write_text(json.dumps({"session_id": "fake-plan-1", "completed": True}) + "\n", encoding="utf-8")
    print("plan candidates ready")
    raise SystemExit(0)

print("unhandled fake invocation", args, file=sys.stderr)
raise SystemExit(2)
'''


class RunnerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sdd-e2e-runner-test-")
        self.root = Path(self.temp.name)
        self.state = self.root / "fake-state"
        self.fake = self.root / "fake-hermes"
        self.fake.write_text(textwrap.dedent(FAKE_HERMES), encoding="utf-8")
        self.fake.chmod(self.fake.stat().st_mode | stat.S_IXUSR)

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self, *extra: str) -> tuple[int, str, str]:
        argv = [
            "--hermes-bin",
            str(self.fake),
            "--profile",
            "staaack",
            "--temp-root",
            str(self.root),
            "--feature-id",
            FEATURE_ID,
            "--timeout",
            "5",
            *extra,
        ]
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, {"FAKE_HERMES_STATE": str(self.state)}, clear=False):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = RUNNER.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_fake_hermes_completes_full_flow(self):
        code, stdout, stderr = self.invoke()
        self.assertEqual(0, code, stderr)
        result = json.loads(stdout)
        self.assertEqual("passed", result["status"])
        self.assertFalse(result["approval_is_human"])
        self.assertTrue(result["checks"]["full_stack_delegation_proved"])
        run_dir = Path(result["run_dir"])
        self.assertTrue((run_dir / "logs/result.json").is_file())
        self.assertTrue((run_dir / "project/.specs" / FEATURE_ID / "03-design.candidate.md").is_file())

        calls = [json.loads(line) for line in (self.state / "calls.jsonl").read_text(encoding="utf-8").splitlines()]
        approval_calls = [call for call in calls if "-q" in call and call[call.index("-q") + 1] == "approve"]
        self.assertEqual(1, len(approval_calls), "approve doit être un subprocess/tour distinct")
        resumed = [call[call.index("--resume") + 1] for call in calls if "--resume" in call]
        self.assertTrue(resumed)
        self.assertEqual({"fake-chat-1"}, set(resumed))

    def test_dry_run_neither_invokes_hermes_nor_creates_sandbox(self):
        code, stdout, stderr = self.invoke("--dry-run")
        self.assertEqual(0, code, stderr)
        result = json.loads(stdout)
        self.assertTrue(result["dry_run"])
        self.assertFalse(result["creates_sandbox"])
        self.assertFalse((self.state / "calls.jsonl").exists())
        self.assertEqual([], list(self.root.glob("sdd-hermes-e2e-*")))

    def test_failure_preserves_sandbox_and_logs(self):
        with mock.patch.dict(os.environ, {"FAKE_MUTATE_APP": "1"}, clear=False):
            code, _stdout, stderr = self.invoke()
        self.assertEqual(1, code)
        failure = json.loads(stderr)
        self.assertIn("hors de .specs", failure["error"])
        run_dir = Path(failure["run_dir"])
        self.assertTrue(run_dir.is_dir())
        self.assertTrue((run_dir / "logs/failure.json").is_file())

    def test_cleanup_occurs_only_after_success_and_explicit_flag(self):
        code, stdout, stderr = self.invoke("--cleanup-on-success")
        self.assertEqual(0, code, stderr)
        run_dir = Path(json.loads(stdout)["run_dir"])
        self.assertFalse(run_dir.exists())

    def test_profile_below_047_fails_and_preserves_logs(self):
        with mock.patch.dict(os.environ, {"FAKE_PROFILE_VERSION": "0.4.6"}, clear=False):
            code, _stdout, stderr = self.invoke()
        self.assertEqual(1, code)
        failure = json.loads(stderr)
        self.assertIn("Profil 0.4.6 < 0.4.7", failure["error"])
        self.assertTrue(Path(failure["run_dir"]).is_dir())

    def test_timeout_terminates_process_group_and_preserves_run(self):
        argv = [
            "--hermes-bin", str(self.fake), "--profile", "staaack",
            "--temp-root", str(self.root), "--feature-id", FEATURE_ID,
            "--timeout", "0.2",
        ]
        stdout = io.StringIO()
        stderr = io.StringIO()
        env = {"FAKE_HERMES_STATE": str(self.state), "FAKE_SLEEP_ON": "/sdd-spec"}
        with mock.patch.dict(os.environ, env, clear=False):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = RUNNER.main(argv)
        self.assertEqual(1, code)
        failure = json.loads(stderr.getvalue())
        self.assertIn("Délai de 0.2s dépassé", failure["error"])
        self.assertTrue(Path(failure["run_dir"]).is_dir())

    def test_cleanup_validator_rejects_unmarked_directory(self):
        unmarked = self.root / "sdd-hermes-e2e-unmarked"
        unmarked.mkdir()
        with self.assertRaises(RUNNER.E2EError):
            RUNNER.validate_cleanup_target(unmarked, self.root)

    def test_subprocesses_never_use_shell_and_start_a_process_group(self):
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        popen_calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "subprocess"
            and node.func.attr == "Popen"
        ]
        self.assertEqual(1, len(popen_calls))
        keywords = {keyword.arg: keyword.value for keyword in popen_calls[0].keywords}
        self.assertNotIn("shell", keywords)
        self.assertIsInstance(keywords.get("start_new_session"), ast.Constant)
        self.assertTrue(keywords["start_new_session"].value)

    def test_test_id_references_outside_definitions_may_repeat(self):
        text = """# Tasks

### T-001: Backend
- Test-IDs:
  - T-001-T1 — first
  - T-001-T2 — second
- Notes: commencer avec T-001-T1 et T-001-T2.

### T-002: Frontend
- Test-IDs: T-002-T1
| T-002-T1 | referenced in a table |
"""
        task_ids, test_ids = RUNNER.parse_test_id_definitions(text)
        self.assertEqual(["T-001", "T-002"], task_ids)
        self.assertEqual(["T-001-T1", "T-001-T2", "T-002-T1"], test_ids)

    def test_duplicate_test_id_definition_is_rejected(self):
        text = """### T-001: Backend
- Test-IDs:
  - T-001-T1 — first
  - T-001-T1 — duplicate definition
"""
        with self.assertRaisesRegex(RUNNER.E2EError, "dupliquées"):
            RUNNER.parse_test_id_definitions(text)

    def test_test_id_with_wrong_task_prefix_is_rejected(self):
        text = """### T-001: Backend
- Test-IDs: T-002-T1
"""
        with self.assertRaisesRegex(RUNNER.E2EError, "Préfixe"):
            RUNNER.parse_test_id_definitions(text)

    def test_each_task_requires_a_test_id_definition(self):
        text = """### T-001: Backend
- Test-IDs: T-001-T1

### T-002: Frontend
- Notes: T-002-T1 is only a reference.
"""
        with self.assertRaisesRegex(RUNNER.E2EError, "pour T-002"):
            RUNNER.parse_test_id_definitions(text)

    def test_validate_run_requires_explicit_plan_transcript(self):
        run_dir = RUNNER.create_run_dir(self.root.resolve())
        code, _stdout, stderr = self.invoke(
            "--validate-run", str(run_dir),
            "--feature-id", FEATURE_ID,
        )
        self.assertEqual(1, code)
        self.assertIn("--plan-transcript est obligatoire", stderr)

    def test_validate_run_reuses_artifacts_without_invoking_hermes(self):
        run_dir = RUNNER.create_run_dir(self.root.resolve())
        project = run_dir / "project"
        feature = project / ".specs" / FEATURE_ID
        feature.mkdir(parents=True)
        (feature / "01-spec.md").write_text(
            "- AC-001: backend\n- AC-002: frontend\n", encoding="utf-8"
        )
        (feature / "03-design.candidate.md").write_text(
            "- status: draft\n- stacks: full-stack\n"
            "spring-architect\nreact-nextjs-architect\n",
            encoding="utf-8",
        )
        (feature / "04-tasks.candidate.md").write_text(
            """### T-001: Backend
- Origine: spring-architect:T-001
- AC-IDs: AC-001
- Test-IDs: T-001-T1
- Notes: T-001-T1 may be referenced again.

### T-002: Frontend
- Origine: react-nextjs-architect:T-001
- AC-IDs: AC-002
- Test-IDs: T-002-T1
""",
            encoding="utf-8",
        )
        transcript = run_dir / "logs/session-01-plan.jsonl"
        transcript.write_text(
            '{"tool":"delegate_task","roles":["spring-architect","react-nextjs-architect"]}\n',
            encoding="utf-8",
        )

        code, stdout, stderr = self.invoke(
            "--validate-run", str(run_dir),
            "--feature-id", FEATURE_ID,
            "--plan-transcript", str(transcript),
        )

        self.assertEqual(0, code, stderr)
        result = json.loads(stdout)
        self.assertEqual("revalidated", result["status"])
        self.assertEqual(0, result["llm_calls"])
        self.assertFalse((self.state / "calls.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
