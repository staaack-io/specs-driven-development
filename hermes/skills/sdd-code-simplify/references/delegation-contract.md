# Contrat de délégation de clarté

Le rôle reçoit un fichier à la fois avec son chemin relatif normalisé, le mode
`dry-run`, la checklist et les argv de tests validés.

Il peut proposer ou modifier uniquement ce fichier. Il ne reçoit aucun handle
en écriture vers `04-tasks.md`, `.tdd-state.json` ou
`05-implementation-log.md`. Il ne lance aucune commande Git, ne crée aucun commit
et ne sollicite aucune review.

Le garde principal reste propriétaire du lease, des empreintes, des tests et
de la restauration atomique du fichier courant en cas de régression.
