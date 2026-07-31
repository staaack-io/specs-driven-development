#!/usr/bin/env python3
"""Tests for deterministic Hermes unittest discovery and execution."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import run_python_tests as runner


class RunPythonTestsTest(unittest.TestCase):
    def repository(self, destination: Path) -> Path:
        root = destination / "repository"
        (root / "hermes/scripts").mkdir(parents=True)
        (root / ".gitignore").write_text("ignored/\n__pycache__/\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", ".gitignore"], cwd=root, check=True)
        return root

    def add(self, root: Path, relative: str, content: str) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", relative], cwd=root, check=True)
        return path

    def run_runner(self, root: Path) -> tuple[int, str]:
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            status = runner.main(root)
        return status, output.getvalue()

    def test_inventory_includes_tracked_and_untracked_nonignored_tests(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            tracked = self.add(root, "hermes/a/test_tracked.py", "import unittest\n")
            untracked = root / "hermes/b/test_untracked.py"
            untracked.parent.mkdir(parents=True)
            untracked.write_text("import unittest\n", encoding="utf-8")
            outside = self.add(root, "tests/test_outside.py", "raise RuntimeError()\n")

            self.assertEqual(
                [tracked, untracked],
                runner.discover_test_files(root),
            )
            self.assertNotIn(outside, runner.discover_test_files(root))

    def test_ignored_test_file_is_not_discovered(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            kept = self.add(root, "hermes/test_kept.py", "import unittest\n")
            ignored = root / "hermes/ignored/test_ignored.py"
            ignored.parent.mkdir(parents=True)
            ignored.write_text("raise RuntimeError('must not run')\n", encoding="utf-8")
            (root / ".gitignore").write_text("hermes/ignored/\n", encoding="utf-8")

            self.assertEqual([kept], runner.discover_test_files(root))

    def test_unittest_without_main_block_is_executed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            self.add(
                root,
                "hermes/test_sample.py",
                "import unittest\n"
                "class SampleTest(unittest.TestCase):\n"
                "    def test_passes(self): self.assertTrue(True)\n",
            )

            status, output = self.run_runner(root)

            self.assertEqual(0, status, output)
            self.assertIn("All 1 Hermes test cases executed", output)

    def test_module_is_registered_for_postponed_dataclass_annotations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            self.add(
                root,
                "hermes/test_dataclass.py",
                "from __future__ import annotations\n"
                "from dataclasses import dataclass\n"
                "import unittest\n"
                "@dataclass\n"
                "class Payload: value: str\n"
                "class DataclassTest(unittest.TestCase):\n"
                "    def test_value(self): self.assertEqual('ok', Payload('ok').value)\n",
            )

            status, output = self.run_runner(root)

            self.assertEqual(0, status, output)

    def test_each_file_runs_in_a_fresh_process(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            first = self.add(
                root,
                "hermes/tests/test_a_leak.py",
                "import sys\n"
                "import types\n"
                "import unittest\n"
                "sys.modules['hermes_test_leak'] = types.ModuleType('hermes_test_leak')\n"
                "class LeakTest(unittest.TestCase):\n"
                "    def test_leak(self): self.assertIn('hermes_test_leak', sys.modules)\n",
            )
            second = self.add(
                root,
                "hermes/tests/test_b_clean.py",
                "import sys\n"
                "import unittest\n"
                "class CleanTest(unittest.TestCase):\n"
                "    def test_clean(self): self.assertNotIn('hermes_test_leak', sys.modules)\n",
            )

            output = io.StringIO()
            with redirect_stdout(output), redirect_stderr(output):
                status = runner.run_tests([first, second], root)

            self.assertEqual(0, status, output.getvalue())
            self.assertIn("All 2 Hermes test cases executed", output.getvalue())

    def test_system_exit_during_import_is_a_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            self.add(root, "hermes/test_exit.py", "raise SystemExit(0)\n")

            status, output = self.run_runner(root)

            self.assertEqual(1, status)
            self.assertIn("cannot load", output)

    def test_pytest_only_file_fails_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            self.add(root, "hermes/test_pytest.py", "def test_pytest_style(): pass\n")

            status, output = self.run_runner(root)

            self.assertEqual(1, status)
            self.assertIn("pytest-only files are unsupported", output)

    def test_file_with_only_skipped_cases_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            self.add(
                root,
                "hermes/test_skipped.py",
                "import unittest\n"
                "@unittest.skip('not runnable')\n"
                "class SkippedTest(unittest.TestCase):\n"
                "    def test_skipped(self): pass\n",
            )

            status, output = self.run_runner(root)

            self.assertEqual(1, status)
            self.assertIn("executed no non-skipped unittest cases", output)

    def test_symbolic_test_link_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            target = root / "outside.py"
            target.write_text("import unittest\n", encoding="utf-8")
            link = root / "hermes/test_link.py"
            try:
                link.symlink_to(target)
            except (NotImplementedError, OSError) as error:
                self.skipTest(f"symbolic links unavailable: {error}")
            subprocess.run(["git", "add", "hermes/test_link.py"], cwd=root, check=True)

            with self.assertRaisesRegex(RuntimeError, "unsafe Hermes test path"):
                runner.discover_test_files(root)

    def test_inventory_failure_is_not_a_silent_empty_success(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "hermes").mkdir()

            status, output = self.run_runner(root)

            self.assertEqual(1, status)
            self.assertIn("cannot enumerate repository tests", output)

    def test_worker_without_exactly_one_json_marker_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            test_file = self.add(
                root,
                "hermes/test_sample.py",
                "import unittest\n"
                "class SampleTest(unittest.TestCase):\n"
                "    def test_passes(self): pass\n",
            )
            worker = root / "fake_worker.py"
            worker.write_text("print('{}')\n", encoding="utf-8")
            output = io.StringIO()

            with redirect_stdout(output), redirect_stderr(output):
                status = runner.run_tests([test_file], root, worker=worker)

            self.assertEqual(1, status)
            self.assertIn("expected one 'HERMES_TEST_RESULT=' marker", output.getvalue())

    def test_worker_timeout_is_a_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            test_file = self.add(
                root,
                "hermes/test_sample.py",
                "import unittest\n"
                "class SampleTest(unittest.TestCase):\n"
                "    def test_passes(self): pass\n",
            )
            worker = root / "slow_worker.py"
            worker.write_text("import time\ntime.sleep(10)\n", encoding="utf-8")
            output = io.StringIO()

            with redirect_stdout(output), redirect_stderr(output):
                status = runner.run_tests(
                    [test_file],
                    root,
                    timeout_seconds=0.05,
                    worker=worker,
                )

            self.assertEqual(1, status)
            self.assertIn("timed out", output.getvalue())

    def test_worker_with_inconsistent_counts_is_rejected(self) -> None:
        payload = {
            "version": runner.PROTOCOL_VERSION,
            "ok": True,
            "discovered": 1,
            "executed": 2,
            "skipped": 0,
            "detail": "",
            "output": "",
        }
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=runner.RESULT_MARKER + json.dumps(payload),
            stderr="",
        )

        with self.assertRaisesRegex(RuntimeError, "inconsistent test counts"):
            runner.worker_result(completed)


if __name__ == "__main__":
    unittest.main()
