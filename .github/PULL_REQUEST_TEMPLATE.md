## Summary

<!-- What does this PR change and why? Link any related issues. -->

## Type of change

- [ ] Docs / typo / non-behavioral
- [ ] New skill / template / agent
- [ ] Change to an existing skill / template / agent
- [ ] Hook or harness script change
- [ ] Maven parent-pom fragment change
- [ ] Methodology change (phases, exit contracts, artifacts)
- [ ] CI / repo hygiene

## Codex structure

If this change touches a skill, keep it in one distinct directory under
`.agents/skills/`. Do not merge it with another skill or create platform copies.

- [ ] Skill remains isolated in `.agents/skills/<name>/`
- [ ] Agent or hook references use `.codex/`
- [ ] N/A (docs/CI/example only)

## Checks

- [ ] `shellcheck` clean (`shellcheck -S style .github/scripts/*.sh .codex/hooks/*.sh`)
- [ ] Markdown lints (`npx markdownlint-cli2 "**/*.md"`)
- [ ] `.codex/hooks.json` parses as JSON
- [ ] [CHANGELOG.md](../CHANGELOG.md) updated under `## [Unreleased]`
- [ ] If methodology changed: [docs/methodology.md](../docs/methodology.md) updated
- [ ] If artifact contract changed: [docs/artifact-contract.md](../docs/artifact-contract.md) updated

## Breaking change?

<!-- A change is breaking if it modifies a phase exit contract, an artifact's required schema, or hook enforcement semantics. See CONTRIBUTING.md#versioning. -->

- [ ] Yes — describe migration:
- [ ] No
