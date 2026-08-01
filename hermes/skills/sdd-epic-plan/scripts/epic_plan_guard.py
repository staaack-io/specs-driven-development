#!/usr/bin/env python3
"""Validate and transactionally promote SDD Epic planning artifacts."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile


DESIGN_CANDIDATE = "03-epic-design.candidate.md"
ROADMAP_CANDIDATE = "03a-epic-roadmap.candidate.md"
DESIGN_FINAL = "03-epic-design.md"
ROADMAP_FINAL = "03a-epic-roadmap.md"
LOCK_FILE = ".epic-plan.lock"
TRANSACTION_FILE = ".epic-plan.transaction.json"
RECEIPT_FILE = ".epic-plan.commit.json"
MAX_ARTIFACT_BYTES = 2 * 1024 * 1024
MAX_JOURNAL_BYTES = 16 * 1024 * 1024
DECISIONS = {"approve", "request-changes"}
EVIDENCE_MODES = {"direct-response", "decision-option"}
AC_RE = re.compile(r"AC-\d{3}")
SLICE_RE = re.compile(r"S-\d{3}")
QUESTION_RE = re.compile(r"Q-\d{3}")
CHANGE_RE = re.compile(r"CR-\d{3}")
MILESTONE_RE = re.compile(r"M-\d{3}")


class GuardError(RuntimeError):
    pass


def token_for(data: bytes | None) -> str:
    if data is None:
        return "absent"
    return "sha256:" + hashlib.sha256(data).hexdigest()


def pair_token(design: bytes | None, roadmap: bytes | None) -> str:
    payload = json.dumps(
        {"design": token_for(design), "roadmap": token_for(roadmap)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return token_for(payload)


def feature_paths(value: str) -> dict[str, Path]:
    raw = Path(value)
    if raw.is_symlink():
        raise GuardError("feature directory must not be a symlink")
    try:
        directory = raw.resolve(strict=True)
    except FileNotFoundError as error:
        raise GuardError("feature directory does not exist") from error
    if not directory.is_dir():
        raise GuardError("feature directory must be a directory")
    if directory.parent.name != ".specs":
        raise GuardError("feature directory must be exactly .specs/<feature-id>")
    return {
        "directory": directory,
        "spec": directory / "01-spec.md",
        "design_candidate": directory / DESIGN_CANDIDATE,
        "roadmap_candidate": directory / ROADMAP_CANDIDATE,
        "design_final": directory / DESIGN_FINAL,
        "roadmap_final": directory / ROADMAP_FINAL,
        "lock": directory / LOCK_FILE,
        "transaction": directory / TRANSACTION_FILE,
        "receipt": directory / RECEIPT_FILE,
    }


def read_regular(path: Path, *, required: bool, limit: int = MAX_ARTIFACT_BYTES) -> bytes | None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        if required:
            raise GuardError(f"missing required artifact: {path.name}")
        return None
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise GuardError(f"artifact must be a regular file: {path.name}")
    if metadata.st_size > limit:
        raise GuardError(f"artifact exceeds size limit: {path.name}")
    return path.read_bytes()


def decode_text(data: bytes, label: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise GuardError(f"{label} is not valid UTF-8") from error


def section(lines: list[str], heading: str) -> list[str]:
    matches = [index for index, line in enumerate(lines) if line == heading]
    if len(matches) != 1:
        raise GuardError(f"expected exactly one section {heading}")
    start = matches[0] + 1
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return lines[start:end]


def field_index(lines: list[str], heading: str, label: str) -> int:
    body = section(lines, heading)
    start = lines.index(heading) + 1
    matches = [
        start + offset
        for offset, line in enumerate(body)
        if line.startswith(f"- {label}")
    ]
    if len(matches) != 1:
        raise GuardError(f"expected exactly one {label} field in {heading}")
    return matches[0]


def field_value(lines: list[str], heading: str, label: str) -> str:
    return lines[field_index(lines, heading, label)].removeprefix(f"- {label}").strip()


def replace_field(lines: list[str], heading: str, label: str, value: str) -> None:
    lines[field_index(lines, heading, label)] = f"- {label}{value}"


def table_rows(lines: list[str], heading: str, columns: int) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section(lines, heading):
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != columns:
            raise GuardError(f"invalid table width in {heading}")
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        rows.append(cells)
    if rows:
        rows = rows[1:]
    return rows


def acceptance_ids(spec_data: bytes) -> list[str]:
    lines = decode_text(spec_data, "01-spec.md").splitlines()
    values: list[str] = []
    for line in section(lines, "## Acceptance Criteria"):
        match = re.match(r"^- (AC-\d{3})\s*:", line)
        if match:
            values.append(match.group(1))
    if not values:
        raise GuardError("specification must contain at least one AC-NNN")
    if len(values) != len(set(values)):
        raise GuardError("specification contains duplicate AC-IDs")
    return values


def open_questions(lines: list[str]) -> set[str]:
    values = QUESTION_RE.findall("\n".join(section(lines, "## Open Questions")))
    if len(values) != len(set(values)):
        raise GuardError("Open Questions contains duplicate Q-IDs")
    return set(values)


def open_change_requests(lines: list[str]) -> set[str]:
    result: set[str] = set()
    seen: set[str] = set()
    for row in table_rows(lines, "## Change Requests", 6):
        if not CHANGE_RE.fullmatch(row[0]):
            continue
        if row[0] in seen:
            raise GuardError("Change Requests contains duplicate CR-IDs")
        seen.add(row[0])
        if row[1].casefold() == "open":
            result.add(row[0])
    return result


def validate_timestamp(value: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise GuardError("decision-at must be ISO-8601") from error
    if parsed.tzinfo is None:
        raise GuardError("decision-at must include a timezone")


def validate_design(data: bytes, feature_id: str) -> tuple[list[str], set[str], set[str]]:
    lines = decode_text(data, DESIGN_CANDIDATE).splitlines()
    if not lines or lines[0] != f"# Conception Epic : {feature_id}":
        raise GuardError("Epic design heading does not match feature-id")
    for heading in (
        "## Summary",
        "## Delegation Record",
        "## Epic Scope",
        "## Architecture Boundaries",
        "## Shared Decisions",
        "## Open Questions",
        "## Resolved Questions",
        "## Change Requests",
        "## User Decision",
    ):
        section(lines, heading)
    roles: list[str] = []
    for row in table_rows(lines, "## Delegation Record", 4):
        if row[0] not in {"spring-architect", "react-nextjs-architect"}:
            raise GuardError(f"unsupported architect role: {row[0]}")
        if row[1] != "ready":
            raise GuardError(f"architect role is not ready: {row[0]}")
        if row[3] not in {"aucun", "[]"}:
            raise GuardError(f"delegated role modified files: {row[0]}")
        roles.append(row[0])
    if not roles or len(roles) != len(set(roles)):
        raise GuardError("delegation record must contain unique architect roles")
    stack = field_value(lines, "## Summary", "stacks: ")
    expected_roles = {
        "spring": {"spring-architect"},
        "react-nextjs": {"react-nextjs-architect"},
        "full-stack": {"spring-architect", "react-nextjs-architect"},
    }
    if stack not in expected_roles:
        raise GuardError(f"unsupported Epic stack: {stack}")
    if set(roles) != expected_roles[stack]:
        raise GuardError("Epic stack and delegated architect roles are inconsistent")
    status = field_value(lines, "## Summary", "status: ")
    decision = field_value(lines, "## User Decision", "decision: ")
    allowed = {
        ("draft", "en attente"),
        ("request-changes", "request-changes"),
        ("approved", "approve"),
    }
    if (status, decision) not in allowed:
        raise GuardError("Epic design has inconsistent status and decision")
    return lines, open_questions(lines), open_change_requests(lines)


def parse_id_cell(value: str, pattern: re.Pattern[str], empty: str = "aucune") -> list[str]:
    if value.casefold() == empty:
        return []
    ids = pattern.findall(value)
    if not ids or len(ids) != len(set(ids)):
        raise GuardError(f"invalid or duplicate IDs in table cell: {value}")
    return ids


def validate_roadmap(data: bytes, feature_id: str, ac_ids: list[str]) -> dict[str, object]:
    text = decode_text(data, ROADMAP_CANDIDATE)
    if "03-epic-design.candidate.md" in text:
        raise GuardError("Epic roadmap must reference 03-epic-design.md")
    lines = text.splitlines()
    if not lines or lines[0] != f"# Feuille de route Epic : {feature_id}":
        raise GuardError("Epic roadmap heading does not match feature-id")
    for heading in (
        "## Slice ID Registry",
        "## Slice Backlog",
        "## Per-slice Delivery Notes",
        "## AC Coverage",
        "## Open Questions",
        "## Resolved Questions",
    ):
        section(lines, heading)
    if open_questions(lines):
        raise GuardError("Epic roadmap contains open questions")
    registry = section(lines, "## Slice ID Registry")
    marks = [re.fullmatch(r"- high_water_mark: (\d+)", line) for line in registry]
    marks = [match for match in marks if match]
    if len(marks) != 1:
        raise GuardError("roadmap requires one numeric high_water_mark")
    high_water_mark = int(marks[0].group(1))
    retired_lines = [line for line in registry if line.startswith("- retired_ids: ")]
    if len(retired_lines) != 1:
        raise GuardError("roadmap requires one retired_ids field")
    retired_ids = set(SLICE_RE.findall(retired_lines[0]))

    slices: dict[str, dict[str, list[str]]] = {}
    order: list[str] = []
    for row in table_rows(lines, "## Slice Backlog", 5):
        slice_id = row[0]
        if not SLICE_RE.fullmatch(slice_id) or slice_id in slices:
            raise GuardError(f"invalid or duplicate Slice-ID: {slice_id}")
        if not row[1] or "<" in row[1]:
            raise GuardError(f"slice {slice_id} has no concrete outcome")
        slice_acs = parse_id_cell(row[2], AC_RE)
        if not slice_acs:
            raise GuardError(f"slice {slice_id} must cover at least one AC")
        unknown_acs = set(slice_acs) - set(ac_ids)
        if unknown_acs:
            raise GuardError(f"slice {slice_id} references unknown AC-IDs")
        dependencies = parse_id_cell(row[3], SLICE_RE)
        if not MILESTONE_RE.fullmatch(row[4]):
            raise GuardError(f"slice {slice_id} has an invalid milestone")
        slices[slice_id] = {"acs": slice_acs, "dependencies": dependencies}
        order.append(slice_id)
    if not slices:
        raise GuardError("roadmap must contain at least one slice")
    if retired_ids & set(slices):
        raise GuardError("retired Slice-IDs must not be active")
    if max(int(value.removeprefix("S-")) for value in set(slices) | retired_ids) > high_water_mark:
        raise GuardError("high_water_mark is below an active or retired Slice-ID")
    positions = {slice_id: index for index, slice_id in enumerate(order)}
    for slice_id, value in slices.items():
        for dependency in value["dependencies"]:
            if dependency not in slices:
                raise GuardError(f"slice {slice_id} has an unknown dependency")
            if positions[dependency] >= positions[slice_id]:
                raise GuardError("slice backlog is not in acyclic topological order")

    note_ids = [
        match.group(1)
        for line in section(lines, "## Per-slice Delivery Notes")
        if (match := re.fullmatch(r"### (S-\d{3})", line))
    ]
    if len(note_ids) != len(set(note_ids)) or set(note_ids) != set(slices):
        raise GuardError("per-slice notes must match the Slice Backlog exactly")

    coverage: dict[str, list[str]] = {}
    for row in table_rows(lines, "## AC Coverage", 3):
        ac_id = row[0]
        if not AC_RE.fullmatch(ac_id) or ac_id in coverage:
            raise GuardError(f"invalid or duplicate AC coverage row: {ac_id}")
        covered_by = parse_id_cell(row[1], SLICE_RE)
        if row[2].casefold() != "oui" or not covered_by:
            raise GuardError(f"AC is not covered: {ac_id}")
        if any(slice_id not in slices for slice_id in covered_by):
            raise GuardError(f"AC coverage references an unknown slice: {ac_id}")
        if any(ac_id not in slices[slice_id]["acs"] for slice_id in covered_by):
            raise GuardError(f"AC coverage contradicts the Slice Backlog: {ac_id}")
        coverage[ac_id] = covered_by
    if set(coverage) != set(ac_ids):
        raise GuardError("AC coverage must match the specification exactly")
    backlog_coverage = {ac for value in slices.values() for ac in value["acs"]}
    if backlog_coverage != set(ac_ids):
        raise GuardError("Slice Backlog must cover every specification AC")
    return {"slices": len(slices), "high_water_mark": high_water_mark}


def artifact_record(data: bytes | None, mode: int | None = None) -> dict[str, object]:
    if data is None:
        return {"exists": False}
    return {
        "exists": True,
        "data_b64": base64.b64encode(data).decode("ascii"),
        "mode": 0o644 if mode is None else mode,
    }


def decode_artifact(value: object, label: str) -> tuple[bytes | None, int | None]:
    if not isinstance(value, dict) or not isinstance(value.get("exists"), bool):
        raise GuardError(f"invalid transaction artifact: {label}")
    if value["exists"] is False:
        return None, None
    encoded = value.get("data_b64")
    mode = value.get("mode")
    if not isinstance(encoded, str) or not isinstance(mode, int):
        raise GuardError(f"invalid transaction artifact: {label}")
    try:
        return base64.b64decode(encoded, validate=True), mode
    except ValueError as error:
        raise GuardError(f"invalid transaction base64: {label}") from error


def mode_for(path: Path, fallback: int = 0o644) -> int:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return fallback
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise GuardError(f"artifact must be a regular file: {path.name}")
    return stat.S_IMODE(metadata.st_mode)


def fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_replace(path: Path, data: bytes, mode: int | None = None) -> None:
    target_mode = mode_for(path) if mode is None else mode
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, target_mode)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def materialize(path: Path, data: bytes | None, mode: int | None) -> None:
    if data is None:
        if path.is_symlink():
            raise GuardError(f"artifact must not be a symlink: {path.name}")
        path.unlink(missing_ok=True)
        return
    atomic_replace(path, data, 0o644 if mode is None else mode)


def open_lock(path: Path):
    if path.is_symlink():
        raise GuardError("Epic lock must not be a symlink")
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    metadata = os.fstat(descriptor)
    if not stat.S_ISREG(metadata.st_mode):
        os.close(descriptor)
        raise GuardError("Epic lock must be a regular file")
    return os.fdopen(descriptor, "a+b")


def current_artifacts(paths: dict[str, Path]) -> tuple[bytes | None, bytes | None]:
    return (
        read_regular(paths["design_final"], required=False),
        read_regular(paths["roadmap_final"], required=False),
    )


def receipt_identity(
    *,
    expected_token: str,
    target_design: bytes,
    target_roadmap: bytes,
    decision: str,
    evidence: str,
    evidence_mode: str,
    reviewer: str,
    decision_at: str,
    comment: str,
) -> dict[str, object]:
    return {
        "version": 1,
        "operation": "commit-epic-plan",
        "expected_token": expected_token,
        "target_token": pair_token(target_design, target_roadmap),
        "target_design_token": token_for(target_design),
        "target_roadmap_token": token_for(target_roadmap),
        "decision": decision,
        "evidence": evidence,
        "evidence_mode": evidence_mode,
        "reviewer": reviewer,
        "decision_at": decision_at,
        "comment": comment,
    }


def load_json(path: Path, *, required: bool, limit: int = MAX_JOURNAL_BYTES) -> dict | None:
    data = read_regular(path, required=required, limit=limit)
    if data is None:
        return None
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GuardError(f"{path.name} is not valid JSON") from error
    if not isinstance(value, dict):
        raise GuardError(f"{path.name} must contain a JSON object")
    return value


def matching_receipt(paths: dict[str, Path], expected: dict[str, object]) -> bool:
    receipt = load_json(paths["receipt"], required=False)
    return receipt == expected


def recover_transaction(paths: dict[str, Path]) -> str | None:
    transaction = load_json(paths["transaction"], required=False)
    if transaction is None:
        return None
    if transaction.get("version") != 1 or transaction.get("operation") != "commit-epic-plan":
        raise GuardError("unsupported Epic transaction journal")
    previous_design, previous_design_mode = decode_artifact(
        transaction.get("previous_design"), "previous_design"
    )
    previous_roadmap, previous_roadmap_mode = decode_artifact(
        transaction.get("previous_roadmap"), "previous_roadmap"
    )
    target_design, target_design_mode = decode_artifact(
        transaction.get("target_design"), "target_design"
    )
    target_roadmap, target_roadmap_mode = decode_artifact(
        transaction.get("target_roadmap"), "target_roadmap"
    )
    if target_design is None or target_roadmap is None:
        raise GuardError("Epic transaction has incomplete target artifacts")
    receipt = transaction.get("receipt")
    if not isinstance(receipt, dict):
        raise GuardError("Epic transaction has no receipt identity")
    if (
        receipt.get("expected_token") != pair_token(previous_design, previous_roadmap)
        or receipt.get("target_design_token") != token_for(target_design)
        or receipt.get("target_roadmap_token") != token_for(target_roadmap)
        or receipt.get("target_token") != pair_token(target_design, target_roadmap)
    ):
        raise GuardError("Epic transaction receipt hashes do not match its artifacts")
    committed = matching_receipt(paths, receipt)
    if committed:
        materialize(paths["design_final"], target_design, target_design_mode)
        materialize(paths["roadmap_final"], target_roadmap, target_roadmap_mode)
        outcome = "committed"
    else:
        materialize(paths["design_final"], previous_design, previous_design_mode)
        materialize(paths["roadmap_final"], previous_roadmap, previous_roadmap_mode)
        outcome = "rolled-back"
    fsync_directory(paths["directory"])
    paths["transaction"].unlink()
    fsync_directory(paths["directory"])
    return outcome


def validate_candidates(paths: dict[str, Path]) -> tuple[bytes, bytes, list[str], dict[str, object]]:
    spec = read_regular(paths["spec"], required=True)
    design = read_regular(paths["design_candidate"], required=True)
    roadmap = read_regular(paths["roadmap_candidate"], required=True)
    assert spec is not None and design is not None and roadmap is not None
    ac_ids = acceptance_ids(spec)
    _lines, questions, _changes = validate_design(
        design, paths["directory"].name
    )
    if questions:
        raise GuardError("Epic design contains open questions")
    stats = validate_roadmap(roadmap, paths["directory"].name, ac_ids)
    return design, roadmap, ac_ids, stats


def validate_decision_arguments(args: argparse.Namespace) -> None:
    if args.evidence != args.decision:
        raise GuardError("explicit evidence must exactly match the decision")
    if args.evidence_mode not in EVIDENCE_MODES:
        raise GuardError("invalid decision evidence mode")
    if (
        not args.reviewer.strip()
        or args.reviewer == "en attente"
        or "\n" in args.reviewer
        or "\r" in args.reviewer
    ):
        raise GuardError("reviewer must identify the explicit decision author")
    validate_timestamp(args.decision_at)
    if "\n" in args.comment or "\r" in args.comment:
        raise GuardError("comment must be a single line")


def decided_design(data: bytes, args: argparse.Namespace) -> bytes:
    lines = decode_text(data, DESIGN_CANDIDATE).splitlines()
    replace_field(
        lines,
        "## Summary",
        "status: ",
        "approved" if args.decision == "approve" else "request-changes",
    )
    replace_field(
        lines,
        "## Summary",
        "approved_at: ",
        args.decision_at if args.decision == "approve" else "en attente",
    )
    replacements = (
        ("decision: ", args.decision),
        ("reviewer: ", args.reviewer.strip()),
        ("decided_at: ", args.decision_at),
        ("decision_evidence: ", args.evidence),
        ("decision_evidence_mode: ", args.evidence_mode),
        ("comment: ", args.comment),
    )
    for label, value in replacements:
        replace_field(lines, "## User Decision", label, value)
    result = ("\n".join(lines) + "\n").encode("utf-8")
    validate_design(result, args.feature_id)
    return result


def completed_retry(
    paths: dict[str, Path], args: argparse.Namespace
) -> dict[str, object] | None:
    receipt = load_json(paths["receipt"], required=False)
    if receipt is None:
        return None
    fixed = {
        "version": 1,
        "operation": "commit-epic-plan",
        "expected_token": args.expected_token,
        "decision": args.decision,
        "evidence": args.evidence,
        "evidence_mode": args.evidence_mode,
        "reviewer": args.reviewer.strip(),
        "decision_at": args.decision_at,
        "comment": args.comment,
    }
    if any(receipt.get(key) != value for key, value in fixed.items()):
        return None
    design, roadmap = current_artifacts(paths)
    if (
        design is None
        or roadmap is None
        or receipt.get("target_design_token") != token_for(design)
        or receipt.get("target_roadmap_token") != token_for(roadmap)
        or receipt.get("target_token") != pair_token(design, roadmap)
    ):
        return None
    paths["design_candidate"].unlink(missing_ok=True)
    paths["roadmap_candidate"].unlink(missing_ok=True)
    fsync_directory(paths["directory"])
    return {
        "committed": True,
        "idempotent": True,
        "token": receipt["target_token"],
        "decision": args.decision,
    }


def snapshot_command(args: argparse.Namespace) -> None:
    paths = feature_paths(args.feature_dir)
    with open_lock(paths["lock"]) as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        recovery = recover_transaction(paths)
        design, roadmap = current_artifacts(paths)
    print(
        json.dumps(
            {
                "token": pair_token(design, roadmap),
                "design": token_for(design),
                "roadmap": token_for(roadmap),
                "recovered": recovery is not None,
                "recovery_outcome": recovery,
            },
            sort_keys=True,
        )
    )


def validate_candidates_command(args: argparse.Namespace) -> None:
    paths = feature_paths(args.feature_dir)
    design, roadmap, ac_ids, stats = validate_candidates(paths)
    print(
        json.dumps(
            {
                "valid": True,
                "design_token": token_for(design),
                "roadmap_token": token_for(roadmap),
                "acceptance_criteria": len(ac_ids),
                **stats,
            },
            sort_keys=True,
        )
    )


def decide_command(args: argparse.Namespace) -> None:
    validate_decision_arguments(args)
    paths = feature_paths(args.feature_dir)
    args.feature_id = paths["directory"].name
    with open_lock(paths["lock"]) as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        recover_transaction(paths)
        design_candidate = read_regular(paths["design_candidate"], required=False)
        roadmap_candidate = read_regular(paths["roadmap_candidate"], required=False)
        if design_candidate is None or roadmap_candidate is None:
            retry = completed_retry(paths, args)
            if retry is None:
                raise GuardError("Epic candidates are missing and no matching receipt exists")
            print(json.dumps(retry, sort_keys=True))
            return

        design, roadmap, ac_ids, stats = validate_candidates(paths)
        design_lines, _questions, changes = validate_design(
            design, paths["directory"].name
        )
        current_design, current_roadmap = current_artifacts(paths)
        current_token = pair_token(current_design, current_roadmap)
        if current_token != args.expected_token:
            raise GuardError(
                f"Epic artifacts changed concurrently: expected {args.expected_token}, "
                f"found {current_token}"
            )

        if args.decision == "request-changes":
            if not changes:
                raise GuardError("request-changes requires at least one open CR-NNN")
            revised = decided_design(design, args)
            atomic_replace(paths["design_candidate"], revised)
            fsync_directory(paths["directory"])
            print(
                json.dumps(
                    {
                        "committed": False,
                        "candidate_updated": True,
                        "decision": args.decision,
                        "acceptance_criteria": len(ac_ids),
                        **stats,
                    },
                    sort_keys=True,
                )
            )
            return

        if changes:
            raise GuardError("approve requires zero open CR-NNN")
        approved_design = decided_design(design, args)
        receipt = receipt_identity(
            expected_token=args.expected_token,
            target_design=approved_design,
            target_roadmap=roadmap,
            decision=args.decision,
            evidence=args.evidence,
            evidence_mode=args.evidence_mode,
            reviewer=args.reviewer.strip(),
            decision_at=args.decision_at,
            comment=args.comment,
        )
        previous_design_mode = (
            mode_for(paths["design_final"]) if current_design is not None else None
        )
        previous_roadmap_mode = (
            mode_for(paths["roadmap_final"]) if current_roadmap is not None else None
        )
        target_design_mode = mode_for(
            paths["design_final"], mode_for(paths["design_candidate"])
        )
        target_roadmap_mode = mode_for(
            paths["roadmap_final"], mode_for(paths["roadmap_candidate"])
        )
        transaction = {
            "version": 1,
            "operation": "commit-epic-plan",
            "previous_design": artifact_record(current_design, previous_design_mode),
            "previous_roadmap": artifact_record(current_roadmap, previous_roadmap_mode),
            "target_design": artifact_record(approved_design, target_design_mode),
            "target_roadmap": artifact_record(roadmap, target_roadmap_mode),
            "receipt": receipt,
        }
        atomic_replace(
            paths["transaction"],
            json.dumps(transaction, sort_keys=True).encode("utf-8"),
            0o600,
        )
        fsync_directory(paths["directory"])
        atomic_replace(paths["design_final"], approved_design, target_design_mode)
        fsync_directory(paths["directory"])
        atomic_replace(paths["roadmap_final"], roadmap, target_roadmap_mode)
        fsync_directory(paths["directory"])
        atomic_replace(
            paths["receipt"],
            json.dumps(receipt, sort_keys=True).encode("utf-8"),
            0o600,
        )
        fsync_directory(paths["directory"])
        paths["transaction"].unlink()
        paths["design_candidate"].unlink()
        paths["roadmap_candidate"].unlink()
        fsync_directory(paths["directory"])
    print(
        json.dumps(
            {
                "committed": True,
                "idempotent": False,
                "token": receipt["target_token"],
                "decision": args.decision,
                "acceptance_criteria": len(ac_ids),
                **stats,
            },
            sort_keys=True,
        )
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(required=True)
    snapshot = commands.add_parser("snapshot")
    snapshot.add_argument("--feature-dir", required=True)
    snapshot.set_defaults(handler=snapshot_command)
    validate = commands.add_parser("validate-candidates")
    validate.add_argument("--feature-dir", required=True)
    validate.set_defaults(handler=validate_candidates_command)
    decide = commands.add_parser("decide")
    decide.add_argument("--feature-dir", required=True)
    decide.add_argument("--expected-token", required=True)
    decide.add_argument("--decision", choices=sorted(DECISIONS), required=True)
    decide.add_argument("--evidence", required=True)
    decide.add_argument("--evidence-mode", choices=sorted(EVIDENCE_MODES), required=True)
    decide.add_argument("--reviewer", required=True)
    decide.add_argument("--decision-at", required=True)
    decide.add_argument("--comment", default="aucun")
    decide.set_defaults(handler=decide_command)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        args.handler(args)
    except (GuardError, OSError) as error:
        print(json.dumps({"committed": False, "error": str(error)}, sort_keys=True))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
