# Journal d'implémentation : 2026-07-31-hermes-parallel-sdd

> Responsables : `spring-test-engineer` + `spring-implementer` · Phase 4 · Ajouts uniquement

---

## T-030 — Encoder la politique de conformité VPS

### T-030 · red · 2026-08-03T16:49:25Z

- Le contrat unitaire structuré couvre T-030-T1 à T-030-T7 : données
  expurgées, invocation Hermes, limites de délégation, barrière gateway,
  service utilisateur, rétention et pureté AST.
- Commande :
  `PYTHONDONTWRITEBYTECODE=1 /private/tmp/hermes-t013-venv/bin/python -m unittest hermes.operations.test_vps_pilot_policy.VpsPilotPolicyTest.test_t030_t1_accepts_a_compliant_structured_policy`.
- Résultat : **échec attendu** —
  `ModuleNotFoundError: No module named 'hermes.operations.vps_pilot_policy'` ;
  1 test exécuté, 1 erreur.
- État : `T-030 = red`, `active_task = T-030`. Aucun module de production
  n'existait au moment de cette preuve.

---

### T-030 · green · 2026-08-03T16:53:58Z

- `validate_vps_pilot_policy` retourne un tuple stable de violations sans
  exécuter de commande ni effectuer d'I/O.
- Les preuves sensibles, l'invocation Hermes, la profondeur, l'auto-approve,
  la barrière des deux succès, le service utilisateur et la rétention sont
  validés de façon fermée en cas de valeur absente ou mal typée.
- Vérification ciblée portable depuis hors dépôt : **7/7 tests verts** en
  0,017 s. Le premier runner complet a aussi révélé puis fait corriger le
  chargement isolé du module de test.
- État : `T-030 = green`, `active_task = T-030`.

---

### T-030 · refactor · 2026-08-03T16:54:46Z

- La fixture charge le module pur une seule fois par classe et les violations
  suivent un ordre métier déterministe, sans changer la surface publique.
- La couverture de l'expurgation distingue explicitement secret, token,
  credential et transcript. Une valeur de compteur mal typée est refusée sans
  lever d'exception.
- Vérification après refactor : **7/7 tests verts** depuis un répertoire isolé
  en 0,006 s.
- État : `T-030 = refactor`, `active_task = T-030`.

---

### T-030 · simplify · 2026-08-03T16:55:25Z

- Passe `clarity-over-cleverness` : chaque section est validée par une fonction
  nommée selon le domaine, les retours sont déterministes et aucun mode,
  paramètre ou helper spéculatif n'est présent.
- Les contrôles de type restent explicites ; le seul chemin absolu admis est
  la valeur distante Hermes imposée par AC-169, jamais un chemin de preuve.
- Vérification : **7/7 tests verts** en 0,007 s et pureté AST confirmée.
- État : `T-030 = simplify`, `active_task = T-030`.

---

### T-030 · done · 2026-08-03T17:00:22Z

- T-030-T1 à T-030-T7 couvrent les quinze AC de la tâche par sept tests
  comportementaux, dont une preuve AST d'absence de processus, réseau et SSH.
- Vérification finale : **400 tests exécutés sur 404 découverts**, 4 skips
  historiques et zéro échec ; **14 skills Hermes** validés ; **2 documents**
  lintés avec zéro erreur ; JSON, état ciblé et `git diff --check` verts.
- La régression de métadonnées a été contrôlée explicitement : `T-014` est
  identique à HEAD et seul `T-030` a suivi le cycle de cette branche.
- Issue d'exécution : `#119`. Branche : `agent/build-t030-vps-policy`, prévue
  sur `agent/plan-s008-vps-pilot-100`, sans reviewer ni merge.
- PR empilée : `#121`, base `agent/plan-s008-vps-pilot-100`, sans reviewer.
- Aucune primitive VPS, gateway, SSH, réseau, déploiement ou publication n'a
  été appelée. État final : `T-030 = done`, `active_task = null`.

---

## T-028 — Auditer les commandes et les onze AC de S-007

### T-028 · red · 2026-08-03T16:05:04Z

- Le contrat `hermes/scripts/test_sdd_s007_contract.py` couvre T-028-T1 à
  T-028-T6 : manifeste des onze AC, inventaire des commandes, DAG, preuves E2E,
  enveloppes d'exécution et barrières de sécurité.
- Commande : `PYTHONDONTWRITEBYTECODE=1 /private/tmp/hermes-t013-venv/bin/python hermes/scripts/test_sdd_s007_contract.py`.
- Résultat : **échec attendu**, 6 tests exécutés, 4 échecs. Les documents ne
  publient pas encore S-007 comme parcours onboard→ship complet et le marqueur
  explicite de preuve de dépendance manque dans l'audit.
- État : `T-028 = red`, `active_task = T-028`. Aucun document de publication
  n'avait été modifié avant cette preuve.

---

### T-028 · green · 2026-08-03T16:09:18Z

- L'aide expose les quatorze commandes installées et identifie le parcours
  S-007 complet sans conserver de commande prévue.
- Le README et les contrats documentent le DAG, les six familles de preuves,
  les enveloppes issue/carte/branche/worktree/session/PR et les barrières de
  sécurité du runner jetable.
- Vérification ciblée : **6/6 tests S-007** verts en 0,023 s.
- État : `T-028 = green`, `active_task = T-028`.

---

### T-028 · refactor · 2026-08-03T16:10:27Z

- Les chemins des scénarios et des documents publiés sont regroupés dans des
  constantes déclaratives pour rendre les frontières de l'audit immédiatement
  visibles et éviter la répétition.
- Vérification après refactor : **6/6 tests S-007** verts en 0,021 s et
  `git diff --check` vert.
- État : `T-028 = refactor`, `active_task = T-028`.

---

### T-028 · simplify · 2026-08-03T16:11:44Z

- Passe `clarity-over-cleverness` : le contrat garde un test par responsabilité
  T-028, un manifeste primaire déclaratif et des marqueurs de preuve nommés.
- Les ajouts documentaires utilisent les mêmes termes du domaine pour le DAG,
  le lifecycle et les barrières ; aucune abstraction ou option spéculative
  n'est ajoutée.
- État : `T-028 = simplify`, `active_task = T-028`.

---

### T-028 · done · 2026-08-03T16:22:17Z

- T-028-T1 à T-028-T6 couvrent AC-225 et relient exactement les onze AC S-007
  à un producteur primaire parmi T-025 à T-029.
- Preuves finales : **6/6 contrat S-007**, **393 tests Hermes exécutés sur 397
  découverts**, 4 skips historiques déclarés, **14 skills validés** et **5
  documents Markdown** lintés sans erreur.
- Le contrat confirme les preuves exécutables de concurrence, capacité,
  conflit, dépendance, échec et fan-in, ainsi que l'enveloppe complète de chaque
  tâche. JSON d'état et `git diff --check` sont verts.
- Issue d'exécution : `#114`. Branche : `agent/build-t028-s007-audit`, empilée
  sur `agent/build-t027-e2e-full-flow`, sans reviewer humain, fusion, VPS ou
  déploiement. PR empilée : `#115`.
- État final : `T-028 = done`, `active_task = null`.

---

## T-027 — Étendre le runner jetable de onboard à ship

### T-027 · red · 2026-08-03T15:42:22Z

- **Commande :** `PYTHONDONTWRITEBYTECODE=1 /private/tmp/hermes-t013-venv/bin/python -m unittest` sur les huit méthodes `test_t027_t*` de `RunnerTest`.
- **Résultat :** FAIL attendu — 8 tests exécutés, 1 échec et 6 erreurs.
- **Extrait :** `KeyError: 'lifecycle'`, `KeyError: 'evidence_order'`,
  `KeyError: 'task_envelopes'`, `KeyError: 'barrier'`, `KeyError: 'resume'` et
  présence du chemin temporaire absolu dans le JSON final.
- État : `T-027 = red`, `active_task = T-027`. Aucun fichier de production
  T-027 n'avait été modifié avant cette preuve rouge.

---

### T-027 · green · 2026-08-03T15:50:29Z

- Le runner traverse désormais onboard, wire-harness, spec, spec-review,
  epic-plan/plan, build, simplify, test, validate, review et ship dans sa racine
  sentinellée.
- Les scénarios exécutables T-025 et T-026 sont lancés avant les commandes
  dépendantes. Leurs enveloppes issue/carte/branche/worktree/session/PR et leur
  barrière fusion observée + go sont agrégées sans lancer de merge.
- Un échec conserve le run et publie une reprise `--resume-run` explicite. Le
  rapport final contient uniquement le nom du run et des preuves relatives,
  sans secret ni chemin absolu.
- **Vérification :** `python hermes/e2e/test_run_sdd_e2e.py -v` — **22/22
  tests verts** en 104,239 s.
- État : `T-027 = green`, `active_task = T-027`.

---

### T-027 · refactor · 2026-08-03T15:54:19Z

- La création du dépôt parallèle, le chargement des scénarios et la
  normalisation des enveloppes sont isolés derrière des fonctions nommées ; le
  runner principal reste l'unique orchestration du flux.
- `--resume-run` valide la sentinelle et la racine autorisée avant de lire une
  preuve conservée. L'erreur persistée remplace les chemins du run, du projet,
  de la racine temporaire et du binaire par `<redacted-path>`.
- **Vérification après refactor :** **22/22 tests du runner verts** en
  101,877 s ; le test direct de reprise est vert en 0,732 s.
- État : `T-027 = refactor`, `active_task = T-027`.

---

### T-027 · simplify · 2026-08-03T15:55:00Z

- Passe `clarity-over-cleverness` : le flux reste linéaire, les phases métier
  sont nommées dans `LIFECYCLE`, les scénarios gardent leurs modules canoniques
  et aucun second ordonnanceur n'est introduit.
- La reprise utilise des retours explicites `already-passed` ou
  `preserved-for-retry`; aucune option de merge, réseau, VPS ou déploiement
  n'est présente.
- Le README décrit le même ordre et les mêmes limites que l'exécutable.
- **Vérification :** la suite ciblée demeure verte à **22/22** après cette
  passe ; `git diff --check` est vert.
- État : `T-027 = simplify`, `active_task = T-027`.

---

### T-027 · done · 2026-08-03T16:00:55Z

- T-027-T1 à T-027-T8 couvrent AC-155, AC-218 et AC-226 : cycle onboard→ship,
  racine sentinellée, preuves T-025/T-026 ordonnées, enveloppes complètes,
  barrière sans merge, reprise explicite et rapport relatif expurgé.
- Preuves finales : **387 tests Hermes exécutés sur 391 découverts**, quatre
  skips historiques déclarés, zéro échec ; **14 skills** validés ; **2
  documents Markdown** lintés sans erreur ; JSON valide et
  `git diff --check` vert.
- Issue d'exécution : `#112`. Branche :
  `agent/build-t027-e2e-full-flow`, composée localement avec T-026 au-dessus de
  T-025. Commit d'implémentation : `ad4f61f`. PR empilée : `#113`, base
  `agent/build-t025-e2e-parallel`. Aucun reviewer, merge, réseau métier, VPS ou
  déploiement.
- État final : `T-027 = done`, `active_task = null`.

---

## T-025 — Prouver deux writers full-stack réellement concurrents

### T-025 · red · 2026-08-03T15:22:52Z

**Command:** `PYTHONDONTWRITEBYTECODE=1 /private/tmp/hermes-t013-venv/bin/python hermes/e2e/test_parallel_scenario.py`

**Result:** FAIL (expected) — 7 tests exécutés, 6 échecs et 1 erreur.

**Excerpt:** `AssertionError: T-025-T1: parallel_scenario.py must run local full-stack writers`

- Les sept tests T-025-T1 à T-025-T7 sont présents avant la production.
- L'échec provient de l'absence intentionnelle de
  `hermes/e2e/parallel_scenario.py`, et non d'une faute de compilation.
