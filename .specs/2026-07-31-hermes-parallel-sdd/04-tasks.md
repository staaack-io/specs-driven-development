# Tâches : S-001 — profil 0.4.8

> Responsable : `spring-architect` · Phase 3b · Tranche Epic : `S-001`
>
> Chaque chemin de `Files in scope` est un chemin littéral relatif au dépôt
> indiqué. Aucun glob n'est autorisé. Les tâches T-001 et T-002 sont les deux
> seuls writers admissibles en parallèle ; T-003 est une gate en lecture seule.

## Inputs

- Révision de `03-design.md` : conception S-001 du 2026-08-01.
- Dépôt source canonique : `staaack-io/specs-driven-development`,
  `origin/main` à `3eef5b5` pour la fusion de #47.
- Dépôt cible des tâches : `staaack-io/hermes-agent-profile-staaack`,
  version observée `0.4.7` sur `main`.
- Couverture attendue : exactement 36 AC affectés à S-001.

## Task ID Registry

- **high_water_mark :** 38
- **retired_ids :** (aucun)

## Task Index

| ID | Titre | AC-IDs | Dépend de | Estimation | Portes |
|---|---|---|---|---:|---|
| T-001 | Porter le contrat onboard puis publier sa copie exacte | AC-009, AC-010, AC-095, AC-096, AC-098, AC-099 | — | 2–4 h | unit, profile-layout, skill-contract, parity, diff |
| T-002 | Versionner et valider la distribution 0.4.8 | AC-081–AC-086, AC-097, AC-195, AC-237, AC-250–AC-251, AC-281–AC-282, AC-286 | — | 1–3 h | unit, distribution, frontmatter, markdown, diff, CI |
| T-003 | Faire franchir la gate humaine à la PR profil | AC-087–AC-094, AC-100, AC-272–AC-275, AC-283–AC-285 | T-001, T-002 | 1–4 h hors attente humaine | CI, tests, contracts, review, threads, approval |

T-001 et T-002 ont des périmètres disjoints et peuvent progresser en parallèle.
T-003 attend leurs résultats verts et n'autorise aucune écriture de production.

## Tasks

### T-001 : Porter le contrat onboard puis publier sa copie exacte

- **Origine qualifiée :** `spring-architect:T-001`
- **Dépôts d'exécution séquentiels :**
  1. `staaack-io/specs-driven-development` pour RED et le correctif canonique ;
  2. `staaack-io/hermes-agent-profile-staaack` pour la copie exacte et les preuves.
- **AC-IDs :** AC-009, AC-010, AC-095, AC-096, AC-098, AC-099
- **Test-IDs :**
  - T-001-T1 (RED profile-layout — le nouveau test source copie les skills dans `profile/skills/...` et reproduit 3 réussites plus 2 erreurs sur les dépendances `docs/` absentes)
  - T-001-T2 (GREEN source-contract — les 5 tests canoniques passent sans lire de fichier extérieur aux surfaces distribuées)
  - T-001-T3 (GREEN profile-contract — après copie exacte, le profil exécute 15/15 tests du garde et 5/5 tests du contrat)
  - T-001-T4 (parity — `check_profile_parity.py` ne rapporte aucune différence entre les deux checkouts)
  - T-001-T5 (regression — la découverte complète des tests du profil conserve les commandes existantes et exécute les tests onboard)
- **Files in scope — dépôt `staaack-io/specs-driven-development` :**
  - `hermes/scripts/test_sdd_onboard_profile_contract.py`
  - `hermes/skills/sdd-onboard/scripts/test_skill_contract.py`
- **Files in scope — dépôt `staaack-io/hermes-agent-profile-staaack` :**
  - `skills/sdd-onboard/scripts/test_onboarding_guard.py`
  - `skills/sdd-onboard/scripts/test_skill_contract.py`
  - `skills/sdd-onboard/SKILL.md`
  - `skills/sdd-onboard/references/artifact-contract.md`
  - `skills/sdd-onboard/references/classification.md`
  - `skills/sdd-onboard/references/delegation-contract.md`
  - `skills/sdd-onboard/references/role-react-nextjs-onboarding.md`
  - `skills/sdd-onboard/references/role-spring-onboarding.md`
  - `skills/sdd-onboard/references/transaction-atomicity.md`
  - `skills/sdd-onboard/scripts/onboarding_guard.py`
  - `skills/sdd-onboard/templates/baseline.template.json`
  - `skills/sdd-onboard/templates/known-debt.template.md`
  - `skills/sdd-onboard/templates/onboarding.template.md`
  - `skills/sdd-onboard/templates/stack.template.json`
  - `skills/sdd-onboard/templates/starter-design.template.md`
- **Dépendances :** aucune
- **Phases estimées :** RED 30–45 min ; GREEN source 30–60 min ; GREEN profil 30–60 min ; REFACTOR et SIMPLIFY 15–30 min.
- **Portes à exécuter après green :** `python-unit-source`, `profile-layout`, `skill-contract-source`, `python-unit-profile`, `skill-contract-profile`, `profile-parity`, `git-diff-check`
- **Retour arrière :** rétablir les deux fichiers source de T-001 et supprimer uniquement `skills/sdd-onboard` de la branche de la PR profil ; les cinq skills 0.4.7 restent inchangés.
- **Notes :** le RED légitime est le test source dédié qui reproduit la disposition installée, pas la suppression d'une assertion. Pour GREEN, remplacer les deux lectures de `docs/` hors distribution par des preuves sémantiquement équivalentes fondées uniquement sur `references/artifact-contract.md`, `sdd-help/SKILL.md` et `sdd-status/SKILL.md`. Conserver les cinq cas du contrat et leurs assertions métier. Après réussite source, copier exactement les quinze fichiers de `hermes/skills/sdd-onboard` vers le profil sans transformation. Ne modifier aucun autre dossier sous `skills/`. Le contrôle de parité utilise `hermes/scripts/check_profile_parity.py` depuis le dépôt source et le checkout du profil comme argument.

### T-002 : Versionner et valider la distribution 0.4.8

- **Origine qualifiée :** `spring-architect:T-002`
- **Dépôt d'exécution :** `staaack-io/hermes-agent-profile-staaack`
- **AC-IDs :** AC-081, AC-082, AC-083, AC-084, AC-085, AC-086, AC-097, AC-195, AC-237, AC-250, AC-251, AC-281, AC-282, AC-286
- **Test-IDs :**
  - T-002-T1 (unit — le contrat de release refuse le profil tant que `distribution.yaml` ne vaut pas 0.4.8 ou que le changelog 0.4.8 manque)
  - T-002-T2 (distribution — manifeste, arborescence, frontmatters et références locales sont valides)
  - T-002-T3 (documentation — Markdownlint et `git diff --check` passent sur le diff de la PR)
  - T-002-T4 (CI contract — les deux workflows attendus existent et exposent leurs noms de checks stables)
  - T-002-T5 (CI gate — les tests Python et contrats sont verts dans chacun des deux dépôts)
- **Files in scope :**
  - `scripts/test_validate_distribution.py`
  - `distribution.yaml`
  - `CHANGELOG.md`
  - `README.md`
  - `.github/workflows/ci.yml`
- **Dépendances :** aucune
- **Phases estimées :** RED 30–45 min ; GREEN 30–60 min ; REFACTOR 15–30 min ; SIMPLIFY 15–30 min.
- **Portes à exécuter après green :** `python-unit`, `distribution`, `frontmatter`, `markdownlint`, `git-diff-check`, `ci`
- **Retour arrière :** rétablir les quatre fichiers de métadonnées et de validation de la branche de PR à leur contenu 0.4.7 ; aucune installation n'est effectuée.
- **Notes :** ajouter le plus petit test de release à la suite existante avant de modifier le manifeste et le changelog. Le workflow CI du profil est déjà présent ; il doit rester fonctionnel et ne doit être modifié que si le test RED démontre un écart aux AC de S-001. La preuve de CI source porte sur `.github/workflows/hermes-ci.yml` du dépôt source, lu sans modification.

### T-003 : Faire franchir la gate humaine à la PR profil

