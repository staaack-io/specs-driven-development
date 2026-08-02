---
name: sdd-status
description: "Résumer l'état des fonctionnalités SDD."
---

# État du workflow SDD

Cette commande est strictement en lecture seule. Ne créer, modifier ou supprimer
aucun fichier.

## Entrée

- un `feature-id` facultatif ;
- sans argument, analyser tous les sous-dossiers de `.specs/`, sauf les fichiers
  et dossiers dont le nom commence par `_`.

Si `.specs/` n'existe pas, l'indiquer et recommander `/sdd-onboard`.

## État de l'onboarding

Avant les fonctionnalités, vérifier en lecture seule l'ensemble global :

- `_onboarding.md` ;
- `_stack.json` ;
- `_baseline.json` ;
- `_starter-design.md` ;
- `_known-debt.md`.

Si l'ensemble est partiel, si un JSON est invalide ou si les deux JSON ne
portent pas le même `git_sha`, annoncer « onboarding incomplet » et recommander
`/sdd-onboard --continue`. Ne jamais réparer ces fichiers depuis `/sdd-status`.

Si l'ensemble est complet, résumer séparément :

- classification ;
- SHA inspecté ;
- nombre de modules ;
- niveau de confiance ;
- état de baseline, qui peut légitimement valoir `not-run`.

Si les cinq artefacts sont absents mais que des fonctionnalités existent déjà,
signaler « onboarding non capturé » sans masquer leur état. Recommander
`/sdd-onboard` comme prochaine action uniquement si aucune phase de
fonctionnalité plus urgente n'est bloquée.

Lorsque l'onboarding est complet et qu'aucun dossier de fonctionnalité
n'existe, recommander `/sdd-spec <demande ou ticket>`.

## Sources

Pour chaque fonctionnalité, lire si présents :

- les artefacts numérotés de `01-spec.md` à `09-ship-plan.md` ;
- `03-design.candidate.md` et `04-tasks.candidate.md` ;
- `.tdd-state.json` ;
- `target/harness-summary.json` à la racine du projet.

Pour un état contenant des tâches, appliquer
`references/kanban-state-contract.md` et utiliser
`scripts/status_guard.py` pour construire la vue task-local.

Une donnée absente vaut `—`. Ne pas la déduire si les fichiers ne la prouvent
pas.

## Vue task-local

Pour chaque tâche, afficher une ligne contenant, dans cet ordre :

- l'identifiant de tâche ;
- l'issue ;
- la branche ;
- la pull request ;
- les checks ;
- la review ;
- le blocage ;
- la prochaine action.

Les états v1 restent lisibles : chacun des sept champs task-local absent vaut
`—`. Pour un état v2, recopier uniquement les valeurs présentes dans la tâche.
En particulier, ne jamais fabriquer une prochaine action depuis la phase, le
statut ou le blocage. La lecture ne lance aucune commande GitHub ou Hermes et
ne modifie aucun fichier.

## Détermination de la phase

Choisir la dernière phase prouvée par un artefact valide :

1. `01-spec.md` : spécification ;
2. `02-spec-review.md` avec verdict `approve` et preuve finale acceptée par
   `../sdd-spec-review/scripts/review_decision_guard.py validate-final` :
   spécification approuvée ; si le garde est absent ou échoue, traiter la revue
   comme en attente et recommander `/sdd-spec-review --continue <feature-id>` ;
3. `03-design.md` et `04-tasks.md` avec `status: approved` et
   `.tdd-state.json` : planification approuvée ;
4. `.tdd-state.json` avec une tâche active : implémentation ;
5. `06-test-plan.md` : tests ;
6. `07-validation-report.md` : validation ;
7. `08-code-review.md` : revue ;
8. `09-ship-plan.md` : préparation de livraison.

Lorsqu'au moins un candidat de planification existe, lire les candidats avant
les versions approuvées de `03-design.md` et `04-tasks.md`. Ils représentent la
révision courante : un ancien plan approuvé et son état TDD ne prouvent pas que
cette nouvelle révision est approuvée.

Un artefact présent mais contenant une question `Q-NNN` au statut `open`, ou un
verdict négatif, bloque le passage à la phase suivante.

Dès qu'au moins un candidat de planification existe, examiner l'état TDD avant
son statut ou son verdict. Si une tâche est active, non `pending`, ou contient
une preuve RED/GREEN, signaler le conflit entre la révision candidate et
l'implémentation commencée, quel que soit le statut du candidat ; ne pas proposer
`--continue` et recommander une nouvelle demande distincte via
`/sdd-spec <demande>`.

Si l'état TDD est absent ou vierge, un candidat avec `status: draft` signifie
toujours « planification en attente d'approbation », même sans question ouverte
ni verdict négatif. Une question ouverte ou un verdict négatif impose le même
statut. Un autre candidat non publié reste en attente de finalisation. Ne pas
annoncer une planification terminée et recommander
`/sdd-plan --continue <feature-id>`.

## Sortie

Afficher un tableau contenant :

- `feature_id` ;
- phase ;
- nombre total d'`AC-NNN` et nombre relié à un test ;
- tâches terminées sur tâches totales ;
- dernier verdict et son horodatage ;
- tâche active et phase TDD.

Sous la ligne de la fonctionnalité, afficher le tableau task-local défini
ci-dessus lorsqu'un état contient des tâches.

Terminer par une seule prochaine action recommandée. Utiliser les commandes
Hermes préfixées `/sdd-`. Si la commande nécessaire n'est pas encore installée,
le signaler au lieu de proposer une commande inexistante.
