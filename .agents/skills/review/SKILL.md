---
name: review
description: "Effectuer la revue SDD avant commit au regard des artefacts approuvés. Utiliser lorsque l’utilisateur invoque $review ou demande la revue de code du framework."
---

# $review

**Phase :** 7 — revue du code avant commit
**Agent responsable :** `.codex/agents/spring-code-reviewer.toml`
**Skills utilisés :** `spring-code-review-rubric`,
`clarity-over-cleverness`, `spring-boot-4-conventions`,
`spring-security-baseline`, `performance-optimization`

## Routage selon la stack

| Fichiers du diff | Agent |
| --- | --- |
| Java/Kotlin/POM/SQL | `spring-code-reviewer` |
| React/Next.js | `react-nextjs-code-reviewer` |
| Les deux | les deux relecteurs, avec un rapport commun |

Inspecter la liste des fichiers. Pour un diff frontend, déléguer entièrement à
`react-nextjs-code-reviewer` et charger `react-nextjs-developer`
séparément.

## Objectif

Relire le diff avant le commit et produire `08-code-review.md` avec des
constats classés.

## Entrées

- `<feature-id>` facultatif, par défaut la plus récente ;
- `--base <ref>` facultatif, par défaut `origin/main`.

## Lectures

- diff depuis la base ;
- spécification, conception et rapport de validation ;
- `spring-code-review-rubric`, source de vérité.

## Écritures

- `08-code-review.md`.

## Processus

1. Exiger un verdict de validation `PASS`.
2. Examiner chaque fichier selon : correction, sécurité, conception, tests,
   observabilité, performance, clarté et conventions.
3. Classer chaque constat en `must-fix`, `should-fix`, `nit` ou
   `praise`. Donner fichier, lignes et correction pour les deux premiers.
4. Vérifier que chaque critère possède un test dans le diff ou déjà fusionné.
5. En présence d’un `must-fix`, recommander `$build` ou
   `$code-simplify`, sans appliquer automatiquement de correction.
6. Résumer les nombres par sévérité et l’action suivante.

## Refuser si

- le rapport de validation manque ou vaut `FAIL` ;
- le diff est vide.

## Terminé lorsque

`08-code-review.md` existe. Sans `must-fix`, proposer un message de commit et
demander à l’utilisateur d’exécuter `git commit` lui-même.
