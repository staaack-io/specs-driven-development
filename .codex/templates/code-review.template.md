# Revue de code : <FEATURE-ID>

> Responsable : `spring-code-reviewer` · Phase 7 · Skills : `spring-code-review-rubric`, `clarity-over-cleverness`, `spring-security-baseline`
>
> Avant commit. Le commit est bloqué tant qu'il reste un constat `blocker` ou `major`, sauf dérogation documentée.

## Inputs

- Spécification : `01-spec.md`
- Conception : `03-design.md`, ADR sous `adr/`
- Validation : `07-validation-report.md`, `07a-traceability.md`
- Diff : <plage git>

## Rubric application

### 1. Traçabilité de la spécification et des AC

- [ ] Chaque AC correspond à un ou plusieurs tests, vérifié via `07a-traceability.md`.
- [ ] Aucun test orphelin ni code orphelin.

### 2. Architecture

- [ ] Les couches sont respectées : contrôleur → service → dépôt.
- [ ] Les frontières de modules sont respectées ; aucun accès intermodule ne contourne le package d'API publié et aucun import de `..internal..` entre packages.

### 3. Conventions Spring

- [ ] Injection par constructeur uniquement, sans `@Autowired` sur les champs.
- [ ] Regroupement par fonctionnalité/domaine, sans nouveau package de premier niveau `controller`/`service`/`repository`/`model`.
- [ ] Aucun Lombok, donc aucun import `lombok.*` dans le diff.
- [ ] Frontières `@Transactional` correctes, sans transaction imbriquée accidentelle.
- [ ] Aucun `@SpringBootTest` lorsqu'un test par tranche suffit.

### 4. Gestion des erreurs et surface API

- [ ] Les erreurs correspondent à un `code` documenté et à un statut HTTP.
- [ ] Aucune `RuntimeException` brute ne traverse les frontières.
- [ ] OpenAPI reflète la réalité, vérifié par la porte de contrat.

### 5. Accès aux données

- [ ] Aucune requête N+1, vérifié par un test d'intégration ou par inspection.
- [ ] Une pagination existe lorsque les listes peuvent grandir.
- [ ] Les migrations sont uniquement progressives OU réversibles avec justification.

### 6. Sécurité

- [ ] Les entrées sont validées à la frontière du contrôleur.
- [ ] Aucun secret dans le code ou la configuration.
- [ ] L'autorisation est imposée lorsque les AC l'exigent.

### 7. Qualité des tests

- [ ] Les assertions sont fortes ; un simple `assertNotNull` ne remplace pas une vraie vérification.
- [ ] Aucun `Thread.sleep` dans les tests.
- [ ] Les mutants survivants dans les packages modifiés sont traités ou justifiés par ADR.
- [ ] Aucun `@Disabled` sans `# DisabledReason: <link>`.

### 8. Clarté plutôt qu'astuce

- [ ] Aucune indirection inutile ni helper à usage unique, selon le skill `clarity-over-cleverness`.
- [ ] Les idiomes de la bibliothèque standard et de Spring sont préférés aux abstractions spécifiques.
- [ ] Les noms sont évidents et les noms inutilement qualifiés sont raccourcis.
- [ ] Les retours anticipés et clauses de garde réduisent l'imbrication.

### 9. Migration et rétrocompatibilité

- [ ] Les changements de schéma sont rétrocompatibles OU un ADR documente la bascule.
- [ ] Les changements d'API publique sont additifs OU documentés comme cassants.

## Findings

| ID | Sévérité | Fichier:Ligne | Description | Correction proposée |
|---|---|---|---|---|
| F-001 | blocker | `X.java:42` | … | … |
| F-002 | major | `Y.java:13` | … | … |
| F-003 | minor | `Z.java:5` | … | … |
| F-004 | nit | `W.java:1` | … | … |

Sévérités :

- **blocker** — doit être corrigé avant le commit ; aucune dérogation.
- **major** — doit être corrigé OU explicitement dérogé avec justification et ADR si la décision est structurelle.
- **minor** — devrait être corrigé ; peut être différé avec l'identifiant d'une issue de suivi.
- **nit** — laissé à l'appréciation de l'auteur.

## Waivers

- W-001 (pour F-NNN) : justification : <texte> ; ADR : <lien> ; approuvé par l'utilisateur le : <YYYY-MM-DD>

## Verdict

- [ ] **approve** — passer à `/commit`
- [ ] **request-changes** — revenir à `spring-implementer` ou `spring-test-engineer`, puis relancer `$build`/`$test`/`$validate`/`$review` selon le besoin.

Relecteur : `spring-code-reviewer`
Date : <YYYY-MM-DD>
Hash du diff : <git-sha-range>
