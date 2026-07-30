# Revue de spécification : <FEATURE-ID>

> Responsable : agent Hermes principal, rôle de relecteur · Étape 2

## Inputs

- Fichier : `.specs/<FEATURE-ID>/01-spec.md`
- Révision Git : <sha ou non disponible>
- Horodatage de lecture : <ISO-8601>

## Summary

- verdict: <ready-for-approval | approve | request-changes>
- acs_total: <nombre>
- acs_failed: <nombre>
- open_questions: <nombre total>
- reviewer: <nom | utilisateur | en attente>
- reviewed_at: <ISO-8601 | en attente>
- decision_evidence: <approve | request-changes | en attente>
- decision_evidence_mode: <direct-response | decision-option | en attente>
- next_command: en attente

## Checklist

| ID | Contrôle | Résultat | Preuve |
| --- | --- | --- | --- |
| C-001 | <contrôle> | <pass, fail ou n/a> | <section ou justification> |

## Findings

| ID | Sévérité | État | Emplacement | Preuve | Correction demandée |
| --- | --- | --- | --- | --- | --- |
| (aucun) | — | — | — | — | — |

## New Questions Raised

- Q-NNN : <question découverte pendant la revue>
  - Pourquoi c'est important : <impact>
  - Options candidates : <options identifiées, sans choix implicite>
  - Statut : <open | transferred | resolved>

## User Decision

- Décision : <approve | request-changes | en attente>
- Relecteur : <nom | utilisateur | en attente>
- Date : <ISO-8601 | en attente>
- Commentaire : <texte ou aucun>
- Preuve explicite : <approve | request-changes | en attente>
- Mode de preuve : <direct-response | decision-option | en attente>

## Handoff

<Avec approve, étape 3. Avec request-changes, retour à l'étape 1.>
