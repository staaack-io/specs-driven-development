#!/usr/bin/env python3
"""Discover and run every Hermes ``test_*.py`` file in an isolated process."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def discover_tests(search_root: Path) -> list[Path]:
    if not search_root.is_dir():
        return []
    return sorted(path for path in search_root.rglob("test_*.py") if path.is_file())


def run_tests(test_files: list[Path], repository_root: Path = REPOSITORY_ROOT) -> int:
    if not test_files:
        print("No Hermes Python tests were discovered.", file=sys.stderr)
        return 2

    print(f"Discovered {len(test_files)} test files.", flush=True)
    failed: list[Path] = []
    for test_file in test_files:
        try:
            display = test_file.relative_to(repository_root)
        except ValueError:
            display = test_file
        print(f"==> {display}", flush=True)
        result = subprocess.run(
            [sys.executable, str(test_file)],
            cwd=repository_root,
            check=False,
        )
        if result.returncode:
            failed.append(display)

    if failed:
        print(
            "Failed Hermes test files: " + ", ".join(str(path) for path in failed),
            file=sys.stderr,
        )
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "search_root",
        nargs="?",
        default=REPOSITORY_ROOT / "hermes",
        type=Path,
        help="directory searched recursively for test_*.py files",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    search_root = args.search_root
    if not search_root.is_absolute():
        search_root = REPOSITORY_ROOT / search_root
    return run_tests(discover_tests(search_root.resolve()))


if __name__ == "__main__":
    raise SystemExit(main())
