# Rapport d'onboarding : legacy-orders

| Champ | Valeur |
|---|---|
| Exécution | 2025-01-20T09:14:02Z |
| Classification | **brownfield** |
| Sources Java | 312 fichiers, environ 30k lignes sous `com.legacy.orders` |
| Tests Java | 492 fichiers, 480 unitaires et 12 d'intégration |
| Modules | 1, package racine unique sans frontières |

## État de la stack (`.specs/_stack.json`)

```json
{
  "java_version": "21",
  "spring_boot_version": "3.2.5",
  "db_engines": ["postgresql"],
  "migration": "none",
  "test": { "junit5": true, "testcontainers": false, "archunit": false },
  "openapi": { "springdoc": false, "spec_file": false },
  "harness_layers": {
    "spotless": false, "checkstyle": false, "spotbugs": false,
    "jacoco": false, "pit": false, "dependency_check": false
  }
}
```

## Exécution de référence du harness

| Couche | Statut | Note |
|---|---|---|
| Spotless | skipped | plugin non configuré |
| Checkstyle | skipped | plugin non configuré |
| Compilation + Error Prone | partial | compilation réussie, Error Prone absent |
| SpotBugs | skipped | plugin non configuré |
| ArchUnit | skipped | dépendance absente |
| Surefire, unitaire | pass | 480 tests, aucun échec, 7 ignorés |
| Failsafe, intégration | warn | 12 tests sur H2 en mémoire, différent du moteur de production |
| JaCoCo | n/a | non configuré |
| Mutation PIT | n/a | non configuré |
| OWASP Dependency-Check | n/a | non configuré |

> Une mesure ponctuelle avec le CLI JaCoCo donne **71 % de lignes et 58 % de
> branches**. Cette valeur devient la référence de fait. Le nouveau code conserve
> son seuil de 95 %, tandis que le plancher du projet augmente progressivement.

## Constats

1. **Aucun outil de migration pour un service Postgres.** Introduire Flyway et
   créer `V1__baseline.sql` depuis un `pg_dump --schema-only` de production.
2. **H2 pour les tests d'intégration d'une application Postgres.** Remplacer par
   Testcontainers avec la même version mineure de Postgres que la production.
3. **Aucun formatage, lint ou analyse statique.** Adopter Spotless et Checkstyle,
   puis SpotBugs dans une PR séparée pour limiter le diff.
4. **Aucune couverture imposée.** Raccorder JaCoCo aux valeurs mesurées, puis
   augmenter le plancher de deux points par sprint jusqu'à 90 %.
5. **Aucun test de mutation.** Différer PIT jusqu'à une couverture d'au moins 80 % lignes et 75 % branches.
6. **Aucune frontière de modules.** Commencer par une règle ArchUnit d'absence de cycles.
7. **Spring Boot 3.2 au lieu de Boot 4.** Suivre la migration comme un élément de roadmap distinct, sans bloquer `$spec`.

## Prochaines commandes recommandées, dans l'ordre

1. Intégrer Spotless et Checkstyle dans le POM.
2. Adopter Flyway et capturer le schéma de production.
3. Remplacer H2 par Testcontainers.
4. Ajouter JaCoCo au plancher de référence.
5. Ajouter SpotBugs et Error Prone.
6. Ajouter OWASP Dependency-Check.
7. Ajouter la règle ArchUnit d'absence de cycles.
8. **Ensuite seulement**, exécuter `$spec` pour la première fonctionnalité.

L'agent ne lance pas `$spec` avant que les quatre premières PR soient vertes ;
sinon `$validate` échouerait systématiquement et la méthode deviendrait cérémonielle.

## Fichiers écrits

- `.specs/_stack.json`
- `.specs/_baseline.json`
- `.specs/_onboarding.md`, ce fichier
