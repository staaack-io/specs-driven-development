from __future__ import annotations

import argparse
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout


SCRIPT = Path(__file__).with_name("review_decision_guard.py")
SPEC = importlib.util.spec_from_file_location("review_decision_guard", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


def report(*, verdict: str = "ready-for-approval", questions: int = 0) -> str:
    return f"""# Revue de spécification : feature

## Summary

- verdict: {verdict}
- acs_total: 20
- acs_failed: 0
- open_questions: {questions}
- reviewer: en attente
- reviewed_at: en attente
- decision_evidence: en attente
- decision_evidence_mode: en attente
- next_command: en attente

## User Decision

- Décision : en attente
- Relecteur : en attente
- Date : en attente
- Commentaire : aucun
- Preuve explicite : en attente
- Mode de preuve : en attente

## Handoff

En attente.
"""


class ReviewDecisionGuardTest(unittest.TestCase):
    def write_report(self, root: Path, content: str | None = None) -> Path:
        path = root / "02-spec-review.md"
        path.write_text(content or report(), encoding="utf-8")
        return path

    def finalize(
        self,
        path: Path,
        *,
        decision: str,
        evidence: str,
        evidence_mode: str = "direct-response",
        token: str | None = None,
    ) -> None:
        args = argparse.Namespace(
            report=path,
            expected_token=token or guard.token_for(path.read_bytes()),
            decision=decision,
            evidence=evidence,
            evidence_mode=evidence_mode,
            reviewer="utilisateur",
            decision_at="2026-07-30T17:00:00+02:00",
            next_command=(
                "/sdd-plan feature"
                if decision == "approve"
                else "/sdd-spec --continue feature"
            ),
            comment="aucun",
        )
        with redirect_stdout(io.StringIO()):
            guard.finalize_command(args)

    def test_first_success_is_only_provisional(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_report(Path(temporary))
            guard.require_provisional(guard.parse_report(path.read_bytes()))
            self.assertIn("- reviewer: en attente", path.read_text())

    def test_auto_approved_report_is_rejected_as_provisional(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_report(
                Path(temporary), report(verdict="approve")
            )
            with self.assertRaises(guard.GuardError):
                guard.require_provisional(guard.parse_report(path.read_bytes()))

    def test_final_report_without_durable_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            content = report(verdict="approve").replace(
                "- reviewer: en attente", "- reviewer: utilisateur"
            ).replace(
                "- reviewed_at: en attente",
                "- reviewed_at: 2026-07-30T17:00:00+02:00",
            )
            path = self.write_report(Path(temporary), content)
            with self.assertRaises(guard.GuardError):
                guard.validate_final(guard.parse_report(path.read_bytes()))

    def test_explicit_approve_is_recorded_durably(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_report(Path(temporary))
            self.finalize(path, decision="approve", evidence=" approve ")
            lines = guard.parse_report(path.read_bytes())
            guard.validate_final(lines)
            self.assertEqual(
                guard.field_value(lines, guard.SUMMARY, "reviewer: "),
                "utilisateur",
            )
            self.assertEqual(
                guard.field_value(lines, guard.SUMMARY, "decision_evidence: "),
                "approve",
            )

    def test_explicit_request_changes_is_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_report(Path(temporary))
            self.finalize(
                path,
                decision="request-changes",
                evidence="request-changes",
                evidence_mode="decision-option",
            )
            lines = guard.parse_report(path.read_bytes())
            guard.validate_final(lines)
            self.assertEqual(
                guard.field_value(lines, guard.SUMMARY, "verdict: "),
                "request-changes",
            )

    def test_command_invocation_is_not_decision_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_report(Path(temporary))
            with self.assertRaises(guard.GuardError):
                self.finalize(
                    path,
                    decision="approve",
                    evidence="/sdd-spec-review feature",
                )

    def test_concurrent_report_change_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_report(Path(temporary))
            old_token = guard.token_for(path.read_bytes())
            path.write_text(report().replace("20", "21"), encoding="utf-8")
            with self.assertRaises(guard.GuardError):
                self.finalize(
                    path,
                    decision="approve",
                    evidence="approve",
                    token=old_token,
                )

    def test_approve_with_open_questions_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_report(Path(temporary), report(questions=1))
            with self.assertRaises(guard.GuardError):
                self.finalize(path, decision="approve", evidence="approve")


if __name__ == "__main__":
    unittest.main()
