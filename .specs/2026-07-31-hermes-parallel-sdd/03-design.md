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

## Conception détaillée : S-003 — `/sdd-build` mono-tâche et parallèle, profil 0.6.0

> Responsable : `spring-architect` · Phase 3b · Tranche Epic : `S-003`
>
> Cet addendum préserve intégralement les conceptions S-001 et S-002. Il porte
> exclusivement sur les 51 AC affectés à S-003 par la roadmap approuvée.

### S-003 Inputs

- Source de tranche : issue GitHub
  [#74](https://github.com/staaack-io/specs-driven-development/issues/74),
  `Plan S-003: publish /sdd-build sequential and parallel in profile 0.6.0`,
  ouverte et relue le 2026-08-03.
- Révision de `01-spec.md` : SHA-256
  `71fd818b8d9e30931ac5203bd3099ec5ecceb6475461b4d494e72674f640a7b6`.
- Révision de `02-spec-review.md` : SHA-256
  `c64ffd8f8af312a50da04a066ee47874a310654753630224a5184a8d5a0e50f2` ;
  verdict `approve`, 286 AC conformes et zéro question ouverte.
- Révision de `03-epic-design.md` : SHA-256
  `f17fced20d9a0f3dc1c9c82732d1a6cb1cb755ebcf52cf06696d9b552c82430b`.
- Révision de `03a-epic-roadmap.md` lue avant cet addendum : SHA-256
  `5bfd79d95e74cee8ae5fedd9e12345214ca040df819bad1b502a4ea15fcee7d1`.
- Baseline source : `main` à `0f5932a`, après achèvement de S-002 et de
  T-008 ; runtime v2, bridge Kanban–GitHub, `/sdd-status`,
  `/sdd-epic-plan`, `/sdd-wire-harness` et profil 0.5.0 disponibles.
- Couverture primaire S-003 : exactement `AC-013`, `AC-019` à `AC-024`,
  `AC-027` à `AC-047`, `AC-124` à `AC-138`, `AC-231`, `AC-233`,
  `AC-234`, `AC-236` et `AC-257` à `AC-260`, soit **51 AC**.

#### S-003 Inputs from detect-stack.sh

L'exécution de `.github/scripts/detect-stack.sh` retourne :

```json
{"error":"pom.xml introuvable","searched":"pom.xml"}
```

Ce résultat confirme que Spring Boot, OpenAPI, base de données, outil de
migration, Testcontainers, frontend applicatif et ArchUnit sont sans objet
pour le produit modifié. `/sdd-build` doit néanmoins sélectionner des rôles
embarqués Spring ou React/Next.js à partir des preuves de stack du projet
cible, sans déduire la stack de ce dépôt Python/Hermes.

### S-003 Architecture Overview

S-003 introduit une seule commande publique, `/sdd-build`, avec deux chemins
d'exécution. Le chemin `/sdd-build <feature-id> <T-NNN>` est livré et fusionné
en premier. Il orchestre dans un même job les rôles test-engineer puis
implementer adaptés à la stack, tout en gardant l'agent principal responsable
des portes et de l'ordre RED → GREEN → REFACTOR → SIMPLIFY. Les rôles ne
reçoivent que le contrat de tâche et un workspace borné ; ils n'accèdent jamais
directement aux artefacts partagés. Le garde principal conserve dans le journal
local les Test-IDs, commandes structurées, sorties expurgées et fichiers
concernés.

Après fusion du socle mono-tâche, `/sdd-build <feature-id> --parallel
[--max-workers 1|2]` utilise exclusivement le Kanban Hermes et les primitives
du runtime v2. L'orchestrateur calcule une vague contenant toutes les tâches
`pending`/`ready` admissibles dont les dépendances sont `done`/`done`, refuse
les périmètres en conflit et laisse le Kanban activer au plus deux leases
disjoints à la fois. Pour chaque tâche admise, il crée une carte
dans le projet parent avec carte parente, branche, clé d'idempotence, skill
préchargé, durée maximale de 45 minutes et deux nouvelles tentatives au plus.
Une enveloppe de job distincte crée ensuite issue enfant, branche, worktree
Hermes sous `.worktrees/`, session et PR brouillon, sans force-push, reset
destructif ou auto-merge.

Le cycle humain reste hors des workers. Une PR prête et revue place sa carte
dans `awaiting_go`. Seule une fusion explicitement autorisée et observée place
la carte à `done`. Quand toutes les cartes de la vague sont `done`, un
synthesizer unique vérifie les journaux immuables, construit les trois
artefacts partagés candidats, appelle le fan-in transactionnel du runtime et
ouvre une PR de fan-in. La vague suivante demeure inadmissible jusqu'à fusion
humaine de cette PR.

### S-003 ADRs

Aucun nouvel ADR n'est nécessaire. S-003 applique sans variante locale les
décisions acceptées :

- [ADR-001](adr/001-use-hermes-kanban.md) — Kanban Hermes comme unique
  ordonnanceur durable ;
- [ADR-002](adr/002-bound-parallel-capacity.md) — deux writers, trois analyses
  en lecture seule et une gate lourde ;
- [ADR-003](adr/003-isolate-each-job.md) — enveloppe complète propre à chaque
  job ;
- [ADR-004](adr/004-use-single-writer-fan-in.md) — journaux task-local et
  synthesizer transactionnel unique ;
- [ADR-005](adr/005-migrate-state-with-dual-read.md) — état v2 compatible avec
  le rollback au profil précédent.

### S-003 Component Map

| Frontière | Composant | Responsabilité S-003 | Writer |
|---|---|---|---|
| Commande mono-tâche | `hermes/skills/sdd-build` | Valider l'appel, choisir les rôles Spring ou React, piloter le cycle TDD et journaliser les preuves | T-009 |
| Admission parallèle | `hermes/runtime/sdd_build_orchestrator.py` | Interroger l'état v2, construire la vague, acquérir les leases et créer les cartes Kanban | T-010 |
| Enveloppe de job | `hermes/runtime/sdd_job_execution.py` | Créer branche, worktree, session, issue et PR ; expurger les logs et préserver les ressources en échec | T-011 |
| Synthèse de vague | `hermes/runtime/sdd_wave_synthesizer.py` | Appliquer la gate de go, observer les merges, consolider les journaux et produire la PR de fan-in | T-012 |
| Audit source | `hermes/scripts/test_sdd_s003_contract.py` | Prouver la couverture exacte 51/51, les frontières, la capacité et la publication de la commande dans l'aide | T-013 |
| Distribution | profil Hermes 0.6.0 | Copier exactement skill et runtime, exécuter les mêmes tests, versionner, appliquer la gate et conserver le rollback 0.5.0 | T-014 |

Le runtime existant reste partagé et non dupliqué :

- `sdd_runtime_guard.py` valide l'état, le DAG, les Test-IDs et scopes, gère
  leases, journaux, empreintes et fan-in transactionnel ;
- `sdd_github_bridge.py` crée issue et PR, rend la PR prête et suit
  checks/reviews/fils sans fusion ;
- les trois nouveaux composants composent ces primitives par adaptateurs
  structurés ; aucun ne crée une seconde boucle d'ordonnancement Python.

### S-003 Module Boundaries

- `hermes/skills/sdd-build` est la seule interface utilisateur de S-003. Son
  garde orchestre une tâche ; il ne remplace ni l'état partagé ni le Kanban.
- `sdd_build_orchestrator.py` décide seulement de l'admission et crée les
  cartes via l'adaptateur Kanban. Il délègue l'exécution à une interface de job
  et ne manipule pas GitHub ou les artefacts partagés directement.
- `sdd_job_execution.py` matérialise une enveloppe déjà admise. Il consomme le
  bridge GitHub existant et n'admet aucune autre tâche.
- `sdd_wave_synthesizer.py` est l'unique appelant autorisé de
  `transactional_fan_in` pour S-003. Les workers ne reçoivent aucune référence
  leur permettant d'écrire `04-tasks.md`, `.tdd-state.json` ou
  `05-implementation-log.md`.
- Les rôles embarqués sont en lecture limitée sur le contrat fourni et en
  écriture uniquement sur les fichiers loués. `delegate_task` reste réservé à
  leurs sous-analyses internes en lecture seule ; il n'ordonnance pas les jobs.
- Après T-009, T-010 est le seul writer S-003 admissible avec le writer S-004
  `/sdd-code-simplify` prévu par la roadmap. T-011 dépend de T-010 : leurs
  chemins restent strictement disjoints pour éviter un couplage de fichiers,
  mais ils ne consomment jamais simultanément les deux slots avec S-004. T-012
  est ensuite le writer unique d'intégration, puis T-013 le writer unique
  d'audit source et T-014 le writer unique du dépôt profil.

### S-003 Interaction Model

#### Chemin mono-tâche

1. Valider les arguments structurés, `feature-id`, `T-NNN`, spec approuvée,
   état v2, contrat de `04-tasks.md`, dépendances `done` et scope littéral.
2. Détecter la stack du projet cible à partir de preuves reliées à la tâche et
   charger le couple de rôles Spring ou React/Next.js correspondant.
3. Acquérir le lease, relever l'empreinte hors scope et transmettre au
   test-engineer uniquement Test-IDs, fichiers de test, commande de test et
   contrat RED. Le rôle écrit seulement le test rouge.
4. Vérifier que l'échec est celui attendu, puis écrire d'abord l'événement RED
   immuable avec Test-IDs, commande, sortie expurgée et fichiers concernés.
5. Transmettre à l'implementer uniquement la preuve RED et les fichiers de
   production en scope. Vérifier GREEN, puis exécuter REFACTOR et SIMPLIFY dans
   le même job, chaque transition étant journalisée avant progression.
6. Vérifier l'empreinte hors scope et libérer le lease. Un échec conserve le
   journal et les preuves, sans écriture directe des artefacts partagés.

#### Chemin parallèle et fan-in

1. Valider `--parallel` et la valeur éventuelle `--max-workers`; sur le VPS,
   l'absence vaut deux et toute valeur supérieure à deux est refusée.
2. Lire les tâches prêtes dans l'état v2, puis placer dans la vague toutes celles
   dont les dépendances sont fusionnées et dont les scopes sont mutuellement
   disjoints. Un conflit est sérialisé et une dépendante reste en attente ; le
   Kanban ne rend actifs que deux writers, les cartes suivantes restant en file.
3. Créer idempotemment chaque carte sur le projet parent, avec carte parente,
   branche, skill, budget de 45 minutes et deux retries, puis matérialiser
   l'enveloppe propre du job.
4. Lancer le même cycle mono-tâche dans chaque job. Le timeout ou l'échec d'un
   job libère uniquement son lease, conserve ses logs/journal/worktree et ne
   modifie ni n'annule l'autre job.
5. Après tests, checks et review, placer la carte à `awaiting_go`. Sans go, ne
   fusionner aucune PR. Après go et fusion humaine observée, passer cette carte
   à `done`.
6. Quand toute la vague est `done`, le synthesizer vérifie chaque manifeste,
   consolide transactionnellement les artefacts partagés sur sa branche et
   crée une PR de fan-in. Une reprise rejoue le même identifiant et contenu.
7. Refuser toute admission de la vague suivante jusqu'à fusion humaine de la
   PR de fan-in.

### S-003 Entity Relationship Model

S-003 n'ajoute aucune entité persistée par une application. Il matérialise les
cardinalités conceptuelles déjà approuvées :

- une tâche possède au plus un job actif ; chaque job parallèle possède
  exactement une carte, une issue enfant, une branche, un worktree, une
  session, un journal et une PR ;
- une vague contient au moins un job et au plus deux writers actifs à un
  instant donné ; le nombre de cartes de la vague peut être supérieur à deux,
  mais les suivantes attendent un slot ;
- une vague possède exactement une PR de fan-in, créée seulement après que
  toutes ses cartes sont `done` ;
- une feature possède une issue et une carte parentes, un projet/board Hermes
  explicites et un seul ensemble d'artefacts partagés.

### S-003 OpenAPI Sketch

N/A. Aucun endpoint HTTP n'est ajouté ou modifié.

### S-003 Data Model + Migrations

- Base de données, table, collection et outil de migration : N/A.
- État SDD : le schéma v2 fusionné en S-002 est réutilisé sans nouveau champ.
  T-009 à T-014 sont ajoutées `pending` avec dépendances, Test-IDs et scopes ;
  T-001 à T-008 et leurs preuves restent inchangées.
- Données durables non versionnées : leases, manifestes et transactions restent
  dans le Git common dir selon le runtime v2.
- Retour arrière : rétablir le profil 0.5.0. Ne supprimer ni état, journal,
  log, issue, carte, branche, worktree, session ou PR existants.

### S-003 Security Posture

- Authentification HTTP et autorisation applicative : N/A.
- GitHub et Hermes sont fournis par des adaptateurs déjà authentifiés ; aucun
  token ou credential n'est transmis aux rôles ni écrit dans les artefacts.
- Les logs et extraits de commandes expurgent secrets, tokens, données
  personnelles, chemins absolus et contenu métier avant journalisation.
- Les commandes restent des listes d'arguments structurées. `--yolo`, options
  de bypass, force-push, reset destructif et toute commande de merge automatique
  sont refusés.
- Chaque worker reçoit le plus petit contexte et le scope littéral nécessaire ;
  les artefacts partagés ne sont jamais montés comme surface d'écriture du rôle.

### S-003 Test Strategy

1. T-009 produit le RED du garde mono-tâche, puis prouve le routage Spring/React,
   l'ordre des rôles et phases, l'écriture locale préalable des preuves et le
   refus des artefacts partagés.
2. Après fusion de T-009, T-010 peut progresser en parallèle du writer S-004
   hors périmètre. T-011 attend T-010, puis complète l'enveloppe sur des
   fichiers distincts. Des adaptateurs factices et une horloge contrôlée
   prouvent admission, cartes, budgets, retries, isolation et reprise sans
   appeler Hermes ou GitHub réels.
3. T-012 injecte des états de PR et des interruptions avant/après fan-in pour
   prouver go humain, aucune fusion automatique, atomicité, idempotence et
   barrière de vague.
4. T-013 exécute un manifeste source exact des 51 AC, vérifie les scopes et le
   DAG, puis rejoue toutes les suites runtime/skill concernées. Il constitue le
   fan-in d'audit, sans réimplémenter T-009 à T-012.
5. T-014 copie exactement les surfaces source dans le profil, exécute les mêmes
   tests depuis la disposition profil, vérifie la parité, la version 0.6.0 et la
   gate CI/tests/contrats/review/fils/go avant fusion.

### S-003 Detailed AC Reconciliation

| Producteur primaire | AC uniques | Nombre | Preuve principale |
|---|---|---:|---|
| T-009 mono-tâche | AC-019, AC-037–AC-044, AC-124–AC-127, AC-257–AC-259 | 16 | garde du skill, cycle et journal task-local |
| T-010 orchestrateur | AC-020–AC-023, AC-027–AC-029, AC-031, AC-128–AC-133, AC-236, AC-260 | 16 | barrière mono fusionnée, sélection de vague et carte Kanban |
| T-011 enveloppe job | AC-030, AC-032–AC-036, AC-233–AC-234 | 8 | branche/worktree/session/GitHub et sécurité Git |
| T-012 fan-in humain | AC-045–AC-047, AC-134–AC-137, AC-231 | 8 | gate de go et synthesizer transactionnel |
| T-013 audit source | AC-024 | 1 | carte visible par `/sdd-status` et manifeste 51/51 |
| T-014 profil 0.6.0 | AC-013, AC-138 | 2 | parité, tests de profil et gate de publication |

Total : **51 AC primaires uniques sur 51**, aucun orphelin et aucun doublon
primaire. T-013 audite secondairement l'ensemble des 51 identifiants.

### S-003 Capacity and Wave Validation

```text
T-008 done
  -> W-009 : T-009 build mono-tâche
       -> W-010 : T-010 orchestrateur || writer S-004 hors périmètre
            -> W-011 : T-011 enveloppe job
                 -> W-012 : T-012 gate humaine et synthesizer
                      -> W-013 : T-013 audit source 51/51
                           -> W-014 : T-014 profil 0.6.0
```

- Writers : W-010 utilise un writer S-003 et réserve le second au chantier
  S-004. W-011 à W-014 utilisent chacune un seul writer S-003.
- Analyses internes : chaque job peut déléguer au plus trois analyses en
  lecture seule ; elles n'obtiennent aucun lease d'écriture.
- Gate lourde : le coordinateur de gate du runtime en autorise exactement une
  à la fois ; les jobs supplémentaires attendent.
- Artefacts partagés : les workers n'y accèdent pas ; T-012 est le seul
  synthesizer transactionnel de sa vague.
- S-004 : `/sdd-code-simplify` peut être développé après fusion de T-009 en
  parallèle de T-010. T-011 attend ensuite T-010 et le prochain slot S-003 ;
  les AC, fichiers et la publication 0.6.1 restent hors de S-003.

### S-003 Risks + Rollback

| Risque | Probabilité | Impact | Réduction | Retour arrière |
|---|---|---|---|---|
| Le mono-tâche laisse un rôle écrire l'état partagé | moyenne | preuves concurrentes ou partielles | contexte sans handle partagé, fingerprint et `validate_worker_changes` | arrêter le job, conserver son journal et revenir au profil 0.5.0 |
| Deux tâches en conflit entrent dans la même vague | moyenne | collision de fichiers | validation DAG/scopes, leases et sérialisation explicite | libérer uniquement le lease non démarré et recalculer la vague |
| Timeout ou échec détruit l'autre job | moyenne | travail perdu | ressources par job, erreurs isolées et aucun nettoyage automatique | conserver branche, worktree, PR, logs et journal ; reprendre idempotemment |
| Carte, branche et PR divergent | moyenne | reprise ambiguë | même clé d'idempotence et identifiants croisés via le bridge | remettre la carte `needs_input`, sans recréer ni supprimer les objets |
| Fan-in partiel après interruption | moyenne | artefacts incohérents | writer unique, verrou, CAS, journal et marqueur transactionnel | reprise runtime vers l'ancien ou le nouvel ensemble complet |
| Fusion sans go | faible | violation de la gouvernance | aucune API de merge dans les modules ; état `awaiting_go` bloquant | ne pas fusionner ; conserver PR et carte |
| Profil 0.6.0 diverge de la source | moyenne | commande installée non prouvée | copie exacte, comparaison sans différence et tests depuis le profil | fermer la PR profil et conserver 0.5.0 |

### S-003 Non-Functional Requirements

- Capacité : au plus deux writers, trois analyses en lecture seule et une gate
  lourde, sans valeur plus élevée configurable sur le VPS.
- Durée/reprise : 45 minutes maximum par tentative et deux nouvelles tentatives
  au plus ; la reprise conserve l'autre job et toutes les preuves du job en
  échec.
- Confidentialité : aucune des cinq catégories sensibles définies par Q-008 ne
  paraît dans les logs versionnés.
- Publication : CI obligatoire, tests et contrats verts, review `approve`, zéro
  fil actionnable et go humain précèdent la fusion du profil 0.6.0.

Aucun autre SLO de latence, débit ou consommation n'est introduit.

### S-003 Open Questions

- (aucune)

### S-003 Resolved Questions

- Les décisions Q-001 à Q-010 de `01-spec.md` et ADR-001 à ADR-005 suffisent ;
  S-003 n'introduit aucune décision supplémentaire.
- Le mono-tâche est fusionné avant l'orchestrateur ; S-004 peut seulement
  démarrer après cette barrière et reste hors de la couverture S-003.

### S-003 Design Review

- [x] Carte des composants Python/Hermes, frontières et interaction présentes.
- [x] Spring applicatif, OpenAPI, persistance, migrations et ArchUnit explicitement N/A.
- [x] Rôles Spring/React embarqués, sécurité, logs et interdictions documentés.
- [x] Les composants parallèles ont des fichiers concrets disjoints et un writer partagé unique.
- [x] Le DAG respecte mono-tâche avant orchestrateur et publication après audit.
- [x] La capacité 2 writers / 3 analyses / 1 gate est vérifiable.
- [x] Chaque risque possède une réduction et un retour arrière 0.5.0.
- [x] Les 51 AC sont couverts exactement, sans doublon primaire.
- [x] Aucun comportement absent de `01-spec.md` ou de l'issue #74 n'est introduit.
- [x] Aucun nouvel ADR n'est requis et aucune question ouverte ne subsiste.

### S-003 Sign-off

- [x] Les artefacts Epic restent approuvés et inchangés dans leurs décisions.
- [x] Chaque AC S-003 est relié à un producteur primaire et à un Test-ID planifié.
- [x] Checklist `design-review.md` relue le 2026-08-03.
- [x] Première tâche build : `/sdd-build 2026-07-31-hermes-parallel-sdd T-009`.

## Conception détaillée : S-004 — `/sdd-code-simplify`, profil 0.6.1

> Cette section prolonge les conceptions S-001 à S-003 sans les réécrire. Elle
> couvre uniquement `AC-014` et `AC-139`. La tranche convertit le comportement
> Codex existant de `code-simplify` en commande Hermes puis le distribue ; elle
> n'ajoute aucun comportement de simplification.

### S-004 Inputs

- Révision de `01-spec.md` : SHA-256
  `71fd818b8d9e30931ac5203bd3099ec5ecceb6475461b4d494e72674f640a7b6`.
- Révision de `02-spec-review.md` : SHA-256
  `c64ffd8f8af312a50da04a066ee47874a310654753630224a5184a8d5a0e50f2`,
  verdict `approve`, zéro question ouverte.
- Conception Epic approuvée : SHA-256
  `f17fced20d9a0f3dc1c9c82732d1a6cb1cb755ebcf52cf06696d9b552c82430b`.
- Roadmap Epic approuvée : SHA-256
  `793454ebaec09cc6c8f7eb05110db35ac0f5f112ebb8b55399d93a6f39494f99`.
- Barrière d'entrée : T-009 est `done`, donc le chantier source S-004 peut
  progresser dans le second slot prévu par la roadmap. La publication T-016
  attend néanmoins T-014 afin que le profil 0.6.0 précède 0.6.1.
- Source fonctionnelle : `.agents/skills/code-simplify/SKILL.md` et
  `.agents/skills/clarity-over-cleverness/SKILL.md` définissent déjà les
  entrées, refus, catégories de réécriture et preuves à conserver.

#### S-004 Inputs from detect-stack.sh

- Résultat observé le 2026-08-03 :
  `{"error":"pom.xml introuvable","searched":"pom.xml"}`.
- La topologie applicative Spring/React, OpenAPI, base de données, migration et
  ArchUnit reste sans objet selon Q-006. La cible est le framework Python et
  les documents de skills Hermes.

### S-004 Architecture Overview

La source canonique ajoute `hermes/skills/sdd-code-simplify`, composé d'un
contrat de commande, d'une checklist de clarté embarquée, d'un contrat de
délégation et d'un garde Python déterministe. Le garde valide une cible
explicite sous `src/main/**`, refuse une cible de test ou hors périmètre, et
compose les primitives du runtime v2 pour protéger le lease et l'empreinte des
fichiers ; il ne devient ni ordonnanceur ni moteur de réécriture. Le skill
charge le rôle existant chargé de la clarté, exige une suite verte avant toute
écriture, conserve la suite verte après chaque fichier et produit le résumé
prévu par le comportement Codex existant. Le contrat source prouve la commande
et actualise l'aide avant que T-016 copie exactement la surface dans le profil
0.6.1. La publication exige uniquement CI, tests et contrats verts, puis le go
explicite avant fusion ; aucune review humaine ou attente de review n'est une
porte de S-004.

### S-004 ADRs

- ADR-001 à ADR-005 restent applicables pour l'ordonnancement Hermes, la
  capacité, l'isolation, l'écrivain unique et la compatibilité d'état.
- Aucun ADR supplémentaire : convertir fidèlement un skill existant et copier
  sa source canonique dans le profil sont des décisions imposées par la tranche,
  sans alternative architecturale significative nouvelle.

### S-004 Component Map

| Frontière | Composant | Responsabilité | Tâche |
|---|---|---|---|
| Commande publique | `hermes/skills/sdd-code-simplify/SKILL.md` | Exposer `/sdd-code-simplify <path> [--dry-run]`, les lectures, refus et preuves de fin | T-015 |
| Contrats embarqués | `hermes/skills/sdd-code-simplify/references/clarity-checklist.md`, `delegation-contract.md` | Conserver la checklist de clarté et borner les écritures du rôle | T-015 |
| Garde déterministe | `hermes/skills/sdd-code-simplify/scripts/code_simplify_guard.py` | Valider arguments et cible, exiger le vert initial et protéger scope/empreinte via le runtime v2 | T-015 |
| Contrats source | tests du skill et `hermes/scripts/test_sdd_s004_contract.py` | Prouver le comportement, l'aide installée et la couverture exacte des deux AC | T-015 |
| Distribution | profil Hermes 0.6.1 | Copier la commande sans différence, exécuter ses tests, versionner et conserver le rollback 0.6.0 | T-016 |

### S-004 Module Boundaries

- **Skill source** — `hermes/skills/sdd-code-simplify/**` est la seule source
  de la commande. Il peut importer `hermes.runtime.sdd_runtime_guard`, mais ne
  copie aucune primitive de lease, fingerprint ou validation de scope.
- **Rôle interne** — le rôle reçoit seulement la cible normalisée, le mode
  `dry-run`, la checklist et la commande de test validée. Il n'obtient aucun
  handle vers `04-tasks.md`, `.tdd-state.json` ou `05-implementation-log.md`.
- **Documentation et audit** — `sdd-help`, le README Hermes et la documentation
  de migration publient la commande comme installée uniquement après son
  contrat source. L'audit S-004 ne modifie pas le skill.
- **Profil** — `skills/sdd-code-simplify/**` est une copie exacte de la source ;
  T-016 est l'unique writer du dépôt profil pour 0.6.1.

```text
T-009 done
  -> T-015 source `/sdd-code-simplify`

T-014 profil 0.6.0 ─┐
                     ├─> T-016 profil 0.6.1
T-015 source ────────┘
```

### S-004 Entity Relationship Model

| Entité conceptuelle | Rôle | Attributs principaux | Relations et cardinalités | Persistance |
|---|---|---|---|---|
| Invocation de simplification | Demande utilisateur bornée | cible relative, `dry-run` | une invocation cible exactement un fichier ou un dossier ; un dossier résout un ou plusieurs fichiers de production | aucune base ; arguments en mémoire |
| Fichier cible | Unité atomique de réécriture ou d'ignorance | chemin normalisé, empreinte, résultat | une invocation concerne 1..* fichiers ; chaque fichier produit exactement un résultat `simplified` ou `ignored` | worktree du job uniquement |
| Preuve de test | Préserve le comportement | argv structurés, code retour, sortie expurgée | une invocation possède exactement une preuve verte initiale et une preuve après chaque fichier traité | journal local du job |
| Résumé de clarté | Résultat observable | fichiers, catégories, tests, régressions | une invocation produit exactement un résumé ; sans feature active il est écrit dans un fichier `clarity-pass-<date>.md` | journal prévu par le skill existant |

Il n'existe aucune entité JPA, relation persistée, table ou cascade dans S-004.

### S-004 OpenAPI Sketch

Sans objet : `/sdd-code-simplify` est une commande Hermes locale et n'ajoute ni
ne modifie aucun endpoint HTTP.

### S-004 Data Model + Migrations

- Tables ou collections touchées : aucune.
- Outil de migration : aucun ; le détecteur ne trouve pas de projet Maven et
  aucun changement de schéma n'est prévu.
- État v2 : lu par le runtime pour le scope et le lease, sans évolution de
  schéma dans cette tranche.
- Réversibilité : retrait de la commande source ou retour du profil de 0.6.1 à
  0.6.0, sans conversion ni suppression d'état.

### S-004 Security Posture

- Authentification et autorisation HTTP : sans objet ; aucun endpoint.
- Validation : le garde accepte un chemin littéral relatif sous `src/main/**`,
  refuse `src/test/**`, glob, lien symbolique et sortie du dépôt, et valide
  `--dry-run` avant toute écriture.
- Isolation : la commande détient le lease du scope exact et compare
  l'empreinte hors périmètre après chaque intervention.
- Confidentialité : argv, sorties de tests et diagnostics sont expurgés selon
  Q-008 ; aucun secret, token, donnée personnelle, chemin absolu ou contenu
  métier n'entre dans un artefact versionné.
- Secrets : aucun secret nouveau ; la commande ne reçoit ni ne stocke de
  credential.

### S-004 Test Strategy

1. T-015 commence par un contrat rouge prouvant l'absence de la commande. Les
   tests du skill couvrent ensuite la validation de cible, `--dry-run`, le vert
   initial, l'ordre fichier par fichier, le retour au contenu antérieur en cas
   de régression et le résumé final.
2. Le garde est testé avec un rôle et un runner de tests injectés ; aucun test
   ne modifie un projet réel ni n'exécute une gate lourde externe.
3. Le contrat source vérifie que l'aide déplace `/sdd-code-simplify` de la
   roadmap vers les commandes installées et que le manifeste S-004 contient
   exactement AC-014 et AC-139.
4. T-016 vérifie depuis la disposition profil la parité sans différence, les
   mêmes tests, la version 0.6.1, le changelog et les métadonnées. La fusion
   reste impossible sans CI/tests/contrats verts et go explicite.

### S-004 Detailed AC Reconciliation

| AC | Producteur primaire | Preuves principales |
|---|---|---|
| AC-014 | T-016 | commande installée dans le profil 0.6.1, parité et tests de disposition ; T-015 fournit et prouve secondairement la source canonique |
| AC-139 | T-016 | barrière T-014/T-015, version 0.6.1, parité, tests de profil, gate technique et go explicite |

Les deux AC ont T-016 comme producteur observable de publication ; T-015 est le
prérequis source traçable d'AC-014. Aucun critère de S-003 ou S-005 n'est
absorbé par cette tranche.

### S-004 Risks + Rollback

| Risque | Probabilité | Impact | Réduction | Retour arrière |
|---|---|---|---|---|
| Une passe change le comportement | moyenne | régression fonctionnelle | suite verte initiale et après chaque fichier, retour atomique du fichier en échec | restaurer le contenu antérieur du fichier et le marquer `ignored` |
| Une cible sort de `src/main/**` | faible | écriture hors autorisation | normalisation, refus des tests, globs, symlinks et chemins externes | refuser avant lease et conserver le worktree intact |
| Le rôle touche un artefact partagé | faible | incohérence de fan-in | contexte sans handle partagé, scope lease et fingerprint | arrêter le job, conserver sa preuve locale, ne pas publier l'événement |
| Le profil 0.6.1 diverge de la source | moyenne | commande installée non prouvée | copie exacte, comparaison sans différence et mêmes tests | fermer/annuler la PR profil et conserver 0.6.0 |
| 0.6.1 est publié avant 0.6.0 | faible | ordre de migration invalide | dépendance T-016 sur T-014 et T-015 | bloquer la publication 0.6.1 jusqu'à 0.6.0 fusionné |

### S-004 Non-Functional Requirements

- Aucune nouvelle exigence de latence, débit, observabilité ou performance.
- Les contraintes Epic existantes restent applicables : deux writers, trois
  analyses en lecture seule et une seule gate lourde à la fois.

### S-004 Open Questions

- (aucune)

### S-004 Resolved Questions

- **Décision autonome — fidélité au comportement existant :** la commande
  Hermes reprend les entrées, refus, checklist et preuves déjà définis par les
  skills Codex `code-simplify` et `clarity-over-cleverness`. Justification : ce
  sont les seules sources de comportement disponibles et la roadmap interdit
  d'étendre S-004.
- **Décision autonome — deux tâches :** séparer la source canonique T-015 de la
  distribution T-016. Justification : les dépôts et rollbacks diffèrent, et la
  publication 0.6.1 doit dépendre explicitement de 0.6.0.
- **Décision autonome — porte sans review :** pour T-015 et T-016, la gate de
  publication signifie CI, tests et contrats verts, puis go explicite avant
  fusion. Aucune demande, attente, approbation ou fil de review n'est planifié,
  conformément à la dernière instruction utilisateur qui remplace ces gates.
- Les Q-001 à Q-010 et ADR-001 à ADR-005 restent résolus ; aucune Q-NNN
  supplémentaire n'est nécessaire.

### S-004 Design Review

- [x] Carte des composants Python/Hermes, frontières et interaction présentes.
- [x] Spring applicatif, OpenAPI, persistance, migrations et ArchUnit explicitement N/A.
- [x] Le modèle conceptuel et ses cardinalités sont explicites.
- [x] Sécurité des chemins, confidentialité, scope et secrets documentés.
- [x] Le DAG est acyclique et impose 0.6.0 avant 0.6.1.
- [x] Chaque risque possède une réduction et un retour arrière 0.6.0.
- [x] AC-014 et AC-139 possèdent chacun un producteur primaire et des preuves.
- [x] Aucun comportement absent de la spécification ou du skill existant n'est introduit.
- [x] Aucune question ouverte ni décision nécessitant un nouvel ADR.

### S-004 Sign-off

- [x] Les artefacts Epic approuvés sont les entrées de la tranche.
- [x] Chaque AC S-004 est relié à une tâche et à des Test-IDs planifiés.
- [x] Checklist `design-review.md` relue le 2026-08-03.
- [x] Première tâche : `/sdd-build 2026-07-31-hermes-parallel-sdd T-015`.

## Conception détaillée : S-005 — `/sdd-test`, `/sdd-validate`, profil 0.7.0

> Cette section prolonge S-001 à S-004 sans les réécrire. Elle couvre
> exactement AC-015, AC-016, AC-140 à AC-147 et AC-196 à AC-217.

### S-005 Inputs

- Spécification et revue approuvées sans question ouverte.
- Conception Epic et roadmap : S-005 publie les phases 5 et 6 après le cycle
  de build et de simplification.
- Barrières : `/sdd-wire-harness` est disponible ; la publication 0.7.0 attend
  le profil 0.6.1 et l'audit source S-005.
- Sources fonctionnelles : `.agents/skills/test/SKILL.md`,
  `.agents/skills/validate/SKILL.md`, les templates de test, validation et
  traçabilité, ainsi que les scripts existants du harness.
- Stack détectée : dépôt de framework Python sans `pom.xml`; Spring, React,
  OpenAPI, persistance et migration sont non applicables à l'implémentation des
  commandes, mais restent des stacks consommatrices déléguées par les skills.

### S-005 Architecture Overview

La source ajoute deux skills indépendants. `sdd-test` construit un plan de test
et peut déléguer l'ajout de tests, avec une frontière d'écriture limitée à
`src/test/**` et `06-test-plan.md`. `sdd-validate` exécute le harness installé,
collecte les résultats spécialisés Spring et React, puis un writer unique
publie `07-validation-report.md` et `07a-traceability.md`. Les deux commandes
utilisent le verrou global canonique du runtime autour de chaque gate lourde :
Maven, Next, PIT et OWASP ne se chevauchent jamais. Les agents spécialisés ne
reçoivent aucun handle vers les rapports communs.

Le développement source des deux commandes peut progresser en parallèle sur
des scopes disjoints. Leur ordre de fusion reste strict : la PR `sdd-test`
précède la PR `sdd-validate`. Un audit source unique prouve ensuite les 32 AC,
installe les deux commandes dans l'aide et ouvre la voie au profil 0.7.0.
Aucune review humaine n'est une gate; tests, contrats et CI sont techniques,
et toute fusion conserve le go explicite prévu par le handoff.

### S-005 ADRs

- ADR-001 à ADR-005 restent applicables : Kanban unique, capacité bornée,
  isolation, writer partagé unique et état v2.
- Aucun nouvel ADR : les limites d'écriture, l'ordre de fusion et les verdicts
  sont imposés directement par AC-140 à AC-147.

### S-005 Component Map

| Frontière | Composant | Responsabilité | Tâche |
|---|---|---|---|
| Test public | `hermes/skills/sdd-test/**` | arguments, gaps, matrice, scope tests, traçabilité et preuve verte | T-017 |
| Validation publique | `hermes/skills/sdd-validate/**` | gates sérialisées, fan-in spécialisé, rapports communs et verdict `PASS\|FAIL` | T-018 |
| Audit source | `hermes/scripts/test_sdd_s005_contract.py` et docs | couverture exacte des 32 AC et publication dans l'aide | T-019 |
| Distribution | profil Hermes 0.7.0 | copie exacte, tests de disposition, version, rollback et barrières | T-020 |

### S-005 Module Boundaries

- `sdd-test` peut lire spécification, conception, tâches et rapports existants.
  Son rôle reçoit uniquement les chemins de tests autorisés et un candidat de
  plan; le garde principal publie atomiquement `06-test-plan.md`.
- `sdd-validate` peut lire le harness, son résumé, le plan de test et les
  artefacts SDD. Les validateurs Spring et React retournent des objets
  structurés en lecture seule; seul le fan-in écrit les deux rapports communs.
- Les deux gardes composent `hermes.runtime.sdd_runtime_guard.global_lock` pour
  une gate lourde à la fois et `validate_worker_changes` pour leur scope.
- L'audit et le profil ne modifient jamais le comportement des deux skills.

```text
T-003 wire-harness ─┬─> T-017 /sdd-test ─────┐
T-009 runtime v2 ───┘                         ├─> T-019 audit source
                     └─> T-018 /sdd-validate ┘

T-016 profil 0.6.1 ─┐
                     ├─> T-020 profil 0.7.0
T-019 audit source ──┘
```

T-017 et T-018 sont développables en parallèle, mais T-018 est empilée ou
retargetée de façon à ne jamais fusionner avant T-017.

### S-005 Data and Report Model

| Objet | Champs principaux | Producteur | Règles |
|---|---|---|---|
| Plan de test | AC, types, gaps, tests, justification | `sdd-test` | un `Gap-NNN` a un test ou `Won't fix`; écriture atomique |
| Preuve de gate | type, argv, retour, sortie expurgée, horodatage | garde de validation | argv structurés; résultat uniquement `PASS` ou `FAIL` |
| Résultat spécialisé | stack, portes, couverture, mutations, traçabilité | validateur Spring ou React | lecture seule; aucun rapport commun écrit |
| Rapport commun | verdict, table des portes, échecs, liens, action | fan-in validation | writer unique; verdict uniquement `PASS` ou `FAIL` |
| Matrice de traçabilité | AC, tâche, test, symbole, porte | fan-in validation | aucun AC sans preuve en cas de `PASS` |

Il n'existe aucune entité JPA, table, relation persistée ou migration dans
S-005. Les fichiers Markdown et JSON sont les seules sorties durables.

### S-005 API and Security Posture

- Aucun endpoint OpenAPI ou HTTP n'est ajouté.
- Les commandes acceptent des identifiants et options structurés, jamais une
  chaîne shell. Tout argument de contournement de test est refusé.
- Chemins absolus, secrets, tokens, données personnelles et contenu métier sont
  expurgés avant journalisation.
- Les liens symboliques, sorties de dépôt et écritures hors scope sont refusés.
- Aucun credential, accès VPS ou déploiement n'appartient à cette tranche.

### S-005 Test Strategy

1. T-017 commence par un contrat rouge sur l'absence de `/sdd-test`, puis
   couvre arguments, refus de production, plan atomique, gaps, tags AC,
   traçabilité et verrou de gate.
2. T-018 commence par l'absence de `/sdd-validate`, puis couvre préconditions,
   résultats frais, fan-in Spring/React, writer unique, sérialisation des gates
   et verdicts `PASS|FAIL`.
3. Les preuves AC-196 à AC-217 référencent des tests exécutables existants du
   runtime et des contrats supplémentaires; aucun test documentaire seul ne
   prétend prouver une reprise ou un chevauchement temporel.
4. T-019 vérifie par manifeste exécutable exactement 32 AC et un producteur
   primaire unique par AC.
5. T-020 exécute les mêmes tests depuis la disposition profil et prouve la
   parité exacte avant toute publication 0.7.0.

### S-005 Detailed AC Reconciliation

| Groupe | Producteur primaire | Preuve prévue |
|---|---|---|
| AC-142, AC-196 à AC-209 | T-017 | garde `sdd-test`, catalogue de tests unitaires et parallèles |
| AC-143 à AC-146, AC-210 à AC-217 | T-018 | garde `sdd-validate`, fan-in et preuves GitHub/transactionnelles |
| AC-140, AC-141 | T-019 | audit DAG, scopes disjoints et ordre de fusion |
| AC-015, AC-016, AC-147 | T-020 | parité, profil 0.7.0 et gate de publication |

La réconciliation contient 15 + 12 + 2 + 3 = 32 producteurs primaires, sans
recouvrir les AC S-004 ou S-006.

### S-005 Risks and Rollback

| Risque | Réduction | Retour arrière |
|---|---|---|
| `sdd-test` touche la production | normalisation du scope et fingerprint | restaurer la transaction et refuser le plan |
| deux gates lourdes se chevauchent | verrou global canonique autour de chaque gate | libérer le lease et conserver la preuve d'échec |
| un validateur écrit un rapport commun | délégation sans handle et fan-in unique | rejeter le résultat et conserver les anciens rapports |
| verdict ambigu | enums fermés `approve\|request-changes` et `PASS\|FAIL` | refuser la publication du rapport |
| profil divergent ou hors ordre | parité et dépendances T-016/T-019 | fermer la PR 0.7.0 et conserver 0.6.1 |

### S-005 Open Questions

- (aucune)

### S-005 Resolved Questions

- **Décision autonome — quatre tâches :** séparer les deux commandes, l'audit
  source et la distribution. Justification : les scopes et rollbacks diffèrent
  et le profil doit attendre les deux commandes auditées.
- **Décision autonome — parallélisme de développement seulement :** T-017 et
  T-018 peuvent progresser ensemble, tandis que la fusion de T-018 attend
  T-017. Justification : concilier AC-140 et AC-141 sans scope commun.
- **Décision autonome — verrou existant :** composer le verrou global runtime
  plutôt que créer un ordonnanceur ou une nouvelle primitive de scheduling.
- **Décision autonome — aucune review :** les gates S-005 sont les tests,
  contrats, CI et le go explicite avant fusion; aucune demande ou attente de
  review n'est ajoutée.

### S-005 Design Sign-off

- [x] Les 32 AC possèdent un producteur primaire unique.
- [x] Le DAG est acyclique et l'ordre test avant validate est explicite.
- [x] Les scopes T-017/T-018 sont disjoints et le writer commun est T-019.
- [x] Sécurité, rollback, fan-in, données et stack non applicable sont décrits.
- [x] Aucune question ouverte ni nouvel ADR n'est requis.

## Conception détaillée : S-006 — `/sdd-review`, `/sdd-ship`, profil 0.8.0

> Cette section prolonge S-001 à S-005 sans les réécrire. Elle couvre
> exactement AC-017, AC-018, AC-148 à AC-154, AC-235 et AC-261 à AC-263.

### S-006 Inputs

- Spécification et revue approuvées, sans `Q-NNN` ouverte.
- S-005 fournit le plan de test, le harness validé, les rapports communs et la
  traçabilité consommés en lecture seule par les deux nouvelles commandes.
- Sources fonctionnelles : `.agents/skills/review/SKILL.md`,
  `.agents/skills/ship/SKILL.md`, `spring-code-review-rubric`,
  `shipping-and-launch` et les deux templates Codex correspondants.
- Le dépôt de framework Python n'ajoute ni Spring applicatif, React, OpenAPI,
  persistance ou migration; ces stacks restent des cibles inspectées.

### S-006 Architecture Overview

`sdd-review` analyse le diff et les artefacts disponibles. Il délègue les
lectures Spring et React/Next.js à des rôles sans handle d'écriture, consolide
leurs constats structurés, puis un writer unique publie `08-code-review.md`.
Son verdict est informatif : il ne bloque ni commit ni PR.

`sdd-ship` lit les artefacts approuvés, classe les préconditions, prépare
retour arrière, observabilité, flags et notes, puis publie uniquement
`09-ship-plan.md`. Le garde ne reçoit ni shell, ni réseau, ni credential, ni
client VPS. Il peut afficher une commande sous forme de donnée expurgée, mais
ne peut jamais l'exécuter.

Les deux skills sont développables en parallèle sur des scopes disjoints.
L'ordre de fusion reste strict : la PR `sdd-review` précède `sdd-ship`. Un audit
source unique installe ensuite les commandes dans l'aide et prouve les 13 AC.
Aucune personne n'est sollicitée pour reviewer les PR de migration; le terme
review désigne ici exclusivement la commande SDD livrée.

### S-006 ADRs

- ADR-001 à ADR-005 restent applicables pour l'isolation, les writers et les
  transactions d'artefacts partagés.
- Aucun nouvel ADR : l'ordre review avant ship et l'absence de déploiement sont
  imposés directement par AC-149, AC-153 et AC-235.

### S-006 Component Map

| Frontière | Composant | Responsabilité | Tâche |
|---|---|---|---|
| Revue publique | `hermes/skills/sdd-review/**` | routage, lectures spécialisées, fan-in et rapport unique | T-021 |
| Préparation publique | `hermes/skills/sdd-ship/**` | portes, rollback, observabilité, flags et notes sans exécution | T-022 |
| Audit source | `hermes/scripts/test_sdd_s006_contract.py` et docs | manifeste exact, ordre, publication et no-deploy | T-023 |
| Distribution | profil Hermes 0.8.0 | copie exacte, tests, version, rollback et barrières | T-024 |

### S-006 Module Boundaries

- Les rôles de revue lisent le diff et retournent des constats structurés;
  seul le garde principal écrit le rapport unique.
- `sdd-review` écrit exclusivement `.specs/<feature>/08-code-review.md`.
- `sdd-ship` écrit exclusivement `.specs/<feature>/09-ship-plan.md` après
  toutes les préconditions; aucun plan partiel n'est publié lors d'un échec.
- Chaque publication utilise `validate_worker_changes` puis un remplacement
  atomique du runtime canonique.
- Les logs et rapports expurgent secrets, tokens, chemins absolus, données
  personnelles et contenu métier non requis.

```text
T-018 validate ─┬─> T-021 /sdd-review ─┐
T-009 runtime ──┘                       ├─> T-023 audit source
                 └─> T-022 /sdd-ship ──┘

T-020 profil 0.7.0 ─┐
                     ├─> T-024 profil 0.8.0
T-023 audit source ──┘
```

T-022 est empilée ou retargetée pour ne jamais fusionner avant T-021.

### S-006 Data and Report Model

| Objet | Champs principaux | Producteur | Règles |
|---|---|---|---|
| Constat spécialisé | stack, sévérité, fichier, ligne, preuve, correction | rôle Spring ou React | lecture seule, vocabulaire fermé, aucune duplication |
| Rapport de revue | inputs, rubric, findings, waivers, verdict | fan-in review | un seul fichier atomique; verdict informatif |
| Porte de livraison | nom, source, résultat, notes | garde ship | toutes `PASS` avant publication |
| Plan de livraison | flag, migration, observabilité, rollback, cohortes, notes | writer ship | toutes sections remplies; commande seulement affichée |

Aucune entité JPA, table ou migration n'est ajoutée. Les deux Markdown sont les
seules sorties durables de S-006.

### S-006 API and Security Posture

- Aucun endpoint HTTP ou contrat OpenAPI n'est ajouté.
- Les références Git et feature IDs sont validées comme données; aucune chaîne
  utilisateur ne devient une commande shell.
- Le garde ship ne possède aucune fonction d'exécution, connexion distante,
  écriture VPS, merge ou déploiement.
- Les liens symboliques, chemins hors dépôt et artefacts hors scope sont
  refusés avant toute écriture.

### S-006 Test Strategy

1. T-021 commence par l'absence de `sdd-review`, puis couvre arguments,
   routage, délégation sans handle, fan-in, writer unique et verdict informatif.
2. T-022 commence par l'absence de `sdd-ship`, puis couvre préconditions,
   rollback, observabilité, flags, notes et preuve structurelle no-deploy.
3. T-023 manifeste exactement 13 AC, vérifie les scopes disjoints, l'ordre de
   fusion et l'installation des deux commandes sans accès VPS.
4. T-024 exécute les mêmes suites depuis le layout profil et prouve la parité
   exacte avant toute publication 0.8.0.

### S-006 Detailed AC Reconciliation

| Groupe | Producteur primaire | Preuve prévue |
|---|---|---|
| AC-150, AC-151 | T-021 | routage Spring/React, fan-in et rapport unique |
| AC-152, AC-153, AC-235, AC-261 à AC-263 | T-022 | plan complet et absence exécutable de déploiement |
| AC-148, AC-149 | T-023 | audit DAG, scopes et ordre review avant ship |
| AC-017, AC-018, AC-154 | T-024 | parité, profil 0.8.0 et gate de publication |

La réconciliation contient 2 + 6 + 2 + 3 = 13 producteurs primaires, sans
recouvrir les AC S-005 ou S-007.

### S-006 Risks and Rollback

| Risque | Réduction | Retour arrière |
|---|---|---|
| deux rôles écrivent le rapport | délégation sans handle et fan-in unique | rejeter les résultats et conserver l'ancien rapport |
| une revue technique devient une gate humaine | verdict explicitement informatif | retirer le skill sans bloquer les opérations Git |
| ship exécute la commande affichée | aucune primitive d'exécution ou réseau | refuser le plan et retirer le skill |
| plan partiel publié après précondition FAIL | validation complète avant remplacement atomique | conserver le plan précédent intact |
| profil divergent ou hors ordre | parité et dépendances T-020/T-023 | fermer la PR 0.8.0 et conserver 0.7.0 |

### S-006 Open Questions

- (aucune)

### S-006 Resolved Questions

- **Décision autonome — quatre tâches :** séparer les commandes, l'audit et la
  distribution préserve leurs scopes, dépôts et retours arrière.
- **Décision autonome — revue non humaine :** `/sdd-review` reste une commande
  du produit; aucune demande, attente ou approbation de reviewer n'est ajoutée
  aux PR de migration.
- **Décision autonome — sécurité par absence de capacité :** `/sdd-ship` ne
  reçoit aucune primitive d'exécution de déploiement, plutôt que de filtrer une
  liste fragile de commandes dangereuses.

### S-006 Design Sign-off

- [x] Les 13 AC possèdent un producteur primaire unique.
- [x] Le DAG est acyclique et l'ordre review avant ship est explicite.
- [x] Les scopes T-021/T-022 sont disjoints et les writers uniques sont nommés.
- [x] Sécurité, rollback, fan-in, données et stacks N/A sont décrits.
- [x] Aucune question ouverte ni nouvel ADR n'est requis.

## Conception détaillée : S-007 — E2E local complet et candidat 0.9.0

### S-007 Architecture Overview

S-007 étend le runner E2E existant dans un dépôt temporaire marqué et
supprimable, depuis `/sdd-onboard` jusqu'à `/sdd-ship`. Deux modules de scénario
disjoints utilisent le runtime Hermes canonique : l'un exécute réellement les
writers backend et frontend en concurrence et mesure leurs intervalles ; l'autre
injecte une panne ou un timeout, vérifie l'attente des dépendances et reprend le
fan-in transactionnel. Le runner agrège ensuite ces preuves avec le cycle
complet des commandes et les enveloppes Git/Kanban propres à chaque tâche. Un
audit source précède la copie exacte dans le profil candidat 0.9.0.

Cette conception réutilise ADR-001 à ADR-005. Elle n'ajoute ni ordonnanceur,
endpoint, persistance, reviewer humain, merge automatique, VPS ou déploiement.

### S-007 ADRs

- ADR-001 conserve Hermes Kanban comme ordonnanceur unique.
- ADR-002 impose deux writers au maximum.
- ADR-003 impose issue, carte, branche, worktree, session et PR par tâche.
- ADR-004 impose le writer unique et le fan-in transactionnel.
- ADR-005 impose la reprise idempotente et compatible.
- Aucun nouvel ADR : le bac à sable supprimable, les scénarios attendus et le
  candidat 0.9.0 sont imposés par la spécification.

### S-007 Component Map

| Frontière | Composant | Responsabilité | Tâche |
|---|---|---|---|
| Concurrence E2E | `hermes/e2e/parallel_scenario.py` | lancer deux processus writers disjoints, mesurer overlap/capacité, sérialiser un conflit | T-025 |
| Reprise E2E | `hermes/e2e/recovery_scenario.py` | attendre fusion/go, injecter échec/timeout, conserver le pair et reprendre le fan-in | T-026 |
| Runner complet | `hermes/e2e/run_sdd_e2e.py` | traverser onboard→ship dans un dépôt jetable et agréger les preuves | T-027 |
| Audit source | `hermes/scripts/test_sdd_s007_contract.py` et docs | vérifier commandes, onze AC, DAG, sécurité et surfaces exécutables | T-028 |
| Distribution | profil Hermes 0.9.0 | copier exactement le runner et publier le candidat après gates | T-029 |

### S-007 Module Boundaries

- `parallel_scenario` reçoit des tâches déjà validées et appelle l'admission,
  les leases et les enveloppes existants ; il ne planifie rien lui-même.
- `recovery_scenario` pilote uniquement les injections et oracles de reprise ;
  le journal, CAS, verrou et synthesizer restent ceux du runtime canonique.
- Les deux scénarios écrivent seulement dans leurs sous-arbres du dépôt E2E et
  dans les journaux task-local ; seul le synthesizer écrit les artefacts partagés.
- Le runner principal crée et valide la sentinelle avant toute suppression. Un
  run échoué est conservé par défaut et repris explicitement.
- Toute preuve persistée utilise des identifiants relatifs et expurgés ; aucun
  token, contenu métier ou chemin absolu n'entre dans les artefacts.

```text
T-024 profil 0.8.0 ─┬─> T-025 concurrence ─┐
                     └─> T-026 reprise ─────┤
                                            └─> T-027 runner onboard→ship
                                                  └─> T-028 audit source
                                                        └─> T-029 profil 0.9.0
```

T-025 et T-026 sont développées sur des branches, worktrees, sessions, issues,
cartes et PR distincts. T-027 attend que leurs deux PR soient fusionnées après
go explicite. Un conflit de chemin observé dans le scénario est sérialisé.

### S-007 Execution and Evidence Model

| Objet | Champs principaux | Producteur | Invariant |
|---|---|---|---|
| Intervalle writer | task, stack, start monotone, end monotone | processus backend/frontend | overlap strictement positif, pic ≤ 2 |
| Enveloppe de tâche | issue, card, branch, worktree, session, PR | pont canonique | identités uniques et idempotentes |
| Injection | task, kind, phase, attempt | scénario reprise | échec/timeout local et déterministe |
| Preuve conservée | task, files, Test-IDs, gate, journal | worker vert | inchangée lorsque le pair échoue |
| Fan-in | old/new generation, CAS, marker | synthesizer unique | ancien ou nouveau complet, jamais mélangé |
| Rapport E2E | commands, tasks, overlap, recovery, result | runner | données relatives expurgées |

Le temps monotone sert uniquement à établir l'ordre et l'intersection des
intervalles ; aucun seuil de performance ou SLO n'est inventé.

### S-007 Local Git and Command Lifecycle

Le dépôt jetable contient une fixture Spring et une fixture React/Next.js. Pour
chaque tâche, les adaptateurs matérialisent issue, carte Kanban, branche
`sdd/<feature>/<task>-<slug>`, worktree, session et PR en brouillon puis prête.
Le scénario observe les checks et le go comme données contrôlées. Il n'appelle
jamais un merge et n'accède à aucun GitHub ou VPS externe.

Le parcours traverse successivement aide, onboarding, harness, spécification,
revue de spécification, plan Epic/détaillé, build parallèle, simplification,
tests, validation, revue technique SDD et préparation ship. Les commandes
dépendantes attendent les fan-in requis ; ship ne déploie rien.

### S-007 Data, API and Security Posture

- Aucun endpoint HTTP ou contrat OpenAPI n'est ajouté par la migration ; les
  fichiers Spring/Next de la fixture sont des cibles jetables du test.
- Aucune entité, table ou migration n'est ajoutée ; Flyway/Liquibase sont N/A.
- Aucune authentification réseau n'est nécessaire. Aucun secret ni credential
  n'est fourni au runner.
- Les processus sont limités à deux writers. Les analyses internes restent en
  lecture seule et les gates lourdes demeurent sérialisées par le runtime.
- Les suppressions sont refusées hors de la racine temporaire portant la
  sentinelle exacte du run.

### S-007 Test Strategy

1. T-025 échoue d'abord faute de scénario, puis lance réellement les writers
   backend/frontend disjoints, mesure l'overlap et le pic de deux, et sérialise
   une paire ayant un fichier commun.
2. T-026 échoue d'abord faute de scénario de reprise, puis bloque une tâche
   dépendante avant fusion/go, injecte échec et timeout, conserve le pair vert,
   reprend sans doublon et vérifie le fan-in ancien/nouveau complet.
3. T-027 étend le runner du plan au ship dans un dossier supprimable et vérifie
   le lifecycle issue→carte→branche→worktree→session→PR pour chaque tâche.
4. T-028 manifeste exactement onze AC et exige toutes les commandes installées,
   les preuves exécutables, l'absence de reviewer humain, merge, VPS et deploy.
5. T-029 exécute les mêmes suites dans le layout profil, prouve la parité et
   publie les métadonnées 0.9.0 uniquement après gates et go explicite.

### S-007 Detailed AC Reconciliation

| Groupe | Producteur primaire | Preuve prévue |
|---|---|---|
| AC-156, AC-219, AC-227 | T-025 | processus concurrents, overlap monotone et pic de deux |
| AC-157, AC-158, AC-228 | T-026 | attente fusion/go, conservation, reprise et fan-in atomique |
| AC-155, AC-218, AC-226 | T-027 | parcours complet dans une racine temporaire supprimable |
| AC-225 | T-028 | inventaire exact des commandes publiées et audit source |
| AC-159 | T-029 | profil candidat 0.9.0 après gate de publication |

La réconciliation contient 3 + 3 + 3 + 1 + 1 = 11 producteurs primaires.
Les scénarios couvrent aussi comme preuves secondaires les exigences de conflit,
Git et transaction AC-207 à AC-217, sans les réattribuer à S-007.

### S-007 Risks and Rollback

| Risque | Réduction | Retour arrière |
|---|---|---|
| faux parallélisme séquentiel | processus distincts et overlap monotone strict | rejeter T-025 et conserver le runner antérieur |
| plus de deux writers | compteur actif et admission canonique | terminer les processus du bac à sable et invalider le run |
| conflit de scope concurrent | oracle explicite de sérialisation | annuler le scénario, aucun fichier externe touché |
| panne d'un job effaçant l'autre | preuves immuables avant injection et comparaison après reprise | garder le run échoué pour diagnostic |
| mélange au fan-in | verrou, CAS, journal et marker canonique | restaurer l'ancien ensemble complet |
| suppression trop large | racine dédiée, nom borné et sentinelle vérifiée | conserver le dossier en cas de doute |
| candidat divergent | parité exacte et gates profil | fermer la PR 0.9.0 et conserver 0.8.0 |

### S-007 Open Questions

- (aucune)

### S-007 Resolved Questions

- **Décision autonome — preuve de concurrence :** lancer des processus writers
  et comparer leurs intervalles monotoniques fournit un oracle déterministe.
- **Décision autonome — panne double :** exercer séparément une exception et un
  timeout couvre l'isolation sans rendre le scénario dépendant du hasard.
- **Décision autonome — environnement local :** les objets Git/Kanban sont
  matérialisés dans le dépôt jetable via les adaptateurs existants ; aucune
  mutation distante n'est nécessaire pour prouver leurs identités et transitions.
- **Décision autonome — absence de review humaine :** aucune demande ni attente
  de reviewer n'entre dans S-007 ; seul le go explicite reste une barrière de fusion.

### S-007 Design Sign-off

- [x] Les onze AC possèdent un producteur primaire unique.
- [x] Le DAG est acyclique, les deux tâches parallèles ont des scopes disjoints.
- [x] Le conflit, la dépendance, l'échec, le timeout et le fan-in ont des oracles.
- [x] Données, sécurité, rollback, Git/Kanban et limites de capacité sont décrits.
- [x] Aucune question ouverte ni nouvel ADR n'est requis.
