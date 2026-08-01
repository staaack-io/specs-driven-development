# ADR-001 : Utiliser Hermes Kanban comme ordonnanceur durable

- **Statut :** accepted
- **Date :** 2026-07-31
- **Décideurs :** utilisateur, `spring-architect`
- **Consultés :** —
- **Informés :** mainteneurs SDD et profil Hermes

## Context and problem statement

L'exécution parallèle a besoin d'un état durable, d'une admission contrôlée et
d'une reprise des jobs. Hermes 0.19 fournit déjà un Kanban natif ; ajouter un
ordonnanceur Python créerait deux autorités concurrentes.

## Decision drivers

- Une seule source de vérité durable pour l'état des jobs.
- Reprise, idempotence et diagnostics déjà attachés aux cartes Hermes.
- Interdiction explicite de développer un second ordonnanceur Python.

## Considered options

1. Utiliser exclusivement le Kanban natif Hermes 0.19.
2. Développer un ordonnanceur Python propre au framework SDD.
3. Partager l'ordonnancement entre Hermes et un service Python.

## Decision outcome

Option retenue : **utiliser exclusivement le Kanban natif Hermes 0.19**, car la
décision `Q-001` fournit une autorité durable unique et évite la synchronisation
de deux ordonnanceurs.

### Consequences

- Positives : état durable réutilisé, reprise centralisée, moins de code
  d'infrastructure et cartes visibles par `/sdd-status`.
- Négatives / compromis : l'orchestration dépend du contrat Kanban Hermes 0.19
  et chaque script doit cibler explicitement le bon board et le bon projet.

## Pros and cons of the options

### Option 1 — Kanban Hermes

- Avantage : une seule autorité et primitives de dispatch/reprise existantes.
- Inconvénient : couplage explicite à Hermes 0.19.

### Option 2 — Ordonnanceur Python SDD

- Avantage : contrôle total du modèle interne.
- Inconvénient : second état durable, davantage de code et divergence possible.

### Option 3 — Ordonnancement partagé

- Avantage : adaptation progressive possible.
- Inconvénient : responsabilité ambiguë et réconciliation complexe après crash.

## Links

- Conception : [Architecture Boundaries](../03-epic-design.md#architecture-boundaries)
- Source : `01-spec.md`, AC-001 à AC-003 et réponse `Q-001`
- ADR liés : [ADR-002](002-bound-parallel-capacity.md),
  [ADR-003](003-isolate-each-job.md)
- Remplace : —
