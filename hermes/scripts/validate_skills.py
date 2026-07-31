#!/usr/bin/env python3
"""Validate that Hermes skills are self-contained and consistently named."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import shlex
import sys
from urllib.parse import unquote


FRONTMATTER_RE = re.compile(r"\A---\r?\n(?P<body>.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)
FIELD_RE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9_-]*):(?P<value>.*)$")
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\((?P<target>[^)]+)\)")
EXTERNAL_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
TEXT_SUFFIXES = {".json", ".md", ".py", ".sh", ".toml", ".yaml", ".yml"}
FORBIDDEN_PATHS = (
    re.compile(r"\.agents/"),
    re.compile(r"\.codex/"),
    re.compile(r"~/?\.codex(?:/|\b)"),
    re.compile(r"\$\{?CODEX_HOME\}?"),
    re.compile(r"/Users/[^\s]+"),
)


@dataclass(frozen=True)
class ValidationError:
    path: Path
    message: str

    def render(self, repository_root: Path) -> str:
        try:
            display = self.path.relative_to(repository_root)
        except ValueError:
            display = self.path
        return f"{display}: {self.message}"


def unquote_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1].strip()
    return value


def parse_frontmatter(skill_file: Path, text: str) -> tuple[dict[str, str], list[ValidationError]]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, [ValidationError(skill_file, "missing or malformed YAML frontmatter")]

    fields: dict[str, str] = {}
    errors: list[ValidationError] = []
    for line_number, line in enumerate(match.group("body").splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        field_match = FIELD_RE.match(line)
        if not field_match:
            errors.append(
                ValidationError(skill_file, f"unsupported frontmatter line {line_number}")
            )
            continue
        key = field_match.group("key")
        if key in fields:
            errors.append(ValidationError(skill_file, f"duplicate frontmatter field: {key}"))
            continue
        fields[key] = unquote_scalar(field_match.group("value"))
    return fields, errors


def markdown_target(raw_target: str) -> str:
    raw_target = raw_target.strip()
    if raw_target.startswith("<") and ">" in raw_target:
        return raw_target[1 : raw_target.index(">")]
    try:
        tokens = shlex.split(raw_target)
    except ValueError:
        return raw_target
    return tokens[0] if tokens else ""


def validate_markdown_links(skill_root: Path) -> list[ValidationError]:
    errors: list[ValidationError] = []
    resolved_root = skill_root.resolve()
    for markdown_file in sorted(skill_root.rglob("*.md")):
        text = markdown_file.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = markdown_target(match.group("target"))
            if not target or target.startswith("#") or EXTERNAL_SCHEME_RE.match(target):
                continue
            path_part = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not path_part:
                continue
            if Path(path_part).is_absolute():
                errors.append(
                    ValidationError(markdown_file, f"absolute local link is not portable: {target}")
                )
                continue
            unresolved_candidate = markdown_file.parent / path_part
            candidate = unresolved_candidate.resolve()
            if not candidate.is_relative_to(resolved_root):
                errors.append(
                    ValidationError(markdown_file, f"local link escapes the skill: {target}")
                )
            elif not candidate.exists():
                errors.append(
                    ValidationError(markdown_file, f"missing local link target: {target}")
                )
            elif unresolved_candidate.is_symlink():
                errors.append(
                    ValidationError(markdown_file, f"symbolic local link target is not embedded: {target}")
                )
    return errors


def validate_portability(skill_root: Path) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for resource in sorted(skill_root.rglob("*")):
        if not resource.is_file() or resource.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = resource.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(ValidationError(resource, "text resource is not valid UTF-8"))
            continue
        for pattern in FORBIDDEN_PATHS:
            match = pattern.search(text)
            if match:
                errors.append(
                    ValidationError(
                        resource,
                        f"non-embedded Codex path is forbidden: {match.group(0).strip()}",
                    )
                )
    return errors


def validate_skill(skill_root: Path) -> list[ValidationError]:
    skill_file = skill_root / "SKILL.md"
    if not skill_file.is_file() or skill_file.is_symlink():
        return [ValidationError(skill_file, "regular SKILL.md file is required")]

    try:
        text = skill_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [ValidationError(skill_file, "SKILL.md is not valid UTF-8")]

    fields, errors = parse_frontmatter(skill_file, text)
    name = fields.get("name", "")
    description = fields.get("description", "")
    if not name:
        errors.append(ValidationError(skill_file, "frontmatter name is required"))
    elif not SKILL_NAME_RE.fullmatch(name):
        errors.append(ValidationError(skill_file, f"invalid skill name: {name}"))
    elif name != skill_root.name:
        errors.append(
            ValidationError(
                skill_file,
                f"frontmatter name {name!r} does not match folder {skill_root.name!r}",
            )
        )
    if not description:
        errors.append(ValidationError(skill_file, "frontmatter description is required"))

    errors.extend(validate_markdown_links(skill_root))
    errors.extend(validate_portability(skill_root))
    return errors


def validate_skills(skills_root: Path) -> tuple[int, list[ValidationError]]:
    if not skills_root.is_dir() or skills_root.is_symlink():
        return 0, [ValidationError(skills_root, "regular skills directory is required")]

    skill_roots = sorted(
        path for path in skills_root.iterdir() if path.is_dir() and not path.name.startswith(".")
    )
    if not skill_roots:
        return 0, [ValidationError(skills_root, "no skill directories found")]

    errors: list[ValidationError] = []
    for skill_root in skill_roots:
        errors.extend(validate_skill(skill_root))
    return len(skill_roots), errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skills_root",
        nargs="?",
        default="hermes/skills",
        type=Path,
        help="directory containing Hermes skill folders (default: hermes/skills)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    skills_root = args.skills_root.resolve()
    count, errors = validate_skills(skills_root)
    repository_root = Path.cwd().resolve()
    if errors:
        for error in errors:
            print(error.render(repository_root), file=sys.stderr)
        print(f"Hermes skill validation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print(f"Validated {count} embedded Hermes skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
