# ADR-004 : Consolider les artefacts partagés par un fan-in à écrivain unique

- **Statut :** accepted
- **Date :** 2026-07-31
- **Décideurs :** utilisateur, `spring-architect`
- **Consultés :** —
- **Informés :** mainteneurs SDD et auteurs des commandes de build

## Context and problem statement

Les jobs parallèles doivent conserver les preuves TDD sans écrire
concurremment `.tdd-state.json`, `05-implementation-log.md` ou les rapports
communs. Un simple verrou autour de chaque worker protégerait les octets, mais
pas l'observation d'un ensemble complet ni la reprise d'une vague interrompue.

## Decision drivers

- Atomicité de l'ensemble des artefacts partagés.
- Historique rejouable et idempotent par tâche.
- Absence de mélange entre versions anciennes et nouvelles après crash.

## Considered options

1. Chaque worker écrit directement les artefacts communs.
2. Chaque worker écrit les artefacts communs sous verrou et CAS.
3. Chaque worker écrit un journal local immuable ; un synthesizer unique réalise
   le fan-in transactionnel.

## Decision outcome

Option retenue : **journaux locaux puis fan-in transactionnel par un synthesizer
unique**, car cette organisation protège l'ensemble cohérent et fournit la
source de reprise sans autoriser les workers à modifier l'état partagé.

### Consequences

- Positives : atomicité, idempotence, audit par tâche et absence de conflit sur
  les artefacts partagés.
- Négatives / compromis : la vague suivante attend la fusion de la PR de fan-in
  et le synthesizer devient un point de sérialisation volontaire.

## Pros and cons of the options

### Option 1 — Écritures directes

- Avantage : progression immédiate de l'état commun.
- Inconvénient : collisions et ensembles partiels possibles.

### Option 2 — Verrou et CAS par worker

- Avantage : empêche l'écrasement concurrent d'un fichier.
- Inconvénient : ne garantit pas seul une transaction multi-artefacts ni une
  consolidation ordonnée de toute la vague.

### Option 3 — Journal local et fan-in

- Avantage : une seule transaction consolidée à partir de sources immuables.
- Inconvénient : barrière de fan-in sur le chemin critique.

## Links

- Conception : [Contrats d'état et modèle conceptuel](../03-epic-design.md#contrats-détat-et-modèle-conceptuel)
- Source : `01-spec.md`, AC-041 à AC-047, AC-068 à AC-079 et AC-214 à AC-217
- ADR liés : [ADR-002](002-bound-parallel-capacity.md),
  [ADR-003](003-isolate-each-job.md),
  [ADR-005](005-migrate-state-with-dual-read.md)
- Remplace : —