- La prochaine étape minimale consiste à réutiliser les leases du runtime et
  l'enveloppe canonique pour exécuter deux vrais processus locaux disjoints.

---

### T-025 · green · 2026-08-03T15:27:31Z

- Le scénario lance deux vrais processus Python locaux pour les writers backend
  et frontend après acquisition de deux leases disjoints du runtime canonique.
- Le départ synchronisé permet de mesurer des intervalles monotones ayant un
  overlap strict ; le pic calculé vaut exactement deux, soit le plafond Hermes.
- `sdd_job_execution.materialize_job` produit les enveloppes isolées issue,
  carte, branche, worktree, session et PR via des adaptateurs locaux.
- Un second lease sur le scope partagé est refusé tant que le premier est actif,
  puis le second writer s'exécute après libération.
- Vérification ciblée : **7/7 tests verts** en 15,239 s.

---

### T-025 · refactor · 2026-08-03T15:28:28Z

- La fixture jetable et son scénario réel sont partagés au niveau de la classe
  de test ; chaque oracle reste indépendant, mais les quatre processus ne sont
  plus relancés six fois sans nécessité.
- Le cleanup explicite du dépôt temporaire supprime les avertissements de
  ressources et réduit la suite ciblée de 15,239 s à 3,673 s.
- Vérification après refactorisation : **7/7 tests verts**, mêmes assertions et
  mêmes frontières publiques.

---

### T-025 · simplify · 2026-08-03T15:29:15Z

- Passe `clarity-over-cleverness` : les identifiants des trois tâches E2E sont
  nommés, et les six adaptateurs canoniques remplacent l'ancien tuple indexé par
  des variables explicites.
- Aucun ordonnanceur, option spéculative, API réseau, merge, déploiement ou
  chemin absolu n'est introduit dans la preuve persistable.
- Vérification après simplification : **7/7 tests verts** en 3,523 s et
  compilation Python des deux fichiers sans erreur.

---

### T-025 · done · 2026-08-03T15:32:54Z

- T-025-T1 à T-025-T7 couvrent AC-156, AC-219 et AC-227 avec de vrais
  processus locaux, des scopes disjoints, un overlap monotone strict et un pic
  exactement égal à deux sans dépassement.
- Le conflit est sérialisé par `acquire_scope_lease`/`release_scope_lease` et
  les enveloppes proviennent de `sdd_job_execution.materialize_job` ; aucun
  second ordonnanceur n'est présent.
- Preuves finales : **371 tests Hermes exécutés sur 375 découverts**, quatre
  skips historiques déclarés, zéro échec ; **14 skills** validés ; Markdown
  linté sans erreur ; JSON valide et `git diff --check` vert.
- Le cache Python généré sous `hermes/e2e/__pycache__/` a été supprimé.
- Issue d'exécution : `#110`. Branche :
  `agent/build-t025-e2e-parallel`. PR empilée : `#111`, base
  `agent/plan-s007-e2e-090`. Aucun reviewer, merge, VPS ou déploiement.
- État final : `T-025 = done`, `active_task = null`.

---

## T-026 — Prouver attente, échec isolé et reprise transactionnelle

### T-026 · red · 2026-08-03T17:23:00Z

- **Command:** `PYTHONDONTWRITEBYTECODE=1 /private/tmp/hermes-t013-venv/bin/python hermes/e2e/test_recovery_scenario.py`
- **Result:** FAIL (expected), 8 tests exécutés et 9 échecs observés.
- **Excerpt:** `AssertionError: T-026-T1: recovery_scenario.py must implement interruption recovery`.
- Le test rouge exige les huit preuves T-026 : attente fusion/go, injections
  locales d'échec et timeout, conservation du pair vert, reprise idempotente,
  fan-in ancien ou nouveau complet et absence d'opération de fusion.
- État : `T-026 = red`, `active_task = T-026`. Branche :
  `agent/build-t026-e2e-recovery`.

---

### T-026 · green · 2026-08-03T17:28:30Z

- Le scénario matérialise les deux enveloppes avec le job wrapper canonique,
  injecte un échec ou timeout local, puis rejoue exactement la même identité.
- Les preuves du pair vert sont écrites dans le journal immuable canonique et
  restent intactes pendant l'injection et la reprise.
- Le runtime CAS et le synthesizer canoniques prouvent un rollback complet
  avant marker puis un commit complet après marker. La tâche dépendante attend
  l'intégration observée et le go explicite ; aucune opération de fusion n'est
  exposée.
- **Command:** `PYTHONDONTWRITEBYTECODE=1 /private/tmp/hermes-t013-venv/bin/python hermes/e2e/test_recovery_scenario.py`
- **Result:** PASS, 8/8 tests en 24,891 s.
- État : `T-026 = green`, `active_task = T-026`.

---

### T-026 · refactor · 2026-08-03T17:30:00Z

- Les deux injections sont préparées une seule fois par classe de test : les
  huit oracles restent indépendants tout en réduisant la suite ciblée de
  24,891 s à 6,260 s.
- La classification ancien/nouveau du fan-in utilise des branches explicites ;
  les commandes de préparation Git et les lectures des artefacts partagés sont
  formatées par étape reconnaissable.
- **Command:** `PYTHONDONTWRITEBYTECODE=1 /private/tmp/hermes-t013-venv/bin/python hermes/e2e/test_recovery_scenario.py`
- **Result:** PASS, 8/8 tests en 6,260 s.
- État : `T-026 = refactor`, `active_task = T-026`.

---

### T-026 · simplify · 2026-08-03T17:31:30Z

- Passe `clarity-over-cleverness` : les phases matérialisation, injection,
  reprise, journal, crash avant/après marker et admission sont séquentielles et
  nommées. Aucun mode spéculatif, option morte ou abstraction à implémentation
  unique n'est conservé.
- Les littéraux métier répétés sont centralisés en constantes et la génération
  du snapshot utilise des retours explicites plutôt qu'un ternaire imbriqué.
- L'issue d'exécution `#108` trace AC-157, AC-158 et AC-228 sur la branche
  `agent/build-t026-e2e-recovery`, sans reviewer sollicité.
- État : `T-026 = simplify`, `active_task = T-026`.

---

### T-026 · done · 2026-08-03T17:35:00Z

- T-026-T1 à T-026-T8 couvrent AC-157, AC-158 et AC-228 : attente du fan-in
  observé et du go, injections locales, conservation, reprise identique,
  générations atomiques ancien/nouveau et absence d'opération de fusion.
- Preuves finales : **8/8 tests ciblés**, **372 cas Hermes exécutés sur 376
  découverts**, 4 skips historiques, zéro échec ; **14 skills Hermes** validés.
- JSON d'état, Markdown et `git diff --check` sont verts. Aucun reviewer,
  merge, VPS ou déploiement n'a été sollicité ou exécuté.
- État final : `T-026 = done`, `active_task = null`. Issue `#108`, commit
  `076ed21` et PR empilée `#109` sur `agent/plan-s007-e2e-090`, sans reviewer.

---

## T-023 — Auditer la tranche S-006 dans la source Hermes

### T-023 · red · 2026-08-03T14:48:48Z

- Le contrat exécutable relie exactement les 13 critères de S-006 à T-021,
  T-022, T-023 et T-024, vérifie les deux suites source, l'ordre du DAG, les
  scopes disjoints et l'absence de capacité de déploiement dans `/sdd-ship`.
- Échec attendu : l'aide classe encore `/sdd-review` et `/sdd-ship` dans la
  feuille de route au lieu des commandes installées.
- Preuve : **6 tests exécutés, 1 échec** sur
  `test_t023_t5_help_and_docs_publish_both_commands_as_installed`.
- État : `T-023 = red`, `active_task = T-023`. Aucun reviewer sollicité.

### T-023 · green · 2026-08-03T14:50:09Z

- L'aide expose les formes exactes `/sdd-review [<feature-id>] [--base <ref>]`
  et `/sdd-ship [<feature-id>] [--base <ref>]` parmi les commandes installées.
- La documentation fixe les writers uniques de `08-code-review.md` et
  `09-ship-plan.md`, l'absence de reviewer humain et l'inertie de la commande
  de livraison affichée.
- Preuve : **6/6 tests S-006 verts**. État : `T-023 = green`,
  `active_task = T-023`.

### T-023 · refactor · 2026-08-03T14:52:54Z

- Le manifeste des 13 AC reste déclaratif et attribue un producteur primaire
  unique à chaque critère ; les contrôles AST isolent explicitement les imports
  interdits de la capacité de livraison.
- Les limites de writers sont formulées au même endroit dans le contrat des
  artefacts, sans dupliquer les contrats détaillés des skills.
- Preuves : **364/368 tests Hermes exécutés**, 4 skips historiques, zéro échec ;
  **14 skills validés** et `git diff --check` vert.
- État : `T-023 = refactor`, `active_task = T-023`.

### T-023 · simplify · 2026-08-03T14:53:29Z

- Passe `clarity-over-cleverness` : six tests nommés par responsabilité suffisent
  pour prouver le manifeste, les skills, le DAG, les frontières de capacité,
  l'aide installée et les interdictions source.
- Aucun helper, format ou abstraction supplémentaire n'est nécessaire. Les cinq
  documents Markdown modifiés passent le linter épinglé sans erreur.
- État : `T-023 = simplify`, `active_task = T-023`.

### T-023 · done · 2026-08-03T14:53:29Z

- T-023-T1 à T-023-T6 couvrent AC-148 et AC-149 ; le manifeste S-006 relie
  exactement **13/13 AC** aux tâches T-021 à T-024.
- Preuves finales : **6/6 tests S-006**, **364/368 tests Hermes** avec 4 skips
  historiques, **14 skills**, **5 documents Markdown**, JSON et diff verts.
- Issue d'exécution : `#104`. Branche : `agent/build-t023-s006-audit`, empilée
  sur T-022. PR : `#105`. Aucun reviewer sollicité ; aucune fusion, VPS ou
  livraison.
- État final : `T-023 = done`, `active_task = null`.

---

## T-021 — Convertir `/sdd-review` dans la source Hermes

### T-021 · red · 2026-08-03T14:28:34Z

- Le test engineer délégué a ajouté huit tests exécutables couvrant T-021-T1
  à T-021-T8 et AC-150/AC-151, sans modifier la production.
- Commande : `PYTHONDONTWRITEBYTECODE=1 /private/tmp/hermes-t013-venv/bin/python hermes/skills/sdd-review/scripts/test_review_guard.py`.
- Résultat attendu : **8 tests exécutés, 8 échecs** ; `SKILL.md` et
  `review_guard.py` sont absents, donc `/sdd-review` n'est pas encore publié.
- État : `T-021 = red`, `active_task = T-021`. Issue : `#100`. Branche :
  `agent/build-t021-sdd-review`.

---

### T-021 · green · 2026-08-03T14:31:14Z

- Le garde accepte uniquement les arguments structurés facultatifs, route les
  lectures Spring et React/Next.js, et ne remet aux rôles que le diff et les
  artefacts sans handle d'écriture.
- Le fan-in valide puis déduplique les constats, expurge les preuves et laisse
  l'unique writer publier atomiquement `08-code-review.md` sous verrou global.
- Le verdict est fermé à `approve|request-changes` et reste toujours informatif,
  sans gate Git ni sollicitation humaine.
- Vérifications : **8/8 tests comportementaux** et **4/4 contrats statiques**
  verts. État : `T-021 = green`, `active_task = T-021`.

---

### T-021 · refactor · 2026-08-03T14:32:32Z

- Les vocabulaires de stack, l'option de base, le répertoire d'artefacts et le
  marqueur d'expurgation sont centralisés dans des constantes métier.
- Les gardes de validité des rôles et de complétude des constats sont nommées
  explicitement, sans modifier les signatures ni le comportement public.
- Vérifications après refactor : **12/12 tests propres au skill** et
  `git diff --check` verts. État : `T-021 = refactor`.

