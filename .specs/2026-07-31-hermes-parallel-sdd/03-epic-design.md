# Conception Epic : 2026-07-31-hermes-parallel-sdd

> Responsable : `spring-architect` · Phase 3a (mode Epic)
>
> Cette conception porte sur un framework CLI, des skills Python et le runtime
> Hermes. Les rubriques Spring, OpenAPI, persistance applicative et frontend sont
> explicitement sans objet.

## Inputs

- Révision de `01-spec.md` : SHA-256
  `71fd818b8d9e30931ac5203bd3099ec5ecceb6475461b4d494e72674f640a7b6`.
- Révision de `02-spec-review.md` : SHA-256
  `c64ffd8f8af312a50da04a066ee47874a310654753630224a5184a8d5a0e50f2`.
- Verdict de `02-spec-review.md` : `approve`, 286 AC conformes, zéro AC en
  échec et zéro question ouverte.
- Révision du socle relu : `main` à `06ee632`, fusion de la pull request #49
  apportant la CI Hermes autonome.
- État observé de la source Hermes : cinq skills publiables (`sdd-help`,
  `sdd-status`, `sdd-spec`, `sdd-spec-review`, `sdd-plan`), garde atomique de
  l'état TDD v1, runner E2E limité au parcours jusqu'au plan, contrôle de parité
  du profil et CI Python/contrats/documentation.
- Détection de stack : `.github/scripts/detect-stack.sh` retourne
  `{"error":"pom.xml introuvable","searched":"pom.xml"}`. Ce résultat est
  attendu et non bloquant : `Q-006` établit que la topologie Spring/frontend est
  sans objet pour ce framework Python/Hermes.

## Epic Scope

- Dans le périmètre : migration progressive du profil 0.4.8 à 1.0.0 ; commandes
  SDD manquantes ; orchestration durable par Hermes Kanban ; admission par DAG
  et périmètres de fichiers ; exécution séquentielle ou parallèle ; isolation
  Git/Hermes/GitHub par tâche ; état v2 rétrocompatible ; journaux locaux ;
  fan-in transactionnel ; validation, review, ship sans déploiement ; CI,
  publication du profil, exploitation VPS et pilote Super Lily.
- Hors périmètre : second ordonnanceur Python, commande publique
  `/sdd-roles`, écriture concurrente des artefacts partagés, auto-merge,
  déploiement depuis `/sdd-ship`, gateway Hermes système, `sudo`, `--yolo`,
  force-push, reset destructif et choix de topologie applicative Spring ou
  frontend.

## Architecture Boundaries

### Carte des composants

| Frontière | Responsabilité | Entrées publiées | Sorties et dépendances |
|---|---|---|---|
| Distribution SDD | Publier les skills et références embarquées du profil `staaack` | Source canonique `hermes/skills/`, version cible | Copie exacte `skills/` dans le profil, changelog, contrôle de parité |
| Commandes SDD | Exposer le workflow de `/sdd-onboard` à `/sdd-ship` et les commandes méta | `feature-id`, `T-NNN`, `--parallel`, `--max-workers` | Verdicts `approve`/`request-changes`, résultats `PASS`/`FAIL`, artefacts SDD |
| Plan de contrôle Hermes | Ordonner durablement les jobs et leurs reprises | Projet, board explicite, DAG, cartes, clé d'idempotence | États Kanban, blocage, prochaine action, dispatch et diagnostics JSON |
| Admission déterministe | Refuser un job invalide ou concurrent avant écriture | DAG, `Test-IDs`, chemins littéraux relatifs, empreintes | Décision d'admission, verrou, CAS, événements durables |
| Enveloppe de job | Isoler une tâche et son cycle TDD | Carte, issue, branche, worktree, session, skill préchargé | Journal local, logs expurgés, PR de tâche et preuves TDD |
| Pont Kanban–GitHub | Maintenir la correspondance durable entre exécution et suivi humain | Carte de job, issue parente, `gh`, branche | Issue enfant, PR brouillon/prête, checks, reviews et fils |
| Synthesizer de vague | Être l'unique écrivain des artefacts communs | Journaux locaux de tous les jobs fusionnés d'une vague | PR de fan-in, état v2 et artefacts partagés atomiquement cohérents |
| Validation et publication | Appliquer une gate identique avant version et mise à jour VPS | CI, tests, contrats, review et fils | Version de profil publiable ou refus explicite |
| Exploitation VPS | Installer une version validée et exécuter le pilote | Profil publié, SSH contraint, clones propres, boards isolés | Profil installé, gateway utilisateur, statistiques et preuves du pilote |

