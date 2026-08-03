# Checklist de clarté embarquée

Appliquer seulement les catégories qui rendent le fichier immédiatement plus
lisible, sans changer son comportement :

1. remplacer les ternaires imbriqués par des **conditions** explicites ;
2. préférer des **boucles lisibles** aux chaînes difficiles à suivre ;
3. intégrer les **helpers** à usage unique dont le nom n'apporte rien ;
4. remplacer les **options** booléennes par des opérations distinctes ;
5. employer des **noms** précis issus du domaine ;
6. retirer les **abstractions** prématurées ;
7. préférer les **retours anticipés** aux imbrications profondes ;
8. supprimer le **code mort** sans consommateur réel ;
9. extraire les **littéraux répétés** au moins deux fois dans le fichier.

Ne jamais supprimer un test, affaiblir une assertion, modifier une API publique
entre modules ou étendre le périmètre pour satisfaire cette checklist.
