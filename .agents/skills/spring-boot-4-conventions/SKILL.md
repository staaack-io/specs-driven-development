---
name: spring-boot-4-conventions
description: Idiomes et valeurs par défaut de Spring Framework 7 et Spring Boot 4. Utiliser pour écrire ou relire contrôleurs, services, configuration, clients HTTP, code asynchrone, threads virtuels ou modèle de programmation Spring.
when_to_use:
  - Écrire des composants Spring : contrôleurs, services ou configuration.
  - Moderniser pendant une revue les patterns Spring 6 vers Spring 7 et Boot 4.
  - Choisir entre RestTemplate, WebClient, RestClient et `@HttpExchange`.
  - Configurer threads virtuels, AOT ou journalisation structurée.
authoritative_references:
  - https://docs.spring.io/spring-boot/reference/index.html
  - https://docs.spring.io/spring-framework/reference/index.html
---

# Conventions Spring Framework 7 et Spring Boot 4

> Java 25 + Spring Framework 7 + Spring Boot 4. Préférer l'idiome moderne sauf ADR contraire.

## Valeurs par défaut

### Packages par fonctionnalité, pas par couche

Les packages de premier niveau sont des contextes délimités ou fonctionnalités,
pas des couches techniques. Dans une fonctionnalité, séparer la surface publiée
`api` de l'implémentation privée.

- Une seule classe d'un type : la garder directement dans le package de la fonctionnalité.
- Plusieurs classes du même type : utiliser `model/`, `repository/` ou `service/` dans la fonctionnalité.
- Sous `api/`, garder le contrôleur ou l'interface publiée au niveau `api` et placer les DTO dans `api/dto/`.
- Les classes des sous-packages privés peuvent être `public` pour fonctionner entre
  sous-packages, mais ArchUnit interdit leur accès depuis une autre fonctionnalité.
- Seul `<feature>.api` est une surface publiée.

```text
com.example.checkout
├── giftcard/
│   ├── api/
│   │   ├── GiftCardController.java
│   │   ├── GiftCardRedemptionService.java
│   │   ├── dto/
│   │   └── exception/
│   ├── model/
│   ├── repository/
│   └── service/
├── order/
│   ├── api/
│   └── service/
└── shared/
    └── exception/
```

Ne jamais créer à la racine `controller/`, `service/`, `repository/`, `model/`,
`dto/` ou `util/`. Ces noms sont autorisés **dans** une fonctionnalité lorsqu'ils
regroupent plusieurs classes. Les fonctionnalités dépendent uniquement de l'API
des autres ; préférer `ApplicationEventPublisher` pour une intégration sans réponse.

### Injection de dépendances

- Injection par constructeur uniquement, jamais par champ ni setter sauf contrainte du framework.
- Un champ `final` par dépendance et un constructeur explicite ; Lombok est interdit.

```java
@Service
public class CheckoutService {
    private final OrderRepository orders;

    public CheckoutService(OrderRepository orders) {
        this.orders = orders;
    }
}
```

### Clients HTTP

- Préférer les clients déclaratifs `@HttpExchange` sur `RestClient`.
- Utiliser `WebClient` uniquement pour une chaîne réellement réactive de bout en bout.
- Ne pas utiliser `RestTemplate` dans le nouveau code.
- Créer une interface dédiée par API externe dans le package d'infrastructure.

### Couche web

- Contrôleurs `@RestController`, retournant des records DTO et jamais des entités.
- `@Validated` sur le contrôleur, `@Valid` sur chaque `@RequestBody` et contrainte
  adaptée sur chaque `@PathVariable` et `@RequestParam`.
- Un test doit déclencher chaque contrainte.
- **Ne jamais exposer `Pageable` comme paramètre de contrôleur.** Déclarer `page`,
  `size` et le tri explicitement, les contraindre, puis créer `PageRequest` dans la méthode.

```java
@GetMapping
FooPageResponse list(
    @RequestParam(defaultValue = "0") @PositiveOrZero int page,
    @RequestParam(defaultValue = "25") @Positive @Max(100) int size) {
    return fooService.getPage(PageRequest.of(page, size));
}
```

