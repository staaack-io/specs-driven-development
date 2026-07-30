# Exemple greenfield : gift-card-checkout

Un nouveau service Spring Boot 4 illustrant le parcours nominal complet.

## Organisation du projet

```text
greenfield/
├── pom.xml                                  # raccordé au harness
├── checkstyle.xml                           # configuration minimale
├── src/
│   ├── main/java/com/example/checkout/
│   │   ├── CheckoutApplication.java         # @SpringBootApplication
│   │   ├── giftcard/                        # module, paquet de premier niveau
│   │   │   ├── api/                         # API publique
│   │   │   └── internal/                    # implémentation privée contrôlée par ArchUnit
│   │   └── shared/
│   └── main/resources/
│       ├── application.yaml
│       ├── db/migration/V1__init.sql
│       └── openapi/openapi.yaml
│   └── test/java/com/example/checkout/
│       ├── ArchitectureTests.java           # règles ArchUnit
│       └── giftcard/...
└── .specs/
    └── 2025-01-15-gift-card-checkout/
        ├── 01-spec.md
        ├── 02-spec-review.md
        ├── 03-design.md
        ├── 04-tasks.md
        ├── 05-implementation-log.md
        ├── 06-test-plan.md
        ├── 07-validation-report.md
        ├── 07a-traceability.md
        ├── 08-code-review.md
        ├── adr/
        │   └── ADR-001-archunit-for-module-boundaries.md
        └── .tdd-state.json
```

## Lire cet exemple

Les fichiers importants se trouvent sous
`.specs/2025-01-15-gift-card-checkout/`. Les lire dans l’ordre :

1. [`01-spec.md`](./.specs/2025-01-15-gift-card-checkout/01-spec.md) — demande
   reçue par `$spec` et spécification produite ;
2. [`02-spec-review.md`](./.specs/2025-01-15-gift-card-checkout/02-spec-review.md)
   — verdict de la checklist ;
3. [`03-design.md`](./.specs/2025-01-15-gift-card-checkout/03-design.md) —
   frontières, contrat REST, persistance et erreurs ;
4. [`04-tasks.md`](./.specs/2025-01-15-gift-card-checkout/04-tasks.md) — trois
   tâches reliées aux critères ;
5. [`05-implementation-log.md`](./.specs/2025-01-15-gift-card-checkout/05-implementation-log.md)
   — étapes TDD et extraits d’échecs ;
6. [`07-validation-report.md`](./.specs/2025-01-15-gift-card-checkout/07-validation-report.md)
   — verdict du harness ;
7. [`08-code-review.md`](./.specs/2025-01-15-gift-card-checkout/08-code-review.md)
   — revue avant commit.

Les sources Java sont abrégées ; les artefacts méthodologiques constituent le
cœur de l’exemple.
