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
      "expected_after_sha256": "sha256:<empreinte>"
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
  Le garde les exécute séquentiellement.
- Conserver les dépendances, scripts, versions, propriétés, plugins, profils,
  modules, migrations, règles et seuils déjà présents. Un ajout de dépendance
  exige une décision utilisateur préalable ; le plan ne constitue pas cette
  décision.
- Le plan et les candidats restent hors du dépôt. Ils ne contiennent aucun
  secret ni valeur d'environnement.
