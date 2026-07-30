# Plan de test : <FEATURE-ID>

> Responsable : `spring-test-engineer` · Phase 5 · Modèle : `.codex/templates/test-plan.template.md`

## Inputs

- Révision de `04-tasks.md` : <git-sha>
- Révision de `05-implementation-log.md` : <git-sha>
- État de la stack : Testcontainers <present|absent> ; source OpenAPI <controllers|file>.

## Test inventory

| Test-ID | Type | Fichier | AC-IDs | Tâche responsable | Statut |
|---|---|---|---|---|---|
| T-001-T1 | tranche (`@WebMvcTest`) | `src/test/java/.../XTest.java` | AC-001 | T-001 | green |
| T-001-T2 | IT (Testcontainers Postgres) | `src/test/java/.../XIT.java` | AC-001 | T-001 | green |
| ARCH-001 | ArchUnit | `src/test/java/.../ArchitectureTest.java` | — | phase 5 | green |
| CONTRACT-001 | diff OpenAPI | `src/test/java/.../OpenApiContractTest.java` | AC-002 | phase 5 | green |
| PROP-001 | génératif (jqwik) | `src/test/java/.../PropertyTest.java` | AC-005 | phase 5 | green |

## Cross-cutting suites added in this phase

### Architecture (ArchUnit)

- Couches : contrôleur → service → dépôt, sans raccourci ni inversion
- Aucune injection de champ : `@Autowired` sur un champ est interdit
- Les entités résident dans `*.domain.model.*`
- Le nom des contrôleurs se termine par `Controller`
- Aucun accès à `..internal..` entre packages de premier niveau ; aucun cycle entre ces packages

### Contract (OpenAPI)

- Source de vérité : `<api/openapi.yaml | généré depuis les contrôleurs>`
- Outil de diff : <plugin openapi-diff>
- Les changements cassants sont `blocker`.

### Integration tests (Testcontainers)

- Conteneurs : Postgres (`@ServiceConnection`), <broker>
- Réutilisation : `withReuse(true)` activé via `~/.testcontainers.properties`
- Horloge fixe et identifiants déterministes pour la reproductibilité

## Coverage strategy

- Seuil par package : **90 % lignes et branches** au minimum ; cible **95 à 100 %**.
- Seuil du nouveau code : **95 %** via le contrôle incrémental.
- Exclusions : code généré et classes de configuration annotées `@ExcludeFromCoverage`.

## Mutation strategy

- Outil : PIT.
- Périmètre : packages touchés par cette fonctionnalité.
- Chaque mutant survivant est revu ; un test est ajouté ou un ADR explique pourquoi il est acceptable.

## Gaps + waivers

> Si le projet ne possède pas Testcontainers, l'outillage OpenAPI ou PIT, documenter l'écart ici et lier l'ADR proposant sa résolution.

- (aucun)

## Sign-off

- [ ] Chaque AC possède au moins un test réussi.
- [ ] Aucun test `@Disabled` sans commentaire `# DisabledReason: <link>`.
- [ ] Toutes les suites transverses réussissent.
- [ ] Revue effectuée par l'utilisateur le <YYYY-MM-DD>.
