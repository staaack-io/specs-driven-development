# Contrat de délégation Epic

Confier uniquement une analyse en lecture seule. Fournir le rôle complet, la
racine du projet, le `feature-id`, les AC, les décisions résolues, les preuves de
stack et les candidats précédents. Interdire toute question directe à
l'utilisateur et toute écriture.

Exiger un unique objet JSON :

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
  "epic": {
    "scope": [],
    "boundaries": [],
    "shared_decisions": [],
    "cross_cutting_constraints": [],
    "risks": [],
    "adr_candidates": []
  },
  "slices": [
    {
      "id": "S-001",
      "outcome": "...",
      "ac_ids": ["AC-001"],
      "depends_on": [],
      "milestone": "M-001",
      "entry_criteria": [],
      "exit_criteria": [],
      "risks": []
    }
  ]
}
```

Appliquer ces règles :

- déclarer `ready` uniquement sans question ouverte ;
- déclarer `needs-input` avec au moins une question stable ;
- considérer les IDs de tranche et de question comme locaux au rôle ;
- produire des `Q-NNN` uniques dans chaque sortie ; le parent les qualifie par
  rôle, refuse les doublons, puis attribue les IDs globaux ;
- ne créer aucun AC et ne choisir aucune décision absente des sources ;
- proposer des tranches verticales, observables et testables ;
- retourner `files_modified: []` même lorsqu'aucun fichier n'a été trouvé ;
- expliquer toute contradiction ou preuve manquante avec `blocked`.
