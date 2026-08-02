# Journal d'implémentation : 2026-07-31-hermes-parallel-sdd

> Responsables : `spring-test-engineer` + `spring-implementer` · Phase 4 · Ajouts uniquement

---

## T-001 — Porter le contrat onboard puis publier sa copie exacte

### T-001 · red · 2026-08-01T11:50:48Z

- Test ajouté : `hermes/scripts/test_sdd_onboard_profile_contract.py::SddOnboardProfileContractTest::test_distributed_contract_runs_from_profile_skills_layout` (`T-001-T1`, `AC-098`, `AC-099`)
- Commande : `python3 hermes/scripts/test_sdd_onboard_profile_contract.py`
- Résultat : **échec attendu** — le contrat distribué exécute 5 tests, dont 3 réussissent et 2 échouent sur les documents absents hors distribution.
- Extrait :

  ```text
  AssertionError: 0 != 1 : E..E.
  ERROR: test_all_five_artifacts_are_shared_by_skill_help_status_and_docs
  FileNotFoundError: [Errno 2] No such file or directory: '<temporary>/docs/artifact-contract.md'
  ERROR: test_mapping_marks_only_converted_commands_as_converted
  FileNotFoundError: [Errno 2] No such file or directory: '<temporary>/docs/codex-migration.md'
  Ran 5 tests in 0.002s
  FAILED (errors=2)
  ```

- Notes : la disposition temporaire est littéralement `profile/skills/...`; l'échec provient du calcul `SKILL_ROOT.parents[2]`, pas d'une faute de syntaxe ou de chargement du test.

---

### T-001 · green · 2026-08-01T11:55:40Z

- Correctif minimal : le contrat canonique lit désormais
  `references/artifact-contract.md` embarqué et classe `/sdd-onboard` et
  `/sdd-build` depuis les sections installées/roadmap de `sdd-help`. La surface
  distribuée `sdd-status` reste vérifiée avec le skill et le contrat
  d'artefacts.
- Aucun cas supprimé : les cinq tests du contrat et leurs assertions métier
  sont conservés.
- Commandes source :

  ```text
  PYTHONDONTWRITEBYTECODE=1 python3 hermes/scripts/test_sdd_onboard_profile_contract.py
  PYTHONDONTWRITEBYTECODE=1 python3 hermes/skills/sdd-onboard/scripts/test_onboarding_guard.py
  PYTHONDONTWRITEBYTECODE=1 python3 hermes/skills/sdd-onboard/scripts/test_skill_contract.py
  ```

- Résultat source : **vert** — 1/1 test de disposition, 15/15 tests du garde,
  5/5 tests du contrat.
- Publication mécanique : les 15 fichiers exacts de
  `hermes/skills/sdd-onboard` ont été copiés vers
  `profile-build/skills/sdd-onboard`, sans métadonnée de version.
- Commandes profil et parité :

  ```text
  PYTHONDONTWRITEBYTECODE=1 python3 skills/sdd-onboard/scripts/test_onboarding_guard.py
  PYTHONDONTWRITEBYTECODE=1 python3 skills/sdd-onboard/scripts/test_skill_contract.py
  PYTHONDONTWRITEBYTECODE=1 python3 hermes/scripts/check_profile_parity.py /private/tmp/hermes-s001.n66XgC/profile-build
  ```

- Résultat profil : **vert** — 15/15 tests du garde, 5/5 tests du contrat et
  parité exacte des 41 fichiers de skills source/profil.

### T-001 · découverte complète · 2026-08-01T11:55:40Z

- Commande :
  `PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_skill_tests.py`.
- Résultat du runner supervisé : **échec d'environnement distinct** après
  découverte de 4 fichiers. Le premier fichier exécute ses 15 tests avec
  `OK`, puis la supervision échoue avec
  `test descendant cleanup failed: RuntimeError: cannot enumerate test descendants`.
  L'échec ne provient d'aucun test onboard.
