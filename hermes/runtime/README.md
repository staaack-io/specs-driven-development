# Socle runtime SDD partagé

`sdd_runtime_guard.py` fournit les contrôles déterministes communs aux skills
Hermes qui exécuteront le workflow. Il ne lance aucun agent et ne remplace pas
le Kanban Hermes. Les orchestrateurs l'appellent autour de chaque délégation.

## Invariants

- l'état v2 reste lisible par les consommateurs v1 et ne contient aucun secret,
  transcript, token CAS ou chemin absolu ;
- le DAG, les Task-IDs, Test-IDs et `files_in_scope` sont validés avant une
  écriture ;
- les globs, traversées, chaînes de symlinks et chevauchements sans dépendance
  sont refusés ;
- les worktrees partagent un verrou et un registre de leases dans le Git common
  dir ; deux scopes disjoints peuvent garder un lease simultanément, un conflit
  attend la libération du premier ;
- chaque lease est lié à une session, un PID et son temps de naissance ; son
  heartbeat prolonge un TTL borné et un lease expiré ou orphelin est récupéré ;
- un worker écrit son code ou ses tests dans son scope et un événement immuable
  sous `.specs/<feature-id>/jobs/<T-ID>/`, jamais les artefacts partagés ;
- le synthesizer est le seul acteur autorisé à publier `04-tasks.md`,
  `.tdd-state.json` et `05-implementation-log.md` par fan-in transactionnel ;
- les fingerprints avant/après démontrent qu'aucun fichier extérieur à la vague
  n'a changé, y compris un fichier ignoré, son mode ou sa version dans l'index ;
- les questions ouvertes, la preuve RED et les arguments de contournement sont
  des portes structurées, et non des instructions supposées respectées.

## Reprise transactionnelle

Le fan-in est namespacé par dépôt et worktree, et lié au `HEAD` observé. Il
écrit d'abord un journal synchronisé dans le Git common dir, puis les artefacts
et enfin un marqueur de commit authentifiant le journal et les empreintes
cibles. Une reprise sans marqueur réinstalle l'ensemble précédent. Une reprise
avec marqueur réinstalle l'ensemble cible. Elle refuse un autre worktree, un
autre `HEAD`, un marqueur altéré ou un artefact dont l'empreinte ne correspond
ni à l'ancienne ni à la nouvelle version.

Le même `transaction_id` et le même contenu rendent un retry idempotent. Un
contenu différent ou un token CAS périmé échoue sans écraser l'état courant.
Les journaux et receipts ne contiennent que des chemins relatifs au dépôt.

## Migration de l'état

Le CLI sépare la capture CAS de l'écriture. Il faut conserver les deux tokens
retournés par la première commande et les fournir sans les transformer :

```bash
python3 hermes/runtime/sdd_runtime_guard.py validate-state \
  --repo-root . \
  --state .specs/<feature-id>/.tdd-state.json

python3 hermes/runtime/sdd_runtime_guard.py migration-snapshot \
  --repo-root . \
  --feature-id <feature-id>

python3 hermes/runtime/sdd_runtime_guard.py migrate-state \
  --repo-root . \
  --state .specs/<feature-id>/.tdd-state.json \
  --output .specs/<feature-id>/.tdd-state.candidate.json \
  --expected-token '<source_token>' \
  --expected-output-token '<output_token>'
```

La migration accepte uniquement la source et la cible canoniques sous le dépôt,
les protège avec le verrou commun, vérifie les deux tokens et produit un
candidat v2 par remplacement atomique. Elle ne remplace jamais l'état actif et
signale `migration.contract_complete: false`, car le schéma v1 ne contenait ni
les dépendances ni les Test-IDs. Cet état incomplet ne peut obtenir aucun lease,
passer la porte RED ou entrer dans un fan-in. Le synthesizer doit compléter ces
preuves à partir de `04-tasks.md` avant le fan-in.

Chaque événement task-local est lié à un manifeste immuable placé dans le Git
common dir. Une modification, une suppression ou un fichier non manifesté est
détecté avant le prochain append et lors de la vérification finale.
