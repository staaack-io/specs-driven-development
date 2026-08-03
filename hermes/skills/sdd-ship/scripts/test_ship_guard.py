#!/usr/bin/env python3
"""Executable contract for the Hermes ``/sdd-ship`` guard."""

from __future__ import annotations

from contextlib import contextmanager
import ast
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "ship_guard.py"


def load_guard():
    spec = importlib.util.spec_from_file_location("ship_guard", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load ship guard")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeRuntime:
    def __init__(self) -> None:
        self.events: list[str] = []

    @contextmanager
    def global_lock(self, _root: Path):
        self.events.append("lock:enter")
        try:
            yield
        finally:
            self.events.append("lock:exit")

    def atomic_replace(self, path: Path, data: bytes) -> None:
        self.events.append(f"write:{path.name}")
        path.write_bytes(data)

    def validate_worker_changes(
        self,
        feature_id: str,
        *,
        task_id: str,
        files_in_scope: list[str],
        changed_paths: list[str],
    ) -> None:
        del feature_id
        self.events.append(
            f"validate:{task_id}:{files_in_scope[0]}:{changed_paths[0]}"
        )


class ShipGuardPublicationTests(unittest.TestCase):
    def test_t_022_t1_ship_guard_is_published(self) -> None:
        """T-022-T1 / AC-152: the public ship guard must exist."""

        self.assertTrue(
            MODULE_PATH.is_file(),
            "T-022-T1: ship_guard.py must publish /sdd-ship",
        )


class ShipGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.guard = load_guard()
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.feature_id = "checkout-shipping"
        self.feature = self.root / ".specs" / self.feature_id
        self.feature.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def passing_gates(self):
        return self.guard.PreShipEvidence(
            validation="PASS",
            review="Approve",
            open_questions=(),
            baseline_regressions=(),
            out_of_scope_paths=(),
            diff_nonempty=True,
        )

    def complete_plan(self):
        return self.guard.ShipPlan(
            rollback=self.guard.RollbackPlan(
                detection="alert checkout_error_rate > 2%",
                limit_damage="disable CHECKOUT_V2 in under five minutes",
                restore_state="reconcile events from the recorded offset",
            ),
            observability=(
                self.guard.ObservabilitySurface(
                    surface="POST /checkout",
                    metric="checkout.duration histogram",
                    log_keys=("feature_id", "ac_id"),
                    alert="checkout_error_rate > 2%",
                    dashboard="https://metrics.example.invalid/checkout",
                ),
            ),
            feature_flag=self.guard.FeatureFlag(
                name="CHECKOUT_V2",
                default="off",
                emergency_stop="set CHECKOUT_V2=off",
                owner="release-owner",
                removal="remove after 14 healthy days",
            ),
            external_notes=("Le paiement est plus fiable.",),
            internal_notes=("AC-152", "AC-153", "AC-261", "AC-262", "AC-263"),
            deployment_command="kubectl rollout restart deployment/checkout",
        )

    def test_t_022_t2_parses_optional_feature_and_base_as_data(self) -> None:
        """T-022-T2: arguments are validated data, never a shell command."""

        request = self.guard.parse_invocation(
            ("checkout-shipping", "--base", "origin/main")
        )
        self.assertEqual("checkout-shipping", request.feature_id)
        self.assertEqual("origin/main", request.base_ref)
        self.assertEqual((None, "origin/main"), tuple(self.guard.parse_invocation(())))
        with self.assertRaisesRegex(self.guard.GuardError, "arguments"):
            self.guard.parse_invocation(("checkout", "--unknown"))
        with self.assertRaisesRegex(self.guard.GuardError, "base"):
            self.guard.parse_invocation(("--base", "main; deploy"))

    def test_t_022_t3_requires_every_pre_ship_gate_before_publication(self) -> None:
        """T-022-T3: validation, review, questions, baseline and scope fail closed."""

        checks = (
            ("validation", {"validation": "FAIL"}),
            ("review", {"review": "Request changes"}),
            ("question", {"open_questions": ("Q-001",)}),
            ("baseline", {"baseline_regressions": ("test failure",)}),
            ("scope", {"out_of_scope_paths": ("secrets.txt",)}),
            ("diff", {"diff_nonempty": False}),
        )
        evidence = self.passing_gates()
        for message, changes in checks:
            with self.subTest(message=message):
                rejected = self.guard.PreShipEvidence(
                    **{**evidence.__dict__, **changes}
                )
                with self.assertRaisesRegex(self.guard.GuardError, message):
                    self.guard.validate_preconditions(rejected)

        self.assertEqual(
            ("validation", "review", "questions", "baseline", "scope", "diff"),
            self.guard.validate_preconditions(evidence),
        )

    def test_t_022_t4_requires_actionable_three_stage_rollback(self) -> None:
        """T-022-T4 / AC-152: rollback covers detection, five minutes and restore."""

        valid = self.complete_plan().rollback
        self.assertEqual(valid, self.guard.validate_rollback(valid))
        for field in ("detection", "limit_damage", "restore_state"):
            with self.subTest(field=field):
                invalid = self.guard.RollbackPlan(
                    **{**valid.__dict__, field: ""}
                )
                with self.assertRaisesRegex(self.guard.GuardError, field):
                    self.guard.validate_rollback(invalid)
        commit_only = self.guard.RollbackPlan("alert", "under five minutes", "revert commit")
        with self.assertRaisesRegex(self.guard.GuardError, "restore"):
            self.guard.validate_rollback(commit_only)
        too_slow = self.guard.RollbackPlan(
            "alert", "disable flag", "reconcile events", limit_within_minutes=6
        )
        with self.assertRaisesRegex(self.guard.GuardError, "five minutes"):
            self.guard.validate_rollback(too_slow)

    def test_t_022_t5_requires_observability_or_explicit_justification(self) -> None:
        """T-022-T5 / AC-261: every surface has metrics, logs, alert and dashboard."""

        surface = self.complete_plan().observability[0]
        self.assertEqual((surface,), self.guard.validate_observability((surface,)))
        missing_metric = self.guard.ObservabilitySurface(
            surface=surface.surface,
            metric="",
            log_keys=surface.log_keys,
            alert=surface.alert,
            dashboard=surface.dashboard,
        )
        with self.assertRaisesRegex(self.guard.GuardError, "metric"):
            self.guard.validate_observability((missing_metric,))
        justified = self.guard.ObservabilitySurface(
            surface="no new surface",
            metric="n/a",
            log_keys=(),
            alert="n/a",
            dashboard="n/a",
            justification="documentation-only change; existing telemetry is unchanged",
        )
        self.assertEqual((justified,), self.guard.validate_observability((justified,)))

    def test_t_022_t6_requires_complete_feature_flag_posture(self) -> None:
        """T-022-T6 / AC-262: flag value, kill switch, owner and removal are explicit."""

        flag = self.complete_plan().feature_flag
        self.assertEqual(flag, self.guard.validate_feature_flag(flag))
        for field in ("name", "default", "emergency_stop", "owner", "removal"):
            with self.subTest(field=field):
                invalid = self.guard.FeatureFlag(**{**flag.__dict__, field: ""})
                with self.assertRaisesRegex(self.guard.GuardError, field):
                    self.guard.validate_feature_flag(invalid)

    def test_t_022_t7_writes_external_and_internal_notes_without_secrets(self) -> None:
        """T-022-T7 / AC-263: both note audiences exist and secrets are rejected."""

        plan = self.complete_plan()
        self.assertEqual(
            (plan.external_notes, plan.internal_notes),
            self.guard.validate_release_notes(plan.external_notes, plan.internal_notes),
        )
        with self.assertRaisesRegex(self.guard.GuardError, "external"):
            self.guard.validate_release_notes((), plan.internal_notes)
        with self.assertRaisesRegex(self.guard.GuardError, "secret"):
            self.guard.validate_release_notes(
                plan.external_notes,
                ("github_pat_abcdefghijklmnopqrstuvwxyz123456",),
            )
        with self.assertRaisesRegex(self.guard.GuardError, "sensitive"):
            self.guard.validate_release_notes(
                plan.external_notes,
                ("diagnostic saved in " + "/" + "Users/alice/private/release.log",),
            )

    def test_t_022_t8_publishes_one_plan_but_never_executes_deployment(self) -> None:
        """T-022-T8 / AC-153 / AC-235: command is inert plan data only."""

        runtime = FakeRuntime()
        target = self.guard.publish_ship_plan(
            self.root,
            self.feature_id,
            self.passing_gates(),
            self.complete_plan(),
            runtime=runtime,
        )
        self.assertEqual(self.feature.resolve() / "09-ship-plan.md", target)
        self.assertEqual(
            [
                "validate:T-022:.specs/checkout-shipping/09-ship-plan.md:"
                ".specs/checkout-shipping/09-ship-plan.md",
                "lock:enter",
                "write:09-ship-plan.md",
                "lock:exit",
            ],
            runtime.events,
        )
        content = target.read_text(encoding="utf-8")
        self.assertIn("kubectl rollout restart deployment/checkout", content)
        self.assertIn("commande affichée uniquement", content)

        source = MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_imports = {"subprocess", "socket", "urllib", "http", "requests", "paramiko"}
        imported = {
            alias.name.split(".", maxsplit=1)[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertTrue(forbidden_imports.isdisjoint(imported))
        forbidden_calls = {"exec", "eval", "system", "popen", "run", "Popen"}
        called = {
            node.func.id if isinstance(node.func, ast.Name) else node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, (ast.Name, ast.Attribute))
        }
        self.assertTrue(forbidden_calls.isdisjoint(called))

        unsafe = self.complete_plan()
        unsafe = self.guard.ShipPlan(
            **{**unsafe.__dict__, "deployment_command": "```sh deploy```"}
        )
        with self.assertRaisesRegex(self.guard.GuardError, "unsafe"):
            self.guard.validate_plan(unsafe)

    def test_failed_precondition_preserves_previous_plan(self) -> None:
        """AC-153: a failed gate cannot publish a partial replacement."""

        previous = self.feature / "09-ship-plan.md"
        previous.write_text("previous\n", encoding="utf-8")
        rejected = self.guard.PreShipEvidence(
            **{**self.passing_gates().__dict__, "validation": "FAIL"}
        )
        with self.assertRaisesRegex(self.guard.GuardError, "validation"):
            self.guard.publish_ship_plan(
                self.root,
                self.feature_id,
                rejected,
                self.complete_plan(),
                runtime=FakeRuntime(),
            )
        self.assertEqual("previous\n", previous.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
