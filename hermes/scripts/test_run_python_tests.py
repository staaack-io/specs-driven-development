#!/usr/bin/env python3
"""Tests for portable Hermes Python test discovery."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

import run_python_tests as runner


class RunPythonTestsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_discovery_is_recursive_sorted_and_restricted_to_test_files(self) -> None:
        nested = self.root / "nested"
        nested.mkdir()
        (self.root / "test_z.py").write_text("", encoding="utf-8")
        (nested / "test_a.py").write_text("", encoding="utf-8")
        (nested / "helper.py").write_text("", encoding="utf-8")

        discovered = runner.discover_tests(self.root)

        self.assertEqual(
            [nested / "test_a.py", self.root / "test_z.py"],
            discovered,
        )

    def test_empty_discovery_fails_closed(self) -> None:
        self.assertEqual(2, runner.run_tests([], self.root))

    @mock.patch.object(runner.subprocess, "run")
    def test_each_file_runs_without_a_shell_and_any_failure_fails(self, run: mock.Mock) -> None:
        first = self.root / "test_first.py"
        second = self.root / "test_second.py"
        run.side_effect = [
            mock.Mock(returncode=0),
            mock.Mock(returncode=1),
        ]

        result = runner.run_tests([first, second], self.root)

        self.assertEqual(1, result)
        self.assertEqual(2, run.call_count)
        for call in run.call_args_list:
            self.assertIsInstance(call.args[0], list)
            self.assertNotIn("shell", call.kwargs)


if __name__ == "__main__":
    unittest.main()
