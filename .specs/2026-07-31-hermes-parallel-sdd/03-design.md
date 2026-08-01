# Conception détaillée : S-001 — profil 0.4.8

> Responsable : `spring-architect` · Phase 3b · Tranche Epic : `S-001`
>
> Cette tranche porte uniquement sur la distribution d'un CLI et de skills
> Python pour Hermes. Spring, OpenAPI, base de données, frontend et ArchUnit
> sont explicitement sans objet conformément à `Q-006`.

## Inputs

- Révision de `01-spec.md` : SHA-256
  `71fd818b8d9e30931ac5203bd3099ec5ecceb6475461b4d494e72674f640a7b6`.
- Révision de `02-spec-review.md` : SHA-256
  `c64ffd8f8af312a50da04a066ee47874a310654753630224a5184a8d5a0e50f2` ;
  verdict `approve`, zéro question ouverte.
- Révision de `03-epic-design.md` : SHA-256
  `f17fced20d9a0f3dc1c9c82732d1a6cb1cb755ebcf52cf06696d9b552c82430b` ;
  architecture Epic approuvée par l'utilisateur le 2026-08-01.
- Révision de `03a-epic-roadmap.md` : SHA-256
  `920f8cf3b64d933a79852c8888ead2fb084cd5f68fb0bd6a801c2b7134c3e8af` ;
  ordre des tranches approuvé par l'utilisateur le 2026-08-01.
- Couverture primaire de S-001 : 36 AC, soit `AC-009`, `AC-010`,
  `AC-081` à `AC-100`, `AC-195`, `AC-237`, `AC-250`, `AC-251`,
  `AC-272` à `AC-275` et `AC-281` à `AC-286`.

### Inputs from detect-stack.sh

L'exécution de `.github/scripts/detect-stack.sh` retourne :

```json
{"error":"pom.xml introuvable","searched":"pom.xml"}
```

Ce résultat est attendu et non bloquant : la topologie applicative Spring ou
frontend est sans objet pour ce framework Python/Hermes selon `Q-006`.

| Élément de stack | Résultat S-001 |
|---|---|
| Outil de build Java | N/A |
| Java / Spring Boot | N/A |
| Base de données / migration | N/A |
| Testcontainers | N/A |
| Runtime concerné | Python 3.11 dans les deux CI ; profil Hermes |
| Dépôts concernés | `staaack-io/specs-driven-development`, `staaack-io/hermes-agent-profile-staaack` |

## Architecture Overview

La tranche publie dans le profil Hermes 0.4.8 le skill canonique
`hermes/skills/sdd-onboard` déjà fusionné dans le dépôt source par la pull
request #47. La publication reste une pull request séparée dans le dépôt de
profil : elle copie l'arborescence vers `skills/sdd-onboard`, conserve les
skills existants, met à jour la version et le changelog, puis démontre la
parité et l'exécution des mêmes tests. Les deux CI autonomes restent les
preuves de dépôt ; la parité entre dépôts est une gate locale explicite. La
fusion et toute mise à jour du VPS restent bloquées jusqu'aux checks, tests,
contrats, review `approve`, absence de fil actionnable et go humain.

La première preuve de publication révèle un défaut de portabilité du contrat
canonique : `test_skill_contract.py` calcule actuellement la racine avec
`SKILL_ROOT.parents[2]`. Après copie exacte dans `profile/skills/sdd-onboard`,
ce calcul remonte hors du dépôt et cherche `docs/artifact-contract.md` et
`docs/codex-migration.md`, absents de la distribution. Le RED observé est
objectif : le garde réussit 15 tests sur 15, tandis que le contrat distribué
produit 3 réussites et 2 erreurs. T-001 corrige d'abord la source canonique
sans affaiblir les assertions, puis recopie exactement le skill dans le profil.

État de départ vérifié pour la conception :

- `origin/main` du dépôt source contient la fusion #47 à `3eef5b5` et les
  quinze fichiers de `hermes/skills/sdd-onboard` ;
- le profil sur `main` déclare encore `version: 0.4.7` dans
  `distribution.yaml` et ne publie pas encore `skills/sdd-onboard` ;
- la CI du profil expose les checks stables `Skills / Python tests` et
  `Distribution / Validate, docs and diff`, et exécute `git diff --check` ;
- la CI source expose `Hermes tests and skill contracts` et
  `Documentation and diff`.

## ADRs

