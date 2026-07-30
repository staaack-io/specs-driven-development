---
name: spring-task-decomposition
description: Découper une conception Spring Boot 4 en tâches TDD de une à quatre heures avec identifiants stables, traçabilité, fichiers autorisés et portes. Utiliser pour rédiger `04-tasks.md`.
when_to_use:
  - Phase 3, Plan — transformer `03-design.md` et `01-spec.md` en liste ordonnée de tâches.
  - Replanifier après une modification de la spécification.
authoritative_references:
  - .codex/templates/tasks.template.md
  - .codex/checklists/implementation-dod.md
---

# Découpage des tâches Spring

## Règle de taille

Chaque tâche représente **1 à 4 heures** pour un ingénieur compétent. Scinder une
tâche plus grande et fusionner une tâche de moins de 30 minutes avec la précédente.

## Forme

Une bonne tâche possède :

1. un identifiant stable `T-NNN`, jamais renuméroté ;
2. les `AC-IDs` dont elle fait progresser le résultat visible ;
3. au moins un `Test-ID`, comme `T-NNN-T1` ;
4. des `Files in scope` listant chaque chemin autorisé ; le hook les impose ;
5. les dépendances `T-NNN` qui doivent être `done` avant ;
6. les couches du harness à exécuter, par défaut toutes celles touchant les packages modifiés ;
7. une phrase expliquant le retour arrière en cas d'échec.

## Convention d'ordre

Ordonner les tâches pour que les dépendances progressent vers l'intérieur :

1. **Domaine et contrats** — DTO, value objects, extrait OpenAPI, migration.
2. **Tests unitaires ou par tranche et implémentation minimale** — une tâche par préoccupation de contrôleur, service ou dépôt.
3. **Tests d'intégration** — Testcontainers et parcours de bout en bout via le contrôleur.
4. **Transverse** — règles ArchUnit, enveloppe d'erreur, observabilité.

## Exemple extrait de `04-tasks.md`

```markdown
### T-001 — Ajouter le DTO de requête `apply-gift-card` et sa validation
- **AC-IDs:** AC-001, AC-003
- **Test-IDs:** T-001-T1 (refuse un code vide), T-001-T2 (refuse un total négatif)
- **Files in scope:**
  - `src/main/java/com/example/shop/checkout/ApplyGiftCardRequest.java`
  - `src/test/java/com/example/shop/checkout/ApplyGiftCardRequestTest.java`
- **Dependencies:** none
- **Gates:** format, compile, unit
- **Rollback:** supprimer les deux fichiers ; aucun autre ne les référence encore.

### T-002 — Créer l'ébauche du contrôleur `POST /checkout/{orderId}/gift-card`
- **AC-IDs:** AC-001, AC-002, AC-003
- **Test-IDs:** T-002-T1 (404 si la commande manque), T-002-T2 (415 pour un mauvais content-type), T-002-T3 (200 sur le parcours nominal avec service simulé)
- **Files in scope:** classe du contrôleur + `@WebMvcTest`
- **Dependencies:** T-001
- **Gates:** format, compile, unit, slice
```

## Anti-patterns

- « Implémenter les cartes cadeaux » : trop grand.
- Une tâche sans `Test-IDs` : TDD impossible.
- Des `Files in scope` égaux à `**/*` : le hook bloquera.
- Deux tâches modifiant le même fichier en parallèle : les sérialiser.
- Une tâche de refactorisation sans AC : refactoriser dans la phase refactor de `$build`.

## Auto-vérification

- [ ] Chaque AC de `01-spec.md` est accessible depuis les `AC-IDs` d'au moins une tâche.
- [ ] Chaque tâche possède au moins un `Test-ID`.
- [ ] Chaque tâche tient dans 1 à 4 heures.
- [ ] Les `Files in scope` sont des chemins concrets, pas des globs.
- [ ] Le graphe des dépendances ne contient aucun cycle.
