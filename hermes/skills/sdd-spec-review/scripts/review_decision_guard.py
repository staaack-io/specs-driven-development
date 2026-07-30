#!/usr/bin/env python3
"""Deterministic two-step guard for SDD specification review decisions."""

from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile


class GuardError(RuntimeError):
    pass


SUMMARY = "## Summary"
USER_DECISION = "## User Decision"
DECISIONS = {"approve", "request-changes"}
EVIDENCE_MODES = {"direct-response", "decision-option"}


def token_for(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def section_bounds(lines: list[str], heading: str) -> tuple[int, int]:
    try:
        start = lines.index(heading) + 1
    except ValueError as error:
        raise GuardError(f"missing section: {heading}") from error
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return start, end


def field_index(lines: list[str], heading: str, label: str) -> int:
    start, end = section_bounds(lines, heading)
    matches = [
        index
        for index in range(start, end)
        if lines[index].startswith(f"- {label}")
    ]
    if len(matches) != 1:
        raise GuardError(f"expected exactly one {label} field in {heading}")
    return matches[0]


def field_value(lines: list[str], heading: str, label: str) -> str:
    line = lines[field_index(lines, heading, label)]
    return line.removeprefix(f"- {label}").strip()


def replace_field(lines: list[str], heading: str, label: str, value: str) -> None:
    lines[field_index(lines, heading, label)] = f"- {label}{value}"


def parse_report(data: bytes) -> list[str]:
    try:
        return data.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise GuardError("report is not valid UTF-8") from error


def require_provisional(lines: list[str]) -> None:
    expected = (
        (SUMMARY, "verdict: ", "ready-for-approval"),
        (SUMMARY, "reviewer: ", "en attente"),
        (SUMMARY, "reviewed_at: ", "en attente"),
        (SUMMARY, "decision_evidence: ", "en attente"),
        (SUMMARY, "decision_evidence_mode: ", "en attente"),
        (SUMMARY, "next_command: ", "en attente"),
        (USER_DECISION, "Décision : ", "en attente"),
        (USER_DECISION, "Relecteur : ", "en attente"),
        (USER_DECISION, "Date : ", "en attente"),
        (USER_DECISION, "Preuve explicite : ", "en attente"),
        (USER_DECISION, "Mode de preuve : ", "en attente"),
    )
    for heading, label, value in expected:
        actual = field_value(lines, heading, label)
        if actual != value:
            raise GuardError(
                f"provisional report requires {label}{value}, found {actual}"
            )
    questions = field_value(lines, SUMMARY, "open_questions: ")
    try:
        question_count = int(questions)
    except ValueError as error:
        raise GuardError("open_questions must be an integer") from error
    if question_count != 0:
        raise GuardError("ready-for-approval requires zero open questions")


def normalize_decision(value: str) -> str:
    normalized = value.strip().casefold()
    if normalized not in DECISIONS:
        raise GuardError("explicit evidence must be exactly approve or request-changes")
    return normalized


def validate_timestamp(value: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise GuardError("decision-at must be ISO-8601") from error
    if parsed.tzinfo is None:
        raise GuardError("decision-at must include a timezone")


def require_next_command(decision: str, value: str) -> None:
    if "\n" in value or "\r" in value:
        raise GuardError("next-command must be a single line")
    allowed = (
        ("/sdd-plan ", "/sdd-epic-plan ")
        if decision == "approve"
        else ("/sdd-spec --continue ",)
    )
    if not value.startswith(allowed):
        raise GuardError(f"next-command is invalid for {decision}")


def validate_final(lines: list[str]) -> None:
    decision = field_value(lines, SUMMARY, "verdict: ")
    if decision not in DECISIONS:
        raise GuardError("final verdict must be approve or request-changes")
    evidence = normalize_decision(
        field_value(lines, SUMMARY, "decision_evidence: ")
    )
    if evidence != decision:
        raise GuardError("decision evidence does not match the final verdict")
    mode = field_value(lines, SUMMARY, "decision_evidence_mode: ")
    if mode not in EVIDENCE_MODES:
        raise GuardError("invalid decision evidence mode")
    reviewer = field_value(lines, SUMMARY, "reviewer: ")
    if not reviewer or reviewer == "en attente":
        raise GuardError("a final decision requires a reviewer")
    reviewed_at = field_value(lines, SUMMARY, "reviewed_at: ")
    validate_timestamp(reviewed_at)
    questions = field_value(lines, SUMMARY, "open_questions: ")
    try:
        question_count = int(questions)
    except ValueError as error:
        raise GuardError("open_questions must be an integer") from error
    if decision == "approve" and question_count != 0:
        raise GuardError("approve requires zero open questions")
    require_next_command(
        decision, field_value(lines, SUMMARY, "next_command: ")
    )
    if field_value(lines, USER_DECISION, "Décision : ") != decision:
        raise GuardError("User Decision does not match the final verdict")
    if field_value(lines, USER_DECISION, "Relecteur : ") != reviewer:
        raise GuardError("User Decision reviewer does not match Summary")
    if field_value(lines, USER_DECISION, "Date : ") != reviewed_at:
        raise GuardError("User Decision date does not match Summary")
    if field_value(lines, USER_DECISION, "Preuve explicite : ") != evidence:
        raise GuardError("User Decision evidence does not match Summary")
    if field_value(lines, USER_DECISION, "Mode de preuve : ") != mode:
        raise GuardError("User Decision evidence mode does not match Summary")


def atomic_replace(path: Path, data: bytes) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def validate_provisional_command(args: argparse.Namespace) -> None:
    data = args.report.read_bytes()
    require_provisional(parse_report(data))
    print(json.dumps({"provisional": True, "token": token_for(data)}))


def validate_final_command(args: argparse.Namespace) -> None:
    data = args.report.read_bytes()
    validate_final(parse_report(data))
    print(json.dumps({"final": True, "token": token_for(data)}))


def finalize_command(args: argparse.Namespace) -> None:
    lock_path = args.report.with_name(".spec-review.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        data = args.report.read_bytes()
        if token_for(data) != args.expected_token:
            raise GuardError("report changed after the provisional review")
        lines = parse_report(data)
        require_provisional(lines)
        decision = normalize_decision(args.decision)
        evidence = normalize_decision(args.evidence)
        if evidence != decision:
            raise GuardError(
                "explicit evidence does not match the requested decision"
            )
        if args.evidence_mode not in EVIDENCE_MODES:
            raise GuardError("invalid evidence mode")
        reviewer = args.reviewer.strip()
        if (
            not reviewer
            or reviewer == "en attente"
            or "\n" in reviewer
            or "\r" in reviewer
        ):
            raise GuardError("reviewer must identify the explicit decision author")
        validate_timestamp(args.decision_at)
        require_next_command(decision, args.next_command)
        if "\n" in args.comment or "\r" in args.comment:
            raise GuardError("comment must be a single line")

        replacements = (
            (SUMMARY, "verdict: ", decision),
            (SUMMARY, "reviewer: ", reviewer),
            (SUMMARY, "reviewed_at: ", args.decision_at),
            (SUMMARY, "decision_evidence: ", evidence),
            (SUMMARY, "decision_evidence_mode: ", args.evidence_mode),
            (SUMMARY, "next_command: ", args.next_command),
            (USER_DECISION, "Décision : ", decision),
            (USER_DECISION, "Relecteur : ", reviewer),
            (USER_DECISION, "Date : ", args.decision_at),
            (USER_DECISION, "Commentaire : ", args.comment),
            (USER_DECISION, "Preuve explicite : ", evidence),
            (USER_DECISION, "Mode de preuve : ", args.evidence_mode),
        )
        for heading, label, value in replacements:
            replace_field(lines, heading, label, value)
        validate_final(lines)
        final_data = ("\n".join(lines) + "\n").encode("utf-8")
        atomic_replace(args.report, final_data)
    print(
        json.dumps(
            {
                "decision": decision,
                "reviewer": reviewer,
                "token": token_for(final_data),
            }
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(required=True)

    provisional = commands.add_parser("validate-provisional")
    provisional.add_argument("--report", type=Path, required=True)
    provisional.set_defaults(handler=validate_provisional_command)

    final = commands.add_parser("validate-final")
    final.add_argument("--report", type=Path, required=True)
    final.set_defaults(handler=validate_final_command)

    finalize = commands.add_parser("finalize")
    finalize.add_argument("--report", type=Path, required=True)
    finalize.add_argument("--expected-token", required=True)
    finalize.add_argument("--decision", choices=sorted(DECISIONS), required=True)
    finalize.add_argument("--evidence", required=True)
    finalize.add_argument(
        "--evidence-mode", choices=sorted(EVIDENCE_MODES), required=True
    )
    finalize.add_argument("--reviewer", default="utilisateur")
    finalize.add_argument("--decision-at", required=True)
    finalize.add_argument("--next-command", required=True)
    finalize.add_argument("--comment", default="aucun")
    finalize.set_defaults(handler=finalize_command)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        args.handler(args)
    except (GuardError, FileNotFoundError, OSError) as error:
        print(f"error: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
