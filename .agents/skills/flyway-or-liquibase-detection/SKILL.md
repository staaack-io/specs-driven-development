---
name: flyway-or-liquibase-detection
description: Détecter automatiquement l’outil de migration de base de données et suivre ses conventions. Ne jamais utiliser Flyway et Liquibase ensemble. Utiliser pour concevoir ou écrire un changement de schéma.
when_to_use:
  - Phase 3, Plan — concevoir une migration liée à une fonctionnalité.
  - Phase 4, Build — ajouter le script de migration.
  - $onboard — consigner l’outil détecté dans la référence de conception.
authoritative_references:
  - https://documentation.red-gate.com/flyway/flyway-cli-and-api
  - https://docs.liquibase.com/concepts/changelogs/home.html
---

# Détection de Flyway ou Liquibase

## Détection

`.github/scripts/detect-stack.sh` renvoie :

- `flyway` — `flyway-core` dans `pom.xml` ET dossier `src/main/resources/db/migration/` ;
- `liquibase` — `liquibase-core` dans `pom.xml` ET dossier `src/main/resources/db/changelog/` ;
- `none` — aucun des deux ;
- `both` — **fatal** : refuser de continuer et demander à l'utilisateur d'en retirer un.

Consigner le résultat dans `03-design.md` sous `### Inputs from detect-stack.sh`.

## Conventions Flyway

- Chemin : `src/main/resources/db/migration/V{version}__{description}.sql`
- Versions : `V1__init.sql`, `V2__add_gift_card_table.sql`, `V3__add_index_gift_card_code.sql`
- Une migration par changement logique. Ne jamais modifier une migration suivie par Git ; en ajouter une.
- Migrations répétables pour vues et fonctions : `R__view_active_orders.sql`.
- Progressives par défaut. Toute migration destructive exige une section `## Rollback` dans `03-design.md`.

```sql
-- V12__add_gift_card_table.sql
CREATE TABLE gift_card (
    id          UUID PRIMARY KEY,
    code        VARCHAR(64) NOT NULL UNIQUE,
    balance     NUMERIC(12,2) NOT NULL CHECK (balance >= 0),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_gift_card_code ON gift_card(code);
```

## Conventions Liquibase

- Changelog principal : `src/main/resources/db/changelog/db.changelog-master.yaml`
- Fichier par fonctionnalité : `db/changelog/changes/2026-04-18-gift-card.yaml`
- Inclusion via `<include file="changes/2026-04-18-gift-card.yaml"/>`.
- Chaque changeset possède `id` et `author`, puis devient **immuable** après fusion.

```yaml
databaseChangeLog:
  - changeSet:
      id: gift-card-1
      author: spring-implementer
      changes:
        - createTable:
            tableName: gift_card
            columns:
              - column: { name: id, type: UUID, constraints: { primaryKey: true } }
              - column: { name: code, type: VARCHAR(64), constraints: { nullable: false, unique: true } }
              - column: { name: balance, type: NUMERIC(12,2), constraints: { nullable: false } }
              - column: { name: created_at, type: TIMESTAMPTZ, defaultValueComputed: now() }
```

## Tests

- Les migrations s'exécutent automatiquement dans le conteneur Postgres Testcontainers au démarrage des tests.
- Un `MigrationsIT` dédié exécute `flyway:info` ou `liquibase status` à la dernière version et vérifie qu'aucune migration n'est en attente.

## Anti-patterns

- Modifier une migration déjà livrée : incohérence de checksum et rupture en production.
- Utiliser `Flyway.repair()` dans le code de l'application.
- Exécuter `DROP TABLE` sans ADR.
- Renommer une colonne sans migration en deux temps : ajout, remplissage, bascule des lectures, bascule des écritures, suppression.
- Faire coexister les deux outils ; `both` est fatal.
