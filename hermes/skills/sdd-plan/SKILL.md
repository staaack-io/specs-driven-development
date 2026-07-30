---
name: sdd-plan
description: "Concevoir et découper une spécification SDD approuvée."
---

# Planification SDD

Transformer une spécification approuvée en `03-design.md`, `04-tasks.md` et,
après approbation humaine, `.tdd-state.json`.

Cette commande orchestre des rôles internes. L'utilisateur ne lance jamais les
rôles directement.

## Entrée

- exiger un `feature-id` ;
- accepter `--continue <feature-id>` pour reprendre un plan existant ;
- si le travail nécessite plusieurs tranches verticales, des décisions
  transverses partagées ou plusieurs jalons, arrêter et recommander
  `/sdd-epic-plan` au lieu de réduire silencieusement l'Epic.

## Portes d'entrée

Avant toute délégation :

1. lire `.specs/<feature-id>/01-spec.md` ;
2. lire `.specs/<feature-id>/02-spec-review.md` ;
3. exiger `verdict: approve` ;
4. exiger zéro `Q-NNN` au statut `open` ;
5. refuser d'écraser un plan existant sans `--continue` ;
6. avec `--continue`, lire `03-design.md` et `04-tasks.md` lorsqu'ils existent ;
7. capturer le token de `.tdd-state.json`, présent ou absent, avec le garde
   atomique et appliquer la porte de protection avant toute délégation ;
8. ne jamais modifier les artefacts des étapes 1 et 2.

## Références

Toujours lire :

