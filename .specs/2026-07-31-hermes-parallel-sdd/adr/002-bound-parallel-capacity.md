# ADR-002 : Borner séparément writers, analyses et gates lourdes

- **Statut :** accepted
- **Date :** 2026-07-31
- **Décideurs :** utilisateur, `spring-architect`
- **Consultés :** —
- **Informés :** mainteneurs SDD et exploitation VPS

## Context and problem statement

Le VPS doit exécuter des tâches réellement en parallèle sans épuisement mémoire
ni contention incontrôlée. Les écritures, analyses en lecture seule et gates
lourdes n'ont pas le même profil de risque et ne peuvent partager une limite
silencieuse.

## Decision drivers

- Capacité VPS approuvée par l'utilisateur.
- Prévention des conflits d'écriture et de l'OOM.
- Conservation d'un parallélisme observable pour les tâches indépendantes.

## Considered options

1. Parallélisme non borné piloté par les tâches prêtes.
2. Limite unique identique pour tout type de travail.
3. Plafonds séparés : deux writers, trois analyses et une gate lourde.

## Decision outcome

Option retenue : **deux writers, trois analyses en lecture seule et une gate
lourde**, car ces plafonds correspondent aux décisions `Q-003` et `Q-004` et à
la capacité d'exploitation spécifiée.

### Consequences

- Positives : consommation prévisible, vrai chevauchement de deux tâches et
  absence de concurrence entre gates Maven, Next, PIT ou OWASP.
- Négatives / compromis : une troisième écriture et toute seconde gate lourde
  attendent, même si leur dépendance fonctionnelle est satisfaite.

## Pros and cons of the options

### Option 1 — Non borné

- Avantage : débit potentiel maximal sur une machine surdimensionnée.
- Inconvénient : OOM et contention non maîtrisés sur le VPS cible.

### Option 2 — Limite unique

- Avantage : configuration simple.
- Inconvénient : gaspille les analyses légères ou laisse se chevaucher des gates
  trop lourdes selon la valeur choisie.

### Option 3 — Plafonds séparés

- Avantage : capacité ajustée au type de charge et vérifiable indépendamment.
- Inconvénient : admission et métriques doivent distinguer les trois catégories.

## Links

- Conception : [Cross-cutting Constraints](../03-epic-design.md#cross-cutting-constraints)
- Source : `01-spec.md`, AC-004 à AC-006, AC-080, AC-170 à AC-177,
  réponses `Q-003` et `Q-004`
- ADR liés : [ADR-001](001-use-hermes-kanban.md),
  [ADR-004](004-use-single-writer-fan-in.md)
- Remplace : —