Aucun nouvel ADR n'est nécessaire pour S-001. La séparation source/profil, la
gate humaine et l'absence d'auto-merge sont imposées par la spécification et la
conception Epic. Les ADR Epic existants restent applicables sans nouvelle
décision locale.

## Component Map

| Frontière | Composant | Responsabilité S-001 | AC principaux |
|---|---|---|---|
| Source canonique | `hermes/skills/sdd-onboard` | Fournir un skill autonome, ses références, modèles, garde et tests portables à copier exactement | AC-009, AC-010, AC-096, AC-098, AC-099 |
| Régression de disposition | `hermes/scripts/test_sdd_onboard_profile_contract.py` | Reproduire une disposition `profile/skills/...` et exécuter le contrat distribué | AC-098, AC-099 |
| Distribution | `skills/sdd-onboard` | Publier `/sdd-onboard` sans modifier les commandes déjà présentes | AC-009, AC-010, AC-095, AC-096 |
| Métadonnées | `distribution.yaml`, `CHANGELOG.md`, `README.md` | Déclarer et documenter la version 0.4.8 | AC-097, AC-251 |
| Tests du skill | `skills/sdd-onboard/scripts/test_onboarding_guard.py`, `skills/sdd-onboard/scripts/test_skill_contract.py` | Rejouer dans le profil les tests copiés depuis la source | AC-082, AC-099, AC-282 |
| Validation du profil | `scripts/validate_distribution.py`, `scripts/test_validate_distribution.py` | Valider manifeste, frontmatters, références, Markdown et contrat de release | AC-082 à AC-086, AC-250, AC-286 |
| CI source | `.github/workflows/hermes-ci.yml` | Prouver tests Python, contrats, frontmatters, Markdown et diff côté source | AC-081 à AC-086, AC-195, AC-237, AC-250 |
| CI profil | `.github/workflows/ci.yml` | Prouver les mêmes catégories côté profil avec des noms de checks stables | AC-081 à AC-086, AC-195, AC-237, AC-250, AC-281, AC-282, AC-286 |
| Gate GitHub | PR #47 et future PR profil 0.4.8 | Conserver les preuves de checks, review, fils, go et fusion séparée | AC-087 à AC-095, AC-100, AC-272 à AC-275, AC-281 à AC-285 |

## Module Boundaries

- **Dépôt source** — `hermes/skills/sdd-onboard` est la source canonique. T-001
  peut modifier uniquement son contrat de test portable et ajouter le test de
  régression de disposition ; tous les autres fichiers source restent en
  lecture seule.
- **Dépôt profil** — `skills/sdd-onboard` est une copie publiée exacte ; les
  autres dossiers sous `skills/` restent présents et inchangés.
- **CI autonomes** — chaque dépôt exécute sa propre CI sans cloner l'autre ni
  partager de secret. La comparaison inter-dépôts est lancée explicitement
  depuis deux checkouts locaux.
- **Gate humaine** — GitHub porte les checks, reviews et fils ; aucun composant
  de S-001 ne fusionne automatiquement une pull request et aucune tâche ne met
  à jour le VPS.

Les dépendances s'orientent dans un seul sens pour la publication :

```text
source canonique fusionnée (#47)
  -> RED dans une disposition profile/skills simulée
  -> contrat source indépendant des docs hors distribution
  -> copie exacte du skill corrigé dans le profil
  -> tests + version + changelog
  -> parité inter-dépôts + CI profil
  -> review approve + zéro fil actionnable + go humain
  -> fusion de la PR profil 0.4.8
```

## Entity Relationship Model

N/A. S-001 ne crée ni entité métier ni persistance applicative. Les relations
de livraison sont uniquement : une source canonique vers une copie publiée,
une version 0.4.8 vers un changelog, et une pull request de profil séparée après
la fusion de la pull request source #47.

## OpenAPI Sketch

N/A. Aucun endpoint HTTP n'est ajouté ou modifié.

## Data Model + Migrations

- Tables ou collections touchées : aucune.
- Outil de migration : N/A ; `detect-stack.sh` ne trouve pas de projet Maven et
  S-001 ne contient aucune persistance applicative.
- Fichiers de migration : aucun.
- Réversibilité : retour au profil publié précédent ; aucune donnée ni schéma
  n'est modifié par S-001.

## Security Posture

- Authentification applicative : N/A.
- Autorisation applicative : N/A.
- Données personnelles : aucune donnée personnelle n'est traitée par la
  publication 0.4.8.
