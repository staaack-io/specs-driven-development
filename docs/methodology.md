# Méthodologie — Développement piloté par les spécifications avec Spring Boot 4

La boîte à outils organise la livraison d’une fonctionnalité en **sept phases**.
Chaque phase possède :

- un unique **agent responsable** ;
- un **artefact Markdown numéroté** sous `.specs/<feature-id>/` ;
- un **contrat d’entrée**, qui indique ce qui doit déjà exister ;
- un **contrat de sortie**, qui indique ce qui doit être vrai pour avancer ;
- une **porte de contrôle** appliquée par les instructions du projet Codex, les
  skills, les agents et les hooks.

```text
1. Spécifier → 2. Relire la spec → 3. Planifier, conception et tâches →
4. Implémenter en TDD → 5. Tester → 6. Valider → 7. Relire le code → Commit
```

## Phase 0 — Onboarder un dépôt existant

**Commande Hermes :** `/sdd-onboard`
**Artefacts :** `.specs/_onboarding.md`, `_stack.json`, `_baseline.json`,
`_starter-design.md`, `_known-debt.md`

L'onboarding capture un snapshot statique du dépôt avant la première
fonctionnalité :

1. vérifier un worktree Git sûr et capturer son SHA ;
2. détecter les modules, frameworks, versions et commandes depuis leurs
   manifests ;
3. déléguer les analyses Spring et React/Next.js en lecture seule lorsque ces
   stacks sont prouvées ;
4. consolider architecture, conventions, dette prouvée et inconnues ;
5. publier les cinq artefacts dans une transaction récupérable.

L'agent principal est l'unique écrivain. Aucun build, test, lint, téléchargement
ou script du dépôt n'est exécuté ; aucun code, test, manifeste ou fichier de
configuration n'est modifié. Le branchement et la mesure du harness appartiennent
à `/sdd-wire-harness`.

Pour une fonctionnalité volumineuse, ou Epic, la phase 3 se divise en deux
sous-étapes :

- **3a. Conception globale de l’Epic** : `03-epic-design.md` et
  `03a-epic-roadmap.md` ;
- **3b. Conception détaillée et tâches de chaque tranche** :
  `03-design.md` et `04-tasks.md`.

## Règle transverse des phases 1 à 3 : aucune supposition

`spec-author` et `spring-architect` appliquent une règle stricte de
**non-invention** pendant la spécification, sa revue, la conception et le
découpage en tâches :

- **Ne jamais deviner.** Les critères d’acceptation, règles métier, cas limites,
  noms de champs, valeurs par défaut, erreurs, SLA, contraintes de sécurité,
  intégrations et exigences non fonctionnelles ne peuvent entrer dans un
  artefact que s’ils proviennent du ticket, de la conversation ou du code
  existant.
- **Toujours consigner les questions ouvertes.** Chaque incertitude devient une
  entrée `Q-NNN` sous `## Open Questions`, avec la question, son importance,
  la décision attendue et les options éventuellement identifiées, mais sans
  choisir de réponse.
- **Toujours interroger l’utilisateur** avant de finaliser l’artefact. Les
  réponses passent sous `## Resolved Questions` avec le texte exact de
  l’utilisateur et un horodatage.
- **Aucune valeur par défaut silencieuse.** Une décision réelle vient de
  l’utilisateur ou d’un ADR explicite.
- **Porte de sortie.** Une phase ne peut pas avancer tant qu’un `Q-NNN` reste
  ouvert, sauf report explicite de l’utilisateur avec justification consignée.
- **Invariant d’implémentation.** `spring-implementer` et
  `spring-test-engineer` refusent les tâches dont un critère ou une section de
  conception référence encore un `Q-NNN` non résolu.

Cette règle est imposée par `.codex/templates/`, `.codex/checklists/` et le
hook Codex `block-progress-on-open-questions`.

## Phase 1 — Spécifier

**Responsable :** `spec-author`
**Artefact :** `01-spec.md`
**Skills :** `issue-tracker-ingestion`, `ears-spec-authoring`

Étapes :

1. Demander si le besoin provient d’un ticket Jira, d’une issue GitHub, de
   Linear ou d’un autre outil.
2. Détecter les serveurs MCP disponibles avec
   `.github/scripts/detect-stack.sh --mcp`, puis récupérer le ticket via le
   connecteur approprié. Consigner son URL et son identifiant sous
   `## Source`.
3. Produire `01-spec.md` depuis le modèle avec :
   - `## Source` : lien et copie du ticket ;
   - `## Goal` : objectif en un paragraphe ;
   - `## Acceptance Criteria` : critères EARS-lite identifiés
     `AC-001`, `AC-002`, etc. ;
   - `## Non-Goals` ;
   - `## Glossary` ;
   - `## Open Questions` avec les `Q-NNN` ;
   - `## Resolved Questions`.
