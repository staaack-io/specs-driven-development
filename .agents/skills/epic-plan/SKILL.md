---
name: epic-plan
description: "Créer la conception globale et la roadmap de tranches d’une Epic SDD. Utiliser lorsque l’utilisateur invoque $epic-plan ou planifie une initiative en plusieurs tranches."
---

# $epic-plan

**Phase :** 3a — planification Epic
**Agent responsable :** `.codex/agents/spring-architect.toml`
**Skills utilisés :** `epic-slicing-planning`,
`spring-boot-4-conventions`, `openapi-contract-first`, `adr-authoring`,
`performance-optimization`

## Objectif

Créer les artefacts globaux d’une Epic avant les tâches détaillées.

## Entrées

- `<feature-id>`.

## Lectures

- `01-spec.md` ;
- `02-spec-review.md`, dont le verdict doit être `PASS` ;
- `.specs/_stack.json` ;
- les modèles `epic-design.template.md` et `epic-roadmap.template.md`.

## Écritures

- `03-epic-design.md` ;
- `03a-epic-roadmap.md` ;
- les ADR `adr/NNN-*.md` nécessaires.

## Processus

1. Refuser si la revue n’est pas `PASS`.
2. Refuser si la spécification contient un `Q-NNN` non résolu.
3. Produire la conception globale : frontières, décisions partagées, points
   d’intégration, risques et liens ADR.
4. Produire la roadmap : tranches verticales, dépendances, jalons et stratégie
   de déploiement.
5. Ouvrir un `Q-NNN` pour toute décision globale manquante et s’arrêter avant
   le découpage détaillé.

## Refuser si

- le verdict n’est pas `PASS` ;
- un critère n’est couvert ni par la conception ni par la roadmap ;
- une question globale reste ouverte lors de la transmission.

## Terminé lorsque

Les deux artefacts existent, sont cohérents et l’étape recommandée est
`$plan`.
