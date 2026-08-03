# Migration de Claude Code vers Codex

Cette migration suit le parcours officiel
[Import from another agent](https://learn.chatgpt.com/docs/import) et les
formats projet documentés pour
[AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md),
[les skills](https://learn.chatgpt.com/docs/build-skills),
[les agents](https://learn.chatgpt.com/docs/agent-configuration/subagents) et
[les hooks](https://learn.chatgpt.com/docs/hooks).

## Correspondance retenue

| Élément Claude | Élément Codex | Décision dans ce dépôt |
| --- | --- | --- |
| Instructions persistantes | `AGENTS.md` | Un fichier racine porte les invariants du workflow |
| `.claude/skills/<nom>/SKILL.md` | `.agents/skills/<nom>/SKILL.md` | Chaque skill reste dans son propre dossier |
| `.claude/commands/<nom>.md` | Skill Codex | Chaque workflow devient un skill distinct, invoqué avec `$<nom>` |
| `.claude/agents/<nom>.md` | `.codex/agents/<nom>.toml` | Un fichier TOML par agent |
| Hooks de `settings.json` | `.codex/hooks.json` | Les scripts sont adaptés au protocole d'outil Codex |
| Paramètres compatibles | `.codex/config.toml` | Aucun paramètre n'est ajouté sans besoin établi |
| Serveurs MCP | Configuration MCP Codex | À configurer et authentifier dans l'environnement utilisateur |

Les custom prompts Codex sont dépréciés. Les anciens slash commands ne sont
donc pas copiés dans un dossier de prompts : l'import officiel les dirige vers
des skills. Les workflows de ce dépôt s'utilisent avec `$spec`, `$plan`,
`$build`, etc. Les commandes natives telles que `/plan`, `/status` et `/review`
restent celles de Codex et ne sont pas remplacées.

## Skills : aucune fusion

Codex découvre les skills partagés d'un dépôt sous `.agents/skills`. Le dossier
contient ici :

- les skills métier d'origine, copiés individuellement ;
- un skill distinct par ancien workflow (`spec`, `plan`, `build`, etc.).

Les instructions d'un skill ne sont pas recopiées dans un autre. Un workflow
énumère les skills qu'il utilise et Codex charge chacun séparément. Cette
structure évite un gros skill généraliste et conserve des déclencheurs ciblés.

## Agents : conversion sans modèle inventé

Un agent Codex projet est un fichier TOML sous `.codex/agents/` avec trois
champs obligatoires :

```toml
name = "spring-validator"
description = "Phase 6 — valider l'implémentation et ses preuves."
developer_instructions = """
Instructions propres au rôle.
"""
```

Les valeurs Claude comme `sonnet` ne sont pas traduites en un nom de modèle
OpenAI supposé équivalent. Sans champ `model`, l'agent hérite du modèle et de
l'effort de raisonnement de la session Codex, conformément au comportement
documenté.

## Hooks : différence importante du protocole

Codex peut faire passer les modifications de fichiers par `apply_patch`. Dans
ce cas, le hook reçoit le patch dans `tool_input.command`, et non un unique
`tool_input.file_path`. Les hooks de ce dépôt extraient donc toutes les lignes
`Add File`, `Update File`, `Delete File` et `Move to` avant d'appliquer les
contrôles TDD et `files_in_scope`.

Les hooks projet ne s'exécutent que pour un dépôt approuvé comme fiable. Après
un clone ou une modification de hook, ouvrez `/hooks` dans Codex, examinez les
commandes et approuvez-les avant de compter sur leur protection.

Hermes n'exécute pas ces hooks Codex. Les skills Hermes d'écriture utilisent le
garde déterministe sous `hermes/runtime/` pour vérifier explicitement questions
ouvertes, preuve RED, arguments interdits, chemins, symlinks, fingerprints et
transitions transactionnelles. Un prompt ou un hook absent n'est jamais traité
comme une preuve de conformité.

## Assets internes

Codex impose les emplacements de `AGENTS.md`, des skills, des agents et des
hooks. Il n'impose pas d'emplacement particulier pour les modèles Markdown, les
checklists ou le fragment Maven. Ce framework les place sous :

```text
.codex/templates/
.codex/checklists/
.codex/maven/
```

Il s'agit d'une convention locale référencée explicitement par les skills, pas
d'une capacité de découverte automatique attribuée à Codex.

## Import automatique ou migration versionnée

Pour une configuration personnelle existante, l'application permet
**Settings > Import** et le CLI expose `/import`. L'import laisse la
configuration Claude intacte et signale les connexions ou hooks à vérifier.

Pour ce framework partagé, les fichiers sont migrés et versionnés directement
dans Git. Cela garantit que tous les membres de l'équipe utilisent les mêmes
instructions et permet de supprimer les copies Claude, Copilot et Windsurf du
dépôt.

## Vérifications après migration

1. Ouvrir le projet comme dépôt fiable dans Codex.
2. Utiliser `/hooks` pour examiner et approuver les hooks projet.
3. Utiliser `/skills` et vérifier que chaque dossier apparaît séparément.
4. Demander à Codex de résumer les instructions chargées depuis `AGENTS.md`.
5. Invoquer `$help`, puis effectuer un essai sans écriture avec `$status`.
6. Tester qu'un patch `src/main/**` sans état TDD rouge est refusé.
7. Exécuter le harness du projet consommateur avant la première fonctionnalité.

## Correspondance Codex vers Hermes

La migration Hermes conserve les étapes utilisateur, avec un préfixe explicite
`/sdd-` pour ne pas les confondre avec les commandes natives :

| Codex | Hermes | État |
| --- | --- | --- |
| `$onboard` | `/sdd-onboard` | converti |
| `$spec` | `/sdd-spec` | converti |
| `$spec-review` | `/sdd-spec-review` | converti |
| `$plan` | `/sdd-plan` | converti |
| `$status` | `/sdd-status` | converti |
| `$help` | `/sdd-help` | converti |
| `$wire-harness` | `/sdd-wire-harness` | converti |
| `$epic-plan` | `/sdd-epic-plan` | converti |
| `$build` | `/sdd-build` | converti |
| `$code-simplify` | `/sdd-code-simplify` | converti |
| `$test` | `/sdd-test` | converti |
| `$validate` | `/sdd-validate` | converti |
| `$review` | `/sdd-review` | feuille de route |
| `$ship` | `/sdd-ship` | feuille de route |

Les fichiers TOML Codex ne sont pas copiés tels quels dans Hermes. Chaque rôle
nécessaire devient une référence autonome embarquée dans le skill orchestrateur.
Hermes transmet cette fiche à `delegate_task`. Le sous-agent spécialisé
retourne son analyse ; il ne devient pas une commande utilisateur et ne doit pas
écrire les artefacts partagés.

`/sdd-build <feature-id> <T-NNN>` conserve le cycle
RED→GREEN→REFACTOR→SIMPLIFY. Sa forme `--parallel` confie l'admission à Hermes
Kanban, limite les writers à deux et isole chaque job. Le runtime ne fusionne
aucune PR : il observe le go explicite et les fusions réalisées ailleurs avant
le fan-in transactionnel. `/sdd-code-simplify <path> [--dry-run]` conserve
ensuite une baseline verte et restaure seulement le fichier dont la
simplification régresse.

`/sdd-test <feature-id> [--gap]` écrit uniquement les tests et
`06-test-plan.md`. `/sdd-validate [<feature-id>]` attend le harness et les
tâches terminées, sérialise les gates lourdes, puis un fan-in unique écrit les
rapports de validation et de traçabilité avec un résultat `PASS` ou `FAIL`.

Pour `/sdd-onboard`, les rôles `spring-onboarding` et
`react-nextjs-onboarding` sont des lecteurs parallélisables. L'agent principal
reste le seul écrivain et publie les cinq fichiers globaux avec un verrou, un
journal, un marqueur de commit et un token de comparaison-et-échange.
