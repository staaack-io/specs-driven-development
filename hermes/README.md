# Adaptateur Hermes Agent

Ce dossier contient la source de l'adaptateur Hermes du framework SDD. Il est
développé séparément de l'intégration Codex existante afin de permettre une
migration progressive et des comparaisons fiables.

## Skills convertis

Les skills suivants sont prêts à être copiés dans la distribution
`staaack-io/hermes-agent-profile-staaack` :

- `sdd-onboard` — inspection statique, délégation en lecture seule et
  publication transactionnelle des cinq artefacts globaux ;
- `sdd-wire-harness` — détection et câblage transactionnel du harness ;
- `sdd-epic-plan` — conception globale et roadmap d'une Epic ;
- `sdd-help` — aide en lecture seule ;
- `sdd-status` — état des fonctionnalités en lecture seule ;
- `sdd-spec` — création guidée de `01-spec.md` ;
- `sdd-spec-review` — revue avec décision utilisateur et production de
  `02-spec-review.md` ;
- `sdd-plan` — conception et tâches avec délégation interne à l'architecte
  Spring ou React/Next.js ;
- `sdd-build` — cycle TDD mono-tâche, admission parallèle bornée, enveloppes
  isolées et fan-in transactionnel après autorisation humaine observée.

Les hooks ne font volontairement pas partie de ce lot. Ils seront activés après
leur conversion au protocole Hermes et la réussite de tests de blocage.

Le socle déterministe partagé vit sous `hermes/runtime/`. Il remplace les
suppositions liées aux hooks Codex par des appels explicites : validation de
l'état v2, DAG, Test-IDs, scopes et preuve RED, leases entre worktrees,
fingerprints, journaux task-local et fan-in transactionnel. `/sdd-build` appelle
ce socle pour chaque transition ; les futurs skills d'écriture font de même au
lieu de réimplémenter ces invariants.

## Étapes du workflow

| Étape | Objectif | Commandes Hermes |
| --- | --- | --- |
| 0 | Intégrer un projet existant | `/sdd-onboard` |
| 0 | Brancher le harness | `/sdd-wire-harness` |
| 1 | Spécifier | `/sdd-spec` |
| 2 | Relire la spécification | `/sdd-spec-review` |
| 3a | Concevoir une Epic, si nécessaire | `/sdd-epic-plan` |
| 3 ou 3b | Concevoir et découper en tâches | `/sdd-plan` |
| 4 | Implémenter en TDD | `/sdd-build` |
| 5 | Ajouter les tests transverses | `/sdd-test` |
| 6 | Valider avec le harness | `/sdd-validate` |
| 7 | Relire le code avant commit | `/sdd-review` |
| 8 | Préparer la livraison, facultatif | `/sdd-ship` |

`/sdd-help` et `/sdd-status` sont des commandes méta disponibles à tout moment.
`/sdd-code-simplify` reste planifiée séparément pour S-004.

## Rôles internes et délégation

Un rôle interne n'est pas une nouvelle étape ni une commande à mémoriser. C'est
une fiche d'instructions que l'orchestrateur fournit à un sous-agent pour lui
confier une partie précise du travail.

Exemple pendant l'étape 4 :

1. `/sdd-build <feature-id> T-001` reste l'unique commande saisie par
   l'utilisateur ;
2. l'orchestrateur charge le rôle `spring-test-engineer` et délègue l'écriture
   du test rouge ;
3. après validation de l'échec, il charge `spring-implementer` et délègue le
   code minimal ;
4. les délégations restent séquentielles pour éviter deux écritures concurrentes
   dans `05-implementation-log.md` ou `.tdd-state.json`.

Le nom de travail `sdd-roles` désigne cette bibliothèque interne. Il ne doit pas
être présenté comme une commande utilisateur `/sdd-roles`.

Pour `/sdd-plan`, les deux premières fiches de rôle sont embarquées directement
dans les références du skill. Les sous-agents analysent en lecture seule ;
l'agent principal reste l'unique auteur de `03-design.md`, `04-tasks.md` et
`.tdd-state.json`.

Pour `/sdd-onboard`, les rôles `spring-onboarding` et
`react-nextjs-onboarding` décrivent chacun leur stack en lecture seule. Ils
retournent `files_modified: []`. L'agent principal consolide les résultats puis
un garde atomique publie ensemble `_onboarding.md`, `_stack.json`,
`_baseline.json`, `_starter-design.md` et `_known-debt.md`. Le câblage du
harness reste une étape séparée.