- **Éviter `ResponseEntity<T>`** sauf si le statut varie à l'exécution. Pour un
  statut fixe, utiliser `@ResponseStatus`. Pour un en-tête, injecter
  `HttpServletResponse` et retourner directement le DTO.
- Traduire les exceptions avec `@RestControllerAdvice` vers une enveloppe unique documentée.

```java
public record ApplyGiftCardRequest(@NotBlank String code, @Min(0) int orderTotalCents) {}
public record ApplyGiftCardResponse(int redeemedCents, int newOrderTotalCents) {}
```

### Persistance

- Spring Data JPA par défaut ; `@Query` pour les lectures non triviales et pas de requête dérivée de plus de trois prédicats.
- Toujours paginer les listes et refuser les requêtes non bornées.
- Utiliser Testcontainers avec `@ServiceConnection` au lieu de surcharges `application-test.yml`.
- Utiliser `Instant` pour les horodatages d'audit, jamais `LocalDateTime`, afin de conserver un instant UTC non ambigu.

### Threads virtuels

Spring Boot 4 les active par défaut pour le serveur web. Les conserver et ne pas
ajouter d'`Executor` sur threads plateforme sans mesure.

### Configuration

- Un record `@ConfigurationProperties` validé par module délimité.
- Pas de `@Value` pour un groupe de paramètres ; le réserver à une primitive isolée.

### Observabilité et AOT

- Journalisation structurée avec `Logger` et paires clé/valeur.
- Métriques via `MeterRegistry`, une par résultat métier.
- Pas de réflexion sur le code applicatif ni d'enregistrement dynamique de beans.
- Toute dynamique nécessaire passe par `RuntimeHintsRegistrar` et figure dans la conception.

## Anti-patterns de revue

- Injection par champ ou Lombok sous toute forme.
- Packages de premier niveau par couche.
- Nouveau `RestTemplate`, entités retournées par les contrôleurs ou corps `Map<String, Object>`.
- `catch (Exception)` transformé en `RuntimeException` sans message.
- `@SpringBootTest` lorsqu'une tranche suffit.
- `Pageable` exposé par un contrôleur ou `ResponseEntity<T>` sans nécessité.
- Contrainte de contrôleur sans test correspondant.
- Interface `FooService` publiée avec une seule implémentation et aucun consommateur externe ; utiliser une classe concrète interne.
- `status().isUnprocessableEntity()` ; utiliser `status().is(422)` avec Spring MVC Test 7.
- `MappingJackson2HttpMessageConverter` dans `standaloneSetup` ; laisser l'auto-configuration Jackson.
- Noms de types pleinement qualifiés dans les signatures ou corps ; ajouter un import et utiliser le nom simple.

## Fonctionnalités Java 25 recommandées

- Records et types scellés pour DTO et domaine.
- Pattern matching dans `switch`.
- Threads virtuels.
- Collections séquencées.

## Interdiction de Lombok

Lombok est **interdit** dans le nouveau code, y compris dans les nouveaux modules
brownfield. Les records, accesseurs et constructeurs Java couvrent les besoins ;
Lombok complique AOT, couverture, mutation, analyse statique et revue des dépendances.

| Lombok | Remplacement |
|---|---|
| `@Data`, `@Value`, `@Builder` sur un DTO | record Java, factory ou constructeur compact |
| `@Getter`, `@Setter` | accesseurs explicites ou ceux du record |
| `@RequiredArgsConstructor`, `@AllArgsConstructor` | constructeur explicite |
| `@Slf4j` | `LoggerFactory.getLogger(...)` |
| `@SneakyThrows` | exception déclarée ou enveloppée avec un message utile |
| `@EqualsAndHashCode`, `@ToString` | record ou implémentation explicite |

Le POM d'un nouveau module ne déclare pas `org.projectlombok:lombok`. Ajouter la
règle ArchUnit correspondante et traiter tout import Lombok comme `must-fix`.
