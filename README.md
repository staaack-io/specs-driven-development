# Spec-Driven Development for Spring Boot 4 + Angular

A Codex toolkit that drives **Spring Framework 7 / Spring Boot 4** and
**Angular** full-stack development through a documented, self-validating
workflow:

> **specify → review → plan → implement (TDD) → test → validate → review → commit**

The agent validates its own work via a layered harness (build, static analysis, architecture, tests, coverage, mutation, contract, security) instead of relying on a human to inspect every line.

```mermaid
flowchart LR
    A["$spec"] --> B["$spec-review"]
    B --> C["$plan"]
    C --> D["$build T-NNN"]
    D --> E["$test"]
    E --> F["$validate"]
    F --> G["$review"]
    G --> H["git commit"]
    H --> I["$ship"]
```

## Why

- **No invention.** During specify/review/plan/tasks, the agent never guesses; every uncertainty becomes a tracked open question that you answer before progress continues.
- **TDD by construction.** Production code can only be written *after* a failing test exists. Hooks enforce it.
- **Traceable.** Every acceptance criterion (`AC-NNN`) maps to tests, code, and the harness gates that exercised it.
- **Self-validating.** A single `.github/scripts/harness.sh` runs locally and in CI; the agent reads its reports and writes a structured validation report.
- **Pre-commit code review** by an agent that uses a Spring-specific rubric.
- **Codex-native.** Instructions, skills, agents, and hooks use Codex project
  conventions without duplicated platform copies.

## Install

This toolkit is a **set of files you drop into your repo**, not a package you `npm install` or `mvn install`. Pick the path that matches your situation.

### Prerequisites

