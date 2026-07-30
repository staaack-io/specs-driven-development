---
name: build
description: "Execute one planned SDD task through red, green, refactor, and simplify. Use when the user invokes $build or asks to implement a T-NNN task."
---

# $build

**Phase:** 4 — build (TDD)
**Owning agent:** `.codex/agents/spring-implementer.toml` (collaborates with `spring-test-engineer`)
**Skills used:** `tdd-red-green-refactor`, `spring-boot-4-conventions`, `clarity-over-cleverness`, `junit5-testcontainers-patterns`, `spring-task-decomposition`

## Stack routing

| Task type | Red step agent | Green/refactor/simplify agent |
|---|---|---|
| Backend (`src/main/java/**`, `src/test/java/**`) | `spring-test-engineer` | `spring-implementer` (this agent) |
| Frontend (`app/**/*.{ts,tsx,js,jsx,css}`, `src/**/*.{ts,tsx,js,jsx,css}`) | `react-nextjs-test-engineer` | `react-nextjs-implementer` |

Determine the task type from its `files_in_scope` in `04-tasks.md`. If all files
are frontend paths, delegate to the React/Next.js agents and load
`react-nextjs-developer` separately. If mixed, split into sub-steps: backend
first with Spring agents, then frontend with React/Next.js agents.

## Purpose
Execute one task end-to-end through the four TDD phases (red → green → refactor → simplify), updating `.tdd-state.json` and appending a block to `05-implementation-log.md` after each phase.

## Inputs
- `<task-id>` (e.g. `T-001`). Required.

## Reads
- `.specs/<feature-id>/04-tasks.md`
- `.specs/<feature-id>/03-design.md`
- `.specs/<feature-id>/.tdd-state.json`
- `.agents/skills/tdd-red-green-refactor/SKILL.md` (authoritative)

## Writes
- `src/test/**` and `src/main/**` files listed in `tasks[<task-id>].files_in_scope`.
- `.specs/<feature-id>/.tdd-state.json` (phase transitions).
- `.specs/<feature-id>/05-implementation-log.md` (one `### <task-id> — <phase>` block per phase).

## Process
For the supplied `<task-id>`:

0. **Pre-flight commit check.** Run `git status`. If there are uncommitted changes from any prior task, refuse to start. List the changed files and remind: `git commit → $build <task-id>`.
1. **Activate.** Set `.tdd-state.json` `active_task = <task-id>`. Refuse if any other task is `phase: red|green|refactor|simplify` (one task in flight at a time).
2. **Red.** Write the smallest test that captures the next AC slice. Run it. Capture the failure message into `tasks[<task-id>].red_failure_excerpt`. Set `phase: "red"`. Append log block.
3. **Green.** Write the minimum production code under `files_in_scope` to pass the test. Run only the new test, then run all tests. Set `phase: "green"`. Append log block.
4. **Refactor.** Improve structure without changing behavior. Re-run all tests. Set `phase: "refactor"`. Append log block.
5. **Simplify.** Apply `clarity-over-cleverness` (untangle ternaries, inline once-used helpers, kill dead options, name domain concepts, extract repeated literals). Re-run all tests. Set `phase: "simplify"`. Append log block.
6. **Done.** Set `phase: "done"`, clear `active_task`. If more ACs in this task remain uncovered, immediately re-run from step 2 with the next slice (do not declare done early).
7. **STOP — commit reminder.** Surface: files changed (`git status`), tests passing, suggested commit message. Recommend: `git status → git commit → $build <next-task-id>`. Do not auto-start the next task unless the user explicitly requests chaining.

## Refuse if
- `<task-id>` is not in `.tdd-state.json`.
- Another task is mid-flight (not `pending` or `done`).
- A `src/main/**` edit is attempted while `phase != "red"` and `red_failure_excerpt` is empty (this is also enforced by the Codex hook `block-impl-without-failing-test.sh`).
- Any test edit lands outside `tasks[<task-id>].files_in_scope` (enforced by `enforce-files-in-scope.sh`).

## Done when
- Every AC listed under `tasks[<task-id>].acs_covered` has at least one `@Tag("AC-NNN")` test.
- All four phase blocks are present in `05-implementation-log.md` for this task.
- `.tdd-state.json` shows `phase: "done"` for `<task-id>`.
- Commit reminder surfaced (Step 7); user commits before starting the next task. After all tasks done, run `$test` then `$validate`.
