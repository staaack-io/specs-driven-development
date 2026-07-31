# Adaptateur Hermes Agent

Ce dossier contient la source de l'adaptateur Hermes du framework SDD. Il est
développé séparément de l'intégration Codex existante afin de permettre une
migration progressive et des comparaisons fiables.

## Skills convertis

Les skills suivants sont prêts à être copiés dans la distribution
`staaack-io/hermes-agent-profile-staaack` :

- `sdd-help` — aide en lecture seule ;
- `sdd-status` — état des fonctionnalités en lecture seule ;
- `sdd-spec` — création guidée de `01-spec.md` ;
- `sdd-spec-review` — revue avec décision utilisateur et production de
  `02-spec-review.md` ;
- `sdd-plan` — conception et tâches avec délégation interne à l'architecte
  Spring ou React/Next.js.

Les hooks ne font volontairement pas partie de ce lot. Ils seront activés après
leur conversion au protocole Hermes et la réussite de tests de blocage.

## Étapes du workflow

| Étape | Objectif | Commandes Hermes |
| --- | --- | --- |
| 0 | Intégrer un projet existant | `/sdd-onboard`, `/sdd-wire-harness` |
| 1 | Spécifier | `/sdd-spec` |
| 2 | Relire la spécification | `/sdd-spec-review` |
| 3a | Concevoir une Epic, si nécessaire | `/sdd-epic-plan` |
| 3 ou 3b | Concevoir et découper en tâches | `/sdd-plan` |
| 4 | Implémenter en TDD | `/sdd-build`, `/sdd-code-simplify` |
| 5 | Ajouter les tests transverses | `/sdd-test` |
| 6 | Valider avec le harness | `/sdd-validate` |
| 7 | Relire le code avant commit | `/sdd-review` |
| 8 | Préparer la livraison, facultatif | `/sdd-ship` |

`/sdd-help` et `/sdd-status` sont des commandes méta disponibles à tout moment.

## Rôles internes et délégation

Un rôle interne n'est pas une nouvelle étape ni une commande à mémoriser. C'est
une fiche d'instructions que l'orchestrateur fournit à un sous-agent pour lui
confier une partie précise du travail.

Exemple pendant l'étape 4 :

1. `/sdd-build T-001` reste l'unique commande saisie par l'utilisateur ;
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
python3 /chemin/vers/skill-creator/scripts/quick_validate.py hermes/skills/sdd-help
python3 /chemin/vers/skill-creator/scripts/quick_validate.py hermes/skills/sdd-status
python3 /chemin/vers/skill-creator/scripts/quick_validate.py hermes/skills/sdd-spec
python3 /chemin/vers/skill-creator/scripts/quick_validate.py hermes/skills/sdd-spec-review
python3 -m unittest -v \
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
