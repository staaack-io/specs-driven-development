#!/usr/bin/env python3
"""Tests for event-correct documentation and whitespace validation."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[2] / ".github/scripts/validate-changed-docs.sh"
ZERO_SHA = "0" * 40


class ValidateChangedDocsTest(unittest.TestCase):
    def repository(self, destination: Path) -> Path:
        root = destination / "repository"
        root.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "ci@example.test"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "CI Test"], cwd=root, check=True)
        return root

    def commit(self, root: Path, relative: str, content: str, message: str) -> str:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", relative], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", message], cwd=root, check=True)
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def run_script(
        self,
        root: Path,
        event: str,
        base: str,
        before: str,
        head: str,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(SCRIPT), event, base, before, head],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_pull_request_uses_merge_base_range(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            base = self.commit(root, "README.txt", "base\n", "base")
            head = self.commit(root, "code.py", "value = 1  \n", "bad branch")

            result = self.run_script(root, "pull_request", base, "", head)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("trailing whitespace", result.stdout + result.stderr)

    def test_push_uses_before_to_head_range(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            before = self.commit(root, "code.py", "value = 1\n", "before")
            head = self.commit(root, "code.py", "value = 2  \n", "after")

            result = self.run_script(root, "push", "", before, head)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("trailing whitespace", result.stdout + result.stderr)

    def test_first_push_checks_root_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            head = self.commit(root, "code.py", "value = 1  \n", "root")

            result = self.run_script(root, "push", "", ZERO_SHA, head)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("trailing whitespace", result.stdout + result.stderr)

    def test_missing_commit_and_unknown_event_fail_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            head = self.commit(root, "code.py", "value = 1\n", "root")

            missing = self.run_script(root, "pull_request", "deadbeef", "", head)
            unknown = self.run_script(root, "schedule", "", "", head)

            self.assertEqual(2, missing.returncode)
            self.assertIn("base commit is unavailable", missing.stderr)
            self.assertEqual(2, unknown.returncode)
            self.assertIn("unsupported GitHub event", unknown.stderr)

    def test_changed_markdown_uses_exact_pinned_linter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.repository(Path(temporary))
            before = self.commit(root, "README.md", "# Before\n", "before")
            head = self.commit(root, "README.md", "# After\n", "after")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            log = root / "npx-arguments"
            fake_npx = bin_dir / "npx"
            fake_npx.write_text(
                "#!/usr/bin/env sh\nprintf '%s\\n' \"$@\" >\"$NPX_LOG\"\n",
                encoding="utf-8",
            )
            fake_npx.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["NPX_LOG"] = str(log)

            result = self.run_script(root, "push", "", before, head, env)

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                ["--yes", "markdownlint-cli2@0.18.1", "--", "README.md"],
                log.read_text(encoding="utf-8").splitlines(),
            )

    def test_script_has_no_gnu_only_shell_dependency(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("mapfile", text)
        self.assertNotIn("sort -z", text)
        self.assertIsNotNone(shutil.which("bash"))


if __name__ == "__main__":
    unittest.main()