- Preuve directe non masquée : les quatre fichiers découverts réussissent
  séparément, soit 42/42 tests (15 onboard guard, 5 onboard contract,
  14 plan guard et 8 spec-review guard).

### T-001 · refactor · 2026-08-01T11:55:40Z

- Relecture du diff : aucun refactor supplémentaire nécessaire. Le retrait de
  la racine de dépôt et les deux substitutions de surfaces constituent le diff
  minimal ; aucune abstraction ni duplication nouvelle ne justifie un helper.
- Résultat après relecture : **vert** — 1/1 + 15/15 + 5/5 côté source.

### T-001 · simplify · 2026-08-01T11:55:40Z

- Passe `clarity-over-cleverness` : aucune simplification supplémentaire sans
  ajouter une abstraction prématurée. Les noms `installed` et `roadmap`
  exposent directement l'intention métier.
- Résultat final profil : **vert** — 42/42 tests directs ; parité exacte des
  41 fichiers de skills.
- `git diff --check` côté source : **vert**.
- État final : `T-001 = done`, `active_task = null`.

---

## T-002 — Versionner et valider la distribution 0.4.8

### T-002 · red · 2026-08-01T12:01:50Z

- Test ajouté : `scripts/test_validate_distribution.py::DistributionValidatorTest::test_release_0_4_8_metadata_is_consistent` (`T-002-T1`, `AC-097`, `AC-251`).
- Commande ciblée :
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/private/tmp/hermes-t002-markdown-stub /opt/miniconda3/bin/python3 -m unittest scripts.test_validate_distribution.DistributionValidatorTest.test_release_0_4_8_metadata_is_consistent`.
- Résultat : **échec attendu** — le manifeste déclare encore exactement
  `0.4.7`, alors que le contrat de release attend `0.4.8`.
- Extrait :

  ```text
  FAIL: test_release_0_4_8_metadata_is_consistent
  T-002-T1 / AC-097, AC-251.
  Traceback (most recent call last):
    File "scripts/test_validate_distribution.py", line 38, in test_release_0_4_8_metadata_is_consistent
      self.assertEqual("0.4.8", manifest["version"])
  AssertionError: '0.4.8' != '0.4.7'
  - 0.4.8
  + 0.4.7
  Ran 1 test in 0.002s
  FAILED (failures=1)
  ```

- Environnement : `markdown-it-py` n'étant pas installé et le réseau étant
  bloqué, seul ce test de métadonnées a été chargé avec un stub d'import
  temporaire hors dépôt. Cette exécution n'est pas une validation globale.

---

### T-002 · green · 2026-08-01T12:08:44Z

- Correctif minimal dans le profil candidat : `distribution.yaml` déclare
  `0.4.8`, `CHANGELOG.md` décrit la publication de `/sdd-onboard`, et
  `README.md` documente la commande, ses rôles lecteurs et la publication
  transactionnelle des cinq artefacts.
- Le test RED `T-002-T1` n'a pas été modifié et devient vert :
  `Ran 1 test in 0.001s — OK`.
- Validation YAML : `distribution.yaml` est chargé par `PyYAML 6.0.3` et sa
  version vaut exactement `0.4.8`.
- Tests directs du profil : **42/42 verts** — 15 garde onboard, 5 contrat
  onboard, 14 garde plan et 8 garde spec-review.
- Parité : **verte**, les 41 fichiers des skills du checkout source candidat
  et du profil candidat sont identiques.
- `git diff --check` sur les modifications non indexées de T-002 : **vert**.
- Le stub `markdown_it` utilisé uniquement pour charger le test ciblé a été
  créé hors dépôt puis supprimé ; il n'a servi ni au validateur global ni à
  une affirmation de validation de distribution.
- Limites d'environnement : le validateur global et sa suite ne sont pas
  exécutables sans `markdown-it-py 4.2.0` (`ModuleNotFoundError`).
  Markdownlint via `npx` n'a produit aucune sortie pendant 60 secondes dans
  l'environnement sans réseau et a été interrompu ; aucune réussite globale
  distribution/Markdown/CI n'est revendiquée.

### T-002 · refactor · 2026-08-01T12:08:44Z

- Aucun refactor supplémentaire : les trois changements de métadonnées sont
  déclaratifs, disjoints et minimaux. Aucun workflow, validateur ou test n'a
  été modifié pendant GREEN.
- Relecture du diff : aucun comportement spéculatif ni duplication nouvelle.

### T-002 · simplify · 2026-08-01T12:08:44Z

- Passe `clarity-over-cleverness` : le README emploie les termes du contrat
  onboard (`lecture seule`, `garde atomique`, cinq artefacts) et le changelog
  reste une liste directe sans abstraction documentaire supplémentaire.
- Résultat final local : test ciblé 1/1, tests directs 42/42, parité 41 fichiers,
  YAML PyYAML 6.0.3 et `git diff --check` verts.
- État final : `T-002 = done`, `active_task = null`. Les gates globales
  distribution, Markdownlint et CI restent à exécuter dans l'environnement CI
  équipé des dépendances épinglées.

---

## Préparation de T-003 — traçabilité externe

### Issue de publication · 2026-08-01T12:42:49Z

- Issue profil créée :
  `staaack-io/hermes-agent-profile-staaack#45`,
  <https://github.com/staaack-io/hermes-agent-profile-staaack/issues/45>.
