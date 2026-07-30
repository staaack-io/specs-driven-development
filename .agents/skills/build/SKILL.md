---
name: build
description: "Exécuter une tâche SDD planifiée selon rouge, vert, refactorisation et simplification. Utiliser lorsque l’utilisateur invoque $build ou demande d’implémenter une tâche T-NNN."
---

# $build

**Phase :** 4 — implémentation TDD
**Agent responsable :** `.codex/agents/spring-implementer.toml`, en
collaboration avec `spring-test-engineer`
**Skills utilisés :** `tdd-red-green-refactor`,
`spring-boot-4-conventions`, `clarity-over-cleverness`,
`junit5-testcontainers-patterns`, `spring-task-decomposition`

## Routage selon la stack

| Type de tâche | Étape rouge | Étapes vert/refactorisation/simplification |
| --- | --- | --- |
| Backend Java | `spring-test-engineer` | `spring-implementer` |
| Frontend React/Next.js | `react-nextjs-test-engineer` | `react-nextjs-implementer` |

Déterminer le type depuis `files_in_scope`. Pour du frontend, charger
`react-nextjs-developer` séparément. Pour une tâche mixte, traiter d’abord le
backend, puis le frontend.

## Objectif

Exécuter une tâche de bout en bout selon rouge → vert → refactorisation →
simplification, actualiser `.tdd-state.json` et compléter
`05-implementation-log.md` après chaque étape.

## Entrées

- `<task-id>`, par exemple `T-001`, obligatoire.

## Lectures

- `04-tasks.md` ;
- `03-design.md` ;
- `.tdd-state.json` ;
- `tdd-red-green-refactor`, source de vérité.

## Écritures

- uniquement les fichiers de test et de production déclarés dans
  `files_in_scope` ;
- `.tdd-state.json` ;
- un bloc par étape dans `05-implementation-log.md`.

## Processus

0. Exécuter `git status`. Refuser de commencer si une tâche précédente laisse
   des modifications non committées.
1. Activer la tâche. Refuser si une autre tâche est en cours.
2. **Rouge.** Écrire le plus petit test pour la prochaine tranche de critère,
   l’exécuter, capturer l’échec attendu, passer la phase à `red` et consigner.
3. **Vert.** Écrire le minimum de production, exécuter le nouveau test puis toute
   la suite, passer à `green` et consigner.
4. **Refactorisation.** Améliorer la structure sans changer le comportement,
   relancer les tests, passer à `refactor` et consigner.
5. **Simplification.** Appliquer `clarity-over-cleverness`, relancer les tests,
   passer à `simplify` et consigner.
6. **Fin.** Passer à `done` et vider `active_task`. Reprendre à l’étape rouge
   si un critère de la tâche reste sans preuve.
7. S’arrêter, afficher les fichiers, tests et message de commit suggéré. Ne pas
   démarrer automatiquement la tâche suivante.

## Refuser si

- la tâche n’existe pas dans l’état TDD ;
- une autre tâche est en cours ;
- une édition de production survient hors phase `red` sans extrait d’échec ;
- un test est modifié hors de `files_in_scope`.

## Terminé lorsque

- chaque critère couvert possède au moins un test `@Tag("AC-NNN")` ;
- les quatre étapes sont consignées ;
- la tâche vaut `done` ;
- le rappel de commit est affiché. Après toutes les tâches, exécuter `$test`
  puis `$validate`.
