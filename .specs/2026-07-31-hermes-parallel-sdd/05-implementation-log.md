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