---

### T-021 · simplify · 2026-08-03T14:33:46Z

- Passe `clarity-over-cleverness` : fonctions courtes par frontière, retours
  anticipés, constantes pour les littéraux répétés et aucune option morte.
- Deux tests de triangulation prouvent les valeurs par défaut des arguments et
  la validation runtime du jeu de changements vide des rôles read-only.
- Vérifications : **10/10 tests comportementaux**, **4/4 contrats statiques**
  et `git diff --check` verts. État : `T-021 = simplify`.

---

### T-021 · done · 2026-08-03T14:40:52Z

- Le runner source complet exécute **346 tests sur 350 découverts**, avec
  quatre skips historiques déclarés et aucun échec.
- Les **13 skills Hermes** sont valides ; les sept documents modifiés passent
  `markdownlint-cli2@0.18.1`, le JSON, l'AST et `git diff --check` sont verts.
- T-021-T1 à T-021-T8 couvrent AC-150/AC-151 : délégation spécialisée en
  lecture seule, fan-in dédupliqué, rapport unique atomique, verdict informatif
  et expurgation.
- La frontière durable valide explicitement le seul changement autorisé avant
  le verrou et expurge le contenu complet avant l'écriture ; le test vérifie
  l'ordre `validate → lock → write` et l'absence de token, e-mail ou chemin.
- État final : `T-021 = done`, `active_task = null`. Issue : `#100`. Aucun
  reviewer humain, aucune fusion, opération VPS ou déploiement.
- PR empilée : `#102`, base `agent/plan-s006-review-ship` (`#99`).

---

## T-022 — Convertir `/sdd-ship` sans capacité de déploiement

### T-022 · red · 2026-08-03T14:25:46Z

- Test minimal :
  `ShipGuardPublicationTests.test_t_022_t1_ship_guard_is_published`.
- Commande :
  `PYTHONDONTWRITEBYTECODE=1 python hermes/skills/sdd-ship/scripts/test_ship_guard.py -v`.
- Résultat : **1 test exécuté, 1 échec attendu** —
  `T-022-T1: ship_guard.py must publish /sdd-ship`.
- Aucun fichier de production `sdd-ship` n'existait pendant cette preuve.
- État : `T-022 = red`, `active_task = T-022`.

---

### T-022 · green · 2026-08-03T14:30:48Z

- `/sdd-ship [<feature-id>] [--base <ref>]` valide les arguments comme des
  données et ne possède aucune primitive d'exécution.
- Les six portes sont fail-closed avant toute publication ; rollback,
  observabilité, flag et deux catégories de notes sont obligatoires.
- Le writer publie uniquement `09-ship-plan.md` par remplacement atomique sous
  le verrou canonique ; une commande de déploiement reste du texte expurgé.
- Vérifications ciblées : **9/9 tests du garde** et **3/3 contrats du skill**
  verts.
- État : `T-022 = green`, `active_task = T-022`.

---

### T-022 · refactor · 2026-08-03T14:32:15Z

- Les preuves, le rollback, l'observabilité, le flag et le plan sont des
  structures immuables explicites ; chaque validateur échoue sur son champ
  métier avant le writer.
- Le rollback encode la limite maximale de cinq minutes et refuse le simple
  revert ; notes et commande refusent secrets et chemins locaux sensibles.
- Vérifications après refactor : **12/12 tests T-022** et
  `git diff --check` verts.
- État : `T-022 = refactor`, `active_task = T-022`.

---

### T-022 · simplify · 2026-08-03T14:35:40Z

- Passe `clarity-over-cleverness` : retours anticipés pour chaque porte,
  validateurs nommés selon le contrat de livraison et structures sans option
  morte ni callback spéculatif.
- La capacité négative est lisible dans le code et prouvée par AST : aucun
  import shell, réseau, SSH ou VPS et aucun appel d'exécution.
- Vérifications : **13/13 skills embarqués**, markdownlint sur cinq documents,
  JSON et `git diff --check` verts.
- État : `T-022 = simplify`, `active_task = T-022`.

---

### T-022 · done · 2026-08-03T14:36:24Z

- Les huit Test-IDs couvrent publication, arguments, six portes, rollback,
  observabilité, flags, notes, writer unique et absence de capacité de
  déploiement pour AC-152, AC-153, AC-235 et AC-261 à AC-263.
- Le runner complet exécute **344 tests sur 348 découverts**, avec quatre skips
  historiques explicitement rapportés et aucun échec.
- Issue d'exécution : `#101`. Branche : `agent/build-t022-sdd-ship`. Aucun
  reviewer, merge, shell, réseau, VPS ou déploiement n'est sollicité ou
  exécuté.
- État final : `T-022 = done`, `active_task = null`.

---

### T-022 · red transversal · 2026-08-03T14:37:47Z

- Le test de triangulation exige l'ordre
  `validate_worker_changes(T-022) → global_lock → atomic_replace` sur le seul
  chemin `.specs/<feature-id>/09-ship-plan.md`.
- Il exige aussi le refus des backticks triples dans la commande affichée afin
  qu'une donnée ne puisse pas fermer le fence Markdown.
- Résultat attendu : **9 tests exécutés, 1 échec** — l'événement de validation
  de scope manque avant le verrou et le writer.
- État : `T-022 = red`, `active_task = T-022`.

---

### T-022 · green transversal · 2026-08-03T14:41:26Z

- Le writer appelle maintenant `validate_worker_changes` pour T-022 et le seul
  `09-ship-plan.md` autorisé avant d'acquérir le verrou et d'écrire.
- Les commandes affichées refusent CR, LF, fences triples, secrets et chemins
  absolus ; elles restent des données inertes.
- Vérifications : **12/12 tests ciblés**, **13/13 skills embarqués** et
  `git diff --check` verts.
- État : `T-022 = green`, `active_task = T-022`.

---

### T-022 · refactor transversal · 2026-08-03T14:41:26Z

- Le chemin relatif autorisé est construit une fois et transmis identiquement
  au scope et aux changements du garde canonique.
- L'ordre de capacité est explicite et testé : validation, verrou, remplacement
  atomique ; aucune autre cible ni primitive n'est exposée.
- État : `T-022 = refactor`, `active_task = T-022`.

---

### T-022 · simplify transversal · 2026-08-03T14:41:26Z

- La validation de la commande reste une suite lisible de refus directs, sans
  parseur shell, allowlist fragile ni abstraction supplémentaire.
- Markdownlint, JSON et contrôle statique no-shell/no-réseau restent verts.
- État : `T-022 = simplify`, `active_task = T-022`.

---

### T-022 · done transversal · 2026-08-03T14:41:26Z

- Le runner complet confirme **344 tests sur 348 découverts**, quatre skips
  historiques et aucun échec après les deux corrections de capacité.
- Issue `#101`; branche `agent/build-t022-sdd-ship`; aucun reviewer, merge,
  réseau, VPS ou déploiement.
- PR `#103`, empilée sur `agent/build-t021-sdd-review` pour imposer l'ordre de
  fusion ; aucun reviewer n'est demandé.
- État final : `T-022 = done`, `active_task = null`.

---

## T-019 — Auditer exactement les 32 AC source S-005

### T-019 · red · 2026-08-03T13:41:55Z

- Le manifeste exécutable couvre exactement AC-015, AC-016, AC-140 à AC-147
  et AC-196 à AC-217 avec un producteur primaire unique.
- Commande : `python3 hermes/scripts/test_sdd_s005_contract.py`.
- Résultat attendu : **6 tests exécutés, 1 échec** ; les deux commandes sont
  prouvées dans la source mais `/sdd-test` et `/sdd-validate` ne sont pas encore
  publiées parmi les commandes installées.
- État : `T-019 = red`, `active_task = T-019`.

---

### T-019 · green · 2026-08-03T13:43:04Z

- Le manifeste relie les 32 AC S-005 à T-017, T-018, T-019 ou T-020 et
  vérifie les catalogues exécutables AC-196 à AC-217.
- L'audit prouve les scopes disjoints, l'ordre de fusion, le verrou runtime
  canonique et l'absence de scheduler, merge, VPS, secret ou chemin local.
- L'aide et les documents publient désormais `/sdd-test` et `/sdd-validate`
  avec leurs frontières d'écriture et leurs résultats `PASS|FAIL`.
- Vérification ciblée : **6/6 contrat S-005** verts.
- État : `T-019 = green`, `active_task = T-019`.

---

### T-019 · red transversal · 2026-08-03T13:46:31Z

- Le runner complet a découvert **33 fichiers**, puis a refusé
  `hermes/skills/sdd-test/scripts/test_guard.py` : ce module de production au
  préfixe `test_` ne contenait légitimement aucun cas `unittest`.
- Le périmètre T-019 inclut explicitement le renommage du garde et ses deux
  contrats ; le runner reste fail-closed et n'est pas assoupli.
- Résultat attendu : échec d'intégration
  `contains no unittest cases; pytest-only files are unsupported`.
- État : `T-019 = red`, `active_task = T-019`.

---

### T-019 · green transversal · 2026-08-03T13:47:07Z

- Le module de production est renommé `guard.py`; ses chargeurs, contrats et
  la future copie du profil 0.7.0 suivent ce nom non ambigu.
- Vérification ciblée : **18/18 tests** du garde, du skill et du contrat S-005
  sont verts.
- État : `T-019 = green`, `active_task = T-019`.

---

### T-019 · refactor · 2026-08-03T13:47:07Z

- Le garde `/sdd-test` porte désormais un nom de module de production clair et
  le runner conserve son inventaire fail-closed sans exception spéciale.
- Le contrat S-005 centralise le manifeste exact des 32 AC et leurs producteurs
  primaires, sans recopier les comportements des deux skills.
- Vérifications : **18/18 tests ciblés** et `git diff --check` verts.
- État : `T-019 = refactor`, `active_task = T-019`.

---

### T-019 · simplify · 2026-08-03T13:49:58Z

- Passe de clarté : chemins et ensembles métier nommés, assertions groupées par
  Test-ID, documentation limitée aux frontières d'écriture et aux sorties.
- Vérifications : **12/12 skills embarqués**, JSON, markdownlint sur six
  documents et `git diff --check` verts.
- État : `T-019 = simplify`, `active_task = T-019`.

---

### T-019 · done · 2026-08-03T13:50:40Z

- Le runner complet exécute **332 tests sur 336 découverts**, avec quatre skips
  historiques explicitement rapportés et aucun échec.
- Les sept Test-IDs couvrent le manifeste, les commandes, le DAG, les scopes,
  la capacité, la publication et les interdictions de sécurité.
- Issue d'exécution : `#96`. Branche : `agent/build-t019-s005-audit`.
  PR empilée sur T-018 : `#97`.
- Aucun reviewer n'est demandé ; aucune fusion ni opération VPS n'est exécutée.
- État final : `T-019 = done`, `active_task = null`.

---

## T-017 — Convertir `/sdd-test` et publier le catalogue AC-196 à AC-209

### T-017 · red · 2026-08-03T13:23:05Z

- Test minimal ajouté :
  `TestGuardTest.test_t017_t1_guard_is_published`.
- Commande :
  `PYTHONDONTWRITEBYTECODE=1 python3 hermes/skills/sdd-test/scripts/test_test_guard.py`.
- Résultat : **échec attendu** —
  `AssertionError: T-017-T1: test_guard.py must publish /sdd-test` ;
  **1 test exécuté, 1 échec**.
- Aucun fichier de production du skill n'existait au moment de cette preuve.
- État : `T-017 = red`, `active_task = T-017`.

---

### T-017 · green · 2026-08-03T13:27:27Z

- Production minimale publiée : arguments exacts, scope `src/test/**` et plan,
  matrice AC/types, gaps résolus, preuves structurées et expurgées, gate sous
  verrou global, publication atomique puis traçabilité.
