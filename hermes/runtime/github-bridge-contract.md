# Contrat du bridge Kanban–GitHub

Le bridge est une surface interne déclenchée par les transitions d'un job déjà
admis. Le Kanban natif Hermes 0.19 reste l'unique ordonnanceur durable. Le
module ne contient donc ni boucle d'admission, ni tâche planifiée, ni commande
de fusion.

## Préconditions d'un job

`start_job` accepte un job qui fournit explicitement `feature_id`, `task_id`,
`kanban_id`, `branch`, `idempotency_key`, `state_revision`,
`active_writer_count`, `runtime_contract_merged` et
`synchronized_with_main`. La clé d'idempotence est exactement
`<feature_id>:<task_id>`. Le bridge refuse un troisième writer, un contrat
runtime non fusionné ou une branche non resynchronisée avec `main`.

## Adaptateurs structurés

- L'adaptateur GitHub crée une issue et une pull request brouillon, rend la PR
  prête, lit checks, reviews et fils, répond à un fil précis et demande une
  nouvelle review. Il ne propose aucune opération de fusion.
- L'adaptateur d'état lit les identifiants déjà enregistrés, les écrit par CAS,
  conserve l'instant du dernier polling et l'attente de review.
- L'adaptateur Kanban enregistre les identifiants externes et change l'état de
  la carte. Il n'admet aucun job.
- L'adaptateur worker applique une correction sur la branche déjà associée au
  job. Il ne crée pas de branche.
- L'horloge est injectée ; aucune attente bloquante n'existe dans le module.

Les appels utilisent des arguments nommés. L'implémentation d'un adaptateur
`gh` peut employer le CLI GitHub avec une liste d'arguments structurée, jamais
une commande shell composée. Aucun secret, transcript ou chemin absolu ne doit
entrer dans l'état ou les journaux.

## Transitions et reprise

Après les tests verts, `mark_ready` rend uniquement la PR brouillon prête et
place la carte en attente de review. `poll_pull_request` effectue au plus une
observation due toutes les cinq minutes : checks, reviews et fils sont lus au
même instant logique. Trente minutes après le début de l'attente sans review,
la carte et l'état passent à `needs_input`.

Une correction conserve la branche, répond au `thread_id` exact, demande une
nouvelle review puis redémarre la fenêtre d'attente. La reprise relit d'abord
les identifiants de l'état. Si le CAS avait réussi avant une interruption de
l'écriture Kanban, le même appel répare la carte sans recréer issue ou PR et
sans second CAS.

La fusion reste une gate humaine extérieure au bridge.
