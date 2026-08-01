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

- **high_water_mark :** 3
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
