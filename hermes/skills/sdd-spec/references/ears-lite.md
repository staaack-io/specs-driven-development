# Rédaction EARS-lite

Chaque critère d'acceptation suit une seule des formes suivantes :

| Forme | Squelette |
| --- | --- |
| Universelle | Le système doit `<réponse>`. |
| Événementielle | Lorsque `<déclencheur>`, le système doit `<réponse>`. |
| Pilotée par l'état | Tant que `<état>`, le système doit `<réponse>`. |
| Fonctionnalité optionnelle | Lorsque `<fonctionnalité présente>`, le système doit `<réponse>`. |
| Comportement indésirable | Si `<condition indésirable>`, alors le système doit `<mesure>`. |

## Règles

1. Un `AC-NNN` contient une condition et un résultat.
2. Un identifiant reste stable et n'est jamais réutilisé.
3. Un critère décrit un comportement observable, jamais une classe, une table,
   une bibliothèque ou un détail d'implémentation.
4. Une exigence vague devient mesurable ou se transforme en `Q-NNN`.
5. Une décision absente devient une question, jamais une valeur par défaut.
6. Une bascule visible nécessite une question sur le feature flag et la
   procédure de retour arrière, sauf dérogation explicite.

Avant de finaliser chaque critère, vérifier qu'un testeur peut écrire un scénario
Étant donné/Quand/Alors sans poser de nouvelle question.
