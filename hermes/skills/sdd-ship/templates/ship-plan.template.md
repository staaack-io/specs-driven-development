# Plan de livraison : <feature-id>

## Pre-ship gates

| Porte | Résultat | Preuve |
| --- | --- | --- |
| Validation | PASS | <07-validation-report.md> |
| Review | Approve | <08-code-review.md> |
| Questions | 0 | <01-spec.md et 03-design.md> |
| Baseline | PASS | <baseline> |
| Scope | PASS | <files_in_scope> |
| Diff | non vide | <base...HEAD> |

## Feature flag

- Nom : <nom>
- Valeur par défaut : <off/on>
- Arrêt d'urgence : <action>
- Responsable : <responsable>
- Retrait : <condition>

## Observability

| Surface | Métrique | Journaux | Alerte | Dashboard | Justification |
| --- | --- | --- | --- | --- | --- |
| <surface> | <métrique> | `feature_id`, `ac_id` | <seuil> | <lien> | <n/a justifié> |

## Rollback

1. Détection : <alerte et seuil>
2. Limitation en moins de cinq minutes : <arrêt d'urgence>
3. Restauration : <réconciliation, événement ou opération de données>

## Release notes externes

- <note simple>

## Release notes internes

- <AC, diff, ADR, migration, flag, dashboard et commits>

## Commande de déploiement

Commande affichée uniquement, jamais exécutée par Hermes :

```text
<commande destinée à l'utilisateur>
```
