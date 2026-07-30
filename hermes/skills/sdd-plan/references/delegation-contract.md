# Contrat de délégation architecturale

Le sous-agent effectue une analyse en lecture seule. Il ne peut ni interroger
l'utilisateur ni écrire un artefact.

## Appel attendu

Utiliser un enfant `leaf` avec un objectif semblable à :

```text
Analyser la fonctionnalité approuvée comme architecte <stack>. Inspecter le
projet en lecture seule et retourner une proposition conforme au contrat.
Ne modifier aucun fichier. Ne choisir aucune décision absente des sources.
```

Le champ `context` doit contenir toutes les informations nécessaires : rôle,
racine du projet, feature-id, AC, questions résolues, verdict, preuves de stack,
contraintes et chemins pertinents. En reprise, ajouter le contenu de
`03-design.md`, de `04-tasks.md` s'il existe, les questions de planification et
les demandes `CR-NNN` avec leur statut.

## Sortie obligatoire

Retourner un unique bloc JSON valide :

```json
{
  "status": "ready | needs-input | blocked",
  "role": "spring-architect | react-nextjs-architect",
  "stack": "spring | react-nextjs",
  "files_modified": [],
  "evidence_files_read": [],
  "open_questions": [
    {
      "id": "Q-NNN",
      "question": "...",
      "why_it_matters": "...",
      "candidate_options": ["..."]
    }
  ],
  "architecture": {
    "overview": "...",
    "components": [],
    "boundaries": [],
    "api_and_data": [],
    "security": [],
    "observability": [],
    "testing": [],
    "risks_and_rollback": []
  },
  "adr_candidates": [],
  "tasks": [
    {
      "id": "T-001",
      "title": "...",
      "stack": "spring | react-nextjs",
      "ac_ids": ["AC-001"],
      "test_ids": ["T-001-T1"],
      "files_in_scope": [],
      "depends_on": [],
      "gates": [],
      "rollback": "..."
    }
  ]
}
```

## Règles

- Dans une délégation full-stack, `id`, `test_ids` et `depends_on` sont locaux
  au rôle enfant. Le parent doit les qualifier puis les renuméroter globalement.
- `ready` exige zéro question ouverte.
- `needs-input` exige au moins une question et ne doit pas inventer de réponse.
- `blocked` explique une preuve manquante ou une contradiction.
- Les chemins proposés doivent provenir de la structure existante ou être des
  chemins concrets de nouveaux fichiers cohérents avec cette structure.
- Le sous-agent ne crée ni ID d'AC ni comportement métier.
- Le parent reste l'unique auteur des artefacts.
