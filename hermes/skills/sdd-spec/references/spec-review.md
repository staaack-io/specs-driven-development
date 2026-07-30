# Checklist de spécification

## Source et cadrage

- [ ] La source est consignée ou marquée `ad-hoc`.
- [ ] L'objectif décrit un résultat visible par l'utilisateur.
- [ ] Les non-objectifs et le glossaire sont présents.
- [ ] Les entités et relations restent conceptuelles.

## Critères d'acceptation

- [ ] Chaque critère possède un identifiant stable `AC-NNN`.
- [ ] Chaque critère suit une forme EARS-lite.
- [ ] Chaque critère est atomique et testable.
- [ ] Aucun critère ne contient de choix d'implémentation.
- [ ] Les exigences non fonctionnelles sont mesurables ou deviennent des
  questions.

## Absence d'invention

- [ ] Les hypothèses proviennent uniquement de l'utilisateur ou de la source.
- [ ] Aucun choix par défaut n'a été ajouté silencieusement.
- [ ] Toute incertitude possède un identifiant `Q-NNN`.

## Exhaustivité et sécurité

- [ ] Tous les comportements de la source sont repris ou explicitement exclus.
- [ ] Les précisions hors ticket sont consignées.
- [ ] Toute bascule visible possède une stratégie de retour arrière ou une
  dérogation explicite.