- Le catalogue AC-196 à AC-209 vérifie les chemins et noms de quatorze preuves
  exécutables déjà présentes dans le runtime.
- Vérifications : **8/8 tests comportementaux**, **4/4 contrats statiques** et
  **40/40 tests runtime + orchestrateur** verts.
- État : `T-017 = green`, `active_task = T-017`.

---

### T-017 · refactor · 2026-08-03T13:28:37Z

- La validation du scope partage maintenant un contrôle explicite des
  composants symboliques et refuse un `src/test` redirigé.
- Le garde canonique valide le changement avant le remplacement atomique ; un
  refus ne peut donc plus publier brièvement un plan non autorisé.
- Les AC du plan doivent être uniques, en plus de respecter la forme `AC-NNN`.
- Vérification après refactor : **12/12 tests T-017** et
  `git diff --check` verts.
- État : `T-017 = refactor`, `active_task = T-017`.

---

### T-017 · simplify · 2026-08-03T13:31:06Z

- Passe `clarity-over-cleverness` : responsabilités courtes, constantes métier,
  retours anticipés et structures de preuves explicites.
- Le contrôle de fichiers temporaires du test utilise désormais des variables
  nommées ; aucune ligne Python du périmètre ne dépasse 100 caractères.
- Le skill embarqué est valide avec ses références locales et son frontmatter ;
  **11 skills Hermes** sont validés.
- Vérifications : **12/12 T-017**, markdownlint et `git diff --check` verts.
- État : `T-017 = simplify`, `active_task = T-017`.

---

### T-017 · done · 2026-08-03T13:32:10Z

- Les huit Test-IDs couvrent les arguments, le scope exact, le plan et ses
  gaps, les preuves expurgées, le verrou global, la publication atomique suivie
  de la traçabilité et le catalogue exécutable AC-196 à AC-209.
- Vérification finale : **12/12 T-017**, **40/40 runtime + orchestrateur** et
  **11/11 skills embarqués** verts ; markdownlint, JSON et
  `git diff --check` sont verts.
- Aucun fichier T-018 à T-020, document partagé, commit, push, PR, review,
  fusion ou VPS n'a été touché.
- État final : `T-017 = done`, `active_task = null`.
- Issue d'exécution : `#92`. Branche : `agent/build-t017-sdd-test`, sans
  reviewer sollicité. PR empilée : `#94`, base
  `agent/plan-s005-test-validate`, sans fusion automatique.

---

### T-017 · correction CI · 2026-08-03T13:52:35Z

- Le runner officiel a correctement refusé le module de production
  `test_guard.py`, découvert à tort comme suite sans cas `unittest`.
- Le garde est renommé `guard.py`; ses tests et contrats suivent ce chemin.
  Aucun filtre ni contournement n'est ajouté au runner fail-closed.
- La correction est reportée à T-017 afin que chaque PR empilée reste verte.

---

## T-018 — Convertir `/sdd-validate` et le fan-in des rapports

### T-018 · red · 2026-08-03T13:23:16Z

- Test minimal ajouté :
  `PublicationContractTests.test_t_018_t1_validation_guard_is_published`.
- Commande :
  `PYTHONDONTWRITEBYTECODE=1 python3 hermes/skills/sdd-validate/scripts/test_validation_guard.py -v`.
- Résultat : **échec attendu** — `AssertionError: False is not true :
  T-018-T1: /sdd-validate guard is absent`; **1 test exécuté, 1 échec**.
- État : `T-018 = red`, `active_task = T-018`. Aucun fichier de production
  n'avait été créé lors de cette preuve RED.

---

## T-015 — Convertir `/sdd-code-simplify` dans la source Hermes

### T-015 · red · 2026-08-03T12:43:39Z

- Les tests comportementaux couvrent la forme exacte de la commande, les
  cibles dangereuses, la baseline, l'isolation par fichier, les preuves et le
  mode `--dry-run`.
- Commande :
  `python3 hermes/skills/sdd-code-simplify/scripts/test_code_simplify_guard.py`.
- Résultat attendu : **5 tests exécutés, 5 échecs**, tous causés par l'absence
  de `code_simplify_guard.py`. Aucun fichier de production n'a été créé ou
  modifié avant cette preuve.
- État : `T-015 = red`, `active_task = T-015`.

---

### T-015 · green · 2026-08-03T12:48:38Z

- Le garde accepte uniquement `<path> [--dry-run]`, résout des fichiers
  concrets sous `src/main/**` et refuse arguments inconnus, tests, globs,
  symlinks, chemins externes ou absents avant écriture.
- La baseline est obligatoire. En écriture, le garde compose le lease,
  l'empreinte et la validation de scope du runtime v2 ; chaque régression
  restaure uniquement le fichier courant.
- Le rôle ne peut ni modifier un autre fichier pendant la passe courante, ni
  écrire en `--dry-run`. Les preuves conservent les argv structurés et
  expurgent secrets et chemins absolus.
- Vérification ciblée : **7/7 tests du garde**, **4/4 contrats du skill** et
  **2/2 contrats source S-004** verts ; compilation Python verte.
- État : `T-015 = green`, `active_task = T-015`.

---

### T-015 · refactor · 2026-08-03T12:49:31Z

- L'acquisition du lease et la première empreinte sont désormais dans le même
  bloc protégé : une erreur d'empreinte libère toujours le lease.
- Un test de récupération dédié prouve cette libération. Les snapshots nommés
  rendent explicite la restauration de toutes les écritures collatérales sans
  modifier le comportement nominal.
- Vérification après refactor : **8/8 garde**, **4/4 contrat du skill**,
  **2/2 contrat S-004** et `git diff --check` verts.
- État : `T-015 = refactor`, `active_task = T-015`.

---

### T-015 · simplify · 2026-08-03T12:49:47Z

- Passe `clarity-over-cleverness` : validation, baseline, lease, traitement
  fichier par fichier et résumé restent des phases linéaires aux noms directs.
  Aucun helper ou niveau d'abstraction supplémentaire ne simplifierait le flux.
- Les neuf catégories de clarté sont embarquées une seule fois dans la
  checklist ; le rôle reçoit une référence et non une copie du comportement.
- Aucun appel shell, commit, fusion ou demande de review n'existe dans le
  périmètre. Aucune ligne Python du changement ne dépasse 100 caractères.
- État : `T-015 = simplify`, `active_task = T-015`.
- Correction de régression : le runner complet a détecté que le contrat
  portable `sdd-onboard` classait encore `/sdd-code-simplify` comme planifiée.
  Son assertion est alignée sur S-004 et ajoutée explicitement au scope T-015.
- Le même runner a ensuite exposé l'assertion historique équivalente dans
  l'audit S-003. Elle vérifie désormais que la commande exacte est installée,
  sans modifier les 51 producteurs primaires de S-003.
- Issue d'exécution créée : `#88`. Branche :
  `agent/build-t015-code-simplify`, sans reviewer sollicité.

---

### T-015 · done · 2026-08-03T12:56:57Z

- Vérification finale dans l'environnement CI épinglé : **301 tests exécutés
  sur 305 découverts**, 4 skips déclarés, zéro échec ; **10 skills Hermes**
  validés ; **8 documents** lintés avec `markdownlint-cli2@0.18.1`, zéro erreur.
- Les huit Test-IDs T-015-T1 à T-015-T8 sont couverts par le garde, le contrat
  statique et l'audit source S-004. `git diff --check` et l'état JSON sont verts.
- PR empilée créée : `#89`, base `agent/plan-s004-code-simplify`, sans reviewer
  sollicité et sans fusion automatique. Issue `#88`, commit `0fe57c6`.
- État final : `T-015 = done`, `active_task = null`.

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

## T-006 — Rendre le runtime partagé portable dans le profil

### T-006 · red · 2026-08-02T00:16:53Z

- Test ajouté :
  `hermes.scripts.test_sdd_runtime_profile_contract.SddRuntimeProfileContractTest.test_distributed_plan_guard_loads_shared_runtime`
  (`T-006-T1`, `AC-048`, `AC-101`, `AC-276` à `AC-280`). La fixture copie
  le skill sous `profile/skills/sdd-plan` et le runtime partagé sous
  `profile/hermes/runtime`, puis exécute réellement le garde distribué.
- Commande ciblée :
  `/usr/bin/time -p env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest hermes.scripts.test_sdd_runtime_profile_contract.SddRuntimeProfileContractTest.test_distributed_plan_guard_loads_shared_runtime`.
- Résultat : **échec attendu** — le runtime est présent dans le profil, mais
  le calcul `Path(__file__).resolve().parents[4]` place le parent du profil
  dans `sys.path`; le garde ne peut donc pas importer `hermes.runtime`.
- Extrait expurgé :

  ```text
  FAIL: test_distributed_plan_guard_loads_shared_runtime
  T-006-T1 / AC-048, AC-101, AC-276-AC-280: profile import works.
  Traceback (most recent call last):
    File "<worktree>/hermes/scripts/test_sdd_runtime_profile_contract.py", line 47
      self.assertEqual(
  AssertionError: 0 != 1 : Traceback (most recent call last):
    File "<temporary>/profile/skills/sdd-plan/scripts/tdd_state_guard.py", line 24
      from hermes.runtime.sdd_runtime_guard import (
  ModuleNotFoundError: No module named 'hermes'
  Ran 1 test in 0.110s
  FAILED (failures=1)
  ```

- Durée rapportée par `/usr/bin/time` : `real 0.22`, `user 0.11`,
  `sys 0.05`.
- État : `T-006 = red`, `active_task = T-006`. Aucun fichier de production
  ni test existant n’a été modifié.

---

### T-006 · green · 2026-08-02T00:24:06Z

- Production minimale : `tdd_state_guard.py` reconnaît uniquement les layouts
  distribués source (`<root>/hermes/skills/...`) et profil
  (`<root>/skills/...`), puis charge le runtime partagé sous
  `<root>/hermes/runtime` sans le copier dans le skill.
- Isolation : la racine, `hermes`, `runtime` et le module doivent être réels,
  réguliers, non symboliques et résolus sous la racine choisie. Un runtime
  disponible uniquement dans le parent extérieur est refusé sans repli.
- Parité : `check_profile_parity.py` conserve son argument et ses codes de
  sortie, compare les skills puis `hermes/runtime`, et distingue les fichiers
  runtime manquants, inattendus et différents.
- Triangulation ajoutée : T-006-T2 couvre les deux layouts, T-006-T3 les trois
  formes de dérive runtime, T-006-T4 les régressions v1/v2, secrets, chemins
  relatifs et rollback, T-006-T5 les racines/runtime symboliques ou extérieurs.
- Commandes et résultats :
  - contrat profil : **4/4 verts**, `real 22,53 s` ;
  - parité : **4/4 verts**, `real 0,10 s` ;
  - plan : **17/17 verts**, `real 3,09 s` ;
  - runtime : **31/31 verts**, `real 18,58 s`.
- État intermédiaire : `T-006 = green`, `active_task = T-006`.

### T-006 · refactor · 2026-08-02T00:27:08Z

- La détection du layout et la validation du runtime ont été séparées en deux
  responsabilités nommées ; les chemins `hermes` et `runtime` ne sont calculés
  qu'une fois.
- Le test de régression distribué utilise un seul helper d'exécution consommé
  par les suites plan et runtime, sans changer leurs assertions.
- Commandes après refactor : contrat profil **4/4 vert** (`real 22,55 s`),
  parité **4/4 verte** (`real 0,10 s`) et plan **17/17 vert**
  (`real 3,11 s`).
- État intermédiaire : `T-006 = refactor`, `active_task = T-006`.

### T-006 · simplify · 2026-08-02T00:36:12Z

- Passe `clarity-over-cleverness` : la sélection du layout utilise un retour
  anticipé, les chemins métier et diagnostics répétés sont nommés, et les deux
  exécutions de suites distribuées partagent un helper avec deux consommateurs
  réels. Aucun fallback ascendant, option morte ou copie du runtime n'existe.
