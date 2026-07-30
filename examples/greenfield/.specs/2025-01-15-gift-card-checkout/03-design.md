# Conception : gift-card-checkout

## Carte des modules, contrôlée par ArchUnit

```
com.example.checkout
├── giftcard            (NOUVEAU)  ← cette fonctionnalité
│   ├── api             public : GiftCardRedemptionService, événements
│   └── internal        privé au package : persistance, hachage
├── order               (existant) dépend de : shared, giftcard.api
└── shared              (existant) aucune dépendance entrante
```

Chaque package de premier niveau sous `com.example.checkout` est un module.
ArchUnit impose les frontières : `..internal..` reste privé au module et aucun
cycle n'existe entre packages principaux. Le nouveau module `giftcard` publie
uniquement `GiftCardRedemptionService` et l'événement `GiftCardRedeemed` via
`api`. `order` dépend de `giftcard.api` dans un seul sens, contrôlé par
`ArchitectureTests`.

## API publique Java

```java
package com.example.checkout.giftcard.api;

public sealed interface GiftCardRedemptionResult {
    record Applied(UUID redemptionId, Money amountApplied, Money remainingBalance) implements GiftCardRedemptionResult {}
    record Rejected(String errorCode) implements GiftCardRedemptionResult {}  // gift_card.{unknown,expired,depleted}
}

public interface GiftCardRedemptionService {
    GiftCardRedemptionResult redeem(RedeemCommand cmd);
}

public record RedeemCommand(
    UUID orderId,
    String cardCode,           // 16 caractères, jamais journalisé
    Money orderSubtotal,
    String idempotencyKey      // fenêtre de 24 h
) {}
```

## Contrat REST, extrait de `src/main/resources/openapi/openapi.yaml`

```yaml
paths:
  /orders/{orderId}/gift-card:
    post:
      summary: Appliquer une carte cadeau à une commande
      parameters:
        - name: orderId
          in: path
          required: true
          schema: { type: string, format: uuid }
        - name: Idempotency-Key
          in: header
          required: true
          schema: { type: string, minLength: 16 }
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/RedeemRequest' }
      responses:
        '200': { $ref: '#/components/responses/Applied' }
        '422': { $ref: '#/components/responses/Rejected' }
        '409': { description: Conflit d'idempotence avec une charge différente }
```

## Modèle de données

```sql
-- Flyway: src/main/resources/db/migration/V1__gift_cards.sql
create table gift_card (
    id              uuid primary key,
    code_hash       bytea not null unique,         -- SHA-256(code || sel)
    initial_balance bigint not null,               -- unités mineures, centimes
    remaining_balance bigint not null,
    issued_at       timestamptz not null,
    expires_at      timestamptz not null,
    constraint gc_balance_nonneg check (remaining_balance >= 0)
);

create table gift_card_redemption (
    id               uuid primary key,
    gift_card_id     uuid not null references gift_card(id),
    order_id         uuid not null,
    amount_applied   bigint not null,
    idempotency_key  text not null,
    created_at       timestamptz not null default now(),
    constraint gcr_amount_pos check (amount_applied > 0),
    unique (gift_card_id, idempotency_key)         -- prend en charge AC-006
);

create index idx_gcr_order on gift_card_redemption(order_id);
```

Outil de migration : **Flyway**, détecté dans `_stack.json`. Liquibase reste absent ; jamais `both`.

## Modèle d'erreur

| Code                  | HTTP | Quand                                       |
|-----------------------|------|---------------------------------------------|
| `gift_card.unknown`   | 422  | Le hash est absent                          |
| `gift_card.expired`   | 422  | `expires_at < now()`                        |
| `gift_card.depleted`  | 422  | `remaining_balance = 0`                     |
| `idempotency.conflict`| 409  | Même clé, charge différente                 |

Les erreurs passent par le mapper `RFC 7807 ProblemDetail` existant dans `shared`.

## Observability

- Compteurs : `gift_card.redeem.success`, `gift_card.redeem.failure{reason}`.
- Une ligne par tentative : `INFO giftcard.redemption order_id=… card_id=… result=… amount_applied=…` ; jamais le code.
- Span `giftcard.redeem` autour de l'appel du service.

## Référence de sécurité

- L'endpoint exige le rôle Spring Security `customer` existant.
- Le code n'est jamais journalisé, retourné ni placé dans une URL.
- `code_hash` possède un index unique et le code brut est jeté après hachage.
- OWASP Dependency-Check est déjà raccordé dans le POM parent.

## Ajouts ArchUnit

```java
@ArchTest
static final ArchRule giftcardInternalIsHidden =
    noClasses().that().resideOutsideOfPackage("..giftcard.internal..")
        .should().dependOnClassesThat().resideInAPackage("..giftcard.internal..");

@ArchTest
static final ArchRule giftcardDoesNotDependOnOrder =
    noClasses().that().resideInAPackage("..giftcard..")
        .should().dependOnClassesThat().resideInAPackage("..order..");

@ArchTest
static final ArchRule noCyclesBetweenTopLevelPackages =
    slices().matching("com.example.checkout.(*)..").should().beFreeOfCycles();
```

## Risques

1. **Attaque temporelle sur le code.** Comparaison des hash en temps constant et recherche par index haché.
2. **Utilisations concurrentes.** La contrainte unique protège les nouvelles
   tentatives ; deux commandes concurrentes reposent sur un verrou de ligne et la contrainte de solde non négatif.

ADR : voir [`adr/ADR-001-archunit-for-module-boundaries.md`](./adr/ADR-001-archunit-for-module-boundaries.md).
