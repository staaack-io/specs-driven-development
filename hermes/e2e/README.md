# Test E2E SDD avec Hermes 0.19.0

`run_sdd_e2e.py` reproduit le workflow SDD complet dans un projet full-stack
jetable. Il n'appelle aucun réseau, VPS ou déploiement et ne sollicite aucun
reviewer humain.

## Périmètre vérifié

Le runner exécute dans cet ordre :

1. `/sdd-help`, `/sdd-status`, `/sdd-onboard` et `/sdd-wire-harness` ;
2. `/sdd-spec` sur une fixture Spring Boot + React/Next.js ;
3. `/sdd-spec-review` et vérification du verdict provisoire
   `ready-for-approval` ;
4. `approve` dans un processus et un tour séparés ;
5. `/sdd-epic-plan` puis `/sdd-plan` avec les deux rôles `spring-architect` et
   `react-nextjs-architect` ;
6. les scénarios locaux T-025 et T-026 avant leurs commandes dépendantes ;
7. `/sdd-build`, `/sdd-code-simplify`, `/sdd-test`, `/sdd-validate`,
   `/sdd-review` et `/sdd-ship` ;
8. export redacted des sessions et agrégation des preuves relatives.

La réponse `approve` est celle de l'acteur synthétique `automated-e2e`. Elle
prouve uniquement la porte de décision du bac à sable et ne représente jamais
une approbation humaine. Le runner observe aussi la fusion et le go du fan-in
comme des données locales, sans exécuter de merge.

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
- rapport final limité au nom relatif du run et à des chemins de preuve relatifs ;
- enveloppes distinctes issue, carte, branche, worktree, session et PR ;
- reprise explicite d'un run conservé, sans nouvel appel LLM ;
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

Le JSON final contient le nom relatif `run_dir`, les IDs de session, les
enveloppes et les validations. En cas d'échec, consulter
`<temp-root>/<run_dir>/logs/failure.json` puis les logs de chaque étape. Pour
supprimer automatiquement un bac à sable uniquement
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
- `--resume-run sdd-hermes-e2e-xxxxxxxx` : inspecter explicitement un run
  conservé sous `--temp-root`, sans LLM et sans mutation.

## Tests unitaires

Les tests utilisent un faux binaire Hermes et n'appellent aucun LLM :

```bash
python3 -m unittest discover -s hermes/e2e -p 'test_*.py' -v
```

Ils couvrent le flux complet, le tour d'approbation séparé, la reprise par ID,
le dry-run, la version minimale, la détection d'une écriture applicative, la
conservation en échec, le timeout de groupe et le nettoyage opt-in.

## Revalider un run préservé sans appel LLM

Après une mise à jour du runner, un run conservé peut être revalidé sans
réexécuter Hermes. Le chemin du run, le feature-id et le transcript exact de la
session `/sdd-plan` doivent être fournis explicitement :

```bash
python3 hermes/e2e/run_sdd_e2e.py \
  --validate-run /tmp/sdd-hermes-e2e-xxxxxxxx \
  --feature-id YYYY-MM-DD-service-state-e2e \
  --plan-transcript /tmp/sdd-hermes-e2e-xxxxxxxx/logs/session-NN-SESSION_ID.jsonl
```

Ce mode refuse un run sans sentinelle valide, un chemin réel incohérent, un
transcript symbolique ou extérieur au dossier `logs/`, et tout transcript dont
le nom ne correspond pas à `session-*.jsonl`. Il n'écrit rien dans le run et
n'appelle ni Hermes ni un LLM.
