# ADR-005 : Migrer l'état par double lecture et écriture v2 compatible v1

- **Statut :** accepted
- **Date :** 2026-07-31
- **Décideurs :** utilisateur, `spring-architect`
- **Consultés :** —
- **Informés :** mainteneurs du runtime, du profil et exploitation VPS

## Context and problem statement

Le runtime parallèle requiert un schéma v2 plus riche, alors que le profil 0.4.7
et les états v1 existants doivent rester exploitables pendant les publications
progressives. Une bascule destructive rendrait le rollback du profil
impossible ou imposerait une conversion inverse risquée.

## Decision drivers

- Reprise des features commencées avec un état v1.
- Retour au profil précédent sans perte ni réécriture destructive.
- Une seule version d'écriture active pour éviter la divergence.

## Considered options

1. Bascule immédiate v2 avec migration destructive de tous les états.
2. Double écriture v1 et v2 pendant la transition.
3. Lecture v1/v2, écriture v2 compatible avec le contrat de lecture v1 et
   rollback par réinstallation du profil précédent.

## Decision outcome

Option retenue : **double lecture v1/v2 et écriture v2 compatible v1**, car la
réponse utilisateur `Q-007` préserve la reprise et réduit le rollback à la
version du profil, sans conversion inverse de données.

### Consequences

- Positives : migration progressive, états antérieurs lisibles, rollback simple
  du code et absence de double écriture divergente.
- Négatives / compromis : le schéma v2 reste contraint par le contrat v1 tant
  que la possibilité de rollback est requise ; les deux parseurs doivent être
  testés.

## Pros and cons of the options

### Option 1 — Bascule destructive

- Avantage : schéma v2 libre de toute compatibilité.
- Inconvénient : rollback complexe et risque de perdre les états existants.

### Option 2 — Double écriture

- Avantage : chaque profil lit son format natif.
- Inconvénient : divergence possible entre deux représentations après un crash.

### Option 3 — Double lecture, écriture v2 compatible

- Avantage : une seule source écrite et rollback du profil sans migration de
  données.
- Inconvénient : compatibilité descendante à maintenir et à tester.

## Links

- Conception : [Contrats d'état et modèle conceptuel](../03-epic-design.md#contrats-détat-et-modèle-conceptuel)
- Source : `01-spec.md`, AC-048 à AC-060, AC-276 à AC-279 et réponse `Q-007`
- ADR liés : [ADR-004](004-use-single-writer-fan-in.md)
- Remplace : —