- Régression finale ciblée : plan **18/18 vert** (`real 2,41 s`), parité
  **5/5 verte** (`real 0,31 s`), contrat profil **4/4 vert**
  (`real 18,62 s`) et runtime **31/31 vert** (`real 18,58 s`).
- La mesure stdlib `trace` atteint **92,8 %** sur le fichier de parité complet
  et **51,4 %** sur le garde plan complet historique. Ces pourcentages de
  fichiers ne représentent pas la couverture T-006 parce que les frontières
  profil et CLI s'exécutent dans des subprocess non agrégés par `trace`.
  L'inspection des lignes ajoutées et T-006-T1 à T-006-T5 couvre toutes les
  branches atteignables ; seule la défense contre une substitution de chemin
  entre `is_symlink` et `resolve` est volontairement non provoquée.
- Gate Hermes complète locale : deux exécutions distinctes, Python 3.14 puis
  Python 3.11 (version CI), découvrent **17 fichiers** et prouvent avant
  l'interruption du superviseur macOS : **14/14 e2e**, **8/8 bridge**,
  **31/31 runtime**, **5/5 parité**. Les deux s'arrêtent à l'en-tête de
  `test_run_python_tests.py`, sans échec ni résumé global ; la CI Linux reste
  la preuve autoritative et cette limite locale n'est pas présentée comme une
  réussite complète.
- Validation complémentaire : **8 skills Hermes valides** en `0,25 s`, JSON
  valide, `git diff --check` vert, aucun secret ni chemin local ajouté. Les
  deux chemins absolus détectés dans le journal sont des preuves historiques
  antérieures à T-006.
- État final : `T-006 = done`, `active_task = null`.

---

## T-007 — Consolider la source et auditer les 84 AC S-002

### T-007 · red · 2026-08-02T12:42:36Z

- Test ajouté :
  `hermes.scripts.test_sdd_s002_contract.SddS002ContractTest.test_help_and_documentation_publish_converted_s002_commands`
  (`T-007-T3`, `AC-011`, `AC-012`, `AC-025`). Le test parse directement les
  tables Markdown de l'aide et de la documentation source ; aucune fixture ni
  copie temporaire ne remplace les fichiers suivis.
- Commande ciblée :
  `/usr/bin/time -p env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest hermes.scripts.test_sdd_s002_contract.SddS002ContractTest.test_help_and_documentation_publish_converted_s002_commands`.
- Résultat : **échec attendu** — `/sdd-epic-plan` est encore classée
  `feuille de route` dans `docs/codex-migration.md`, au lieu de `converti`.
- Extrait (10 lignes) :

  ```text
  FAIL: test_help_and_documentation_publish_converted_s002_commands
  T-007-T3 / AC-011, AC-012, AC-025: commands are public.
  Traceback (most recent call last):
    File "hermes/scripts/test_sdd_s002_contract.py", line 67, in test_help_and_documentation_publish_converted_s002_commands
      self.assertEqual(
  AssertionError: 'converti' != 'feuille de route'
  - converti
  + feuille de route
   : /sdd-epic-plan must be marked converted in docs/codex-migration.md
  FAILED (failures=1)
  ```

- Durée rapportée par `/usr/bin/time` : `real 0.07`, `user 0.04`,
  `sys 0.01`.
- État : `T-007 = red`, `active_task = T-007`. Aucun des quatre fichiers
  d'aide ou de documentation en scope n'a été modifié.

---

### T-007 · green · 2026-08-02T12:50:49Z

- Le RED T-007-T3 a été rejoué avant toute modification : **1/1 en échec**
  pour la raison consignée (`/sdd-epic-plan` encore en `feuille de route`).
- Production documentaire minimale : `/sdd-epic-plan` et
  `/sdd-wire-harness` passent dans la table des commandes disponibles de
  l'aide, la liste canonique du README et l'état `converti` de la migration.
  `sdd-roles` reste une bibliothèque interne et aucune commande publique
  `/sdd-roles` n'est ajoutée.
- T-007-T1 parse indépendamment la tâche T-007 et la ligne S-002 de la roadmap,
  puis les compare à 30 groupes de preuves structurées couvrant exactement
  **84/84 AC**. AC-123 est la seule preuve `pending-external`, explicitement
  liée à T-008 ; elle n'est pas déclarée satisfaite.
- T-007-T2 à T-007-T6 vérifient les commits, fichiers, symboles et tests réels
  des baselines #61/#57/#59, les contrats bridge/status et leurs scopes
  disjoints, les limites 2 writers/3 analyses/1 gate et les constructions
  runtime interdites par analyse AST ciblée.
- Commande ciblée T-007-T3 :
  `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest hermes.scripts.test_sdd_s002_contract.SddS002ContractTest.test_help_and_documentation_publish_converted_s002_commands`
  — **1/1 vert** en 0,001 s.
- Suite source S-002 :
  `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v hermes.scripts.test_sdd_s002_contract`
  — **6/6 verts** en 0,291 s.
- État intermédiaire : `T-007 = green`, `active_task = T-007`.

---

### T-007 · refactor · 2026-08-02T12:55:32Z

- Refactorisation sans changement de comportement : les helpers génériques
  `read` et `python_symbols` deviennent `read_repository_file` et
  `declared_python_symbols`; l'expansion des plages AC porte désormais un nom
  explicite. La cartographie, les assertions et les surfaces publiques restent
  inchangées.
- La preuve des baselines ne dépend plus de l'historique Git disponible : les
  SHA contractuels versionnés sont recoupés avec les vrais fichiers, symboles
  et méthodes de test. Le test reste déterministe dans le checkout CI shallow.
- Commande :
  `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v hermes.scripts.test_sdd_s002_contract`
  — **6/6 verts** en 0,203 s.
- État intermédiaire : `T-007 = refactor`, `active_task = T-007`.

---

### T-007 · simplify · 2026-08-02T12:59:46Z

- Passe `clarity-over-cleverness` : les 30 groupes de preuve utilisent un
  constructeur `evidence` nommé, les plages AC restent explicites et aucun
  helper spéculatif, option morte ou comportement implicite n'est ajouté.
- Régression finale T-007 : **6/6 verts** en 0,197 s. Validation structurée :
  **8/8 skills Hermes valides**, JSON valide et `git diff --check` vert.
- Markdownlint local n'a produit aucun verdict : `npx` a échoué avec
  `ENOTFOUND registry.npmjs.org`. La porte Markdown CI reste autoritative ;
  aucun succès local n'est revendiqué.
- Porte Hermes complète lancée une seule fois effectivement hors sandbox après
  un premier arrêt pré-test (`ps` interdit). Elle a découvert 18 fichiers et
  exécuté 9 fichiers : **112 tests recensés, 108 réussis et 4 ignorés**. Les
  suites E2E 14/14, bridge 8/8, runtime 31/31, parité 5/5, superviseur 37/37
  (4 ignorés), contrats profil 1/1 et 4/4, S-002 6/6 et docs 6/6 sont vertes.
  Le chargement du 10e fichier s'est arrêté avant test avec
  `ModuleNotFoundError: markdown_it`; la dépendance épinglée de CI n'est pas
  installée globalement dans ce worktree. La porte locale n'est donc pas
  déclarée verte et n'est pas relancée inchangée.
- État final : `T-007 = done`, `active_task = null`. AC-123 reste
  `pending-external` vers T-008. `04-tasks.md` n'est pas modifié car il est hors
  du scope T-007 confié à ce writer.

---

## T-008 — Publier le profil 0.5.0 avec parité skills/runtime

### T-008 · red · 2026-08-02T18:31:54Z

- Test ajouté :
  `scripts.test_validate_distribution.DistributionValidatorTest.test_release_0_5_0_includes_sdd_commands_and_shared_runtime`
  (`T-008-T1`, `AC-011`, `AC-012`, `AC-025`, `AC-026`, `AC-123`,
  `AC-278`). Le contrat exige d'abord la version 0.5.0, puis les deux skills
  publics et le package du runtime partagé par des chemins distribués réels.
- Commande ciblée :
  `/usr/bin/time -p env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/private/tmp/hermes-t008-markdown-stub /opt/miniconda3/bin/python3 -m unittest scripts.test_validate_distribution.DistributionValidatorTest.test_release_0_5_0_includes_sdd_commands_and_shared_runtime`.
- Résultat : **échec attendu** — le manifeste déclare encore exactement
  `0.4.8`, alors que le contrat de release attend `0.5.0`.
- Extrait (10 lignes) :

  ```text
  FAIL: test_release_0_5_0_includes_sdd_commands_and_shared_runtime (scripts.test_validate_distribution.DistributionValidatorTest.test_release_0_5_0_includes_sdd_commands_and_shared_runtime)
  T-008-T1 / AC-011, AC-012, AC-025, AC-026, AC-123, AC-278.
  Traceback (most recent call last):
    File "scripts/test_validate_distribution.py", line 54, in test_release_0_5_0_includes_sdd_commands_and_shared_runtime
      self.assertEqual("0.5.0", manifest["version"])
  AssertionError: '0.5.0' != '0.4.8'
  - 0.5.0
  + 0.4.8
  Ran 1 test in 0.001s
  FAILED (failures=1)
  ```

- Durée rapportée par `/usr/bin/time` : `real 0.26`, `user 0.08`,
  `sys 0.03`.
- Environnement : `markdown-it-py` n'est pas installé localement ; le stub
  d'import temporaire hors dépôt ne participe à aucune assertion et sert
  uniquement à charger ce test de métadonnées ciblé.
- État : `T-008 = red`, `active_task = T-008`. Aucun fichier de production,
  manifeste, skill, runtime ou documentation n'a été modifié.

---

### T-008 · green · 2026-08-02T18:43:46Z

- Le RED de release a été rejoué avant toute copie et a échoué exactement sur
  `0.5.0 != 0.4.8` : **1/1 échec attendu** en 0,001 s.
- Copie mécanique sans transformation : **31/31 fichiers skills** en scope,
  puis **7/7 fichiers runtime**. Après le premier groupe, la parité ne signalait
  plus que les sept fichiers runtime absents ; après le second, elle confirme
  **65 fichiers skills et 7 fichiers runtime identiques**.
- Runner minimal : la découverte suivie/non ignorée couvre désormais
  `skills/**/test_*.py` et les tests directs `hermes/runtime/test_*.py` dans le
  même superviseur. Chaque fichier reste refusé s'il ne découvre ou n'exécute
  aucun cas `unittest` non ignoré.
- Triangulation du runner : le nouveau test mixte a d'abord échoué parce que le
  fichier runtime n'était pas découvert, puis réussit **1/1 en 0,931 s** hors
  sandbox macOS. La suite du runner réussit **66/66 tests en 28,897 s**, avec
  trois tests conditionnels ignorés.
- Métadonnées minimales : `distribution.yaml` vaut `0.5.0`; le changelog et le
  README publient epic-plan, wire-harness et le runtime partagé. Le rollback
  nomme explicitement la réinstallation du profil 0.4.8 sans suppression ni
  reconversion des états v2, journaux, branches ou worktrees.
- Le contrat T-008-T1 devient **vert, 1/1 en 0,001 s**. Le contrat historique
  T-002 conserve ses trois assertions sur la présence documentée de 0.4.8,
  désormais comme entrée de release antérieure.
- État intermédiaire : `T-008 = green`, `active_task = T-008`. La gate lourde
  de tous les tests profil reste réservée à la passe finale après simplification.

---

### T-008 · refactor · 2026-08-02T18:44:58Z

- Relecture structurelle : la sélection des deux racines de tests reste dans
  la découverte existante et réutilise l'unique superviseur. Aucun second
  runner, ordonnanceur, mode ou option n'a été ajouté.
- Le contrat historique de 0.4.8 vérifie désormais explicitement qu'au moins
  deux releases sont présentes avant d'accéder à la release précédente. Il
  conserve ses assertions de version, changelog et README sans masquer 0.5.0.
