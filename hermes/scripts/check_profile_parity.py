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
    source = Path(__file__).resolve().parents[1] / "skills"
    published = args.profile_root.resolve() / "skills"
    try:
        differences = compare_directories(source, published)
    except ValueError as error:
        print(error)
        return 2

    if differences:
        print("Hermes profile drift detected:")
        for difference in differences:
            print(f"- {difference}")
        return 1

    print(f"Hermes skill trees are identical ({len(files_below(source))} files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
