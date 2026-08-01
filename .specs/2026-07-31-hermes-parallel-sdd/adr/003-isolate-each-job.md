# ADR-003 : Isoler et suivre chaque job de bout en bout

- **Statut :** accepted
- **Date :** 2026-07-31
- **Décideurs :** utilisateur, `spring-architect`
- **Consultés :** —
- **Informés :** mainteneurs SDD et exploitation VPS

## Context and problem statement

Deux tâches indépendantes doivent progresser simultanément sans partager leur
espace d'écriture ni leur cycle de review. Une isolation limitée à Git ne suffit
pas à relier durablement l'exécution Hermes, le suivi GitHub et les preuves TDD.

## Decision drivers

- Traçabilité d'une tâche depuis son admission jusqu'à son go humain.
- Reprise et diagnostic d'un seul job sans perdre l'autre.
- Interdiction d'auto-merge et conservation d'une review indépendante.

## Considered options

1. Branche partagée et une seule PR par vague.
2. Branche/worktree par tâche, avec suivi Hermes et GitHub partagé.
3. Carte, issue, branche, worktree, session, journal et PR propres à chaque job.

## Decision outcome

Option retenue : **une enveloppe complète propre à chaque job**, car elle rend
les conflits, preuves, checks, reviews et reprises observables à la granularité
de la tâche tout en conservant une validation humaine avant fusion.

### Consequences

- Positives : isolation forte, diagnostic ciblé, PR indépendantes et
  conservation du travail d'un job quand un autre échoue.
- Négatives / compromis : davantage de ressources et de liens croisés à créer,
  stocker, surveiller puis nettoyer avec prudence.

## Pros and cons of the options

### Option 1 — Branche et PR de vague

- Avantage : faible nombre d'objets GitHub.
- Inconvénient : collisions, review couplée et rollback impossible par tâche.

### Option 2 — Isolation Git seulement

- Avantage : fichiers séparés avec moins d'objets de suivi.
- Inconvénient : état Hermes/GitHub ambigu et reprise moins traçable.

### Option 3 — Enveloppe complète

- Avantage : correspondance univoque entre tâche, exécution, preuve et review.
- Inconvénient : cycle de vie et nettoyage plus élaborés.

## Links

- Conception : [Modèle d'interaction](../03-epic-design.md#modèle-dinteraction)
- Source : `01-spec.md`, AC-027 à AC-047, AC-110 à AC-120, AC-236 et
  réponse `Q-002`
- ADR liés : [ADR-001](001-use-hermes-kanban.md),
  [ADR-004](004-use-single-writer-fan-in.md)
- Remplace : —