- Secrets : aucun secret n'est ajouté au profil ni aux workflows ; chaque CI
  reste autonome avec `permissions: contents: read`.
- Déploiement : interdit dans S-001 ; la mise à jour du VPS reste bloquée avant
  revue, autorisation et fusion de la PR profil.

## Test Strategy

1. Ajouter côté source
   `hermes/scripts/test_sdd_onboard_profile_contract.py`. Ce test copie les
   skills dans une disposition temporaire littérale `profile/skills/...`, puis
   exécute le contrat distribué. Sur l'état courant, il reproduit les 3
   réussites et 2 erreurs dues aux deux chemins `docs/` absents : RED.
2. Rendre `hermes/skills/sdd-onboard/scripts/test_skill_contract.py`
   indépendant de la racine du dépôt source. Le contrat conserve ses
   assertions en lisant uniquement les références du skill et les surfaces
   distribuées communes `sdd-help` et `sdd-status`.
3. Copier exactement l'arborescence corrigée `hermes/skills/sdd-onboard` vers
   `skills/sdd-onboard`, puis exécuter dans le profil les 15 tests du garde,
   les 5 tests du contrat, la découverte complète et la parité sans différence.
4. Ajouter à la suite existante du validateur de distribution le contrat de
   release 0.4.8 ; il échoue sur le manifeste et le changelog 0.4.7 avant leur
   mise à jour, ce qui constitue RED pour T-002.
5. Relancer les tests Python, contrats, frontmatters, Markdownlint et
   `git diff --check` dans la PR profil.
6. T-003 est une gate de livraison sans écriture de production : elle vérifie
   les preuves GitHub historiques de #47 et les preuves courantes de la PR
   profil avant toute fusion.

## Detailed AC Traceability

| Groupe | AC couverts | Composants / tâches |
|---|---|---|
| Commandes et publication onboard | AC-009, AC-010, AC-095, AC-096, AC-098, AC-099 | Distribution, tests du skill, T-001 |
| CI et métadonnées de release | AC-081 à AC-086, AC-097, AC-195, AC-237, AC-250, AC-251, AC-281, AC-282, AC-286 | Métadonnées, validation, CI des deux dépôts, T-002 |
| Cycle de fusion et gate humaine | AC-087 à AC-094, AC-100, AC-272 à AC-275, AC-283 à AC-285 | Gate GitHub, T-003 |

La réunion de ces trois lignes contient exactement les 36 AC affectés à S-001
dans `03a-epic-roadmap.md`, sans AC d'une tranche ultérieure.

## Risks + Rollback

| Risque | Probabilité | Impact | Réduction du risque | Retour arrière |
|---|---|---|---|---|
| Copie incomplète ou modifiée du skill | moyenne | `/sdd-onboard` diverge de la source | copie de l'arborescence complète, tests copiés, comparaison sans différence | fermer la PR profil sans fusion ; le profil reste en 0.4.7 |
| Contrat dépendant de fichiers hors distribution | constatée | tests verts en source mais erreurs dans le profil | test source dans une disposition `profile/skills/...` et assertions limitées aux surfaces distribuées communes | rétablir le contrat source et fermer la PR profil ; conserver 0.4.7 |
| Régression d'une commande existante | faible | workflow SDD installé incomplet | conserver les dossiers existants et exécuter la découverte complète des tests | retirer uniquement les changements 0.4.8 avant fusion |
| Version ou changelog incohérent | moyenne | distribution non traçable | test de contrat de release puis validateur de distribution | rétablir `distribution.yaml`, `README.md` et `CHANGELOG.md` dans la PR |
| Confondre CI verte et parité inter-dépôts | moyenne | profil valide isolément mais différent de la source | exécuter explicitement `check_profile_parity.py` avec les deux checkouts | bloquer la gate et corriger la copie |
| Fusion avant review ou fil résolu | faible | violation de la gate humaine | T-003 vérifie les cinq conditions et le go avant fusion | ne pas fusionner ; poursuivre sur la même branche de PR |
| Mise à jour prématurée du VPS | faible | profil non validé installé | AC-100 bloque toute mise à jour avant revue, autorisation et fusion | conserver la version 0.4.7 installée |

## Non-Functional Requirements

- Parité exacte, sans différence, entre la source et le profil pour les skills
  publiés.
