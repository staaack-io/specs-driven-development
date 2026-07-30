# Test E2E SDD avec Hermes 0.19.0

`run_sdd_e2e.py` reproduit le début du workflow SDD dans un projet full-stack
jetable. Il ne remplace pas une approbation humaine et ne lance ni build, ni
test applicatif, ni déploiement.

## Périmètre vérifié

Le runner exécute dans cet ordre :

1. `/sdd-help` ;
2. `/sdd-status` ;
3. `/sdd-spec` sur une fixture Spring Boot + React/Next.js ;
4. `/sdd-spec-review` et vérification du verdict provisoire
   `ready-for-approval` ;
5. `approve` dans un processus et un tour séparés ;
6. `/sdd-plan` avec les deux rôles `spring-architect` et
   `react-nextjs-architect` ;
7. export redacted des sessions et validation déterministe des artefacts.

Le test s'arrête aux candidats `03-design.candidate.md` et
`04-tasks.candidate.md`. Il refuse la création de `.tdd-state.json` ou des
artefacts approuvés : l'approbation du plan reste une décision humaine hors du
test.

## Pourquoi deux modes Hermes

Hermes 0.19.0 expose l'identifiant exact d'une commande
`hermes chat -Q -q` sur stderr. Les cinq premiers tours utilisent donc ce mode,
puis reprennent explicitement la session avec `--resume <session-id>`. Le
runner n'utilise jamais `--continue`, qui pourrait sélectionner une autre
session.

Une délégation `delegate_task` lancée par le CLI classique est asynchrone. Un
processus `chat -q` peut quitter avant ses enfants et perdre leur travail.
Hermes 0.19.0 prévoit `hermes -z` pour les appels stateless : dans ce mode, la
délégation devient synchrone. Le runner utilise donc `-z` uniquement pour
`/sdd-plan`, récupère son identifiant exact via `--usage-file`, puis exporte
cette session par ID.

Références de compatibilité : release Hermes 0.19.0, commit
`3ef6bbd201263d354fd83ec55b3c306ded2eb72a` (tag `v2026.7.20`).

## Garde-fous

- profil Hermes minimal : `0.4.7` ;
- Hermes minimal : `0.19.0` ;
- dossier créé exclusivement avec `mktemp` sous une racine résolue et validée ;
- verrou non bloquant par profil et binaire ;
- aucun `shell=True` ;
- groupe de processus dédié et terminaison du groupe au timeout ;
- comparaison des empreintes après chaque tour : toute écriture hors `.specs`
  fait échouer le test ;
- liens symboliques interdits sous `.specs` ;
- logs et projet conservés par défaut, et toujours conservés en cas d'échec ;
- suppression possible uniquement avec `--cleanup-on-success`, après succès,
  et après validation du chemin réel, du préfixe et d'une sentinelle UUID ;
- export de session avec `--redact` ;
- preuve `delegate_task`, présence des deux rôles, couverture des AC et unicité
  des Task-IDs/Test-IDs.

L'acteur qui répond `approve` est enregistré comme `automated-e2e` avec
`approval_is_human: false`. Le test échoue si le rapport attribue cette décision
à `utilisateur` ou à un humain. Une exécution verte prouve donc le mécanisme de
porte, pas une vraie approbation métier.

## Exécution

Prévisualisation sans exécuter Hermes et sans créer de dossier :

```bash
python3 hermes/e2e/run_sdd_e2e.py \
  --profile staaack \
  --hermes-bin hermes \
  --dry-run
```

Exécution réelle, seulement après publication et installation du profil
`>=0.4.7` :

```bash
hermes profile info staaack
python3 hermes/e2e/run_sdd_e2e.py \
  --profile staaack \
  --hermes-bin hermes
```

Le JSON final contient les chemins `run_dir` et `project`, les IDs de session et
les validations. En cas d'échec, consulter `run_dir/logs/failure.json` puis les
logs de chaque étape. Pour supprimer automatiquement un bac à sable uniquement
après un succès complet :

```bash
python3 hermes/e2e/run_sdd_e2e.py \
  --profile staaack \
  --hermes-bin hermes \
  --cleanup-on-success
```

Options utiles :

- `--timeout 900` : délai maximal de chaque processus Hermes ;
- `--temp-root /chemin/temporaire` : racine autorisée pour `mktemp` ;
- `--feature-id YYYY-MM-DD-slug` : identifiant stable, au plus 40 caractères.

## Tests unitaires

Les tests utilisent un faux binaire Hermes et n'appellent aucun LLM :

```bash
python3 -m unittest discover -s hermes/e2e -p 'test_*.py' -v
```

Ils couvrent le flux complet, le tour d'approbation séparé, la reprise par ID,
le dry-run, la version minimale, la détection d'une écriture applicative, la
conservation en échec, le timeout de groupe et le nettoyage opt-in.
