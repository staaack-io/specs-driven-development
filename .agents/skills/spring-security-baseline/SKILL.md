---
name: spring-security-baseline
description: Configuration minimale et référence de revue Spring Security 7. Utiliser pour concevoir ou relire authentification, autorisation, CSRF, CORS, secrets et validation des entrées.
when_to_use:
  - Phase 3, Plan — concevoir l’authentification et l’autorisation d’un endpoint.
  - Phase 7, revue de code — grille de sécurité de `08-code-review.md`.
authoritative_references:
  - https://docs.spring.io/spring-security/reference/index.html
  - https://owasp.org/Top10/
---

# Référence Spring Security

## Déclarations requises pour chaque endpoint

Dans `03-design.md`, préciser pour chaque endpoint nouveau ou modifié :

- **AuthN** : anonyme, Bearer JWT, session ou mTLS ;
- **AuthZ** : rôle, scope ou claim requis ;
- **validation des entrées** : Bean Validation sur le DTO ET invariants dans le service ;
- **sortie** : aucun champ que l'appelant n'est pas autorisé à voir ;
- **audit** : besoin éventuel d'un journal structuré avec `actor`, `subject` et `outcome`.

Si un point est ambigu, écrire une `Q-NNN` au lieu de choisir une valeur par défaut.

## `SecurityFilterChain` de base pour un resource server JWT

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
class SecurityConfig {

    @Bean
    SecurityFilterChain api(HttpSecurity http) throws Exception {
        http
            .securityMatcher("/api/**")
            .authorizeHttpRequests(a -> a
                .requestMatchers("/api/public/**").permitAll()
                .anyRequest().authenticated())
            .oauth2ResourceServer(o -> o.jwt(Customizer.withDefaults()))
            .csrf(csrf -> csrf.disable())
            .sessionManagement(s -> s.sessionCreationPolicy(STATELESS))
            .headers(h -> h
                .contentSecurityPolicy(c -> c.policyDirectives("default-src 'none'"))
                .referrerPolicy(r -> r.policy(STRICT_ORIGIN_WHEN_CROSS_ORIGIN)));
        return http.build();
    }
}
```

Désactiver CSRF **uniquement pour une API sans état**. Avec des sessions, CSRF reste actif.

## Autorisation au niveau méthode

Préférer `@PreAuthorize` avec des claims JWT :

```java
@PreAuthorize("hasAuthority('SCOPE_orders:write') and #orderId == authentication.token.claims['order_id']")
public Order apply(@PathVariable UUID orderId, @Valid @RequestBody ApplyGiftCardRequest req) { ... }
```

## Secrets

- **Ne jamais** commiter de secret. Utiliser des variables d'environnement ou un gestionnaire de secrets.
- `application.yml` référence `${VAR}` et échoue rapidement au démarrage si elle manque.
- Les secrets des conteneurs de test sont jetables.

## Validation des entrées

Deux couches :

1. **Frontière** — Bean Validation sur le DTO et `@Valid` sur la méthode du contrôleur.
2. **Service** — nouvelle vérification des invariants qui dépendent de l'état d'une entité.

Ne jamais faire confiance aux identifiants fournis par le client. Toujours les
résoudre vers un objet métier limité au périmètre de l'appelant.

## Journalisation et observabilité

- Journaliser les événements de sécurité en `INFO` avec des clés structurées.
- Ne jamais journaliser données personnelles, secrets, JWT complet ou numéro de carte complet. Masquer les valeurs sensibles.

## Grille de revue

- [ ] Aucun endpoint sans décision explicite dans `requestMatchers` ; refus par défaut.
- [ ] Aucun `permitAll()` sur un endpoint qui modifie l'état.
- [ ] Aucun SpEL `@PreAuthorize` utilisant sans contrôle une donnée fournie par l'utilisateur.
- [ ] Aucun `@CrossOrigin("*")` dans le code de production.
- [ ] Aucun SQL brut construit par concaténation.
- [ ] Aucun accès réflexif à un bean depuis une entrée utilisateur.
- [ ] Aucun `@JsonProperty` exposant un champ interne d'entité.
- [ ] L'état CSRF correspond au caractère avec ou sans état de l'API.
- [ ] Les données sensibles sont masquées dans les journaux.
- [ ] Aucune nouvelle CVE haute ou critique, ou une dérogation par CVE dans `dependency-check-suppressions.xml`.
