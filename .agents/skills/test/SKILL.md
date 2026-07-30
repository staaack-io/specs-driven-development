---
name: test
description: "Créer ou compléter le plan de test SDD et combler les écarts sans modifier la production. Utiliser lorsque l’utilisateur invoque $test ou demande de corriger la couverture ou les mutations."
---

# $test

**Phase :** 5 — plan et renforcement des tests
**Agent responsable :** `.codex/agents/spring-test-engineer.toml`
**Skills utilisés :** `junit5-testcontainers-patterns`,
`requirements-traceability`, `pit-mutation-tuning`, `archunit-rules`

## Objectif

Créer ou actualiser `06-test-plan.md` et ajouter uniquement les tests
nécessaires pour fermer les écarts de couverture ou de mutation.

## Entrées

- `<feature-id>` ;
- `--gap` facultatif pour lire les derniers rapports.

## Lectures

- spécification, conception et tâches ;
- résumé du harness et rapports JaCoCo/PIT présents ;
- modèle `test-plan.template.md`.

## Écritures

- `06-test-plan.md` ;
- fichiers sous `src/test/**` uniquement, jamais `src/main/**`.

## Processus

1. Construire la matrice critères × types de tests et les exigences
   Testcontainers.
2. Avec `--gap`, consigner les lignes non couvertes et mutants survivants sous
   forme de `Gap-NNN`.
3. Écrire les tests avec `@Tag("AC-NNN")` et un `@DisplayName` descriptif.
4. Exécuter `mvn test`, ou `mvn verify` si les tests d’intégration changent.
5. Régénérer la traçabilité avec
   `.github/scripts/traceability.sh <feature-id>`.

## Refuser si

- une modification sous `src/main/**` est demandée ; la déléguer à `$build` ;
- `04-tasks.md` manque.

## Terminé lorsque

Le plan est à jour, chaque `Gap-NNN` possède un test ou une justification
explicite `Won't fix`, et la matrice est régénérée.
