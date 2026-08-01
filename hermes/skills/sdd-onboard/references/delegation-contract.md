# Contrat de délégation d'onboarding

Chaque rôle reçoit un contexte autonome et retourne un seul objet :

```json
{
  "role": "spring-onboarding | react-nextjs-onboarding",
  "status": "ready | needs-input | blocked",
  "files_read": ["chemin/relatif"],
  "files_modified": [],
  "commands_executed": [],
  "modules": [],
  "architecture": [],
  "conventions": [],
  "observed_debt": [],
  "unknowns": [],
  "confidence_limits": [],
  "questions": []
}
```

## Invariants

- Lecture seule : `files_modified` vaut exactement `[]`.
- Aucun build, test, lint, serveur, migration ou téléchargement.
- Aucun sous-agent supplémentaire.
- Aucun dialogue direct avec l'utilisateur.
- Chaque fait cite un chemin relatif lu.
- Une absence de preuve devient une inconnue, jamais une recommandation choisie.
- Aucun chemin absolu, secret, environnement ou contenu d'authentification dans
  la sortie.

Le rôle ne crée aucun fichier. L'agent principal valide, fusionne et écrit les
candidats.
