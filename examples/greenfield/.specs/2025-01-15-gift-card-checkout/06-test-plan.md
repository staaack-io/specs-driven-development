# Plan de test : gift-card-checkout

## Matrice de couverture

| AC      | Unitaire                                                | Tranche / WebMvc                | Intégration (Testcontainers)      | Contrat (OpenAPI)            |
|---------|---------------------------------------------------------|---------------------------------|-----------------------------------|-------------------------------|
| AC-001  | `appliesFullBalanceWhenCardCoversSubtotal`              | `controller_returns_200`        | `GiftCardRedemptionIT.fullCover`  | request/response 200 schema   |
| AC-002  | `rejectsUnknownCode`                                    | `controller_returns_422_unknown`| —                                 | 422 unknown error envelope    |
| AC-003  | `rejectsExpiredCard`                                    | `controller_returns_422_expired`| —                                 | 422 expired error envelope    |
| AC-004  | `rejectsDepletedCard`                                   | `controller_returns_422_depleted`| —                                | 422 depleted error envelope   |
| AC-005  | `appliesFullBalanceWhenCardDoesNotCover`                | —                               | `GiftCardRedemptionIT.partial`    | couvert transitivement        |
| AC-006  | —                                                       | —                               | `IdempotentRedeemIT.sameKeyTwice` | présence de l'en-tête         |

## Types de tests utilisés

- **Unitaire :** JUnit 5 avec dépôt simulé, moins de 50 ms chacun.
- **Tranche :** `@WebMvcTest(GiftCardController.class)` avec service `@MockBean`.
- **Intégration :** `@SpringBootTest`, Testcontainers Postgres 16 et migrations Flyway au démarrage.
- **Contrat :** swagger-request-validator dans MockMvc détecte tout écart avec `openapi.yaml`.
- **Architecture :** `ArchitectureTests` vérifie en permanence les frontières et packages internes.

## Tests de mutation

PIT s'exécute avec `mvn -Ppit`, cible `com.example.checkout.giftcard.*` et impose
80 %. Les mutants survivants figurent dans le rapport puis sont tués ou justifiés.

## Gap-NNN entries

*(vide — `$test --gap` ne trouve aucun écart et le nouveau code est couvert à 100 %.)*

## Éléments volontairement non testés ici

- Mapper `ProblemDetail` partagé, couvert par les tests de plateforme.
- Configuration Spring Security, couverte par `SecurityConfigurationTest`.
- Chemins Liquibase, car `_stack.json` indique Flyway exclusivement.
