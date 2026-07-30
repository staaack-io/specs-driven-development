---
name: spring-code-review-rubric
description: Grille de revue avant commit pour les changements Spring Boot 4. Utilisée par `spring-code-reviewer` pour produire `08-code-review.md`. Couvre traçabilité, architecture, idiomes Spring, erreurs, données, sécurité, tests, clarté et migrations.
when_to_use:
  - Phase 7, revue de code — commande `$review`.
  - Revue avant PR dans un dépôt brownfield qui adopte ce framework.
authoritative_references:
  - .codex/templates/code-review.template.md
  - .agents/skills/spring-boot-4-conventions/SKILL.md
  - .agents/skills/spring-security-baseline/SKILL.md
  - .agents/skills/clarity-over-cleverness/SKILL.md
---

# Grille de revue du code Spring

## Sévérités

- **blocker** — correction obligatoire avant commit : faille, comportement cassé ou contournement d'une porte.
- **major** — correction avant commit OU ADR et dérogation.
- **minor** — correction recommandée ; laisser une note sinon.
- **nit** — préférence ; la mentionner une fois sans insister.

## Dix sections

### 1. Traçabilité

- Chaque fragment du diff correspond à un `AC-NNN` et un `T-NNN`.
- Le périmètre de fichiers est respecté.
- Toute nouvelle API publique possède un test qui référence l'AC.

### 2. Architecture

- Frontières de modules respectées, sans import croisé de `internal`.
- Règles ArchUnit vertes, couches correctes et aucun nouveau cycle.

### 3. Conventions Spring

- Injection par constructeur uniquement.
- Regroupement par fonctionnalité ou domaine, sans packages de premier niveau par couche.
- `@HttpExchange` ou `RestClient`, sans nouveau `RestTemplate`.
- `@MockitoBean`, pas `@MockBean`.
- Aucun `@Autowired` sur champs ou constructeurs.
- Aucun `@SpringBootTest` lorsqu'une tranche suffit.
- Aucun Lombok dans le diff.
- Aucun nom pleinement qualifié dans le code ; utiliser un import et le nom simple.

### 4. Gestion des erreurs

- Traduire les exceptions à la frontière du contrôleur, pas dans le service.
- Une seule enveloppe d'erreur, documentée dans OpenAPI.
- Aucun `catch (Exception e) { throw new RuntimeException(e); }`.
- Exceptions métier contrôlées ou scellées, pas de `RuntimeException` brute.

### 5. Accès aux données

- Aucune requête N+1, listes paginées, migration progressive ou retour arrière documenté.
- Aucun SQL brut concaténé et transactions sur les services, pas les contrôleurs.

### 6. Sécurité

- Appliquer `spring-security-baseline`.
- Aucun secret, validation à la frontière ET dans le service, journaux sensibles masqués et aucune nouvelle CVE haute ou critique.

### 7. Qualité des tests

- Les tests ont échoué pour la bonne raison pendant red.
- Un AC par test si possible, aucun `@Disabled` sans raison et aucune assertion supprimée.
- Couverture maintenue, nouveau code à 95 %, mutants tués ou justifiés et Testcontainers utilisé lorsque requis.

### 8. Clarté plutôt qu'astuce

- Appliquer `clarity-over-cleverness`, utiliser le glossaire du domaine, supprimer le code mort et les blocs commentés.
- Une responsabilité par méthode publique ; 30 lignes maximum comme recommandation, pas comme règle stricte.

### 9. Migration et contrat

- Le diff OpenAPI correspond au code ; tout changement cassant possède un ADR.
- La migration suit `flyway-or-liquibase-detection` et ne modifie aucun script déjà livré.

### 10. Performance

Appliquer `performance-optimization`. Bloquer notamment :

- une liste non paginée ;
- une requête N+1 ;
- un appel HTTP externe sans timeouts explicites ;
- `@Cacheable` sans TTL ni limite de taille ;
- `@Transactional` autour d'un appel HTTP ;
- `synchronized` autour d'une E/S ;
- un changement de pool Hikari sans mesure ;
- un `Counter` utilisé pour une durée au lieu d'un `Timer` ;
- un changement de performance sans profil ni mesure avant/après.

## Format des constats

```markdown
| ID | Severity | Section | File | Line | Finding | Suggested fix |
|----|---------|---------|------|------|---------|---------------|
| F-001 | blocker | security | CheckoutController.java | 47 | `@CrossOrigin("*")` | restreindre les origines |
```

## Verdict

- ✅ **Approve** — aucun blocker ; commit sûr.
- ⚠️ **Approve with waivers** — constats dérogés via les ADR listés.
- ❌ **Request changes** — blocker sans dérogation ; commit bloqué.
