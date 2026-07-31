#!/usr/bin/env python3
"""Tests for deterministic Hermes unittest discovery and execution."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

import run_python_test_file as worker
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
                    worker_grace_seconds=0.1,
                )

            self.assertEqual(1, status)
            self.assertIn("timed out", output.getvalue())

    @unittest.skipUnless(
        sys.platform.startswith("linux"),
        "Linux child-subreaper support is required",
    )
    def test_outer_timeout_reaps_worker_detached_test_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            test_file = self.add(
                root,
                "hermes/test_sample.py",
                "import unittest\n"
                "class SampleTest(unittest.TestCase):\n"
                "    def test_passes(self): pass\n",
            )
            pid_file = root / "detached-test.pid"
            detached_test = (
                "import os\n"
                "from pathlib import Path\n"
                "import signal\n"
                "import time\n"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                f"Path({str(pid_file)!r}).write_text(str(os.getpid()))\n"
                "while True: time.sleep(0.05)\n"
            )
            fake_worker = root / "wedged_worker.py"
            fake_worker.write_text(
                "import signal\n"
                "import subprocess\n"
                "import sys\n"
                "import time\n"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                "subprocess.Popen(\n"
                f"    [sys.executable, '-c', {detached_test!r}],\n"
                "    start_new_session=True,\n"
                ")\n"
                f"while not __import__('pathlib').Path({str(pid_file)!r}).exists():\n"
                "    time.sleep(0.01)\n"
                "while True: time.sleep(0.05)\n",
                encoding="utf-8",
            )
            output = io.StringIO()

            with redirect_stdout(output), redirect_stderr(output):
                status = runner.run_tests(
                    [test_file],
                    root,
                    timeout_seconds=0.2,
                    worker=fake_worker,
                    worker_grace_seconds=0.2,
                )

            self.assertEqual(1, status)
            self.assertIn("supervisor timed out", output.getvalue())
            detached_pid = int(pid_file.read_text(encoding="utf-8"))
            with self.assertRaises(ProcessLookupError):
                os.kill(detached_pid, 0)

    @unittest.skipUnless(os.name == "posix", "POSIX process signals are required")
    def test_outer_timeout_reaps_adopted_test_without_process_listing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            pid_file = root / "stopped-worker-test.pid"
            test_file = self.add(
                root,
                "hermes/test_stop_worker.py",
                "import os\n"
                "from pathlib import Path\n"
                "import signal\n"
                "import time\n"
                "import unittest\n"
                "class StopWorkerTest(unittest.TestCase):\n"
                "    def test_stop_worker(self):\n"
                f"        Path({str(pid_file)!r}).write_text(str(os.getpid()))\n"
                "        os.kill(os.getppid(), signal.SIGSTOP)\n"
                "        while True: time.sleep(0.05)\n",
            )
            output = io.StringIO()
            original_cleanup = runner.test_file_worker.kill_and_reap_linux_descendants

            def unavailable_process_listing() -> None:
                raise RuntimeError("process listing unavailable")

            runner.test_file_worker.kill_and_reap_linux_descendants = (
                unavailable_process_listing
            )
            try:
                with redirect_stdout(output), redirect_stderr(output):
                    status = runner.run_tests(
                        [test_file],
                        root,
                        timeout_seconds=0.2,
                        worker_grace_seconds=0.2,
                    )
            finally:
                runner.test_file_worker.kill_and_reap_linux_descendants = (
                    original_cleanup
                )

            self.assertEqual(1, status)
            self.assertIn("supervisor timed out", output.getvalue())
            test_pid = int(pid_file.read_text(encoding="utf-8"))
            with self.assertRaises(ProcessLookupError):
                os.kill(test_pid, 0)

    @unittest.skipUnless(
        os.name == "posix" and not sys.platform.startswith("linux"),
        "non-Linux POSIX process tagging is required",
    )
    def test_outer_timeout_reaps_external_double_forked_posix_descendant(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            final_pid_file = root / "double-fork-final.pid"
            helper_source = root / "double_fork_helper.c"
            helper_binary = root / "double-fork-helper"
            helper_source.write_text(
                "#include <errno.h>\n"
                "#include <signal.h>\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "#include <sys/types.h>\n"
                "#include <sys/wait.h>\n"
                "#include <unistd.h>\n"
                "int main(int argc, char **argv) {\n"
                "    if (argc != 2) return 2;\n"
                "    pid_t first = fork();\n"
                "    if (first < 0) return 3;\n"
                "    if (first == 0) {\n"
                "        if (setsid() < 0) _exit(4);\n"
                "        pid_t second = fork();\n"
                "        if (second < 0) _exit(5);\n"
                "        if (second == 0) {\n"
                "            signal(SIGTERM, SIG_IGN);\n"
                "            FILE *output = fopen(argv[1], \"w\");\n"
                "            if (output == NULL) _exit(6);\n"
                "            if (fprintf(output, \"%d\", getpid()) < 0) _exit(7);\n"
                "            if (fclose(output) != 0) _exit(8);\n"
                "            for (;;) pause();\n"
                "        }\n"
                "        _exit(0);\n"
                "    }\n"
                "    int status = 0;\n"
                "    if (waitpid(first, &status, 0) < 0) return 9;\n"
                "    return WIFEXITED(status) ? WEXITSTATUS(status) : 10;\n"
                "}\n",
                encoding="utf-8",
            )
            compiler = shutil.which("cc")
            if compiler is None:
                self.skipTest("a C compiler is required for the external helper")
            subprocess.run(
                [compiler, str(helper_source), "-o", str(helper_binary)],
                check=True,
                capture_output=True,
                text=True,
            )
            test_file = self.add(
                root,
                "hermes/test_double_fork.py",
                "import os\n"
                "from pathlib import Path\n"
                "import signal\n"
                "import subprocess\n"
                "import time\n"
                "import unittest\n"
                "class DoubleForkTest(unittest.TestCase):\n"
                "    def test_stop_worker_after_double_fork(self):\n"
                f"        subprocess.run([{str(helper_binary)!r}, "
                f"{str(final_pid_file)!r}], check=True)\n"
                f"        while not Path({str(final_pid_file)!r}).exists(): time.sleep(0.01)\n"
                "        os.kill(os.getppid(), signal.SIGSTOP)\n"
                "        while True: time.sleep(0.05)\n",
            )
            output = io.StringIO()

            with redirect_stdout(output), redirect_stderr(output):
                status = runner.run_tests(
                    [test_file],
                    root,
                    timeout_seconds=1.0,
                    worker_grace_seconds=2.0,
                )

            self.assertEqual(1, status)
            self.assertIn("timed out", output.getvalue())
            final_pid = int(final_pid_file.read_text(encoding="utf-8"))
            with self.assertRaises(ProcessLookupError):
                os.kill(final_pid, 0)

    def test_worker_with_inconsistent_counts_is_rejected(self) -> None:
        payload = {
            "version": runner.PROTOCOL_VERSION,
            "ok": True,
            "discovered": 1,
            "executed": 2,
            "skipped": 0,
            "detail": "",
        }

        with self.assertRaisesRegex(RuntimeError, "inconsistent test counts"):
            runner.worker_result(runner.RESULT_MARKER + json.dumps(payload))

    def test_child_cannot_forge_success_on_stdout_before_hard_exit(self) -> None:
        forged = runner.RESULT_MARKER + json.dumps(
            {
                "version": runner.PROTOCOL_VERSION,
                "ok": True,
                "discovered": 1,
                "executed": 1,
                "skipped": 0,
                "detail": "",
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            self.add(
                root,
                "hermes/test_spoof.py",
                "import os\n"
                "import unittest\n"
                "class SpoofTest(unittest.TestCase):\n"
                "    def test_spoof(self):\n"
                f"        os.write(1, {forged.encode()!r})\n"
                "        os._exit(0)\n",
            )

            status, output = self.run_runner(root)

            self.assertEqual(1, status)
            self.assertIn("without normal framework completion", output)

    def test_test_frames_expose_no_result_connection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            self.add(
                root,
                "hermes/test_no_result_connection.py",
                "import inspect\n"
                "import unittest\n"
                "from multiprocessing.connection import Connection\n"
                "class NoResultConnectionTest(unittest.TestCase):\n"
                "    def test_frames(self):\n"
                "        frame = inspect.currentframe()\n"
                "        while frame is not None:\n"
                "            self.assertFalse(any(\n"
                "                isinstance(value, Connection) and value.writable\n"
                "                for namespace in (frame.f_locals, frame.f_globals)\n"
                "                for value in namespace.values()\n"
                "            ))\n"
                "            frame = frame.f_back\n",
            )

            status, output = self.run_runner(root)

            self.assertEqual(0, status, output)

    def test_frame_walk_forged_success_before_failure_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            self.add(
                root,
                "hermes/test_frame_spoof.py",
                "import inspect\n"
                "import unittest\n"
                "from multiprocessing.connection import Connection\n"
                "class FrameSpoofTest(unittest.TestCase):\n"
                "    def test_spoof_then_fail(self):\n"
                "        frame = inspect.currentframe()\n"
                "        forged = False\n"
                "        while frame is not None:\n"
                "            values = list(frame.f_locals.values()) + list(frame.f_globals.values())\n"
                "            for value in values:\n"
                "                if isinstance(value, Connection) and value.writable:\n"
                "                    value.send({\n"
                f"                        'version': {runner.PROTOCOL_VERSION},\n"
                "                        'ok': True,\n"
                "                        'discovered': 1,\n"
                "                        'executed': 1,\n"
                "                        'skipped': 0,\n"
                "                        'detail': '',\n"
                "                    })\n"
                "                    forged = True\n"
                "                    break\n"
                "            if forged: break\n"
                "            frame = frame.f_back\n"
                "        self.assertFalse(forged, 'test process exposed a result channel')\n"
                "        self.fail('real test failure after attempted forged success')\n",
            )

            status, output = self.run_runner(root)

            self.assertEqual(1, status)
            self.assertIn("unittest suite failed", output)

    def test_frame_walk_forged_success_before_hard_exit_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            self.add(
                root,
                "hermes/test_frame_hard_exit_spoof.py",
                "import inspect\n"
                "import os\n"
                "import unittest\n"
                "from multiprocessing.connection import Connection\n"
                "class FrameHardExitSpoofTest(unittest.TestCase):\n"
                "    def test_spoof_then_exit_zero(self):\n"
                "        frame = inspect.currentframe()\n"
                "        forged = False\n"
                "        while frame is not None:\n"
                "            values = list(frame.f_locals.values()) + list(frame.f_globals.values())\n"
                "            for value in values:\n"
                "                if isinstance(value, Connection) and value.writable:\n"
                "                    value.send({\n"
                f"                        'version': {runner.PROTOCOL_VERSION},\n"
                "                        'ok': True,\n"
                "                        'discovered': 1,\n"
                "                        'executed': 1,\n"
                "                        'skipped': 0,\n"
                "                        'detail': '',\n"
                "                    })\n"
                "                    forged = True\n"
                "                    break\n"
                "            if forged: break\n"
                "            frame = frame.f_back\n"
                "        os._exit(0)\n",
            )

            status, output = self.run_runner(root)

            self.assertEqual(1, status)
            self.assertIn("without normal framework completion", output)

    def test_worker_output_is_disk_backed_and_bounded_to_64_kib(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            self.add(
                root,
                "hermes/test_large_output.py",
                "import os\n"
                "import unittest\n"
                "class LargeOutputTest(unittest.TestCase):\n"
                "    def test_large_output(self):\n"
                "        os.write(1, b'x' * (8 * 1024 * 1024))\n",
            )

            status, output = self.run_runner(root)

            self.assertEqual(0, status, output[-2000:])
            self.assertIn("worker output truncated after 65536 bytes", output)
            self.assertLess(len(output), 70_000)

    @unittest.skipUnless(os.name == "posix", "POSIX process groups are required")
    def test_timeout_escalates_from_term_to_kill_and_reaps_child(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            pid_file = root / "test-child.pid"
            test_file = self.add(
                root,
                "hermes/test_ignore_term.py",
                "import os\n"
                "from pathlib import Path\n"
                "import signal\n"
                "import time\n"
                "import unittest\n"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                "class IgnoreTermTest(unittest.TestCase):\n"
                "    def test_never_finishes(self):\n"
                f"        Path({str(pid_file)!r}).write_text(str(os.getpid()))\n"
                "        while True: time.sleep(0.05)\n",
            )
            output = io.StringIO()

            with redirect_stdout(output), redirect_stderr(output):
                status = runner.run_tests(
                    [test_file],
                    root,
                    timeout_seconds=0.3,
                    worker_grace_seconds=1.0,
                )

            self.assertEqual(1, status)
            self.assertIn("timed out after 0.3 seconds", output.getvalue())
            child_pid = int(pid_file.read_text(encoding="utf-8"))
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)

    @unittest.skipUnless(os.name == "posix", "POSIX process groups are required")
    def test_success_cleanup_kills_unwaited_same_group_descendant(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            sentinel = root / "leaked-descendant.txt"
            descendant = (
                "import time\n"
                "from pathlib import Path\n"
                "time.sleep(1)\n"
                f"Path({str(sentinel)!r}).write_text('leaked')\n"
            )
            self.add(
                root,
                "hermes/test_descendant.py",
                "import subprocess\n"
                "import sys\n"
                "import unittest\n"
                f"subprocess.Popen([sys.executable, '-c', {descendant!r}])\n"
                "class DescendantTest(unittest.TestCase):\n"
                "    def test_passes(self): self.assertTrue(True)\n",
            )

            status, output = self.run_runner(root)

            self.assertEqual(0, status, output)
            time.sleep(1.2)
            self.assertFalse(sentinel.exists(), "test descendant survived cleanup")

    @unittest.skipUnless(
        sys.platform.startswith("linux"),
        "Linux child-subreaper support is required",
    )
    def test_detached_descendant_is_adopted_killed_and_reaped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            sentinel = root / "leaked-detached-descendant.txt"
            descendant = (
                "import time\n"
                "from pathlib import Path\n"
                "time.sleep(1)\n"
                f"Path({str(sentinel)!r}).write_text('leaked')\n"
            )
            detached_parent = (
                "import subprocess\n"
                "import sys\n"
                "import time\n"
                "subprocess.Popen(\n"
                f"    [sys.executable, '-c', {descendant!r}],\n"
                "    start_new_session=True,\n"
                ")\n"
                "time.sleep(2)\n"
            )
            self.add(
                root,
                "hermes/test_detached_descendant.py",
                "import subprocess\n"
                "import sys\n"
                "import unittest\n"
                "subprocess.Popen(\n"
                f"    [sys.executable, '-c', {detached_parent!r}],\n"
                "    start_new_session=True,\n"
                ")\n"
                "class DetachedDescendantTest(unittest.TestCase):\n"
                "    def test_passes(self): self.assertTrue(True)\n",
            )

            status, output = self.run_runner(root)

            self.assertEqual(0, status, output)
            time.sleep(1.2)
            self.assertFalse(sentinel.exists(), "detached descendant survived cleanup")

    def test_missing_proc_children_visibility_fails_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing_proc = Path(temporary) / "unmounted-proc"

            with self.assertRaisesRegex(RuntimeError, "cannot inspect Linux descendant"):
                worker.linux_direct_children(
                    12345,
                    require_visibility=True,
                    proc_root=missing_proc,
                )

    def test_existing_proc_process_without_children_file_fails_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            proc_root = Path(temporary)
            (proc_root / "12345/task/12345").mkdir(parents=True)

            with self.assertRaisesRegex(RuntimeError, "children files"):
                worker.linux_direct_children(12345, proc_root=proc_root)


if __name__ == "__main__":
    unittest.main()
