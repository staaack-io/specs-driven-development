# Contrat des artefacts `.specs/<feature-id>/`

Chaque fonctionnalité produit les fichiers suivants dans cet ordre. Le passage à
une phase exige que le fichier précédent existe et que sa checklist soit verte.

```text
.specs/
├── _baseline.json                  # référence des échecs brownfield du dépôt
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
    └── adr/
        └── NNN-<slug>.md           # ADR MADR référencé depuis 03-design.md
```

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

`$build` maintient ce fichier d’exécution. Le hook
`block-impl-without-failing-test` le lit avant une édition de production.

```json
{
  "feature_id": "shop-1422-gift-card-checkout",
  "active_task": "T-001",
  "tasks": {
    "T-001": {
      "phase": "red | green | refactor | simplify | done",
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

Une nouvelle modification de `src/main/**` n’est autorisée que si la phase de
la tâche active vaut `red`, que `red_at` est renseigné et que
`red_failure_excerpt` n’est pas vide.

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
