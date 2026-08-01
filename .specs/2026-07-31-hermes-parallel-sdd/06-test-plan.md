# Plan de test : 2026-07-31-hermes-parallel-sdd — S-001 profil 0.4.8

> Responsable : `spring-test-engineer` · Phase 5 · Tranche Epic : `S-001` · Modèle : `.codex/templates/test-plan.template.md`
>
> Ce plan décrit les preuves déjà consignées pour T-001 et T-002 et les
> preuves externes encore attendues pour T-003. Il ne vaut pas rapport de
> validation globale et ne transforme aucune gate non exécutée en succès.

## Inputs

- `01-spec.md` : révision SHA-256
  `71fd818b8d9e30931ac5203bd3099ec5ecceb6475461b4d494e72674f640a7b6`,
  36 AC affectés à S-001.
- `03-design.md` : conception S-001 approuvée le 2026-08-01.
- `04-tasks.md`, `05-implementation-log.md` et `.tdd-state.json` : état de
  travail non commité observé le 2026-08-01 ; T-001 et T-002 sont `done`,
  T-003 est `pending`.
- Stack : CLI/skills Python 3.11 et profil Hermes. Testcontainers, Spring,
  OpenAPI, base de données, JaCoCo, PIT et ArchUnit sont N/A conformément à
  `Q-006`.
- Candidat profil local :
  `/private/tmp/hermes-s001.n66XgC/profile-build`.

## Test inventory

| Test-ID | Type et preuve | Fichier ou surface | AC-IDs | Tâche | Statut |
|---|---|---|---|---|---|
| T-001-T1 | Régression de disposition `profile/skills/...` ; 1/1 après RED attendu | `hermes/scripts/test_sdd_onboard_profile_contract.py` | AC-098, AC-099 | T-001 | **green local** |
| T-001-T2 | Contrat source ; 5/5 | `hermes/skills/sdd-onboard/scripts/test_skill_contract.py` | AC-009, AC-010, AC-099 | T-001 | **green local** |
| T-001-T3 | Garde 15/15 et contrat 5/5 dans le profil | `skills/sdd-onboard/scripts/test_onboarding_guard.py`, `skills/sdd-onboard/scripts/test_skill_contract.py` | AC-010, AC-096, AC-099 | T-001 | **green local** |
| T-001-T4 | Comparaison source/profil sans différence, 41 fichiers | `hermes/scripts/check_profile_parity.py` | AC-096, AC-098 | T-001 | **green local** |
| T-001-T5 | Quatre suites directes : 15 + 5 + 14 + 8 = 42/42 | `skills/*/scripts/test_*.py` du candidat profil | AC-009, AC-010 | T-001 | **green direct ; runner global non prouvé** |
| T-002-T1 | Contrat de release ciblé ; 1/1 | `scripts/test_validate_distribution.py::DistributionValidatorTest::test_release_0_4_8_metadata_is_consistent` | AC-097, AC-251 | T-002 | **green local ciblé** |
| T-002-T2 | Validateur complet du manifeste, de l'arborescence, des frontmatters et références | `scripts/validate_distribution.py`, `scripts/test_validate_distribution.py` | AC-082, AC-083, AC-086, AC-286 | T-002 | **non exécuté globalement** |
| T-002-T3 | Markdownlint et contrôle du diff | `.markdownlint-cli2.yaml`, diff de PR | AC-084, AC-250 | T-002 | **partiel : `git diff --check` green ; Markdownlint non prouvé** |
| T-002-T4 | Présence des deux workflows et stabilité des noms de checks | `.github/workflows/hermes-ci.yml`, `.github/workflows/ci.yml` | AC-081, AC-085, AC-237 | T-002 | **inspection de conception seulement ; gate CI non exécutée** |
| T-002-T5 | Tests Python et contrats dans les deux dépôts | CI source et CI profil | AC-082, AC-195, AC-281, AC-282, AC-286 | T-002 | **pending externe** |
| T-003-T1 | Preuves historiques de #47 : checks, review lue avec filiation, corrections et go | PR source #47 | AC-087 à AC-094, AC-272 à AC-275, AC-285 | T-003 | **pending dans l'état SDD** |
| T-003-T2 | PR profil 0.4.8 distincte de #47 | issue profil #45 puis PR du dépôt profil | AC-095 | T-003 | **issue créée ; PR pending** |
| T-003-T3 | CI, tests et contrats verts de la PR profil | Checks de la PR profil | AC-100 | T-003 | **pending externe** |
| T-003-T4 | Review `approve` et zéro fil actionnable | Review et fils de la PR profil | AC-283, AC-284 | T-003 | **pending externe** |
| T-003-T5 | Go humain obtenu après toutes les autres preuves | Instruction humaine attachée à la PR profil | AC-094, AC-100 | T-003 | **pending externe** |
| T-003-T6 | Absence de mise à jour VPS avant revue, autorisation et fusion | Version VPS et état de la PR profil | AC-100 | T-003 | **pending externe** |

