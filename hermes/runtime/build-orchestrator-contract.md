# Contrat d'admission parallèle `/sdd-build`

`/sdd-build <feature-id> --parallel [--max-workers 1|2]` effectue une seule
passe d'admission. L'absence de `--max-workers` vaut `2`; toute autre valeur que
`1` ou `2` est refusée avant mutation.

## Autorité et barrières

- T-009 doit être observée `done` et fusionnée avant l'admission parallèle.
- `sdd_runtime_guard.validate_state` reste l'autorité du schéma v2, du DAG, des
  dépendances et des scopes concrets.
- Le Kanban Hermes est l'unique surface de dispatch. L'orchestrateur ne crée ni
  boucle concurrente, ni pool de threads, ni ordonnanceur de jobs secondaire.

## Vague et capacité

Les tâches `pending` ou `ready`, dont toutes les dépendances sont `done` et
fusionnées, sont parcourues dans l'ordre stable de leur identifiant. Deux scopes
disjoints peuvent rejoindre la même vague. Un chevauchement est sérialisé et ne
reçoit aucun lease dans cette passe.

Chaque tâche admise reçoit idempotemment une carte avec le projet, le board, la
carte parente, la branche, la clé `<feature-id>:<task-id>`, le skill
`sdd-build`, `max-runtime=45m` et deux retries. Toutes les cartes de la vague
sont créées, mais seulement `max_workers` leases sont acquis et dispatchés ; les
autres restent en file sans mutation de worker.

## Isolation d'échec

Une erreur de dispatch place uniquement la carte concernée en `failed` et
libère uniquement son lease. Les autres cartes et leases restent actifs. Les
logs, journaux et surfaces de travail ne sont ni supprimés ni réinitialisés.
