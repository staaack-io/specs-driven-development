# Tâches : <FEATURE-ID>

> Responsable : `spring-architect` · Phase 3 · Modèle : `.codex/templates/tasks.template.md`
>
> Une tâche représente environ 1 à 4 heures. Elle possède des Test-IDs, un périmètre de fichiers et des portes explicites. Les tâches sont exécutées avec `$build <task-id>`.

## Inputs

- Révision de `03-design.md` : <git-sha ou horodatage>

## Task Index

| ID | Titre | AC-IDs | Dépend de | Portes |
|---|---|---|---|---|
| T-001 | … | AC-001 | — | unit, slice, IT, coverage |
| T-002 | … | AC-002, AC-003 | T-001 | unit, slice, IT, coverage |

## Tasks

### T-001 : <titre impératif court>

- **AC-IDs :** AC-001
- **Test-IDs :** T-001-T1 (slice — validation du contrôleur), T-001-T2 (IT — Testcontainers Postgres)
- **Files in scope :**
  - `src/main/java/<package>/<NewClass>.java`
  - `src/test/java/<package>/<NewClassTest>.java`
  - `src/test/java/<package>/<NewClassIT>.java`
- **Dépendances :** aucune
- **Portes à exécuter après green :** `format`, `compile`, `archunit`, `unit`, `slice`, `it`, `coverage`
- **Retour arrière :** annuler le commit ; aucune modification de schéma.
- **Notes :** <information utile à l'implémentation, sans jamais inventer de comportement>

### T-NNN : …

## Cross-cutting items (handled in Phase 5)

- Règles de vérification ArchUnit
- Test du contrat OpenAPI
- Tests génératifs, lorsqu'ils sont utiles

## Open Questions

- Q-001 : …

## Resolved Questions

- (aucune pour le moment)

## Sign-off

- [ ] Chaque AC de `01-spec.md` est couverte par au moins une tâche.
- [ ] Chaque tâche possède des Test-IDs et des Files-in-scope.
- [ ] Toutes les `Q-NNN` sont résolues ou différées avec justification.
- [ ] Revue effectuée par l'utilisateur le <YYYY-MM-DD>.
