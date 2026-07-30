# Revue de spécification : <FEATURE-ID>

> Responsable : `spec-author` · Phase 2 · Checklist : `.codex/checklists/spec-review.md`

## Inputs

- Révision de `01-spec.md` : <git-sha ou horodatage>

## Checklist

- [ ] La source indique l'identifiant du ticket, son URL et la date de capture.
- [ ] L'objectif tient en un paragraphe et décrit un résultat visible par l'utilisateur.
- [ ] Chaque AC suit une forme EARS-lite.
- [ ] Chaque AC est atomique : une condition et un résultat.
- [ ] Chaque AC est testable : l'agent peut décrire un test Étant donné/Quand/Alors.
- [ ] Aucun AC ne contient de choix d'implémentation (noms de classes, bibliothèques, colonnes).
- [ ] Les non-objectifs sont présents et explicites.
- [ ] Le glossaire couvre chaque terme métier utilisé dans les AC.
- [ ] La liste des hypothèses ne contient que des éléments fournis par l'utilisateur ou la source.
- [ ] Toutes les `Q-NNN` sont résolues ou explicitement différées avec justification.
- [ ] Aucune nouvelle `Q-NNN` découverte pendant la revue ne reste ouverte.

## Findings

> Chaque constat reçoit un identifiant et une sévérité (`blocker | major | minor | nit`). Les constats bloquants et majeurs doivent être résolus avant de continuer.

- (aucun)

## New Questions Raised

> Si la revue révèle une incertitude, la consigner ici, revenir à la phase 1 et l'ajouter à la section `## Open Questions` de `01-spec.md`.

- (aucune)

## Verdict

- [ ] Approved — passer à `/design`
- [ ] Changes requested — revenir à `spec-author`

Relecteur : <utilisateur>
Date : <YYYY-MM-DD>
