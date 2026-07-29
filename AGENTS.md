# Spec-driven Spring + Angular

This repository uses the spec-driven workflow documented in
`docs/methodology.md`. These instructions apply to Codex in every task.

## Codex workflow surfaces

- Reusable workflows and domain guidance live as separate skills under
  `.agents/skills/<name>/SKILL.md`.
- Project agents live under `.codex/agents/<name>.toml`.
- Templates and checklists live under `.codex/templates/` and
  `.codex/checklists/`.
- Lifecycle guardrails live in `.codex/hooks.json` and `.codex/hooks/`.
- The deterministic harness remains under `.github/scripts/`; that directory is
  infrastructure, not a GitHub Copilot integration.

Invoke workflow skills explicitly with `$spec`, `$spec-review`, `$epic-plan`,
`$plan`, `$build`, `$test`, `$validate`, `$review`, `$ship`, `$onboard`,
`$wire-harness`, `$status`, `$help`, or `$code-simplify`. Natural-language
requests may activate the same skills through their descriptions.

When a workflow skill declares an owning agent, delegate that phase to the
matching project agent when Codex subagents are available. Keep dependent phases
sequential. Do not invent new roles or combine multiple skills into one.

## Source documents

Read the relevant document before changing a workflow artifact or its rules:

- `docs/methodology.md` — phases and gates.
- `docs/harness-principles.md` — self-validation requirements.
- `docs/artifact-contract.md` — `.specs/<feature-id>/` layout.
- `docs/spec-format.md` — EARS-lite acceptance criteria and open questions.

## Phases 1–3: no invention

- Never silently choose a DB engine, auth scheme, error envelope, pagination
  rule, unit, currency, retention policy, or other missing requirement.
- Record missing decisions as `Q-NNN` under `## Open Questions` and stop for the
  user.
- Keep `AC-NNN`, `Q-NNN`, and `T-NNN` identifiers stable; never renumber them.
- For Epic-sized work, produce `03-epic-design.md` and
  `03a-epic-roadmap.md` before slice-level design and tasks.
- Do not advance while an earlier artifact has unresolved questions unless the
  user explicitly defers them with a recorded rationale.

## Phase 4: TDD and scope

- Never edit `src/main/**` unless the active task in
  `.specs/<feature>/.tdd-state.json` has a recorded failing test.
- Edit only files listed in the active task's `files_in_scope`.
- Follow red → green → refactor → simplify for backend and frontend tasks.
- Never delete a test, remove an assertion, lower a quality threshold, or add an
  unexplained disabled test.
- Never use build or verification bypasses such as `-DskipTests`,
  `-Dpit.skip`, `-Dcheckstyle.skip`, `-Dspotbugs.skip`, or `--no-verify`.
- Do not add a production or test dependency without explicit user approval.

## Validation and review

- During `$validate` and `$review`, do not modify production code or tests.
- Treat a missing configured report as an error.
- Treat a skipped test without a documented reason as an error.
- Require every waiver to reference an ADR.
- Use `.github/scripts/harness.sh` as the shared local and CI entry point.

## Commit and deployment boundaries

- Never run `git commit`; show the diff and suggest a commit message for the
  user to execute.
- Never push or deploy unless the user explicitly requests that action.
- `$ship` prepares a plan and a command for the user; it does not deploy.

## Stack conventions

When changing Spring code, apply the separate skills
`spring-boot-4-conventions`, `spring-security-baseline`, and the relevant test or
architecture skills. When changing Angular code, apply `angular-developer` and
the Angular agent for the active phase. Do not copy guidance from one skill into
another; load each relevant skill independently.
