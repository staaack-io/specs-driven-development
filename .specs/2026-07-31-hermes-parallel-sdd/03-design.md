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
