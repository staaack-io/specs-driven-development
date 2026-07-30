---
name: performance-optimization
description: Travail de performance Spring Boot 4 et JVM, en mesurant avant de corriger. Couvre profilage, Micrometer, antipatterns Spring, cache, GC et SLO. Utiliser avec `$plan` pour les risques et `$review` pour les régressions.
when_to_use:
  - Phase 3, Plan — chemin critique, nouvelle requête, appel externe ou SLO déclaré.
  - Phase 4, Build — tâche explicitement consacrée à la performance.
  - Phase 7, Review — repérer N+1, résultats non bornés, pinning ou absence de pagination.
  - À la demande — question sur la lenteur ou le réglage du pool.
authoritative_references:
  - https://docs.spring.io/spring-boot/reference/index.html
  - https://docs.oracle.com/en/java/javase/25/
  - .agents/skills/spring-boot-4-conventions/SKILL.md
  - .agents/skills/spring-code-review-rubric/SKILL.md
---

# Optimisation des performances Spring Boot 4 et JVM

## Règle zéro : mesurer d'abord

> Aucune optimisation sans profil ou benchmark. « Cela semble lent » est une hypothèse, pas un constat.

Une PR `perf` sans profil, résultat JMH, flame graph ou mesure avant/après doit
recevoir `request-changes`. Référencer la preuve dans la PR et dans
`05-implementation-log.md`.

Preuves acceptables : flame graph async-profiler, enregistrement JFR, résultat
JMH JSON, histogrammes Micrometer p50/p95/p99 ou `EXPLAIN ANALYZE` de la requête.

## Le SLO avant l'optimisation

Toute affirmation de performance est reliée à un objectif de niveau de service.
Sans SLO, créer une `Q-NNN` et s'arrêter. Ne jamais inventer les valeurs :

```text
Endpoint:        <method> <path>
Latence p50:     ___ ms   (actuelle : ___ ms)
Latence p95:     ___ ms   (actuelle : ___ ms)
Latence p99:     ___ ms   (actuelle : ___ ms)
Débit:           ___ rps  (actuel : ___ rps)
Budget d'erreur: ___ %    (fenêtre : ___)
Mesure:          <métrique Micrometer + tableau de bord>
```

## Outils

| Outil | Usage | Notes |
|---|---|---|
| async-profiler | flame graphs CPU et allocations | `-e cpu` ou `-e alloc` |
| JFR + Mission Control | profil, allocations, GC et verrous | faible surcoût |
| JMH | microbenchmarks | au moins 2 forks, 5 warmups et 5 mesures |
| Micrometer + Actuator | latence, débit et erreurs | `Timer` avec histogramme, jamais `Counter` pour une durée |
| `EXPLAIN ANALYZE` | plan SQL réel | inclure lignes, buffers et temps |
| `-Djdk.tracePinnedThreads=full` | pinning des threads virtuels | profils de test |
| `-Xlog:gc*` ou JFR | pauses GC | examiner p99, pas la moyenne |

## Anti-patterns à rechercher

### Accès aux données

- **N+1** : navigation d'entité dans une boucle ; utiliser `JOIN FETCH`, entity graph ou projection.
- **Liste non bornée** : tout endpoint `List<T>` doit être paginé.
- **Transaction longue** autour d'un appel HTTP : déplacer l'E/S hors transaction.
- **Chargement EAGER** par défaut : utiliser LAZY et charger explicitement.
- **Requête dérivée de plus de trois prédicats** : préférer `@Query`.
- **Lecture en flux sans fetch size** : configurer la taille, itérer puis fermer.

### Pool HikariCP

Point de départ mesuré :

```text
connections = (core_count * 2) + effective_spindle_count
```

Sur SSD cloud, commencer souvent à `(cores * 2) + 1`, puis vérifier les métriques
Actuator `active`, `pending` et `usage`. Ne jamais modifier `maximumPoolSize` sans mesure.

### Threads virtuels

- Éviter `synchronized` autour d'une E/S, qui épingle le carrier ; utiliser `ReentrantLock` si nécessaire.
- Éviter les grands `ThreadLocal` ; préférer `ScopedValue` ou un pool explicite.
- Ne pas introduire d'`Executor` personnalisé sur threads plateforme sans ADR et mesure.

### Cache

- Mettre en cache le résultat avec une clé fondée sur ses entrées réelles.
- TTL obligatoire et taille bornée.
- Protéger contre les stampedes, par exemple avec Caffeine asynchrone ou single-flight.
- Pour un cache local + Redis, invalider les deux via pub/sub ou TTL local court.

### Charge utile et sérialisation

- Diffuser les grandes réponses au lieu de matérialiser une énorme liste.
- Activer la compression du texte au-dessus d'un seuil explicite.
- Préférer un record ou DTO typé à `Map<String, Object>`.
- Ne pas journaliser les charges utiles complètes en INFO.

### GC et tas

- Choisir le collecteur selon la charge : G1 pour le débit, ZGC pour une forte contrainte de latence et un grand tas.
- Vérifier la prise en compte de la mémoire du conteneur et préférer `MaxRAMPercentage` à un `-Xmx` rigide.
- Mesurer le taux d'allocation avec JFR ; surveiller `ObjectMapper` par requête, `String.format` sur chemin chaud et autoboxing.

### Clients HTTP

- Dimensionner les pools de connexion par dépendance.
- Définir des timeouts de connexion, lecture, écriture et acquisition pour chaque appel.
- Utiliser un coupe-circuit et un bulkhead pour les dépendances instables.

## Contrôles de `$review`

1. Endpoint `List<T>` sans pagination : blocker.
2. Navigation d'entité dans une boucle déclenchant des requêtes : N+1 probable, major.
3. Pool Hikari modifié sans preuve : demander la mesure.
4. `synchronized` autour d'une E/S : demander une correction.
5. `@Cacheable` sans TTL ni limite : blocker.
6. Appel HTTP externe sans timeouts : blocker.
7. `Counter` pour une durée : demander un `Timer` avec histogramme.

## Preuve avant/après

Chaque changement de performance ajoute à `05-implementation-log.md` :

```text
### T-NNN — perf
Hypothèse: <amélioration attendue>
Avant:     <mesure et unités>
Changement:<résumé>
Après:     <même mesure, même charge>
Preuve:    <chemin ou URL>
Impact SLO:<delta p95 et budget d'erreur>
```

## Vérification

- [ ] Un SLO chiffré est écrit.
- [ ] Une preuve de mesure est liée.
- [ ] Le delta avant/après est consigné.
- [ ] Un changement risqué est protégé par un feature flag.
- [ ] Aucun nouvel anti-pattern n'est introduit.
- [ ] La section Performance de la grille de revue réussit.
