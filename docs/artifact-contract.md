# Contrat des artefacts `.specs/<feature-id>/`

Chaque fonctionnalité produit les fichiers suivants dans cet ordre. Le passage à
une phase exige que le fichier précédent existe et que sa checklist soit verte.

```text
.specs/
├── _onboarding.md                  # résumé de l'inspection du dépôt
├── _stack.json                     # stacks, versions et preuves détectées
├── _baseline.json                  # commandes et référence statique initiale
├── _starter-design.md              # architecture existante observée
├── _known-debt.md                  # dette prouvée et inconnues
└── <feature-id>/
    ├── 01-spec.md                  # phase 1 — responsable : spec-author
    ├── 02-spec-review.md           # phase 2 — responsable : spec-author
    ├── 03-epic-design.md           # phase 3a facultative — spring-architect
    ├── 03a-epic-roadmap.md         # phase 3a facultative — spring-architect
    ├── 03-design.md                # phase 3 — spring-architect
    ├── 04-tasks.md                 # phase 3 — spring-architect
    ├── 05-implementation-log.md    # phase 4 — agents de test et d’implémentation
    ├── 06-test-plan.md             # phase 5 — spring-test-engineer
    ├── 07-validation-report.md     # phase 6 — spring-validator
    ├── 07a-traceability.md         # phase 6 — spring-validator
    ├── 08-code-review.md           # phase 7 — spring-code-reviewer
    ├── 09-ship-plan.md             # phase 8 facultative — spring-code-reviewer
    ├── .tdd-state.json             # état utilisé par le hook TDD
    ├── jobs/                        # journaux immuables des workers Hermes
    │   └── T-001/
    │       ├── 001-red.json
    │       └── 002-green.json
    └── adr/
        └── NNN-<slug>.md           # ADR MADR référencé depuis 03-design.md
```

## Artefacts globaux d'onboarding

`/sdd-onboard` Hermes produit toujours les cinq fichiers globaux dans une seule
transaction. Ils décrivent le même SHA Git et ne modifient ni le code, ni les
tests, ni les manifests ou configurations du projet.

- `_stack.json` et `_baseline.json` ont `schema_version: 1` et le même
  `git_sha`.
- `_stack.json` conserve les modules, stacks, versions et limites de confiance
  avec des chemins relatifs.
- `_baseline.json` conserve les commandes configurées mais porte
  `heavy_gates_executed: false` et `status: not-run` : l'onboarding ne lance
  aucun gate lourd.
- `_starter-design.md` décrit uniquement les patterns observés.
- `_known-debt.md` sépare la dette prouvée des inconnues.

Les rôles Hermes spécialisés analysent en lecture seule. L'agent principal est
l'unique écrivain et passe par le garde transactionnel embarqué. Le câblage ou
l'exécution du harness appartient à `/sdd-wire-harness`, pas à l'onboarding.

## Règles de nommage

- `<feature-id>` utilise le `kebab-case`, ne dépasse pas 40 caractères et
  commence par la clé du ticket lorsqu’elle existe, par exemple
  `shop-1422-gift-card-checkout`.
- Chaque fichier numéroté conserve son préfixe à deux chiffres. Une insertion
  utilise un suffixe `a`, `b` ou `c`, comme `07a-…`.

## Modèles

Chaque artefact part du modèle correspondant sous `.codex/templates/` :

| Artefact | Modèle |
| --- | --- |
| `01-spec.md` | `spec.template.md` |
| `02-spec-review.md` | `spec-review.template.md` |
| `03-epic-design.md` | `epic-design.template.md` |
| `03a-epic-roadmap.md` | `epic-roadmap.template.md` |
| `03-design.md` | `design.template.md` |
| `04-tasks.md` | `tasks.template.md` |
| `05-implementation-log.md` | `implementation-log.template.md` |
| `06-test-plan.md` | `test-plan.template.md` |
| `07-validation-report.md` | `validation-report.template.md` |
| `07a-traceability.md` | `traceability.template.md` |
| `08-code-review.md` | `code-review.template.md` |
| `09-ship-plan.md` | `ship-plan.template.md` |
| `adr/NNN-<slug>.md` | `adr.template.md` |

## Fichier `.tdd-state.json`

`$build` maintient ce fichier d’exécution. Le hook Codex historique
`block-impl-without-failing-test` peut le lire, mais les skills Hermes doivent
appeler le garde runtime explicite : ils ne bénéficient pas des hooks Codex.

