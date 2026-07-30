---
name: spec-review
description: "Auditer une spécification SDD pour détecter ambiguïtés et manques. Utiliser lorsque l’utilisateur invoque $spec-review ou demande une revue de spécification."
---

# $spec-review

**Phase :** 2 — revue
**Agent responsable :** `.codex/agents/spec-author.toml`, avec le rôle de
relecteur
**Skills utilisés :** `ears-spec-authoring`,
`requirements-traceability`

## Objectif

Auditer `01-spec.md` avec la checklist et produire
`02-spec-review.md` avec un verdict et la liste numérotée des corrections.

## Entrées

- `<feature-id>`. En son absence, utiliser la fonctionnalité la plus récemment
  modifiée sous `.specs/`.

## Lectures

- `.specs/<feature-id>/01-spec.md` ;
- `.codex/checklists/spec-review.md` ;
- `.codex/templates/spec-review.template.md`.

## Écritures

- `.specs/<feature-id>/02-spec-review.md`.

## Processus

1. Examiner chaque élément et consigner `pass | fail | n/a` avec une
   justification courte.
2. Pour chaque `fail`, indiquer la ligne et la correction concrète.
3. Vérifier la forme EARS de chaque critère.
4. Vérifier que chaque critère peut être testé indépendamment.
5. Exiger une section `## Open Questions` vide avant un verdict global
   `PASS`.
6. Produire `verdict`, `acs_total`, `acs_failed`, `open_questions` et
   `next_command`.

## Refuser si

- `01-spec.md` n’existe pas ;
- un `Q-NNN` n’est pas résolu : le verdict doit être `FAIL` et citer les
  questions exactement.

## Terminé lorsque

`02-spec-review.md` existe. Avec `PASS`, orienter vers `$plan`. Avec
`FAIL`, demander de corriger `01-spec.md`.
