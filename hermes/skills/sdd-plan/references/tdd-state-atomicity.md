# Atomicité de l'état TDD

Toutes les commandes qui écrivent `.tdd-state.json` partagent le verrou
`.specs/<feature-id>/.tdd-state.lock` et utilisent le script
`scripts/tdd_state_guard.py`. Une lecture suivie d'une écriture directe ne
constitue jamais une protection suffisante.

## Planification

1. Avant toute délégation, exécuter `snapshot --feature-dir <chemin>` et
   conserver le `token` retourné (`absent` ou `sha256:<empreinte>`).
2. Après l'approbation humaine, préparer dans le dossier de la fonctionnalité :
   - `03-design.approved.candidate.md` ;
   - `.tdd-state.candidate.json`.
3. Exécuter `commit-plan` avec le token conservé et les deux candidats.
4. Considérer l'approbation comme enregistrée uniquement si la commande réussit.

Après un succès, le script consomme les deux fichiers candidats. En cas
d'échec, il les conserve pour le diagnostic.

`commit-plan` acquiert le verrou, compare l'état courant au token et vérifie
qu'un état existant est encore vierge. Avant le premier remplacement, il écrit
et synchronise sur disque `.tdd-state.transaction.json`. Ce journal contient
les empreintes de l'état avant/après ainsi que les versions précédente et cible
du design. Le script remplace ensuite le design, puis l'état TDD, et ne supprime
le journal qu'après synchronisation des deux artefacts.

Après un arrêt brutal, la première commande `snapshot`, `commit-plan` ou
`write-state` qui obtient le verrou récupère la transaction avant toute autre
opération :

- si l'état possède encore l'empreinte attendue, elle restaure l'ancien design ;
- si l'état possède l'empreinte cible, elle réinstalle le design approuvé ;
- si l'état ne correspond à aucune empreinte, elle refuse toute écriture et
  conserve le journal pour diagnostic manuel.

La récupération conserve également les permissions des artefacts. Un
changement concurrent provoque un refus et aucun état commencé n'est écrasé.

## Autres écrivains

Toute future commande, notamment `/sdd-build`, `/sdd-test` ou une migration,
doit appeler `write-state` avec le token de l'état qu'elle a lu. Elle ne doit
jamais écrire, déplacer ou remplacer `.tdd-state.json` directement.

Le verrou protège la concurrence ; le token fournit une comparaison-et-échange
et détecte également une écriture qui n'aurait pas respecté le verrou.

## Échec

Si le script retourne une erreur de concurrence ou d'état non vierge :

- ne modifier aucun autre artefact ;
- conserver les fichiers candidats pour diagnostic ;
- montrer le nouvel état à l'utilisateur ;
- recommencer uniquement après une nouvelle lecture et une décision explicite.