- Commande ciblée : les contrats de release 0.4.8 historique et 0.5.0 courant
  réussissent **2/2 en 0,001 s**.
- Aucun refactor des 38 fichiers copiés n'est autorisé : ils restent strictement
  byte-for-byte avec la source canonique.
- État intermédiaire : `T-008 = refactor`, `active_task = T-008`.

---

### T-008 · simplify · 2026-08-02T18:46:14Z

- Passe `clarity-over-cleverness` : la découverte filtre d'abord le nom de test,
  sélectionne ensuite explicitement la racine skill ou runtime, puis applique
  les contrôles de fichier sûr. Les versions courante et précédente sont des
  constantes nommées dans le contrat de release.
- Aucun ternaire imbriqué, option morte, paramètre inutilisé, second runner ou
  helper spéculatif n'est introduit. Les 38 fichiers canoniques restent
  inchangés et byte-for-byte avec la source.
- Preuves post-simplification : runner mixte **1/1 vert en 0,964 s**, contrats
  de release **2/2 verts en 0,001 s**, parité exacte **65 skills + 7 runtime**
  et `git diff --check` vert.
- État conservé intentionnellement : `T-008 = simplify`,
  `active_task = T-008`. T-008-T7 exige encore CI, review `approve`, zéro fil
  actionnable et go humain avant fusion ; la tâche n'est donc pas `done`.

### T-008 · waiting-publication-gate · 2026-08-02T18:46:14Z

- Les portes locales finales, la PR profil et ses deux checks restent à produire.
- La branche source/meta demeure un ledger actif non commité et non poussé.
- Aucune fusion, installation de profil, mise à jour VPS ou déploiement n'est
  autorisé dans cette attente.

### T-008 · publication-checkpoint · 2026-08-02T18:56:56Z

- Gate profil complète : **10/10 fichiers de test**, **137/137 cas exécutés**,
  zéro ignoré, en environ **59,4 s**. Elle couvre les deux tests runtime, plan,
  epic-plan, wire-harness, status, onboard, spec-review et leurs contrats.
- Suite distribution locale : **226 tests en 131,867 s**, avec deux échecs
  déterministes de fixtures SemVer qui remplaçaient encore la version 0.4.8 et
  trois tests conditionnels ignorés. Après correction dans le scope, les deux
  tests ciblés réussissent **2/2 en 1,075 s** ; la suite complète n'est pas
  déclarée verte localement sans relance inchangée.
- Validateur autonome : **8 skills valides**. Parité : **65 skills + 7 runtime
  identiques**. `git diff --check` : vert. Markdownlint local a été interrompu
  après 60 s sans sortie ; aucune réussite locale Markdown n'est revendiquée.
- Commit profil : `5042e33038a9b22f04da8b91e9e1d8b617d96a39`, **44 fichiers**,
  **9 633 insertions et 60 suppressions**, poussé sur
  `agent/build-t008-profile-050`.
- PR profil : `staaack-io/hermes-agent-profile-staaack#48`, ouverte en draft
  avec `Closes #47`, puis passée prête après CI verte.
- CI Linux autoritative : **2/2 checks verts** — `Skills / Python tests` en
  **20 s** et `Distribution / Validate, docs and diff` en **1 min 32 s**. Ce
  second check couvre la suite distribution complète, le validateur,
  Markdownlint et le diff.
- État GitHub : `MERGEABLE/CLEAN`, **0 review**, décision de review vide et
  **0 fil de review**. T-008-T7 reste donc incomplète : une review `approve` et
  un go humain explicite sont encore requis avant toute fusion.
- État maintenu : `T-008 = simplify`, `active_task = T-008`. La branche
  source/meta reste non commitée et non poussée ; la branche profil est propre.

---

### T-008 · done · 2026-08-02T18:59:05Z

- Le go humain explicite a été reçu après présentation du SHA profil, des deux
  checks CI verts, de l'état `MERGEABLE/CLEAN`, de l'absence de fils et de
  l'absence de review formelle.
- La review `approve` prévue par T-008-T7 reste absente. Comme pour le profil
  0.4.8, cette absence est consignée comme une dérogation explicite : le nouvel
  `AGENTS.md` rend `$review` facultatif et le go utilisateur autorise la fusion
  sans revendiquer une approbation inexistante.
- PR profil `staaack-io/hermes-agent-profile-staaack#48` fusionnée à
  `2026-08-02T18:59:05Z`, depuis la tête
  `5042e33038a9b22f04da8b91e9e1d8b617d96a39` vers le commit de fusion
  `e0e518b9d2b7e1e7c708546e9d4b02da945078ce`.
- La publication source/profil 0.5.0 est complète : **65 fichiers skills et 7
  fichiers runtime identiques**, **137/137 tests profil** et **2/2 checks CI**.
- Aucun profil VPS n'a été installé ou mis à jour ; aucun gateway, board,
  déploiement ou état distant Hermes n'a été modifié.
- État final : `T-008 = done`, `active_task = null`.

---

## T-009 — Orchestrer `/sdd-build` mono-tâche et ses preuves

### T-009 · red · 2026-08-03T07:13:58Z

- Tests ajoutés uniquement dans
  `hermes/skills/sdd-build/scripts/test_build_guard.py` et
  `hermes/skills/sdd-build/scripts/test_skill_contract.py` : **15 méthodes**
  couvrent T-009-T1 à T-009-T9 sans réseau, runtime externe ou écriture de
  production.
- Commande ciblée :
  `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest hermes/skills/sdd-build/scripts/test_build_guard.py -k test_t009_t1_public_arguments_are_validated_before_mutation`.
- Résultat : **échec attendu**, code retour `1`, **1/1 test rouge en 0,001 s**.
- Extrait expurgé :

  ```text
  FAIL: test_t009_t1_public_arguments_are_validated_before_mutation
  T-009-T1: malformed public arguments fail before mutation.
  Traceback (most recent call last):
    test_build_guard.py, line 138, in test_t009_t1_public_arguments_are_validated_before_mutation
      guard = load_guard()
    test_build_guard.py, line 38, in load_guard
      raise AssertionError(
  AssertionError: build_guard.py must implement the /sdd-build sequential guard
  Ran 1 test in 0.001s
  FAILED (failures=1)
  ```

- La suite RED complète a cartographié **20 échecs/subtests attendus** : le
  garde, le skill et les six références de contrat/rôles n'existent pas encore.
- État : `T-009 = red`, `active_task = T-009`. Aucune production n'a été créée
  avant cette preuve durable.

### T-009 · red-triangulation · 2026-08-03T07:20:50Z

- La relecture du premier GREEN a révélé que le garde réutilisait des
  validateurs mais n'appelait pas encore les primitives runtime imposées par
  la conception. Un test AST comportemental a été ajouté sans modifier la
  production.
- Commande ciblée :
  `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest hermes/skills/sdd-build/scripts/test_skill_contract.py -k test_t009_t4_t8_t9_guard_composes_canonical_runtime_primitives`.
- Résultat : **échec attendu**, code retour `1`, **1/1 test rouge en 0,003 s**.
- Écart exact : appels absents à `validate_state`, `acquire_scope_lease`,
  `validate_red_gate`, `repository_fingerprint`, `validate_worker_changes`,
  `append_job_event` et `release_scope_lease`.
- État maintenu : `T-009 = red`, `active_task = T-009`. Le premier GREEN n'est
  pas retenu comme porte de progression tant que cette composition canonique
  n'est pas prouvée.

---

### T-009 · green · 2026-08-03T07:27:17Z

- Le skill `/sdd-build <feature-id> <T-NNN>` publie un cœur injecté et une
  façade canonique `run_runtime_task`. La façade valide l'état v2, acquiert le
  lease exact, protège l'empreinte hors scope, journalise les quatre phases,
  applique la porte RED avant GREEN, contrôle les changements et libère le
  lease dans un `finally`.
- Les sept primitives prévues sont composées sans duplication :
  `validate_state`, `acquire_scope_lease`, `validate_red_gate`,
  `repository_fingerprint`, `validate_worker_changes`, `append_job_event` et
  `release_scope_lease`.
- Les quatre contrats de rôles séparent test-engineer et implementer pour
  Spring et React/Next.js. Les rôles ne reçoivent aucun handle vers
  `04-tasks.md`, `.tdd-state.json` ou `05-implementation-log.md`.
- Preuve comportementale sur dépôt Git jetable : cycle complet, quatre
  événements vérifiés, refus hors scope et artefact partagé, lease libéré après
  échec puis reprise réussie : **1/1 vert en 6,067 s**.
- Suite T-009 inchangée : **17/17 tests verts en 5,980 s** (`real 6,08 s`).
- Régression runtime partagée : **31/31 tests verts en 17,952 s**
  (`real 18,07 s`). `git diff --check` est vert.
- État : `T-009 = green`, `active_task = T-009`.

---

### T-009 · refactor · 2026-08-03T07:30:52Z

- Refactor interne limité à `build_guard.py` : contrat de tâche typé,
  validation des fichiers modifiés centralisée et construction uniforme des
  événements de phase.
- Les sept contournements de typage ont été supprimés ; les scopes état et
  délégation portent désormais des noms explicites. L'API publique et les sept
  appels runtime canoniques restent inchangés.
- Deux boucles intermédiaires sont restées vertes : **17/17 en 5,584 s**, puis
  **17/17 en 5,719 s**.
- Vérification indépendante après refactor : **17/17 T-009 en 6,421 s** et
  **31/31 runtime en 17,805 s**. `git diff --check` est vert.
- État : `T-009 = refactor`, `active_task = T-009`.

---

### T-009 · simplify · 2026-08-03T07:39:36Z

- Passe `clarity-over-cleverness` limitée à `build_guard.py` : phase RED
  nommée, gardes anticipées, wrappers d'exception redondants retirés, état
  intermédiaire inutile supprimé et writer durable rendu explicite.
- Aucun ternaire imbriqué, option morte, paramètre inutilisé,
  `type: ignore`, ligne supérieure à 100 caractères ou abstraction parallèle
  T-010 n'est introduit.
- Après la dernière micro-passe : **17/17 T-009 en 6,313 s** et **31/31 runtime
  en 18,237 s**.
- Porte skills pertinente exécutée sur les dix fichiers de tests suivis :
  **115/115 verts en 49,589 s** ; vérification indépendante finale :
  **115/115 en 54,808 s** (`real 55,12 s`).
- Le runner global optionnel a validé 112 cas, avec quatre cas conditionnels
  ignorés, puis s'est arrêté sur l'absence locale de `markdown_it`. Aucune
  dépendance n'a été ajoutée et aucune réussite globale n'est revendiquée.
- `git diff --check` est vert.

### T-009 · done · 2026-08-03T07:39:36Z

- Les neuf Test-IDs T-009-T1 à T-009-T9 sont couverts par **17 tests** et les
  quatre phases RED, GREEN, REFACTOR et SIMPLIFY sont consignées.
- Les fichiers modifiés restent strictement dans le scope T-009 : deux tests,
  un garde, un skill et six références de contrat/rôles, plus les deux
  artefacts partagés écrits par l'agent principal.
- Issue d'exécution : `#76`. Branche : `agent/build-t009-sdd-build`.
- État final : `T-009 = done`, `active_task = null`.

---

### T-009 · ci-correction · 2026-08-03T07:47:02Z

- PR `#77`, premier run `30794572000` : documentation verte en **39 s** ;
  tests/contrats Hermes rouges en **53 s**.
- Cause exacte : le runner isolé retire la racine du dépôt de `sys.path` ;
  l'import de package `hermes.runtime` échouait avec `ModuleNotFoundError`
  avant l'exécution des tests T-009.
- Correctif borné à `build_guard.py` : résolution sûre du runtime partagé dans
  les dispositions source `hermes/skills/...` et profil `skills/...`, refus des
  chemins symboliques et réutilisation du même module vérifié pour conserver
  l'identité de `GuardError` entre chargements isolés.
