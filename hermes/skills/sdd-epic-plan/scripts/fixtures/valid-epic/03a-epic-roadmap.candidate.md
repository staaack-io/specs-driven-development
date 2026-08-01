# Feuille de route Epic : sample-epic

## Inputs

- Conception approuvée : `.specs/sample-epic/03-epic-design.md`

## Slice Strategy

- Principe : résultats verticaux visibles
- Taille : une capacité par tranche

## Slice ID Registry

- high_water_mark: 2
- retired_ids: (aucun)

## Slice Backlog

| ID | Résultat | AC-IDs | Dépend de | Jalon |
| --- | --- | --- | --- | --- |
| S-001 | exposer l'état du service | AC-001 | aucune | M-001 |
| S-002 | afficher l'état du service | AC-002 | S-001 | M-002 |

## Per-slice Delivery Notes

### S-001

- Critères d'entrée : contrat approuvé
- Critères de sortie : endpoint testable
- Risques : aucun

### S-002

- Critères d'entrée : S-001 disponible
- Critères de sortie : page testable
- Risques : indisponibilité réseau

## AC Coverage

| AC-ID | Tranches | Couvert |
| --- | --- | --- |
| AC-001 | S-001 | oui |
| AC-002 | S-002 | oui |

## Rollout and Risk Strategy

- aucun déploiement pendant la planification

## Open Questions

- (aucune)

## Resolved Questions

- (aucune)

## Sign-off

- [ ] Chaque AC est couvert.
- [ ] Les dépendances sont acycliques.
- [ ] Les questions ouvertes sont résolues.
