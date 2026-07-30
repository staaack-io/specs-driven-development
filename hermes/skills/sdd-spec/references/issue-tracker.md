# Ingestion d'un ticket

## Sources prises en charge

| Source | Forme courante |
| --- | --- |
| Jira | `SHOP-1422` ou URL |
| GitHub Issue | `owner/repo#42` ou URL |
| GitHub Pull Request | `owner/repo!42` ou URL |
| Linear | `ENG-123` ou URL |
| Azure Boards | `AB#54321` ou URL |

Utiliser uniquement un connecteur ou serveur MCP réellement configuré. Sans
accès, demander à l'utilisateur de coller le contenu du ticket.

Capturer : titre, description, statut, labels, responsable, commentaires
pertinents, noms des pièces jointes, URL et horodatage de lecture. Ne jamais
affirmer qu'une information vient du ticket sans l'avoir lue.

Extraire les critères candidats uniquement du contenu récupéré. Une déduction
nécessaire mais absente de la source devient une `Q-NNN`.

Lors d'une nouvelle lecture d'un ticket déjà capturé, consigner les changements
sous `## Out-of-Band Inputs` avec leur date.
