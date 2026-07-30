# Développement piloté par les spécifications avec Spring, React et Next.js

Ce dépôt utilise le workflow de développement piloté par les spécifications
documenté dans `docs/methodology.md`. Ces instructions s’appliquent à Codex
pour chaque tâche.

## Surfaces du workflow Codex

- Les workflows réutilisables et les recommandations métier vivent dans des
  skills séparés sous `.agents/skills/<name>/SKILL.md`.
- Les agents du projet vivent sous `.codex/agents/<name>.toml`.
- Les modèles et checklists vivent sous `.codex/templates/` et
  `.codex/checklists/`.
- Les garde-fous du cycle de vie vivent dans `.codex/hooks.json` et
  `.codex/hooks/`.
- Le harness déterministe reste sous `.github/scripts/` ; ce dossier est une
  infrastructure, pas une intégration GitHub Copilot.

Invoquer explicitement les skills de workflow avec `$spec`, `$spec-review`,
`$epic-plan`, `$plan`, `$build`, `$test`, `$validate`, `$review`,
`$ship`, `$onboard`, `$wire-harness`, `$status`, `$help` ou
`$code-simplify`. Une demande en langage naturel peut activer les mêmes skills
via leur description.

Lorsqu’un skill de workflow désigne un agent responsable, déléguer cette phase à
l’agent de projet correspondant si les sous-agents Codex sont disponibles.
Garder les phases dépendantes séquentielles. Ne pas inventer de rôle et ne pas
combiner plusieurs skills en un seul.

## Documents de référence

Lire le document pertinent avant de modifier un artefact du workflow ou ses
règles :

- `docs/methodology.md` — phases et portes de contrôle ;
- `docs/harness-principles.md` — exigences d’auto-validation ;
- `docs/artifact-contract.md` — structure de `.specs/<feature-id>/` ;
- `docs/spec-format.md` — critères d’acceptation EARS-lite et questions
  ouvertes.

## Phases 1 à 3 : ne rien inventer

- Ne jamais choisir silencieusement un moteur de base de données, un mécanisme
  d’authentification, une enveloppe d’erreur, une règle de pagination, une unité,
  une devise, une politique de conservation ou toute autre exigence manquante.
- Consigner les décisions manquantes sous forme de `Q-NNN` dans
  `## Open Questions`, puis s’arrêter pour demander à l’utilisateur.
- Conserver les identifiants `AC-NNN`, `Q-NNN` et `T-NNN` stables ; ne
  jamais les renuméroter.
- Pour une Epic, produire `03-epic-design.md` et `03a-epic-roadmap.md` avant
  la conception détaillée et les tâches de chaque tranche.
- Ne pas avancer tant qu’un artefact antérieur contient des questions non
  résolues, sauf report explicite de l’utilisateur accompagné d’une justification
  consignée.

## Phase 4 : TDD et périmètre

- Ne jamais modifier `src/main/**` tant que la tâche active dans
  `.specs/<feature>/.tdd-state.json` ne contient pas un test en échec consigné.
- Modifier uniquement les fichiers déclarés dans `files_in_scope` pour la tâche
  active.
- Suivre rouge → vert → refactorisation → simplification pour les tâches backend
  et frontend.
- Ne jamais supprimer un test, retirer une assertion, abaisser un seuil de qualité
  ou ajouter un test désactivé sans explication.
- Ne jamais contourner la compilation ou la vérification avec
  `-DskipTests`, `-Dpit.skip`, `-Dcheckstyle.skip`, `-Dspotbugs.skip` ou
  `--no-verify`.
- Ne pas ajouter de dépendance de production ou de test sans l’accord explicite
  de l’utilisateur.

## Validation et revue

- Pendant `$validate` et `$review`, ne pas modifier le code de production ni
  les tests.
- Considérer l’absence d’un rapport configuré comme une erreur.
- Considérer un test ignoré sans raison documentée comme une erreur.
- Exiger que chaque dérogation référence un ADR.
- Utiliser `.github/scripts/harness.sh` comme point d’entrée commun en local et
  en CI.

## Limites de commit et de déploiement

- Ne jamais exécuter `git commit` ; montrer le diff et proposer à l’utilisateur
  un message de commit à exécuter lui-même.
- Ne jamais pousser ni déployer sans demande explicite de l’utilisateur.
- `$ship` prépare un plan et une commande pour l’utilisateur ; il ne déploie
  rien.

## Conventions de stack

Lors d’une modification Spring, appliquer séparément les skills
`spring-boot-4-conventions`, `spring-security-baseline` et les skills de test
ou d’architecture pertinents. Lors d’une modification React ou Next.js,
appliquer `react-nextjs-developer` et l’agent React/Next.js de la phase active.
Ne pas recopier les recommandations d’un skill dans un autre ; charger chaque
skill pertinent indépendamment.
