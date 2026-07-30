# Contrat des tâches TDD

Chaque tâche :

1. possède un identifiant stable `T-NNN` ;
2. couvre au moins un `AC-NNN` ;
3. possède au moins un `Test-ID` ;
4. liste des chemins concrets dans `Files in scope` ;
5. déclare ses dépendances sans cycle ;
6. liste les portes réellement disponibles dans le projet ;
7. explique son retour arrière ;
8. représente environ 1 à 4 heures de travail.

Une tâche qui modifie du code de production inclut au moins un fichier de test.
Les tests sont listés avant les fichiers de production pour rendre le cycle TDD
explicite.

Ordonner les tâches selon leurs dépendances. Si deux tâches touchent le même
fichier, la seconde dépend de la première. Ne jamais utiliser `**/*` ou un
dossier entier comme périmètre.

Chaque AC doit apparaître dans au moins une tâche. Ne créer aucun AC pendant le
découpage.

## Normalisation full-stack

Lorsque plusieurs architectes retournent des tâches :

1. qualifier chaque ID local par son rôle, par exemple
   `spring-architect:T-001` et `react-nextjs-architect:T-001` ;
2. qualifier de la même façon chaque entrée `depends_on` avant la fusion ;
3. fusionner les tâches et dériver les dépendances inter-stack depuis les AC et
   décisions approuvés ainsi que le design proposé courant ; le design n'a pas
   besoin d'être déjà marqué `approved` à cette étape ;
4. effectuer un tri topologique. À priorité égale, ordonner par rôle
   `spring-architect`, puis `react-nextjs-architect`, puis par ID local ;
5. attribuer les IDs globaux `T-001`, `T-002`, etc. dans cet ordre ;
6. réécrire chaque dépendance avec l'ID global correspondant ;
7. renommer les tests de chaque tâche en `<Task-ID>-T1`, `<Task-ID>-T2`, etc.,
   selon leur ordre local ;
8. utiliser uniquement ces IDs globaux dans l'index, la couverture des AC,
   `04-tasks.md` et `.tdd-state.json`.

Refuser la sortie si un Task-ID ou Test-ID global est dupliqué, si une
dépendance ne correspond à aucune tâche, si le nombre de tâches change pendant
la normalisation ou si le graphe contient un cycle.

Exécuter cette normalisation avant de présenter le plan à l'utilisateur. Après
chaque `request-changes` qui modifie le design ou les tâches, la réexécuter avant
la nouvelle demande d'approbation afin que les arêtes inter-stack reflètent
toujours le design proposé courant.
