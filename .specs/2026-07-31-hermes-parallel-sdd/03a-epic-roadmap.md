# Feuille de route Epic : 2026-07-31-hermes-parallel-sdd

> Responsable : `spring-architect` · Phase 3a (mode Epic)
>
> La roadmap ordonne les capacités publiables. Elle ne détaille pas encore les
> tâches TDD de `04-tasks.md`.

## Inputs

- Révision de `03-epic-design.md` : brouillon du 2026-07-31 fondé sur
  `01-spec.md` SHA-256
  `71fd818b8d9e30931ac5203bd3099ec5ecceb6475461b4d494e72674f640a7b6`.
- Revue de spécification : `approve`, 286 AC, zéro échec et zéro question.
- Socle de départ : `main` à `06ee632`, CI Hermes fusionnée par la pull request
  #49 ; profil VPS initial 0.4.7 ; runner E2E actuel arrêté au plan.

## Execution Snapshot — 2026-08-01

| Tranche | État observé | Conditions de sortie restantes |
|---|---|---|
| S-001 / 0.4.8 | En cours | La PR source [#62](https://github.com/staaack-io/specs-driven-development/pull/62) est prête, `MERGEABLE/CLEAN` et ses deux checks sont verts, mais aucune review n'est consignée. L'issue profil [#45](https://github.com/staaack-io/hermes-agent-profile-staaack/issues/45) est ouverte ; aucune PR profil ni version 0.4.8 n'existe. |
| S-002 / 0.5.0 | Partiellement fusionnée en source | Runtime v2 [#61](https://github.com/staaack-io/specs-driven-development/pull/61), `/sdd-epic-plan` [#57](https://github.com/staaack-io/specs-driven-development/pull/57) et `/sdd-wire-harness` [#59](https://github.com/staaack-io/specs-driven-development/pull/59) sont sur `origin/main` à `a5815b1`. Le pont Kanban–GitHub, l'enrichissement de `/sdd-status`, l'audit des 84 AC et le profil 0.5.0 manquent. |
| S-003 / 0.6.0 | Non commencée | `/sdd-build` mono-tâche, puis orchestrateur parallèle et fan-in. |
| S-004 / 0.6.1 | Non commencée | `/sdd-code-simplify` et publication après 0.6.0. |
| S-005 / 0.7.0 | Non commencée | `/sdd-test`, puis `/sdd-validate`. |
| S-006 / 0.8.0 | Non commencée | `/sdd-review`, puis `/sdd-ship`. |
| S-007 / 0.9.0 | Non commencée | E2E complet onboard→ship, parallélisme, dépendance et reprise injectée. |
| S-008 / 1.0.0 | Non commencée | Sandbox VPS, gateway utilisateur et pilote Super Lily sans déploiement. |

Le profil publié reste exactement en **0.4.7** avec cinq skills : `sdd-help`,
`sdd-plan`, `sdd-spec`, `sdd-spec-review` et `sdd-status`. Le dépôt source en
contient huit ; `sdd-onboard`, `sdd-epic-plan` et `sdd-wire-harness` ne sont
donc pas encore distribués.

## Roadmap / Reality Reconciliation

- La roadmap historique part de `06ee632` puis `3eef5b5`; le nouveau point de
  référence source est `a5815b1`, avant la PR #62.
- S-002 a avancé avant la sortie de S-001. Le code déjà fusionné reste acquis,
  mais le train de publication demeure bloqué à 0.4.7.
- Le séquencement interne connu de S-002 est valide : le contrat runtime v2 a
  été fusionné avant `/sdd-epic-plan` et `/sdd-wire-harness`.
- Les tâches détaillées actuelles couvrent S-001 seulement. Avant tout nouveau
  writer S-002, un architecte consolide les preuves des 84 AC et ne crée des
  tâches que pour les écarts réels.
- Le runtime v2 valide état, DAG, périmètres, leases, CAS, reprise et fan-in ;
  il ne remplace pas le pont Hermes Kanban–GitHub et ne lance aucun job.
- Les nouvelles règles locales rendent les audits Codex `$validate` et
  `$review` facultatifs. Elles ne retirent pas les commandes Hermes
  `/sdd-validate` et `/sdd-review` des tranches S-005 et S-006. Si cette
  suppression devient souhaitée, la spécification doit être révisée avant ces
  tranches.

## Recovery Execution Waves

Toutes les vagues respectent deux writers maximum, trois analyses en lecture
seule maximum, un écrivain des artefacts partagés et une seule gate lourde à la
fois.

| Vague | Writer A | Writer B | Gate et critère de sortie |
|---|---|---|---|
| G-000 | — | — | Obtenir la review de #62, traiter ses fils, recevoir le go explicite et fusionner. |
| W-001 | Profil 0.4.8 depuis l'issue #45 : copie exacte onboard, version, changelog, tests et parité. | Réconciliation S-002 : matrice des 84 AC, conception détaillée et tâches limitées aux écarts. | CI profil, review, zéro fil actionnable, go, fusion et publication 0.4.8. |
| W-002 | Pont Hermes Kanban–GitHub : issue, carte, branche, worktree, session, draft PR, polling et reprise. | `/sdd-status` enrichi et corrections d'audit seulement si les fichiers sont disjoints. | PR source fusionnées après leurs gates ; fan-in par un writer unique. |
| G-002 | Profil 0.5.0 : runtime et skills S-002 ayant satisfait la parité. | — | CI, review, zéro fil, go, fusion et publication 0.5.0. |
| W-003 | `/sdd-build` mono-tâche avec RED→GREEN→REFACTOR→SIMPLIFY. | — | Socle mono-tâche fusionné avant toute orchestration parallèle. |
| W-004 | `/sdd-build --parallel`, admission et fan-in. | `/sdd-code-simplify`. | Fusion et publication 0.6.0 avant 0.6.1. |
| W-005 | `/sdd-test`. | `/sdd-validate`. | Développement parallèle autorisé, fusion de test avant validate, gates lourdes sérialisées, profil 0.7.0. |
| W-006 | `/sdd-review`. | `/sdd-ship`. | Développement parallèle autorisé, fusion de review avant ship, profil 0.8.0. |
| W-007 | Runner E2E onboard→ship dans un dossier supprimable. | Analyses en lecture seule seulement. | Chevauchement de deux tâches, dépendance, échec injecté, reprise et profil 0.9.0. |
| W-008 | Préparation et pilote VPS/Super Lily. | Deuxième job sandbox seulement après dry-run valide. | Deux jobs maximum, zéro OOM ou perte, gateway utilisateur, pilote réel puis 1.0.0. |

Le chemin critique actualisé est :

```text
#62 review/go/merge
  -> profil 0.4.8
  -> audit S-002 + bridge + status
  -> profil 0.5.0
  -> build mono
  -> build parallèle / 0.6.0
  -> code-simplify / 0.6.1
  -> test puis validate / 0.7.0
  -> review puis ship / 0.8.0
  -> E2E / 0.9.0
  -> sandbox VPS + pilote Super Lily / 1.0.0
```

## Slice Strategy

- Une tranche correspond à une version installable et à un résultat visible de
  bout en bout, de 0.4.8 à 1.0.0.
- Les PR indépendantes d'une même tranche peuvent progresser en parallèle
  uniquement après fusion de leur contrat commun. Leur ordre de fusion suit le
  DAG ci-dessous, jamais leur date de fin de développement.
- Toute fusion attend la gate de publication et un go humain. Toute vague attend
  la fusion de son fan-in avant la suivante.
- La couverture primaire affecte chaque AC à une seule tranche afin de prouver
  exhaustivement 286/286 critères ; les contraintes transverses restent
  applicables aux tranches ultérieures même lorsqu'elles ne sont comptées qu'une
  fois.

## Slice Backlog

| Tranche | Résultat visible | Couverture primaire | Nombre d'AC | Dépendances | Jalon |
|---|---|---|---:|---|---|
| S-001 | CI obligatoire, PR #47 intégrée et `/sdd-onboard` publié avec parité | AC-009–AC-010, AC-081–AC-100, AC-195, AC-237, AC-250–AC-251, AC-272–AC-275, AC-281–AC-286 | 36 | CI des deux dépôts ; checks/review/fils/go de #47 | 0.4.8 |
| S-002 | Runtime v2 reprenable, pont Kanban–GitHub, `/sdd-epic-plan` et `/sdd-wire-harness` | AC-001–AC-007, AC-011–AC-012, AC-025–AC-026, AC-048–AC-080, AC-101–AC-123, AC-243–AC-249, AC-252–AC-256, AC-276–AC-280 | 84 | S-001 ; contrat runtime avant les trois PR de capacité | 0.5.0 |
| S-003 | `/sdd-build` mono-tâche puis parallèle avec jobs isolés et fan-in | AC-013, AC-019–AC-024, AC-027–AC-047, AC-124–AC-138, AC-231, AC-233–AC-234, AC-236, AC-257–AC-260 | 51 | S-002 ; mono-tâche avant orchestrateur parallèle | 0.6.0 |
| S-004 | `/sdd-code-simplify` publié | AC-014, AC-139 | 2 | Socle mono-tâche de S-003 ; publication après 0.6.0 | 0.6.1 |
| S-005 | `/sdd-test` et `/sdd-validate` testent et consolident sans écriture concurrente | AC-015–AC-016, AC-140–AC-147, AC-196–AC-217 | 32 | S-002 pour le harness ; S-003/S-004 pour le cycle complet ; test avant validate | 0.7.0 |
| S-006 | `/sdd-review` produit un rapport unique et `/sdd-ship` prépare sans déployer | AC-017–AC-018, AC-148–AC-154, AC-235, AC-261–AC-263 | 13 | S-005 ; review avant ship | 0.8.0 |
| S-007 | Candidat complet prouvé localement par le runner E2E onboard→ship | AC-155–AC-159, AC-218–AC-219, AC-225–AC-228 | 11 | S-006 et toutes les commandes publiées | 0.9.0 |
| S-008 | Profil stable validé sur le VPS et pilote Super Lily réussi | AC-008, AC-160–AC-194, AC-220–AC-224, AC-229–AC-230, AC-232, AC-238–AC-242, AC-264–AC-271 | 57 | S-007 ; profil validé avant mise à jour ; sandbox avant gateway | 1.0.0 |

Total de couverture primaire : **286 AC**, sans trou ni doublon.

## Dependency Graph

```text
CI SDD fusionnée (#49) ─┐
CI profil indépendante ─┴─> PR #47 + main + checks + review + fils + go
                           └─> S-001 / profil 0.4.8
                                  |
                                  v
                        contrat runtime v2
                         /        |        \
                pont Kanban   epic-plan   wire-harness
                         \        |        /
                          resync + fusions
                                  |
                                  v
                            S-002 / 0.5.0
                                  |
                                  v
                         build mono-tâche
                           /             \
                  build parallèle     code-simplify
                        |                  |
                  S-003 / 0.6.0      S-004 / 0.6.1
                           \             /
                            v           v
                           test  ----> validate
                                  |
                            S-005 / 0.7.0
                                  |
                         review ----> ship
                                  |
                            S-006 / 0.8.0
                                  |
                           E2E onboard→ship
                                  |
                            S-007 / 0.9.0
                                  |
                    VPS sandbox + pilote Super Lily
                                  |
                            S-008 / 1.0.0
```

Dans chaque vague de build :

```text
jobs admissibles (2 writers maximum)
  -> PR de tâche + checks + review
  -> attente du go humain
  -> fusion de toutes les PR de tâche
  -> synthesizer unique
  -> PR de fan-in
  -> attente du go humain et fusion
  -> vague suivante
```

## Critical Path and Exact Constraints

Le temps n'est pas principalement lié à la génération des fichiers ; il est
contraint par les barrières suivantes :

- **8 jalons de publication séquentiels** : 0.4.8, 0.5.0, 0.6.0, 0.6.1,
  0.7.0, 0.8.0, 0.9.0 et 1.0.0.
- **286 critères** à prouver : 36 + 84 + 51 + 2 + 32 + 13 + 11 + 57 par
  tranche.
- **2 writers maximum** : une troisième tâche d'écriture attend même si elle
  est prête. Les analyses en lecture seule sont plafonnées séparément à 3.
- **1 gate lourde maximum** : Maven, Next, PIT et OWASP ne se chevauchent pas
  sur le VPS.
- **1 écrivain des artefacts partagés** : chaque vague attend que toutes ses PR
  de tâche soient fusionnées, puis qu'une PR de fan-in soit produite et fusionnée.
- **5 conditions par gate de publication** : CI, tests, contrats, review
  `approve` et zéro fil actionnable.
- **Review de la PR #47** : attente minimale de 5 minutes après la demande avant
  lecture des fils ; toute correction déclenche une nouvelle attente de review.
- **Polling des PR de job** : checks, reviews et fils toutes les 5 minutes ;
  passage à `needs_input` après 30 minutes sans review.
- **Budget d'un job** : 45 minutes maximum par tentative et 2 nouvelles
  tentatives au plus, soit au plus 3 tentatives. Si chaque tentative atteint le
  plafond, cela représente 135 minutes de temps d'exécution de job, hors review,
  fusion et fan-in.
- **2 jobs sandbox parallèles** doivent chacun satisfaire la gate avant
  installation du gateway permanent.

Une durée calendrier totale exacte ne peut pas être déduite sans inventer le
temps des checks, des corrections, des reviews et des go humains. La roadmap
rend en revanche explicites tous les plafonds et attentes chiffrés de la
spécification.

## Per-slice Delivery Notes

### S-001 — 0.4.8

- Entrée : CI indépendante dans les deux dépôts ; CI SDD déjà fusionnée sur
  `main` à `06ee632`.
- Séquence : resynchroniser #47 avec `main`, attendre ses checks, demander la
  review Codex, attendre au moins cinq minutes, traiter chaque fil dans sa
  filiation, obtenir la nouvelle review si correction, puis utiliser le go déjà
  consigné uniquement lorsque toutes les autres gardes sont vertes.
- Sortie : #47 fusionnée, PR de profil 0.4.8 séparée, `/sdd-onboard`, changelog,
  parité sans différence et mêmes tests dans source et profil.
- Risque : confondre le go existant avec une dérogation aux checks ou à la
  review ; les AC-272 à AC-275 et AC-285 restent bloquants.

### S-002 — 0.5.0

- Entrée : S-001 publiée ; état v1 préservé.
- Séquence : fusionner d'abord le contrat runtime (schéma v2, journaux, gardes,
  reprise), puis développer le pont Kanban–GitHub, `/sdd-epic-plan` et
  `/sdd-wire-harness` dans trois PR distinctes ; après le contrat, resynchroniser
  chacune avec `main` et les fusionner dans n'importe quel ordre autorisé.
- Sortie : état lisible v1/v2 et écrit v2, commandes publiées, bridge traçable,
  dry-run du harness et intégration atomique.
- Risque : incohérence entre carte, issue et état ; la clé d'idempotence et le
  stockage croisé des identifiants sont des critères de sortie.

### S-003 — 0.6.0

- Entrée : runtime et bridge de S-002.
- Séquence : livrer d'abord le build mono-tâche et ses preuves, puis développer
  l'orchestrateur parallèle ; limiter l'admission aux dépendances fusionnées et
  aux périmètres disjoints.
- Sortie : deux writers au plus, cycle RED→GREEN→REFACTOR→SIMPLIFY, PR par
  tâche, go explicite, cartes `done` et fan-in transactionnel.
- Risque : un worker écrit un artefact partagé ; seul son journal local est
  autorisé hors fichiers de tâche.

### S-004 — 0.6.1

- Entrée : le socle mono-tâche permet son développement en parallèle du build
  parallèle, mais la publication suit 0.6.0.
- Sortie : `/sdd-code-simplify` fusionné et gate de publication satisfaite.
- Risque : couplage implicite au fan-in ; la conception détaillée devra nommer
  les fichiers et tests sans étendre le comportement spécifié.

### S-005 — 0.7.0

- Entrée : `/sdd-wire-harness` disponible et contrat de phase figé.
- Séquence : développer `/sdd-test` et `/sdd-validate` en parallèle ; fusionner
  `/sdd-test` avant `/sdd-validate` ; sérialiser les gates lourdes.
- Sortie : tests unitaires, tests de parallélisme, GitHub et transactionnels
  prouvent DAG, conflits, CAS, verrous, reprise, idempotence et écrivain unique.
- Risque : validate écrit avant les fan-in spécialisés ; il attend et n'écrit
  que les rapports communs.

### S-006 — 0.8.0

- Entrée : fixtures et validation de S-005 disponibles.
- Séquence : développer review et ship en parallèle, puis fusionner review avant
  ship.
- Sortie : lectures spécialisées consolidées en un rapport ; ship prépare
  retour arrière, observabilité, flags et notes sans déployer.
- Risque : assimiler préparation et déploiement ; toute action de déploiement
  reste interdite.

### S-007 — 0.9.0

- Entrée : toutes les commandes 0.4.8 à 0.8.0 publiées.
- Séquence : étendre le runner actuel, aujourd'hui limité au plan, jusqu'au
  ship ; prouver le chevauchement backend/frontend, l'attente d'une dépendance
  et la reprise après échec injecté dans un dossier supprimable.
- Sortie : candidat complet 0.9.0 satisfaisant la gate.
- Risque : test vert mais travail ou preuves perdus ; la conservation doit être
  explicitement vérifiée.

### S-008 — 1.0.0

- Entrée : candidat 0.9.0 validé, GitHub Issues actif sur Super Lily, GitHub CLI
  installé et authentifié sur le VPS, clones propres et boards isolés.
- Séquence : configurer les limites, exécuter dry-run puis dispatch réel à deux
  jobs, valider deux jobs sandbox avant le gateway utilisateur, puis effectuer
  le parcours réel Super Lily de l'onboarding au ship.
- Sortie : parallélisme prouvé, dépendance respectée, reprise cohérente, zéro OOM
  et zéro travail perdu ; review, validation et ship se terminent sans déployer.
- Risque : mise à jour prématurée du VPS ; seule une version fusionnée et ayant
  satisfait la gate peut être installée.

## Rollout and Risk Strategy

- Aucun feature flag de migration n'est ajouté. La stratégie approuvée est une
  compatibilité de données : lecture v1/v2, écriture v2 et état v2 restant
  lisible par le profil précédent.
- Chaque version est fusionnée, validée et publiée avant sa mise à jour VPS.
  L'exploitation relève la version avant et après installation et teste la
  version installée.
- Le rollback rétablit la version précédente du profil. Il ne supprime ni ne
  reconvertit les états, journaux, logs, worktrees ou branches.
- Déclencheurs de rollback : échec d'une condition de publication découvert
  après installation, état v2 illisible par le profil précédent, incohérence
  transactionnelle, perte de travail, OOM ou incapacité de reprendre un job.
- Le gateway permanent reste bloqué avant deux jobs sandbox parallèles validés ;
  il est ensuite installé au niveau utilisateur seulement.

## Open Questions

- (aucune)

## Resolved Questions

- Les décisions `Q-001` à `Q-010` de `01-spec.md` sont intégrées dans la
  conception et la stratégie de rollout ; aucune question Epic supplémentaire
  n'a été découverte.

## Sign-off

- [x] L'ordre des tranches a été validé avec l'utilisateur le 2026-08-01
  (instruction : « Continue à migrer »).
- [x] Les dépendances ont été revues par `spring-architect`.
- [x] Les questions ouvertes au niveau Epic sont résolues ou différées.
