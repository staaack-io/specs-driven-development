# Définition de terminé — par tâche (`$build <task-id>`)

Une tâche est **terminée** uniquement lorsque TOUS les points suivants sont vrais.

## Red

- [ ] Au moins un nouveau test existe avec les `Test-IDs` de la tâche.
- [ ] Les nouveaux tests ont été exécutés et **ont échoué pour la raison attendue** (écart d'assertion, NPE, endpoint manquant — pas une erreur de compilation déguisée en échec).
- [ ] Une entrée `red` a été ajoutée à `05-implementation-log.md` avec la commande en échec et un extrait de sa sortie.
- [ ] `.specs/<feature-id>/.tdd-state.json` a été mis à jour.

## Green

- [ ] Les modifications du code de production restent dans les `Files in scope` de la tâche.
- [ ] Le minimum de code de production nécessaire au passage du test a été écrit, sans fonctionnalité supplémentaire ni abstraction spéculative.
- [ ] Tous les nouveaux tests réussissent.
- [ ] Une entrée `green` a été ajoutée à `05-implementation-log.md`.

## Refactor + Simplify

- [ ] La suite complète du module (`mvn -q verify -pl <module>`) réussit.
- [ ] `$code-simplify` a été exécuté (clarté plutôt qu'astuce) et la suite réussit toujours.
- [ ] Les entrées `refactor` et `simplify` ont été ajoutées à `05-implementation-log.md`.

## Qualité

- [ ] Aucun test `@Disabled` n'est introduit sans commentaire `# DisabledReason: <link>`.
- [ ] Aucune assertion n'est supprimée.
- [ ] Aucun seuil de couverture n'est abaissé.
- [ ] Spotless et Checkstyle passent sur les fichiers modifiés.

## Traçabilité

- [ ] Chaque nouveau test référence son AC via `@DisplayName("AC-NNN: …")` ou `@Tag("AC-NNN")`.
- [ ] L'entrée de la tâche dans `04-tasks.md` est marquée `done` avec le SHA du commit d'implémentation.

## Interdictions

- [ ] Aucun `git commit` n'a été tenté ; les commits n'interviennent qu'après approbation de `$review`.
- [ ] Aucun `mvn -DskipTests`, `-Dpit.skip`, `-Dcheckstyle.skip` ou `--no-verify` n'a été utilisé.