### Méthodes locales directement exécutées

- `SddOnboardProfileContractTest.test_distributed_contract_runs_from_profile_skills_layout` : 1 test.
- `SkillContractTest` : 5 méthodes, toutes exécutées côté source puis profil.
- `OnboardingGuardTest` : 15 méthodes exécutées côté source puis profil.
- Total source T-001 : **21/21** (1 disposition + 15 garde + 5 contrat).
- `TddStateGuardTest` : 14 méthodes exécutées directement dans le candidat profil.
- `ReviewDecisionGuardTest` : 8 méthodes exécutées directement dans le candidat profil.
- `DistributionValidatorTest.test_release_0_4_8_metadata_is_consistent` :
  seul test de la suite de distribution exécuté avec succès ; les 158 autres
  méthodes de cette suite n'ont pas été validées dans cette exécution.

## Commands and observed evidence

| Périmètre | Commande consignée | Résultat observé |
|---|---|---|
| Disposition profil | `PYTHONDONTWRITEBYTECODE=1 python3 hermes/scripts/test_sdd_onboard_profile_contract.py` | 1/1 green après le RED attendu |
| Garde source | `PYTHONDONTWRITEBYTECODE=1 python3 hermes/skills/sdd-onboard/scripts/test_onboarding_guard.py` | 15/15 green |
| Contrat source | `PYTHONDONTWRITEBYTECODE=1 python3 hermes/skills/sdd-onboard/scripts/test_skill_contract.py` | 5/5 green |
| Garde profil | `PYTHONDONTWRITEBYTECODE=1 python3 skills/sdd-onboard/scripts/test_onboarding_guard.py` | 15/15 green |
| Contrat profil | `PYTHONDONTWRITEBYTECODE=1 python3 skills/sdd-onboard/scripts/test_skill_contract.py` | 5/5 green |
| Parité | `PYTHONDONTWRITEBYTECODE=1 python3 hermes/scripts/check_profile_parity.py /private/tmp/hermes-s001.n66XgC/profile-build` | 41 fichiers identiques |
| Découverte supervisée | `PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_skill_tests.py` | échec d'environnement après 15 tests green : impossible d'énumérer les descendants |
| Release ciblée | `python3 -m unittest scripts.test_validate_distribution.DistributionValidatorTest.test_release_0_4_8_metadata_is_consistent` avec stub d'import temporaire hors dépôt | 1/1 green ; ne prouve pas le validateur global |
| Diff source/profil | `git diff --check` | green local |
| Markdownlint | `npx` interrompu après 60 secondes sans sortie dans l'environnement sans réseau | aucun résultat revendiqué |

## AC coverage for S-001

La tranche contient exactement 36 AC : `AC-009`, `AC-010`, `AC-081` à
`AC-100`, `AC-195`, `AC-237`, `AC-250`, `AC-251`, `AC-272` à `AC-275` et
`AC-281` à `AC-286`.

- **Preuves locales acquises :** AC-009, AC-010, AC-096 à AC-099 et AC-251
  disposent d'au moins une preuve locale verte ciblée. La preuve d'AC-097 est
  limitée au test ciblé et au chargement YAML local.
- **Preuves seulement partielles :** AC-082 à AC-086, AC-195, AC-237,
  AC-250, AC-281, AC-282 et AC-286 attendent tout ou partie des gates globales
  distribution, Markdown ou CI.
- **Preuves externes non acquises dans l'état SDD :** AC-087 à AC-095,
  AC-100, AC-272 à AC-275 et AC-283 à AC-285 dépendent de T-003.