- Checks CI aux noms stables et obligatoires avant fusion.
- Attente minimale de cinq minutes après la demande de review Codex de #47
  avant lecture des fils.
- Gate de publication composée de CI, tests, contrats, review `approve` et zéro
  fil actionnable.

Aucun SLO de performance n'est spécifié pour S-001 ; aucune optimisation ni
mesure de performance n'est planifiée.

## Open Questions

- (aucune)

## Resolved Questions

- `Q-006` : Spring et frontend sont non applicables au framework
  CLI/skills Python/Hermes.
- Les décisions `Q-001` à `Q-010` restent celles de `01-spec.md` ; S-001
  n'introduit aucune décision supplémentaire.

## Design Review

- [x] Carte des composants CLI/skills/CI présente ; composants Spring N/A.
- [x] Frontières des deux dépôts et sens de publication documentés ; ArchUnit N/A.
- [x] OpenAPI, modèle relationnel et migrations explicitement N/A.
- [x] Sécurité, secrets et absence de déploiement traités dans le périmètre.
- [x] Chaque risque possède une réduction et un retour arrière.
- [x] Chaque décision non évidente réutilise la conception Epic ; aucun ADR local manquant.
- [x] Aucun comportement absent de `01-spec.md` n'est introduit.
- [x] Les 36 AC de S-001 sont couverts exactement.
- [x] Aucune question ouverte ne subsiste.

## Sign-off

- [x] Chaque AC de S-001 est couvert par au moins un composant et une tâche.
- [x] Toutes les `Q-NNN` sont résolues.
- [x] Revue de conception interne effectuée par `spring-architect` le 2026-08-01.
- [x] Poursuite de la migration autorisée par l'utilisateur le 2026-08-01
  (instruction : « Continue à migrer »).

## Conception détaillée : S-002 — socle parallèle et profil 0.5.0

> Responsable : `spring-architect` · Phase 3b · Tranche Epic : `S-002`
>
> Cette section s'ajoute à la conception S-001 ci-dessus sans la remplacer.
> Les capacités déjà fusionnées sont des preuves de référence ; seules les
> lacunes observées deviennent de nouvelles tâches.

### S-002 Inputs

- Révision de `01-spec.md` : SHA-256
  `71fd818b8d9e30931ac5203bd3099ec5ecceb6475461b4d494e72674f640a7b6`.
- Révision de `02-spec-review.md` : SHA-256
  `c64ffd8f8af312a50da04a066ee47874a310654753630224a5184a8d5a0e50f2` ;
  verdict `approve`, 286 AC conformes et aucune question ouverte.
- Révision de `03-epic-design.md` : SHA-256
  `f17fced20d9a0f3dc1c9c82732d1a6cb1cb755ebcf52cf06696d9b552c82430b`.
- Révision de `03a-epic-roadmap.md` : SHA-256
  `5bfd79d95e74cee8ae5fedd9e12345214ca040df819bad1b502a4ea15fcee7d1`.
- Point de référence : `origin/main` à `9607aae`, après les fusions #61,
  #57, #59 et #62.
- Couverture primaire de S-002 : exactement 84 AC, soit `AC-001` à
  `AC-007`, `AC-011`, `AC-012`, `AC-025`, `AC-026`, `AC-048` à `AC-080`,
  `AC-101` à `AC-123`, `AC-243` à `AC-249`, `AC-252` à `AC-256` et
  `AC-276` à `AC-280`.

#### S-002 Inputs from detect-stack.sh

L'exécution de `.github/scripts/detect-stack.sh` retourne :

```json
{"error":"pom.xml introuvable","searched":"pom.xml"}
```

Ce résultat confirme que Spring, OpenAPI, base de données, migration,
Testcontainers, frontend et ArchUnit restent sans objet pour cette tranche
Python/Hermes, conformément à `Q-006`.

### S-002 Reality Baseline

