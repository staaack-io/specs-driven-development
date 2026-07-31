#!/usr/bin/env python3
"""Validate the tracked and non-ignored Hermes skill distribution."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SKILLS_ROOT = REPOSITORY_ROOT / "hermes/skills"
PINNED_PYYAML = "6.0.3"
MAX_MARKDOWN_FILES = 256
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HTML_DESTINATION_RE = re.compile(
    r'''\b(?:href|src)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+))''',
    re.IGNORECASE,
)
INLINE_PATH_RE = re.compile(r"`((?:\.\./|references/|templates/|scripts/)[^`\s,;:]+)`")
MARKDOWN_ESCAPE_RE = re.compile(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])")
TEXT_SUFFIXES = {".json", ".md", ".py", ".sh", ".toml", ".yaml", ".yml"}
FORBIDDEN_PATHS = (
    re.compile(r"\.agents/"),
    re.compile(r"\.codex/"),
    re.compile(r"~/?\.codex(?:/|\b)"),
    re.compile(r"\$\{?CODEX_HOME\}?"),
    re.compile(r"/Users/[^\s]+"),
    re.compile(r"/home/[^/\s]+/(?:\.codex|\.agents)(?:/|\b)"),
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


class ContractError(Exception):
    """Raised when a skill contract cannot be parsed safely."""


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def construct_unique_mapping(
    loader: UniqueKeyLoader,
    node: MappingNode,
    deep: bool = False,
) -> dict[object, object]:
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as error:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable key",
                key_node.start_mark,
            ) from error
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_unique_mapping,
)


def parse_flat_yaml(text: str, source: Path) -> dict[str, str]:
    try:
        document = yaml.load(text, Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        raise ContractError(f"invalid YAML: {error}") from error
    if not isinstance(document, dict):
        raise ContractError("YAML frontmatter must be a mapping")

    values: dict[str, str] = {}
    for key, value in document.items():
        if not isinstance(key, str) or not re.fullmatch(
            r"[A-Za-z][A-Za-z0-9_-]*", key
        ):
            raise ContractError(f"invalid frontmatter key {key!r}")
        if not isinstance(value, str) or not value.strip():
            raise ContractError(f"frontmatter {key} must be a non-empty string")
        values[key] = value.strip()
    return values


def parse_skill(skill_file: Path) -> tuple[dict[str, str], str]:
    text = skill_file.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ContractError("missing opening YAML frontmatter marker")
    try:
        closing = lines.index("---", 1)
    except ValueError as error:
        raise ContractError("missing closing YAML frontmatter marker") from error
    if closing == 1:
        raise ContractError("empty YAML frontmatter")
    values = parse_flat_yaml("\n".join(lines[1:closing]), skill_file)
    return values, "\n".join(lines[closing + 1 :]).strip()


def is_escaped(text: str, position: int) -> bool:
    backslashes = 0
    position -= 1
    while position >= 0 and text[position] == "\\":
        backslashes += 1
        position -= 1
    return backslashes % 2 == 1


def destination_token(text: str, start: int, inline: bool) -> tuple[str, int] | None:
    while start < len(text) and text[start] in " \t\r\n":
        start += 1
    if start >= len(text):
        return None
    if text[start] == "<":
        cursor = start + 1
        while cursor < len(text):
            if text[cursor] == ">" and not is_escaped(text, cursor):
                return text[start + 1 : cursor], cursor + 1
            if text[cursor] in "\r\n":
                return None
            cursor += 1
        return None

    cursor = start
    depth = 0
    while cursor < len(text):
        character = text[cursor]
        if character == "\\" and cursor + 1 < len(text):
            cursor += 2
            continue
        if character == "(":
            depth += 1
        elif character == ")":
            if depth == 0:
                if inline:
                    return text[start:cursor], cursor + 1
                break
            depth -= 1
        elif character.isspace() and depth == 0:
            break
        cursor += 1
    if inline and cursor == len(text):
        return None
    if depth != 0 or cursor == start:
        return None
    return text[start:cursor], cursor


def inline_destinations(text: str) -> list[str]:
    destinations: list[str] = []
    cursor = 0
    while cursor < len(text) - 1:
        marker = text.find("](", cursor)
        if marker < 0:
            break
        if is_escaped(text, marker):
            cursor = marker + 2
            continue
        parsed = destination_token(text, marker + 2, inline=True)
        if parsed is None:
            cursor = marker + 2
            continue
        destination, cursor = parsed
        destinations.append(destination)
    return destinations


def reference_definition_destination(
    line: str,
    continuation: str | None,
) -> str | None:
    cursor = 0
    while cursor < len(line) and line[cursor] == " " and cursor < 4:
        cursor += 1
    if cursor > 3 or cursor >= len(line) or line[cursor] != "[":
        return None
    cursor += 1
    while cursor < len(line):
        if line[cursor] == "\\" and cursor + 1 < len(line):
            cursor += 2
            continue
        if line[cursor] == "]":
            break
        cursor += 1
    if cursor >= len(line) or cursor + 1 >= len(line) or line[cursor + 1] != ":":
        return None
    parsed = destination_token(line, cursor + 2, inline=False)
    if parsed is None and not line[cursor + 2 :].strip() and continuation is not None:
        indentation = len(continuation) - len(continuation.lstrip(" "))
        if indentation <= 3:
            parsed = destination_token(continuation, indentation, inline=False)
    return parsed[0] if parsed is not None else None


def local_reference_targets(
    markdown_file: Path,
    include_inline_paths: bool,
) -> set[str]:
    text = markdown_file.read_text(encoding="utf-8")
    targets: set[str] = set()

    def add_target(raw: str) -> None:
        raw = MARKDOWN_ESCAPE_RE.sub(r"\1", raw.strip())
        try:
            split = urlsplit(raw)
        except ValueError as error:
            raise ContractError(f"invalid link destination {raw!r}: {error}") from error
        if split.scheme or split.netloc or not split.path:
            return
        targets.add(unquote(split.path))

    for destination in inline_destinations(text):
        add_target(destination)
    lines = text.splitlines()
    for index, line in enumerate(lines):
        continuation = lines[index + 1] if index + 1 < len(lines) else None
        destination = reference_definition_destination(line, continuation)
        if destination is not None:
            add_target(destination)
    for match in HTML_DESTINATION_RE.finditer(text):
        add_target(next(value for value in match.groups() if value is not None))
    if include_inline_paths:
        targets.update(INLINE_PATH_RE.findall(text))
    return targets


def validate_reference(
    skill_root: Path,
    source_file: Path,
    reference: str,
    distributed_files: set[Path],
    errors: list[ValidationError],
) -> Path | None:
    candidate = source_file.parent / reference
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError):
        errors.append(ValidationError(source_file, f"missing local reference: {reference}"))
        return None
    try:
        resolved.relative_to(skill_root.resolve(strict=True))
    except ValueError:
        errors.append(ValidationError(source_file, f"local reference escapes the skill: {reference}"))
        return None
    if not resolved.is_file():
        errors.append(ValidationError(source_file, f"local reference is not a file: {reference}"))
        return None
    if resolved not in distributed_files:
        errors.append(ValidationError(source_file, f"local reference is ignored: {reference}"))
        return None
    return resolved


def validate_markdown_graph(
    skill_root: Path,
    skill_file: Path,
    distributed_files: set[Path],
    errors: list[ValidationError],
) -> None:
    pending = [skill_file]
    visited: set[Path] = set()
    while pending:
        markdown_file = pending.pop()
        resolved_markdown = markdown_file.resolve()
        if resolved_markdown in visited:
            continue
        if len(visited) >= MAX_MARKDOWN_FILES:
            errors.append(
                ValidationError(skill_file, f"Markdown traversal exceeds {MAX_MARKDOWN_FILES} files")
            )
            return
        visited.add(resolved_markdown)
        try:
            references = local_reference_targets(
                markdown_file,
                include_inline_paths=resolved_markdown == skill_file.resolve(),
            )
        except (OSError, UnicodeError, ContractError) as error:
            errors.append(ValidationError(markdown_file, f"cannot parse Markdown: {error}"))
            continue
        for reference in sorted(references):
            target = validate_reference(
                skill_root,
                markdown_file,
                reference,
                distributed_files,
                errors,
            )
            if target is not None and target.suffix.casefold() == ".md":
                pending.append(target)


def repository_inventory(repository_root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=repository_root,
        check=False,
        capture_output=True,
    )
    if result.returncode:
        detail = os.fsdecode(result.stderr).strip() or "git ls-files failed"
        raise ContractError(f"cannot enumerate repository files: {detail}")
    return [
        Path(os.fsdecode(raw_path))
        for raw_path in result.stdout.split(b"\0")
        if raw_path
    ]


def validate_portability(
    skill_root: Path,
    distributed_files: set[Path],
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for resource in sorted(distributed_files):
        try:
            resource.relative_to(skill_root.resolve())
        except ValueError:
            continue
        if resource.suffix.casefold() not in TEXT_SUFFIXES:
            continue
        try:
            text = resource.read_text(encoding="utf-8")
        except UnicodeError:
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


def validate_skill(
    skill_root: Path,
    distributed_files: set[Path],
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    skill_file = skill_root / "SKILL.md"
    try:
        skill_resolved = skill_file.resolve(strict=True)
    except OSError:
        errors.append(ValidationError(skill_file, "distributed SKILL.md is required"))
        return errors
    if skill_resolved not in distributed_files:
        errors.append(ValidationError(skill_file, "SKILL.md is ignored from the distribution"))
        return errors
    try:
        fields, body = parse_skill(skill_file)
    except (OSError, UnicodeError, ContractError) as error:
        errors.append(ValidationError(skill_file, str(error)))
        return errors

    missing = sorted({"name", "description"} - fields.keys())
    if missing:
        errors.append(ValidationError(skill_file, f"missing frontmatter keys: {', '.join(missing)}"))
    name = fields.get("name")
    if name is not None:
        if not NAME_RE.fullmatch(name):
            errors.append(ValidationError(skill_file, f"invalid skill name: {name}"))
        if name != skill_root.name:
            errors.append(
                ValidationError(
                    skill_file,
                    f"frontmatter name {name!r} does not match folder {skill_root.name!r}",
                )
            )

    body_lines = body.splitlines()
    if not body:
        errors.append(ValidationError(skill_file, "skill body must not be empty"))
    elif not body_lines[0].startswith("# "):
        errors.append(ValidationError(skill_file, "skill body must start with a level-one title"))
    elif not "\n".join(body_lines[1:]).strip():
        errors.append(ValidationError(skill_file, "skill body must contain instructions"))

    validate_markdown_graph(skill_root, skill_file, distributed_files, errors)
    errors.extend(validate_portability(skill_root, distributed_files))
    return errors


def validate_skills(
    skills_root: Path,
    repository_root: Path,
) -> tuple[int, list[ValidationError]]:
    errors: list[ValidationError] = []
    if skills_root.is_symlink() or not skills_root.is_dir():
        return 0, [ValidationError(skills_root, "regular skills directory is required")]
    try:
        inventory = repository_inventory(repository_root)
    except ContractError as error:
        return 0, [ValidationError(repository_root, str(error))]

    skill_entries: list[tuple[Path, Path]] = []
    for relative in inventory:
        path = repository_root / relative
        try:
            skill_relative = path.relative_to(skills_root)
        except ValueError:
            continue
        skill_entries.append((skill_relative, path))

    safe_files: set[Path] = set()
    for relative, path in skill_entries:
        if path.is_symlink():
            errors.append(ValidationError(path, "symbolic links are not allowed in skills"))
        elif not path.is_file():
            errors.append(ValidationError(path, "skill entries must be regular files"))
        else:
            safe_files.add(path.resolve())

    loose_entries = [path for relative, path in skill_entries if len(relative.parts) == 1]
    for entry in sorted(loose_entries):
        errors.append(ValidationError(entry, "skills directory may only contain skill folders"))

    skill_names = sorted(
        {
            relative.parts[0]
            for relative, _path in skill_entries
            if len(relative.parts) >= 2
        }
    )
    if not skill_names:
        errors.append(ValidationError(skills_root, "no distributed skill directories found"))
        return 0, errors

    for skill_name in skill_names:
        skill_root = skills_root / skill_name
        if not NAME_RE.fullmatch(skill_name):
            errors.append(ValidationError(skill_root, "invalid skill directory name"))
        if skill_root.is_symlink():
            errors.append(ValidationError(skill_root, "symbolic skill directory is forbidden"))
            continue
        errors.extend(validate_skill(skill_root, safe_files))
    return len(skill_names), errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skills_root",
        nargs="?",
        default=DEFAULT_SKILLS_ROOT,
        type=Path,
        help="skills directory (default: hermes/skills)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if yaml.__version__ != PINNED_PYYAML:
        print(
            f"error: PyYAML {PINNED_PYYAML} is required; found {yaml.__version__}",
            file=sys.stderr,
        )
        return 1
    skills_root = args.skills_root
    if not skills_root.is_absolute():
        skills_root = REPOSITORY_ROOT / skills_root
    count, errors = validate_skills(skills_root, REPOSITORY_ROOT)
    if errors:
        for error in errors:
            print(f"error: {error.render(REPOSITORY_ROOT)}", file=sys.stderr)
        print(f"Hermes skill validation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print(f"Validated {count} embedded Hermes skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
