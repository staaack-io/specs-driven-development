#!/usr/bin/env python3
"""Discover and execute every supported Hermes unittest file."""

from __future__ import annotations

from contextlib import contextmanager
import fnmatch
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from typing import Iterator
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def repository_inventory(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode:
        detail = os.fsdecode(result.stderr).strip() or "git ls-files failed"
        raise RuntimeError(f"cannot enumerate repository tests: {detail}")
    return [
        Path(os.fsdecode(raw_path))
        for raw_path in result.stdout.split(b"\0")
        if raw_path
    ]


def discover_test_files(root: Path) -> list[Path]:
    hermes_root = (root / "hermes").resolve(strict=True)
    tests: list[Path] = []
    for relative in repository_inventory(root):
        if (
            len(relative.parts) < 2
            or relative.parts[0] != "hermes"
            or not fnmatch.fnmatchcase(relative.name, "test_*.py")
        ):
            continue
        test = root / relative
        if test.is_symlink() or not test.is_file():
            raise RuntimeError(f"unsafe Hermes test path: {relative}")
        try:
            test.resolve(strict=True).relative_to(hermes_root)
        except (OSError, ValueError) as error:
            raise RuntimeError(f"Hermes test escapes hermes/: {relative}") from error
        tests.append(test)
    return sorted(tests)


@contextmanager
def loaded_test_suite(test: Path, index: int) -> Iterator[unittest.TestSuite]:
    module_name = f"_hermes_repository_test_{index}"
    module_spec = importlib.util.spec_from_file_location(module_name, test)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"cannot import {test}")
    module = importlib.util.module_from_spec(module_spec)
    previous_module = sys.modules.get(module_name)
    previous_path = list(sys.path)
    sys.modules[module_name] = module
    sys.path.insert(0, str(test.parent))
    try:
        module_spec.loader.exec_module(module)
        yield unittest.defaultTestLoader.loadTestsFromModule(module)
    finally:
        sys.path[:] = previous_path
        if previous_module is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous_module


def run_tests(test_files: list[Path], repository_root: Path = REPOSITORY_ROOT) -> int:
    if not test_files:
        print("error: no Hermes Python tests were discovered", file=sys.stderr)
        return 1

    print(f"Discovered {len(test_files)} Hermes test files.", flush=True)
    total_cases = 0
    total_executed = 0
    total_skipped = 0
    for index, test_file in enumerate(test_files):
        try:
            display = test_file.relative_to(repository_root)
        except ValueError:
            display = test_file
        print(f"\n==> {display}", flush=True)
        try:
            with loaded_test_suite(test_file, index) as suite:
                case_count = suite.countTestCases()
                if case_count == 0:
                    print(
                        f"error: {display} contains no unittest cases; "
                        "pytest-only files are unsupported",
                        file=sys.stderr,
                    )
                    return 1
                total_cases += case_count
                result = unittest.TextTestRunner(verbosity=1).run(suite)
        except BaseException as error:  # Imports must never terminate CI cleanly.
            print(f"error: cannot load {display}: {error}", file=sys.stderr)
            return 1
        if not result.wasSuccessful():
            print(f"error: {display} failed", file=sys.stderr)
            return 1
        executed = result.testsRun - len(result.skipped)
        if executed == 0:
            print(
                f"error: {display} executed no non-skipped unittest cases",
                file=sys.stderr,
            )
            return 1
        total_executed += executed
        total_skipped += len(result.skipped)

    print(
        f"\nAll {total_executed} Hermes test cases executed "
        f"({total_skipped} skipped; {total_cases} discovered)."
    )
    return 0


def main(root: Path = REPOSITORY_ROOT) -> int:
    try:
        tests = discover_test_files(root.resolve(strict=True))
    except (OSError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return run_tests(tests, root)


if __name__ == "__main__":
    raise SystemExit(main())
