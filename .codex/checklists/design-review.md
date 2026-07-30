# Checklist de revue de conception

Utilisée par `spring-architect` pour autoriser la sortie de la phase 3 (`03-design.md` + `04-tasks.md`).

## Architecture

- [ ] La carte des composants est présente (contrôleurs, services, dépôts, événements).
- [ ] Les composants sont regroupés par fonctionnalité/domaine (package de premier niveau = contexte délimité avec `api`/`internal`) ; aucun package de premier niveau `controller`/`service`/`repository`/`model` n'est introduit.
- [ ] Les frontières de modules sont documentées (packages de premier niveau avec sous-packages `internal`, contrôlés par ArchUnit).
- [ ] Les règles de couches sont respectées (pas de raccourci contrôleur → dépôt ni d'inversion).
- [ ] Une esquisse OpenAPI existe pour chaque endpoint nouveau ou modifié.

## Données

- [ ] Le modèle de relations entre entités est présent et cohérent avec les entités et relations de `01-spec.md`.
- [ ] Les cardinalités sont explicites et cohérentes entre l'API, le modèle de données et les tâches.
- [ ] L'outil de migration est détecté et cohérent (Flyway OU Liquibase, jamais les deux).
- [ ] Les migrations sont uniquement progressives avec justification, OU réversibles.
- [ ] Les champs contenant des données personnelles sont identifiés.

## Sécurité

- [ ] L'approche d'authentification est indiquée.
- [ ] Les règles d'autorisation sont indiquées pour chaque AC qui en nécessite.
- [ ] Le stockage des secrets est indiqué.

## Tâches

- [ ] Chaque AC de `01-spec.md` est couverte par au moins une tâche.
- [ ] Chaque tâche possède des `Test-IDs` et des `Files in scope`.
- [ ] Chaque tâche liste les portes de qualité à exécuter.
- [ ] Chaque tâche représente environ 1 à 4 heures.
- [ ] Les tests transverses sont réservés à la phase 5, sans duplication dans les tâches.

## Mode Epic (si applicable)

- [ ] `03-epic-design.md` existe et consigne les décisions transverses partagées.
- [ ] `03a-epic-roadmap.md` existe et ordonne les tranches verticales avec leurs dépendances.
- [ ] Les frontières de tranche sont verticales (résultats visibles par l'utilisateur), et non couche par couche.
- [ ] La décomposition détaillée de `04-tasks.md` ne commence qu'après approbation des artefacts Epic.

## ADR

- [ ] Chaque décision de conception non évidente possède un ADR (le statut `proposed` convient).
- [ ] Les ADR renvoient à la section de conception qui les a déclenchés.

## Absence d'invention

- [ ] Aucun comportement ni exigence non fonctionnelle absent de `01-spec.md` ou du code existant n'a été introduit.
- [ ] Toutes les `Q-NNN` sont résolues ou différées avec justification.

## Validation

- [ ] Revue effectuée par l'utilisateur.
- [ ] Verdict consigné.