- **Origine qualifiée :** `spring-architect:T-003`
- **Dépôt d'exécution :** `staaack-io/hermes-agent-profile-staaack`
- **AC-IDs :** AC-087, AC-088, AC-089, AC-090, AC-091, AC-092, AC-093, AC-094, AC-100, AC-272, AC-273, AC-274, AC-275, AC-283, AC-284, AC-285
- **Test-IDs :**
  - T-003-T1 (historical-gate — #47 est fusionnée après checks verts, review reçue et lue, fils traités avec filiation et go explicite)
  - T-003-T2 (pull-request — la publication 0.4.8 utilise une PR du dépôt profil distincte de #47)
  - T-003-T3 (publication-gate — CI, tests et contrats de la PR profil sont verts)
  - T-003-T4 (review-gate — la review de la PR profil vaut `approve` et aucun fil actionnable ne reste ouvert)
  - T-003-T5 (human-gate — le go humain explicite est obtenu après les autres preuves et avant toute fusion)
  - T-003-T6 (vps-block — aucune mise à jour VPS n'est effectuée avant revue, autorisation et fusion de la PR profil)
- **Files in scope :**
  - `.github/workflows/ci.yml`
  - `distribution.yaml`
  - `CHANGELOG.md`
  - `skills/sdd-onboard/SKILL.md`
  - `skills/sdd-onboard/scripts/test_onboarding_guard.py`
  - `skills/sdd-onboard/scripts/test_skill_contract.py`
- **Dépendances :** T-001, T-002
- **Phases estimées :** vérification initiale 15–30 min ; corrections éventuelles 30–120 min ; nouvelle validation 15–30 min ; hors délai de review et de go humains.
- **Portes à exécuter après green :** `ci`, `tests`, `contracts`, `review-approve`, `actionable-threads-zero`, `human-approval`
- **Retour arrière :** ne pas fusionner ou fermer la PR profil ; conserver le profil publié 0.4.7 et ne pas mettre à jour le VPS.
- **Notes :** tâche de gate en lecture seule tant qu'une correction n'est pas demandée. Toute correction revient à T-001 ou T-002 selon son périmètre, reste sur la même branche de profil et impose une nouvelle review. T-003 n'autorise ni auto-merge ni mise à jour VPS. La fusion finale nécessite une instruction humaine explicite distincte de l'autorisation de poursuivre la migration.

## AC Coverage Matrix

| AC-ID | Tâche | Test-ID principal |
|---|---|---|
| AC-009, AC-010 | T-001 | T-001-T5, T-001-T2 |
| AC-081, AC-082, AC-083, AC-084, AC-085, AC-086 | T-002 | T-002-T4, T-002-T5, T-002-T2, T-002-T3 |
| AC-087, AC-088, AC-089, AC-090, AC-091, AC-092, AC-093, AC-094 | T-003 | T-003-T1 |
| AC-095, AC-096, AC-098, AC-099 | T-001 | T-001-T1, T-001-T2, T-001-T3, T-001-T4, T-001-T5 |
| AC-097 | T-002 | T-002-T1 |
| AC-100 | T-003 | T-003-T6 |
| AC-195, AC-237, AC-250, AC-251 | T-002 | T-002-T4, T-002-T5, T-002-T3, T-002-T1 |
| AC-272, AC-273, AC-274, AC-275 | T-003 | T-003-T1 |
| AC-281, AC-282 | T-002 | T-002-T5 |
| AC-283, AC-284, AC-285 | T-003 | T-003-T4, T-003-T1 |
| AC-286 | T-002 | T-002-T2, T-002-T5 |

La matrice couvre 36 identifiants uniques et ne contient aucun AC hors S-001.

## Dependency Validation

```text
T-001 ─┐
       ├─> T-003
T-002 ─┘
```

- Le graphe ne contient aucun cycle.
- T-001 et T-002 ne partagent aucun fichier modifiable ; ils sont admissibles
  dans la même vague de deux writers. Les deux dépôts internes à T-001 restent
  strictement séquentiels : correctif source vert avant copie profil.
- T-003 dépend des deux résultats et n'est pas un writer de production.
- L'ordre topologique de passage à `$build` commence par T-001, puis T-002 ;
  T-003 devient admissible lorsque les deux sont `green`.

## Cross-cutting items (handled in Phase 5)

- Aucun test ArchUnit ni contrat OpenAPI : stack non applicable.
- La parité source/profil est déjà affectée à T-001 car elle constitue une
  condition directe de la publication 0.4.8, pas un test transverse futur.
- La gate GitHub est déjà affectée à T-003 car elle conditionne directement la
  fusion de cette tranche.

## Open Questions

- (aucune)

## Resolved Questions

- Le périmètre est CLI/skills Python/Hermes ; Spring, OpenAPI et base de données
  sont N/A selon `Q-006`.
- La fusion n'est jamais automatique ; T-003 attend un go humain explicite.

## Sign-off

- [x] Chaque AC de S-001 est couvert par au moins une tâche.
- [x] Chaque tâche possède des Test-IDs et des chemins littéraux concrets.
- [x] Chaque tâche liste les portes réellement disponibles dans son dépôt.
- [x] Chaque tâche tient dans une plage de 1 à 4 heures hors attente humaine.
- [x] Le graphe de dépendances est acyclique et les writers parallèles ont des périmètres disjoints.
- [x] Toutes les `Q-NNN` sont résolues.
- [x] Checklist `design-review.md` relue par `spring-architect` le 2026-08-01.
- [x] Poursuite de la migration autorisée par l'utilisateur le 2026-08-01
  (instruction : « Continue à migrer »).

Étape suivante : `$build T-001` dans un checkout du dépôt profil, avec le dépôt
source fusionné disponible en lecture seule pour la copie et la parité.

## Tâches : S-002 — socle parallèle et profil 0.5.0

> Cette section prolonge le registre S-001. Les entrées T-001 à T-003
> ci-dessus restent inchangées. Les capacités fusionnées par #61, #57 et #59
> sont des preuves auditées, jamais des tâches rétrospectives.

### S-002 Inputs

- Révision de `03-design.md` : addendum S-002 du 2026-08-01.
- Baseline source : `origin/main` à `9607aae`.
- Preuves fusionnées : runtime v2 #61 à `257ce11`, epic-plan #57 à
  `d583bb5`, wire-harness #59 à `a5815b1`.
- Couverture attendue : exactement 84 AC affectés à S-002.

### S-002 Task Index

| ID | Titre | AC-IDs principaux | Dépend de | Estimation | Portes |
|---|---|---|---|---:|---|
| T-004 | Relier les jobs Kanban à GitHub sans ordonnanceur concurrent | AC-001, AC-002, AC-004, AC-106, AC-110–AC-122, AC-253–AC-256 | T-003 | 3–4 h | unit, bridge-contract, runtime, diff |
| T-005 | Afficher la carte task-local dans `/sdd-status` | AC-243–AC-249 | T-003 | 1–3 h | unit, read-only, skill-contract, diff |
| T-006 | Rendre le runtime partagé portable dans le profil | AC-048, AC-058–AC-060, AC-101, AC-276–AC-280 | T-004, T-005 | 2–4 h | unit, profile-layout, runtime-parity, diff |
| T-007 | Consolider la source et auditer les 84 AC S-002 | AC-001–AC-007, AC-011–AC-012, AC-025–AC-026, AC-048–AC-080, AC-101–AC-123, AC-243–AC-249, AC-252–AC-256, AC-276–AC-280 | T-004, T-005, T-006 | 2–4 h | source-contract, python, skills, markdown, diff, CI |
| T-008 | Publier le profil 0.5.0 avec parité skills/runtime | AC-011, AC-012, AC-025, AC-026, AC-123, AC-278 | T-003, T-007 | 3–4 h | profile-layout, parity, distribution, python, markdown, diff, CI |

T-004 et T-005 sont la seule vague de deux writers : leurs fichiers sont
strictement disjoints. T-006, T-007 et T-008 sont ensuite séquentiels. Une
seule gate lourde est lancée à la fois.

### S-002 Tasks

#### T-004 : Relier les jobs Kanban à GitHub sans ordonnanceur concurrent

- **Origine qualifiée :** `spring-architect:T-004`
- **Dépôt d'exécution :** `staaack-io/specs-driven-development`
- **AC-IDs :** AC-001, AC-002, AC-004, AC-106, AC-110, AC-111, AC-112,
  AC-113, AC-114, AC-115, AC-116, AC-117, AC-118, AC-119, AC-120, AC-121,
  AC-122, AC-253, AC-254, AC-255, AC-256
- **Test-IDs :**
  - T-004-T1 (RED lifecycle — un job admis n'a encore ni issue, ni carte
    enrichie, ni PR brouillon traçable)
  - T-004-T2 (GREEN identifiers — issue et PR créées avec `gh`, puis IDs
    stockés dans la carte et l'état via CAS)
  - T-004-T3 (GREEN ready — tests verts transforment uniquement la PR brouillon
    en PR prête)
  - T-004-T4 (polling — checks, reviews et fils sont consultés toutes les cinq
    minutes avec une horloge injectée)
  - T-004-T5 (correction — une demande reste sur la même branche, répond dans
    le fil exact et attend une nouvelle review)
  - T-004-T6 (timeout — trente minutes sans review produisent `needs_input`)
  - T-004-T7 (safety — aucune commande de merge, aucun scheduler Python et
    aucun troisième lease writer ne sont possibles)
  - T-004-T8 (recovery — la même clé d'idempotence reprend sans dupliquer issue,
    carte ou PR)
- **Files in scope :**
  - `hermes/runtime/github-bridge-contract.md`
  - `hermes/runtime/sdd_github_bridge.py`
  - `hermes/runtime/test_sdd_github_bridge.py`
- **Dépendances :** T-003
- **Phases estimées :** RED 30–45 min ; GREEN 90–120 min ; REFACTOR 30–45
  min ; SIMPLIFY 15–30 min.
- **Portes à exécuter après green :** `python-unit-bridge`,
  `bridge-contract`, `runtime-regression`, `git-diff-check`
- **Retour arrière :** retirer les trois nouveaux fichiers de la branche ; le
  runtime #61 reste fusionné et passif, sans supprimer carte, issue ou PR.
- **Notes :** le module expose des transitions appelées par Hermes et utilise
  des adaptateurs structurés pour le Kanban et `gh`. Il ne contient aucune
  boucle d'admission, n'appelle pas `delegate_task`, n'exécute jamais
  `gh pr merge` et ne stocke aucun secret. Les tests utilisent des adaptateurs
  factices et une horloge contrôlée ; ils n'appellent pas GitHub réel. Avant sa
  fusion, la branche est resynchronisée avec `main`, comme #57 et #59.

#### T-005 : Afficher la carte task-local dans `/sdd-status`

- **Origine qualifiée :** `spring-architect:T-005`
- **Dépôt d'exécution :** `staaack-io/specs-driven-development`
- **AC-IDs :** AC-243, AC-244, AC-245, AC-246, AC-247, AC-248, AC-249
- **Test-IDs :**
  - T-005-T1 (RED fields — le status actuel n'affiche pas issue, branche, PR,
    checks, review, blocage et prochaine action par tâche)
  - T-005-T2 (GREEN v2 — une fixture v2 complète rend les sept champs de chaque
    tâche sans les déduire)
  - T-005-T3 (compatibility — les champs absents d'un état v1 valent `—`)
  - T-005-T4 (read-only — l'empreinte du dépôt ne change pas pendant la lecture)
  - T-005-T5 (next-action — la recommandation task-local suit phase, statut et
    blocage prouvés)
- **Files in scope :**
  - `hermes/skills/sdd-status/SKILL.md`
  - `hermes/skills/sdd-status/references/kanban-state-contract.md`
  - `hermes/skills/sdd-status/scripts/status_guard.py`
  - `hermes/skills/sdd-status/scripts/test_status_guard.py`
- **Dépendances :** T-003
- **Phases estimées :** RED 20–30 min ; GREEN 45–75 min ; REFACTOR 20–30 min ;
  SIMPLIFY 15–30 min.
- **Portes à exécuter après green :** `python-unit-status`,
  `status-read-only`, `skill-contract`, `git-diff-check`
- **Retour arrière :** rétablir `SKILL.md` et retirer les trois nouveaux
  fichiers ; l'ancienne vue de phase reste disponible.
- **Notes :** aucune commande GitHub ou Hermes mutante n'est autorisée. Le
  garde lit uniquement les champs prouvés et affiche `—` lorsqu'une valeur est
  absente ; il ne répare ni la carte ni l'état.

#### T-006 : Rendre le runtime partagé portable dans le profil

- **Origine qualifiée :** `spring-architect:T-006`
- **Dépôt d'exécution :** `staaack-io/specs-driven-development`
- **AC-IDs :** AC-048, AC-058, AC-059, AC-060, AC-101, AC-276, AC-277,
  AC-278, AC-279, AC-280
- **Test-IDs :**
  - T-006-T1 (RED profile-layout — une copie sous `profile/skills/sdd-plan`
    reproduit l'échec d'import du runtime partagé)
  - T-006-T2 (GREEN dual-layout — le même garde charge le runtime depuis les
    dispositions source et profil)
  - T-006-T3 (runtime-parity — la comparaison couvre `hermes/runtime` en plus
    de `skills` et signale tout fichier manquant ou différent)
  - T-006-T4 (migration-regression — les tests v1/v2, secrets, chemins relatifs
    et rollback logique restent verts)
  - T-006-T5 (isolation — la résolution refuse tout runtime symbolique ou hors
    de la racine distribuée)
- **Files in scope :**
  - `hermes/scripts/check_profile_parity.py`
  - `hermes/scripts/test_check_profile_parity.py`
  - `hermes/scripts/test_sdd_runtime_profile_contract.py`
  - `hermes/skills/sdd-plan/scripts/tdd_state_guard.py`
  - `hermes/skills/sdd-plan/scripts/test_tdd_state_guard.py`
- **Dépendances :** T-004, T-005
- **Phases estimées :** RED 30–45 min ; GREEN 45–75 min ; REFACTOR 30–45
  min ; SIMPLIFY 15–30 min.
- **Portes à exécuter après green :** `python-unit-plan`,
  `profile-layout`, `runtime-parity`, `runtime-regression`, `git-diff-check`
- **Retour arrière :** rétablir les cinq fichiers ; bloquer la publication
  0.5.0 et conserver le profil 0.4.8.
- **Notes :** le test RED doit reproduire la disposition installée sans
  affaiblir l'import ni copier le runtime dans le skill. La solution conserve
  un runtime partagé unique sous `hermes/runtime` dans les deux dépôts et
  refuse les chemins absolus ou symboliques. AC-278 est prouvée ici comme
  compatibilité technique ; sa procédure de publication appartient à T-008.

#### T-007 : Consolider la source et auditer les 84 AC S-002

- **Origine qualifiée :** `spring-architect:T-007`
- **Dépôt d'exécution :** `staaack-io/specs-driven-development`
- **AC-IDs :** AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007,
  AC-011, AC-012, AC-025, AC-026, AC-048, AC-049, AC-050, AC-051, AC-052,
  AC-053, AC-054, AC-055, AC-056, AC-057, AC-058, AC-059, AC-060, AC-061,
  AC-062, AC-063, AC-064, AC-065, AC-066, AC-067, AC-068, AC-069, AC-070,
  AC-071, AC-072, AC-073, AC-074, AC-075, AC-076, AC-077, AC-078, AC-079,
  AC-080, AC-101, AC-102, AC-103, AC-104, AC-105, AC-106, AC-107, AC-108,
  AC-109, AC-110, AC-111, AC-112, AC-113, AC-114, AC-115, AC-116, AC-117,
  AC-118, AC-119, AC-120, AC-121, AC-122, AC-123, AC-243, AC-244, AC-245,
  AC-246, AC-247, AC-248, AC-249, AC-252, AC-253, AC-254, AC-255, AC-256,
  AC-276, AC-277, AC-278, AC-279, AC-280
- **Test-IDs :**
  - T-007-T1 (coverage — le manifeste S-002 contient exactement les 84 AC de
    la roadmap, sans trou ni identifiant S-001)
  - T-007-T2 (merged-baseline — les symboles et tests attendus de #61, #57 et
    #59 sont présents sans réimplémentation)
  - T-007-T3 (commands — help et documentation présentent epic-plan et
    wire-harness comme disponibles, sans `/sdd-roles`)
  - T-007-T4 (bridge-status — le bridge et status satisfont leurs contrats
    déterministes et leurs scopes restent disjoints)
  - T-007-T5 (capacity — deux writers, trois analyses au plus et une gate lourde
    sont prouvés par les contrats source)
  - T-007-T6 (release-candidate — la surface source n'expose aucun secret,
    auto-merge, second ordonnanceur ou chemin absolu versionné)
- **Files in scope :**
  - `hermes/scripts/test_sdd_s002_contract.py`
  - `hermes/skills/sdd-help/SKILL.md`
  - `hermes/README.md`
  - `docs/artifact-contract.md`
  - `docs/codex-migration.md`
- **Dépendances :** T-004, T-005, T-006
- **Phases estimées :** RED 30–45 min ; GREEN 60–90 min ; REFACTOR 30–45
  min ; SIMPLIFY 15–30 min.
- **Portes à exécuter après green :** `s002-source-contract`,
  `python-all`, `skill-contracts`, `markdownlint`, `git-diff-check`, `ci`
- **Retour arrière :** rétablir les quatre documents et retirer le test
  agrégé ; les capacités fusionnées restent intactes, mais T-008 reste bloquée.
- **Notes :** cette tâche est un fan-in de preuve, pas une réécriture de #61,
  #57 ou #59. Toute correction imprévue revient au fichier et à la tâche qui
  en est propriétaire ; aucun fichier de T-004, T-005 ou T-006 n'est modifié
  ici. Le test agrégé relie chaque AC à un test ou à une preuve externe
  explicite ; AC-123 reste en attente de T-008.

#### T-008 : Publier le profil 0.5.0 avec parité skills/runtime

- **Origine qualifiée :** `spring-architect:T-008`
- **Dépôt d'exécution :** `staaack-io/hermes-agent-profile-staaack`
- **AC-IDs :** AC-011, AC-012, AC-025, AC-026, AC-123, AC-278
- **Test-IDs :**
  - T-008-T1 (RED release — le contrat refuse une distribution encore en 0.4.8
    ou sans epic-plan, wire-harness et runtime)
  - T-008-T2 (skills-parity — chaque fichier canonique sous `hermes/skills`
    est identique sous `skills`)
  - T-008-T3 (runtime-parity — chaque fichier canonique distribuable sous
    `hermes/runtime` est identique dans le profil)
  - T-008-T4 (profile-tests — les tests runtime, plan, epic-plan, wire-harness,
    status et contrats s'exécutent depuis la disposition profil)
  - T-008-T5 (distribution — version 0.5.0, changelog, frontmatters,
    documentation et fichiers distribués sont valides)
  - T-008-T6 (rollback — la note de release nomme le retour au profil 0.4.8
    sans suppression ni conversion inverse de l'état)
  - T-008-T7 (publication-gate — CI, tests, contrats, review approve, zéro fil
    actionnable et go explicite précèdent la fusion)
- **Files in scope — runtime distribué :**
  - `hermes/runtime/README.md`
  - `hermes/runtime/__init__.py`
  - `hermes/runtime/github-bridge-contract.md`
  - `hermes/runtime/sdd_github_bridge.py`
  - `hermes/runtime/sdd_runtime_guard.py`
  - `hermes/runtime/test_sdd_github_bridge.py`
  - `hermes/runtime/test_sdd_runtime_guard.py`
- **Files in scope — skills ajoutés ou actualisés :**
  - `skills/sdd-help/SKILL.md`
  - `skills/sdd-plan/SKILL.md`
  - `skills/sdd-plan/references/tdd-state-atomicity.md`
  - `skills/sdd-plan/scripts/tdd_state_guard.py`
  - `skills/sdd-plan/scripts/test_tdd_state_guard.py`
  - `skills/sdd-plan/templates/tdd-state.template.json`
  - `skills/sdd-status/SKILL.md`
  - `skills/sdd-status/references/kanban-state-contract.md`
  - `skills/sdd-status/scripts/status_guard.py`
  - `skills/sdd-status/scripts/test_status_guard.py`
  - `skills/sdd-epic-plan/SKILL.md`
  - `skills/sdd-epic-plan/references/delegation-contract.md`
  - `skills/sdd-epic-plan/references/epic-contract.md`
  - `skills/sdd-epic-plan/references/role-react-nextjs-architect.md`
  - `skills/sdd-epic-plan/references/role-spring-architect.md`
  - `skills/sdd-epic-plan/references/stack-evidence.md`
  - `skills/sdd-epic-plan/references/transaction-atomicity.md`
  - `skills/sdd-epic-plan/scripts/epic_plan_guard.py`
  - `skills/sdd-epic-plan/scripts/fixtures/valid-epic/01-spec.md`
  - `skills/sdd-epic-plan/scripts/fixtures/valid-epic/03-epic-design.candidate.md`
  - `skills/sdd-epic-plan/scripts/fixtures/valid-epic/03a-epic-roadmap.candidate.md`
  - `skills/sdd-epic-plan/scripts/test_epic_plan_guard.py`
  - `skills/sdd-epic-plan/scripts/test_skill_contract.py`
  - `skills/sdd-epic-plan/templates/epic-design.template.md`
  - `skills/sdd-epic-plan/templates/epic-roadmap.template.md`
  - `skills/sdd-wire-harness/SKILL.md`
  - `skills/sdd-wire-harness/references/plan-contract.md`
  - `skills/sdd-wire-harness/references/role-harness-integrator.md`
  - `skills/sdd-wire-harness/references/transaction-safety.md`
  - `skills/sdd-wire-harness/scripts/harness_guard.py`
  - `skills/sdd-wire-harness/scripts/test_harness_guard.py`
- **Files in scope — validation et métadonnées du profil :**
  - `scripts/run_skill_tests.py`
  - `scripts/test_run_skill_tests.py`
  - `scripts/validate_distribution.py`
  - `scripts/test_validate_distribution.py`
  - `distribution.yaml`
  - `CHANGELOG.md`
  - `README.md`
  - `.github/workflows/ci.yml`
- **Dépendances :** T-003, T-007
- **Phases estimées :** RED 30–45 min ; GREEN copie et packaging 75–105 min ;
  REFACTOR 30–45 min ; SIMPLIFY 15–30 min.
- **Portes à exécuter après green :** `profile-layout`, `skills-parity`,
  `runtime-parity`, `python-all-profile`, `distribution`, `frontmatter`,
  `markdownlint`, `git-diff-check`, `ci`, `review-approve`,
  `actionable-threads-zero`, `human-approval`
- **Retour arrière :** fermer ou annuler la PR profil et conserver la version
  0.4.8 ; si 0.5.0 a été installée plus tard, réinstaller 0.4.8 sans
  supprimer ni reconvertir les états v2, journaux, branches ou worktrees.
- **Notes :** copier les fichiers canoniques sans transformation. La CI du
  profil doit découvrir les tests runtime en plus des tests sous `skills/`.
  Aucun fichier 0.4.8 non remplacé par sa source canonique n'est supprimé.
  T-008 crée une PR profil séparée et ne la fusionne jamais sans instruction
  humaine explicite.

### S-002 AC Coverage Matrix

| AC S-002 | Preuve ou tâche de production | Audit/fan-in |
|---|---|---|
| AC-001–AC-007 | T-004 ; baseline #61/#57/#59 ; preuve Issues | T-007-T2, T-007-T5, T-007-T6 |
| AC-011–AC-012 | Skills source #57/#59 ; T-008 | T-007-T1, T-008-T1–T-008-T5 |
| AC-025–AC-026 | Baseline skills ; T-008 | T-007-T3, T-008-T2 |
| AC-048–AC-079 | Runtime #61 ; T-006 pour la disposition profil | T-007-T1, T-007-T2, T-007-T5, T-007-T6 |
| AC-080 | Wire-harness #59 | T-007-T2, T-007-T5 |
| AC-101–AC-105 | Runtime #61 | T-007-T2 |
| AC-106 | Historique #61/#57/#59 ; T-004 pour la troisième PR | T-007-T2, T-007-T4 |
| AC-107 | Epic-plan #57 | T-007-T2 |
| AC-108–AC-109 | Wire-harness #59 | T-007-T2 |
| AC-110–AC-122 | T-004 | T-007-T4, T-007-T6 |
| AC-123 | T-008 | T-008-T5, T-008-T7 |
| AC-243–AC-249 | T-005 | T-007-T4 |
| AC-252 | Runtime #61 | T-007-T2 |
| AC-253–AC-256 | T-004 | T-007-T4 |
| AC-276–AC-280 | Runtime #61 ; T-006 ; T-008 pour le rollback | T-007-T2, T-008-T3, T-008-T6 |

La matrice contient **84 identifiants uniques sur 84**. T-007 les énumère
explicitement et échoue si la liste diverge de la roadmap.

### S-002 Dependency Validation

```text
T-003 ─> T-004 ─┐
       └> T-005 ─┼─> T-006 ─> T-007 ─> T-008
                  ┘────────────────────────┘
```

- Le graphe est acyclique et l'ordre topologique conserve S-001 avant S-002.
- T-004 et T-005 ne partagent aucun fichier et utilisent au plus deux writers.
- T-006 attend la vague pour éviter un troisième writer, bien que ses fichiers
  soient disjoints.
- T-007 est l'unique fan-in source et ne modifie aucun fichier de T-004 à T-006.
- T-008 est l'unique writer du dépôt profil pour 0.5.0.

### S-002 Cross-cutting Items

- Aucun test ArchUnit, OpenAPI ou de migration de base : stack non applicable.
- Les tests d'intégration GitHub réels restent réservés à la tranche S-005 ;
  T-004 utilise des adaptateurs déterministes pour le contrat direct S-002.
- Les preuves historiques de merge sont auditées, mais aucun commit de #61,
  #57 ou #59 n'est rejoué ni réécrit.

### S-002 Open Questions

- (aucune)

### S-002 Resolved Questions

- Le bridge est interne au runtime et n'ajoute aucune commande utilisateur.
- Le runtime partagé est distribué sous `hermes/runtime`, séparé des skills,
  et sa parité est validée explicitement.
- La prochaine publication reste 0.5.0 après le fan-in source S-002.

### S-002 Sign-off

- [x] T-001, T-002 et T-003 conservent leurs IDs, textes, preuves et scopes.
- [x] Le registre progresse sans réutilisation jusqu'à `high_water_mark: 8`.
- [x] Chaque nouvelle tâche possède des Test-IDs et des chemins littéraux.
- [x] Chaque nouvelle tâche tient dans une plage de 1 à 4 heures.
- [x] Le graphe est acyclique, avec deux writers maximum et une gate lourde.
- [x] Les 84 AC S-002 sont couverts sans orphelin.
- [x] Aucune question ouverte ne subsiste.
- [x] Checklist `design-review.md` relue le 2026-08-01.

Prochaine tâche S-002 après livraison de S-001 : `$build T-004`, en parallèle
avec `$build T-005` dans deux worktrees aux scopes disjoints.

## Tâches : S-003 — `/sdd-build` mono-tâche et parallèle, profil 0.6.0

> Cette section prolonge le registre S-001/S-002. T-001 à T-008, leurs
> preuves, scopes et états restent inchangés. Chaque nouveau chemin est un
> littéral relatif au dépôt nommé ; aucun glob ni dossier n'est autorisé.

### S-003 Inputs

- Révision de `03-design.md` : addendum S-003 du 2026-08-03.
- Source de tranche : issue GitHub #74.
- Baseline source : `main` à `0f5932a`, T-001 à T-008 `done`.
- Couverture primaire : exactement 51 AC de S-003.
- Barrière : T-009 mono-tâche doit être `done` et fusionnée avant T-010 ;
  T-011 attend T-010 afin de laisser le second slot global au writer S-004.
- Capacité : deux writers, trois analyses internes en lecture seule et une gate
  lourde au maximum.

### S-003 Task Index

| ID | Titre | AC-IDs primaires | Dépend de | Estimation | Portes |
|---|---|---|---|---:|---|
| T-009 | Orchestrer `/sdd-build` mono-tâche et ses preuves | AC-019, AC-037–AC-044, AC-124–AC-127, AC-257–AC-259 | T-008 | 3–4 h | unit, skill-contract, runtime, diff |
| T-010 | Admettre et créer les cartes du build parallèle | AC-020–AC-023, AC-027–AC-029, AC-031, AC-128–AC-133, AC-236, AC-260 | T-009 | 3–4 h | unit, orchestrator-contract, runtime, diff |
| T-011 | Isoler l'enveloppe Git, Hermes et GitHub d'un job | AC-030, AC-032–AC-036, AC-233–AC-234 | T-010 | 3–4 h | unit, job-contract, bridge, runtime, diff |
| T-012 | Appliquer le go humain et le fan-in de vague | AC-045–AC-047, AC-134–AC-137, AC-231 | T-010, T-011 | 3–4 h | unit, fan-in-contract, runtime, diff |
| T-013 | Auditer la source S-003 sur exactement 51 AC | AC-024 | T-012 | 2–4 h | s003-contract, python, skills, markdown, diff, CI |
| T-014 | Publier le profil 0.6.0 avec parité et rollback | AC-013, AC-138 | T-013 | 3–4 h | profile-layout, parity, distribution, python, markdown, diff, CI, review |

Après T-009, T-010 est le writer S-003 qui peut progresser avec le writer S-004
hors périmètre. T-011 attend T-010 ; leurs scopes restent strictement disjoints
mais ils ne sont pas planifiés comme writers concurrents. Toutes les tâches
S-003 utilisent donc un seul slot de développement à la fois après T-009.

### S-003 Tasks

### T-009 : Orchestrer `/sdd-build` mono-tâche et ses preuves

- **Origine qualifiée :** `spring-architect:T-009`
- **Dépôt d'exécution :** `staaack-io/specs-driven-development`
- **AC-IDs :** AC-019, AC-037, AC-038, AC-039, AC-040, AC-041, AC-042,
  AC-043, AC-044, AC-124, AC-125, AC-126, AC-127, AC-257, AC-258, AC-259
- **Test-IDs :**
  - T-009-T1 (RED arguments — l'absence actuelle de `/sdd-build <feature-id> <T-NNN>` échoue avant toute mutation)
  - T-009-T2 (stack routing — les preuves Spring chargent test-engineer puis implementer Spring ; les preuves React/Next chargent les deux rôles React)
  - T-009-T3 (RED ownership — le test-engineer reçoit seulement Test-IDs et fichiers de test, écrit le test rouge et ne reçoit aucun handle d'artefact partagé)
  - T-009-T4 (RED proof gate — une production sans signature, commande, échec attendu ou événement RED durable est refusée)
  - T-009-T5 (GREEN ownership — l'implementer intervient après la preuve RED et écrit uniquement le minimum de production en scope)
  - T-009-T6 (cycle order — le même job observe strictement RED, GREEN, REFACTOR puis SIMPLIFY sans phase sautée)
  - T-009-T7 (evidence — chaque transition conserve Test-IDs, argv structurés, sortie expurgée et liste des fichiers concernés)
  - T-009-T8 (shared-artifact safety — les rôles et le worker ne peuvent modifier `04-tasks.md`, `.tdd-state.json` ou `05-implementation-log.md`)
  - T-009-T9 (journal recovery — une reprise avec le même event-id et le même contenu est idempotente ; une preuve différente est refusée)
- **Files in scope :**
  - `hermes/skills/sdd-build/scripts/test_build_guard.py`
  - `hermes/skills/sdd-build/scripts/test_skill_contract.py`
  - `hermes/skills/sdd-build/scripts/build_guard.py`
  - `hermes/skills/sdd-build/SKILL.md`
  - `hermes/skills/sdd-build/references/delegation-contract.md`
  - `hermes/skills/sdd-build/references/tdd-cycle-contract.md`
  - `hermes/skills/sdd-build/references/role-spring-test-engineer.md`
  - `hermes/skills/sdd-build/references/role-spring-implementer.md`
  - `hermes/skills/sdd-build/references/role-react-nextjs-test-engineer.md`
  - `hermes/skills/sdd-build/references/role-react-nextjs-implementer.md`
- **Dépendances :** T-008
- **Phases estimées :** RED 30–45 min ; GREEN 90–120 min ; REFACTOR 30–45 min ; SIMPLIFY 20–30 min.
- **Portes à exécuter après green :** `python-unit-build`, `skill-contract`,
  `runtime-regression`, `git-diff-check`
- **Retour arrière :** retirer uniquement le nouveau dossier
  `hermes/skills/sdd-build` de la branche ; le profil 0.5.0 et le runtime S-002
  restent inchangés.
- **Notes :** écrire les tests avant le garde. Le garde appelle les primitives
  runtime existantes pour état, lease, RED, journal et fingerprint ; il ne les
  recopie pas. Chaque rôle reçoit un contexte autonome minimal et aucun chemin
  vers les artefacts partagés. Les commandes sont des listes d'arguments, et
  la sortie est expurgée avant `append_job_event`. T-009 doit être fusionnée
  avant toute tâche d'orchestration parallèle.

### T-010 : Admettre et créer les cartes du build parallèle

- **Origine qualifiée :** `spring-architect:T-010`
- **Dépôt d'exécution :** `staaack-io/specs-driven-development`
- **AC-IDs :** AC-020, AC-021, AC-022, AC-023, AC-027, AC-028, AC-029,
  AC-031, AC-128, AC-129, AC-130, AC-131, AC-132, AC-133, AC-236, AC-260
- **Test-IDs :**
  - T-010-T1 (RED parallel CLI — `--parallel` est absent et `--max-workers` n'a pas encore de validation structurée)
  - T-010-T2 (worker bounds — seules les valeurs 1 et 2 sont acceptées ; l'absence sur VPS vaut 2 et le plafond reste 2)
  - T-010-T3 (admission — toutes les tâches `pending`/`ready` dont les dépendances sont `done`/`done` et les scopes mutuellement disjoints reçoivent une carte dans la vague)
  - T-010-T4 (scope wave — deux scopes disjoints sont admis ensemble ; tout chevauchement est sérialisé)
  - T-010-T5 (card metadata — chaque carte porte projet parent, carte parente, branche, clé d'idempotence, skill, max-runtime 45 minutes et deux retries)
  - T-010-T6 (capacity — toutes les cartes admissibles sont lancées dans la vague, mais deux leases writers au plus sont actifs et les suivantes attendent sans mutation)
  - T-010-T7 (mono barrier — T-010 refuse de démarrer tant que T-009 n'est pas fusionnée ; ensuite l'orchestrateur S-003 et le chantier S-004 peuvent avoir des scopes disjoints sans intégrer AC-014/AC-139)
  - T-010-T8 (Hermes authority — l'adaptateur Kanban est l'unique surface de dispatch ; aucune boucle scheduler Python ni utilisation de `delegate_task` pour un job)
  - T-010-T9 (failure isolation — timeout ou échec d'une carte ne révoque pas le lease ni la progression d'un autre job)
- **Files in scope :**
  - `hermes/runtime/test_sdd_build_orchestrator.py`
  - `hermes/skills/sdd-build/scripts/test_build_guard.py`
  - `hermes/runtime/build-orchestrator-contract.md`
  - `hermes/runtime/sdd_build_orchestrator.py`
  - `hermes/skills/sdd-build/scripts/build_guard.py`
  - `hermes/skills/sdd-build/SKILL.md`
- **Dépendances :** T-009
- **Phases estimées :** RED 30–45 min ; GREEN 90–120 min ; REFACTOR 30–45 min ; SIMPLIFY 20–30 min.
- **Portes à exécuter après green :** `python-unit-orchestrator`,
  `orchestrator-contract`, `runtime-regression`, `skill-contract`,
  `git-diff-check`
- **Retour arrière :** rétablir les trois fichiers du skill à leur version
  mono-tâche et retirer les trois fichiers d'orchestrateur ; `/sdd-build`
  séquentiel reste utilisable.
- **Notes :** le test T-010-T7 est la preuve explicite d'AC-128. La tâche ne
  crée ni issue, worktree, session ou PR ; elle fournit à T-011 une enveloppe
  admise par adaptateur. La sélection réutilise `validate_state` et
  `acquire_scope_lease`. Les timers utilisent une horloge injectée, sans attente
  bloquante.

### T-011 : Isoler l'enveloppe Git, Hermes et GitHub d'un job

- **Origine qualifiée :** `spring-architect:T-011`
- **Dépôt d'exécution :** `staaack-io/specs-driven-development`
- **AC-IDs :** AC-030, AC-032, AC-033, AC-034, AC-035, AC-036, AC-233, AC-234
- **Test-IDs :**
  - T-011-T1 (RED envelope — un job admis ne sait pas encore créer son issue enfant, sa branche, son worktree, sa session et sa PR brouillon)
  - T-011-T2 (Git isolation — la branche vaut `sdd/<feature-id>/<task-id>-<slug>` et le worktree Hermes natif reste sous `.worktrees/`)
  - T-011-T3 (Hermes/GitHub isolation — une session, une issue enfant liée et une PR brouillon uniques sont associées au job)
  - T-011-T4 (redaction — logs et erreurs excluent secrets, tokens, données personnelles, chemins absolus et contenu métier)
  - T-011-T5 (idempotent recovery — rejouer la clé du job réutilise branche, worktree, session, issue et PR sans doublon)
  - T-011-T6 (failure preservation — timeout ou échec conserve logs, journal, branche, worktree et PR du job sans endommager l'autre job)
  - T-011-T7 (Git safety — aucun adaptateur n'expose force-push, reset destructif, suppression de worktree ou fusion)
- **Files in scope :**
  - `hermes/runtime/test_sdd_job_execution.py`
  - `hermes/runtime/job-execution-contract.md`
  - `hermes/runtime/sdd_job_execution.py`
- **Dépendances :** T-010
- **Phases estimées :** RED 30–45 min ; GREEN 90–120 min ; REFACTOR 30–45 min ; SIMPLIFY 20–30 min.
- **Portes à exécuter après green :** `python-unit-job`, `job-contract`,
  `github-bridge-regression`, `runtime-regression`, `git-diff-check`
- **Retour arrière :** retirer les trois fichiers de la branche ; conserver
  tous les objets GitHub/Hermes et worktrees déjà créés pour diagnostic, sans
  nettoyage automatique.
- **Notes :** utiliser des adaptateurs structurés pour Git, worktree, session et
  logs, puis appeler le bridge S-002 pour issue/PR. La tâche ne crée pas la
  carte, n'admet aucun job et ne modifie aucun artefact partagé. Les tests
  emploient des doubles sans réseau ni GitHub réel.

### T-012 : Appliquer le go humain et le fan-in de vague

- **Origine qualifiée :** `spring-architect:T-012`
- **Dépôt d'exécution :** `staaack-io/specs-driven-development`
- **AC-IDs :** AC-045, AC-046, AC-047, AC-134, AC-135, AC-136, AC-137, AC-231
- **Test-IDs :**
  - T-012-T1 (RED wave — aucune surface S-003 ne sait encore consolider une vague terminée)
  - T-012-T2 (awaiting-go — PR prête, checks verts et review approve placent seulement la carte en `awaiting_go`)
  - T-012-T3 (human merge gate — sans go explicite aucune fusion ni carte `done` ; après go et merge humain observé, seule la carte concernée devient `done`)
  - T-012-T4 (fan-in eligibility — le synthesizer attend que toutes les cartes de la vague soient `done` et vérifie chaque journal immuable)
  - T-012-T5 (single writer — seul l'acteur `synthesizer` actualise transactionnellement `04-tasks.md`, `.tdd-state.json` et `05-implementation-log.md`)
  - T-012-T6 (fan-in PR — le synthesizer crée une seule PR de fan-in idempotente et n'appelle aucune fusion)
  - T-012-T7 (wave barrier — aucune tâche de la vague suivante n'est admise avant observation de la fusion humaine de la PR de fan-in)
  - T-012-T8 (crash recovery — interruption avant/après marqueur rend l'ancien ou le nouvel ensemble complet, jamais un mélange)
- **Files in scope :**
  - `hermes/runtime/test_sdd_wave_synthesizer.py`
  - `hermes/runtime/wave-synthesizer-contract.md`
  - `hermes/runtime/sdd_wave_synthesizer.py`
- **Dépendances :** T-010, T-011
- **Phases estimées :** RED 30–45 min ; GREEN 90–120 min ; REFACTOR 30–45 min ; SIMPLIFY 20–30 min.
- **Portes à exécuter après green :** `python-unit-fan-in`,
  `fan-in-contract`, `runtime-regression`, `github-bridge-regression`,
  `git-diff-check`
- **Retour arrière :** retirer les trois fichiers de la branche avant fusion ;
  en interruption, appeler la reprise transactionnelle existante et conserver
  cartes, PR et journaux. Ne jamais nettoyer une vague non consolidée.
- **Notes :** composer `verify_job_journal` et `transactional_fan_in` au lieu
  de les dupliquer. La PR de fan-in est créée sur une branche propre du
  synthesizer. La présence d'un go est une donnée fournie par l'adaptateur
  humain, jamais déduite d'une review ou de checks verts.

### T-013 : Auditer la source S-003 sur exactement 51 AC

- **Origine qualifiée :** `spring-architect:T-013`
- **Dépôt d'exécution :** `staaack-io/specs-driven-development`
- **AC-IDs :** AC-024
- **Test-IDs :**
  - T-013-T1 (RED manifest — le contrat agrégé manque et la liste de commandes marque encore `/sdd-build` comme prévue)
  - T-013-T2 (coverage — le manifeste contient exactement les 51 AC S-003, chacun avec un producteur primaire unique et une preuve exécutable)
  - T-013-T3 (DAG/scopes — T-009 précède T-010, T-010 précède T-011, leurs scopes sont disjoints, T-012 est le fan-in et le graphe est acyclique)
  - T-013-T4 (status — la carte créée par T-010 est visible par le contrat `/sdd-status` sans écriture ni valeur déduite)
  - T-013-T5 (capacity — les contrats prouvent deux writers, trois analyses internes et une gate lourde au plus)
  - T-013-T6 (source regression — toutes les suites build, runtime, bridge, status et skill passent depuis la source)
  - T-013-T7 (safety audit — aucun auto-merge, force-push, reset destructif, secret, chemin absolu versionné ou ordonnanceur Python concurrent)
- **Files in scope :**
  - `hermes/scripts/test_sdd_s003_contract.py`
  - `hermes/skills/sdd-onboard/scripts/test_skill_contract.py`
  - `hermes/runtime/README.md`
  - `hermes/skills/sdd-help/SKILL.md`
  - `hermes/README.md`
  - `docs/artifact-contract.md`
  - `docs/codex-migration.md`
- **Dépendances :** T-012
- **Phases estimées :** RED 30–45 min ; GREEN 60–90 min ; REFACTOR 30–45 min ; SIMPLIFY 20–30 min.
- **Portes à exécuter après green :** `s003-source-contract`, `python-all`,
  `skill-contracts`, `markdownlint`, `git-diff-check`, `ci`
- **Retour arrière :** rétablir les cinq documents et retirer le contrat agrégé ;
  conserver les capacités T-009 à T-012 mais bloquer la publication T-014.
- **Notes :** T-013 est l'unique fan-in d'audit source ; il ne modifie aucun
  fichier détenu par T-009 à T-012. Son manifeste énumère les 51 AC et échoue
  sur tout manque, ajout ou doublon primaire. `/sdd-help` déplace `/sdd-build`
  des commandes prévues vers les commandes installées ; `/sdd-code-simplify`
  reste prévu pour S-004.

### T-014 : Publier le profil 0.6.0 avec parité et rollback

- **Origine qualifiée :** `spring-architect:T-014`
- **Dépôt d'exécution :** `staaack-io/hermes-agent-profile-staaack`
- **AC-IDs :** AC-013, AC-138
- **Test-IDs :**
  - T-014-T1 (RED release — le contrat refuse une distribution encore en 0.5.0 ou sans `/sdd-build` et ses modules runtime)
  - T-014-T2 (skills parity — `skills/sdd-build` et `skills/sdd-help` sont identiques à leurs sources canoniques)
  - T-014-T3 (runtime parity — orchestrateur, enveloppe, synthesizer, contrats, README et tests sont identiques à la source)
  - T-014-T4 (profile tests — les tests build et runtime s'exécutent depuis la disposition profil avec les mêmes résultats)
  - T-014-T5 (distribution — version 0.6.0, changelog, frontmatters, documentation et découverte des tests sont valides)
  - T-014-T6 (rollback — la note de release nomme le retour au profil 0.5.0 sans suppression d'états, journaux, logs ou worktrees)
  - T-014-T7 (publication gate — CI, tests et contrats verts, review approve, zéro fil actionnable et go explicite précèdent la fusion)
  - T-014-T8 (no VPS — aucune mise à jour ou action VPS n'est exécutée par cette tâche)
- **Files in scope :**
  - `scripts/test_validate_distribution.py`
  - `skills/sdd-build/scripts/test_build_guard.py`
  - `skills/sdd-build/scripts/test_skill_contract.py`
  - `hermes/runtime/test_sdd_build_orchestrator.py`
  - `hermes/runtime/test_sdd_job_execution.py`
  - `hermes/runtime/test_sdd_wave_synthesizer.py`
  - `skills/sdd-build/scripts/build_guard.py`
  - `skills/sdd-build/SKILL.md`
  - `skills/sdd-build/references/delegation-contract.md`
  - `skills/sdd-build/references/tdd-cycle-contract.md`
  - `skills/sdd-build/references/role-spring-test-engineer.md`
  - `skills/sdd-build/references/role-spring-implementer.md`
  - `skills/sdd-build/references/role-react-nextjs-test-engineer.md`
  - `skills/sdd-build/references/role-react-nextjs-implementer.md`
  - `skills/sdd-help/SKILL.md`
  - `hermes/runtime/README.md`
  - `hermes/runtime/build-orchestrator-contract.md`
  - `hermes/runtime/sdd_build_orchestrator.py`
  - `hermes/runtime/job-execution-contract.md`
  - `hermes/runtime/sdd_job_execution.py`
  - `hermes/runtime/wave-synthesizer-contract.md`
  - `hermes/runtime/sdd_wave_synthesizer.py`
  - `distribution.yaml`
  - `CHANGELOG.md`
  - `README.md`
  - `.github/workflows/ci.yml`
- **Dépendances :** T-013
- **Phases estimées :** RED 30–45 min ; GREEN copie et packaging 90–120 min ; REFACTOR 30–45 min ; SIMPLIFY 15–30 min.
- **Portes à exécuter après green :** `profile-layout`, `skills-parity`,
  `runtime-parity`, `python-all-profile`, `distribution`, `frontmatter`,
  `markdownlint`, `git-diff-check`, `ci`, `review-approve`,
  `actionable-threads-zero`, `human-approval`
- **Retour arrière :** fermer ou annuler la PR profil et conserver la version
  0.5.0 ; si 0.6.0 est installée ultérieurement, réinstaller 0.5.0 sans
  supprimer ni convertir états, journaux, logs, branches ou worktrees.
- **Notes :** copier les fichiers canoniques sans transformation et exécuter
  les tests depuis la disposition profil. Cette tâche prépare une PR séparée,
  ne la fusionne jamais automatiquement et n'accède à aucun VPS.

### S-003 Primary AC Coverage Matrix

| AC S-003 | Producteur primaire | Test-ID principal |
|---|---|---|
| AC-013 | T-014 | T-014-T1, T-014-T5, T-014-T7 |
| AC-019 | T-009 | T-009-T1, T-009-T6 |
| AC-020–AC-023 | T-010 | T-010-T1, T-010-T2, T-010-T6 |
| AC-024 | T-013 | T-013-T4 |
| AC-027–AC-029 | T-010 | T-010-T3, T-010-T4 |
| AC-030 | T-011 | T-011-T3 |
| AC-031 | T-010 | T-010-T5 |
| AC-032–AC-036 | T-011 | T-011-T2, T-011-T3, T-011-T4 |
| AC-037–AC-044 | T-009 | T-009-T3–T-009-T9 |
| AC-045–AC-047 | T-012 | T-012-T4–T-012-T7 |
| AC-124–AC-127 | T-009 | T-009-T2–T-009-T8 |
| AC-128 | T-010 | T-010-T7 |
| AC-129–AC-133 | T-010 | T-010-T5 |
| AC-134–AC-137 | T-012 | T-012-T2–T-012-T6 |
| AC-138 | T-014 | T-014-T5, T-014-T7 |
| AC-231 | T-012 | T-012-T3, T-012-T6 |
| AC-233–AC-234 | T-011 | T-011-T7 |
| AC-236 | T-010 | T-010-T5 |
| AC-257–AC-259 | T-009 | T-009-T7 |
| AC-260 | T-010 | T-010-T5 |

La matrice contient **51 identifiants uniques sur 51**. T-013-T2 audite
secondairement la liste complète et refuse tout AC S-004 ou doublon primaire.

### S-003 Dependency and Capacity Validation

```text
T-008 done -> T-009 -> T-010 -> T-011 -> T-012 -> T-013 -> T-014
                         ||
                         └-> writer S-004 hors périmètre après T-009
```

- Le graphe est acyclique et l'index suit son ordre topologique.
- T-010 peut progresser avec le writer S-004 après T-009 `done`, qui représente
  le mono fusionné. T-011 dépend de T-010 et attend le prochain slot ; T-010 et
  T-011 ne partagent néanmoins aucun fichier.
- T-012 est le seul writer de synthèse de vague ; T-013 est le seul writer de
  l'audit source ; T-014 est le seul writer du profil.
- Le plafond est de deux leases writers. Les trois analyses internes sont en
  lecture seule et ne consomment aucun lease. Une seule gate lourde est active.
- `/sdd-code-simplify` peut progresser dans un autre worktree après T-009, mais
  ne partage aucun AC ni fichier avec cette tranche planifiée.

### S-003 Cross-cutting Items

- Aucun test ArchUnit, OpenAPI ou migration de base : stack non applicable.
- Les tests GitHub réels et l'E2E complet restent dans les tranches S-005 et
  S-007 ; S-003 utilise des adaptateurs déterministes pour ses contrats directs.
- Les artefacts partagés sont écrits uniquement par T-012 via le runtime v2 ;
  les tâches de production n'élargissent jamais leur scope vers ces fichiers.

### S-003 Open Questions

- (aucune)

### S-003 Resolved Questions

- Les ADR-001, ADR-003 et ADR-004 couvrent respectivement le Kanban, l'isolation
  et le fan-in ; aucun ADR-006 n'est nécessaire.
- Le rollback de publication est le profil 0.5.0 et aucune opération VPS
  n'appartient à S-003.

### S-003 Sign-off

- [x] Le registre progresse sans réutilisation jusqu'à `high_water_mark: 14`.
- [x] T-001 à T-008 conservent leurs textes, preuves et scopes.
- [x] Chaque nouvelle tâche possède des Test-IDs et des chemins littéraux.
- [x] Chaque nouvelle tâche tient dans une plage de 1 à 4 heures.
- [x] Le DAG est acyclique ; T-011 attend T-010 et le second slot reste disponible pour S-004.
- [x] La capacité 2 writers / 3 analyses / 1 gate est respectée.
- [x] Les 51 AC S-003 ont un producteur primaire unique et une preuve.
- [x] Aucune question ouverte ne subsiste et aucun nouvel ADR n'est requis.
- [x] Checklist `design-review.md` relue le 2026-08-03.

Première tâche : `/sdd-build 2026-07-31-hermes-parallel-sdd T-009`.

## Tâches : S-004 — `/sdd-code-simplify`, profil 0.6.1

> Cette section prolonge le registre sans modifier T-001 à T-014. Le
> `high_water_mark` entrant est 14 ; les nouveaux identifiants commencent à
> T-015 et couvrent uniquement AC-014 et AC-139.

### S-004 Inputs

- Conception détaillée : section S-004 de `03-design.md`, 2026-08-03.
- Barrière source : T-009 est `done` ; T-015 peut donc démarrer.
- Barrière de publication : T-016 attend T-014 et T-015 afin que le profil
  0.6.0 précède 0.6.1 et que la source canonique soit prouvée.
- Porte utilisateur : aucune review ni attente de review ; CI, tests, contrats
  et go explicite seulement avant fusion.

### S-004 Task Index

| ID | Titre | AC-IDs | Dépend de | Estimation | Portes |
|---|---|---|---|---|---|
| T-015 | Convertir et prouver `/sdd-code-simplify` dans la source Hermes | AC-014 | T-009 | 3–4 h | unit, skill-contract, s004-contract, python, markdown, diff, CI |
| T-016 | Publier le profil 0.6.1 avec parité et rollback | AC-014, AC-139 | T-014, T-015 | 3–4 h | profile-layout, parity, distribution, python, markdown, diff, CI, go |

### S-004 Tasks

### T-015 : Convertir et prouver `/sdd-code-simplify` dans la source Hermes

- **Origine qualifiée :** `spring-architect:T-015`
- **AC-IDs :** AC-014
- **Test-IDs :**
  - T-015-T1 (RED publication — la source Hermes ne contient pas encore `sdd-code-simplify` et l'aide le classe comme prévu)
  - T-015-T2 (arguments — accepter exactement `/sdd-code-simplify <path> [--dry-run]`, puis refuser argument inconnu, cible de test, glob, symlink ou chemin hors dépôt avant écriture)
  - T-015-T3 (baseline — refuser toute mutation si la commande de tests validée n'est pas verte au départ)
  - T-015-T4 (clarity contract — embarquer et appliquer les catégories existantes : conditions, boucles lisibles, helpers, options, noms, abstractions, retours anticipés, code mort et littéraux répétés)
  - T-015-T5 (file isolation — détenir le lease exact, traiter un fichier à la fois et restaurer seulement le fichier courant si ses tests régressent)
  - T-015-T6 (result evidence — conserver argv structurés et sortie expurgée, puis résumer fichiers, catégories, tests, régressions et résultats `simplified`/`ignored` sans commit automatique)
  - T-015-T7 (dry-run — proposer le même plan et le même résumé sans modifier la cible ni les artefacts partagés)
  - T-015-T8 (source contract — l'aide et la documentation marquent la commande comme installée et le manifeste S-004 contient exactement AC-014 et AC-139 avec un producteur primaire chacun)
- **Files in scope :**
  - `hermes/skills/sdd-code-simplify/SKILL.md`
  - `hermes/skills/sdd-code-simplify/references/clarity-checklist.md`
  - `hermes/skills/sdd-code-simplify/references/delegation-contract.md`
  - `hermes/skills/sdd-code-simplify/scripts/code_simplify_guard.py`
  - `hermes/skills/sdd-code-simplify/scripts/test_code_simplify_guard.py`
  - `hermes/skills/sdd-code-simplify/scripts/test_skill_contract.py`
  - `hermes/scripts/test_sdd_s004_contract.py`
  - `hermes/skills/sdd-onboard/scripts/test_skill_contract.py`
  - `hermes/scripts/test_sdd_s003_contract.py`
  - `hermes/skills/sdd-help/SKILL.md`
  - `hermes/README.md`
  - `docs/codex-migration.md`
- **Dépendances :** T-009
- **Phases estimées :** RED 30–45 min ; GREEN 90–120 min ; REFACTOR 30–45 min ; SIMPLIFY 15–30 min.
- **Portes à exécuter après green :** `python-unit`, `skill-contract`,
  `s004-contract`, `frontmatter`, `markdownlint`, `git-diff-check`, `ci`
- **Retour arrière :** annuler la PR source ou retirer le nouveau dossier et
  les entrées d'aide ; `/sdd-build` et le profil 0.6.0 restent utilisables.
- **Notes :** le garde compose les primitives runtime v2 et ne réimplémente ni
  ordonnanceur, ni lease, ni fingerprint. Les tests utilisent un runner et un
  rôle injectés ; ils ne simplifient aucun fichier réel du dépôt. Cette tâche
  ne demande aucune review et ne fusionne rien sans go explicite.

### T-016 : Publier le profil 0.6.1 avec parité et rollback

- **Origine qualifiée :** `spring-architect:T-016`
- **AC-IDs :** AC-014, AC-139
- **Test-IDs :**
  - T-016-T1 (RED release — le contrat refuse un profil encore en 0.6.0 ou sans `/sdd-code-simplify`)
  - T-016-T2 (skill parity — `skills/sdd-code-simplify` et l'entrée installée de `skills/sdd-help` sont identiques aux sources canoniques)
  - T-016-T3 (profile tests — garde, contrat du skill et contrat S-004 s'exécutent depuis la disposition profil avec les mêmes résultats)
  - T-016-T4 (distribution — version 0.6.1, changelog, frontmatters, documentation et découverte des tests sont cohérents)
  - T-016-T5 (release order — refuser la publication tant que T-014/0.6.0 ou T-015/source ne sont pas fusionnés)
  - T-016-T6 (publication gate — CI, tests et contrats verts puis go explicite précèdent la fusion, sans review ni attente de review)
  - T-016-T7 (rollback — la note de release nomme le retour à 0.6.0 sans supprimer ni convertir états, journaux, logs, branches ou worktrees)
  - T-016-T8 (no VPS — aucune mise à jour ou action VPS n'est exécutée par cette tâche)
- **Files in scope :**
  - `scripts/test_validate_distribution.py`
  - `scripts/test_sdd_s004_contract.py`
  - `skills/sdd-code-simplify/SKILL.md`
  - `skills/sdd-code-simplify/references/clarity-checklist.md`
  - `skills/sdd-code-simplify/references/delegation-contract.md`
  - `skills/sdd-code-simplify/scripts/code_simplify_guard.py`
  - `skills/sdd-code-simplify/scripts/test_code_simplify_guard.py`
  - `skills/sdd-code-simplify/scripts/test_skill_contract.py`
  - `skills/sdd-help/SKILL.md`
  - `distribution.yaml`
  - `CHANGELOG.md`
  - `README.md`
  - `.github/workflows/ci.yml`
- **Dépendances :** T-014, T-015
- **Phases estimées :** RED 30–45 min ; GREEN copie et packaging 90–120 min ; REFACTOR 30–45 min ; SIMPLIFY 15–30 min.
- **Portes à exécuter après green :** `profile-layout`, `skills-parity`,
  `python-all-profile`, `distribution`, `frontmatter`, `markdownlint`,
  `git-diff-check`, `ci`, `explicit-go-before-merge`
- **Retour arrière :** fermer ou annuler la PR profil et conserver la version
  0.6.0 ; si 0.6.1 est installée ultérieurement, réinstaller 0.6.0 sans
  supprimer ni convertir états, journaux, logs, branches ou worktrees.
- **Notes :** copier les fichiers canoniques sans transformation et exécuter
  les mêmes tests depuis la disposition profil. Cette tâche ne demande aucune
  review, ne fusionne rien automatiquement et n'accède à aucun VPS.

### S-004 Primary AC Coverage Matrix

| AC S-004 | Producteur primaire | Preuves principales | Couverture secondaire |
|---|---|---|---|
| AC-014 | T-016 | T-016-T1, T-016-T2, T-016-T3 | T-015-T1, T-015-T4, T-015-T8 |
| AC-139 | T-016 | T-016-T1, T-016-T4, T-016-T5, T-016-T6 | T-015-T8 |

La matrice contient exactement les deux AC S-004, sans AC de tranche voisine.

### S-004 Dependency and Capacity Validation

```text
T-009 done -> T-015
T-014 ─────────┐
               ├─> T-016
T-015 ─────────┘
```

- Le graphe est acyclique et l'index suit son ordre topologique.
- T-015 peut utiliser le second slot prévu face à T-010 ; ses fichiers sont
  disjoints des scopes T-010 à T-014.
- T-016 attend T-014 et T-015 et devient l'unique writer du dépôt profil pour
  0.6.1. Une seule gate lourde est exécutée à la fois.
- Aucun worker ne reçoit en écriture `04-tasks.md`, `.tdd-state.json` ou
  `05-implementation-log.md` ; le synthesizer reste l'écrivain partagé unique.

### S-004 Cross-cutting Items

- Aucun test ArchUnit, OpenAPI, base ou migration : stack non applicable.
- Les contrats de commande et distribution appartiennent aux tâches ; les
  scénarios E2E multi-commandes restent réservés à S-007.
- Aucune porte, demande ou attente de review n'est planifiée pour T-015 ou
  T-016.

### S-004 Open Questions

- (aucune)

### S-004 Resolved Questions

- **Décision autonome :** convertir sans extension le skill Codex existant et
  réutiliser le runtime v2. Cette décision garde la tranche limitée aux deux AC.
- **Décision autonome :** T-016 dépend à la fois de T-014 et T-015 pour rendre
  l'ordre de versions et la provenance source vérifiables.
- **Décision autonome :** les portes S-004 excluent toute review conformément à
  la dernière instruction utilisateur ; le go explicite avant fusion demeure.

### S-004 Sign-off

- [x] Le registre progresse jusqu'à `high_water_mark: 16` sans réutiliser un ID.
- [x] T-001 à T-014 conservent leurs IDs, textes, preuves et scopes.
- [x] Chaque tâche dure 3–4 h et possède Test-IDs, chemins littéraux, dépendances, portes et rollback.
- [x] Chaque tâche de production inclut ses tests dans le même scope.
- [x] AC-014 et AC-139 ont un producteur observable de publication ; T-015 reste le prérequis source traçable.
- [x] Le DAG est acyclique et 0.6.0 précède 0.6.1.
- [x] Aucune question ouverte ni nouvelle décision ADR ne subsiste.
- [x] Checklist `design-review.md` relue le 2026-08-03.

Première tâche : `/sdd-build 2026-07-31-hermes-parallel-sdd T-015`.

## Tâches : S-005 — `/sdd-test`, `/sdd-validate`, profil 0.7.0

### S-005 Task Index

| ID | Tâche | AC primaires | Dépendances | Estimation | Portes |
|---|---|---|---|---|---|
| T-017 | Convertir `/sdd-test` dans la source Hermes | AC-142, AC-196–AC-209 | T-003, T-009 | 3–4 h | unit, contract, scope, traceability, CI |
| T-018 | Convertir `/sdd-validate` et le fan-in des rapports | AC-143–AC-146, AC-210–AC-217 | T-003, T-009 | 3–4 h | unit, contract, fan-in, gate-lock, CI |
| T-019 | Auditer exactement les 32 AC source S-005 | AC-140, AC-141 | T-017, T-018 | 3–4 h | source-audit, help, docs, all-python, CI |
| T-020 | Publier le profil 0.7.0 avec parité et rollback | AC-015, AC-016, AC-147 | T-016, T-019 | 3–4 h | parity, profile, distribution, CI, go |

### T-017 : Convertir `/sdd-test` dans la source Hermes

- **Origine qualifiée :** `spring-architect:T-017`
- **AC-IDs :** AC-142, AC-196 à AC-209
- **Test-IDs :**
  - T-017-T1 (RED publication — le skill et son garde sont absents)
  - T-017-T2 (arguments — accepter `<feature-id> [--gap]` et refuser le reste)
  - T-017-T3 (scope — autoriser uniquement `src/test/**` et `06-test-plan.md`)
  - T-017-T4 (plan — matrice AC/types, Testcontainers, Gap-NNN et `Won't fix`)
  - T-017-T5 (preuves — tags AC, noms descriptifs, argv structurés et sortie expurgée)
  - T-017-T6 (gate — sérialiser la commande de tests avec le verrou runtime)
  - T-017-T7 (traçabilité — publier atomiquement le plan puis régénérer la matrice)
  - T-017-T8 (catalogue — relier AC-196 à AC-209 à des tests exécutables)
- **Files in scope :**
  - `hermes/skills/sdd-test/SKILL.md`
  - `hermes/skills/sdd-test/references/delegation-contract.md`
  - `hermes/skills/sdd-test/references/test-plan-contract.md`
  - `hermes/skills/sdd-test/templates/test-plan.template.md`
  - `hermes/skills/sdd-test/scripts/guard.py`
  - `hermes/skills/sdd-test/scripts/test_test_guard.py`
  - `hermes/skills/sdd-test/scripts/test_skill_contract.py`
- **Dépendances :** T-003, T-009
- **Phases estimées :** RED 30–45 min ; GREEN 90–120 min ; REFACTOR 30 min ; SIMPLIFY 15 min.
- **Portes :** tests du garde, contrat du skill, tests runtime référencés,
  frontmatter, markdownlint, `git diff --check`, CI source.
- **Retour arrière :** retirer le dossier `sdd-test`; aucun fichier de
  production consommateur ni artefact de feature n'est modifié par la PR.
- **Notes :** le rôle de test ne reçoit aucun handle `src/main/**`. Aucun
  commit, fusion ou review n'est automatique.

### T-018 : Convertir `/sdd-validate` et le fan-in des rapports

- **Origine qualifiée :** `spring-architect:T-018`
- **AC-IDs :** AC-143 à AC-146, AC-210 à AC-217
- **Test-IDs :**
  - T-018-T1 (RED publication — le skill et son garde sont absents)
  - T-018-T2 (préconditions — harness disponible, tâches done, résultats frais, aucun bypass)
  - T-018-T3 (routage — Spring, React ou les deux selon les sources modifiées)
  - T-018-T4 (gate — sérialiser Maven, Next, PIT et OWASP sous le verrou runtime)
  - T-018-T5 (fan-in — résultats spécialisés structurés, sans handle partagé)
  - T-018-T6 (writer — écrire uniquement `07-validation-report.md` et `07a-traceability.md`)
  - T-018-T7 (verdicts — décision `approve|request-changes`, technique `PASS|FAIL`)
  - T-018-T8 (preuves — relier AC-210 à AC-217 aux tests GitHub et transactionnels)
- **Files in scope :**
  - `hermes/skills/sdd-validate/SKILL.md`
  - `hermes/skills/sdd-validate/references/delegation-contract.md`
  - `hermes/skills/sdd-validate/references/validation-contract.md`
  - `hermes/skills/sdd-validate/references/role-spring-validator.md`
  - `hermes/skills/sdd-validate/references/role-react-nextjs-validator.md`
  - `hermes/skills/sdd-validate/templates/validation-report.template.md`
  - `hermes/skills/sdd-validate/templates/traceability.template.md`
  - `hermes/skills/sdd-validate/scripts/validation_guard.py`
  - `hermes/skills/sdd-validate/scripts/test_validation_guard.py`
  - `hermes/skills/sdd-validate/scripts/test_skill_contract.py`
- **Dépendances :** T-003, T-009
- **Phases estimées :** RED 30–45 min ; GREEN 90–120 min ; REFACTOR 30 min ; SIMPLIFY 15 min.
- **Portes :** tests du garde, contrat du skill, fan-in, verrou de gate,
  frontmatter, markdownlint, `git diff --check`, CI source.
- **Retour arrière :** retirer le dossier `sdd-validate`; les anciens rapports
  communs restent intacts grâce à la transaction du writer unique.
- **Notes :** T-018 peut être développée avec T-017 sur un scope disjoint, mais
  sa fusion attend T-017. Aucune review n'est demandée.

### T-019 : Auditer exactement les 32 AC source S-005

- **Origine qualifiée :** `spring-architect:T-019`
- **AC-IDs :** AC-140, AC-141
- **Test-IDs :**
  - T-019-T1 (manifeste — exactement 32 AC S-005 sans doublon primaire)
  - T-019-T2 (commandes — les deux skills et leurs suites sont présents)
  - T-019-T3 (DAG — développement parallèle et fusion test avant validate)
  - T-019-T4 (scopes — T-017/T-018 disjoints, writer commun réservé à l'audit)
  - T-019-T5 (capacité — deux writers et une gate lourde au maximum)
  - T-019-T6 (publication — aide et docs classent test/validate comme installées)
  - T-019-T7 (sécurité — aucun scheduler, merge, secret, chemin absolu ou VPS)
- **Files in scope :**
  - `hermes/scripts/test_sdd_s005_contract.py`
  - `hermes/skills/sdd-test/scripts/test_guard.py` (suppression du nom
    découvert à tort comme suite)
  - `hermes/skills/sdd-test/scripts/guard.py`
  - `hermes/skills/sdd-test/scripts/test_test_guard.py`
  - `hermes/skills/sdd-test/scripts/test_skill_contract.py`
  - `hermes/skills/sdd-help/SKILL.md`
  - `hermes/README.md`
  - `docs/artifact-contract.md`
  - `docs/codex-migration.md`
- **Dépendances :** T-017, T-018
- **Phases estimées :** RED 30 min ; GREEN 60–90 min ; REFACTOR 30 min ; SIMPLIFY 15 min.
- **Portes :** contrat S-005, toutes les suites Python Hermes, validation des
  skills, markdownlint, `git diff --check`, CI source.
- **Retour arrière :** annuler la PR d'audit et garder les deux commandes
  sources sur leurs branches sans les annoncer comme installées.
- **Notes :** T-019 est l'unique writer des documents partagés de publication.

### T-020 : Publier le profil 0.7.0 avec parité et rollback

- **Origine qualifiée :** `spring-architect:T-020`
- **AC-IDs :** AC-015, AC-016, AC-147
- **Test-IDs :**
  - T-020-T1 (RED release — profil antérieur ou commandes absentes refusés)
  - T-020-T2 (parité — copies exactes des deux skills et de l'aide)
  - T-020-T3 (profile layout — mêmes tests exécutés depuis `skills/**`)
  - T-020-T4 (distribution — version, changelog, frontmatters et découverte cohérents)
  - T-020-T5 (ordre — profil 0.6.1 et audit T-019 fusionnés avant publication)
  - T-020-T6 (gate — CI et contrats verts puis go explicite, sans review)
  - T-020-T7 (rollback — réinstaller 0.6.1 sans supprimer les preuves)
  - T-020-T8 (no VPS — aucune installation ou mise à jour exécutée)
- **Files in scope :**
  - `scripts/test_validate_distribution.py`
  - `scripts/test_sdd_s005_contract.py`
  - `skills/sdd-test/SKILL.md`
  - `skills/sdd-test/references/delegation-contract.md`
  - `skills/sdd-test/references/test-plan-contract.md`
  - `skills/sdd-test/templates/test-plan.template.md`
  - `skills/sdd-test/scripts/guard.py`
  - `skills/sdd-test/scripts/test_test_guard.py`
  - `skills/sdd-test/scripts/test_skill_contract.py`
  - `skills/sdd-validate/SKILL.md`
  - `skills/sdd-validate/references/delegation-contract.md`
  - `skills/sdd-validate/references/validation-contract.md`
  - `skills/sdd-validate/references/role-spring-validator.md`
  - `skills/sdd-validate/references/role-react-nextjs-validator.md`
  - `skills/sdd-validate/templates/validation-report.template.md`
  - `skills/sdd-validate/templates/traceability.template.md`
  - `skills/sdd-validate/scripts/validation_guard.py`
  - `skills/sdd-validate/scripts/test_validation_guard.py`
  - `skills/sdd-validate/scripts/test_skill_contract.py`
  - `skills/sdd-help/SKILL.md`
  - `distribution.yaml`
  - `CHANGELOG.md`
  - `README.md`
  - `.github/workflows/ci.yml`
- **Dépendances :** T-016, T-019
- **Phases estimées :** RED 30 min ; GREEN 90–120 min ; REFACTOR 30 min ; SIMPLIFY 15 min.
- **Portes :** parité, runner profil, distribution, frontmatter, markdownlint,
  `git diff --check`, CI et go explicite avant fusion.
- **Retour arrière :** fermer ou annuler la PR 0.7.0 et conserver 0.6.1; après
  publication, réinstaller 0.6.1 sans supprimer ni convertir les preuves.
- **Notes :** aucune review, fusion automatique, action VPS ou déploiement.

### S-005 Primary AC Coverage Matrix

| AC | Producteur primaire | Preuve principale |
|---|---|---|
| AC-015 | T-020 | T-020-T1 à T-020-T4 |
| AC-016 | T-020 | T-020-T1 à T-020-T4 |
| AC-140 | T-019 | T-019-T3, T-019-T4 |
| AC-141 | T-019 | T-019-T3 |
| AC-142 | T-017 | T-017-T3, T-017-T7 |
| AC-143 | T-018 | T-018-T2 |
| AC-144 | T-018 | T-018-T3, T-018-T5, T-018-T6 |
| AC-145 | T-018 | T-018-T7 |
| AC-146 | T-018 | T-018-T7 |
| AC-147 | T-020 | T-020-T4 à T-020-T6 |
| AC-196–AC-209 | T-017 | T-017-T8 et catalogue exécutable |
| AC-210–AC-217 | T-018 | T-018-T8 et catalogue exécutable |

Les plages de la matrice se développent en 32 AC distincts. Chaque AC possède
un seul producteur primaire; les tests existants restent des preuves
secondaires lorsque leur producteur historique appartient à une autre tranche.

### S-005 Dependency and Capacity Validation

- Le DAG est acyclique. T-017 et T-018 ont des scopes disjoints et peuvent
  occuper les deux slots writers; T-019 puis T-020 sont séquentielles.
- T-018 n'est jamais fusionnée avant T-017 malgré leur développement parallèle.
- Les gates Maven, Next, PIT et OWASP partagent le verrou global canonique.
- Aucun worker n'écrit directement les artefacts partagés de fan-in.

### S-005 Open Questions

- (aucune)

### S-005 Resolved Questions

- **Décision autonome :** quatre tâches préservent scopes et rollbacks.
- **Décision autonome :** les preuves AC-196 à AC-217 doivent référencer des
  tests exécutables, pas seulement un manifeste Markdown.
- **Décision autonome :** aucune review n'est une gate; le go explicite de
  fusion demeure une barrière séparée.

### S-005 Sign-off

- [x] `high_water_mark: 20`; aucun ID T-001 à T-016 n'est réutilisé.
- [x] Les 32 AC sont couverts exactement une fois comme producteurs primaires.
- [x] Chaque tâche possède tests, fichiers littéraux, dépendances, portes et rollback.
- [x] Le DAG permet deux writers puis impose audit et publication séquentiels.
- [x] Aucune question ouverte ni décision ADR supplémentaire.

Première tâche : `/sdd-build 2026-07-31-hermes-parallel-sdd T-017`.

## Tâches : S-006 — `/sdd-review`, `/sdd-ship`, profil 0.8.0

### S-006 Task Index

| ID | Tâche | AC primaires | Dépendances | Estimation | Portes |
|---|---|---|---|---|---|
| T-021 | Convertir `/sdd-review` dans la source Hermes | AC-150, AC-151 | T-018, T-009 | 3–4 h | unit, contract, fan-in, scope, CI |
| T-022 | Convertir `/sdd-ship` sans capacité de déploiement | AC-152, AC-153, AC-235, AC-261–AC-263 | T-018, T-009 | 3–4 h | unit, contract, no-deploy, scope, CI |
| T-023 | Auditer exactement les 13 AC source S-006 | AC-148, AC-149 | T-021, T-022 | 3–4 h | source-audit, help, docs, all-python, CI |
| T-024 | Publier le profil 0.8.0 avec parité et rollback | AC-017, AC-018, AC-154 | T-020, T-023 | 3–4 h | parity, profile, distribution, CI, go |

### T-021 : Convertir `/sdd-review` dans la source Hermes

- **Origine qualifiée :** `spring-architect:T-021`
- **AC-IDs :** AC-150, AC-151
- **Test-IDs :**
  - T-021-T1 (RED publication — le skill et son garde sont absents)
  - T-021-T2 (arguments — accepter `[<feature-id>] [--base <ref>]` sans shell)
  - T-021-T3 (routage — déléguer Spring, React ou les deux selon le diff)
  - T-021-T4 (lecture — diff et artefacts transmis sans handle d'écriture)
  - T-021-T5 (fan-in — consolider les constats structurés sans doublon)
  - T-021-T6 (writer — écrire uniquement `08-code-review.md` atomiquement)
  - T-021-T7 (verdict — vocabulaire fermé et revue informative non bloquante)
  - T-021-T8 (sécurité — expurger secrets, données métier et chemins absolus)
- **Files in scope :**
  - `hermes/skills/sdd-review/SKILL.md`
  - `hermes/skills/sdd-review/references/delegation-contract.md`
  - `hermes/skills/sdd-review/references/review-contract.md`
  - `hermes/skills/sdd-review/references/role-spring-code-reviewer.md`
  - `hermes/skills/sdd-review/references/role-react-nextjs-code-reviewer.md`
  - `hermes/skills/sdd-review/templates/code-review.template.md`
  - `hermes/skills/sdd-review/scripts/review_guard.py`
  - `hermes/skills/sdd-review/scripts/test_review_guard.py`
  - `hermes/skills/sdd-review/scripts/test_skill_contract.py`
- **Dépendances :** T-018, T-009
- **Phases estimées :** RED 30–45 min ; GREEN 90–120 min ; REFACTOR 30 min ; SIMPLIFY 15 min.
- **Portes :** tests du garde, contrat du skill, fan-in, frontmatter,
  markdownlint, `git diff --check`, CI source.
- **Retour arrière :** retirer `sdd-review`; aucun rapport de feature existant
  n'est modifié par la PR tant que la commande n'est pas invoquée.
- **Notes :** la commande SDD effectue une revue technique déléguée ; la PR de
  migration ne demande aucune review à une personne.

### T-022 : Convertir `/sdd-ship` sans capacité de déploiement

- **Origine qualifiée :** `spring-architect:T-022`
- **AC-IDs :** AC-152, AC-153, AC-235, AC-261 à AC-263
- **Test-IDs :**
  - T-022-T1 (RED publication — le skill et son garde sont absents)
  - T-022-T2 (arguments — accepter `[<feature-id>] [--base <ref>]` sans shell)
  - T-022-T3 (préconditions — validation, revue, questions, baseline et scope)
  - T-022-T4 (rollback — détection, limitation sous cinq minutes, restauration)
  - T-022-T5 (observabilité — métriques, journaux, alertes et dashboard ou justification)
  - T-022-T6 (flags — valeur, arrêt d'urgence, responsable et retrait)
  - T-022-T7 (notes — externes et internes sans données sensibles)
  - T-022-T8 (no-deploy — aucune primitive shell, réseau, VPS ou déploiement)
- **Files in scope :**
  - `hermes/skills/sdd-ship/SKILL.md`
  - `hermes/skills/sdd-ship/references/delegation-contract.md`
  - `hermes/skills/sdd-ship/references/shipping-contract.md`
  - `hermes/skills/sdd-ship/templates/ship-plan.template.md`
  - `hermes/skills/sdd-ship/scripts/ship_guard.py`
  - `hermes/skills/sdd-ship/scripts/test_ship_guard.py`
  - `hermes/skills/sdd-ship/scripts/test_skill_contract.py`
- **Dépendances :** T-018, T-009
- **Phases estimées :** RED 30–45 min ; GREEN 90–120 min ; REFACTOR 30 min ; SIMPLIFY 15 min.
- **Portes :** tests du garde, contrat du skill, preuve négative de déploiement,
  frontmatter, markdownlint, `git diff --check`, CI source.
- **Retour arrière :** retirer `sdd-ship`; aucun déploiement, mutation VPS ou
  modification de production n'a pu être exécuté.
- **Notes :** T-022 est développable avec T-021 sur un scope disjoint, mais sa
  fusion attend celle de T-021. Aucun reviewer n'est demandé.

### T-023 : Auditer exactement les 13 AC source S-006

- **Origine qualifiée :** `spring-architect:T-023`
- **AC-IDs :** AC-148, AC-149
- **Test-IDs :**
  - T-023-T1 (manifeste — exactement 13 AC et un producteur primaire par AC)
  - T-023-T2 (commandes — les deux skills et leurs suites sont présents)
  - T-023-T3 (DAG — développement parallèle, fusion review avant ship)
  - T-023-T4 (scopes — T-021/T-022 disjoints, documents réservés à l'audit)
  - T-023-T5 (publication — aide et docs classent les deux commandes installées)
  - T-023-T6 (sécurité — aucun déploiement, merge, secret, chemin absolu ou VPS)
- **Files in scope :**
  - `hermes/scripts/test_sdd_s006_contract.py`
  - `hermes/skills/sdd-help/SKILL.md`
  - `hermes/README.md`
  - `docs/artifact-contract.md`
  - `docs/codex-migration.md`
- **Dépendances :** T-021, T-022
- **Phases estimées :** RED 30 min ; GREEN 60–90 min ; REFACTOR 30 min ; SIMPLIFY 15 min.
- **Portes :** contrat S-006, toutes les suites Python Hermes, validation des
  skills, markdownlint, `git diff --check`, CI source.
- **Retour arrière :** annuler la PR d'audit et garder les deux commandes sur
  leurs branches sans les annoncer comme installées.
- **Notes :** T-023 est l'unique writer des documents partagés de publication.

### T-024 : Publier le profil 0.8.0 avec parité et rollback

- **Origine qualifiée :** `spring-architect:T-024`
- **AC-IDs :** AC-017, AC-018, AC-154
- **Test-IDs :**
  - T-024-T1 (RED release — profil antérieur ou commandes absentes refusés)
  - T-024-T2 (parité — copies exactes de review, ship et aide)
  - T-024-T3 (profile layout — mêmes suites exécutées depuis `skills/**`)
  - T-024-T4 (distribution — version 0.8.0, changelog et découverte cohérents)
  - T-024-T5 (ordre — profil 0.7.0 et audit T-023 fusionnés avant publication)
  - T-024-T6 (gate — CI et contrats verts puis go explicite, sans reviewer)
  - T-024-T7 (rollback — réinstaller 0.7.0 en conservant les preuves)
  - T-024-T8 (no VPS — aucune installation, mise à jour ou livraison exécutée)
- **Files in scope :**
  - `scripts/test_validate_distribution.py`
  - `scripts/test_sdd_s006_contract.py`
  - `skills/sdd-review/SKILL.md`
  - `skills/sdd-review/references/delegation-contract.md`
  - `skills/sdd-review/references/review-contract.md`
  - `skills/sdd-review/references/role-spring-code-reviewer.md`
  - `skills/sdd-review/references/role-react-nextjs-code-reviewer.md`
  - `skills/sdd-review/templates/code-review.template.md`
  - `skills/sdd-review/scripts/review_guard.py`
  - `skills/sdd-review/scripts/test_review_guard.py`
  - `skills/sdd-review/scripts/test_skill_contract.py`
  - `skills/sdd-ship/SKILL.md`
  - `skills/sdd-ship/references/delegation-contract.md`
  - `skills/sdd-ship/references/shipping-contract.md`
  - `skills/sdd-ship/templates/ship-plan.template.md`
  - `skills/sdd-ship/scripts/ship_guard.py`
  - `skills/sdd-ship/scripts/test_ship_guard.py`
  - `skills/sdd-ship/scripts/test_skill_contract.py`
  - `skills/sdd-help/SKILL.md`
  - `distribution.yaml`
  - `CHANGELOG.md`
  - `README.md`
  - `.github/workflows/ci.yml`
- **Dépendances :** T-020, T-023
- **Phases estimées :** RED 30 min ; GREEN 90–120 min ; REFACTOR 30 min ; SIMPLIFY 15 min.
- **Portes :** parité, runner profil, distribution, frontmatter, markdownlint,
  `git diff --check`, CI et go explicite avant fusion.
- **Retour arrière :** fermer la PR 0.8.0 et conserver 0.7.0; après
  publication, réinstaller 0.7.0 sans supprimer ni convertir les preuves.
- **Notes :** aucune review humaine, fusion automatique, action VPS ou déploiement.

### S-006 Primary AC Coverage Matrix

| AC | Producteur primaire | Preuve principale |
|---|---|---|
| AC-017, AC-018, AC-154 | T-024 | T-024-T1 à T-024-T7 |
| AC-148, AC-149 | T-023 | T-023-T1, T-023-T3, T-023-T4 |
| AC-150, AC-151 | T-021 | T-021-T3 à T-021-T7 |
| AC-152, AC-153, AC-235, AC-261–AC-263 | T-022 | T-022-T3 à T-022-T8 |

Les plages se développent en 13 AC distincts avec un producteur primaire
unique. Les preuves S-005 restent secondaires et ne sont pas réattribuées.

### S-006 Dependency and Capacity Validation

- Le DAG est acyclique. T-021 et T-022 ont des scopes disjoints et peuvent
  occuper les deux slots writers; T-023 puis T-024 sont séquentielles.
- T-022 n'est jamais fusionnée avant T-021 malgré leur développement parallèle.
- Aucun skill S-006 ne peut lancer un déploiement ou écrire hors de son artefact.

### S-006 Open Questions

- (aucune)

### S-006 Resolved Questions

- **Décision autonome :** quatre tâches séparent commandes, audit et profil.
- **Décision autonome :** `/sdd-review` est une commande technique du produit;
  aucune personne n'est sollicitée pour relire les PR de migration.
- **Décision autonome :** `/sdd-ship` produit uniquement un plan structuré et
  ne reçoit aucune primitive d'exécution de déploiement.

### S-006 Sign-off

- [x] `high_water_mark: 24`; aucun ID existant n'est réutilisé.
- [x] Les 13 AC possèdent un producteur primaire unique.
- [x] Chaque tâche possède tests, fichiers littéraux, dépendances, portes et rollback.
- [x] Le DAG autorise deux writers puis impose audit et publication séquentiels.
- [x] Aucune question ouverte ni décision ADR supplémentaire.

Première tâche : `/sdd-build 2026-07-31-hermes-parallel-sdd T-021`.

## Tâches : S-007 — E2E local complet et profil candidat 0.9.0

### S-007 Task Index

| ID | Tâche | AC primaires | Dépendances | Estimation | Portes |
|---|---|---|---|---|---|
| T-025 | Prouver deux writers full-stack réellement concurrents | AC-156, AC-219, AC-227 | T-024 | 3–4 h | unit, overlap, capacity, scope, CI |
| T-026 | Prouver attente, échec isolé et reprise transactionnelle | AC-157, AC-158, AC-228 | T-024 | 3–4 h | unit, dependency, failure, recovery, fan-in, CI |
| T-027 | Étendre le runner jetable de onboard à ship | AC-155, AC-218, AC-226 | T-025, T-026 | 3–4 h | e2e, lifecycle, disposable, all-python, CI |
| T-028 | Auditer les commandes et les onze AC de S-007 | AC-225 | T-027 | 2–3 h | source-audit, help, docs, all-python, CI |
| T-029 | Publier le profil candidat 0.9.0 | AC-159 | T-028 | 3–4 h | parity, profile-e2e, distribution, CI, go |

### T-025 : Prouver deux writers full-stack réellement concurrents

- **Origine qualifiée :** `spring-architect:T-025`
- **AC-IDs :** AC-156, AC-219, AC-227
- **Test-IDs :**
  - T-025-T1 (RED concurrence — le scénario full-stack parallèle est absent)
  - T-025-T2 (writers — backend et frontend écrivent des fichiers disjoints)
  - T-025-T3 (chevauchement — leurs intervalles monotoniques se recouvrent strictement)
  - T-025-T4 (capacité — le pic observé vaut deux et ne dépasse jamais deux)
  - T-025-T5 (enveloppes — issue, carte, branche, worktree, session et PR sont uniques par tâche)
  - T-025-T6 (conflit — deux scopes partageant un chemin sont sérialisés)
  - T-025-T7 (preuves — intervalles, identités et fichiers sont publiés sans chemin absolu)
- **Files in scope :**
  - `hermes/e2e/parallel_scenario.py`
  - `hermes/e2e/test_parallel_scenario.py`
- **Dépendances :** T-024
- **Phases estimées :** RED 30–45 min ; GREEN 90–120 min ; REFACTOR 30 min ; SIMPLIFY 15 min.
- **Portes :** tests du scénario, chevauchement monotone positif, pic de
  concurrence égal à deux, sérialisation du conflit, scope, `git diff --check`,
  CI source.
- **Retour arrière :** retirer les deux fichiers du scénario ; le runner
  existant limité au plan reste inchangé.
- **Notes :** utiliser l'admission et les leases du runtime canonique, jamais un
  second ordonnanceur. Les deux writers sont de vrais processus locaux dans un
  dépôt jetable et non une succession simulée d'événements.

### T-026 : Prouver attente, échec isolé et reprise transactionnelle

- **Origine qualifiée :** `spring-architect:T-026`
- **AC-IDs :** AC-157, AC-158, AC-228
- **Test-IDs :**
  - T-026-T1 (RED reprise — le scénario d'interruption est absent)
  - T-026-T2 (dépendance — la tâche fan-in reste non admissible avant fusion et go observés)
  - T-026-T3 (isolement — l'échec ou timeout injecté d'un writer ne révoque pas l'autre)
  - T-026-T4 (conservation — changements et preuves du writer vert survivent à l'échec pair)
  - T-026-T5 (reprise — le job interrompu reprend avec les mêmes identités sans doublon)
  - T-026-T6 (fan-in — la reprise rend l'ancien ou le nouvel ensemble complet)
  - T-026-T7 (atomicité — aucun mélange d'artefacts partagés n'est observable)
  - T-026-T8 (no-merge — aucune fusion n'est exécutée sans go explicite)
- **Files in scope :**
  - `hermes/e2e/recovery_scenario.py`
  - `hermes/e2e/test_recovery_scenario.py`
- **Dépendances :** T-024
- **Phases estimées :** RED 30–45 min ; GREEN 90–120 min ; REFACTOR 30 min ; SIMPLIFY 15 min.
- **Portes :** tests de dépendance, timeout/échec injecté, conservation,
  reprise, idempotence, fan-in atomique, absence de merge, `git diff --check`,
  CI source.
- **Retour arrière :** retirer les deux fichiers du scénario ; aucun état réel,
  PR distante ou artefact de feature n'est muté.
- **Notes :** T-025 et T-026 ont des scopes disjoints et occupent au plus les
  deux slots. L'échec est injecté uniquement dans leur bac à sable local.

### T-027 : Étendre le runner jetable de onboard à ship

- **Origine qualifiée :** `spring-architect:T-027`
- **AC-IDs :** AC-155, AC-218, AC-226
- **Test-IDs :**
  - T-027-T1 (RED parcours — le runner s'arrête encore après plan)
  - T-027-T2 (cycle — onboard, wire, spec, spec-review, epic-plan/plan, build, simplify, test, validate, review et ship sont traversés)
  - T-027-T3 (dossier — tout le parcours vit sous une racine temporaire supprimable avec sentinelle)
  - T-027-T4 (fan-in — les scénarios T-025/T-026 sont exécutés avant les commandes dépendantes)
  - T-027-T5 (Git — chaque tâche conserve issue, carte, branche, worktree, session et PR dédiés)
  - T-027-T6 (barrière — la tâche dépendante attend fusion et go sans effectuer la fusion)
  - T-027-T7 (échec — le runner expose une reprise explicite du run conservé)
  - T-027-T8 (sortie — le rapport final référence toutes les preuves sans secret ni chemin absolu)
- **Files in scope :**
  - `hermes/e2e/run_sdd_e2e.py`
  - `hermes/e2e/test_run_sdd_e2e.py`
  - `hermes/e2e/README.md`
- **Dépendances :** T-025, T-026
- **Phases estimées :** RED 30–45 min ; GREEN 90–120 min ; REFACTOR 30 min ; SIMPLIFY 15 min.
- **Portes :** tests du runner, E2E local jetable, cycle complet, enveloppes
  Git/Kanban, reprise, toutes les suites Python Hermes, markdownlint,
  `git diff --check`, CI source.
- **Retour arrière :** revenir au runner borné au plan et supprimer uniquement
  les runs portant la sentinelle E2E ; les runs en échec restent conservés par défaut.
- **Notes :** T-027 ne démarre qu'après fusion autorisée de T-025 et T-026. Le
  runner n'utilise ni VPS, ni dépôt métier, ni merge automatique.

### T-028 : Auditer les commandes et les onze AC de S-007

- **Origine qualifiée :** `spring-architect:T-028`
- **AC-IDs :** AC-225
- **Test-IDs :**
  - T-028-T1 (manifeste — exactement onze AC S-007 et un producteur primaire par AC)
  - T-028-T2 (commandes — toutes les commandes onboard à ship sont installées)
  - T-028-T3 (DAG — T-025/T-026 parallèles puis T-027/T-028 séquentielles)
  - T-028-T4 (preuves — overlap, capacité, conflit, dépendance, échec et fan-in sont exécutables)
  - T-028-T5 (lifecycle — issue, carte, branche, worktree, session et PR par tâche)
  - T-028-T6 (sécurité — aucun reviewer humain, merge, VPS, déploiement ou chemin absolu)
- **Files in scope :**
  - `hermes/scripts/test_sdd_s007_contract.py`
  - `hermes/skills/sdd-help/SKILL.md`
  - `hermes/README.md`
  - `docs/artifact-contract.md`
  - `docs/codex-migration.md`
- **Dépendances :** T-027
- **Phases estimées :** RED 30 min ; GREEN 60–90 min ; REFACTOR 30 min ; SIMPLIFY 15 min.
- **Portes :** contrat S-007, toutes les suites Python Hermes, validation des
  skills, markdownlint, `git diff --check`, CI source.
- **Retour arrière :** annuler la PR d'audit et ne pas annoncer le runner comme
  complet ; les scénarios source restent isolés sur leurs branches.
- **Notes :** T-028 est l'unique writer des documents partagés de publication.

### T-029 : Publier le profil candidat 0.9.0

- **Origine qualifiée :** `spring-architect:T-029`
- **AC-IDs :** AC-159
- **Test-IDs :**
  - T-029-T1 (RED release — version antérieure ou surface E2E absente refusées)
  - T-029-T2 (parité — runtime, skills, scénarios, runner et aide sont des copies exactes)
  - T-029-T3 (profile layout — les suites E2E s'exécutent depuis le profil)
  - T-029-T4 (distribution — version 0.9.0, précédent 0.8.0 et changelog cohérents)
  - T-029-T5 (gate — runner complet, contrats, CI et parité sont verts)
  - T-029-T6 (ordre — T-028 et le profil 0.8.0 sont fusionnés avant publication)
  - T-029-T7 (rollback — réinstaller 0.8.0 sans supprimer les preuves)
  - T-029-T8 (barrières — go explicite, aucune review humaine, fusion automatique, action VPS ou déploiement)
- **Files in scope :**
  - `scripts/run_skill_tests.py`
  - `scripts/test_run_skill_tests.py`
  - `scripts/test_validate_distribution.py`
  - `scripts/test_sdd_s007_contract.py`
  - `hermes/e2e/parallel_scenario.py`
  - `hermes/e2e/test_parallel_scenario.py`
  - `hermes/e2e/recovery_scenario.py`
  - `hermes/e2e/test_recovery_scenario.py`
  - `hermes/e2e/run_sdd_e2e.py`
  - `hermes/e2e/test_run_sdd_e2e.py`
  - `hermes/e2e/README.md`
  - `skills/sdd-help/SKILL.md`
  - `distribution.yaml`
  - `CHANGELOG.md`
  - `README.md`
  - `.github/workflows/ci.yml`
- **Dépendances :** T-024, T-028
- **Phases estimées :** RED 30 min ; GREEN 90–120 min ; REFACTOR 30 min ; SIMPLIFY 15 min.
- **Portes :** parité, runner profil, distribution, frontmatter, markdownlint,
  `git diff --check`, CI et go explicite avant fusion.
- **Retour arrière :** fermer la PR 0.9.0 et conserver 0.8.0 ; après
  publication, réinstaller 0.8.0 sans supprimer états, journaux, logs,
  branches, worktrees ou preuves E2E.
- **Notes :** 0.9.0 est un candidat local complet, pas une autorisation de
  pilote VPS, de déploiement ou de fusion automatique.

### S-007 Primary AC Coverage Matrix

| AC | Producteur primaire | Preuve principale |
|---|---|---|
| AC-156, AC-219, AC-227 | T-025 | T-025-T2 à T-025-T7 |
| AC-157, AC-158, AC-228 | T-026 | T-026-T2 à T-026-T8 |
| AC-155, AC-218, AC-226 | T-027 | T-027-T2 à T-027-T8 |
| AC-225 | T-028 | T-028-T1 à T-028-T6 |
| AC-159 | T-029 | T-029-T1 à T-029-T8 |

La matrice développe exactement onze AC distincts, sans réattribuer les
critères secondaires AC-207 à AC-217 exercés par les mêmes scénarios.

### S-007 Dependency and Capacity Validation

- Le DAG est acyclique. T-025 et T-026 ont des scopes disjoints et peuvent
  occuper les deux slots writers ; T-027, T-028 puis T-029 sont séquentielles.
- T-027 reste inadmissible tant que les deux PR parentes ne sont pas fusionnées
  après go explicite ; aucune étape du plan n'exécute elle-même une fusion.
- Le scénario mesure des intervalles monotoniques : le chevauchement
  backend/frontend est strictement positif et le pic de writers vaut deux.
- Le conflit de scope est sérialisé ; l'échec ou timeout d'un writer conserve
  le résultat vert de l'autre et la reprise produit un fan-in complet.

### S-007 Open Questions

- (aucune)

### S-007 Resolved Questions

- **Décision autonome — modules de preuve disjoints :** concurrence et reprise
  sont séparées pour rendre les scopes parallélisables et les échecs lisibles.
- **Décision autonome — concurrence mesurée :** des processus locaux et des
  intervalles monotoniques prouvent un overlap réel ; des événements séquentiels
  préfabriqués ne suffisent pas.
- **Décision autonome — GitHub sans mutation distante :** le bac à sable local
  matérialise et vérifie issue, carte, branche, worktree, session et PR par
  tâche via les adaptateurs canoniques ; aucun dépôt externe n'est modifié.
- **Décision autonome — aucune review humaine :** les gates locales, CI, parité
  et go explicite suffisent ; aucune personne n'est sollicitée pour reviewer.

### S-007 Sign-off

- [x] `high_water_mark: 29`; aucun ID existant n'est réutilisé.
- [x] Les onze AC possèdent un producteur primaire unique.
- [x] Chaque tâche possède tests, fichiers littéraux, dépendances, portes et rollback.
- [x] Le DAG autorise deux writers puis impose intégration, audit et profil séquentiels.
- [x] Aucune question ouverte ni décision ADR supplémentaire.

Première vague : `/sdd-build 2026-07-31-hermes-parallel-sdd --parallel`
admet T-025 et T-026 lorsque T-024 est terminée.

## Tâches : S-008 — conformité VPS, pilote Super Lily et profil 1.0.0

> T-030 à T-032 sont des tâches locales autorisées sans réseau. T-033 à T-038
> sont des opérations externes `pending` : elles exigent un go explicite, les
> credentials nécessaires et la réussite de toutes leurs dépendances. Ce plan
> ne fournit aucune autorisation de fusion, SSH, mutation GitHub, gateway,
> pilote, publication ou déploiement et ne demande aucun reviewer humain.

### S-008 Task Index

| ID | Tâche | Producteur primaire de | Dépendances | Estimation | Admission |
|---|---|---|---|---|---|
| T-030 | Encoder la politique de conformité VPS | AC-163, AC-169, AC-175–AC-177, AC-181, AC-187, AC-190–AC-194, AC-266–AC-268 | T-029 | 2–4 h | local |
| T-031 | Générer un dry-run borné du pilote | AC-170–AC-174, AC-183 | T-029 | 2–4 h | local |
| T-032 | Auditer S-008 et la traçabilité 286/286 | AC-232 | T-030, T-031 | 2–4 h | local |
| T-033 | Préparer GitHub CLI et mettre à jour le profil VPS | AC-161, AC-162, AC-164–AC-168, AC-240, AC-264 | T-032 | 1–4 h | externe bloqué |
| T-034 | Préparer les clones, Issues, projets et boards | AC-008, AC-178–AC-180, AC-182, AC-238, AC-239, AC-241, AC-242 | T-033 | 2–4 h | externe bloqué |
| T-035 | Valider deux jobs sandbox réels | AC-184–AC-186, AC-229, AC-230, AC-265 | T-034 | 2–4 h | externe bloqué |
| T-036 | Installer le gateway utilisateur | AC-188, AC-189 | T-035 | 1–2 h | externe bloqué |
| T-037 | Exécuter le pilote Super Lily onboard→ship | AC-220–AC-224, AC-269–AC-271 | T-036 | 3–4 h | externe bloqué |
| T-038 | Publier le profil 1.0.0 | AC-160 | T-037 | 2–4 h | externe bloqué |

### T-030 : Encoder la politique de conformité VPS

- **Origine qualifiée :** `spring-architect:T-030`
- **AC-IDs :** AC-163, AC-169, AC-175, AC-176, AC-177, AC-181, AC-187,
  AC-190, AC-191, AC-192, AC-193, AC-194, AC-266, AC-267, AC-268
- **Test-IDs :**
  - T-030-T1 (RED — le validateur de politique VPS est absent)
  - T-030-T2 (secrets — token, credential, transcript et chemin absolu sont refusés)
  - T-030-T3 (Hermes — shell de connexion ou binaire absolu distant, board explicite et `--yolo` interdit)
  - T-030-T4 (capacité — profondeur 1, auto-approve faux et gateway bloqué avant deux succès)
  - T-030-T5 (service — gateway système et `sudo` sont refusés)
  - T-030-T6 (rétention — carte, branche, worktree, logs et journal sont conservés tant que les preuves manquent)
  - T-030-T7 (pureté — aucun import ou appel réseau, SSH ou subprocess)
- **Files in scope :**
  - `hermes/operations/vps-pilot-policy-contract.md`
  - `hermes/operations/vps_pilot_policy.py`
  - `hermes/operations/test_vps_pilot_policy.py`
- **Dépendances :** T-029, limité au candidat local 0.9.0 prouvé par PR #58
- **Phases estimées :** RED 30 min ; GREEN 60–90 min ; REFACTOR 30 min ; SIMPLIFY 15 min.
- **Portes :** unit policy, import safety, redaction, scope, toutes les suites Python, `git diff --check`, CI source.
- **Retour arrière :** retirer ces trois fichiers ; aucune ressource externe n'a été contactée.
- **Notes :** le module accepte des données structurées et retourne des erreurs ; il ne possède aucune primitive d'exécution. L'identité SSH et la cible de la spécification sont comparées sous forme de valeurs attendues mais ne sont jamais utilisées pour se connecter.

### T-031 : Générer un dry-run borné du pilote

- **Origine qualifiée :** `spring-architect:T-031`
- **AC-IDs :** AC-170, AC-171, AC-172, AC-173, AC-174, AC-183
- **Test-IDs :**
  - T-031-T1 (RED — le générateur de dry-run n'existe pas)
  - T-031-T2 (config — les trois limites Kanban valent 2 et `failure_limit` vaut 2)
  - T-031-T3 (validation — le plan termine par une vérification de configuration)
  - T-031-T4 (dry-run — Super Lily est préparé avec `max-workers=2` sans dispatch réel)
  - T-031-T5 (inertie — aucune ligne n'est exécutée et aucun client réseau n'est importé)
  - T-031-T6 (sortie — commandes ordonnées, board explicite et valeurs expurgées)
- **Files in scope :**
  - `hermes/operations/vps_pilot_dry_run.py`
  - `hermes/operations/test_vps_pilot_dry_run.py`
  - `hermes/operations/templates/vps-pilot-plan.template.json`
- **Dépendances :** T-029, limité au candidat local 0.9.0 prouvé par PR #58
- **Phases estimées :** RED 30 min ; GREEN 60–90 min ; REFACTOR 30 min ; SIMPLIFY 15 min.
- **Portes :** unit dry-run, config contract, no-exec, JSON schema, toutes les suites Python, `git diff --check`, CI source.
- **Retour arrière :** retirer les deux modules et le modèle ; aucune configuration VPS n'a été modifiée.
- **Notes :** T-030 et T-031 ont des scopes disjoints et sont les deux seuls writers de leur vague. Le dry-run prépare aussi les étapes du pilote sans accès au VPS ou à Super Lily.

### T-032 : Auditer S-008 et la traçabilité 286/286

- **Origine qualifiée :** `spring-architect:T-032`
- **AC-IDs :** AC-232
- **Test-IDs :**
  - T-032-T1 (RED — le contrat S-008 et son inventaire exact sont absents)
  - T-032-T2 (slice — exactement 57 AC S-008 ont un producteur primaire unique)
  - T-032-T3 (Epic — les huit tranches couvrent exactement 286 AC sans trou ni doublon primaire)
  - T-032-T4 (DAG — deux writers locaux maximum puis tâches externes séquentielles)
  - T-032-T5 (barrières — toute mise à jour VPS exige version fusionnée, gate verte et go explicite)
  - T-032-T6 (scopes — chemins littéraux, relatifs, disjoints dans la vague locale)
  - T-032-T7 (sécurité — aucun reviewer humain, merge, SSH, gateway ou déploiement exécuté par l'audit)
- **Files in scope :**
  - `hermes/scripts/test_sdd_s008_contract.py`
  - `hermes/operations/vps-pilot-runbook.md`
  - `hermes/README.md`
  - `docs/codex-migration.md`
- **Dépendances :** T-030, T-031
- **Phases estimées :** RED 30 min ; GREEN 60–90 min ; REFACTOR 30 min ; SIMPLIFY 15 min.
- **Portes :** contrat S-008, couverture 57/57, traçabilité 286/286, toutes les suites Python, validation des skills, markdownlint, `git diff --check`, CI source.
- **Retour arrière :** annuler la PR d'audit ; les opérations externes restent inadmissibles.
- **Notes :** T-032 réconcilie T-029 comme candidat local `done` seulement parce que PR #58 et CI 2/2 vertes le prouvent. Elle consigne explicitement `merge_gate: external-explicit-go-pending`, PR ouverte et aucune publication.

### T-033 : Préparer GitHub CLI et mettre à jour le profil VPS

- **Origine qualifiée :** `spring-architect:T-033`
- **Classe d'autorité :** `EXTERNE BLOQUÉE` — go explicite et credentials d'exploitation requis.
- **AC-IDs :** AC-161, AC-162, AC-164, AC-165, AC-166, AC-167, AC-168, AC-240, AC-264
- **Test-IDs :**
  - T-033-T1 (admission — refuse si le profil 0.9.0 n'est pas fusionné, publié et gate verte)
  - T-033-T2 (GitHub CLI — installation Debian officielle, device/web flow SSH et scopes exacts)
  - T-033-T3 (secret — aucun token n'est fourni au prompt ou à une preuve)
  - T-033-T4 (SSH — batch, identité unique, clé hôte stricte et cible exacte)
  - T-033-T5 (versions — versions avant/après et test de la version installée)
  - T-033-T6 (preuve — résultat expurgé, sans transcript ni chemin absolu)
- **Files in scope :**
  - `.specs/2026-07-31-hermes-parallel-sdd/jobs/T-033/001-vps-prerequisites.json`
  - `.specs/2026-07-31-hermes-parallel-sdd/jobs/T-033/002-profile-version.json`
  - `hermes/scripts/test_sdd_s008_contract.py`
- **Dépendances :** T-032 et preuve externe que la PR #58 est fusionnée et 0.9.0 publiée
- **Phases estimées :** admission 30 min ; exécution 60–120 min ; vérification et expurgation 30 min.
- **Portes :** explicit-go, credentials, release-gate, gh-auth-status, installed-version, redaction ; une seule gate lourde.
- **Retour arrière :** restaurer 0.9.0 et conserver toutes les preuves ; ne supprimer aucun état ou worktree.
- **Notes :** rester `pending` tant que le go ou les credentials manquent. Aucune review humaine n'est demandée.
- **Résultat :** `done` ; SHA : `a96e3b28085262eeb27795f58b1b217d770ea485`.

### T-034 : Préparer les clones, Issues, projets et boards

- **Origine qualifiée :** `spring-architect:T-034`
- **Classe d'autorité :** `EXTERNE BLOQUÉE` — go explicite et session GitHub/VPS requise.
- **AC-IDs :** AC-008, AC-178, AC-179, AC-180, AC-182, AC-238, AC-239, AC-241, AC-242
- **Test-IDs :**
  - T-034-T1 (admission — GitHub auth et version VPS prouvées)
  - T-034-T2 (issues — Issues actif sur Super Lily)
  - T-034-T3 (clones — deux clones propres avant création ou réutilisation)
  - T-034-T4 (boards — slugs et workdirs par défaut exacts)
  - T-034-T5 (projects — clones principaux exacts et isolés)
  - T-034-T6 (idempotence — inspecte et réutilise board/projet existants)
- **Files in scope :**
  - `.specs/2026-07-31-hermes-parallel-sdd/jobs/T-034/001-clones.json`
  - `.specs/2026-07-31-hermes-parallel-sdd/jobs/T-034/002-boards.json`
- **Dépendances :** T-033
- **Phases estimées :** admission 15 min ; inspection 45–60 min ; création ou réutilisation 60–90 min ; preuves 30 min.
- **Portes :** explicit-go, repo-clean, issues-enabled, board-isolation, project-workdir, idempotence.
- **Retour arrière :** conserver les clones propres ; ne retirer qu'une ressource nouvellement créée et vide, jamais une ressource existante ou contenant du travail.
- **Notes :** les chemins VPS attendus ne sont conservés dans les preuves que sous forme de labels relatifs expurgés.
- **Résultat :** `done` ; SHA : `332ac1837074b9c7c8a3c04945245723318957b4`.

### T-035 : Valider deux jobs sandbox réels

- **Origine qualifiée :** `spring-architect:T-035`
- **Classe d'autorité :** `EXTERNE BLOQUÉE` — go explicite requis pour le dispatch réel.
- **AC-IDs :** AC-184, AC-185, AC-186, AC-229, AC-230, AC-265
- **Test-IDs :**
  - T-035-T1 (admission — dry-run T-031 rejoué et boards T-034 valides)
  - T-035-T2 (dispatch — exactement deux jobs au maximum)
  - T-035-T3 (monitoring — cartes assignées à `staaack` suivies)
  - T-035-T4 (diagnostics — statistiques et diagnostics JSON consultés)
  - T-035-T5 (ressources — aucune OOM et une seule gate lourde active)
  - T-035-T6 (conservation — zéro travail perdu, worktree/log/journal conservés en échec)
- **Files in scope :**
  - `.specs/2026-07-31-hermes-parallel-sdd/jobs/T-035/001-sandbox-dispatch.json`
  - `.specs/2026-07-31-hermes-parallel-sdd/jobs/T-035/002-sandbox-diagnostics.json`
- **Dépendances :** T-034
- **Phases estimées :** admission et dry-run 30 min ; dispatch 60–120 min ; diagnostics et preuve 60 min.
- **Portes :** explicit-go, max-two-writers, max-one-heavy-gate, both-jobs-green, no-oom, no-loss.
- **Retour arrière :** arrêter le dispatch sans archiver les cartes ni supprimer branches, worktrees, logs ou journaux.
- **Notes :** les writers peuvent se chevaucher ; leurs gates lourdes restent sérialisées. Le gateway permanent reste interdit pendant toute la tâche.
- **Résultat :** `done` ; SHA : `0a9089bcf330c58524e941d090671d0636b1a011`.

### T-036 : Installer le gateway utilisateur

- **Origine qualifiée :** `spring-architect:T-036`
- **Classe d'autorité :** `EXTERNE BLOQUÉE` — go explicite requis.
- **AC-IDs :** AC-188, AC-189
- **Test-IDs :**
  - T-036-T1 (admission — deux jobs sandbox verts et preuves T-035 intactes)
  - T-036-T2 (installation — gateway utilisateur, démarrage immédiat et au login)
  - T-036-T3 (statut — statut utilisateur vérifié sans `sudo`)
  - T-036-T4 (négatif — aucun service ou gateway système)
- **Files in scope :**
  - `.specs/2026-07-31-hermes-parallel-sdd/jobs/T-036/001-user-gateway.json`
- **Dépendances :** T-035
- **Phases estimées :** admission 15 min ; installation 30–45 min ; statut et preuves 30 min.
- **Portes :** explicit-go, sandbox-gate, user-scope-only, status, redaction.
- **Retour arrière :** arrêter et désinstaller uniquement le gateway utilisateur ; préserver le profil, les boards et les preuves sandbox.

### T-037 : Exécuter le pilote Super Lily onboard→ship

- **Origine qualifiée :** `spring-architect:T-037`
- **Classe d'autorité :** `EXTERNE BLOQUÉE` — go explicite, accès Super Lily et gateway utilisateur sain requis.
- **AC-IDs :** AC-220, AC-221, AC-222, AC-223, AC-224, AC-269, AC-270, AC-271
- **Test-IDs :**
  - T-037-T1 (onboard — le pilote commence par l'onboarding réel)
  - T-037-T2 (parallèle — backend et frontend disjoints se chevauchent, pic deux)
  - T-037-T3 (dépendance — la troisième tâche attend la fusion de sa dépendance)
  - T-037-T4 (GitHub — une issue et une PR propres par tâche)
  - T-037-T5 (validate — phase terminée sans déploiement)
  - T-037-T6 (review — rapport terminé sans reviewer humain ni déploiement)
  - T-037-T7 (ship — plan terminé sans exécuter de déploiement)
  - T-037-T8 (rétention — les tâches non fusionnées ou en échec ne sont ni archivées ni supprimées)
- **Files in scope :**
  - `.specs/2026-07-31-hermes-parallel-sdd/jobs/T-037/001-pilot-lifecycle.json`
  - `.specs/2026-07-31-hermes-parallel-sdd/jobs/T-037/002-pilot-resource-proof.json`
- **Dépendances :** T-036
- **Phases estimées :** admission 30 min ; onboard et plan 45 min ; jobs 90–120 min ; validate/review/ship et preuve 60 min.
- **Portes :** explicit-go, lifecycle-order, overlap, dependency, per-task-issue-pr, no-deploy, no-loss, redaction ; une seule gate lourde.
- **Retour arrière :** arrêter le pilote, conserver toutes les ressources non fusionnées et désactiver le gateway utilisateur si sa santé est en cause.
- **Notes :** `/sdd-review` est une commande d'audit automatique ; aucune personne n'est sollicitée pour reviewer.

### T-038 : Publier le profil 1.0.0

- **Origine qualifiée :** `spring-architect:T-038`
- **Classe d'autorité :** `EXTERNE BLOQUÉE` — go explicite distinct requis après le pilote.
- **AC-IDs :** AC-160
- **Test-IDs :**
  - T-038-T1 (RED release — 1.0.0 refusée tant qu'une preuve pilote manque)
  - T-038-T2 (distribution — version 1.0.0 et précédent 0.9.0 cohérents)
  - T-038-T3 (gate — 57/57 S-008, 286/286 Epic, parité, tests, contrats et CI verts)
  - T-038-T4 (pilot-gate — onboard, parallèle, dépendance, validate, review et ship prouvés)
  - T-038-T5 (publication — fusion et publication uniquement après go explicite)
  - T-038-T6 (rollback — 0.9.0 réinstallable sans perte de preuve)
- **Files in scope :**
  - `scripts/test_validate_distribution.py`
  - `scripts/test_sdd_s008_contract.py`
  - `distribution.yaml`
  - `CHANGELOG.md`
  - `README.md`
  - `.github/workflows/ci.yml`
  - `.specs/2026-07-31-hermes-parallel-sdd/jobs/T-038/001-release-1.0.0.json`
- **Dépendances :** T-037
- **Phases estimées :** RED 30 min ; GREEN 60–90 min ; validation 60 min ; fusion/publication après go 30 min.
- **Portes :** explicit-go, pilot-complete, parity, profile-tests,
  distribution, frontmatter, markdownlint, CI, automated-audit-clear,
  rollback-proof.
- **Retour arrière :** fermer la PR avant fusion ; après publication, restaurer 0.9.0 sans supprimer les preuves du pilote.
- **Notes :** la tâche reste `pending` même si tous les tests locaux sont verts tant que le go de publication n'est pas explicite. Aucun reviewer humain n'est demandé.

### S-008 Primary AC Coverage Matrix

| Producteur primaire | AC-IDs |
|---|---|
| T-030 | AC-163, AC-169, AC-175–AC-177, AC-181, AC-187, AC-190–AC-194, AC-266–AC-268 |
| T-031 | AC-170–AC-174, AC-183 |
| T-032 | AC-232 |
| T-033 | AC-161, AC-162, AC-164–AC-168, AC-240, AC-264 |
| T-034 | AC-008, AC-178–AC-180, AC-182, AC-238, AC-239, AC-241, AC-242 |
| T-035 | AC-184–AC-186, AC-229, AC-230, AC-265 |
| T-036 | AC-188, AC-189 |
| T-037 | AC-220–AC-224, AC-269–AC-271 |
| T-038 | AC-160 |

La matrice contient exactement 57 critères uniques. T-030 à T-032 produisent
les contrats et audits locaux ; T-033 à T-038 produisent les faits externes
uniquement après autorisation.

### S-008 Dependency and Capacity Validation

```text
T-029 candidat local
  ├─> T-030 ─┐
  └─> T-031 ─┴─> T-032
                    └─[go + credentials + 0.9.0 fusionnée/publiée]─> T-033
                         -> T-034 -> T-035 -> T-036 -> T-037
                         -> [go de publication] -> T-038
```

- Le graphe est acyclique.
- T-030 et T-031 ont des scopes disjoints et occupent au plus deux slots.
- T-032 est l'unique writer de l'audit partagé.
- T-033 à T-038 sont séquentielles ; une seule gate lourde est active.
- Les deux jobs de T-035 et les deux writers du pilote peuvent se chevaucher,
  mais leur capacité reste 2 et leurs gates lourdes sont sérialisées.
- Une instruction de poursuite locale ne satisfait aucune barrière externe.

### S-008 Open Questions

- (aucune)

### S-008 Resolved Questions

- **Décision autonome — T-029 :** PR #58 ouverte, commit `e4e6bc4` et CI 2/2
  verte permettent `done` pour le candidat local seulement ;
  `merge_gate: external-explicit-go-pending` et `published: false` restent vrais.
- **Décision autonome — autorité externe :** aucune opération VPS, GitHub,
  gateway, pilote, fusion ou publication n'est implicitement autorisée.
- **Décision autonome — revue :** aucun reviewer humain n'est sollicité ; les
  audits automatiques restent des commandes produit, jamais des demandes à une personne.
- **Décision autonome — progression externe :** T-033 ajoute le contrat
  `test_sdd_s008_contract.py` à son périmètre afin que T-032-T4 accepte le
  préfixe séquentiel des tâches externes déjà terminées et, au plus, la tâche
  active. Toutes les tâches suivantes doivent rester `pending` et
  `external-blocked`; le DAG et les barrières d'autorité ne sont pas affaiblis.

### S-008 Sign-off

- [x] `high_water_mark: 38`; aucun identifiant antérieur n'est réutilisé.
- [x] Les 57 AC ont un producteur primaire unique.
- [x] Chaque tâche possède Test-IDs, scopes littéraux, dépendances, portes et rollback.
- [x] Le DAG respecte deux writers maximum et une gate lourde.
- [x] Toutes les tâches externes restent pending derrière une barrière explicite.
- [x] Aucune question ouverte ni ADR supplémentaire.

Première vague locale : `/sdd-build 2026-07-31-hermes-parallel-sdd --parallel`
admet T-030 et T-031. T-033 et les suivantes restent inadmissibles sans go
explicite et sans leurs preuves externes.
