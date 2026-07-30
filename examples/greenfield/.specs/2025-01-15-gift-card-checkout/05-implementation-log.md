# Journal d'implémentation : gift-card-checkout

Chaque tâche contribue quatre blocs : red, green, refactor et simplify. La sortie
du test en échec est citée telle quelle et l'état JSON de chaque phase est reflété
dans `.tdd-state.json`.

---

### T-001 — red

**Test ajouté :** `GiftCardCodeHasherTest#hashesAreDeterministicAndDifferFromInput`

```java
@Test
@Tag("foundation")
@DisplayName("foundation: hashing is deterministic and obscures the code")
void hashesAreDeterministicAndDifferFromInput() {
    var hasher = new GiftCardCodeHasher("salt");
    byte[] a = hasher.hash("ABCD-1234-EFGH-5678");
    byte[] b = hasher.hash("ABCD-1234-EFGH-5678");
    assertArrayEquals(a, b);
    assertFalse(new String(a, StandardCharsets.UTF_8).contains("ABCD"));
}
```

**Échec (`mvn test -Dtest=GiftCardCodeHasherTest`) :**
```
[ERROR] GiftCardCodeHasherTest.hashesAreDeterministicAndDifferFromInput  Time elapsed: 0.013 s  <<< ERROR!
java.lang.NoClassDefFoundError: com/example/checkout/giftcard/internal/GiftCardCodeHasher
```

`.tdd-state.json` après cette phase :
```json
{ "active_task": "T-001", "tasks": { "T-001": { "phase": "red",
    "red_failure_excerpt": "NoClassDefFoundError: GiftCardCodeHasher",
    "files_in_scope": [...], "acs_covered": [] } } }
```

### T-001 — green

Implémentation de `GiftCardCodeHasher` avec SHA-256, préfixe de sel et tableau de
32 octets. Ajout des entités, dépôts et du script Flyway `V1__gift_cards.sql` issu de `03-design.md`.

**`mvn test`** : 1 test unitaire réussit.
**`mvn -Dtest=GiftCardRepositoryIT verify`** : réussit sur Testcontainers
`postgres:16-alpine`, démarrage en environ 2,4 s et requête en 12 ms.

### T-001 — refactor

Extraction du sel dans un record `@ConfigurationProperties("checkout.giftcard")`.
La production injecte `${CHECKOUT_GIFTCARD_SALT}` et le test utilise `"salt"`.
Aucun changement de comportement ; tous les tests restent verts.

### T-001 — simplify

Application de la clarté : intégration du helper `concatBytes()` à usage unique et
renommage de `GiftCardEntity.bal` en `remainingBalance`. Tests verts, comportement inchangé.

Après cette phase : `T-001.phase = "done"`, `active_task = null`.

---

### T-002 — red

**Test ajouté :** `DefaultGiftCardRedemptionServiceTest#appliesFullBalanceWhenCardCoversSubtotal`

```java
@Test
@Tag("AC-001")
@DisplayName("AC-001: full coverage debits the order subtotal and persists redemption")
void appliesFullBalanceWhenCardCoversSubtotal() { ... }
```

**Échec :**
```
[ERROR] DefaultGiftCardRedemptionServiceTest.appliesFullBalanceWhenCardCoversSubtotal
expected: Applied[amountApplied=Money[2500 USD], remainingBalance=Money[7500 USD]]
 but was: <service does not exist>
```

### T-002 — green

Implémentation du parcours nominal de `redeem()` : chargement par hash, contrôles,
débit, persistance et résultat `Applied`. Le test d'utilisation partielle AC-005
réussit sans code supplémentaire grâce à `min(remainingBalance, subtotal)`.

`mvn verify` : 4 réussites, 2 unitaires et 2 d'intégration.

### T-002 — refactor

Extraction du calcul dans `amountToDebit(Money subtotal, Money balance)` sur
l'entité, pour la lisibilité. Comportement inchangé et tests verts.

### T-002 — simplify

Remplacement d'un stream trop astucieux par une clause de garde et du code
linéaire. Suppression d'un retour `Optional<Money>` inutile.

---

### T-003 — red

Ajout de trois tests de refus et d'un test d'intégration d'idempotence. Tous
échouent car le service lève `NoSuchElementException` au lieu de retourner
`Rejected(code)` et `IdempotencyStore` n'existe pas.

### T-003 — green

Les refus retournent maintenant `new Rejected(code)`. Ajout d'un
`IdempotencyStore` appuyé par la contrainte unique ; en cas de conflit, la ligne
existante est chargée et le même résultat `Applied` est renvoyé.

### T-003 — refactor

Regroupement des trois gardes dans `reasonToReject(...)`, qui renvoie le code ou
vide. Le service passe de 30 à 18 lignes.

### T-003 — simplify

Suppression de l'enum expérimental `RejectionReason` : les chaînes sont le
contrat. Les codes vivent désormais comme constantes de `GiftCardRedemptionResult`.

---

### T-004 — red

Le test WebMvc vérifie 200 avec JSON et 422 avec ProblemDetail. Le test de contrat
compare à `openapi.yaml`. Tous échouent car le contrôleur n'existe pas.

### T-004 — green

Ajout de `GiftCardController.redeem(...)`, du mapping DTO vers commande, de la
délégation au service et des statuts 200 ou 422. Mise à jour d'OpenAPI ; tous les tests réussissent.

### T-004 — refactor

Déplacement du mapping dans `GiftCardRedeemRequest.toCommand(...)` pour garder un contrôleur fin, sans changement de comportement.

### T-004 — simplify

Remplacement d'un paramètre `Optional<String>` toujours fourni par un paramètre
obligatoire et suppression d'un commentaire `TODO` obsolète.

`.tdd-state.json` après simplify de T-004 :
```json
{ "active_task": null,
  "tasks": {
    "T-001": { "phase": "done" },
    "T-002": { "phase": "done" },
    "T-003": { "phase": "done" },
    "T-004": { "phase": "done" } } }
```

Les quatre tâches sont terminées. Passer à `$test --gap`, sans écart attendu, puis `$validate`.
