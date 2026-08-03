# Contrat du cycle TDD

Une invocation suit strictement `RED → GREEN → REFACTOR → SIMPLIFY`.

La transition hors de RED exige une preuve durable comprenant la signature du
test, une commande `argv` structurée, le code retour, l'échec attendu et la
sortie expurgée. Chaque événement comprend aussi les Test-IDs et les fichiers concernés.
Le coordinateur persiste cette preuve avant de déléguer GREEN.

Chaque transition est écrite avec `append_job_event` ou un writer injecté de
même sémantique. Son `event-id` est stable : une reprise identique est
idempotente et une preuve divergente est refusée.

Le chemin canonique valide l'état avant mutation, détient le lease exact pendant
le cycle et compare l'empreinte hors scope avant de le libérer en toutes
circonstances. La porte RED du runtime est appelée après l'événement RED durable
et avant toute délégation GREEN.
