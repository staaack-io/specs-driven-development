# Contrat de lecture de l'état Kanban

## But

`/sdd-status <feature-id>` expose les preuves task-local sans devenir un writer
du workflow. La source est le dictionnaire `tasks` de l'état SDD lu sur disque.

## Champs affichés

Chaque ligne contient `task_id`, puis les sept champs suivants :

| Champ | Preuve recopiée |
| --- | --- |
| `issue` | identifiant de l'issue de tâche |
| `branch` | nom de la branche isolée |
| `pr` | identifiant de la pull request |
| `checks` | état des checks |
| `review` | état de la review |
| `blocking` | blocage prouvé |
| `next_action` | prochaine action déjà enregistrée |

Les lignes sont triées par `task_id` afin que deux lectures du même état
produisent la même sortie.

## Compatibilité v1/v2

- Un état v2 peut porter les sept champs directement dans chaque tâche.
- Un état v1 reste accepté en lecture.
- Tout champ absent vaut `—`, indépendamment de la version.
- Une valeur présente est recopiée telle quelle.
- Aucun champ n'est déduit de `phase`, `status`, d'un autre champ ou d'un appel
  externe.

## Lecture seule

Le garde `scripts/status_guard.py` charge éventuellement le JSON par
`task_local_rows_from_file`, puis rend les lignes avec `task_local_rows`. Il
n'écrit pas le fichier, ne répare pas l'état et n'exécute aucune commande. Une
empreinte de tous les fichiers du dépôt doit donc être identique avant et après
la lecture.