- L'issue consigne le périmètre 0.4.8, les preuves locales, les deux noms de
  checks CI attendus et les gates review, fils, go humain et VPS.
- La création de l'issue sœur dans
  `staaack-io/specs-driven-development` a été refusée par GitHub avec
  `403 Resource not accessible by integration`. Aucun ticket source n'est
  revendiqué.
- Cette préparation ne démarre pas T-003 : aucune PR profil, CI, review ou
  autorisation de fusion n'existe encore. `T-003` reste `pending` et
  `active_task` reste `null`.

### Passe de reproductibilité · 2026-08-01T12:45:01Z

- Tests source réexécutés : **21/21** (`1 + 15 + 5`).
- Tests directs du profil réexécutés : **42/42** (`15 + 5 + 14 + 8`).
- Parité réexécutée : **41 fichiers identiques**.
- Diff candidat/base : exactement quatre fichiers modifiés (`CHANGELOG.md`,
  `README.md`, `distribution.yaml`, `scripts/test_validate_distribution.py`)
  et un dossier ajouté (`skills/sdd-onboard`).
- Recherche ciblée de signatures de secrets : aucun résultat dans les fichiers
  source, SDD ou profil modifiés.
- Archive candidate vérifiée : **78 entrées**, SHA-256
  `10cb97559a2718ff62bde84d8f6446cd2defa0c134f16b9daf4feef272bcb2d7`.
- Aucun statut de gate externe ne change : ces preuves restent locales.

---

## T-003 — Gate de publication du profil 0.4.8

### T-003 · done · 2026-08-01T23:00:29Z

- Issue profil : `staaack-io/hermes-agent-profile-staaack#45`.
- PR profil : `staaack-io/hermes-agent-profile-staaack#46`, tête
  `903ce4cfca4a80ab270c43f7ba44a4f7f8f8bd93`.
- CI : **2/2 checks verts** — Skills en 8 s et Distribution en 1 min 19 s.
- Preuves locales : **42/42** tests skills, **159/159** tests distribution,
  Markdownlint sans erreur et parité canonique exacte.
- Fils de review : **0** ; état avant fusion : `MERGEABLE/CLEAN`.
- Review GitHub formelle : absente. Le nouvel `AGENTS.md` rend `$review`
  facultatif et l'utilisateur a explicitement autorisé le 2026-08-02 la
  fusion malgré cette absence ; cette dérogation est consignée sans revendiquer
  une review inexistante.