### Modèle d'interaction

1. Une commande lit la feature et son plan, puis le garde valide le DAG, les
   `Test-IDs` et chaque chemin littéral relatif, sans glob, lien symbolique ni
   sortie du dépôt.
2. Les tâches dont les dépendances sont fusionnées et les périmètres disjoints
   deviennent admissibles. Hermes Kanban reste l'unique ordonnanceur durable.
3. Le répartiteur ouvre au plus deux slots d'écriture. Les analyses en lecture
   seule peuvent utiliser au plus trois agents ; elles ne deviennent jamais des
   writers. Une gate Maven, Next, PIT ou OWASP acquiert l'unique slot de gate
   lourde.
4. Chaque job reçoit exactement une carte, une issue enfant, une branche, un
   worktree natif sous `.worktrees/`, une session Hermes, un journal local et
   une PR. La carte référence le projet, sa carte parente, la branche et la clé
   d'idempotence.
5. Le job exécute RED, vérification de la preuve, GREEN, REFACTOR et SIMPLIFY.
   Il n'écrit que son périmètre et son journal local ; les empreintes avant et
   après chaque phase rendent toute écriture hors périmètre bloquante.
6. La PR passe de brouillon à prête après réussite des tests. Checks, reviews et
   fils sont relus toutes les cinq minutes. Une correction reste sur la même
   branche et reçoit une nouvelle review ; sans review après trente minutes, la
   carte passe à `needs_input`.
7. Aucune fusion n'est automatique. Après gate verte et go humain explicite,
   la PR de tâche peut être fusionnée et sa carte passe à `done`.
8. Quand toutes les cartes de la vague sont `done`, un seul synthesizer produit
   la PR de fan-in et consolide transactionnellement les journaux dans les
   artefacts partagés. La vague suivante reste bloquée jusqu'à fusion du fan-in.

### Contrats d'état et modèle conceptuel

- Le schéma partagé v2 porte le mode `sequential` ou `parallel`, le board, le
  projet, le maximum de workers et, par tâche, les identifiants Kanban, issue,
  branche, PR, phase et statut. Il ne contient ni chemin absolu, transcript,
  token ni secret.
- Pendant la migration, les lecteurs acceptent v1 et v2, les écrivains
  produisent v2 et tout état v2 reste lisible selon le contrat v1. Le retour
  arrière réinstalle le profil précédent sans réécrire ni perdre l'état.
- Les cardinalités de `01-spec.md` sont conservées : une feature possède une
  issue parente et un état partagé ; un job actif au plus par tâche ; un job a
  exactement une carte, une issue enfant, une branche, un worktree, une session,
  un journal et une PR ; une vague a exactement un fan-in ; le VPS a de zéro à
  deux writers actifs et de zéro à une gate lourde.

### Contrats externes

- Hermes 0.19 et son Kanban natif : boards `sdd-framework` et `super-lily`,
  projet et `--board <slug>` toujours explicites.
- Git et GitHub CLI : branches `sdd/<feature-id>/<task-id>-<slug>`, issues
  parent/enfant, PR et réponses thread-aware ; aucune API d'auto-merge.
- GitHub Actions : deux checks actuels aux noms stables, `Hermes tests and skill
  contracts` et `Documentation and diff`. Les checks attendus absents échouent
  et les checks configurés deviennent obligatoires avant fusion.
