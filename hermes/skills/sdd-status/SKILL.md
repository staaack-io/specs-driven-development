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

Si `.specs/` n'existe pas, l'indiquer et recommander `/sdd-spec`.

## Sources

Pour chaque fonctionnalité, lire si présents :

- les artefacts numérotés de `01-spec.md` à `09-ship-plan.md` ;
- `03-design.candidate.md` et `04-tasks.candidate.md` ;
- `.tdd-state.json` ;
- `target/harness-summary.json` à la racine du projet.

Une donnée absente vaut `—`. Ne pas la déduire si les fichiers ne la prouvent
pas.

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

Terminer par une seule prochaine action recommandée. Utiliser les commandes
Hermes préfixées `/sdd-`. Si la commande nécessaire n'est pas encore installée,
le signaler au lieu de proposer une commande inexistante.