- Go humain reçu après présentation des preuves et avant la fusion.
- Fusion confirmée à `2026-08-01T23:00:29Z`, commit
  `96ee0fb697d48bf49d80639a00a83aea34fce2ff`.
- Aucun déploiement ni changement VPS n'a été effectué.
- État final : `T-003 = done`, `active_task = null`.

---

## T-004 — Relier les jobs Kanban à GitHub sans ordonnanceur concurrent

### T-004 · red · 2026-08-01T23:14:29Z

- Test ajouté :
  `hermes.runtime.test_sdd_github_bridge.GitHubBridgeLifecycleTest.test_admitted_job_creates_and_records_issue_and_draft_pull_request`
  (`T-004-T1`, `T-004-T2`, `AC-110` à `AC-113`, `AC-253`, `AC-254`).
  Le test fournit des adaptateurs factices structurés pour `gh`, Kanban et
  l'état CAS, puis vérifie la création de l'issue, la création d'une PR
  brouillon et l'écriture des deux identifiants dans la carte et l'état.
- Commande ciblée :
  `/usr/bin/time -p env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest hermes.runtime.test_sdd_github_bridge.GitHubBridgeLifecycleTest.test_admitted_job_creates_and_records_issue_and_draft_pull_request`.
- Résultat : **échec attendu** en 0,06 s — le module du bridge GitHub n'existe
  pas encore ; l'erreur survient au chargement de la cible, pas à cause d'une
  faute de syntaxe ou d'assertion dans le test.
- Extrait expurgé :

  ```text
  ERROR: test_admitted_job_creates_and_records_issue_and_draft_pull_request
  T-004-T1/T-004-T2 / AC-110–AC-113, AC-253–AC-254.
  Traceback (most recent call last):
    File "<worktree>/hermes/runtime/test_sdd_github_bridge.py", line 105
      bridge = load_bridge()
    File "<worktree>/hermes/runtime/test_sdd_github_bridge.py", line 33
      module_spec.loader.exec_module(module)
    File "<frozen importlib._bootstrap_external>", line 953, in get_data
  FileNotFoundError: [Errno 2] No such file or directory:
    '<worktree>/hermes/runtime/sdd_github_bridge.py'
  ```

- Durée rapportée par `/usr/bin/time` : `real 0.06`, `user 0.04`, `sys 0.01`.
- État : `T-004 = red`, `active_task = T-004`. Aucun fichier de production ni
  contrat Markdown n'a été modifié.

---

### T-004 · green · 2026-08-01T23:20:11Z

- Le RED renforcé a été rejoué sans modification avant production :
  `python3 -m unittest hermes.runtime.test_sdd_github_bridge.GitHubBridgeLifecycleTest.test_admitted_job_creates_and_records_issue_and_draft_pull_request`.
  Résultat attendu : `FileNotFoundError` sur le module absent, **1/1 en échec**
  en 0,08 s.
- Production minimale : API de transitions sans boucle pour démarrer/reprendre
  un job, rendre une PR prête, effectuer un polling dû et appliquer une
  correction. Les adaptateurs GitHub, Kanban, état, worker et horloge portent
  seuls les effets externes.
- Triangulation T-004-T2 à T-004-T8 : identifiants et CAS, passage `ready`,
  polling checks/reviews/fils à cinq minutes, correction sur la même branche
  et le fil exact, nouvelle attente, timeout à trente minutes, refus du
  troisième writer et des préconditions de phase, reprise idempotente après
  interruption Kanban.
- Commande bridge :
  `python3 -m unittest hermes.runtime.test_sdd_github_bridge` — **7/7 verts**
  en 0,08 s (`real`, 0,006 s unittest).