- Reproduction avant correction depuis le dossier du test : **10 tests,
  12 erreurs** sur l'import manquant. Après correction : **10/10 tests du garde
  en 6,637 s** et **7/7 contrats en 0,007 s**.
- Runner Hermes exact hors sandbox : E2E **14/14**, bridge **8/8**, runtime
  **31/31**, parité **5/5**, runner **37/37** avec quatre skips, onboarding
  **1/1**, profil runtime **4/4**, S-002 **6/6** et docs **6/6** verts. Il
  s'arrête ensuite uniquement sur `markdown_it` absent localement ; cette étape
  était **32/32 verte en CI** avant le test T-009. Aucune dépendance ajoutée.
- `git diff --check` reste vert ; état TDD maintenu `done`.

---

## T-010 — Admettre et créer les cartes du build parallèle

### T-010 · red · 2026-08-03T11:12:21Z

- Tests ajoutés : `hermes/runtime/test_sdd_build_orchestrator.py`, couvrant
  T-010-T1 à T-010-T9 et AC-020 à AC-023, AC-027 à AC-029, AC-031,
  AC-128 à AC-133, AC-236 et AC-260.
- Commande :
  `python3 -m unittest hermes.runtime.test_sdd_build_orchestrator.ParallelBuildOrchestratorTest.test_t010_t1_parallel_cli_requires_structured_parallel_arguments`.
- Résultat : **échec attendu** —
  `AssertionError: T-010-T1: sdd_build_orchestrator.py must implement parallel admission` ;
  **1 test exécuté, 1 échec**.
- La branche T-010 est empilée sur le commit T-009 `e1449d437f...` sans
  fusionner la PR #77. Cette décision suit l'instruction utilisateur explicite
  de poursuivre le développement sans demander de review.
- État : `T-010 = red`, `active_task = T-010`. Aucun code de production T-010
  n'existait lors de cette preuve RED.

---

### T-010 · green · 2026-08-03T11:17:41Z

- Production minimale : `sdd_build_orchestrator.py` effectue une seule passe
  d'admission, valide les arguments et l'état v2, sélectionne les scopes
  disjoints, crée les cartes et confie exclusivement leur dispatch au Kanban.
- Intégration publique : `build_guard.py` conserve le chemin mono-tâche et route
  `--parallel` vers l'orchestrateur canonique ; `SKILL.md` et
  `build-orchestrator-contract.md` publient les invariants.
- Tests T-010 : **9/9 verts en 6,065 s**. Garde build complet : **12/12 verts
  en 5,360 s**. Runtime partagé : **31/31 verts en 17,197 s**. Contrat du skill :
  **7/7 verts en 0,008 s**.
- `py_compile` des quatre fichiers Python modifiés et `git diff --check` sont
  verts.
- État : `T-010 = green`, `active_task = T-010`.

---

### T-010 · refactor · 2026-08-03T11:19:29Z

- La séquence acquisition → dispatch → libération ciblée en cas d'échec est
  extraite dans `_dispatch_admitted_card`. La passe principale ne conserve que
  la sélection, la création de carte et le suivi `active|queued|failed`.
- Aucun contrat public ni comportement n'a changé. La constante métier
  `FAILED_STATUS` remplace le littéral répété de statut.
- Vérifications après refactor : **9/9 T-010 en 6,615 s**, **12/12 garde build
  en 5,883 s** et **31/31 runtime en 17,539 s**.
- État : `T-010 = refactor`, `active_task = T-010`.

---

### T-010 · simplify · 2026-08-03T11:25:40Z

- Passe `clarity-over-cleverness` : import mort retiré, plafond workers centralisé
  par `MAX_WORKERS`, noms métier explicites et aucune ligne Python supérieure à
  100 caractères dans les quatre fichiers modifiés.
- Vérifications ciblées après simplification : **9/9 T-010**, **12/12 garde
  build**, **7/7 contrat du skill** et **31/31 runtime** verts.
- Le superviseur global a découvert 21 fichiers et validé E2E **14/14**,
  orchestrateur **9/9**, bridge **8/8**, runtime **31/31**, parité **5/5**,
  superviseur **37/37 avec 4 skips conditionnels**, onboarding **1/1**, profil
  runtime **4/4**, contrat S-002 **6/6** et documentation **6/6**. Il s'arrête
  ensuite sur `ModuleNotFoundError: markdown_it` dans `test_validate_skills.py`,
  écart d'environnement identique à T-009. Aucun runtime local fourni ne porte
  ce module et aucune dépendance n'a été ajoutée.
- Issue d'exécution créée : `#78`. Branche :
  `agent/build-t010-parallel-admission`. PR empilée : `#79`, basée sur la
  branche de T-009 jusqu'à sa fusion.
- État : `T-010 = simplify`, `active_task = T-010`.

---

### T-010 · done · 2026-08-03T11:26:28Z

- Les neuf Test-IDs T-010-T1 à T-010-T9 couvrent les 16 AC de la tâche dans
  neuf tests runtime et deux tests d'intégration au garde public.
- Vérification finale : **9/9 T-010 en 6,799 s**, **12/12 garde build en
  5,923 s**, **7/7 contrat du skill en 0,047 s**, **31/31 runtime en 17,312 s**
  et **6/6 documentation en 2,109 s** ; `git diff --check` est vert.
- Aucun scheduler Python concurrent, `delegate_task`, force-push, reset
  destructif, suppression de worktree ou fusion automatique n'est exposé.
- État final : `T-010 = done`, `active_task = null`.

---

### T-010 · ci-correction · 2026-08-03T11:34:00Z

- PR `#79`, run `30809707342` : documentation verte ; les **270 tests Hermes
  découverts** sont verts avec deux skips conditionnels.
- Cause exacte de l'échec final : `validate_skills.py` refuse le lien
  `../../runtime/build-orchestrator-contract.md` car une référence locale d'un
  skill ne peut sortir de son propre dossier.
- Correctif minimal : retirer uniquement ce lien de la liste publiée par le
  skill. Le contrat runtime reste versionné et couvert directement par
  `test_sdd_build_orchestrator.py`.
- Aucun comportement, test, dépendance ou seuil de qualité n'est modifié.

---

## T-011 — Isoler l'enveloppe Git, Hermes et GitHub d'un job

### T-011 · red · 2026-08-03T11:31:20Z

- Tests ajoutés : `hermes/runtime/test_sdd_job_execution.py`, couvrant
  T-011-T1 à T-011-T7 et AC-030, AC-032 à AC-036, AC-233 et AC-234.
- Commande :
  `python3 -m unittest hermes.runtime.test_sdd_job_execution.JobExecutionTest.test_t011_t1_materializes_the_complete_job_envelope`.
- Résultat : **échec attendu** —
  `AssertionError: T-011-T1: sdd_job_execution.py must materialize an admitted job` ;
  **1 test exécuté, 1 échec**.
- La branche T-011 est empilée sur le commit T-010 `d7dae15` sans fusion ni
  demande de review, conformément à l'instruction utilisateur.
- État : `T-011 = red`, `active_task = T-011`. Aucun code de production T-011
  n'existait lors de cette preuve RED.

---

### T-011 · green · 2026-08-03T11:36:27Z

- Production minimale : `sdd_job_execution.py` compose le bridge GitHub S-002
  avec des adaptateurs idempotents pour branche, worktree, session, issue enfant
  et PR brouillon.
- La reprise lit d'abord l'enveloppe durable. Un échec ne journalise que son type
  et ne supprime aucune ressource déjà créée.
- Contrat publié dans `job-execution-contract.md` sans exposer de nettoyage ou
  fusion automatique.
- Vérifications : **7/7 T-011**, **8/8 bridge GitHub**, **9/9 orchestrateur** et
  **31/31 runtime** verts.
- État : `T-011 = green`, `active_task = T-011`.

---

### T-011 · refactor · 2026-08-03T11:37:49Z

- Les phases locales Git/Hermes et distante GitHub sont extraites dans
  `_ensure_local_surfaces` et `_create_github_surfaces`. L'ordre, les arguments
  idempotents et la frontière de journalisation restent inchangés.
- Vérifications après refactor : **7/7 T-011**, **8/8 bridge GitHub** et
  `git diff --check` verts.
- État : `T-011 = refactor`, `active_task = T-011`.

---

### T-011 · simplify · 2026-08-03T11:38:32Z

- Passe `clarity-over-cleverness` : responsabilités nommées, retours anticipés,
  constantes métier et zéro ligne Python supérieure à 100 caractères.
- Aucun paramètre mort, branche de nettoyage, chemin absolu, transcript brut,
  secret, donnée personnelle ou contenu métier n'est transmis au journal.
- L'API de production ne contient aucune surface de force-push, reset,
  suppression de branche/worktree ou fusion.
- Issue d'exécution créée : `#80`. Branche :
  `agent/build-t011-job-envelope`. PR empilée : `#81`, basée sur la branche
  T-010 jusqu'à son intégration.
- État : `T-011 = simplify`, `active_task = T-011`.

---

### T-011 · done · 2026-08-03T11:39:27Z

- Les sept Test-IDs T-011-T1 à T-011-T7 couvrent les huit AC de la tâche dans
  sept tests comportementaux déterministes.
- Vérification finale : **7/7 T-011 en 0,018 s**, **8/8 bridge en 0,011 s**,
  **9/9 orchestrateur en 6,313 s**, **31/31 runtime en 16,181 s** et **6/6
  documentation en 1,986 s** ; `git diff --check` est vert.
- La branche, le worktree, la session, l'issue et la PR sont isolés et
  récupérables par clé de job ; aucune ressource n'est supprimée sur échec.
- État final : `T-011 = done`, `active_task = null`.

---

## T-012 — Appliquer le go humain et le fan-in de vague

### T-012 · red · 2026-08-03T11:43:56Z

- Tests ajoutés : `hermes/runtime/test_sdd_wave_synthesizer.py`, couvrant
  T-012-T1 à T-012-T8 et AC-045 à AC-047, AC-134 à AC-137 et AC-231.
- Commande :
  `python3 -m unittest hermes.runtime.test_sdd_wave_synthesizer.WaveSynthesizerTest.test_t012_t1_completed_wave_has_one_synthesis_surface`.
- Résultat : **échec attendu** —
  `AssertionError: T-012-T1: sdd_wave_synthesizer.py must implement wave synthesis` ;
  **1 test exécuté, 1 échec**.
- La branche T-012 est empilée sur le commit T-011 `a8f9b46`, sans fusion ni
  demande de review.
- État : `T-012 = red`, `active_task = T-012`.

---

### T-012 · green · 2026-08-03T11:45:39Z

- Production minimale : observation séparée des gates techniques, du go humain
  et de la fusion déjà réalisée ; vérification des journaux ; appel unique au
  fan-in transactionnel ; création idempotente d'une PR brouillon de fan-in.
- `next_wave_admissible` reste faux tant que la fusion humaine de la PR de
  fan-in n'est pas observée.
- Le test de reprise réel injecte un crash avant marqueur et prouve la
  restauration de l'ancien ensemble complet des trois artefacts.
- Vérification : **8/8 T-012 verts en 0,877 s**.
- État : `T-012 = green`, `active_task = T-012`.

---

### T-012 · refactor · 2026-08-03T11:46:59Z

- `_ensure_fan_in_pr` isole la récupération/création idempotente de la PR et
  garde `synthesize_wave` centré sur l'ordre journal → transaction → PR → gate.
- T-012-T8 prouve maintenant les deux côtés du marqueur : rollback complet
  avant marqueur et roll-forward complet après marqueur.
- Vérification après refactor : **8/8 T-012 en 1,738 s** et
  `git diff --check` vert.
- État : `T-012 = refactor`, `active_task = T-012`.

---

### T-012 · simplify · 2026-08-03T11:48:01Z