4. Présenter les `Q-NNN` à l’utilisateur et consigner ses réponses.

**Contrat de sortie :** chaque critère possède un identifiant, aucun `Q-NNN`
ne reste ouvert et la source est consignée.

## Phase 2 — Relire la spécification

**Responsable :** `spec-author`
**Artefact :** `02-spec-review.md`
**Checklist :** `checklists/spec-review.md`

Examiner la spécification avec la checklist. Toute ambiguïté devient un nouveau
`Q-NNN` et renvoie à la phase 1 pour résolution.

**Contrat de sortie :** toute la checklist est verte et la ligne d’approbation
est présente.

## Phase 3 — Planifier la conception et les tâches

**Responsable :** `spring-architect`
**Artefacts :** `03-design.md`, `04-tasks.md`, plus les artefacts Epic si ce
mode est actif
**Skills :** `spring-boot-4-conventions`, `spring-security-baseline`,
`openapi-contract-first`, `flyway-or-liquibase-detection`,
`adr-authoring`, `spring-task-decomposition`

`03-design.md` contient :

- la vue d’ensemble de l’architecture et les liens vers les ADR MADR sous
  `.specs/<feature-id>/adr/` ;
- la carte des composants Spring : contrôleurs, services, dépôts et événements ;
- les frontières de modules imposées par ArchUnit ;
- une esquisse OpenAPI : requêtes, réponses et codes de statut ;
- le modèle de données et la stratégie Flyway ou Liquibase, jamais les deux ;
- la posture de sécurité ;
- les risques et la stratégie de retour arrière ;
- `## Open Questions` et `## Resolved Questions`.

`04-tasks.md` contient une liste numérotée. Chaque tâche suit ce contrat :

```text
### T-001: <titre court>
- AC-IDs: AC-001, AC-002
- Test-IDs: T-001-T1 (slice), T-001-T2 (IT)
- Files in scope: src/main/java/.../X.java, src/test/java/.../XTest.java
- Dependencies: none | T-000
- Gates: unit, slice, IT (Testcontainers), coverage
- Rollback: revert commit; no schema change
- Notes: ...
```

Une tâche représente environ une à quatre heures de travail. Les tests
transverses à plusieurs tâches appartiennent à la phase 5.

### Mode Epic

Lorsqu’une fonctionnalité est trop grande pour être découpée directement,
`spring-architect` doit produire les artefacts Epic avant les tâches
détaillées :

- `03-epic-design.md` — frontières d’architecture, décisions partagées,
  contraintes transverses et risques globaux ;
- `03a-epic-roadmap.md` — tranches verticales ordonnées, dépendances, objectifs
  des jalons et critères couverts par chaque tranche.

Règles du mode Epic :

1. Ne pas écrire `04-tasks.md` tant que les `Q-NNN` de l’Epic ne sont pas
   résolus ou explicitement différés avec justification.
2. Planifier en détail une tranche après l’autre.
3. Consigner une seule fois les décisions partagées dans des ADR liés depuis les
   artefacts Epic, puis les réutiliser.

**Contrat de sortie :** chaque critère est relié à au moins une tâche ; chaque
tâche déclare ses tests et ses fichiers ; aucun `Q-NNN` ne reste ouvert ; en
mode Epic, la conception globale et la roadmap sont approuvées avant le
découpage détaillé.

## Phase 4 — Implémenter en TDD

**Responsables :** `spring-test-engineer` et `spring-implementer`
**Artefacts :** `05-implementation-log.md` et
`.specs/<feature-id>/.tdd-state.json`
**Commande :** `$build <task-id>`
**Skills :** `tdd-red-green-refactor`, `junit5-testcontainers-patterns`,
`clarity-over-cleverness`

Pour chaque tâche, `$build` orchestre strictement
**rouge → vert → refactorisation → simplification** :

1. **Rouge.** `spring-test-engineer` écrit le plus petit test en échec pour les
   `Test-IDs` de la tâche. L’échec doit survenir pour la raison attendue.
   Consigner l’étape dans `05-implementation-log.md` et
   `.tdd-state.json`.
2. **Vert.** `spring-implementer` écrit le minimum de code de production pour
   rendre le test vert, relance les tests et consigne le résultat.
3. **Refactorisation et simplification.** Refactoriser avec la suite verte, puis
   exécuter `$code-simplify`. Relancer les tests et `mvn -q verify` sur le
   module touché, puis consigner les deux étapes.

Le hook `block-impl-without-failing-test` impose l’invariant rouge avant vert :
une modification du code de production est refusée tant qu’aucun nouveau test
en échec n’a été observé.

## Phase 5 — Tester plus largement

**Responsable :** `spring-test-engineer`
**Artefact :** `06-test-plan.md`
**Skills :** `archunit-rules`, `openapi-contract-first`,
`junit5-testcontainers-patterns`

