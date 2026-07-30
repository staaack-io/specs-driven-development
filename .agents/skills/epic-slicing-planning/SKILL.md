---
name: epic-slicing-planning
description: Planifier les grandes fonctionnalités en définissant l’architecture globale de l’Epic et une roadmap de tranches verticales avant les tâches détaillées. Utiliser en phase 3 pour les initiatives en plusieurs tranches.
when_to_use:
  - La fonctionnalité couvre plusieurs jalons ou tranches verticales.
  - Des décisions architecturales transverses doivent précéder les tâches détaillées.
  - L’équipe a besoin d’un ordre tenant compte des dépendances et d’un périmètre contrôlé.
authoritative_references:
  - .codex/templates/epic-design.template.md
  - .codex/templates/epic-roadmap.template.md
  - .codex/checklists/design-review.md
---

# Planification et découpage d'un Epic

## Objectif

Réduire le risque de planification des grandes fonctionnalités en séparant :

1. les décisions de conception au niveau Epic ;
2. la planification détaillée et le découpage en tâches de chaque tranche.

## Livrables

1. `03-epic-design.md` : frontières, décisions partagées, contraintes
   transverses, liens vers les ADR et `Q-NNN` au niveau Epic.
2. `03a-epic-roadmap.md` : backlog des tranches verticales, ordre des dépendances,
   intention des jalons et notes de mise en production.

## Règles de découpage

- Préférer des tranches verticales visibles par l'utilisateur aux tranches horizontales par couche.
- Garder chaque tranche testable et livrable indépendamment.
- Placer les décisions d'infrastructure partagées dans la conception Epic, sans les répéter par tranche.
- Éviter de planifier à l'avance toutes les tâches d'implémentation de l'Epic complet.

## Anti-patterns

- Une roadmap composée uniquement des couches backend puis frontend.
- Des tranches invisibles pour l'utilisateur et impossibles à valider de bout en bout.
- Des décisions Epic non résolues répercutées dans de nombreuses tâches.
- Des tranches géantes impliquant plusieurs équipes sans frontières définies.

## Critères de passage de relais

- Les artefacts Epic sont approuvés.
- Les `Q-NNN` de l'Epic sont résolues ou différées avec justification.
- Au moins une première tranche est prête pour la décomposition détaillée par `$plan`.
