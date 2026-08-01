#!/usr/bin/env python3

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("epic_plan_guard.py")
FIXTURE = Path(__file__).with_name("fixtures") / "valid-epic"
MODULE_SPEC = importlib.util.spec_from_file_location("epic_plan_guard", SCRIPT)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
GUARD = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(GUARD)


class EpicPlanGuardTest(unittest.TestCase):
    def feature(self, temporary: str) -> Path:
        destination = Path(temporary) / ".specs" / "sample-epic"
        destination.parent.mkdir()
        shutil.copytree(FIXTURE, destination)
        return destination

    def run_guard(self, *arguments: str, expected: int = 0) -> dict:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(expected, result.returncode, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def decision_arguments(self, feature: Path, token: str, decision: str = "approve") -> list[str]:
        return [
            "decide",
            "--feature-dir",
            str(feature),
            "--expected-token",
            token,
            "--decision",
            decision,
            "--evidence",
            decision,
            "--evidence-mode",
            "direct-response",
            "--reviewer",
            "alice",
            "--decision-at",
            "2026-08-01T10:00:00+00:00",
            "--comment",
            "validé",
        ]

    def snapshot(self, feature: Path) -> dict:
        return self.run_guard("snapshot", "--feature-dir", str(feature))

    def test_validate_and_promote_approved_epic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            validated = self.run_guard(
                "validate-candidates", "--feature-dir", str(feature)
            )
            self.assertEqual(2, validated["acceptance_criteria"])
            self.assertEqual(2, validated["slices"])
            snapshot = self.snapshot(feature)

            result = self.run_guard(
                *self.decision_arguments(feature, snapshot["token"])
            )

            self.assertTrue(result["committed"])
            design = (feature / GUARD.DESIGN_FINAL).read_text(encoding="utf-8")
            roadmap = (feature / GUARD.ROADMAP_FINAL).read_text(encoding="utf-8")
            self.assertIn("- status: approved", design)
            self.assertIn("- decision: approve", design)
            self.assertIn("- decision_evidence: approve", design)
            self.assertNotIn("03-epic-design.candidate.md", roadmap)
            self.assertIn("03-epic-design.md", roadmap)
            self.assertFalse((feature / GUARD.DESIGN_CANDIDATE).exists())
            self.assertFalse((feature / GUARD.ROADMAP_CANDIDATE).exists())
            self.assertTrue((feature / GUARD.RECEIPT_FILE).is_file())

    def test_completed_promotion_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            snapshot = self.snapshot(feature)
            arguments = self.decision_arguments(feature, snapshot["token"])
            self.run_guard(*arguments)

            retry = self.run_guard(*arguments)

            self.assertTrue(retry["committed"])
            self.assertTrue(retry["idempotent"])

    def test_request_changes_updates_only_design_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            design = feature / GUARD.DESIGN_CANDIDATE
            design.write_text(
                design.read_text(encoding="utf-8").replace(
                    "| (aucune) | — | — | — | — | — |",
                    "| CR-001 | open | 2026-08-01 | séparer les jalons | — | — |",
                ),
                encoding="utf-8",
            )
            snapshot = self.snapshot(feature)

            result = self.run_guard(
                *self.decision_arguments(
                    feature, snapshot["token"], decision="request-changes"
                )
            )

            self.assertFalse(result["committed"])
            self.assertTrue(result["candidate_updated"])
            self.assertIn("- status: request-changes", design.read_text())
            self.assertIn("- decision: request-changes", design.read_text())
            self.assertFalse((feature / GUARD.DESIGN_FINAL).exists())
            self.assertFalse((feature / GUARD.ROADMAP_FINAL).exists())

    def test_request_changes_requires_open_change_request(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            snapshot = self.snapshot(feature)

            result = self.run_guard(
                *self.decision_arguments(
                    feature, snapshot["token"], decision="request-changes"
                ),
                expected=2,
            )

            self.assertIn("requires at least one open CR-NNN", result["error"])

    def test_approve_requires_exact_explicit_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            snapshot = self.snapshot(feature)
            arguments = self.decision_arguments(feature, snapshot["token"])
            arguments[arguments.index("--evidence") + 1] = "continue"

            result = self.run_guard(*arguments, expected=2)

            self.assertIn("explicit evidence", result["error"])
            self.assertFalse((feature / GUARD.DESIGN_FINAL).exists())

    def test_open_question_blocks_validation_and_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            design = feature / GUARD.DESIGN_CANDIDATE
            design.write_text(
                design.read_text(encoding="utf-8").replace(
                    "## Open Questions\n\n- (aucune)",
                    "## Open Questions\n\n- Q-001 : Quelle topologie ?",
                ),
                encoding="utf-8",
            )

            result = self.run_guard(
                "validate-candidates", "--feature-dir", str(feature), expected=2
            )

            self.assertIn("open questions", result["error"])

    def test_duplicate_question_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            design = feature / GUARD.DESIGN_CANDIDATE
            design.write_text(
                design.read_text(encoding="utf-8").replace(
                    "## Open Questions\n\n- (aucune)",
                    "## Open Questions\n\n- Q-001 : A ?\n- Q-001 : B ?",
                ),
                encoding="utf-8",
            )

            result = self.run_guard(
                "validate-candidates", "--feature-dir", str(feature), expected=2
            )

            self.assertIn("duplicate Q-IDs", result["error"])

    def test_roadmap_candidate_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            roadmap = feature / GUARD.ROADMAP_CANDIDATE
            roadmap.write_text(
                roadmap.read_text(encoding="utf-8").replace(
                    "03-epic-design.md", "03-epic-design.candidate.md"
                ),
                encoding="utf-8",
            )

            result = self.run_guard(
                "validate-candidates", "--feature-dir", str(feature), expected=2
            )

            self.assertIn("must reference 03-epic-design.md", result["error"])

    def test_missing_ac_coverage_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            roadmap = feature / GUARD.ROADMAP_CANDIDATE
            roadmap.write_text(
                roadmap.read_text(encoding="utf-8").replace(
                    "| AC-002 | S-002 | oui |\n", ""
                ),
                encoding="utf-8",
            )

            result = self.run_guard(
                "validate-candidates", "--feature-dir", str(feature), expected=2
            )

            self.assertIn("must match the specification exactly", result["error"])

    def test_non_topological_dependency_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            roadmap = feature / GUARD.ROADMAP_CANDIDATE
            roadmap.write_text(
                roadmap.read_text(encoding="utf-8").replace(
                    "| S-001 | exposer l'état du service | AC-001 | aucune | M-001 |",
                    "| S-001 | exposer l'état du service | AC-001 | S-002 | M-001 |",
                ),
                encoding="utf-8",
            )

            result = self.run_guard(
                "validate-candidates", "--feature-dir", str(feature), expected=2
            )

            self.assertIn("acyclic topological order", result["error"])

    def test_delegated_write_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            design = feature / GUARD.DESIGN_CANDIDATE
            design.write_text(
                design.read_text(encoding="utf-8").replace(
                    "| spring-architect | ready | backend/pom.xml | aucun |",
                    "| spring-architect | ready | backend/pom.xml | src/App.java |",
                ),
                encoding="utf-8",
            )

            result = self.run_guard(
                "validate-candidates", "--feature-dir", str(feature), expected=2
            )

            self.assertIn("delegated role modified files", result["error"])

    def test_stack_and_delegated_roles_must_match(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            design = feature / GUARD.DESIGN_CANDIDATE
            design.write_text(
                design.read_text(encoding="utf-8").replace(
                    "- stacks: full-stack", "- stacks: spring"
                ),
                encoding="utf-8",
            )

            result = self.run_guard(
                "validate-candidates", "--feature-dir", str(feature), expected=2
            )

            self.assertIn("stack and delegated architect roles", result["error"])

    def test_duplicate_change_request_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            design = feature / GUARD.DESIGN_CANDIDATE
            design.write_text(
                design.read_text(encoding="utf-8").replace(
                    "| (aucune) | — | — | — | — | — |",
                    "| CR-001 | resolved | 2026-08-01 | A | fait | 2026-08-01 |\n"
                    "| CR-001 | open | 2026-08-01 | B | — | — |",
                ),
                encoding="utf-8",
            )

            result = self.run_guard(
                "validate-candidates", "--feature-dir", str(feature), expected=2
            )

            self.assertIn("duplicate CR-IDs", result["error"])

    def test_feature_directory_outside_specs_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "sample-epic"
            shutil.copytree(FIXTURE, feature)

            result = self.run_guard(
                "validate-candidates", "--feature-dir", str(feature), expected=2
            )

            self.assertIn("exactly .specs/<feature-id>", result["error"])

    def test_concurrent_final_change_rejects_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            snapshot = self.snapshot(feature)
            (feature / GUARD.DESIGN_FINAL).write_text(
                "# Concurrent design\n", encoding="utf-8"
            )

            result = self.run_guard(
                *self.decision_arguments(feature, snapshot["token"]), expected=2
            )

            self.assertIn("changed concurrently", result["error"])
            self.assertEqual(
                "# Concurrent design\n",
                (feature / GUARD.DESIGN_FINAL).read_text(encoding="utf-8"),
            )
            self.assertFalse((feature / GUARD.ROADMAP_FINAL).exists())

    def transaction_fixture(
        self,
        feature: Path,
        previous_design: bytes,
        previous_roadmap: bytes,
        target_design: bytes,
        target_roadmap: bytes,
    ) -> tuple[dict, dict]:
        receipt = GUARD.receipt_identity(
            expected_token=GUARD.pair_token(previous_design, previous_roadmap),
            target_design=target_design,
            target_roadmap=target_roadmap,
            decision="approve",
            evidence="approve",
            evidence_mode="direct-response",
            reviewer="alice",
            decision_at="2026-08-01T10:00:00+00:00",
            comment="validé",
        )
        transaction = {
            "version": 1,
            "operation": "commit-epic-plan",
            "previous_design": GUARD.artifact_record(previous_design, 0o644),
            "previous_roadmap": GUARD.artifact_record(previous_roadmap, 0o644),
            "target_design": GUARD.artifact_record(target_design, 0o644),
            "target_roadmap": GUARD.artifact_record(target_roadmap, 0o644),
            "receipt": receipt,
        }
        return transaction, receipt

    def test_recovery_rolls_back_mixed_artifacts_without_commit_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            previous_design = b"# Old design\n"
            previous_roadmap = b"# Old roadmap\n"
            target_design = b"# New design\n"
            target_roadmap = b"# New roadmap\n"
            transaction, _receipt = self.transaction_fixture(
                feature,
                previous_design,
                previous_roadmap,
                target_design,
                target_roadmap,
            )
            (feature / GUARD.DESIGN_FINAL).write_bytes(target_design)
            (feature / GUARD.ROADMAP_FINAL).write_bytes(previous_roadmap)
            (feature / GUARD.TRANSACTION_FILE).write_text(
                json.dumps(transaction), encoding="utf-8"
            )

            recovered = self.snapshot(feature)

            self.assertEqual("rolled-back", recovered["recovery_outcome"])
            self.assertEqual(previous_design, (feature / GUARD.DESIGN_FINAL).read_bytes())
            self.assertEqual(previous_roadmap, (feature / GUARD.ROADMAP_FINAL).read_bytes())
            self.assertFalse((feature / GUARD.TRANSACTION_FILE).exists())

    def test_recovery_commits_mixed_artifacts_with_commit_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            previous_design = b"# Old design\n"
            previous_roadmap = b"# Old roadmap\n"
            target_design = b"# New design\n"
            target_roadmap = b"# New roadmap\n"
            transaction, receipt = self.transaction_fixture(
                feature,
                previous_design,
                previous_roadmap,
                target_design,
                target_roadmap,
            )
            (feature / GUARD.DESIGN_FINAL).write_bytes(target_design)
            (feature / GUARD.ROADMAP_FINAL).write_bytes(previous_roadmap)
            (feature / GUARD.TRANSACTION_FILE).write_text(
                json.dumps(transaction), encoding="utf-8"
            )
            (feature / GUARD.RECEIPT_FILE).write_text(
                json.dumps(receipt), encoding="utf-8"
            )

            recovered = self.snapshot(feature)

            self.assertEqual("committed", recovered["recovery_outcome"])
            self.assertEqual(target_design, (feature / GUARD.DESIGN_FINAL).read_bytes())
            self.assertEqual(target_roadmap, (feature / GUARD.ROADMAP_FINAL).read_bytes())
            self.assertFalse((feature / GUARD.TRANSACTION_FILE).exists())

    def test_recovery_rejects_tampered_target_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            previous_design = b"# Old design\n"
            previous_roadmap = b"# Old roadmap\n"
            target_design = b"# New design\n"
            target_roadmap = b"# New roadmap\n"
            transaction, receipt = self.transaction_fixture(
                feature,
                previous_design,
                previous_roadmap,
                target_design,
                target_roadmap,
            )
            transaction["target_design"] = GUARD.artifact_record(
                b"# Tampered design\n", 0o644
            )
            (feature / GUARD.DESIGN_FINAL).write_bytes(target_design)
            (feature / GUARD.ROADMAP_FINAL).write_bytes(previous_roadmap)
            (feature / GUARD.TRANSACTION_FILE).write_text(
                json.dumps(transaction), encoding="utf-8"
            )
            (feature / GUARD.RECEIPT_FILE).write_text(
                json.dumps(receipt), encoding="utf-8"
            )

            result = self.run_guard(
                "snapshot", "--feature-dir", str(feature), expected=2
            )

            self.assertIn("receipt hashes", result["error"])
            self.assertEqual(target_design, (feature / GUARD.DESIGN_FINAL).read_bytes())
            self.assertEqual(previous_roadmap, (feature / GUARD.ROADMAP_FINAL).read_bytes())
            self.assertTrue((feature / GUARD.TRANSACTION_FILE).exists())

    @unittest.skipUnless(os.name == "posix", "symlinks are required")
    def test_candidate_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = self.feature(temporary)
            candidate = feature / GUARD.DESIGN_CANDIDATE
            external = feature.parent / "external.md"
            external.write_bytes(candidate.read_bytes())
            candidate.unlink()
            candidate.symlink_to(external)

            result = self.run_guard(
                "validate-candidates", "--feature-dir", str(feature), expected=2
            )

            self.assertIn("regular file", result["error"])
            self.assertTrue(candidate.is_symlink())
            self.assertTrue(external.is_file())


if __name__ == "__main__":
    unittest.main()