Aucun AC de S-001 n'est orphelin dans `04-tasks.md`, mais la couverture par des
tests ou gates **réussis** n'est pas complète tant que T-003 et les gates
globales n'ont pas produit leurs preuves.

## Cross-cutting suites

### Architecture, Spring et intégration

- ArchUnit : N/A ; aucun bytecode Java ni frontière Spring dans S-001.
- JUnit 5 et Testcontainers : N/A ; aucun service Spring, base ou broker.
- OpenAPI : N/A ; aucun endpoint HTTP.
- Smoke test applicatif : N/A ; la surface est une distribution de skills et
  ses contrôles pertinents sont les contrats Python, la parité et la CI.

### Coverage and mutation

- JaCoCo : N/A ; aucun code JVM.
- PIT : N/A ; aucun code JVM et aucune configuration PIT applicable.
- Aucun seuil de couverture Python n'est défini dans la spécification S-001 ;
  aucun pourcentage n'est inventé.
- Aucun test génératif n'est ajouté : les comportements S-001 sont des contrats
  de disposition, de métadonnées, de parité et de gate, couverts par des cas
  déterministes.

## Test integrity review

- Aucun test ou assertion n'a été supprimé dans le diff S-001 observé.
- Le contrat onboard conserve ses 5 méthodes. Les deux lectures non portables
  hors distribution sont remplacées par quatre assertions sur les surfaces
  réellement distribuées `sdd-help` et `sdd-status` ; aucune assertion n'est
  neutralisée.
- T-002 ajoute un test de release avec trois assertions sans modifier les tests
  historiques.
- Aucun `skip`, `skipTest`, `@Disabled` ou marqueur équivalent n'est ajouté par
  S-001 dans les tests modifiés.
- La suite historique `test_validate_distribution.py` contient deux
  `skipUnless` et deux `skipTest` conditionnels à la disponibilité des liens
  symboliques. Ils préexistent au changement S-001 et ne sont pas comptés
  comme preuve verte dans ce plan.
- Aucun seuil de qualité n'a été abaissé et aucune dépendance n'a été ajoutée.

## Gaps + waivers

- **GAP-001 — T-003 et gates CI externes non exécutées.** L'issue profil
  [#45](https://github.com/staaack-io/hermes-agent-profile-staaack/issues/45)
  existe, mais la PR profil, ses
  checks obligatoires, ses tests/contrats CI, la review `approve`, le contrôle
  des fils actionnables, le go humain et le blocage VPS n'ont aucune preuve
  consignée dans `.tdd-state.json`. **Statut : ouvert, bloquant.** Fermeture :
  exécuter T-003 et attacher les preuves GitHub sans auto-merge.
- **GAP-002 — gates globales locales non exécutables.** Les 42 tests directs
  sont verts, mais `scripts/run_skill_tests.py` échoue dans la supervision avec
  `cannot enumerate test descendants`. Le validateur complet requiert
  `markdown-it-py 4.2.0`, absent localement, et Markdownlint n'a pas abouti
  sans réseau. **Statut : ouvert.** Fermeture : exécuter le runner, la suite de
  distribution et Markdownlint dans la CI équipée des dépendances épinglées,
  sans convertir les échecs ou absences de résultat actuels en succès.
- **Waivers :** aucun. Les éléments Spring/Testcontainers/OpenAPI/JaCoCo/PIT
  sont N/A par décision `Q-006`, et non dérogés par une waiver.

## Sign-off

- [x] Les 36 AC de S-001 sont affectés à un Test-ID ou une gate dans l'inventaire.
- [x] Aucun test S-001 n'est ignoré ou affaibli par le changement observé.
- [x] Les preuves locales sont distinguées des preuves CI/GitHub externes.
- [ ] Chaque AC possède une preuve réussie.
- [ ] Le validateur de distribution, Markdownlint et le runner global réussissent.
- [ ] T-003 est terminé : CI/tests/contrats verts, review `approve`, zéro fil actionnable et go humain.

## Verdict

**FAIL — plan complet, sign-off S-001 bloqué par GAP-001 et GAP-002.**

T-001 et le test ciblé de T-002 disposent de preuves locales vertes, mais la
tranche ne satisfait pas encore la gate de validation de publication. Aucune
fusion de la PR profil ni mise à jour du VPS ne peut être déduite de ce plan.
