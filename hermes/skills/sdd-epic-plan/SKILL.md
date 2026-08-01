---
name: sdd-epic-plan
description: "Concevoir une Epic SDD approuvée et ordonner ses tranches verticales."
---

# Planification d'une Epic SDD

Produire une conception globale et une roadmap de tranches verticales sans
détailler les tâches d'implémentation. Orchestrer des rôles internes ; ne jamais
présenter ces rôles comme des commandes utilisateur.

## Entrée

- exiger un `feature-id` ;
- accepter `--continue <feature-id>` pour reprendre les candidats existants ;
- accepter `--decision approve|request-changes` uniquement avec `--continue`
  après la production de candidats valides ;
- refuser d'écraser un artefact final ou candidat sans `--continue`.

## Portes d'entrée

Avant toute délégation :

1. lire `.specs/<feature-id>/01-spec.md` et exiger des `AC-NNN` uniques ;
2. lire `.specs/<feature-id>/02-spec-review.md`, exiger
   `verdict: approve`, puis exécuter
   `../sdd-spec-review/scripts/review_decision_guard.py validate-final` ;
3. exiger zéro `Q-NNN` au statut `open` dans la spécification et la revue ;
4. exécuter `scripts/epic_plan_guard.py snapshot` avant toute délégation et
   conserver son token ;
5. lire les candidats avant les artefacts finaux lors d'une reprise ;
6. ne jamais modifier la spécification, sa revue ou le code du projet.

## Références

Toujours lire :

- [contrat de délégation](references/delegation-contract.md) ;
- [contrat de l'Epic](references/epic-contract.md) ;
- [preuves de stack](references/stack-evidence.md) ;
- [atomicité](references/transaction-atomicity.md) ;
- [modèle de conception](templates/epic-design.template.md) ;
- [modèle de roadmap](templates/epic-roadmap.template.md).

Lire les rôles prouvés par la fonctionnalité :

- backend Spring : [architecte Spring](references/role-spring-architect.md) ;
- frontend React/Next.js :
  [architecte React/Next.js](references/role-react-nextjs-architect.md) ;
- full-stack : lire et déléguer les deux rôles.

Appliquer `references/stack-evidence.md` avant de choisir un rôle. Avec
`stack: unknown`, ne déléguer aucun architecte et demander une clarification ou
recommander `/sdd-onboard` au lieu de choisir un rôle par proximité.

## Délégation en lecture seule

1. Construire un contexte autonome avec la racine du projet, le `feature-id`,
   la spécification approuvée, la revue finale, les AC, les décisions résolues,
   les preuves de stack, les candidats précédents et le rôle complet.
2. Appeler `delegate_task` avec un objectif d'analyse Epic, le contrat de sortie
   embarqué et `max_iterations: 30`.
3. En full-stack, lancer les deux analyses dans un même lot. Autoriser leur
   parallélisme uniquement parce que les enfants restent en lecture seule.
4. Exiger `files_modified: []`. Arrêter et signaler toute écriture enfant.
5. Faire remonter les questions ; ne jamais demander au sous-agent d'interroger
   l'utilisateur ni de choisir une option absente des sources.

Les IDs `S-NNN` des enfants sont locaux à leur rôle. L'agent principal les
normalise globalement selon `references/epic-contract.md`. Traiter également
chaque `Q-NNN` enfant comme local : qualifier d'abord son origine, refuser les
doublons locaux, puis attribuer un ID global stable sans collision.

## Production des candidats

Après le retour des délégations :

1. refuser un résultat `ready` contenant une question ouverte ;
2. avec `needs-input`, écrire seulement
   `03-epic-design.candidate.md`, consigner les `Q-NNN` stables et demander les
   décisions ; ne produire ni roadmap finale ni approbation ;
3. avec `ready`, faire écrire uniquement par l'agent principal :
   - `03-epic-design.candidate.md` ;
   - `03a-epic-roadmap.candidate.md` ;
4. préserver les artefacts finaux existants ;
5. exécuter `scripts/epic_plan_guard.py validate-candidates` ;
6. présenter stacks, rôles, décisions, risques, tranches, dépendances et
   couverture des AC ;
7. demander une réponse exacte `approve` ou `request-changes`, puis arrêter le
   tour sans promouvoir les candidats.

L'agent principal reste l'unique écrivain. Ne créer aucun ADR séparé pendant
cette étape : consigner les candidats ADR dans la conception Epic, puis les
matérialiser dans le plan détaillé de la tranche concernée.

## Décision explicite

Finaliser uniquement après une nouvelle réponse utilisateur explicite, ou avec
`--continue <feature-id> --decision <valeur>` sur des candidats déjà valides.

- Ne jamais déduire une approbation du lancement de la commande, d'une ancienne
  décision, de `continue`, du retour d'un sous-agent ou de l'absence de réponse.
- Avec `request-changes`, attribuer un `CR-NNN` stable à chaque demande, le
  laisser `open`, puis appeler `epic_plan_guard.py decide` avec la preuve exacte.
  Conserver les candidats et proposer `--continue`.
- Avec `approve`, exiger zéro question et zéro `CR-NNN` ouverts, puis appeler
  `epic_plan_guard.py decide` avec le token capturé, l'acteur, l'horodatage et la
  preuve exacte `approve`.
- N'annoncer l'approbation qu'après `committed: true`.

Le garde applique un verrou, une comparaison-et-échange, un journal durable et
une promotion transactionnelle vers `03-epic-design.md` et
`03a-epic-roadmap.md`. Ne jamais renommer ou remplacer ces fichiers directement.

## Reprise et idempotence

Avec `--continue` :

1. exécuter `snapshot` en premier ; il termine ou annule toute transaction
   interrompue avant de retourner le token courant ;
2. conserver les `Q-NNN`, `CR-NNN`, `S-NNN`, le `high_water_mark` et les
   `retired_ids` existants ;
3. déplacer les questions résolues vers `Resolved Questions` avec réponse et
   date ;
4. relancer uniquement les rôles affectés, toujours en lecture seule ;
5. régénérer les candidats complets et les revalider ;
6. réutiliser le même appel `decide` après une interruption. Un reçu identique
   rend l'opération idempotente ; un contenu ou token différent est refusé.

## Contraintes

- Écrire uniquement dans `.specs/<feature-id>/`.
- Ne modifier ni code, tests, dépendances, configuration, Kanban, VPS ou profil
  Hermes.
- Préférer des tranches verticales visibles, testables et livrables.
- Ne pas détailler les `T-NNN` ; chaque tranche approuvée passe ensuite à
  `/sdd-plan`.
- Couvrir chaque `AC-NNN` exactement dans la matrice de couverture et au moins
  une fois dans le backlog.
- Refuser les doublons d'IDs, dépendances inconnues et cycles de tranches.

## Terminé lorsque

- les deux artefacts finaux existent et `03-epic-design.md` contient
  `decision: approve` ;
- le champ canonique `decision: approve` appartient uniquement à
  `03-epic-design.md` ; la roadmap référence ce fichier final et n'invente pas
  une seconde décision ;
- aucune question ou demande de changement ouverte ne subsiste ;
- chaque AC est couverte et le graphe des tranches est acyclique ;
- chaque délégation déclare n'avoir modifié aucun fichier ;
- la prochaine commande est `/sdd-plan <feature-id>` pour la première tranche
  sans dépendance non satisfaite.