- [contrat de délégation](references/delegation-contract.md) ;
- [contrat des tâches](references/task-contract.md) ;
- [checklist de conception](references/design-checklist.md) ;
- [preuves de stack](references/stack-evidence.md) ;
- [atomicité de l'état TDD](references/tdd-state-atomicity.md) ;
- [modèle de conception](templates/design.template.md) ;
- [modèle de tâches](templates/tasks.template.md) ;
- [modèle d'état TDD](templates/tdd-state.template.json).

Lire ensuite le rôle correspondant :

- backend Spring : [architecte Spring](references/role-spring-architect.md) ;
- frontend React/Next.js :
  [architecte React/Next.js](references/role-react-nextjs-architect.md) ;
- full-stack : lire les deux rôles.

## Détection de la stack

Appliquer `references/stack-evidence.md`. Un fichier générique comme `pom.xml`,
`build.gradle*`, `src/main/java/`, `package.json`, `app/` ou `pages/` ne prouve
jamais à lui seul un framework.

- établir le périmètre de la fonctionnalité depuis les AC et décisions
  approuvées ;
- Spring : exiger une preuve Spring spécifique reliée à ce périmètre ;
- React/Next.js : exiger une preuve React ou Next.js spécifique reliée à ce
  périmètre ;
- full-stack : exiger une preuve spécifique et reliée au périmètre pour chaque
  famille.

Dans un monorepo, ne jamais déduire la stack de la seule présence d'un framework
ailleurs dans le dépôt. Si le lien entre les preuves et le périmètre de la
fonctionnalité reste ambigu, demander à l'utilisateur avant de déléguer.

Si aucune stack prise en charge n'est prouvée, arrêter avec `stack: unknown`,
présenter les fichiers inspectés et recommander `/sdd-onboard` si disponible.
Ne jamais choisir l'architecte le plus proche par défaut.

## Reprise d'un plan

Avec `--continue <feature-id>` :

1. exiger au moins un brouillon `03-design.md` ;
2. lire intégralement le design et, s'il existe, `04-tasks.md` ;
3. extraire les questions ouvertes, les questions résolues, la dernière décision
   utilisateur et toutes les demandes réelles `CR-NNN` ; ignorer la ligne
   explicite `(aucune)` du modèle ;
4. présenter les questions et demandes encore `open` avant de déléguer ;
5. inclure les artefacts précédents, leurs chemins et tous ces éléments dans le
   contexte autonome du sous-agent ;
6. après correction, conserver chaque `CR-NNN` et passer son statut à
   `resolved` avec un résumé et une date ; ne jamais supprimer l'historique ;
7. conserver les identifiants des tâches dont l'objectif ne change pas en
   appliquant la table d'origine et l'algorithme de reprise de
   `references/task-contract.md` ; ne jamais réattribuer tous les IDs depuis
   zéro.

Une reprise ne repart jamais uniquement de `01-spec.md` et
`02-spec-review.md`. Si le brouillon attendu est absent, refuser `--continue` et
expliquer qu'un premier `/sdd-plan <feature-id>` est requis.

## Protection de l'état TDD

1. Toujours exécuter `scripts/tdd_state_guard.py snapshot` comme décrit dans
   `references/tdd-state-atomicity.md` et conserver le token retourné, y compris
   lorsqu'il vaut `absent`.
2. Si l'état existe, exiger un JSON valide et considérer l'implémentation comme
   commencée si `active_task` n'est pas nul,
   si une tâche a une phase différente de `pending`, ou si un champ de preuve
   RED/GREEN n'est pas nul ;
3. si l'implémentation a commencé, refuser la planification avant toute
   délégation et ne modifier aucun artefact ; montrer la tâche et les preuves
   qui ont fermé la porte ;
4. si toutes les tâches sont `pending`, qu'aucune tâche n'est active et qu'aucune
   preuve n'existe, autoriser la reprise mais préserver le fichier jusqu'à
   l'approbation du nouveau plan ;
5. ne jamais remplacer l'état directement après une délégation : la validation
   finale et le remplacement appartiennent à la même section critique décrite
   dans `references/tdd-state-atomicity.md`.

Ne jamais migrer, vider ou recréer silencieusement un état commencé. Recommander
une nouvelle fonctionnalité ou un processus de changement distinct lorsque le
plan d'une implémentation commencée doit évoluer.

## Délégation en lecture seule

1. Préparer un contexte autonome contenant : chemin absolu du projet,
   `feature-id`, contenu des AC approuvés, décisions résolues, verdict de revue,
   preuves de stack, chemins des fichiers utiles, texte complet du rôle et, en
   reprise, le design, les tâches, les questions et les `CR-NNN` précédents.
   Demander explicitement aux rôles de conserver leurs IDs locaux pour les
   objectifs inchangés.
2. Appeler `delegate_task` avec un objectif explicite d'analyse architecturale
   en lecture seule, le contrat de sortie fourni dans
   `references/delegation-contract.md` et `max_iterations: 30`.
3. Pour du full-stack, déléguer les deux analyses dans un même lot. Elles
   peuvent être parallèles uniquement parce qu'aucun enfant n'écrit.
   Considérer leurs Task-IDs et Test-IDs comme locaux à leur rôle.
4. Après l'envoi, indiquer que l'analyse continue en arrière-plan et s'arrêter.
   Ne pas produire le plan avant le retour de délégation.

Les sous-agents ne peuvent pas interroger l'utilisateur. Toute question doit
revenir dans leur résumé pour être traitée par l'agent principal.

## Traitement du retour

1. Vérifier que chaque résultat déclare `files_modified: []`. Si un enfant a
   écrit, arrêter, montrer les chemins concernés et demander une décision.
2. Vérifier que le rôle et la stack correspondent aux preuves du projet.
3. En full-stack, fusionner les propositions dans un seul design, puis appliquer
   d'abord la validation des IDs locaux, puis la normalisation globale de
   `references/task-contract.md` avant d'écrire les tâches. Refuser les doublons
   locaux avant toute qualification ou renumérotation. Séparer les tâches par
   stack sans conserver deux IDs globaux identiques. Ne jamais créer deux
   fichiers concurrents. Dériver les dépendances inter-stack depuis les
   exigences approuvées et le design proposé courant, sans attendre que ce
   design porte déjà le statut `approved`.
4. Si le résultat vaut `needs-input`, écrire uniquement un brouillon de
   `03-design.md` contenant les faits et questions reçus, puis demander les
   décisions à l'utilisateur. Ne pas créer `04-tasks.md` ni l'état TDD.
5. Après les réponses, consigner les décisions dans le brouillon et relancer la
   délégation avec le contexte complet. Déplacer chaque question traitée vers
   `Resolved Questions` avec sa réponse et sa date.
6. Si le résultat vaut `ready`, l'agent principal écrit `03-design.md` et
   `04-tasks.md` à partir des modèles, seulement après avoir revérifié la porte
   de l'état TDD. Les sous-agents ne les écrivent pas.
7. Créer un ADR seulement lorsqu'au moins deux options plausibles existent et
   que la décision est explicitement prouvée. Une décision manquante devient
   une question, jamais un ADR inventé.
8. Appliquer la checklist et vérifier que chaque `AC-NNN` est couvert par une
   tâche. Vérifier aussi l'unicité globale des Task-IDs et Test-IDs, ainsi que
   l'existence de chaque dépendance réécrite.

## Approbation humaine

Après production du design et des tâches :

1. présenter stacks, rôles consultés, risques, ADR, nombre de tâches et matrice
   de couverture des AC ;
2. demander explicitement `approve` ou `request-changes` ;
3. avec `request-changes`, créer une entrée `CR-NNN` stable pour chaque demande,
   remplacer la ligne `(aucune)` lors de la première demande, l'inscrire au
   statut `open` dans `03-design.md`, conserver les artefacts en brouillon et
   proposer `/sdd-plan --continue <feature-id>` ;
4. avec `approve`, préparer le design approuvé et l'état vierge dans les deux
   fichiers candidats imposés par `references/tdd-state-atomicity.md`, puis
   appeler `commit-plan` avec le token capturé avant la délégation ;
5. si la comparaison-et-échange échoue, ne pas inscrire l'approbation et montrer
   l'état concurrent ; sinon seulement annoncer le plan comme approuvé.

Ne jamais déduire l'approbation du seul lancement de `/sdd-plan`.

## Contraintes d'écriture

- Écrire uniquement dans `.specs/<feature-id>/`.
- Toute écriture de `.tdd-state.json` passe par
  `scripts/tdd_state_guard.py` ; aucune commande ne le remplace directement.
- Ne jamais modifier `.tdd-state.json` lorsqu'une tâche est active, non
  `pending`, ou possède une preuve RED/GREEN.
- Ne jamais modifier le code, les tests, les dépendances ou la configuration du
  projet pendant la planification.
- Utiliser des chemins concrets dans `Files in scope`, jamais des globs.
- Une tâche de production doit inclure au moins un fichier de test.
- Sérialiser deux tâches qui modifient le même fichier.

## Terminé lorsque

- `03-design.md` et `04-tasks.md` sont approuvés ;
- chaque AC est couvert par au moins une tâche ;
- aucune question ouverte ne subsiste ;
- aucune demande `CR-NNN` ne reste `open` ;
- `.tdd-state.json` existe avec des tâches `pending` ;
- la prochaine commande est `/sdd-build T-001`, signalée comme non installée
  si nécessaire.
