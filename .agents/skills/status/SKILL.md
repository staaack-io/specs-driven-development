---
name: status
description: "Afficher la phase courante et la prochaine action des fonctionnalités SDD. Utiliser lorsque l’utilisateur invoque $status ou demande l’état du workflow."
---

# $status

**Phase :** méta — lecture seule
**Agent responsable :** aucun

## Objectif

Montrer la position de chaque fonctionnalité active, sans écriture ni effet de
bord.

## Entrées

- `<feature-id>` facultatif ; sinon résumer toutes les fonctionnalités.

## Lectures

- artefacts numérotés, état TDD et dernier rapport ;
- `target/harness-summary.json` s’il existe.

## Écritures

Aucune.

## Processus

Pour chaque fonctionnalité, afficher une ligne avec :

- `feature_id` ;
- `phase`, déduite des artefacts et verdicts ;
- `acs_total` et `acs_with_tests` ;
- `tasks_done / tasks_total` ;
- dernier verdict et horodatage ;
- `active_task` et sa phase.

Terminer par une phrase indiquant l’action suivante recommandée.

## Refuser si

Jamais. Afficher `—` lorsqu’une donnée manque.

## Terminé lorsque

La table et la prochaine commande sont affichées.
