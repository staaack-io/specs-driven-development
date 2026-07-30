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
