---
name: tdd-red-green-refactor
description: Discipline stricte rouge, vert, refactorisation et simplification pour `$build <task-id>`. Utiliser pour toute tâche de phase 4. Ne jamais écrire de production sans test en échec consigné dans `.tdd-state.json`.
when_to_use:
  - Phase 4 — pour chaque tâche, sans exception.
  - Avant toute modification de `src/main/**`.
authoritative_references:
  - .codex/checklists/implementation-dod.md
  - .codex/templates/implementation-log.template.md
---

# TDD : red / green / refactor / simplify

## Les quatre phases de chaque tâche

### 1. RED — écrire un test en échec

- Lire la tâche dans `04-tasks.md` et confirmer ses `Test-IDs` et `AC-IDs`.
- Écrire le plus petit test qui vérifie le comportement de l'AC.
- Chaque méthode `@Test` porte obligatoirement, dans cet ordre, `@Test`,
  `@Tag("AC-NNN")`, puis `@DisplayName("...")`. Écrire le nom avant le corps du
  test. Pour un test tracé, utiliser
  `"<T-ID>: given <precondition>, when <action>, then <outcome>"`.
- Exécuter uniquement ce test avec `mvn -Dtest=ClassName#method test`.
- Le test **doit échouer pour la bonne raison**, et non pour une faute ou une erreur de compilation.
- Ajouter un bloc `red` à `05-implementation-log.md` avec la commande et les dix premières lignes de l'échec.
- Mettre `.specs/<id>/.tdd-state.json` à jour :

  ```json
  { "active_task": "T-001", "tasks": { "T-001": { "phase": "red", "red_at": "2026-04-18T10:00:00Z", "red_test_signature": "...", "red_failure_excerpt": "..." } } }
  ```

Le hook `block-impl-without-failing-test` lit ce fichier. Aucune modification de
`src/main/**` n'est autorisée sans `phase == red` et `red_failure_excerpt` non vide.

### 2. GREEN — minimum de code de production

- Modifier uniquement les `Files in scope` de la tâche ; le hook l'impose.
- Écrire **le minimum de code** pour faire passer le test, sans fonctionnalité spéculative ni nettoyage hors sujet.
- Relancer le test ciblé, puis toute la suite Surefire du module avec `mvn -q test -pl <module>`.
- Ajouter un bloc `green` au journal et passer `phase` à `green`.

### 3. REFACTOR — améliorer l'intérieur sans changer le comportement

- Éliminer les duplications, extraire des helpers, clarifier les noms et placer la logique dans la bonne couche.
- Relancer toute la suite du module après **chaque** modification ; elle reste verte.
- Sont permis : extraction de méthode ou classe, intégration de variable, renommage et déplacement vers un package interne.
- Sont interdits : signatures publiques, comportement ou fonctionnalités modifiés.
- Ajouter un bloc `refactor` par changement significatif.

### 4. SIMPLIFY — passe `$code-simplify`

- Appliquer `clarity-over-cleverness` : préférer la forme qu'un ingénieur junior
  comprend immédiatement.
- Rechercher ternaires imbriqués, streams astucieux, abstraction prématurée,
  options mortes, paramètres inutiles et helpers à appelant unique.
- Extraire toute chaîne ou valeur numérique répétée au moins deux fois dans une
  même classe vers une constante `private static final` au nom métier.
- Vérifier que chaque test nouveau ou modifié possède `@DisplayName`, sans réécrire les tests historiques non touchés.
- Garder la suite verte, ajouter un bloc `simplify` et passer `phase` à `done`.

### 5. COMMIT — afficher le rapport d'arrêt

Lorsque `phase` atteint `done`, **S'ARRÊTER**. Ne pas démarrer la tâche suivante.
Afficher les fichiers modifiés, les tests réussis et un message de commit suggéré,
puis recommander :

```text
git status               # relire les changements
git commit               # commiter la tâche
$build <next-task-id>    # démarrer la tâche suivante
```

L'agent n'exécute jamais `git commit`. Le prochain `$build` refuse de démarrer si
la tâche précédente laisse des modifications non commitées. L'utilisateur peut
explicitement demander d'enchaîner sans commit ; respecter alors cette demande.

## Format du journal

```markdown
### T-001 · red · 2026-04-18T10:00:00Z
**Command:** `mvn -q -Dtest=ApplyGiftCardRequestTest#rejectsBlankCode test`
**Result:** FAIL (expected)
**Excerpt:** [premières lignes de l'échec]
```

## Sens de « minimum de code »

- Une constante codée en dur peut suffire pour un seul test ; le suivant impose la généralisation.
- Ne pas créer d'interface pour une seule implémentation.
- Ne pas créer d'option de configuration pour un seul appelant.
- Ne pas ajouter de paramètre « pour plus tard ».

## Anti-patterns bloqués par le hook

- Écrire un test qui réussit déjà.
- Supprimer un test pour verdir la CI.
- Modifier des fichiers hors des `Files in scope`.
- Sauter red ou adapter une assertion existante au mauvais comportement.
- Marquer `done` sans les quatre blocs du journal.
- Ajouter une méthode sans consommateur réel, couverte uniquement par un test tautologique.
- Démarrer automatiquement la tâche suivante sans laisser à l'utilisateur la possibilité de commiter.
