# Contrat de délégation de validation

Chaque validateur reçoit seulement sa stack et la liste normalisée des sources
modifiées. Il ne reçoit aucun handle, chemin ou callback d'écriture vers
`07-validation-report.md` ou `07a-traceability.md`.

Le validateur retourne un objet structuré en lecture seule : stack, gates,
couverture, score de mutation et preuves de traçabilité. Il ne lance aucune
commande shell libre, ne demande aucune review et ne crée aucun commit.

Le fan-in principal vérifie le type et l'unicité des résultats. Il est le seul
writer des deux rapports communs.
