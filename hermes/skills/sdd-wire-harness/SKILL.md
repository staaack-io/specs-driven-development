---
name: sdd-wire-harness
description: "Planifier, câbler et vérifier transactionnellement le harness qualité d’un projet onboardé. Utiliser avec /sdd-wire-harness [feature-id] [--dry-run] pour une stack Spring, React ou Next.js prouvée."
---

# Câblage du harness SDD

Configurer uniquement les portes qualité prouvées par l'onboarding. Déléguer
l'analyse au rôle intégrateur en lecture seule, puis conserver l'agent Hermes
principal comme unique écrivain. Ne jamais déployer.

## Entrée

Accepter exactement :

```text
/sdd-wire-harness [feature-id] [--dry-run]
```

- sans `feature-id`, câbler les modules prouvés du dépôt ;
- avec `feature-id`, exiger le dossier réel `.specs/<feature-id>/` ;
- refuser tout autre argument, chemin, glob ou option ;
- avec `--dry-run`, n'écrire aucun fichier, verrou, candidat ou journal et
  n'exécuter aucune gate.

## Références obligatoires

Lire avant toute action :

- [contrat du plan](references/plan-contract.md) ;
- [rôle intégrateur](references/role-harness-integrator.md) ;
- [transaction et reprise](references/transaction-safety.md).

## Inspection déterministe

1. Résoudre la racine Git réelle. Refuser une racine ou `.specs` symbolique.
2. Exécuter :

   ```text
   python3 <skill>/scripts/harness_guard.py inspect \
     --project-root <racine> [--feature-id <feature-id>] [--dry-run]
   ```

3. Conserver exactement `git_sha`, `snapshot_token`, `stacks`, les preuves et
   `allowed_targets` retournés.
4. Exiger `_stack.json` au schéma 1, une confiance globale et par module
   `proved`, un manifeste directement dans le module déclaré et un gestionnaire
   de paquets prouvé pour React/Next.js.
5. Refuser Flyway et Liquibase ensemble, les ambiguïtés, les modifications
   utilisateur sans reçu exact et toute transaction incohérente.

En mode non sec, `inspect` récupère d'abord une transaction interrompue. En
mode sec, un journal en attente bloque : annoncer qu'une reprise non sèche est
requise au lieu d'écrire.

## Délégation en lecture seule

Appeler `delegate_task` une seule fois avec le texte complet du
[rôle intégrateur](references/role-harness-integrator.md), le résultat de
l'inspection, les manifests et les configurations autorisées. Fixer
`max_iterations: 30`.

Le sous-agent :

- lit les preuves et configurations ;
- propose les ajouts minimaux et les gates ;
- retourne `files_modified: []` ;
- ne crée aucun candidat, ne lance aucune commande et ne choisit aucune version,
  dépendance, suppression ou seuil sans preuve.

Après son retour, revérifier que le worktree et le token sont inchangés. Refuser
une sortie qui modifie un fichier, omet une stack prouvée ou propose une cible
absente de `allowed_targets`.

## Dry-run

Après la délégation, présenter en mémoire le plan proposé, les fichiers visés,
les gates pré/post et les décisions manquantes. Ne créer ni dossier temporaire,
ni plan JSON, ni configuration candidate. S'arrêter avec `dry_run: true`.

## Préparation par l'écrivain unique

En mode non sec :

1. Créer un dossier candidat privé hors du dépôt.
2. Copier dans ce dossier uniquement les fichiers cibles proposés et appliquer
   les changements minimaux. Ne jamais écrire directement dans le projet.
3. Préserver toutes les dépendances, versions, scripts, plugins, profils,
   modules, propriétés, workspaces, overrides, exports, seuils, migrations et
   règles existants. Déclarer chaque clé JSON ajoutée dans
   `approved_additions` et citer la réponse utilisateur exacte sous
   `approval_evidence`. Demander l'accord explicite avant toute nouvelle
   dépendance.
4. Ne placer aucun secret, chemin absolu, commande de déploiement, téléchargement
   exécutable, `sudo`, suppression récursive ou contournement de tests dans les
   candidats.
5. Écrire `plan.json` conformément au [contrat du plan](references/plan-contract.md),
   avec empreintes avant/après, chemins concrets et deux gates sérialisées par
   module : `pre-commit` et `post-commit`.

## Validation et publication

Valider d'abord sans écrire dans le projet :

```text
python3 <skill>/scripts/harness_guard.py validate \
  --project-root <racine> [--feature-id <feature-id>] \
  --expected-head <git_sha> --expected-token <snapshot_token> \
  --plan <plan.json> --candidate-dir <dossier> --dry-run
```

Présenter le plan structuré. S'il est conforme, publier une seule fois :

```text
python3 <skill>/scripts/harness_guard.py commit \
  --project-root <racine> [--feature-id <feature-id>] \
  --expected-head <git_sha> --expected-token <snapshot_token> \
  --plan <plan.json> --candidate-dir <dossier>
```

Le garde conserve le verrou global pendant toute validation, y compris un
replay. Il exécute réellement et séquentiellement les gates `pre-commit` dans
un bac à sable temporaire de `HEAD` contenant les candidats, les fichiers sûrs
en attente et une copie des `node_modules` existants. Le gestionnaire Node doit
être celui prouvé et disponible sur `PATH` ; ne jamais installer ni simuler un
wrapper. Il revérifie ensuite le CAS, journalise les versions, remplace
atomiquement les configurations et réexécute les commandes strictement
identiques en phase `post-commit` dans un nouveau bac à sable. Les empreintes de
tout le dépôt, fichiers ignorés et métadonnées Git pertinentes comprises,
doivent rester identiques hors cibles. Un échec restaure l'ensemble précédent.
Deux gates lourdes ne s'exécutent jamais simultanément.

Sur succès, supprimer uniquement le dossier candidat exact. Sur refus ou
échec, le préserver et annoncer son chemin. Un replay exact retourne
`unchanged: true` sans réécrire ni relancer les gates.

## Limites d'écriture

Autoriser seulement :

- Spring Maven : `pom.xml`, `checkstyle.xml`,
  `dependency-check-suppressions.xml`, `config/checkstyle/checkstyle.xml` dans
  le module prouvé ;
- React/Next.js : `package.json`, `tsconfig.json`, configurations ESLint,
  Vitest, Jest ou Next dans le module prouvé ;
- commun : `.github/scripts/harness.sh`.

Ne modifier ni code produit, ni test, ni artefact `.specs`, ni ADR, ni lockfile,
ni workflow CI. Ne jamais lancer `spotless:apply`, installer une dépendance,
publier, pousser, fusionner ou déployer.

## Terminé lorsque

- chaque stack prouvée possède une gate pré et post réussie ;
- seules les configurations autorisées ont changé ;
- les empreintes avant/après et sorties de gates sont structurées ;
- le journal est absent et le reçu namespacé par worktree, branche et HEAD
  permet reprise et idempotence sans collision ;
- le résumé précise les fichiers modifiés, les gates exécutées et l'absence de
  déploiement.