## Publication dans le profil

Le contenu de `hermes/skills/<nom>/` devient
`skills/<nom>/` dans le dépôt de distribution Hermes. Les dossiers de ressources
restent avec leur skill afin que le profil installé soit autonome.

Le dossier `hermes/skills/` de ce dépôt est la source canonique. Avant de publier
le profil, vérifier la parité exacte des deux arborescences depuis cette racine :

```bash
python3 hermes/scripts/check_profile_parity.py \
  /chemin/vers/hermes-agent-profile-staaack
```

Le contrôle échoue si un fichier manque, si le profil contient un fichier en
plus ou si le contenu d'un fichier diffère.

Cette parité entre deux dépôts reste une gate locale obligatoire avant
publication du profil ; elle n'est pas exécutée par GitHub Actions dans ce
dépôt, qui ne dispose volontairement ni du checkout ni des secrets du profil.

Ne pas utiliser un lien direct vers `.agents/skills/` : ce dossier contient la
version Codex et ses chemins ne sont pas tous portables vers Hermes.

## Validation locale

Depuis la racine du dépôt :

```bash
python3 /chemin/vers/skill-creator/scripts/quick_validate.py hermes/skills/sdd-onboard
python3 /chemin/vers/skill-creator/scripts/quick_validate.py hermes/skills/sdd-help
python3 /chemin/vers/skill-creator/scripts/quick_validate.py hermes/skills/sdd-status
python3 /chemin/vers/skill-creator/scripts/quick_validate.py hermes/skills/sdd-spec
python3 /chemin/vers/skill-creator/scripts/quick_validate.py hermes/skills/sdd-spec-review
python3 -m unittest -v \
  hermes/skills/sdd-onboard/scripts/test_onboarding_guard.py \
  hermes/skills/sdd-onboard/scripts/test_skill_contract.py \
  hermes/skills/sdd-spec-review/scripts/test_review_decision_guard.py
```

Le test de la porte humaine vérifie qu'une première revue réussie reste
`ready-for-approval` et qu'une décision finale conserve une preuve utilisateur
explicite. `/sdd-plan` et `/sdd-status` rejettent un ancien rapport final qui ne
contient pas cette preuve.

La validation avec Hermes sur le VPS reste obligatoire avant publication d'une
version stable du profil.

Le runner CI `hermes/scripts/run_python_tests.py` isole les fichiers de test et
échoue en cas de timeout ou de protocole incomplet. Sous Linux, le mécanisme
`child-subreaper` du noyau permet aussi de retrouver les descendants détachés.
Sous les autres systèmes POSIX, le nettoyage des descendants ordinaires repose
sur un marqueur privé hérité par `fork` et `exec` : c'est une protection contre
les fuites accidentelles, pas une sandbox. Un programme exécuté avec le même
utilisateur peut volontairement effacer ce marqueur et sortir de ce périmètre ;
les tests hostiles exigent alors une sandbox ou un contrôle de jobs fourni par
le système d'exploitation.

Avant chaque fichier de test, le runner vérifie que l'énumérateur requis est
disponible (`/proc` sous Linux, `ps` sur les autres POSIX). Il refuse de démarrer
le fichier si cette porte échoue, plutôt que d'exécuter un descendant qu'il ne
pourrait ensuite garantir de nettoyer.

Le registre de secours ne considère jamais un PID comme une identité suffisante.
Le worker transmet aussi le temps de naissance du processus (`/proc` sous Linux,
`libproc` sous Darwin). L'outer le revalide avant tout signal ; sous Linux, il
ouvre en plus un `pidfd` et signale ce handle stable. Si l'identité ne correspond
plus, le PID a disparu ou a été réutilisé et aucun signal ne lui est envoyé.
Ce nettoyage est appliqué aux timeouts comme à toute sortie worker non nulle ou
à tout protocole de résultat incomplet.

La même règle s'applique aux descendants énumérés. Linux recoupe deux snapshots
d'ascendance et de temps de naissance autour de l'ouverture du `pidfd`, puis ne
signale que ce handle. Les descendants POSIX marqués sont revalidés par token et
temps de naissance immédiatement avant chaque `SIGSTOP` ou `SIGKILL`.
Sous Linux, cette énumération reste obligatoire après la mort du worker :
l'outer `child-subreaper` récupère et nettoie aussi les daemons que le subreaper
intermédiaire avait adoptés avant de disparaître.
