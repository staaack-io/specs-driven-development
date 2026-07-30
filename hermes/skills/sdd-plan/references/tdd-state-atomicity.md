# Atomicité de l'état TDD

Toutes les commandes qui écrivent `.tdd-state.json` partagent le verrou
`.specs/<feature-id>/.tdd-state.lock` et utilisent le script
`scripts/tdd_state_guard.py`. Une lecture suivie d'une écriture directe ne
constitue jamais une protection suffisante.

## Planification

1. Avant toute délégation, exécuter `snapshot --feature-dir <chemin>` et
   conserver le `token` retourné (`absent` ou `sha256:<empreinte>`).
2. Pendant la revue humaine, écrire uniquement les candidats suivants et
   préserver les artefacts approuvés existants :
   - `03-design.candidate.md` ;
   - `04-tasks.candidate.md` ;
3. Après l'approbation humaine, inscrire la décision dans le design candidat et
   préparer :
   - `.tdd-state.candidate.json`.
4. Exécuter `commit-plan` avec le token conservé et les trois candidats.
5. Considérer l'approbation comme enregistrée uniquement si la commande réussit.

L'état candidat doit produire une empreinte différente de l'état courant. Le
script refuse deux états identiques, car leurs tokens ne permettraient pas de
distinguer une transaction seulement préparée d'une transaction déjà validée
pendant la récupération après crash.

Avant de consommer les trois fichiers candidats, le script écrit et synchronise
un reçu durable `.tdd-state.commit.json`. Ce reçu conserve le token attendu,
les empreintes des trois cibles et les chemins exacts des candidats. En cas
d'échec antérieur au reçu, les candidats restent disponibles pour le diagnostic.
En cas d'arrêt pendant leur suppression, un retry peut terminer le nettoyage
uniquement si le reçu, les cibles et tout candidat restant correspondent encore.

`commit-plan` acquiert le verrou, compare l'état courant au token et vérifie
qu'un état existant est encore vierge. Avant le premier remplacement, il écrit
et synchronise sur disque `.tdd-state.transaction.json`. Ce journal contient
les empreintes de l'état avant/après ainsi que les versions précédentes et cibles
du design et des tâches. Le script remplace ensuite le design, les tâches, puis
l'état TDD, et ne supprime le journal qu'après synchronisation des trois artefacts.

Après un arrêt brutal, la première commande `snapshot`, `commit-plan` ou
`write-state` qui obtient le verrou récupère la transaction avant toute autre
opération :

- si l'état possède encore l'empreinte attendue, elle restaure l'ancien design
  et les anciennes tâches ;
- si l'état possède l'empreinte cible, elle réinstalle le design et les tâches
  approuvés ;
- si l'état ne correspond à aucune empreinte, elle refuse toute écriture et
  conserve le journal pour diagnostic manuel.

Un journal existant dont les empreintes attendue et cible sont identiques est
également refusé et conservé : il ne contient pas assez d'information pour
décider sans risque entre rollback et roll-forward.

Une récupération par roll-forward constitue un commit réussi : `commit-plan`
écrit le reçu, retourne `committed: true` et consomme les candidats. Une
récupération par rollback conserve l'erreur initiale et les candidats pour
diagnostic.

Après un redémarrage, un nouvel appel `commit-plan` peut lui-même terminer le
roll-forward avant la comparaison du token. Il retourne alors le succès
uniquement si l'état, le design et les tâches récupérés correspondent exactement
aux trois candidats fournis ; toute différence impose un diagnostic manuel.
La même vérification idempotente s'applique si le journal a déjà été supprimé :
un token attendu obsolète est accepté uniquement lorsque les trois cibles
courantes correspondent exactement aux candidats. Avant le succès, le garde
rematérialise les trois entrées par remplacement atomique afin qu'aucun symlink,
hard link ou identité de fichier externe ne survive au commit.

La récupération conserve également les permissions des artefacts. Un
changement concurrent provoque un refus et aucun état commencé n'est écrasé.
Pour un journal historique antérieur à l'ajout des tâches dans la transaction,
la récupération ne touche jamais à `04-tasks.md`, y compris à son identité,
ses liens ou ses métadonnées étendues.

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