Ajouter les tests transverses qui ne dépendent pas d’une seule tâche :

- règles ArchUnit sur les frontières, cycles et noms ;
- tests de contrat OpenAPI ;
- tests par propriétés lorsqu’ils sont utiles ;
- tests d’intégration Testcontainers obligatoires lorsqu’il est détecté, gérés
  par Failsafe avec le suffixe `*IT.java`. En son absence, proposer son ajout
  avec un ADR ou utiliser des tranches embarquées en consignant l’écart.

`06-test-plan.md` documente la carte consolidée de la suite et sa justification.

## Phase 6 — Valider

**Responsable :** `spring-validator`
**Artefacts :** `07-validation-report.md`, `07a-traceability.md`
**Skills :** `harness-report-parsing`, `requirements-traceability`,
`jacoco-coverage-policy`, `pit-mutation-tuning`

Exécuter `.github/scripts/harness.sh`, le même script qu’en CI. Lire chaque
rapport, distinguer les régressions des échecs de référence consignés dans
`.specs/_baseline.json`, puis écrire `07-validation-report.md`.

Construire la matrice de traçabilité dans `07a-traceability.md` :

| AC-ID | Tâches | Tests et état | Symboles de code | Portes |
| --- | --- | --- | --- | --- |

Un critère sans test, ou un test ou symbole sans critère associé, produit un
constat qui bloque la phase.

## Phase 7 — Relire le code avant commit

**Responsable :** `spring-code-reviewer`
**Artefact :** `08-code-review.md`
**Skills :** `spring-code-review-rubric`, `clarity-over-cleverness`,
`spring-security-baseline`

Relire le diff au regard de la spécification, de la conception, des conventions,
de la sécurité et de la qualité des tests, y compris les mutants survivants.
Classer les constats en `blocker | major | minor | nit` et conclure par
`approve | request-changes`.

Le commit exige zéro constat bloquant ou majeur, sauf dérogation documentée.
Un verdict `request-changes` renvoie à l’agent d’implémentation ou de test,
puis les phases concernées sont rejouées.

## Références brownfield

`.specs/_baseline.json` consigne les échecs du harness présents avant
l’intégration du framework. Les agents de validation et de revue les considèrent
comme informatifs ; seules les nouvelles régressions bloquent.

## Résumé des phases

| Phase | Artefacts | Responsable | Porte |
| --- | --- | --- | --- |
| 1. Spécifier | `01-spec.md` | `spec-author` | aucun `Q-NNN` ouvert |
| 2. Relire | `02-spec-review.md` | `spec-author` | checklist verte |
| 3. Planifier | conception et tâches | `spring-architect` | critères tracés, questions résolues |
| 4. Implémenter | `05-implementation-log.md` | agents de test et d’implémentation | cycle TDD consigné |
| 5. Tester | `06-test-plan.md` | `spring-test-engineer` | suite transverse cartographiée |
| 6. Valider | rapports de validation et traçabilité | `spring-validator` | harness vert |
| 7. Relire le code | `08-code-review.md` | `spring-code-reviewer` | zéro blocage ou constat majeur |
| 8. Préparer la livraison, facultatif | `09-ship-plan.md` | `spring-code-reviewer` | portes pré-déploiement vertes |

## Phase 8 — Préparer la livraison, facultatif

**Responsable :** `spring-code-reviewer`, sans nouveau rôle
**Artefact :** `09-ship-plan.md`
**Commande :** `$ship`
**Skills :** `shipping-and-launch`, `spring-security-baseline`,
`flyway-or-liquibase-detection`

Produire un plan pré-déploiement qui confirme les sept phases, classe les
migrations, consigne les feature flags, l’observabilité et le retour arrière,
planifie un déploiement progressif et prépare les notes de version.

**L’agent ne déploie jamais.** Il produit le plan et affiche la commande que
l’utilisateur pourra exécuter.

**Contrat de sortie :** les sept sections de `09-ship-plan.md` sont remplies,
chaque porte est `PASS`, chaque migration possède un retour arrière nommé,
chaque nouvel endpoint possède une métrique et une alerte ou une justification,
et un humain a confirmé le responsable du flag, les seuils et les cohortes.

La phase 8 reste facultative et se place après le commit, avant le déclenchement
du déploiement.

## Travail de performance

La performance est une préoccupation transverse, pas une phase. Appliquer
`performance-optimization` lorsque :

- la phase 3 touche un chemin critique, une requête, un appel externe ou un SLO ;
- la phase 4 cible explicitement la performance ;
- la phase 7 recherche des requêtes N+1, listes non bornées, blocages de threads
  virtuels, paginations manquantes ou appels externes non chronométrés.

La règle est **mesurer d’abord** : aucune optimisation ne peut être livrée sans
profil, mesure avant/après et résultat consigné dans
`05-implementation-log.md`.
