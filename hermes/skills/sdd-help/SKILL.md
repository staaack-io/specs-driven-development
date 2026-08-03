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
| 0 | `/sdd-onboard` | Analyser un projet existant sans modifier le produit. |
| 0 | `/sdd-wire-harness` | Brancher le harness de validation. |
| 1 | `/sdd-spec <demande ou ticket>` | Créer une spécification EARS-lite. |
| 2 | `/sdd-spec-review [feature-id]` | Relire et approuver la spécification. |
| 3a, Epic uniquement | `/sdd-epic-plan` | Concevoir l'Epic et sa roadmap. |
| 3 | `/sdd-plan <feature-id>` | Concevoir et découper en tâches. |
| 4 | `/sdd-build <feature-id> <T-NNN>` | Implémenter en TDD ou admettre une vague `--parallel`. |
| 4 | `/sdd-code-simplify <path> [--dry-run]` | Simplifier sans changer le comportement. |
| 5 | `/sdd-test <feature-id> [--gap]` | Ajouter les tests transverses sans toucher à la production. |
| 6 | `/sdd-validate [<feature-id>]` | Exécuter le harness et publier les rapports communs. |

Signaler séparément que les commandes suivantes font partie de la feuille de
route et ne doivent pas être présentées comme installées avant leur conversion :

| Étape | Commande prévue | Rôle |
| --- | --- | --- |
| 7 | `/sdd-review` | Relire le code avant commit. |
| 8, facultative | `/sdd-ship` | Préparer la livraison sans déployer. |

Les rôles restent des références internes embarquées dans les skills. Le nom
interne `sdd-roles` n'est pas une commande publique `/sdd-roles`.

## Avec un argument

1. Normaliser l'argument en retirant un éventuel préfixe `/`.
2. Vérifier que le skill correspondant est disponible.
3. Résumer son objectif, ses entrées, ses lectures, ses écritures, ses refus et
   sa condition de fin.
4. Si le skill n'est pas installé, le dire explicitement et ne pas inventer son
   comportement.

## Résultat attendu

Une aide courte, en français, adaptée à une personne qui découvre Hermes.
