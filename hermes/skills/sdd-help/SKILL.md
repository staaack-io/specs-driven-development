---
name: sdd-help
description: "Présenter les commandes du workflow SDD."
---

# Aide du workflow SDD

Cette commande est en lecture seule. Elle explique le framework sans modifier
le projet.

## Sans argument

Présenter les commandes SDD effectivement disponibles dans le profil Hermes.
Pour chacune, donner en une ligne son objectif, ses entrées et la phase à
laquelle elle appartient.

Les commandes actuellement disponibles sont :

| Étape | Commande | Rôle |
| --- | --- | --- |
| Méta | `/sdd-help [commande]` | Afficher cette aide ou le détail d'une commande. |
| Méta | `/sdd-status [feature-id]` | Résumer l'état du workflow sans écrire. |
| 1 | `/sdd-spec <demande ou ticket>` | Créer une spécification EARS-lite. |
| 2 | `/sdd-spec-review [feature-id]` | Relire et approuver la spécification. |

Signaler séparément que les commandes suivantes font partie de la feuille de
route et ne doivent pas être présentées comme installées avant leur conversion :

| Étape | Commande prévue | Rôle |
| --- | --- | --- |
| 0 | `/sdd-onboard` | Analyser un projet existant. |
| 0 | `/sdd-wire-harness` | Brancher le harness de validation. |
| 3a, Epic uniquement | `/sdd-epic-plan` | Concevoir l'Epic et sa roadmap. |
| 3 ou 3b | `/sdd-plan` | Concevoir et découper en tâches. |
| 4 | `/sdd-build <T-NNN>` | Implémenter une tâche en TDD. |
| 4 | `/sdd-code-simplify` | Simplifier après le passage au vert. |
| 5 | `/sdd-test` | Ajouter les tests transverses. |
| 6 | `/sdd-validate` | Exécuter le harness et la traçabilité. |
| 7 | `/sdd-review` | Relire le code avant commit. |
| 8, facultative | `/sdd-ship` | Préparer la livraison sans déployer. |

## Avec un argument

1. Normaliser l'argument en retirant un éventuel préfixe `/`.
2. Vérifier que le skill correspondant est disponible.
3. Résumer son objectif, ses entrées, ses lectures, ses écritures, ses refus et
   sa condition de fin.
4. Si le skill n'est pas installé, le dire explicitement et ne pas inventer son
   comportement.

## Résultat attendu

Une aide courte, en français, adaptée à une personne qui découvre Hermes.