- Régression runtime proportionnée :
  `python3 -m unittest hermes.runtime.test_sdd_runtime_guard` — **31/31 verts**
  en 15,36 s (`real`, 15,260 s unittest).
- La suite Hermes complète est réservée à une exécution unique après la passe
  de simplification, conformément à la coordination de la gate lourde.

---

### T-004 · refactor · 2026-08-01T23:21:42Z

- Refactorisation interne sans changement d'API ni de comportement : les
  identifiants `task_id`, `card_id`, `pr` et `branch` sont nommés une fois au
  début de chaque transition longue ; la signature de `start_job` est rendue
  lisible sans helper ni classe prématurée.
- Commande : `python3 -m unittest hermes.runtime.test_sdd_github_bridge` —
  **7/7 verts** en 0,07 s (`real`, 0,008 s unittest).
- Aucun test, assertion, délai ou invariant n'a été retiré.

---

### T-004 · simplify · 2026-08-01T23:29:54Z

- Passe `clarity-over-cleverness` : les clés de domaine répétées sont des
  constantes nommées ; les transitions utilisent des variables locales
  explicites et des retours anticipés. Aucun scheduler, auto-merge, troisième
  writer, secret ou chemin absolu n'est introduit.
- La relecture a découvert le cas limite AC-119 « review disponible exactement
  à trente minutes ». Le nouveau test ciblé a d'abord échoué en 0,07 s avec
  `KeyError: 'reviews'`, prouvant que le timeout précédait l'observation.
- Correction minimale : lorsqu'un polling est dû, checks, reviews et fils sont
  lus et l'instant est enregistré avant d'évaluer le timeout. `needs_input`
  s'applique uniquement si la liste des reviews est vide à l'échéance.
- Preuves post-correction : test ciblé **1/1 vert** en 0,06 s ; suite bridge
  **8/8 verte** en 0,07 s ; runtime ciblé **31/31 vert** en 15,73 s.
- Runner CI complet post-correction, avec `PYTHONDONTWRITEBYTECODE=1` et les
  dépendances de `requirements-ci.txt` installées uniquement sous
  `/private/tmp` : **224 découverts, 220 exécutés verts, 4 ignorés**, 15
  fichiers en 82,39 s. Le premier essai sandbox avait échoué avant test car
  `ps` était interdit ; un essai intermédiaire avait ensuite révélé la
  dépendance CI locale manquante `markdown_it`. Aucun de ces deux arrêts n'est
  présenté comme une réussite.
- Validation séparée : **8 skills Hermes valides** en 0,26 s.
- Couverture `coverage.py 7.15.2`, installée uniquement sous `/private/tmp` :
  `sdd_github_bridge.py` atteint **100 %** des 68 instructions et **100 %**
  des 14 branches ; aucun manque.
- Markdownlint épinglé 0.18.1 : **2 fichiers, 0 erreur**.
- État final : `T-004 = done`, `active_task = null`. La mise à jour du statut
  partagé dans `04-tasks.md` reste au synthesizer de fan-in ; ce writer ne sort
  pas du scope autorisé.

---

## T-005 — Afficher la carte task-local dans `/sdd-status`

### T-005 · red · 2026-08-01T23:11:33Z

- Test ajouté : `hermes/skills/sdd-status/scripts/test_status_guard.py::StatusGuardTest::test_v2_task_local_view_exposes_all_proven_fields` (`T-005-T1`, `AC-243` à `AC-249`).
- Commande ciblée :
  `PYTHONDONTWRITEBYTECODE=1 python3 hermes/skills/sdd-status/scripts/test_status_guard.py StatusGuardTest.test_v2_task_local_view_exposes_all_proven_fields`.
- Durée : **0,07 s** (`real`; test : `0.000s`).
- Résultat : **échec attendu** — la vue task-local et son garde de rendu
  n'existent pas encore ; le test demande les sept champs prouvés sans les
  déduire.
