---
name: validate
description: "Exécuter le harness SDD et produire les rapports de validation et de traçabilité. Utiliser lorsque l’utilisateur invoque $validate ou demande de valider une fonctionnalité."
---

# $validate

**Phase :** 6 — validation par le harness
**Agent responsable :** `.codex/agents/spring-validator.toml`
**Skills utilisés :** `harness-report-parsing`,
`jacoco-coverage-policy`, `pit-mutation-tuning`,
`requirements-traceability`, `archunit-rules`

## Routage selon la stack

| Sources modifiées | Agent |
| --- | --- |
| Java/Kotlin uniquement | `spring-validator` |
| React/Next.js uniquement | `react-nextjs-validator` |
| Les deux | les deux validateurs, avec un rapport commun |

Déterminer le périmètre depuis les tâches ou `git diff --name-only`.

## Objectif

Exécuter les dix couches, lire les résultats et écrire un rapport avec un
verdict unique `PASS` ou `FAIL`.

## Entrées

- `<feature-id>` facultatif ; en son absence, couvrir les changements depuis
  `origin/main`.

## Lectures

- scripts du harness, de couverture et de traçabilité ;
- `target/harness-summary.json` ;
- spécification, tâches et plan de test.

## Écritures

- `07-validation-report.md` ;
- `07a-traceability.md` ;
- rapports JSON sous `target/`.

## Processus

1. Exécuter `.github/scripts/harness.sh --report`.
2. Exécuter le contrôle de couverture du nouveau code, avec un minimum de 95 %.
3. Régénérer la traçabilité ; un critère sans test produit `FAIL`.
4. Agréger les dix portes, la couverture et la traçabilité. Le verdict vaut
   `PASS` uniquement si tout passe ; une mutation peut valoir `warn`
   seulement avec justification explicite.
5. Écrire le verdict, la table des portes, les principaux échecs, les liens et
   l’action suivante.

## Refuser si

- une tâche n’est pas `done` ;
- les résultats sont anciens ou le harness a été contourné ;
- l’invocation Maven aurait été bloquée par `forbid-skip-flags.sh`.

## Terminé lorsque

Le rapport contient un verdict clair. Avec `PASS`, orienter vers `$review`.
Avec `FAIL`, proposer le plus petit ensemble d’actions `$build` ou
`$test`.
