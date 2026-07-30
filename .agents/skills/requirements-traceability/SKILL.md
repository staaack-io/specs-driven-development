---
name: requirements-traceability
description: Construire et vérifier dans `07a-traceability.md` la matrice critères ↔ tâches ↔ tests ↔ symboles ↔ portes. Utiliser pour confirmer qu’aucun critère n’est découvert et qu’aucun test n’est orphelin.
when_to_use:
  - Phase 6, Validate — `$validate` produit la matrice.
  - Revue de code — vérifier la matrice contre les fichiers réels.
authoritative_references:
  - .codex/templates/traceability.template.md
---

# Traçabilité des exigences

## Éléments tracés

Pour chaque `AC-NNN` de `01-spec.md` :

- les tâches `T-NNN` qui l'implémentent dans `04-tasks.md` ;
- les méthodes de test qui le vérifient via `@Tag("AC-NNN")` ou `@DisplayName("AC-NNN: …")` ;
- les symboles de production touchés par les diffs de ces tâches ;
- les portes du harness exécutées sur ces symboles.

Pour chaque méthode de test : l'AC qu'elle affirme vérifier et la tâche qui l'a introduite.

Pour chaque symbole de production modifié : au moins un test qui le couvre, sinon il devient du code orphelin.

## Construction de la matrice

`spring-validator` exécute `.github/scripts/traceability.sh`, qui :

1. extrait les titres `**AC-NNN**` de `01-spec.md` ;
2. extrait des tâches de `04-tasks.md` les associations `**AC-IDs:**` ;
3. cherche dans `src/test/java/**/*.java` les annotations de traçabilité ;
4. lit `git diff --name-only origin/main...HEAD` et croise les fichiers avec la couverture JaCoCo par méthode ;
5. lit `harness-summary.json` pour connaître les portes exécutées ;
6. produit `07a-traceability.md`.

## Contrôles requis

- **Aucun AC non couvert.** Chaque `AC-NNN` apparaît dans au moins un `@Tag` ou `@DisplayName`.
- **Aucun test orphelin.** Chaque test marqué `AC-NNN` référence un AC réel.
- **Aucun code orphelin.** Chaque méthode de production modifiée est couverte par au moins un test.
- **Aucune tâche non tracée.** Chaque `T-NNN` marquée `done` possède un commit consigné.

L'échec d'un seul contrôle fait renvoyer ❌ au validateur.

## Exemple de sortie abrégé

```markdown
## Coverage

| AC-ID | Tasks | Tests | Status |
|-------|-------|-------|--------|
| AC-001 | T-001, T-002 | ApplyGiftCardRequestTest#rejectsBlankCode | ✅ |

## Orphan tests

_Aucun._

## Orphan code

_Aucun._

## Verdict

✅ Tous les AC sont couverts. Aucun orphelin.
```

## Convention de marquage imposée

```java
@Test
@DisplayName("AC-007: rejects expired gift card with 4xx")
@Tag("AC-007")
void rejectsExpired() { ... }
```

Écrire `@DisplayName` et `@Tag` pour la redondance : l'un est lisible par une
personne, l'autre par la machine. Une règle Checkstyle refuse un `@DisplayName`
qui correspond à `^AC-\\d{3}:` sans `@Tag` correspondant.

## Anti-patterns

- Un test géant qui vérifie cinq AC : le scinder.
- Marquer seulement l'AC de plus grand numéro d'un groupe : marquer chaque AC vérifié.
- Ajouter un tag sans assertion réelle du comportement.
- Retirer un tag pour rendre la traçabilité verte.