- Passe `clarity-over-cleverness` : fonctions courtes par transition, constantes
  de statuts, retours anticipés et zéro ligne Python supérieure à 100 caractères.
- Aucune demande de review, fusion, boucle concurrente, suppression ou commande
  Git destructive n'est exposée.
- Issue d'exécution créée : `#82`. Branche :
  `agent/build-t012-wave-fan-in`. PR empilée : `#83`, basée sur la branche
  T-011 jusqu'à son intégration.
- État : `T-012 = simplify`, `active_task = T-012`.

---

### T-012 · done · 2026-08-03T11:48:53Z

- Les huit Test-IDs T-012-T1 à T-012-T8 couvrent les huit AC de la tâche dans
  huit tests, dont deux récupérations transactionnelles réelles.
- Vérification finale : **8/8 T-012 en 1,710 s**, **31/31 runtime en 15,949 s**,
  **8/8 bridge en 0,009 s**, **7/7 enveloppe job en 0,015 s** et **6/6
  documentation en 1,881 s** ; `git diff --check` est vert.
- Le synthesizer n'infère jamais le go, ne fusionne rien et bloque la vague
  suivante jusqu'à observation de la PR de fan-in fusionnée ailleurs.
- État final : `T-012 = done`, `active_task = null`.

---

## T-013 — Auditer la source S-003 sur exactement 51 AC

### T-013 · red · 2026-08-03T11:54:43Z

- Contrat agrégé ajouté dans `hermes/scripts/test_sdd_s003_contract.py` pour
  T-013-T1 à T-013-T7 et les 51 AC de S-003.
- Commande : `python3 hermes/scripts/test_sdd_s003_contract.py`.
- Résultat : **échec attendu** — `/sdd-build` manque dans les commandes
  installées et les marqueurs de capacité S-003 manquent dans le README runtime ;
  **6 tests exécutés, 3 échecs**.
- Le test de scopes a été aligné sur le plan approuvé : le chevauchement
  T-009/T-010 est sérialisé par dépendance ; T-010/T-011 et T-011/T-012 sont
  disjoints.
- État : `T-013 = red`, `active_task = T-013`. Aucun document de production
  n'avait été modifié lors de la preuve RED.

---

### T-013 · green · 2026-08-03T11:58:01Z

- Les cinq documents publient désormais `/sdd-build`, ses trois surfaces
  runtime, sa capacité 2/3/1, la vue status sans inférence et le fan-in borné
  par un go explicite observé.
- `/sdd-help` déplace uniquement `/sdd-build` vers les commandes installées ;
  `/sdd-code-simplify` reste planifiée pour S-004.
- Vérifications : **6/6 contrat S-003**, **56/56 suites build, orchestrateur,
  job, fan-in, bridge et status**, puis **49/49 runtime, S-002, S-003 et
  documentation** verts.
- État : `T-013 = green`, `active_task = T-013`.

---

### T-013 · refactor · 2026-08-03T11:59:31Z

- Le manifeste de preuves a été mis en forme pour garder une entrée lisible par
  groupe d'AC et les contrôles AST ont reçu des variables intermédiaires
  explicites.
- L'audit Git destructif couvre aussi `--force-with-lease`, sans changer la
  politique : force-push, reset dur et fusion par commande restent interdits.
- Vérification après refactor : **6/6 S-003** et `git diff --check` verts ;
  aucune nouvelle ligne supérieure à 100 caractères dans le périmètre modifié.
- État : `T-013 = refactor`, `active_task = T-013`.

---

### T-013 · simplify · 2026-08-03T12:00:50Z

- Passe `clarity-over-cleverness` : le contrat reste un manifeste déclaratif,
  les parsers sont courts et chaque test correspond à une responsabilité
  T-013 explicite. Aucun helper supplémentaire ne réduirait la complexité.
- Les documents distinguent clairement la commande installée, les commandes
  encore planifiées et les opérations volontairement absentes du runtime.
- Issue d'exécution créée : `#84`. Branche :
  `agent/build-t013-s003-audit`, empilée sur T-012 sans solliciter de review.
- État : `T-013 = simplify`, `active_task = T-013`.

- Correction de régression : le runner complet a détecté que le contrat
  portable `sdd-onboard` classait encore `/sdd-build` comme planifié. Son
  assertion est alignée sur S-003 et le fichier est ajouté explicitement au
  scope T-013 ; `/sdd-code-simplify` reste vérifié comme planifié.

---

### T-013 · done · 2026-08-03T12:09:39Z

- Le manifeste exécutable relie exactement **51/51 AC S-003** à un producteur
  primaire unique et à une preuve source présente.
- Vérification finale dans l'environnement CI épinglé : **287 tests exécutés
  sur 291 découverts**, 4 skips déclarés, zéro échec ; **9 skills Hermes**
  validés ; **7 documents** lintés avec `markdownlint-cli2@0.18.1`, zéro erreur.
- Le test portable onboarding est aligné sur la commande convertie et le contrat
  de sécurité ne détecte aucun ordonnanceur concurrent, secret, chemin local,
  force-push, reset dur, auto-merge ou commande de fusion.
- `git diff --check` est vert. État final : `T-013 = done`,
  `active_task = null`.
- PR empilée créée : `#85`, base `agent/build-t012-wave-fan-in`, sans reviewer
  sollicité. L'issue `#84`, le commit `df9a245` et les preuves locales y sont
  liés.

---

### T-018 · green · 2026-08-03T13:27:42Z

- Le garde applique les préconditions harness/tâches/résultats, refuse les
  bypass, route Spring et React/Next.js depuis les sources modifiées et compose
  `runtime.global_lock` autour de chacune des quatre gates lourdes.
- Le fan-in n'accepte que des résultats spécialisés structurés ; les rôles ne
  reçoivent aucun handle partagé et le writer est borné à
  `07-validation-report.md` et `07a-traceability.md`.
- Les enums sont fermés à `approve|request-changes` et `PASS|FAIL`; le catalogue
  AC-210–217 pointe vers des méthodes de test exécutables existantes.
- Vérifications : **8/8 tests du garde** et **4/4 contrats du skill** verts.
- État : `T-018 = green`, `active_task = T-018`.

---

### T-018 · refactor · 2026-08-03T13:30:00Z

- La lecture de fraîcheur accepte le schéma réel du harness
  (`started_at`, `gates`) ainsi que le schéma unitaire explicite, puis normalise
  le résultat en `PASS|FAIL`.
- La collecte des preuves remplace les chemins du dépôt et les signatures de
  tokens par des marqueurs expurgés avant le fan-in.
- Le writer des deux rapports est désormais lui aussi enfermé dans le verrou
  global canonique, sans changer sa surface autorisée.
- Vérifications après refactor : **9/9 garde**, **4/4 contrat skill** et
  **47/47 tests GitHub, runtime transactionnel et wave synthesizer** verts.
- État : `T-018 = refactor`, `active_task = T-018`.

---

### T-018 · simplify · 2026-08-03T13:32:42Z

- Passe `clarity-over-cleverness` : chaque frontière reste une fonction courte
  et nommée par son intention (`validate_preconditions`, `route_validators`,
  `execute_heavy_gates`, `fan_in`, `write_reports`).
- Aucun mode spéculatif, abstraction à implémentation unique, shell libre ou
  option morte n'a été conservé. Les quatre gates utilisent une boucle
  explicite dans un ordre stable.
- Vérifications : **9/9 garde**, **4/4 contrat skill**, validation syntaxique,
  **11 skills intégrés validés**, **8 documents Markdown sans erreur** et
  `git diff --check` vert.
- État : `T-018 = simplify`, `active_task = T-018`.

---

### T-018 · done · 2026-08-03T13:33:34Z

- T-018 couvre T-018-T1 à T-018-T8 et AC-143 à AC-146 ainsi que le catalogue
  exécutable AC-210 à AC-217.
- Preuves finales : **13/13 tests propres au skill**, **47/47 tests GitHub et
  transactionnels**, **11 skills intégrés validés**, **8 documents lintés**,
  JSON d'état valide et `git diff --check` vert.
- Aucun reviewer ni review n'a été sollicité ; aucun commit, push, PR, merge,
  accès VPS ou déploiement n'a été exécuté.
- État final : `T-018 = done`, `active_task = null`.
- Issue d'exécution : `#93`. Branche : `agent/build-t018-sdd-validate`, sans
  reviewer sollicité. PR empilée : `#95`, base
  `agent/build-t017-sdd-test`, sans fusion automatique.

---

### T-031 · red · 2026-08-03T16:49:58Z

- Le contrat comportemental couvre T-031-T1 à T-031-T6 : limites Kanban,
  délégation bornée, auto-approve désactivé, vérification finale, dry-run
  Super Lily, inertie, board explicite, expurgation et modèle JSON validé.
- Commande :
  `PYTHONDONTWRITEBYTECODE=1 /private/tmp/hermes-t013-venv/bin/python hermes/operations/test_vps_pilot_dry_run.py`.
- Résultat : **échec attendu** — `vps_pilot_dry_run.py` est absent ; aucune
  commande, connexion, opération VPS ou mutation externe n'a été exécutée.
- État : `T-031 = red`, `active_task = T-031`.

---

### T-031 · green · 2026-08-03T16:51:43Z

- Le générateur charge et valide un modèle JSON fermé, puis remplace uniquement
  le slug de board prévalidé. Les trois plafonds Kanban, `failure_limit`, la
  profondeur de délégation et l'auto-approve ont leurs valeurs exactes.
- Le plan contient huit argv structurés et ordonnés, tous marqués
  `execute: false`; le dry-run `super-lily` est borné à deux et reste
  `dispatched: false`; `hermes config check` clôt la séquence.
- Vérification ciblée : **6/6 tests** verts. Aucun client réseau, processus,
  accès VPS, dispatch réel ou déploiement n'est présent dans la production.
- État : `T-031 = green`, `active_task = T-031`.

---

### T-031 · refactor · 2026-08-03T16:52:27Z

- La validation ferme désormais les champs racine et la forme de chaque
  commande structurée avant toute lecture détaillée ; un champ secret ajouté
  ou un argv non textuel est refusé au lieu d'être toléré silencieusement.
- La triangulation rejette les slugs contenant casse, espace, chemin ou
  séparateur shell, ainsi que les champs de modèle supplémentaires.
- Vérification après refactor : **8/8 tests** et `git diff --check` verts,
  sans changement du plan valide produit.
- État : `T-031 = refactor`, `active_task = T-031`.

---

### T-031 · simplify · 2026-08-03T16:53:56Z

- Passe `clarity-over-cleverness` : les limites, le profil, le mode, les argv
  attendus et la version de schéma portent des noms métier ; la validation des
  commandes utilise une boucle explicite et le retour est direct.
- Le générateur reste une lecture locale suivie d'une matérialisation JSON. Il
  n'expose ni exécuteur, ni callback, ni option d'activation, ni client externe.
- Vérifications : **8/8 tests**, compilation des deux modules et
  `git diff --check` verts.
- État : `T-031 = simplify`, `active_task = T-031`.

---

### T-031 · done · 2026-08-03T17:00:04Z

- T-031 couvre T-031-T1 à T-031-T6 et AC-170 à AC-174 ainsi que AC-183.
- Preuves finales : **8/8 tests ciblés**, **401/405 tests Hermes exécutés**,
  **4 skips historiques**, **14 skills validés**, modèle et état JSON valides,
  journal Markdown sans erreur et `git diff --check` vert.
- Le résultat est uniquement un plan local expurgé : aucune commande n'a été
  exécutée, aucun client réseau ou processus n'est importé, et aucun accès VPS,
  dispatch réel, gateway, fusion ou déploiement n'a eu lieu.
- Issue d'exécution : `#118`. Branche :
  `agent/build-t031-vps-dry-run`, sans reviewer sollicité.
- État final : `T-031 = done`, `active_task = null`.

---
