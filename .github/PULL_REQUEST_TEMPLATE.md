## Résumé

<!-- Que change cette PR et pourquoi ? Lier les issues concernées. -->

## Type de changement

- [ ] Documentation, typo ou changement sans effet fonctionnel
- [ ] Nouveau skill, modèle ou agent
- [ ] Modification d'un skill, modèle ou agent existant
- [ ] Modification d'un hook ou du harness
- [ ] Modification du fragment POM parent Maven
- [ ] Modification de la méthodologie, des phases, contrats de sortie ou artefacts
- [ ] CI ou hygiène du dépôt

## Structure Codex

Si ce changement touche un skill, le conserver dans un dossier distinct sous
`.agents/skills/`. Ne pas le fusionner avec un autre skill ni créer de copies par plateforme.

- [ ] Le skill reste isolé dans `.agents/skills/<name>/`
- [ ] Les références d'agents ou hooks utilisent `.codex/`
- [ ] N/A, documentation, CI ou exemple uniquement

## Contrôles

- [ ] `shellcheck` réussit : `shellcheck -S style .github/scripts/*.sh .codex/hooks/*.sh`
- [ ] Markdown lint réussit : `npx markdownlint-cli2 "**/*.md"`
- [ ] `.codex/hooks.json` est un JSON valide
- [ ] [CHANGELOG.md](../CHANGELOG.md) est mis à jour sous `## [Unreleased]`
- [ ] Si la méthodologie change : [docs/methodology.md](../docs/methodology.md) est mis à jour
- [ ] Si le contrat des artefacts change : [docs/artifact-contract.md](../docs/artifact-contract.md) est mis à jour

## Changement cassant ?

<!-- Un changement est cassant s'il modifie le contrat de sortie d'une phase, le schéma requis d'un artefact ou le comportement d'un hook. -->

- [ ] Oui — décrire la migration :
- [ ] Non
