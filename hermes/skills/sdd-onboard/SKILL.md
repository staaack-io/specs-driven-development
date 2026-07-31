---
name: sdd-onboard
description: "Analyser un projet existant et créer sa référence SDD sans modifier le produit."
---

# Onboarding SDD

Analyser statiquement le dépôt courant, déléguer les lectures spécialisées et
publier ensemble les cinq artefacts globaux d'onboarding. Cette commande est
diagnostique : elle ne câble pas le harness et ne lance aucune porte lourde.

L'agent Hermes principal est l'unique écrivain. Les rôles délégués sont des
lecteurs spécialisés, pas des commandes utilisateur.

## Entrée

- sans argument, analyser la racine Git courante ;
- accepter `--continue` pour reprendre le dialogue après une question ou une
  interruption ; cette option relance `inspect`, dont la récupération est
  automatique, et n'est pas transmise comme option au garde ;
- refuser un chemin qui n'est pas exactement la racine du worktree Git ;
- ne jamais demander un commit préalable, mais capturer le SHA courant.

## Références obligatoires

Lire avant toute action :

- [contrat des artefacts](references/artifact-contract.md) ;
- [classification et preuves](references/classification.md) ;
- [contrat de délégation](references/delegation-contract.md) ;
- [transaction et reprise](references/transaction-atomicity.md) ;
- [rôle Spring](references/role-spring-onboarding.md) lorsqu'une preuve Spring
  existe ;
- [rôle React/Next.js](references/role-react-nextjs-onboarding.md) lorsqu'une
  preuve React ou Next.js existe ;