- Profil Hermes : la source `hermes/skills/` est canonique ; la publication
  exige une comparaison sans différence avec `skills/` dans le dépôt de profil.
- VPS : connexion `ubuntu@179.237.107.15` avec l'identité SSH imposée, GitHub
  CLI authentifié par device/web flow et gateway exclusivement utilisateur.

## Shared Decisions

| Décision | Solutions envisagées | Option retenue | Justification | ADR |
|---|---|---|---|---|
| Ordonnanceur durable | Kanban Hermes ; ordonnanceur Python distinct | Kanban natif Hermes 0.19 | Décision utilisateur `Q-001`, état durable déjà fourni, absence de double source de vérité | [ADR-001](adr/001-use-hermes-kanban.md) |
| Modèle de capacité | Parallélisme non borné ; limite globale ; plafonds séparés | 2 writers, 3 analyses en lecture seule, 1 gate lourde | Capacité VPS approuvée et protection contre l'épuisement mémoire | [ADR-002](adr/002-bound-parallel-capacity.md) |
| Isolation et suivi | Branche partagée ; isolation Git seule ; enveloppe complète par job | Issue, carte, branche, worktree, session et PR propres | Traçabilité, reprise et review indépendante sans collision | [ADR-003](adr/003-isolate-each-job.md) |
| Écriture des artefacts communs | Workers directs ; verrou autour de chaque worker ; journaux locaux et fan-in | Écrivain unique au fan-in transactionnel | Évite les mélanges partiels et maintient un historique rejouable | [ADR-004](adr/004-use-single-writer-fan-in.md) |
| Migration d'état | Bascule immédiate ; double écriture ; double lecture avec écriture v2 | Lecture v1/v2, écriture v2, compatibilité v1 et rollback du profil | Réponse utilisateur `Q-007`, reprise sans migration destructive | [ADR-005](adr/005-migrate-state-with-dual-read.md) |

## Cross-cutting Constraints

### Sécurité et confidentialité

- Les logs de job expurgent secrets, tokens, données personnelles, chemins
  absolus et contenu métier. Aucun token n'entre dans un prompt, un artefact SDD
  ou un fichier versionné.
- Le garde accepte uniquement des chemins littéraux relatifs au dépôt, refuse
  tout glob, lien symbolique, chemin extérieur et argument de contournement.
- Les opérations interdites restent : auto-merge, force-push, reset destructif,
  suppression sans preuve de propreté et d'ascendance, gateway système,
  `sudo`, `--yolo` et déploiement depuis `/sdd-ship`.

### Capacité et délais spécifiés

- Au plus 2 writers, 3 agents d'analyse en lecture seule et 1 gate lourde sur le
  VPS ; `kanban.max_spawn`, `kanban.max_in_progress` et
  `kanban.max_in_progress_per_profile` valent 2.
- Une carte de job a une durée maximale de 45 minutes et au plus 2 nouvelles
  tentatives. Les checks, reviews et fils sont consultés toutes les 5 minutes ;
  l'absence de review pendant 30 minutes produit `needs_input`.
- Aucun SLO de latence ou de débit supplémentaire n'est introduit : la
  spécification contraint la capacité et les délais d'orchestration, pas un SLO
  applicatif.

### Observabilité et gate de publication

- `/sdd-status` expose, par tâche, carte, issue, branche, PR, checks, review,
  blocage et prochaine action. Les boards conservent statistiques et diagnostics
  JSON ; les échecs conservent logs, journal et worktree.
- Un livrable satisfait la gate de publication uniquement si les cinq
  conditions sont vraies : CI obligatoire verte, tests verts, contrats verts,
  review `approve` et zéro fil actionnable.
- Chaque fusion attend un go humain explicite. Une nouvelle review est requise
  après correction. Une version de profil ne peut mettre à jour le VPS qu'après
  fusion et satisfaction de la gate.

## Release Architecture

