# Conception Epic : sample-epic

## Summary

- status: draft
- stacks: full-stack
- architect_roles: spring-architect, react-nextjs-architect
- planned_at: 2026-08-01T00:00:00+00:00
- approved_at: en attente

## Inputs

- Spécification : `.specs/sample-epic/01-spec.md`
- Revue : `.specs/sample-epic/02-spec-review.md`
- Révision Git : non disponible
- Preuves de stack : `backend/pom.xml`, `frontend/package.json`

## Delegation Record

| Rôle | Statut | Preuves lues | Fichiers modifiés |
| --- | --- | --- | --- |
| spring-architect | ready | backend/pom.xml | aucun |
| react-nextjs-architect | ready | frontend/package.json | aucun |

## Epic Scope

- Dans le périmètre : état opérationnel du service
- Hors périmètre : historique de disponibilité

## Architecture Boundaries

| Zone | Responsabilité | Interface publiée | Dépendances autorisées |
| --- | --- | --- | --- |
| backend | publier l'état | HTTP | aucune |
| frontend | afficher l'état | page | backend |

## Shared Decisions

| Décision | Options prouvées | Option retenue | Justification | ADR candidat |
| --- | --- | --- | --- | --- |
| contrat d'état | JSON | JSON | AC-001 | aucun |

## Cross-cutting Constraints

- aucune

## Risks and Mitigations

| Risque | Impact | Réduction | Retour arrière |
| --- | --- | --- | --- |
| indisponibilité backend | affichage dégradé | état indisponible | retirer la page |

## Open Questions

- (aucune)

## Resolved Questions

- (aucune)

## Change Requests

| ID | Statut | Demandé le | Demande | Résolution | Résolu le |
| --- | --- | --- | --- | --- | --- |
| (aucune) | — | — | — | — | — |

## User Decision

- decision: en attente
- reviewer: en attente
- decided_at: en attente
- decision_evidence: en attente
- decision_evidence_mode: en attente
- comment: aucun

## Sign-off

- [ ] Chaque AC est couvert par la roadmap.
- [ ] Aucune question ouverte ne subsiste.
- [ ] Les rôles délégués n'ont modifié aucun fichier.
- [ ] L'Epic est explicitement approuvée.