- [modèle d'onboarding](templates/onboarding.template.md) ;
- [modèle de stack](templates/stack.template.json) ;
- [modèle de baseline](templates/baseline.template.json) ;
- [modèle de conception initiale](templates/starter-design.template.md) ;
- [modèle de dette](templates/known-debt.template.md).

## Porte initiale et inspection déterministe

1. Résoudre le chemin absolu de la racine du projet, sans l'inscrire dans les
   artefacts.
2. Exécuter le garde embarqué :

   ```text
   python3 <skill>/scripts/onboarding_guard.py inspect \
     --project-root <racine-absolue>
   ```

3. Conserver exactement `git_sha`, `snapshot_token`, `workspace` et
   `inspection` retournés. Ils forment la preuve et la porte CAS du run.
4. Si le garde signale une transaction récupérée, annoncer
   `rolled-back | committed` avant de continuer.
5. Refuser si le garde signale :
   - une modification suivie ou non suivie hors des cinq artefacts déjà produits ;
   - une modification indexée, même dans `.specs/` ;
   - un verrou détenu par un autre processus ;
   - un journal ou un marqueur ambigu ;
   - un lien symbolique à la place de la racine, de `.specs/` ou d'un artefact.

Le probe ne lance que des lectures de fichiers, `git rev-parse` et
`git status`. Ne jamais exécuter Maven, Gradle, npm, pnpm, Yarn, Bun, Docker,
un script du dépôt ou une commande trouvée dans un manifeste pendant
`/sdd-onboard`.

## Classification et routage

Appliquer `references/classification.md` sans déduire un framework d'un
manifeste générique :

- une dépendance ou un plugin Spring spécifique prouve Spring ;
- les dépendances `react` ou `next` prouvent React ou Next.js ;
- un `pom.xml`, `build.gradle*`, `package.json`, `src/` ou `app/` générique ne
  suffit pas ;
- la présence de vrai code produit classe le dépôt `brownfield` ; son absence
  le classe `greenfield` ;
- une détection limitée ou contradictoire reste `limited | unknown`, avec les
  chemins lus et les limites. Ne jamais choisir silencieusement la stack la plus
  proche.

Refuser une combinaison Flyway et Liquibase dans le même module Spring. Pour
les autres ambiguïtés qui changeraient la classification ou les commandes,
retourner la question à l'utilisateur avant toute délégation.

## Délégation en lecture seule

1. Construire un contexte autonome avec le chemin absolu du projet, le SHA,
   l'inventaire du probe, les chemins de preuve et le texte complet de chaque
   rôle applicable. Le chemin absolu sert uniquement à la lecture et ne doit
   jamais apparaître dans la sortie finale.
2. Appeler `delegate_task` dans un même lot avec `max_iterations: 30` :
   - rôle `spring-onboarding` pour chaque module Spring prouvé ;
   - rôle `react-nextjs-onboarding` pour chaque module React ou Next.js prouvé.
3. Demander explicitement une analyse en lecture seule et le contrat de sortie
   de `references/delegation-contract.md`.
4. Les analyses peuvent être parallèles parce qu'aucun enfant n'écrit.
5. Si aucune stack spécialisée n'est prouvée, l'agent principal consolide
   l'inventaire générique et marque la confiance `limited`; il n'invente pas de
   rôle.

Après le retour, vérifier chaque résultat avant de rédiger :

- `files_modified` vaut exactement `[]` ;
- `commands_executed` ne contient aucune porte, build ou test ;
- chaque fait cite un chemin relatif présent dans l'inventaire ou effectivement
  lu ;
- le rôle n'a pas transformé une absence de preuve en choix.

Si un enfant a écrit, si `files_modified` n'est pas vide ou si le worktree a
changé, arrêter. Le garde de commit effectuera aussi cette vérification.

## Consolidation par l'écrivain unique

L'agent principal crée un dossier candidat temporaire privé en dehors du projet
et y écrit exactement :

- `_onboarding.md` ;
- `_stack.json` ;
- `_baseline.json` ;
- `_starter-design.md` ;
- `_known-debt.md`.

N'écrire aucun candidat directement sous `.specs/`. Remplir les modèles avec :

- le SHA exact et la classification ;
- les modules, stacks et versions prouvés, sans valeur par défaut ;
- les commandes de validation configurées, avec le fichier qui les prouve ;
- l'architecture et les conventions observées ;
- la dette observée séparée des inconnues ;
- les limites de confiance et les preuves relatives.

`_baseline.json` est une référence **statique** avec
`heavy_gates_executed: false` et `status: not-run`. Une commande détectée est
documentée mais jamais exécutée. Sa mesure appartient à `/sdd-wire-harness` ou
à une future validation explicitement autorisée.

Ne jamais copier dans les artefacts :

- un chemin absolu ;
- une variable d'environnement, un secret ou une valeur d'authentification ;
- le contenu arbitraire d'un script de validation ;
- une métrique de test, couverture, mutation, qualité ou vulnérabilité qui n'a
  pas été mesurée.

## Publication transactionnelle

Appeler une seule fois :

```text
python3 <skill>/scripts/onboarding_guard.py commit \
  --project-root <racine-absolue> \
  --expected-head <git_sha> \
  --expected-token <snapshot_token> \
  --candidate-dir <dossier-candidat-absolu>
```

Le garde :

- revérifie le SHA, le worktree et tous les candidats ;
- prend le verrou exclusif ;
- compare le token de snapshot ;
- journalise les anciennes et nouvelles versions des cinq fichiers ;
- remplace chaque fichier atomiquement ;
- écrit le marqueur de commit en dernier ;
- fsync les fichiers et dossiers ;
- produit un reçu qui autorise une reprise ou un second run identique.

Sur succès, supprimer uniquement le dossier candidat temporaire exact. Sur
échec, le préserver et annoncer son chemin pour la reprise. Ne jamais remplacer
un artefact à la main.

Un second run sans changement peut retourner `unchanged: true`. Il ne doit ni
dupliquer les sections ni modifier le produit.

## Écritures autorisées

Uniquement les cinq fichiers finaux sous `.specs/`. Le garde conserve son
verrou, son journal, son marqueur et son reçu dans le répertoire Git technique,
hors du contenu versionné.

Interdictions :

- modifier `src/`, les tests, un manifeste, une dépendance ou une configuration ;
- ajouter ou régler le harness ;
- exécuter les commandes découvertes ;
- créer un artefact de fonctionnalité numéroté ;
- laisser un enfant écrire un artefact partagé ;
- poursuivre après un état concurrent ou une preuve ambiguë.

## Terminé lorsque

- les cinq artefacts existent et portent le même SHA ;
- chaque stack, version, commande et affirmation architecturale possède une
  preuve relative ;
- les inconnues restent explicites ;
- le commit du garde a réussi ou confirmé un no-op idempotent ;
- le résumé indique qu'aucun code, test, manifeste ou gate lourd n'a été
  modifié ou exécuté ;
- la prochaine commande est `/sdd-spec <demande ou ticket>`, ou
  `/sdd-wire-harness` si l'utilisateur souhaite d'abord câbler et mesurer les
  portes et que cette commande est installée.
