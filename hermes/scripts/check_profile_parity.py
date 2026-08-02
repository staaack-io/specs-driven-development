#!/usr/bin/env python3
"""Verify that the published Hermes profile matches the canonical skills."""

from __future__ import annotations

import argparse
from pathlib import Path


def files_below(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        raise ValueError(f"skill directory does not exist: {root}")
    return {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }


def compare_directories(source: Path, published: Path) -> list[str]:
    source_files = files_below(source)
    published_files = files_below(published)
    differences: list[str] = []

    for relative_path in sorted(source_files.keys() - published_files.keys()):
        differences.append(f"missing from profile: {relative_path}")
    for relative_path in sorted(published_files.keys() - source_files.keys()):
        differences.append(f"unexpected in profile: {relative_path}")
    for relative_path in sorted(source_files.keys() & published_files.keys()):
        if (
            source_files[relative_path].read_bytes()
            != published_files[relative_path].read_bytes()
        ):
            differences.append(f"content differs: {relative_path}")

    return differences


def compare_profile_trees(source_root: Path, profile_root: Path) -> list[str]:
    """Compare the canonical skills and shared runtime with a profile checkout."""
    source_skills = source_root / "skills"
    profile_skills = profile_root / "skills"
    differences = compare_directories(source_skills, profile_skills)

    source_runtime = source_root / "runtime"
    profile_runtime = profile_root / "hermes" / "runtime"
    if not profile_runtime.is_dir():
        differences.extend(
            f"runtime: missing from profile: {relative_path}"
            for relative_path in sorted(files_below(source_runtime))
        )
        return differences

    differences.extend(
        f"runtime: {difference}"
        for difference in compare_directories(source_runtime, profile_runtime)
    )
    return differences


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare canonical Hermes skills with a profile checkout."
    )
    parser.add_argument(
        "profile_root",
        type=Path,
        help="path to the hermes-agent-profile-staaack checkout",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = Path(__file__).resolve().parents[1]
    profile_root = args.profile_root.resolve()
    try:
        differences = compare_profile_trees(source_root, profile_root)
    except ValueError as error:
        print(error)
        return 2

    if differences:
        print("Hermes profile drift detected:")
        for difference in differences:
            print(f"- {difference}")
        return 1

    skill_count = len(files_below(source_root / "skills"))
    runtime_count = len(files_below(source_root / "runtime"))
    print(
        "Hermes skill and runtime trees are identical "
        f"({skill_count} skill files, {runtime_count} runtime files)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
