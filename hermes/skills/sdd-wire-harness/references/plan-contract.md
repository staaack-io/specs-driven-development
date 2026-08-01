# Contrat du plan de câblage

Le plan est un objet JSON au schéma 1. Tous les chemins utilisent `/`, sont
relatifs à la racine et ne contiennent ni glob, `..`, lien symbolique ou chemin
absolu.

```json
{
  "schema_version": 1,
  "git_sha": "<SHA inspecté>",
  "snapshot_token": "sha256:<token inspecté>",
  "feature_id": null,
  "changes": [
    {
      "path": "backend/pom.xml",
      "candidate": "backend/pom.xml",
      "action": "replace",
      "stack": "spring",
      "purpose": "Ajouter les portes Maven absentes",
      "expected_before_sha256": "sha256:<empreinte>",
      "expected_after_sha256": "sha256:<empreinte>",
      "approved_additions": ["$.scripts.test"],
      "approval_evidence": "user:<réponse exacte>"
    }
  ],
  "validation": [
    {
      "stack": "spring",
      "phase": "pre-commit",
      "argv": ["./mvnw", "verify"],
      "working_directory": "backend",
      "timeout_seconds": 900
    },
    {
      "stack": "spring",
      "phase": "post-commit",
      "argv": ["./mvnw", "verify"],
      "working_directory": "backend",
      "timeout_seconds": 900
    }
  ]
}
```

## Invariants

- Déclarer une seule entrée par cible et uniquement `create | replace`.
- Exiger une empreinte `absent` pour une création et l'empreinte exacte du
  fichier courant pour un remplacement.
- Faire correspondre `stack`, module, manifeste, `working_directory` et
  gestionnaire de paquets aux preuves de l'inspection.
- Déclarer exactement des arguments, jamais une chaîne shell. Refuser
  métacaractères, options de contournement et commandes de déploiement.
- Inclure au moins une gate `pre-commit` et `post-commit` par module prouvé.
  Les listes d'arguments, répertoires et timeouts doivent être strictement
  identiques entre les deux phases. Le garde les exécute séquentiellement.
- Conserver intégralement chaque valeur JSON existante, dont workspaces,
  overrides, resolutions, configuration pnpm, exports, Jest et ESLint, ainsi que
  les dépendances, scripts et versions. Lister exactement chaque nouvelle clé
  dans `approved_additions` avec une preuve `user:`. Inspecter aussi les scripts
  lifecycle `pre*` et `post*`.
- Conserver les propriétés, plugins, profils, modules, migrations, règles et
  seuils XML déjà présents.
- Le plan et les candidats restent hors du dépôt. Ils ne contiennent aucun
  secret ni valeur d'environnement.
