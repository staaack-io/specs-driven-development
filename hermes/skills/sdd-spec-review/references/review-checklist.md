# Checklist de revue de spécification

Attribuer à chaque contrôle `pass`, `fail` ou `n/a`, avec une preuve courte.

## Source et cadrage

- La source est consignée avec outil, identifiant, URL et date, ou marquée
  explicitement `ad-hoc`.
- L'objectif tient en un paragraphe et décrit un résultat visible.
- Les non-objectifs sont présents et explicites.
- Le glossaire couvre les termes métier des critères.
- `Domain Entities and Relationships` est présent.
- Les entités restent conceptuelles, sans classe, table ou bibliothèque.
- Les relations indiquent un sens métier et une cardinalité, ou une question
  résolue justifie leur absence.

## Critères d'acceptation

- Chaque critère possède un identifiant `AC-NNN` unique et stable.
- Chaque critère suit une forme EARS-lite.
- Chaque critère contient une condition et un résultat observable.
- Chaque critère peut produire un test Étant donné/Quand/Alors indépendant.
- Aucun critère ne contient de choix d'implémentation.
- Toute exigence non fonctionnelle est mesurable ou reliée à une question.

## Absence d'invention

- Les hypothèses proviennent de la source ou des réponses de l'utilisateur.
- Aucun choix par défaut silencieux n'est introduit.
- Chaque `Q-NNN` est résolue ou explicitement différée avec justification.

## Exhaustivité et sécurité

- Les comportements de la source sont repris ou exclus explicitement.
- Les informations hors ticket figurent dans `Out-of-Band Inputs`.
- Toute bascule visible possède un feature flag et un retour arrière, ou une
  dérogation utilisateur explicite.

## Porte humaine

- Un résultat technique réussi vaut seulement `ready-for-approval`.
- Le verdict `approve` exige une réponse explicite de l'utilisateur pendant la
  revue.
- Toute nouvelle ambiguïté impose `request-changes` et un retour à
  `/sdd-spec --continue`.