- Extrait :

  ```text
  FAIL: test_v2_task_local_view_exposes_all_proven_fields
  T-005-T1 / AC-243, AC-244, AC-245, AC-246, AC-247, AC-248, AC-249.
  Traceback (most recent call last):
    File "hermes/skills/sdd-status/scripts/test_status_guard.py", line 23
      self.fail(
  AssertionError: T-005-T1: task-local status view is absent because
  status_guard.py does not exist
  Ran 1 test in 0.000s
  FAILED (failures=1)
  real 0.07
  ```

- État : `T-005 = red`, `active_task = T-005`. Aucun fichier de production,
  skill ou référence Markdown n'a été modifié.

---

### T-005 · green · 2026-08-01T23:19:52Z

- Production minimale : `task_local_rows` recopie les sept champs prouvés de
  chaque tâche v2 et utilise `—` lorsqu'ils sont absents. La lecture JSON
  dédiée n'écrit aucun fichier.
- Triangulation ajoutée sans affaiblir T-005-T1 :
  - T-005-T2 : état v2 complet et ordre déterministe ;
  - T-005-T3 : compatibilité v1 avec sept valeurs `—` ;
  - T-005-T4 : empreinte du dépôt identique avant et après lecture ;
  - T-005-T5 : `next_action` est recopiée si prouvée et jamais déduite.
- Commande RED puis GREEN ciblée :
  `PYTHONDONTWRITEBYTECODE=1 python3 hermes/skills/sdd-status/scripts/test_status_guard.py StatusGuardTest.test_v2_task_local_view_exposes_all_proven_fields`.
- Résultat ciblé : **1/1 test vert**, **0,063 s**.
- Commande de suite du skill :
  `PYTHONDONTWRITEBYTECODE=1 python3 hermes/skills/sdd-status/scripts/test_status_guard.py`.
- Résultat du skill : **5/5 tests verts**, **0,121 s**.
- Commande de contrat distribué :
  `.venv-ci/bin/python hermes/scripts/validate_skills.py hermes/skills`.
- Résultat du contrat : **8/8 skills valides**, **0,256 s**.
- Régression Hermes lancée une fois avec
  `PYTHONDONTWRITEBYTECODE=1 python3 hermes/scripts/run_python_tests.py` : la
  capture prouve **14/14 e2e**, **31/31 runtime** et **3/3 parité** verts avant
  de s'interrompre à l'en-tête du fichier suivant, sans résumé global. Aucun
  échec fonctionnel n'est affiché et la gate n'a pas été relancée inchangée.
- État intermédiaire : `T-005 = green`.

### T-005 · refactor · 2026-08-01T23:20:10Z

- Relecture structurelle : la production conserve deux fonctions publiques
  consommées par la frontière status, sans interface, option ni helper à
  appelant unique supplémentaire. Aucun changement de comportement retenu.
- Commande :
  `PYTHONDONTWRITEBYTECODE=1 python3 hermes/skills/sdd-status/scripts/test_status_guard.py`.
- Résultat : **5/5 tests verts**, **0,084 s**.

### T-005 · simplify · 2026-08-01T23:20:36Z

- `clarity-over-cleverness` : la compréhension imbriquée a été remplacée par
  une boucle explicite sur les sept champs métier ; les assertions longues ont
  été mises en forme sans changer leur comportement.
- Le skill et sa référence nomment explicitement l'ordre des champs, la lecture
  v1/v2, la valeur `—`, l'absence de déduction et l'interdiction d'écriture.
- Commande :
  `PYTHONDONTWRITEBYTECODE=1 python3 hermes/skills/sdd-status/scripts/test_status_guard.py`.
- Résultat : **5/5 tests verts**, **0,077 s**.
- Couverture : `python3 -m trace --count --summary --module unittest discover`
  exécute **5/5 tests** et couvre **21/21 lignes de production (100 %)**.
- État final : `T-005 = done`, `active_task = null`.

---
