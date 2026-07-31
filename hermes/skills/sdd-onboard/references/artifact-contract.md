# Contrat des artefacts d'onboarding

Le commit porte toujours les cinq fichiers ensemble :

| Fichier | Contenu |
| --- | --- |
| `.specs/_onboarding.md` | Résumé, SHA, classification, confiance et prochaine étape. |
| `.specs/_stack.json` | Inventaire structuré des modules, stacks, versions et preuves. |
| `.specs/_baseline.json` | Commandes configurées et état statique non exécuté. |
| `.specs/_starter-design.md` | Architecture et conventions observées. |
| `.specs/_known-debt.md` | Dette prouvée, inconnues et politique de non-régression. |

Les deux documents JSON utilisent `schema_version: 1` et le même `git_sha`.
Tous les chemins enregistrés sont relatifs à la racine Git et utilisent `/`
comme séparateur.

## `_stack.json`

Champs obligatoires :

```json
{
  "schema_version": 1,
  "git_sha": "<sha>",
  "classification": "greenfield | brownfield",
  "modules": [],
  "confidence": {
    "level": "proved | limited | unknown",
    "limitations": []
  }
}
```

Chaque module conserve son chemin, son type, les versions réellement lues, ses
preuves et ses commandes configurées. Une version absente reste `null` ou est
omise ; elle ne devient jamais `latest`, `4`, `16` ou une autre valeur supposée.

## `_baseline.json`

Champs obligatoires :

```json
{
  "schema_version": 1,
  "git_sha": "<sha>",
  "status": "not-run",
  "heavy_gates_executed": false,
  "validation_commands": []
}
```

Une entrée de commande comporte `command` et `evidence`. Il s'agit d'une
commande à exécuter plus tard, pas d'un résultat. Les métriques non mesurées
restent absentes.

## Cohérence

- Les cinq fichiers décrivent le même snapshot Git.
- `_onboarding.md` et `_starter-design.md` citent le SHA.
- Les modules et preuves Markdown doivent correspondre à `_stack.json`.
- Les inconnues ne sont pas classées comme dette prouvée.
- Les cinq fichiers existants sont remplacés ensemble ou aucun ne l'est.
