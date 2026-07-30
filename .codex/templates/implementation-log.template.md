# Journal d'implémentation : <FEATURE-ID>

> Responsables : `spring-test-engineer` + `spring-implementer` · Phase 4 · Ajouts uniquement

Chaque tâche contribue un bloc `red`, `green`, `refactor` et `simplify`, au format ci-dessous.

---

## T-001 — <titre de la tâche>

### red — <YYYY-MM-DDTHH:MM:SSZ>

- Tests ajoutés : `src/test/java/<...>/XTest#shouldRejectExpiredCard` (T-001-T1)
- Commande : `mvn -q -Dtest=XTest#shouldRejectExpiredCard test`
- Résultat : **échec attendu** — `AssertionFailedError: expected status 400 but was 200`
- Notes : <si un élément est inhabituel>

### green — <YYYY-MM-DDTHH:MM:SSZ>

- Fichiers modifiés : `src/main/java/<...>/X.java`
- Taille du diff : +12 −0
- Commande : `mvn -q -Dtest=XTest#shouldRejectExpiredCard test`
- Résultat : **réussi**
- Notes : <implémentation minimale, rien de plus>

### refactor — <YYYY-MM-DDTHH:MM:SSZ>

- Fichiers modifiés : `src/main/java/<...>/X.java`
- Modifications : extraction du helper privé `validateExpiry`, sans changement de comportement.
- Commande : `mvn -q verify -pl <module>`
- Résultat : **réussi** (suite verte)

### simplify — <YYYY-MM-DDTHH:MM:SSZ>

- Fichiers modifiés : `src/main/java/<...>/X.java`
- Modifications :
  - intégration du helper à usage unique `formatErrorCode` (clarté plutôt qu'astuce) ;
  - remplacement d'une chaîne de ternaires par une expression `switch`.
- Commande : `mvn -q verify -pl <module>`
- Résultat : **réussi**

---
