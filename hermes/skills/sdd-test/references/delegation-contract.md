# Contrat de délégation `/sdd-test`

Le rôle de test reçoit seulement la spécification nécessaire, un candidat de
plan et des chemins concrets sous `src/test/**`. Il ne reçoit aucun handle vers
`src/main/**`, `06-test-plan.md` ou un autre artefact partagé.

Le rôle retourne des tests candidats, leurs AC, types, noms et commandes. Le
garde principal valide les changements, exécute les gates et reste l'unique
writer de `06-test-plan.md`. Il publie le plan de façon atomique, puis lance la
régénération de la traçabilité. Cet ordre ne peut pas être inversé.

Toute écriture hors `src/test/**` est refusée. Aucun commit, push, merge, review,
accès VPS ou déploiement n'est délégué ou automatique.