| Preuve fusionnée | SHA de merge | Surface observée | Tests présents | Statut de planification |
|---|---|---|---:|---|
| Contrat runtime v2, PR #61 | `257ce11` | État v1/v2, DAG, Test-IDs, scopes, leases, journaux locaux, empreintes, CAS, reprise et fan-in | 30 tests runtime, plus tests du garde de plan | baseline, aucune tâche rétrospective |
| `/sdd-epic-plan`, PR #57 | `d583bb5` | Délégations internes en lecture seule, verdict Hermes `approve`, promotion atomique | 19 tests de garde et 6 contrats | baseline, aucune tâche rétrospective |
| `/sdd-wire-harness`, PR #59 | `a5815b1` | Dry-run sans écriture, writer unique, verrou commun, gates séquentielles et rollback transactionnel | 20 tests de garde | baseline, aucune tâche rétrospective |
| GitHub Issues du dépôt source | observation du 2026-08-01 | `hasIssuesEnabled: true` pour `staaack-io/specs-driven-development` | preuve GitHub en lecture seule | AC-007 satisfaite |

Les merges prouvent aussi l'ordre historique requis : la PR #61 précède les
PR #57 et #59 ; les branches de #57 et #59 ont chacune intégré `origin/main` avant leur
merge. Le bridge restant devra reproduire cette resynchronisation avant sa
fusion pour terminer AC-106, AC-121 et AC-122.

### S-002 Architecture Overview

S-002 conserve le Kanban natif Hermes comme unique ordonnanceur durable. Un
bridge Python sans boucle d'ordonnancement traduit les transitions d'un job
admis par Hermes vers `gh` et répercute les identifiants GitHub dans la carte
et l'état SDD ; il n'admet ni ne fusionne lui-même une tâche. Le runtime v2
fusionné reste l'autorité déterministe pour les contrats d'état, les leases,
les journaux task-local, les empreintes et le fan-in. `/sdd-status` devient une
vue strictement en lecture seule de la carte et des champs task-local. Un fan-in
source unique exécute ensuite le contrat exhaustif des 84 AC avant que le profil
0.5.0 copie les skills et le runtime partagé, valide leur parité et publie la
version.

### S-002 ADRs

Aucun nouvel ADR n'est requis. Les décisions non évidentes sont déjà
acceptées :

- [ADR-001](adr/001-use-hermes-kanban.md) — Kanban Hermes, sans second
  ordonnanceur Python ;
- [ADR-002](adr/002-bound-parallel-capacity.md) — deux writers, trois analyses
  et une gate lourde ;
- [ADR-003](adr/003-isolate-each-job.md) — enveloppe GitHub/Hermes par job ;
- [ADR-004](adr/004-use-single-writer-fan-in.md) — fan-in à writer unique ;
- [ADR-005](adr/005-migrate-state-with-dual-read.md) — lecture v1/v2 et
  écriture v2 compatible.

### S-002 Component Map

| Frontière | Composant | Responsabilité S-002 | État |
|---|---|---|---|
| Runtime partagé | `hermes/runtime/sdd_runtime_guard.py` | Valider état, DAG, scopes, leases, journaux, RED, CAS, empreintes et fan-in | fusionné #61 |
| Bridge interne | `hermes/runtime/sdd_github_bridge.py` | Appeler `gh`, mettre à jour carte et état, suivre checks/reviews/fils sans fusionner | à créer, T-004 |
| Vue utilisateur | `hermes/skills/sdd-status` | Afficher carte, issue, branche, PR, checks, review, blocage et prochaine action | à enrichir, T-005 |
| Portabilité | `sdd-plan` et parité runtime | Faire fonctionner l'import runtime dans les dispositions source et profil | écart audité, T-006 |
| Fan-in source | contrat S-002 | Rejouer la preuve agrégée des 84 AC après bridge et status | à créer, T-007 |
| Distribution | profil Hermes 0.5.0 | Copier skills et runtime, exécuter les mêmes tests, versionner et conserver le rollback 0.4.8 | à publier, T-008 |

### S-002 Module Boundaries

- `hermes/runtime/sdd_runtime_guard.py` reste indépendant de GitHub et ne
  lance aucun job. Le bridge l'appelle ; le runtime n'importe pas le bridge.
- `hermes/runtime/sdd_github_bridge.py` consomme des adaptateurs Hermes et `gh`
  explicites. Il ne contient ni ordonnanceur, ni auto-merge, ni secret.
- `hermes/skills/sdd-status` lit l'état et les sorties structurées ; il
  n'appelle aucune commande mutante et ne répare aucun artefact.
- Les workers continuent d'écrire uniquement leurs fichiers en scope et leur
  journal local. Seul le synthesizer runtime publie les artefacts partagés.
- La distribution copie les skills sous `skills/` et le runtime partagé sous
  `hermes/runtime/`. La parité couvre les deux surfaces avant publication.

Deux writers seulement sont admissibles dans la première vague :