- **Backend:** Java 25 + Maven 3.9+ (for the Spring harness to run).
- **Frontend:** Node.js 22+ and Angular CLI 20+ (for the Angular harness — lint, typecheck, unit tests, build, e2e).
- [Codex](https://developers.openai.com/codex/) installed and authenticated.
- `bash`, `git`, `jq` on your `PATH` (the harness scripts use them).

For backend-only projects, Angular tooling is not required (and vice versa).

### Option A — Start a new project from this toolkit

```bash
# 1. Clone (or use as a template)
git clone https://github.com/loiane/specs-driven-development-spring-angular.git my-service
cd my-service
rm -rf .git && git init

# 2. Drop in your own Spring Boot 4 application code under src/
#    Merge .codex/maven/parent-pom-fragment.xml into your pom.xml
#    (it pins the 10-layer harness: Surefire, Failsafe, JaCoCo, PIT, Checkstyle,
#    SpotBugs, ArchUnit deps, OWASP dep-check, OpenAPI generator).

# 3. Make the scripts and hooks executable
chmod +x .github/scripts/*.sh .codex/hooks/*.sh

# 4. Verify the harness wires up
./.github/scripts/harness.sh --report     # runs the harness and emits a JSON summary
```

### Option B — Add the toolkit to an existing Spring repo

```bash
# From the root of your existing repo:
git clone --depth=1 https://github.com/loiane/specs-driven-development-spring-angular.git /tmp/sdd

# Copy the Codex workflow and its documentation:
cp /tmp/sdd/AGENTS.md .
cp -r /tmp/sdd/.agents /tmp/sdd/.codex /tmp/sdd/docs /tmp/sdd/examples .
mkdir -p .github
cp -r /tmp/sdd/.github/scripts .github/

chmod +x .github/scripts/*.sh .codex/hooks/*.sh

# Then merge .codex/maven/parent-pom-fragment.xml into your pom.xml.
# Then run the brownfield onboarding skill from Codex (see Use below).
```

> **Note on `.github/`** — only `.github/scripts/` belongs to the framework's
> runtime harness. Merge that directory with your existing GitHub configuration;
> the framework does not install a workflow or a Copilot configuration.

### Verify Codex wiring

1. Open the repository as a trusted Codex project.
2. Run `/skills` and confirm the repo skills are listed separately.
3. Run `/hooks`, review the project hook commands, and trust them.
4. Invoke `$help` to display the framework workflow.

## Use

Once installed, drive the workflow from Codex with repository skills. Explicit
skill invocation uses `$skill-name`; Codex may also select a skill from a clear
natural-language request.

### Day-zero (brownfield only)

```text
$onboard
$wire-harness
```

Classifies the repo, captures a baseline harness run, writes
`.specs/_onboarding.md` and `.specs/_known-debt.md`, and adds any missing harness
layers as ratchets (so existing failures don't block you, but no new ones can
land). See [examples/brownfield/README.md](examples/brownfield/README.md).

### Per-feature loop

```text
$spec "Add gift-card checkout"      # or: $spec JIRA-123
$spec-review                        # gate exit from Phase 1
$epic-plan                          # for Epics: high-level design + slice roadmap
$plan                               # design + tasks + .tdd-state.json
$build T-001                        # red → green → refactor → simplify (one task at a time)
$test --gap                         # close coverage / mutation gaps
$validate                           # full 10-layer harness + traceability
$review                             # pre-commit code review against the Spring rubric
git commit                          # YOU run this — the agent never commits
$ship                               # post-commit ship plan + release notes (never deploys)
```

Repeat `$build T-NNN` for each task in `04-tasks.md`. The agent refuses to edit
`src/main/**` unless `.specs/<feature-id>/.tdd-state.json` shows a failing test
for the active task.

For Epic-sized initiatives, run `$epic-plan` after `$spec-review`, then run `$plan`
to produce slice-level detailed design and tasks from the approved roadmap.

### Read-only helpers

- `$status` — see where each feature sits in the pipeline.
- `$help [workflow]` — print the framework catalog or a single workflow spec.

### Natural-language aliases

You don't have to remember every skill name. The skill descriptions let Codex
route clear natural-language requests to the matching workflow:

| You type | Runs |
| --- | --- |
| "spec this" / "turn this ticket into requirements" | `$spec` |
| "review the spec" | `$spec-review` |
| "plan this epic" / "design this epic" / "slice this epic" | `$epic-plan` |
| "plan this" / "design this" | `$plan` |
| "implement T-003" / "build T-003" | `$build T-003` |
| "validate" / "run the harness" | `$validate` |
| "review the code" / "pre-commit review" | `$review` |
| "simplify the code" / "remove the cleverness" | `$code-simplify` |
| "ship it" / "release this" / "prepare release" | `$ship` |
| "onboard this repo" | `$onboard` |

Full list: [.agents/skills/](.agents/skills/).

### Running the harness directly

The same gates the agent runs are reachable from a normal terminal:

```bash
./.github/scripts/harness.sh                 # all 10 layers
./.github/scripts/harness.sh --report        # emit harness-summary.json
./.github/scripts/check-new-code-coverage.sh # diff-coverage gate against main
./.github/scripts/traceability.sh <feature-id>
```

## Repository layout

```text
AGENTS.md         persistent Codex project instructions
.agents/skills/   one directory per domain or workflow skill
.codex/           agents · hooks · templates · checklists · maven
.github/scripts/  deterministic harness scripts (not Copilot configuration)
docs/             methodology · harness · spec format · Codex migration · artifact contract
examples/         greenfield (worked end-to-end specs) · brownfield (onboarding report)
```

There is one source of truth for every skill. Workflow skills reference domain
skills by name and never merge their instructions.

## Workflow artifacts

Each feature lives under `.specs/<feature-id>/`:

| File | Phase | Owner |
| --- | --- | --- |
| `01-spec.md` | Specify | `spec-author` |
| `02-spec-review.md` | Review specs | `spec-author` |
| `03-epic-design.md` | Plan (Epic mode) | `spring-architect` / `angular-architect` |
| `03a-epic-roadmap.md` | Plan (Epic mode) | `spring-architect` / `angular-architect` |
| `03-design.md` | Plan | `spring-architect` / `angular-architect` |
| `04-tasks.md` | Plan | `spring-architect` / `angular-architect` |
| `05-implementation-log.md` | Implement (TDD) | `spring-implementer` + `spring-test-engineer` / `angular-implementer` + `angular-test-engineer` |
| `06-test-plan.md` | Test | `spring-test-engineer` / `angular-test-engineer` |
| `07-validation-report.md` | Validate | `spring-validator` / `angular-validator` |
| `07a-traceability.md` | Validate | `spring-validator` / `angular-validator` |
| `08-code-review.md` | Code review | `spring-code-reviewer` / `angular-code-reviewer` |

### Stack routing

Each workflow skill defaults to the Spring agent but delegates to the Angular
counterpart based on feature scope:

- **Backend-only** → Spring agents
- **Frontend-only** → Angular agents
- **Full-stack** → both agents collaborate, splitting tasks by stack

The routing contract is documented in each workflow skill's `## Stack routing`
section. See [.agents/skills/plan/SKILL.md](.agents/skills/plan/SKILL.md) for an
example.

## Documentation

- [docs/README.md](docs/README.md) — vue d'ensemble du framework en français et premier parcours
- [docs/methodology.md](docs/methodology.md) — the 7-phase workflow in detail
- [docs/harness-principles.md](docs/harness-principles.md) — self-validation philosophy and gate layers
- [docs/spec-format.md](docs/spec-format.md) — EARS-lite spec format with examples
- [docs/codex-migration.md](docs/codex-migration.md) — verified Claude-to-Codex migration mapping
- [docs/artifact-contract.md](docs/artifact-contract.md) — `.specs/<id>/` file layout and `.tdd-state.json` schema
- [examples/greenfield/README.md](examples/greenfield/README.md) — full worked feature
- [examples/brownfield/README.md](examples/brownfield/README.md) — onboarding-only walkthrough

## Stack assumptions

### Backend (Spring)

- Java 25, Spring Framework 7, Spring Boot 4
- Maven (Gradle support deferred)
- REST APIs with OpenAPI
- Module boundaries enforced via ArchUnit rules (no extra runtime dependency)
- DB engine + migration tool (Flyway/Liquibase) auto-detected from `pom.xml`
- Testcontainers integration tests are mandatory when Testcontainers is detected

### Frontend (Angular)

- Angular 20+ with standalone components
- TypeScript strict mode
- Route-level code splitting
- Accessible components (ARIA, keyboard reachability)
- Unit tests (Karma/Jest) + e2e tests (Cypress/Playwright)
- Typed API clients (no untyped HTTP response handling)

## License

MIT — see [LICENSE](LICENSE).
