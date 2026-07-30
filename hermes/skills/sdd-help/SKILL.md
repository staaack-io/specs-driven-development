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

Dans le premier lot, les commandes disponibles sont :

| Commande | Rôle |
| --- | --- |
| `/sdd-help [commande]` | Afficher cette aide ou le détail d'une commande. |
| `/sdd-status [feature-id]` | Résumer l'état du workflow sans écrire. |
| `/sdd-spec <demande ou ticket>` | Créer une spécification EARS-lite. |

Signaler séparément que les commandes suivantes font partie de la feuille de
route et ne doivent pas être présentées comme installées avant leur conversion :

`/sdd-spec-review`, `/sdd-epic-plan`, `/sdd-plan`, `/sdd-build`, `/sdd-test`,
`/sdd-validate`, `/sdd-review`, `/sdd-code-simplify`, `/sdd-ship`,
`/sdd-onboard` et `/sdd-wire-harness`.

## Avec un argument

1. Normaliser l'argument en retirant un éventuel préfixe `/`.
2. Vérifier que le skill correspondant est disponible.
3. Résumer son objectif, ses entrées, ses lectures, ses écritures, ses refus et
   sa condition de fin.
4. Si le skill n'est pas installé, le dire explicitement et ne pas inventer son
   comportement.

## Résultat attendu

Une aide courte, en français, adaptée à une personne qui découvre Hermes.
