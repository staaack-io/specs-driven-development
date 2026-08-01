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

- **high_water_mark :** 8
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