```text
T-004 bridge (hermes/runtime/sdd_github_bridge.*) ─┐
                                                    ├─> T-007 fan-in source
T-005 status (hermes/skills/sdd-status/**) ──────┘
                       T-006 portabilité ───────────┘
                                                     -> T-008 profil 0.5.0
```

Les chemins exacts, sans glob, sont déclarés dans `04-tasks.md`. Le schéma
ci-dessus abrège seulement les familles de fichiers pour la lecture.

### S-002 Interaction Model

1. Hermes admet une tâche après validation runtime et obtention du lease.
2. Le bridge crée avec `gh` l'issue enfant, la branche et la PR brouillon, puis
   stocke les identifiants dans la carte et l'état v2 via les gardes existants.
3. Après tests verts, le bridge rend la PR prête. Il consulte checks, reviews
   et fils toutes les cinq minutes ; une correction reste sur la même branche
   et déclenche une nouvelle attente de review.
4. Sans review après trente minutes, la carte passe à `needs_input`. Le bridge
   ne fusionne jamais la PR.
5. `/sdd-status` affiche pour chaque tâche les champs consolidés et sa prochaine
   action sans écrire.
6. Après les merges autorisés, T-007 exécute le fan-in source et le contrat
   exhaustif ; T-008 publie ensuite le profil 0.5.0.

### S-002 Entity Relationship Model

S-002 ne crée aucune entité persistée par une application. Le modèle
conceptuel de l'Epic reste applicable : une feature possède plusieurs tâches ;
une tâche possède au plus une carte, une issue, une branche, un worktree, une
session et une PR ; une vague agrège une ou deux tâches et possède au plus un
fan-in. Les identifiants externes sont des champs de l'état v2, pas une base de
données supplémentaire.

### S-002 OpenAPI Sketch

N/A. Aucun endpoint HTTP n'est ajouté ou modifié.

### S-002 Data Model + Migrations

- Tables ou collections touchées : aucune.
- Outil de migration applicatif : N/A.
- Migration de fichier : lecture des états v1 et v2, écriture d'un candidat
  v2 par le runtime fusionné ; l'état actif n'est jamais remplacé
  silencieusement.
- Réversibilité : réinstaller le profil 0.4.8 ; ne supprimer ni état,
  journal, branche, worktree ou preuve.

### S-002 Security Posture

- Authentification applicative et autorisation HTTP : N/A.
- Authentification GitHub : contexte `gh` existant ; aucun token n'est ajouté
  à l'état, aux logs ou au profil.
- Données sensibles : les logs du bridge excluent secrets, tokens, données
  personnelles, chemins absolus et contenu métier.
- Commandes externes : arguments structurés, sans shell composé ; aucune
  commande `gh pr merge` n'est autorisée.
- Déploiement et mise à jour VPS : hors S-002.

### S-002 Detailed AC Reconciliation

| Groupe S-002 | Nombre | Preuve fusionnée | Écart et couverture planifiée |
|---|---:|---|---|
| AC-001–AC-007 | 7 | Runtime sans lancement de job, délégations internes, plafonds et Issues activées | T-004 termine l'usage Kanban sans ordonnanceur ; T-007 audite les sept AC |
| AC-011–AC-012 | 2 | Skills source fusionnés par #57 et #59 | T-008 les publie dans le profil 0.5.0 |
| AC-025–AC-026 | 2 | Aucun `sdd-roles` ; rôles embarqués dans epic-plan et wire-harness | T-007 audite, T-008 conserve les références |
| AC-048–AC-080 | 33 | AC-048–AC-079 : runtime #61 ; AC-080 : verrou et gates #59 | T-006 corrige la portabilité profil ; T-007 rejoue le contrat |
| AC-101–AC-123 | 23 | AC-101–AC-105 : #61 ; AC-107 : #57 ; AC-108–AC-109 : #59 | T-004 couvre AC-106 et AC-110–AC-122 ; T-008 couvre AC-123 |
| AC-243–AC-249 | 7 | Le skill status existe mais n'affiche pas encore les champs task-local | T-005 couvre les sept champs |
| AC-252–AC-256 | 5 | AC-252 : garde DAG #61 | T-004 couvre les identifiants PR et le polling reviews/fils |
| AC-276–AC-280 | 5 | AC-276, AC-277, AC-279 et AC-280 : migration #61 | T-006 prouve la disposition profil ; T-008 couvre le rollback AC-278 |

