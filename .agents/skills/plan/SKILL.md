---
name: plan
description: "Créer la conception détaillée et le découpage TDD d’une spécification approuvée. Utiliser lorsque l’utilisateur invoque $plan ou demande de concevoir et planifier une fonctionnalité SDD."
---

# $plan

**Phase :** 3 — planification
**Agent responsable :** `.codex/agents/spring-architect.toml`
**Skills utilisés :** `epic-slicing-planning`,
`spring-task-decomposition`, `spring-boot-4-conventions`,
`openapi-contract-first`, `flyway-or-liquibase-detection`,
`archunit-rules`, `adr-authoring`, `performance-optimization`

## Routage selon la stack

| Périmètre | Agent |
| --- | --- |
| Backend ou full-stack Spring | `spring-architect` |
| Frontend React/Next.js | `react-nextjs-architect` |
| Full-stack | les deux, chacun pour ses tâches |

Si les critères portent uniquement sur l’interface React/Next.js, déléguer à
`react-nextjs-architect` et charger séparément
`react-nextjs-developer`. Pour un périmètre mixte, produire un unique
`03-design.md`, puis séparer les tâches backend et frontend.

## Objectif

Transformer une spécification au verdict `PASS` en conception et tâches, puis
initialiser `.tdd-state.json`. En mode Epic, partir d’abord de la conception
globale et de la roadmap approuvées.

## Entrées

- `<feature-id>` ;
- `--epic` facultatif pour forcer le mode Epic.

## Lectures

- `01-spec.md` et `02-spec-review.md` ;
- `.specs/_stack.json` ;
- modèles de conception, tâches, ADR et, si nécessaire, Epic ;
- tous les skills d’architecture listés plus haut.

## Écritures

- artefacts Epic en mode Epic ;
- `03-design.md` ;
- `04-tasks.md` ;
- `.tdd-state.json`, sans tâche active et avec chaque phase à `pending` ;
- ADR pour toute décision architecturale significative.

## Processus

1. Exiger une revue présente et `PASS`.
2. Exiger zéro `Q-NNN` ouvert.
3. Activer le mode Epic si demandé ou si plusieurs tranches et décisions
   partagées sont nécessaires.
4. En mode Epic, produire d’abord les deux artefacts et s’arrêter s’ils
   contiennent une question ouverte.
5. Décrire modules, API, contrat REST/OpenAPI, données, migrations, erreurs,
   observabilité, sécurité et règles ArchUnit.
6. Écrire un ADR pour chaque choix architectural important.
7. Découper en tâches `T-001`, `T-002`, etc. Chaque tâche déclare `id`,
   `title`, `acs_covered`, `files_in_scope`, `depends_on` et
   `estimated_phases`. Une tâche touchant `src/main/**` doit inclure un
   fichier sous `src/test/**`.
8. Vérifier que chaque critère apparaît dans au moins une tâche.
9. Initialiser l’état TDD avec les clés contractuelles existantes.

## Refuser si

- la revue n’est pas `PASS` ;
- un artefact Epic obligatoire manque ;
- un critère n’a aucune tâche ;
- une tâche de production n’inclut aucun test dans son périmètre.

## Terminé lorsque

La conception, les tâches, les ADR et l’état TDD sont écrits. Orienter vers
`$build T-001`.