```json
{
  "schema_version": 2,
  "feature_id": "shop-1422-gift-card-checkout",
  "mode": "parallel",
  "project": "shop",
  "board": "shop",
  "max_workers": 2,
  "revision": 4,
  "active_task": null,
  "tasks": {
    "T-001": {
      "phase": "red",
      "status": "in_progress",
      "dependencies": [],
      "test_ids": ["T-001-T1"],
      "kanban_id": "card-123",
      "issue": 1423,
      "branch": "sdd/shop-1422-gift-card-checkout/t-001-api",
      "pr": 1424,
      "red_at": "2026-04-18T10:00:00Z",
      "red_test_signature": "com.example.X.shouldRejectExpiredCard",
      "red_failure_excerpt": "AssertionFailedError: expected 400 but was 200",
      "green_at": null,
      "files_in_scope": ["src/main/java/.../X.java", "src/test/java/.../XTest.java"]
    }
  }
}
```

Les valeurs des clés JSON restent en anglais car les hooks les consomment
directement.

Le schéma v2 est additif : `feature_id`, `active_task`, `tasks`, `phase` et les
preuves TDD restent aux mêmes emplacements. Un état v1 est accepté en lecture et
peut produire un candidat v2 explicite. Il n'est jamais migré silencieusement
pendant une implémentation commencée.

L'état ne contient aucun chemin absolu, transcript, token, credential ou secret.
Les tokens CAS et journaux de transaction résident dans le Git common dir, hors
des artefacts versionnés. `max_workers` vaut `1` ou `2`, et le mode `sequential`
impose `1`.

Une nouvelle modification de `src/main/**` n’est autorisée que si la phase de
la tâche active vaut `red`, que `red_at` est renseigné et que
`red_failure_excerpt` n’est pas vide.

## Écrivains parallèles et fan-in

Chaque worker possède un worktree, un lease de fichiers et un journal propre
sous `jobs/<T-ID>/`. Un événement existant peut être rejoué uniquement avec le
même identifiant et le même contenu. Le worker ne modifie jamais
`04-tasks.md`, `.tdd-state.json` ou `05-implementation-log.md`.

Le lease est lié à la session Hermes et à l'identité complète du processus
(PID et temps de naissance). Un heartbeat prolonge son TTL, borné à 45 minutes.
Un lease expiré ou dont le processus a disparu est récupéré avant une nouvelle
attribution. Le nombre de leases actifs ne dépasse jamais `max_workers`.
L'attribution exige la feature exacte, une tâche en phase `pending` avec le
statut `pending` ou `ready`, et chaque dépendance en phase et statut `done`.

Chaque événement task-local est couvert par un manifeste dans le Git common
dir. Une modification, une suppression ou un fichier non manifesté bloque la
reprise. Le fingerprint avant/après inclut les fichiers ignorés, les modes et
l'index Git, en plus du contenu du worktree.

Deux tâches ne sont prêtes dans la même vague que si leurs dépendances sont
terminées et leurs chemins concrets disjoints. Un conflit de chemin impose une
dépendance et une exécution séquentielle. Les globs, dossiers, chemins hors
dépôt et chaînes de symlinks sont refusés.

Après fusion autorisée des PR d'une vague, un synthesizer unique lit les
journaux task-local et publie les artefacts partagés. Le fan-in utilise le
verrou du Git common dir, des tokens CAS, un journal synchronisé et un marqueur
de commit lié au dépôt, au worktree et au `HEAD`. Après interruption, la reprise
restitue l'ancien ou le nouvel ensemble complet, jamais un mélange. Elle refuse
une reprise depuis un autre worktree, après un changement de `HEAD` ou avec un
marqueur altéré.

## Interdictions

- Modifier les artefacts dans le désordre.
- Sauter `02-spec-review.md`, dont l’approbation est obligatoire.
- En mode Epic, écrire `04-tasks.md` avant l’approbation de
  `03-epic-design.md` et `03a-epic-roadmap.md`.
- Commencer `04-tasks.md` tant que `03-design.md` contient un `Q-NNN`
  ouvert.
- Faire modifier `08-code-review.md` par un autre agent que
  `spring-code-reviewer`.

## Déclenchement du mode Epic

Le mode Epic est obligatoire si la fonctionnalité comporte au moins deux
tranches verticales prévues, des décisions architecturales transverses partagées
ou plusieurs jalons de livraison.

1. `03-epic-design.md` et `03a-epic-roadmap.md` doivent exister avant le
   découpage détaillé.
2. Les `Q-NNN` globaux doivent être résolus ou différés avec justification
   avant de finaliser `04-tasks.md`.
3. Les tâches détaillées sont produites progressivement depuis la roadmap.

## Références croisées

- ticket source → section `## Source` de `01-spec.md` ;
- critère → tests via `@DisplayName("AC-NNN: …")` ou `@Tag("AC-NNN")` ;
- critère → tâches via `AC-IDs` dans `04-tasks.md` ;
- tâche → tests via `Test-IDs` dans `04-tasks.md` ;
- constat → ADR via la section `Waivers` de `08-code-review.md`.
