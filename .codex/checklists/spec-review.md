# Checklist de revue de spécification

Utilisée par `spec-author` pour autoriser la sortie de la phase 2.

## Source et cadrage

- [ ] La source est consignée (outil de suivi, identifiant, URL, date de capture) OU explicitement marquée `ad-hoc`.
- [ ] L'objectif tient en un paragraphe et décrit un résultat visible par l'utilisateur.
- [ ] Les non-objectifs sont présents et explicites.
- [ ] Le glossaire couvre chaque terme métier utilisé dans les AC.
- [ ] La section `## Domain Entities and Relationships` est présente.
- [ ] Les entités sont décrites en termes métier, sans fuite de classes, tables ou bibliothèques.
- [ ] Les relations précisent clairement leur cardinalité et leur sens métier.

## Critères d'acceptation

- [ ] Chaque AC possède un identifiant stable `AC-NNN` (complété par des zéros et croissant).
- [ ] Chaque AC suit une forme EARS-lite (universelle, événement, état, optionnelle ou indésirable).
- [ ] Chaque AC est atomique : une condition et un résultat.
- [ ] Chaque AC est testable : l'agent peut décrire un test Étant donné/Quand/Alors.
- [ ] Aucun AC ne contient de choix d'implémentation (noms de classes, bibliothèques, colonnes, valeurs par défaut).
- [ ] Les exigences non fonctionnelles vagues (« rapide », « sécurisé », « extensible ») sont remplacées par des conditions mesurables OU transformées en `Q-NNN`.

## Absence d'invention

- [ ] La liste des hypothèses ne contient que des éléments fournis par l'utilisateur ou la source.
- [ ] Aucun choix par défaut silencieux (moteur de base de données, authentification, pagination, format d'erreur, etc.).
- [ ] Toutes les `Q-NNN` sont résolues ou explicitement différées avec justification.

## Exhaustivité

- [ ] Tous les AC du ticket source sont repris, ou explicitement exclus comme non-objectifs.
- [ ] Les informations hors ticket (précisions du chat, captures d'écran) sont consignées sous `## Out-of-Band Inputs`.

## Sécurité de bascule

- [ ] Toute bascule visible (migration, remplacement de comportement, changement d'interface) possède soit un feature flag et une procédure de retour arrière, soit une dérogation explicitement approuvée par l'utilisateur.

## Validation

- [ ] Revue effectuée par l'utilisateur.
- [ ] Verdict consigné dans `02-spec-review.md` (`approve` ou `request-changes`).
