---
name: junit5-testcontainers-patterns
description: Modèles de tests JUnit 5 et Spring Boot 4, tranches et intégration Testcontainers avec `@ServiceConnection`. Utiliser pour écrire ou relire un test et choisir entre unitaire, tranche et intégration.
when_to_use:
  - Phase 4, étape red de `$build` — écrire le test en échec.
  - Phase 5, Test — ajouter les suites transverses.
  - Chaque fois qu’un `@SpringBootTest` pourrait être remplacé par un test par tranche.
authoritative_references:
  - https://docs.spring.io/spring-boot/reference/testing/index.html
  - https://java.testcontainers.org/
---

# Modèles JUnit 5 et Testcontainers

## Choisir le plus petit périmètre couvrant l'AC

| Type d'AC | Utiliser |
|---|---|
| Logique pure, calcul, validation, mapping | JUnit 5 seul, sans Spring |
| Validation du contrôleur, statuts, forme JSON | `@WebMvcTest` |
| Requête ou mapping JPA | `@DataJpaTest` + Testcontainers avec `@ServiceConnection` |
| Bout en bout HTTP avec base ou service externe | `@SpringBootTest(webEnvironment = RANDOM_PORT)` + Testcontainers |
| Cache, sécurité, câblage de beans | tranche ciblée, par exemple `@WebMvcTest` + `@Import` |

**`@SpringBootTest` est un dernier recours.** Utiliser une tranche lorsqu'elle suffit.

## Nommage et traçabilité

- Chaque méthode `@Test` ou `@ParameterizedTest` possède obligatoirement `@DisplayName`.
- Le bloc complet contient, dans cet ordre :

  ```java
  @Test
  @Tag("AC-007")
  @DisplayName("AC-007: given expired gift card, when applied, then returns 4xx")
  void appliesExpiredGiftCard() { ... }
  ```

- Pour un test tracé, utiliser `"<T-ID>: given <precondition>, when <action>, then <outcome>"`.
- `@Tag("AC-NNN")` rend le test lisible par la matrice de traçabilité.
- Un AC par méthode lorsque possible.
- La phase simplify vérifie `@DisplayName` sur tous les tests nouveaux ou modifiés.

## Testcontainers avec `@ServiceConnection`

```java
@DataJpaTest
@Testcontainers
class GiftCardRepositoryTest {

    @Container @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17-alpine");

    @Autowired GiftCardRepository repo;

    @Test
    @Tag("AC-004")
    @DisplayName("AC-004: given a new gift card, when saved and reloaded, then balance is preserved")
    void persistsBalance() {
        var saved = repo.save(GiftCard.with(BigDecimal.valueOf(100)));
        assertThat(repo.findById(saved.id()).orElseThrow().balance())
            .isEqualByComparingTo("100");
    }
}
```

Points clés :

- `@ServiceConnection` remplace le code répétitif `@DynamicPropertySource` depuis Boot 3.
- Un conteneur par classe de test, ou statique pour la suite via une classe de base.
- Figer le tag de l'image, par exemple `postgres:17-alpine`, jamais `latest`.
- Pour Kafka, RabbitMQ ou Redis, utiliser le même modèle avec le module Testcontainers officiel.

## Quand Testcontainers est obligatoire

Si le dépôt déclare une dépendance `org.testcontainers:*`, le harness exige un
test d'intégration pour toute fonctionnalité qui touche :

- une implémentation de dépôt ;
- un `@RestController` qui lit ou écrit la base ;
- un script de migration ;
- un producteur ou consommateur de messages.

Seul un ADR `adr/NNN-no-testcontainers-for-<reason>.md` permet une dérogation.

## Exemple de test par tranche

```java
@WebMvcTest(CheckoutController.class)
class CheckoutControllerTest {

    @Autowired MockMvc mvc;
    @MockitoBean CheckoutService service;

    @Test
    @Tag("AC-003")
    @DisplayName("AC-003: given unknown order id, when POST, then returns 404")
    void unknownOrder() throws Exception {
        when(service.applyGiftCard(any(), any())).thenThrow(OrderNotFound.class);
        mvc.perform(post("/checkout/{id}/gift-card", "missing")
                .contentType(APPLICATION_JSON)
                .content("""{"code":"ABC","orderTotalCents":1000}"""))
           .andExpect(status().isNotFound());
    }
}
```

Utiliser `@MockitoBean` de Spring Boot 4 à la place de `@MockBean`, déprécié.

## Fixtures

- Préférer des builders comme `GiftCardFixtures.fullyRedeemed()` aux constructeurs bruts.
- Placer les fixtures sous `src/test/java/.../testsupport/`.
- Aucun code de production dans les tests, ni code de test dans la production.

## Interdictions dans les tests

- `Thread.sleep` pour synchroniser ; utiliser Awaitility.
- Ports hôtes codés en dur.
- Mock du système sous test.
- `@Disabled` sans commentaire `# DisabledReason: <ticket-or-ADR-link>` au-dessus.
- Assertion supprimée pour faire passer un test.
- `catch (Exception)` sans assertion.

## API dépréciées dans Spring MVC Test 7

| Déprécié | Remplacement | Raison |
|---|---|---|
| `status().isUnprocessableEntity()` | `status().is(422)` | Supprimé dans Spring MVC Test 7.0 |
| `new MappingJackson2HttpMessageConverter()` dans `standaloneSetup` | Supprimer `.setMessageConverters()` | Le convertisseur est supprimé et Jackson est auto-enregistré |
| `@MockBean` | `@MockitoBean` | Déprécié dans Spring Boot 4 |