| Version | Capacité visible | Barrière de sortie |
|---|---|---|
| 0.4.8 | `/sdd-onboard`, CI autonome et parité source/profil | PR #47 validée et fusionnée, profil 0.4.8 revu, autorisé et fusionné |
| 0.5.0 | Runtime v2, pont Kanban–GitHub, `/sdd-epic-plan`, `/sdd-wire-harness` | Contrat runtime fusionné avant les trois PR resynchronisées ; gate de publication |
| 0.6.0 | `/sdd-build` mono-tâche puis réellement parallèle | Cycle TDD prouvé, plafond de writers, PR de tâches et fan-in validés |
| 0.6.1 | `/sdd-code-simplify` | Commande fusionnée et gate de publication satisfaite |
| 0.7.0 | `/sdd-test` et `/sdd-validate` | `/sdd-test` fusionné avant `/sdd-validate`, harness disponible, gate satisfaite |
| 0.8.0 | `/sdd-review` et `/sdd-ship` sans déploiement | `/sdd-review` fusionné avant `/sdd-ship`, rapport unique et gate satisfaite |
| 0.9.0 | Candidat complet prouvé par E2E onboard→ship | Parallélisme, dépendance et reprise injectée validés |
| 1.0.0 | Profil stable après pilote Super Lily | AC-226 à AC-230 démontrés, sans OOM, perte ni déploiement automatique |

## Risks and Mitigations

| Risque | Probabilité | Impact | Réduction du risque | Responsable |
|---|---|---|---|---|
| Deux jobs touchent le même fichier ou sortent du dépôt | Moyenne | Élevé | Normalisation, chemins littéraux, contrôle de chevauchement et empreintes avant/après | Garde commun |
| État partagé partiellement écrit après interruption | Moyenne | Élevé | Journal local d'abord, verrou, CAS, marqueur transactionnel, fan-in unique et reprise idempotente | Synthesizer |
| Double source de vérité entre Hermes, GitHub et l'état SDD | Moyenne | Élevé | Identifiants croisés sur carte et état, clé d'idempotence et transitions durables | Pont Kanban–GitHub |
| Épuisement mémoire ou contention du VPS | Moyenne | Élevé | Deux writers, une gate lourde, trois analyses au plus, sandbox préalable et pilote sans OOM | Exploitation |
| Review ou go humain allonge le chemin critique | Élevée | Moyen | États visibles, polling toutes les cinq minutes et passage `needs_input` à trente minutes | Orchestrateur et humain |
| Régression du profil pendant la migration v1/v2 | Moyenne | Élevé | Parité, lecture v1/v2, écriture v2 compatible v1 et retour au profil précédent | Mainteneur du profil |
| Nettoyage détruit des preuves ou du travail non fusionné | Faible | Élevé | Conservation en échec et suppression uniquement après propreté et ascendance à `origin/main` | Exploitation |
| CI locale non reproductible sans dépendances Python épinglées | Moyenne | Moyen | `requirements-ci.txt`, Python 3.11 en CI et installation épinglée avant les tests | Mainteneur CI |

## Open Questions

- (aucune)

## Resolved Questions

- `Q-001` : Hermes Kanban est l'ordonnanceur durable.
- `Q-002` : GitHub Issues suit features et tâches.
- `Q-003` : le VPS accepte au plus deux writers.
- `Q-004` : les gates lourdes sont sérialisées.
- `Q-005` : aucune PR n'est fusionnée automatiquement.
- `Q-006` : les topologies Spring/frontend sont sans objet.
- `Q-007` : lecture v1/v2, écriture v2 et rollback par profil précédent
  compatible v1.
- `Q-008` : les cinq catégories de données sensibles sont expurgées.
- `Q-009` : tout glob est interdit et les chemins sont littéraux et relatifs.
- `Q-010` : la gate de publication et le pilote réussi utilisent les preuves
  exactes de `01-spec.md`.

## Sign-off

- [x] L'architecture Epic a été revue avec l'utilisateur le 2026-08-01
  (instruction : « Continue à migrer »).
- [x] Toutes les Q-NNN au niveau Epic sont résolues ou différées avec
  justification.