Total : **84/84 AC S-002**, sans doublon avec la couverture primaire de S-001
et sans AC orphelin. T-007 est le contrat de fan-in qui relie chaque preuve
fusionnée ou nouvel écart à un test exécutable ; il ne réimplémente pas les
capacités de #61, #57 ou #59.

### S-002 Audit Finding: Profile Runtime Layout

Le code fusionné de `sdd-plan` calcule aujourd'hui sa racine d'import avec
`Path(__file__).resolve().parents[4]`, chemin correct sous
`hermes/skills/sdd-plan/scripts/` mais extérieur au dépôt sous
`skills/sdd-plan/scripts/`. La copie exacte du skill ne suffit donc pas à
charger `hermes.runtime.sdd_runtime_guard` dans le profil. T-006 doit d'abord
reproduire ce RED dans une disposition profil temporaire, puis rendre la
résolution explicite et tester la parité de `hermes/runtime`. Aucun autre
correctif des capacités fusionnées n'est planifié sans nouvel échec prouvé.

### S-002 Risks + Rollback

| Risque | Probabilité | Impact | Réduction du risque | Retour arrière |
|---|---|---|---|---|
| Bridge devenu ordonnanceur concurrent | moyenne | Deux sources de vérité | API de transition sans boucle d'admission ; contrat interdit tout scheduler Python | retirer T-004 ; le runtime fusionné reste passif |
| Carte, issue et état divergent après crash | moyenne | Reprise ambiguë | clé d'idempotence, écriture croisée des IDs et CAS runtime | rejouer la même transition ; ne supprimer aucun objet |
| Polling duplique une correction ou une réponse | moyenne | Review incohérente | curseur/idempotence par fil et même branche | mettre la carte `needs_input`, conserver la PR |
| Status écrit en voulant réparer | faible | Violation du writer unique | garde de lecture seule et tests d'empreinte | retirer T-005 ; conserver l'ancien status |
| Runtime vert en source mais absent du profil | constatée | `/sdd-plan` installé casse | test de disposition profil et parité runtime dans T-006/T-008 | conserver le profil 0.4.8 |
| Publication 0.5.0 avant fan-in complet | faible | Distribution partielle | dépendance T-008 sur T-007 et contrat 84/84 | fermer la PR profil ; conserver 0.4.8 |

### S-002 Non-Functional Requirements

- Deux writers maximum et une gate lourde maximum, conformément aux AC de
  S-002 ; trois analyses internes au plus.
- Polling GitHub toutes les cinq minutes et passage `needs_input` après trente
  minutes sans review.
- Parité exacte des skills et du runtime distribués.
- Reprise idempotente sans secret, transcript ni chemin absolu dans l'état ou
  les journaux versionnés.

Aucun autre SLO de performance n'est spécifié ; aucune optimisation n'est
introduite.

### S-002 Open Questions

- (aucune)

### S-002 Resolved Questions

- Les décisions `Q-001` à `Q-010` de `01-spec.md` et les cinq ADR acceptés
  fournissent toutes les décisions nécessaires.
- Le bridge est une surface runtime interne, pas une nouvelle commande
  utilisateur ni un second ordonnanceur.

### S-002 Design Review

- [x] Carte des composants Python/Hermes et frontières source/profil présentes.
- [x] Spring, OpenAPI, relations persistées, migrations et ArchUnit explicitement N/A.
- [x] Posture GitHub, secrets, logs et interdiction d'auto-merge documentées.
- [x] Les preuves de #61, #57 et #59 sont des baselines, pas du travail recréé.
- [x] Les cinq nouvelles tâches ciblent uniquement audit ou écarts observés.
- [x] Les deux writers de la première vague ont des fichiers concrets disjoints.
- [x] Les 84 AC de S-002 sont réconciliés sans orphelin.
- [x] Aucun nouveau comportement absent de `01-spec.md` n'est introduit.
- [x] Aucun nouvel ADR n'est requis et aucune question ouverte ne subsiste.

### S-002 Sign-off

- [x] Chaque AC S-002 est relié à une preuve fusionnée ou à une tâche.
- [x] Les tâches S-001 et leur couverture restent inchangées.
- [x] Checklist `design-review.md` relue le 2026-08-01.
- [x] Exécution de la migration autorisée par l'utilisateur le 2026-08-01
  (instruction : « ok go »).
