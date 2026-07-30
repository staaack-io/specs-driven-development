# Checklist de conception et planification

## Entrées

- La revue contient exactement `verdict: approve`.
- Aucun `Q-NNN` n'est ouvert dans la spécification ou la revue.
- La stack et le périmètre sont prouvés par des fichiers.
- Le mode Epic n'est pas requis.

## Architecture

- Les composants, frontières et responsabilités sont explicites.
- Les choix correspondent aux conventions existantes du projet.
- API, données, sécurité, observabilité et tests sont traités seulement lorsque
  la fonctionnalité les concerne.
- Les exigences non fonctionnelles sont mesurables et proviennent des sources.
- Chaque risque possède une réduction et un retour arrière.
- Toute décision non résolue devient une question.

## Délégation

- Chaque sous-agent a reçu un contexte autonome et le rôle approprié.
- Chaque sous-agent déclare `files_modified: []`.
- L'agent principal est le seul auteur de `03-design.md` et `04-tasks.md`.
- Les résultats full-stack sont fusionnés dans des artefacts uniques.

## Tâches

- Chaque AC est couvert.
- Chaque tâche possède Test-IDs, chemins concrets, dépendances et portes.
- Toute tâche de production contient un test.
- Le graphe de dépendances est acyclique.
- Deux tâches touchant le même fichier sont séquencées.

## Sortie

- Aucune question ouverte ne subsiste avant approbation.
- L'utilisateur approuve explicitement le plan.
- L'état TDD n'est créé qu'après approbation.
