# Adaptateur Hermes Agent

Ce dossier contient la source de l'adaptateur Hermes du framework SDD. Il est
développé séparément de l'intégration Codex existante afin de permettre une
migration progressive et des comparaisons fiables.

## Premier lot

Les skills suivants sont prêts à être copiés dans la distribution
`staaack-io/hermes-agent-profile-staaack` :

- `sdd-help` — aide en lecture seule ;
- `sdd-status` — état des fonctionnalités en lecture seule ;
- `sdd-spec` — création guidée de `01-spec.md`.

Les hooks ne font volontairement pas partie de ce lot. Ils seront activés après
leur conversion au protocole Hermes et la réussite de tests de blocage.

## Publication dans le profil

Le contenu de `hermes/skills/<nom>/` devient
`skills/<nom>/` dans le dépôt de distribution Hermes. Les dossiers de ressources
restent avec leur skill afin que le profil installé soit autonome.

Ne pas utiliser un lien direct vers `.agents/skills/` : ce dossier contient la
version Codex et ses chemins ne sont pas tous portables vers Hermes.

## Validation locale

Depuis la racine du dépôt :

```bash
python3 /chemin/vers/skill-creator/scripts/quick_validate.py hermes/skills/sdd-help
python3 /chemin/vers/skill-creator/scripts/quick_validate.py hermes/skills/sdd-status
python3 /chemin/vers/skill-creator/scripts/quick_validate.py hermes/skills/sdd-spec
```

La validation avec Hermes sur le VPS reste obligatoire avant publication d'une
version stable du profil.
