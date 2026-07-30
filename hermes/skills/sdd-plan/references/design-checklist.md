# Checklist de conception et planification

## Entrées

- La revue contient exactement `verdict: approve`.
- Aucun `Q-NNN` n'est ouvert dans la spécification ou la revue.
- La stack et le périmètre sont prouvés par des marqueurs spécifiques au
  framework, pas seulement par un outil de build ou un nom de dossier générique.
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

## Reprise

- `--continue` a chargé le design et les tâches existants.
- Les questions résolues et demandes `CR-NNN` sont dans le contexte délégué.
- Chaque demande corrigée reste consignée avec statut, résolution et date.
- Aucun retour utilisateur ni identifiant de tâche inchangée n'est perdu.

## État TDD

- L'état TDD a été lu avant délégation et revérifié avant écriture.
- Un état commencé bloque toute modification du design, des tâches et de l'état.
- Un état vierge reste inchangé jusqu'à l'approbation du nouveau plan.
- Une erreur JSON ou une modification concurrente arrête la planification.

## Tâches

- Chaque AC est couvert.
- Chaque tâche possède Test-IDs, chemins concrets, dépendances et portes.
- Toute tâche de production contient un test.
- Le graphe de dépendances est acyclique.
- Deux tâches touchant le même fichier sont séquencées.
- En full-stack, Task-IDs et Test-IDs sont uniques après normalisation globale.
- Chaque dépendance réécrite cible une tâche existante et le nombre de tâches est
  conservé.

## Sortie

- Aucune question ouverte ne subsiste avant approbation.
- Aucune demande `CR-NNN` ne reste ouverte avant approbation.
- L'utilisateur approuve explicitement le plan.
- L'état TDD n'est créé qu'après approbation.
