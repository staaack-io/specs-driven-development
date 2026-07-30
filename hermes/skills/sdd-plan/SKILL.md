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
6. ne jamais modifier les artefacts des étapes 1 et 2.

## Références

Toujours lire :

- [contrat de délégation](references/delegation-contract.md) ;
- [contrat des tâches](references/task-contract.md) ;
- [checklist de conception](references/design-checklist.md) ;
- [modèle de conception](templates/design.template.md) ;
- [modèle de tâches](templates/tasks.template.md) ;
- [modèle d'état TDD](templates/tdd-state.template.json).

Lire ensuite le rôle correspondant :

- backend Spring : [architecte Spring](references/role-spring-architect.md) ;
- frontend React/Next.js :
  [architecte React/Next.js](references/role-react-nextjs-architect.md) ;
- full-stack : lire les deux rôles.

## Détection de la stack

Inspecter les fichiers réels sans inventer :

- Spring : `pom.xml`, `build.gradle*`, `src/main/java/` ou
  `.specs/_onboarding.md` le prouve ;
- React/Next.js : `package.json`, `next.config.*`, `app/`, `pages/` ou
  `.specs/_onboarding.md` le prouve ;
- full-stack : les deux familles sont prouvées.

Si plusieurs stacks existent mais que le périmètre de la fonctionnalité reste
ambigu, demander à l'utilisateur avant de déléguer.

## Délégation en lecture seule

1. Préparer un contexte autonome contenant : chemin absolu du projet,
   `feature-id`, contenu des AC approuvés, décisions résolues, verdict de revue,
   preuves de stack, chemins des fichiers utiles et texte complet du rôle.
2. Appeler `delegate_task` avec un objectif explicite d'analyse architecturale
   en lecture seule, le contrat de sortie fourni dans
   `references/delegation-contract.md` et `max_iterations: 30`.
3. Pour du full-stack, déléguer les deux analyses dans un même lot. Elles
   peuvent être parallèles uniquement parce qu'aucun enfant n'écrit.
4. Après l'envoi, indiquer que l'analyse continue en arrière-plan et s'arrêter.
   Ne pas produire le plan avant le retour de délégation.

Les sous-agents ne peuvent pas interroger l'utilisateur. Toute question doit
revenir dans leur résumé pour être traitée par l'agent principal.

## Traitement du retour

1. Vérifier que chaque résultat déclare `files_modified: []`. Si un enfant a
   écrit, arrêter, montrer les chemins concernés et demander une décision.
2. Vérifier que le rôle et la stack correspondent aux preuves du projet.
3. En full-stack, fusionner les propositions dans un seul design et séparer les
   tâches par stack. Ne jamais créer deux fichiers concurrents.
4. Si le résultat vaut `needs-input`, écrire uniquement un brouillon de
   `03-design.md` contenant les faits et questions reçus, puis demander les
   décisions à l'utilisateur. Ne pas créer `04-tasks.md` ni l'état TDD.
5. Après les réponses, consigner les décisions dans le brouillon et relancer la
   délégation avec le contexte complet.
6. Si le résultat vaut `ready`, l'agent principal écrit `03-design.md` et
   `04-tasks.md` à partir des modèles. Les sous-agents ne les écrivent pas.
7. Créer un ADR seulement lorsqu'au moins deux options plausibles existent et
   que la décision est explicitement prouvée. Une décision manquante devient
   une question, jamais un ADR inventé.
8. Appliquer la checklist et vérifier que chaque `AC-NNN` est couvert par une
   tâche.

## Approbation humaine

Après production du design et des tâches :

1. présenter stacks, rôles consultés, risques, ADR, nombre de tâches et matrice
   de couverture des AC ;
2. demander explicitement `approve` ou `request-changes` ;
3. avec `request-changes`, conserver les artefacts en brouillon et proposer
   `/sdd-plan --continue <feature-id>` ;
4. avec `approve`, inscrire la décision et la date dans `03-design.md`, puis
   créer `.tdd-state.json` avec toutes les tâches à `pending` et
   `active_task: null`.

Ne jamais déduire l'approbation du seul lancement de `/sdd-plan`.

## Contraintes d'écriture

- Écrire uniquement dans `.specs/<feature-id>/`.
- Ne jamais modifier le code, les tests, les dépendances ou la configuration du
  projet pendant la planification.
- Utiliser des chemins concrets dans `Files in scope`, jamais des globs.
- Une tâche de production doit inclure au moins un fichier de test.
- Sérialiser deux tâches qui modifient le même fichier.

## Terminé lorsque

- `03-design.md` et `04-tasks.md` sont approuvés ;
- chaque AC est couvert par au moins une tâche ;
- aucune question ouverte ne subsiste ;
- `.tdd-state.json` existe avec des tâches `pending` ;
- la prochaine commande est `/sdd-build T-001`, signalée comme non installée
  si nécessaire.
