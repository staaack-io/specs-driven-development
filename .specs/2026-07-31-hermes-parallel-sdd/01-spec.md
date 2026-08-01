# Spécification : 2026-07-31-hermes-parallel-sdd — Migration SDD complète avec exécution parallèle sous Hermes

> Responsable : `spec-author` · Phase 1 · Modèle : `.codex/templates/spec.template.md`
>
> **Aucune invention.** Si une information ne figure ni dans la source, ni dans la conversation, ni dans le code existant, elle doit être enregistrée comme `Q-NNN`.

## Source

- Outil de suivi : ad-hoc
- Identifiant : `2026-07-31-hermes-parallel-sdd`
- URL : sans objet — texte joint à la demande utilisateur
- Pièce source : `/Users/cor/.codex/attachments/ba6c1e9c-7bf7-424b-948f-7c887b271ee4/pasted-text.txt`
- Date de capture : 2026-07-31
- Résumé de la capture :
  > Migration SDD complète avec exécution parallèle sous Hermes
  >
  > Utiliser le Kanban natif de Hermes 0.19 comme ordonnanceur durable. Ne pas développer un second ordonnanceur Python.
  >
  > Limiter le VPS à 2 jobs écrivains simultanés, 3 agents seulement pour les analyses en lecture seule, et 1 seule gate lourde à la fois.
  >
  > Isoler chaque tâche dans un worktree, une branche, une session Hermes, une issue GitHub et une PR propres.
  >
  > Conserver un écrivain unique pour .tdd-state.json, 05-implementation-log.md et les autres artefacts partagés.
  >
  > Ne jamais fusionner automatiquement : chaque fusion attend un go explicite.

Le texte intégral de la pièce source fait autorité pour les commandes, séquences de livraison, contraintes VPS et scénarios de test détaillés repris ci-dessous.

## Goal

Faire évoluer le framework SDD et son profil Hermes des versions 0.4.8 à 1.0.0 afin d'exécuter durablement des tâches indépendantes en parallèle sous le Kanban natif de Hermes, avec au plus deux écrivains, des espaces de travail et cycles GitHub isolés par tâche, un état partagé transactionnel, des gates lourdes sérialisées, une reprise sans perte et une validation humaine avant toute fusion, puis prouver le parcours complet de l'onboarding à la préparation de livraison sur un pilote Super Lily sans déploiement automatique.

## Acceptance Criteria

### Ordonnancement, capacité et interfaces SDD

- **AC-001** — Le framework SDD doit utiliser le Kanban natif de Hermes 0.19 comme ordonnanceur durable.
- **AC-002** — Le framework SDD doit s'abstenir de créer un second ordonnanceur Python.
- **AC-003** — Le framework SDD doit réserver `delegate_task` aux sous-analyses internes d'un job.
- **AC-004** — Tant que le framework s'exécute sur le VPS, il doit limiter à deux le nombre de jobs écrivains simultanés.
- **AC-005** — Tant que des analyses en lecture seule sont déléguées, le framework doit limiter à trois le nombre d'agents d'analyse.
- **AC-006** — Tant que des gates lourdes sont exécutées, le framework doit n'en exécuter qu'une à la fois.
- **AC-007** — Le dépôt `specs-driven-development` doit avoir GitHub Issues activé.
- **AC-008** — Le dépôt Super Lily doit avoir GitHub Issues activé avant le pilote.
- **AC-009** — Le framework SDD doit conserver les commandes SDD existantes.
- **AC-010** — Le profil SDD 0.4.8 doit publier la commande `/sdd-onboard`.
- **AC-011** — Le profil SDD 0.5.0 doit publier la commande `/sdd-wire-harness`.
- **AC-012** — Le profil SDD 0.5.0 doit publier la commande `/sdd-epic-plan`.
- **AC-013** — Le profil SDD 0.6.0 doit publier la commande `/sdd-build` avec son mode parallèle.
- **AC-014** — Le profil SDD 0.6.1 doit publier la commande `/sdd-code-simplify`.
- **AC-015** — Le profil SDD 0.7.0 doit publier la commande `/sdd-test`.
- **AC-016** — Le profil SDD 0.7.0 doit publier la commande `/sdd-validate`.
- **AC-017** — Le profil SDD 0.8.0 doit publier la commande `/sdd-review`.
- **AC-018** — Le profil SDD 0.8.0 doit publier la commande `/sdd-ship`.
- **AC-019** — Lorsque `/sdd-build <feature-id> <T-NNN>` est invoqué, le framework SDD doit exécuter la tâche désignée séquentiellement.
- **AC-020** — Lorsque `/sdd-build <feature-id> --parallel` est invoqué, le framework SDD doit lancer toutes les tâches prêtes admissibles.
- **AC-021** — Lorsque l'option `--max-workers` est fournie à `/sdd-build`, le framework SDD doit accepter uniquement la valeur `1` ou `2`.
- **AC-022** — Lorsque l'option `--max-workers` est omise sur le VPS, le framework SDD doit utiliser deux workers.
- **AC-023** — Tant que `/sdd-build` s'exécute sur le VPS, le framework SDD doit plafonner le nombre de workers à deux.
- **AC-024** — Lorsque `/sdd-status <feature-id>` est invoqué, le framework SDD doit afficher la carte Kanban de chaque tâche.
- **AC-025** — Le framework SDD doit s'abstenir de créer une commande `/sdd-roles`.
- **AC-026** — Tant qu'un skill SDD utilise un rôle, le framework doit conserver ce rôle comme référence interne embarquée dans le skill.

### Admission d'une tâche et isolation d'un job

- **AC-027** — Tant qu'une dépendance d'une tâche n'est pas fusionnée, le framework SDD doit refuser de rendre cette tâche parallélisable.
- **AC-028** — Si les `files_in_scope` normalisés de deux tâches d'une vague se chevauchent, alors le framework SDD doit refuser leur exécution parallèle.
- **AC-029** — Lorsque deux tâches prêtes ont des `files_in_scope` normalisés disjoints, le framework SDD doit permettre leur admission dans la même vague, sous réserve du plafond de workers.
- **AC-030** — Lorsque le framework crée un job parallèle, il doit créer une issue enfant liée à l'issue parente de la feature.
- **AC-031** — Lorsque le framework crée un job parallèle, il doit créer une carte Kanban portant une clé d'idempotence.
- **AC-032** — Lorsque le framework crée un job parallèle, il doit créer une branche nommée `sdd/<feature-id>/<task-id>-<slug>`.
- **AC-033** — Lorsque le framework crée un job parallèle, il doit créer un worktree Hermes natif sous `.worktrees/`.
- **AC-034** — Lorsque le framework crée un job parallèle, il doit créer une session Hermes propre à ce job.
- **AC-035** — Lorsque le framework crée un job parallèle, il doit produire des logs propres à ce job dont sont expurgés les secrets, les tokens, les données personnelles, les chemins absolus et le contenu métier.
- **AC-036** — Lorsque le framework crée un job parallèle, il doit créer une pull request en brouillon propre à ce job.
- **AC-037** — Lorsque le test-engineer intervient dans un job, il doit écrire uniquement le test rouge de la tâche.
- **AC-038** — Lorsque le test-engineer a écrit le test rouge, l'agent principal doit vérifier la preuve RED avant toute intervention de l'implementer.
- **AC-039** — Lorsque la preuve RED d'un job est vérifiée, l'implementer doit écrire uniquement le code minimal nécessaire à la réussite du test.
- **AC-040** — Lorsque l'implementer a produit le code minimal, l'agent principal doit exécuter successivement GREEN, REFACTOR puis SIMPLIFY dans le même job.
- **AC-041** — Tant qu'un worker exécute une tâche, il doit s'abstenir de modifier `04-tasks.md`.
- **AC-042** — Tant qu'un worker exécute une tâche, il doit s'abstenir de modifier `.tdd-state.json`.
- **AC-043** — Tant qu'un worker exécute une tâche, il doit s'abstenir de modifier `05-implementation-log.md`.
- **AC-044** — Lorsque l'état d'un job change, le worker doit écrire l'événement dans un journal immuable propre à la tâche sous `.specs/<feature-id>/jobs/<T-ID>/`.
- **AC-045** — Lorsque toutes les pull requests d'une vague sont fusionnées, un synthesizer unique doit créer une pull request de fan-in.
- **AC-046** — Lorsque le synthesizer produit la pull request de fan-in, il doit actualiser transactionnellement les artefacts partagés.
- **AC-047** — Tant que la pull request de fan-in d'une vague n'est pas fusionnée, le framework SDD doit empêcher le démarrage de la vague suivante.

### État partagé, gardes et reprise

- **AC-048** — Le framework SDD doit faire évoluer `.tdd-state.json` vers un schéma v2 rétrocompatible.
- **AC-049** — Le schéma d'état v2 doit représenter le mode `sequential` ou `parallel`.
- **AC-050** — Le schéma d'état v2 doit référencer le board et le projet Hermes de la feature.
- **AC-051** — Le schéma d'état v2 doit représenter le maximum de workers autorisé.
- **AC-052** — Le schéma d'état v2 doit représenter pour chaque tâche son identifiant Kanban.
- **AC-053** — Le schéma d'état v2 doit représenter pour chaque tâche son issue.
- **AC-054** — Le schéma d'état v2 doit représenter pour chaque tâche sa branche.
- **AC-055** — Le schéma d'état v2 doit représenter pour chaque tâche sa pull request.
- **AC-056** — Le schéma d'état v2 doit représenter pour chaque tâche sa phase.
- **AC-057** — Le schéma d'état v2 doit représenter pour chaque tâche son statut.
- **AC-058** — Le schéma d'état v2 doit s'abstenir de contenir un chemin absolu.
- **AC-059** — Le schéma d'état v2 doit s'abstenir de contenir un transcript.
- **AC-060** — Le schéma d'état v2 doit s'abstenir de contenir un token ou un secret.
- **AC-061** — Avant d'admettre une tâche, le garde commun doit valider le DAG.
- **AC-062** — Avant d'admettre une tâche, le garde commun doit valider ses `Test-IDs`.
- **AC-063** — Avant d'admettre une tâche, le garde commun doit valider son périmètre de fichiers.
- **AC-064** — Si un élément de `files_in_scope` contient un glob, alors le garde commun doit refuser la tâche.
- **AC-065** — Si un périmètre de fichiers traverse un lien symbolique, alors le garde commun doit refuser la tâche.
- **AC-066** — Si un périmètre de fichiers contient un chemin hors dépôt, alors le garde commun doit refuser la tâche.
- **AC-067** — Si deux jobs candidats ont des périmètres de fichiers qui se chevauchent, alors le garde commun doit empêcher leur écriture simultanée.
- **AC-068** — Lorsque l'état partagé est actualisé, le garde commun doit protéger l'écriture par verrou.
- **AC-069** — Lorsque l'état partagé est actualisé, le garde commun doit appliquer un contrôle compare-and-swap.
- **AC-070** — Lorsque l'état partagé est actualisé, le garde commun doit inscrire l'opération dans un journal durable.
- **AC-071** — Lorsqu'une exécution est interrompue, le garde commun doit permettre sa reprise.
- **AC-072** — Lorsqu'une opération déjà enregistrée est rejouée, le garde commun doit préserver l'idempotence.
- **AC-073** — Avant chaque phase d'un job, le garde commun doit relever l'empreinte des fichiers hors périmètre.
- **AC-074** — Après chaque phase d'un job, le garde commun doit refuser une modification détectée hors périmètre.
- **AC-075** — Tant qu'une spécification contient des questions ouvertes, le garde de phase doit empêcher le passage à la phase suivante.
- **AC-076** — Si une écriture de production est tentée sans preuve de test rouge, alors le garde RED doit la refuser.
- **AC-077** — Si un argument de contournement est fourni à une commande SDD, alors la validation structurée des arguments doit le refuser.
- **AC-078** — Lorsque le cycle TDD d'une tâche progresse, le framework SDD doit enregistrer d'abord la transition dans le journal local de la tâche.
- **AC-079** — Lorsque les journaux locaux d'une vague sont consolidés, seul le fan-in transactionnel doit modifier les artefacts partagés.
- **AC-080** — Tant qu'une gate Maven, Next, PIT ou OWASP est en cours, le framework SDD doit empêcher le démarrage d'une autre gate lourde.

### Phase 0 — CI, onboarding et profil 0.4.8

- **AC-081** — Avant toute fusion de fonctionnalité, chacun des deux dépôts concernés doit disposer d'une pull request CI indépendante.
- **AC-082** — Lorsque la CI d'un dépôt s'exécute, elle doit vérifier les tests Python et les contrats des skills.
- **AC-083** — Lorsque la CI d'un dépôt s'exécute, elle doit valider les frontmatters.
- **AC-084** — Lorsque la CI d'un dépôt s'exécute, elle doit exécuter Markdownlint.
- **AC-085** — Les checks CI obligatoires doivent avoir des noms stables.
- **AC-086** — Si un workflow CI attendu est absent, alors le contrôle doit produire un échec.
- **AC-087** — Lorsque la CI est fusionnée, la branche de la pull request #47 doit fusionner normalement `main` afin de déclencher ses checks.
- **AC-088** — Lorsque les checks de la pull request #47 sont disponibles, le processus doit demander une review Codex.
- **AC-089** — Après la demande de review Codex de la pull request #47, le processus doit attendre au moins cinq minutes avant de lire les fils.
- **AC-090** — Lorsque les fils de review de la pull request #47 sont lus, le processus doit les interpréter en tenant compte de leur filiation.
- **AC-091** — Lorsqu'un fil de review de la pull request #47 demande une correction, le processus doit corriger la branche concernée.
- **AC-092** — Lorsqu'un fil de review de la pull request #47 reçoit une correction, le processus doit répondre directement dans ce fil.
- **AC-093** — Après une correction de review sur la pull request #47, le processus doit attendre une nouvelle review.
- **AC-094** — Tant qu'aucun go explicite n'est donné pour la pull request #47, le processus doit empêcher sa fusion.
- **AC-095** — Lorsque la pull request #47 est fusionnée, le processus doit créer une pull request de profil séparée.
- **AC-096** — La pull request de profil 0.4.8 doit copier exactement `hermes/skills/sdd-onboard` vers `skills/sdd-onboard`.
- **AC-097** — La pull request de profil 0.4.8 doit publier la version 0.4.8.
- **AC-098** — La pull request de profil 0.4.8 doit démontrer la parité source/profil par une comparaison sans différence entre `hermes/skills/sdd-onboard` et `skills/sdd-onboard`.
- **AC-099** — La pull request de profil 0.4.8 doit exécuter dans le profil les mêmes tests que dans la source.
- **AC-100** — Tant que la pull request de profil 0.4.8 n'a pas été revue, autorisée et fusionnée, le processus doit empêcher la mise à jour du VPS.

### Phase 1 — socle parallèle, Epic et harness

- **AC-101** — La pull request de contrat runtime doit introduire le schéma d'état v2.
- **AC-102** — La pull request de contrat runtime doit introduire les journaux locaux aux tâches.
- **AC-103** — La pull request de contrat runtime doit introduire le garde de fichiers.
- **AC-104** — La pull request de contrat runtime doit permettre la reprise après interruption.
- **AC-105** — La pull request de contrat runtime doit remplacer les protections fondées sur les hooks par les gardes déterministes spécifiés.
- **AC-106** — Lorsque le contrat runtime est fusionné, le processus doit permettre le développement parallèle du pont Hermes Kanban–GitHub, de `/sdd-epic-plan` et de `/sdd-wire-harness` dans trois pull requests distinctes.
- **AC-107** — Lorsque `/sdd-epic-plan` produit son verdict, il doit utiliser le verdict Hermes `approve`.
- **AC-108** — Lorsque `/sdd-wire-harness` est invoqué avec `--dry-run`, il doit décrire les changements sans les appliquer.
- **AC-109** — Lorsque `/sdd-wire-harness` applique une configuration, le rôle intégrateur doit rendre observable soit l'ensemble complet antérieur, soit l'ensemble complet nouveau, jamais un mélange des deux.
- **AC-110** — Lorsque le pont GitHub démarre un job, il doit créer l'issue avec `gh`.
- **AC-111** — Lorsque le pont GitHub prépare la contribution d'un job, il doit créer la pull request avec `gh`.
- **AC-112** — Lorsque le pont GitHub obtient l'identifiant d'une issue, il doit le stocker dans la carte Kanban.
- **AC-113** — Lorsque le pont GitHub obtient l'identifiant d'une issue, il doit le stocker dans l'état SDD.
- **AC-114** — Lorsque les tests d'un job réussissent, le pont GitHub doit passer sa pull request de brouillon à prête.
- **AC-115** — Tant qu'une pull request de job attend ses checks, le pont GitHub doit consulter les checks toutes les cinq minutes.
- **AC-116** — Lorsqu'une review demande une correction, le pont GitHub doit appliquer la correction sur la même branche.
- **AC-117** — Lorsqu'une correction répond à un fil de review, le pont GitHub doit répondre directement dans ce fil.
- **AC-118** — Après une correction de review, le pont GitHub doit attendre une nouvelle review.
- **AC-119** — Si aucune review n'est disponible après trente minutes, alors le pont GitHub doit placer la carte dans l'état `needs_input`.
- **AC-120** — Le pont GitHub doit s'abstenir de fusionner une pull request.
- **AC-121** — Tant que la pull request de contrat runtime n'est pas fusionnée, le processus doit empêcher la fusion des trois pull requests de phase 1.
- **AC-122** — Lorsque la pull request de contrat runtime est fusionnée, chacune des trois pull requests de phase 1 doit être resynchronisée avec `main` avant sa fusion dans n'importe quel ordre.
- **AC-123** — Lorsque les livrables de la phase 1 sont fusionnés et satisfont la gate de validation de publication, le profil doit publier la version 0.5.0.

### Phase 2 — build réellement parallèle

- **AC-124** — La pull request `/sdd-build` mono-tâche doit orchestrer séquentiellement les rôles test-engineer puis implementer adaptés à Spring ou React.
- **AC-125** — Lorsque `/sdd-build` mono-tâche s'exécute, il doit respecter le cycle RED → GREEN → REFACTOR → SIMPLIFY.
- **AC-126** — Lorsque `/sdd-build` mono-tâche progresse, il doit conserver les preuves des `Test-IDs`.
- **AC-127** — Tant qu'un rôle de `/sdd-build` mono-tâche travaille, il doit s'abstenir d'accéder directement aux artefacts partagés.
- **AC-128** — Lorsque la pull request `/sdd-build` mono-tâche est fusionnée, le processus doit permettre le développement parallèle de l'orchestrateur `/sdd-build --parallel` et de `/sdd-code-simplify`.
- **AC-129** — Lorsque l'orchestrateur crée une carte, il doit utiliser explicitement le projet Kanban parent.
- **AC-130** — Lorsque l'orchestrateur crée une carte, il doit lui associer la branche du job.
- **AC-131** — Lorsque l'orchestrateur crée une carte, il doit fixer sa durée maximale à 45 minutes.
- **AC-132** — Lorsque l'orchestrateur crée une carte, il doit autoriser deux nouvelles tentatives au maximum.
- **AC-133** — Lorsque l'orchestrateur crée une carte, il doit précharger le skill requis par le job.
- **AC-134** — Lorsqu'une pull request de tâche est prête et revue, l'orchestrateur doit placer sa carte en attente de go.
- **AC-135** — Tant qu'aucun go explicite n'est donné, l'orchestrateur doit empêcher la fusion d'une pull request de tâche.
- **AC-136** — Lorsque la fusion d'une pull request de tâche a été explicitement autorisée et réalisée, l'orchestrateur doit passer sa carte à `done`.
- **AC-137** — Lorsque toutes les cartes d'une vague sont `done`, le synthesizer doit produire la pull request de fan-in.
- **AC-138** — Lorsque le build parallèle est fusionné et satisfait la gate de validation de publication, le profil doit publier la version 0.6.0.
- **AC-139** — Lorsque `/sdd-code-simplify` est fusionné et satisfait la gate de validation de publication, le profil doit publier la version 0.6.1.

### Phase 3 — test et validation

- **AC-140** — Lorsque le contrat de phase 3 est figé, le processus doit permettre le développement parallèle de `/sdd-test` et `/sdd-validate`.
- **AC-141** — Tant que la pull request `/sdd-test` n'est pas fusionnée, le processus doit empêcher la fusion de `/sdd-validate`.
- **AC-142** — Tant que `/sdd-test` s'exécute, il doit limiter ses écritures aux tests et à `06-test-plan.md`.
- **AC-143** — Tant que `/sdd-validate` s'exécute, il doit attendre que `/sdd-wire-harness` soit disponible.
- **AC-144** — Lorsque les validateurs Spring et React ont terminé leur fan-in, `/sdd-validate` doit écrire uniquement les rapports communs.
- **AC-145** — Lorsque le framework rend un verdict de décision, il doit utiliser uniquement `approve` ou `request-changes`.
- **AC-146** — Lorsque le framework rend un résultat technique, il doit utiliser uniquement `PASS` ou `FAIL`.
- **AC-147** — Lorsque les livrables de la phase 3 sont fusionnés et satisfont la gate de validation de publication, le profil doit publier la version 0.7.0.

### Phase 4 — review, ship et parcours E2E

- **AC-148** — Lorsque les contrats de fixtures sont disponibles, le processus doit permettre le développement parallèle de `/sdd-review` et `/sdd-ship`.
- **AC-149** — Tant que la pull request `/sdd-review` n'est pas fusionnée, le processus doit empêcher la fusion de `/sdd-ship`.
- **AC-150** — Lorsque `/sdd-review` s'exécute, il doit déléguer les lectures spécialisées Spring et React.
- **AC-151** — Lorsque les lectures spécialisées de `/sdd-review` sont terminées, la commande doit produire un rapport unique.
- **AC-152** — Lorsque `/sdd-ship` s'exécute, il doit préparer le retour arrière.
- **AC-153** — Lorsque `/sdd-ship` s'exécute, il doit s'abstenir de déployer.
- **AC-154** — Lorsque `/sdd-review` et `/sdd-ship` sont fusionnés et satisfont la gate de validation de publication, le profil doit publier la version 0.8.0.
- **AC-155** — Lorsque le runner E2E est étendu, il doit traverser le parcours de `/sdd-onboard` à `/sdd-ship`.
- **AC-156** — Lorsque le runner E2E exerce le parallélisme full-stack, il doit exécuter simultanément une tâche backend et une tâche frontend disjointes.
- **AC-157** — Lorsque le runner E2E exerce une dépendance, il doit empêcher la tâche dépendante de démarrer avant la fusion de sa dépendance.
- **AC-158** — Lorsqu'un échec est injecté dans le runner E2E, le framework doit reprendre le parcours sans perdre les changements ni les preuves d'un livrable ayant satisfait la gate de validation de publication.
- **AC-159** — Lorsque le runner E2E complet satisfait la gate de validation de publication, le profil doit publier la version 0.9.0 comme candidat complet.
- **AC-160** — Tant que le pilote réel Super Lily ne satisfait pas tous les critères `AC-226` à `AC-230`, le profil doit empêcher la publication de la version 1.0.0.

### Déploiement et exploitation du VPS

- **AC-161** — Avant d'utiliser l'intégration GitHub sur le VPS, l'exploitation doit installer GitHub CLI depuis le dépôt Debian officiel GitHub CLI conformément à la documentation officielle citée dans la source.
- **AC-162** — Lorsque GitHub CLI est installé sur le VPS, l'exploitation doit authentifier le compte GitHub par le device/web flow officiel avec le protocole Git SSH et les portées `repo`, `read:org` et `workflow`.
- **AC-163** — Tant qu'une authentification GitHub est effectuée, aucun token ne doit être copié dans un prompt, un artefact SDD ou un fichier versionné.
- **AC-164** — Lorsque l'authentification GitHub du VPS est terminée, l'exploitation doit en vérifier le statut.
- **AC-165** — Lorsque la mise à jour du profil VPS est autorisée, l'exploitation doit se connecter avec l'identité `/Users/cor/.ssh/hermes-agent`, en mode batch, avec cette identité seule et avec vérification stricte de la clé hôte.
- **AC-166** — Avant de mettre à jour le profil `staaack`, l'exploitation doit relever sa version courante.
- **AC-167** — Lorsque la version publiée du profil concerné est fusionnée et satisfait la gate de validation de publication, l'exploitation doit mettre à jour le profil `staaack`.
- **AC-168** — Après la mise à jour du profil `staaack`, l'exploitation doit relever la version installée.
- **AC-169** — Lorsque Hermes est appelé par un script SSH non interactif, le script doit utiliser un shell de connexion ou le chemin absolu `/home/ubuntu/.local/bin/hermes`.
- **AC-170** — Lorsque les limites Kanban du profil `staaack` sont configurées, `kanban.max_spawn` doit valoir `2`.
- **AC-171** — Lorsque les limites Kanban du profil `staaack` sont configurées, `kanban.max_in_progress` doit valoir `2`.
- **AC-172** — Lorsque les limites Kanban du profil `staaack` sont configurées, `kanban.max_in_progress_per_profile` doit valoir `2`.
- **AC-173** — Lorsque les limites Kanban du profil `staaack` sont configurées, `kanban.failure_limit` doit valoir `2`.
- **AC-174** — Après la configuration des limites Kanban, l'exploitation doit exécuter la vérification de configuration Hermes.
- **AC-175** — Tant que le profil `staaack` exécute le framework SDD, `delegation.max_spawn_depth` doit rester égal à `1`.
- **AC-176** — Tant que le profil `staaack` exécute le framework SDD, `subagent_auto_approve` doit rester désactivé.
- **AC-177** — Tant que le profil `staaack` exécute le framework SDD, l'option `--yolo` doit être interdite.
- **AC-178** — Avant de créer les boards persistants, l'exploitation doit préparer sous `~/workspaces` des clones dont aucun fichier n'est modifié, indexé ou non suivi.
- **AC-179** — Lorsque l'environnement SDD est initialisé, l'exploitation doit disposer d'un board isolé `sdd-framework` associé au projet et au clone `specs-driven-development`.
- **AC-180** — Lorsque l'environnement Super Lily est initialisé, l'exploitation doit disposer d'un board isolé `super-lily` associé au projet et au clone Super Lily.
- **AC-181** — Lorsque les scripts Hermes ciblent un board, ils doivent toujours fournir explicitement `--board <slug>`.
- **AC-182** — Si le board ou le projet demandé existe déjà, alors l'exploitation doit l'inspecter et le réutiliser.
- **AC-183** — Avant d'activer un service permanent, l'exploitation doit exécuter un dispatch Super Lily à blanc avec un maximum de deux jobs.
- **AC-184** — Lorsque le dispatch à blanc réussit, l'exploitation doit exécuter un dispatch Super Lily réel avec un maximum de deux jobs.
- **AC-185** — Lorsque le dispatch réel est lancé, l'exploitation doit surveiller les cartes assignées au profil `staaack`.
- **AC-186** — Après le dispatch réel, l'exploitation doit consulter les statistiques du board Super Lily.
- **AC-187** — Tant que deux jobs sandbox parallèles n'ont pas chacun satisfait la gate de validation de publication, l'exploitation doit empêcher l'installation du gateway permanent.
- **AC-188** — Lorsque deux jobs sandbox parallèles ont réussi, l'exploitation doit installer le gateway utilisateur avec démarrage immédiat et au login.
- **AC-189** — Après l'installation du gateway utilisateur, l'exploitation doit en vérifier le statut.
- **AC-190** — Le processus d'exploitation doit s'abstenir d'installer un gateway système Hermes.
- **AC-191** — Le processus d'exploitation doit s'abstenir d'utiliser `sudo` pour Hermes.
- **AC-192** — Tant qu'une carte n'est pas fusionnée, l'exploitation doit empêcher son archivage.
- **AC-193** — Tant qu'un worktree ou une branche n'est pas propre et ancêtre de `origin/main`, l'exploitation doit empêcher sa suppression.
- **AC-194** — Lorsqu'un job échoue, l'exploitation doit conserver son worktree.

### Vérification et succès final

- **AC-195** — Tant que la CI obligatoire n'est pas verte dans chacun des deux dépôts, le processus doit empêcher toute fusion.
- **AC-196** — Les tests unitaires doivent vérifier la validation du DAG.
- **AC-197** — Les tests unitaires doivent vérifier la détection des conflits de périmètre.
- **AC-198** — Les tests unitaires doivent vérifier le compare-and-swap.
- **AC-199** — Les tests unitaires doivent vérifier les verrous.
- **AC-200** — Les tests unitaires doivent vérifier le refus des liens symboliques.
- **AC-201** — Les tests unitaires doivent vérifier la reprise après un crash avant le marqueur transactionnel.
- **AC-202** — Les tests unitaires doivent vérifier la reprise après un crash après le marqueur transactionnel.
- **AC-203** — Les tests unitaires doivent vérifier les nouvelles tentatives.
- **AC-204** — Les tests unitaires doivent vérifier l'idempotence.
- **AC-205** — Lorsque le test de parallélisme utilise un faux Hermes avec deux tâches disjointes, leurs intervalles d'exécution doivent se chevaucher.
- **AC-206** — Tant que le test de parallélisme s'exécute, il doit observer au plus deux writers simultanés.
- **AC-207** — Lorsque le test de parallélisme contient une tâche dépendante, il doit observer qu'elle attend la fusion de sa dépendance.
- **AC-208** — Lorsque le test de parallélisme contient un conflit de fichiers, il doit observer que les écritures concernées sont sérialisées.
- **AC-209** — Lorsqu'un job du test de parallélisme expire ou échoue, le framework doit préserver l'autre job.
- **AC-210** — Le test GitHub doit vérifier le parcours issue → carte → branche → pull request en brouillon → pull request prête → checks et reviews.
- **AC-211** — Le test GitHub doit vérifier que les réponses aux remarques sont publiées directement dans leurs fils.
- **AC-212** — Le test GitHub doit vérifier qu'une correction provoque une nouvelle attente de review.
- **AC-213** — Le test GitHub doit vérifier qu'aucune fusion n'a lieu sans go explicite.
- **AC-214** — Le test transactionnel doit vérifier que les workers n'écrivent que dans leurs fichiers autorisés et leurs journaux locaux.
- **AC-215** — Le test transactionnel doit vérifier que seul le synthesizer écrit les artefacts partagés.
- **AC-216** — Lorsqu'une interruption survient pendant le test transactionnel, la reprise doit produire soit l'ancien ensemble complet, soit le nouvel ensemble complet.
- **AC-217** — Lorsqu'une interruption survient pendant le test transactionnel, la reprise doit s'abstenir de produire un mélange d'artefacts anciens et nouveaux.
- **AC-218** — Avant l'essai VPS, le processus doit exécuter l'E2E local dans un dossier supprimable.
- **AC-219** — Tant que l'E2E s'exécute sur le VPS, il doit utiliser au plus deux jobs.
- **AC-220** — Lorsque le pilote Super Lily commence, il doit effectuer l'onboarding.
- **AC-221** — Lorsque le pilote Super Lily exerce une feature full-stack, il doit exécuter réellement en parallèle une tâche backend et une tâche frontend disjointes.
- **AC-222** — Lorsque le pilote Super Lily exerce la troisième tâche, il doit attendre la fusion de sa dépendance.
- **AC-223** — Lorsque le pilote Super Lily exécute une tâche, il doit créer une issue propre à cette tâche.
- **AC-224** — Lorsque le pilote Super Lily atteint la validation, il doit terminer cette phase sans déploiement.
- **AC-225** — Le succès final doit démontrer que toutes les commandes prévues sont publiées.
- **AC-226** — Le succès final doit démontrer que le runner traverse le parcours de l'onboarding au ship.
- **AC-227** — Le succès final doit démontrer le chevauchement réel de tâches admissibles.
- **AC-228** — Le succès final doit démontrer la cohérence transactionnelle des artefacts après interruption.
- **AC-229** — Le succès final doit démontrer que le VPS termine le pilote sans épuisement mémoire.
- **AC-230** — Le succès final doit démontrer que le VPS termine le pilote sans travail perdu.
- **AC-231** — Tant qu'une fusion n'a pas reçu un go explicite, le processus doit s'abstenir de la réaliser automatiquement.
- **AC-232** — Tant qu'une version publiée ne satisfait pas la gate de validation de publication, le processus doit empêcher toute mise à jour du VPS associée.
- **AC-233** — Le processus doit s'abstenir de réaliser un force-push.
- **AC-234** — Le processus doit s'abstenir de réaliser un reset destructif.
- **AC-235** — Tant qu'une commande SDD prépare une livraison, elle doit s'abstenir de déployer.
- **AC-236** — Lorsque l'orchestrateur crée une carte Kanban de tâche, il doit lui associer explicitement sa carte parente.
- **AC-237** — Lorsque la CI d'un dépôt est configurée, ses checks aux noms stables doivent être obligatoires avant fusion.
- **AC-238** — Lorsque le board `sdd-framework` est créé, son répertoire de travail par défaut doit être `~/workspaces/specs-driven-development`.
- **AC-239** — Lorsque le board `super-lily` est créé, son répertoire de travail par défaut doit être `~/workspaces/super-lily`.
- **AC-240** — Lorsque l'exploitation met à jour le profil VPS, elle doit cibler `ubuntu@179.237.107.15`.
- **AC-241** — Lorsque le projet `sdd-framework` est créé, son clone principal doit être `~/workspaces/specs-driven-development`.
- **AC-242** — Lorsque le projet `super-lily` est créé, son clone principal doit être `~/workspaces/super-lily`.
- **AC-243** — Lorsque `/sdd-status <feature-id>` est invoqué, le framework SDD doit afficher l'issue de chaque tâche.
- **AC-244** — Lorsque `/sdd-status <feature-id>` est invoqué, le framework SDD doit afficher la branche de chaque tâche.
- **AC-245** — Lorsque `/sdd-status <feature-id>` est invoqué, le framework SDD doit afficher la pull request de chaque tâche.
- **AC-246** — Lorsque `/sdd-status <feature-id>` est invoqué, le framework SDD doit afficher les checks de chaque tâche.
- **AC-247** — Lorsque `/sdd-status <feature-id>` est invoqué, le framework SDD doit afficher la review de chaque tâche.
- **AC-248** — Lorsque `/sdd-status <feature-id>` est invoqué, le framework SDD doit afficher le blocage de chaque tâche.
- **AC-249** — Lorsque `/sdd-status <feature-id>` est invoqué, le framework SDD doit afficher la prochaine action de chaque tâche.
- **AC-250** — Lorsque la CI d'un dépôt s'exécute, elle doit exécuter `git diff --check`.
- **AC-251** — La pull request de profil 0.4.8 doit publier le changelog de la version 0.4.8.
- **AC-252** — La pull request de contrat runtime doit introduire le garde de DAG.
- **AC-253** — Lorsque le pont GitHub obtient l'identifiant d'une pull request, il doit le stocker dans la carte Kanban.
- **AC-254** — Lorsque le pont GitHub obtient l'identifiant d'une pull request, il doit le stocker dans l'état SDD.
- **AC-255** — Tant qu'une pull request de job attend une review, le pont GitHub doit consulter les reviews toutes les cinq minutes.
- **AC-256** — Tant qu'une pull request de job attend une review, le pont GitHub doit consulter les fils de review toutes les cinq minutes.
- **AC-257** — Lorsque `/sdd-build` mono-tâche progresse, il doit conserver les commandes exécutées.
- **AC-258** — Lorsque `/sdd-build` mono-tâche progresse, il doit conserver les sorties des commandes exécutées.
- **AC-259** — Lorsque `/sdd-build` mono-tâche progresse, il doit conserver la liste des fichiers concernés.
- **AC-260** — Lorsque l'orchestrateur crée une carte, il doit lui associer la clé d'idempotence du job.
- **AC-261** — Lorsque `/sdd-ship` s'exécute, il doit préparer l'observabilité de la livraison.
- **AC-262** — Lorsque `/sdd-ship` s'exécute, il doit préparer les flags de la livraison.
- **AC-263** — Lorsque `/sdd-ship` s'exécute, il doit préparer les notes de livraison.
- **AC-264** — Après la mise à jour du profil `staaack`, l'exploitation doit tester la version installée.
- **AC-265** — Après le dispatch réel, l'exploitation doit consulter les diagnostics JSON du board Super Lily.
- **AC-266** — Le processus d'exploitation doit s'abstenir d'exécuter un gateway système Hermes.
- **AC-267** — Lorsqu'un job échoue, l'exploitation doit conserver ses logs.
- **AC-268** — Lorsqu'un job échoue, l'exploitation doit conserver son journal.
- **AC-269** — Lorsque le pilote Super Lily exécute une tâche, il doit créer une pull request propre à cette tâche.
- **AC-270** — Lorsque le pilote Super Lily atteint la review, il doit terminer cette phase sans déploiement.
- **AC-271** — Lorsque le pilote Super Lily atteint le ship, il doit terminer cette phase sans déploiement.
- **AC-272** — Tant que les checks obligatoires de la pull request #47 ne sont pas verts, le processus doit empêcher sa fusion.
- **AC-273** — Tant que la review Codex demandée pour la pull request #47 n'a pas été reçue, le processus doit empêcher sa fusion.
- **AC-274** — Tant qu'un fil actionnable de la pull request #47 reste non résolu, le processus doit empêcher sa fusion.
- **AC-275** — Tant qu'une nouvelle review attendue après une correction de la pull request #47 n'a pas été reçue, le processus doit empêcher sa fusion.
- **AC-276** — Tant que la migration du contrat runtime, du schéma d'état et du profil est active, le framework SDD doit lire les états conformes au schéma v1 ou au schéma v2.
- **AC-277** — Tant que la migration du contrat runtime, du schéma d'état et du profil est active, le framework SDD doit écrire les états au schéma v2.
- **AC-278** — Si un retour arrière de la migration est déclenché, alors l'exploitation doit rétablir la version précédente du profil.
- **AC-279** — Tant que la migration peut faire l'objet d'un retour arrière, chaque état v2 écrit doit rester lisible par le profil précédent selon le contrat v1.
- **AC-280** — Avant d'admettre une tâche, le garde commun doit accepter dans `files_in_scope` uniquement des chemins littéraux relatifs au dépôt.
- **AC-281** — Tant qu'un check CI obligatoire d'un livrable n'est pas vert, le processus doit empêcher ce livrable de satisfaire la gate de validation de publication.
- **AC-282** — Tant que les tests d'un livrable ne sont pas verts, le processus doit empêcher ce livrable de satisfaire la gate de validation de publication.
- **AC-283** — Tant que la review d'un livrable ne porte pas le verdict `approve`, le processus doit empêcher ce livrable de satisfaire la gate de validation de publication.
- **AC-284** — Tant qu'un fil actionnable d'un livrable reste non résolu, le processus doit empêcher ce livrable de satisfaire la gate de validation de publication.
- **AC-285** — Tant que la review Codex reçue pour la pull request #47 n'a pas été lue, le processus doit empêcher sa fusion.
- **AC-286** — Tant que les contrats d'un livrable ne sont pas verts, le processus doit empêcher ce livrable de satisfaire la gate de validation de publication.

## Domain Entities and Relationships

La topologie applicative `modular monolith`/`microservices` et la topologie frontend `single SPA`/`microfrontends` sont sans objet : le périmètre spécifié est un framework CLI et un ensemble de skills pilotés par Hermes, et non une application Spring ou un frontend. Les éléments suivants décrivent uniquement le domaine d'orchestration SDD.

### Entités

- **Feature SDD** — rôle : unité de livraison suivie de la spécification au ship ; attributs métier principaux : identifiant, issue parente, mode d'exécution, board, projet, version cible.
- **Commande SDD** — rôle : interface utilisateur d'une phase du workflow ; attributs métier principaux : nom, feature ciblée, tâche ciblée, options, verdict ou résultat.
- **Tâche SDD** — rôle : unité planifiée et traçable d'une feature ; attributs métier principaux : identifiant `T-NNN`, dépendances, `Test-IDs`, périmètre de fichiers, phase, statut.
- **Dépendance de tâche** — rôle : contrainte d'ordre entre deux tâches ; attributs métier principaux : tâche antécédente, tâche dépendante, état de fusion.
- **Vague** — rôle : groupe de tâches indépendantes admissibles à une exécution concomitante ; attributs métier principaux : tâches admises, plafond de writers, état de fan-in.
- **Job** — rôle : exécution isolée d'une tâche ; attributs métier principaux : clé d'idempotence, phase TDD, durée maximale, nombre de tentatives, statut.
- **Carte Kanban** — rôle : état durable d'un job dans Hermes ; attributs métier principaux : identifiant, projet, parent, clé d'idempotence, statut, blocage.
- **Issue GitHub** — rôle : suivi humain d'une feature ou d'une tâche ; attributs métier principaux : identifiant, lien parent-enfant, état.
- **Pull request de tâche** — rôle : proposition isolée issue d'un job ; attributs métier principaux : identifiant, état brouillon/prête, checks, review, autorisation humaine.
- **Pull request de fan-in** — rôle : consolidation transactionnelle d'une vague ; attributs métier principaux : vague, artefacts partagés, état de fusion.
- **Branche de tâche** — rôle : historique Git isolé d'une tâche ; attributs métier principaux : nom normalisé, propreté, relation à `origin/main`.
- **Worktree de tâche** — rôle : espace de travail isolé d'un job ; attributs métier principaux : emplacement relatif, état de propreté, conservation après échec.
- **Session Hermes** — rôle : contexte d'exécution d'un job ; attributs métier principaux : job, logs expurgés, statut.
- **Journal local de tâche** — rôle : trace immuable des transitions d'un job ; attributs métier principaux : événements, preuves RED/GREEN/REFACTOR/SIMPLIFY, marqueur transactionnel.
- **État partagé SDD** — rôle : vue consolidée rétrocompatible d'une feature ; attributs métier principaux : mode, board, projet, maximum de workers, identifiants et états des tâches.
- **Artefact partagé** — rôle : document de feature actualisé uniquement au fan-in ; attributs métier principaux : chemin relatif, version avant/après transaction.
- **Board Hermes** — rôle : espace Kanban isolé d'un projet ; attributs métier principaux : slug, nom, répertoire de travail par défaut.
- **Projet Hermes** — rôle : association durable entre un clone, un board et un projet suivi ; attributs métier principaux : slug, clone principal, board.
- **Gate lourde** — rôle : contrôle consommateur de ressources devant être sérialisé ; attributs métier principaux : famille Maven/Next/PIT/OWASP, état, résultat technique.
- **Version de profil** — rôle : jalon publiable du profil Hermes SDD ; attributs métier principaux : version, changelog, parité source/profil, validation.
- **Environnement VPS** — rôle : capacité d'exécution distante du profil SDD ; attributs métier principaux : plafond de writers, exclusivité des gates lourdes, profil, gateway utilisateur.

### Relations

- **Feature SDD 1..* Tâche SDD** — une feature contient une ou plusieurs tâches ; chaque tâche appartient à une seule feature.
- **Tâche SDD antécédente 0..* Dépendance de tâche** — une tâche peut être l'antécédent de zéro à plusieurs dépendances ; chaque dépendance désigne exactement une tâche antécédente à fusionner avant l'admission de la tâche dépendante.
- **Tâche SDD dépendante 0..* Dépendance de tâche** — une tâche peut porter zéro à plusieurs dépendances ; chaque dépendance désigne exactement une tâche dépendante dont elle contraint l'admission.
- **Vague 1..* Job** — une vague contient un ou plusieurs jobs admis ; son nombre total de jobs n'est pas limité par le plafond d'exécution simultanée.
- **Environnement VPS 0..2 Job écrivain actif** — à tout instant, le VPS exécute zéro, un ou deux jobs écrivains actifs.
- **Tâche SDD 0..1 Job actif** — une tâche peut ne pas être lancée ou avoir un seul job actif à un instant donné.
- **Job 1..1 Carte Kanban** — chaque job parallèle est représenté par exactement une carte durable.
- **Job 1..1 Issue GitHub enfant** — chaque job est suivi par une issue enfant propre.
- **Feature SDD 1..1 Issue GitHub parente** — chaque feature parallélisée possède l'issue à laquelle ses issues de tâche sont liées.
- **Issue GitHub parente 1..* Issue GitHub enfant** — l'issue de feature regroupe les issues des tâches exécutées.
- **Job 1..1 Branche de tâche** — chaque job écrit sur une branche isolée.
- **Job 1..1 Worktree de tâche** — chaque job s'exécute dans un worktree isolé.
- **Job 1..1 Session Hermes** — chaque job possède une session d'exécution propre.
- **Job 1..1 Journal local de tâche** — chaque job consigne ses transitions dans son journal immuable.
- **Job 1..1 Pull request de tâche** — chaque job propose ses changements dans une pull request propre.
- **Vague 1..1 Pull request de fan-in** — après fusion de toutes ses pull requests de tâche, une vague produit exactement une pull request de fan-in.
- **Pull request de fan-in 1..* Artefact partagé** — le fan-in actualise transactionnellement un ou plusieurs artefacts communs.
- **Feature SDD 1..1 État partagé SDD** — chaque feature possède une vue consolidée de son exécution.
- **Board Hermes 1..* Carte Kanban** — un board durable porte les cartes de ses jobs.
- **Projet Hermes 1..1 Board Hermes** — chacun des projets isolés spécifiés est associé explicitement à son board.
- **Version de profil 1..* Commande SDD** — chaque jalon publie le sous-ensemble de commandes prévu par son plan de livraison.
- **Environnement VPS 0..1 Gate lourde** — à tout instant, au plus une gate lourde est en cours sur le VPS.

## Non-Goals

- Développer un second ordonnanceur Python en parallèle du Kanban Hermes.
- Créer une commande `/sdd-roles` ou exposer les rôles comme interface publique.
- Autoriser un worker à modifier directement `04-tasks.md`, `.tdd-state.json`, `05-implementation-log.md` ou un autre artefact partagé.
- Exécuter simultanément deux gates lourdes Maven, Next, PIT ou OWASP.
- Fusionner automatiquement une pull request, sans go humain explicite.
- Déployer depuis `/sdd-ship`.
- Mettre à jour le VPS avant la fusion et la validation de la version de profil publiée concernée.
- Utiliser un gateway Hermes système, `sudo` pour Hermes ou l'option `--yolo`.
- Supprimer les preuves d'un job en échec ou nettoyer une branche/worktree sans preuve de propreté et d'ascendance à `origin/main`.
- Effectuer un force-push ou un reset destructif.
- Choisir une topologie d'application Spring ou frontend : le périmètre est un framework CLI/skills Python/Hermes.

## Glossary

- **Artefact partagé** — fichier SDD commun à plusieurs tâches, notamment `.tdd-state.json`, `05-implementation-log.md` et les rapports consolidés.
- **CAS** — contrôle compare-and-swap empêchant qu'une écriture concurrente remplace un état qui a changé depuis sa lecture.
- **Carte Kanban** — enregistrement durable Hermes représentant l'état et les métadonnées d'un job.
- **Check** — contrôle automatisé attaché à une pull request GitHub.
- **Clone propre** — clone dans lequel aucun fichier n'est modifié, indexé ou non suivi.
- **DAG** — graphe orienté acyclique des dépendances entre tâches.
- **Données sensibles** — secrets, tokens, données personnelles, chemins absolus et contenu métier, qui doivent tous être expurgés des logs.
- **Fan-in** — consolidation transactionnelle des journaux locaux et résultats d'une vague dans les artefacts partagés.
- **Feature** — unité de livraison SDD possédant une spécification et une issue parente.
- **Fil actionnable** — fil de review non résolu qui demande une correction ou une réponse avant approbation.
- **Gate lourde** — gate Maven, Next, PIT ou OWASP dont l'exécution doit être exclusive.
- **Gate de validation de publication** — état atteint uniquement lorsque la CI obligatoire est verte, les tests et contrats sont verts, la review porte le verdict `approve` et aucun fil actionnable ne reste non résolu, conformément à `AC-281` à `AC-284` et `AC-286`.
- **Glob** — expression de chemin contenant un motif de sélection au lieu d'un chemin littéral ; tout glob est interdit dans `files_in_scope`.
- **Go** — autorisation humaine explicite nécessaire avant chaque fusion.
- **Idempotence** — propriété selon laquelle la reprise ou la répétition d'une opération ne duplique pas ses effets.
- **Job** — exécution isolée d'une tâche SDD dans ses propres ressources Hermes et GitHub.
- **Journal local** — historique immuable propre à une tâche, utilisé comme source du fan-in.
- **Parité source/profil** — absence de différence entre le contenu publié depuis la source et sa copie dans le profil.
- **Pilote réussi** — pilote qui a traversé le parcours onboard→ship, prouvé le parallélisme, repris avec des artefacts cohérents et terminé sans épuisement mémoire ni travail perdu, conformément à `AC-226` à `AC-230`.
- **PR** — pull request GitHub, en brouillon pendant le travail puis prête après réussite des tests.
- **Profil** — distribution versionnée des skills SDD utilisée par le profil Hermes `staaack`.
- **Review thread-aware** — lecture et réponse qui préservent l'appartenance de chaque commentaire à son fil de review.
- **Synthesizer** — écrivain unique chargé de produire la pull request de fan-in.
- **Tâche prête** — tâche dont toutes les dépendances sont fusionnées et dont le périmètre n'entre pas en conflit avec un autre job de la vague.
- **Vague** — ensemble de jobs admissibles exécutés en parallèle avant un fan-in commun.
- **Writer** — job autorisé à modifier les fichiers de son périmètre.
- **Worktree** — espace Git isolé associé à la branche d'une tâche.

## Assumptions

> Ces hypothèses sont explicitement retenues dans la source ; aucune hypothèse supplémentaire n'est ajoutée.

- Hermes Kanban est l'ordonnanceur officiel ; `delegate_task` reste réservé aux sous-analyses d'un job.
- GitHub Issues sera activé sur SDD ; Super Lily devra aussi avoir Issues actif.
- Deux writers constituent le plafond du VPS ; les gates lourdes sont séquentielles.
- Aucun auto-merge, force-push, reset destructif, déploiement ou mise à jour VPS n'a lieu avant validation de la version publiée.
- Chaque problème indépendant conserve son issue, sa branche, sa pull request et son cycle de review.
- État initial consigné par la source : profil VPS 0.4.7, pull request #47 prête mais sans CI/review, `/sdd-onboard` non publié, GitHub CLI absent du VPS et gateway Hermes arrêté.

## Out-of-Band Inputs

- Le 2026-07-31, l'utilisateur confirme explicitement les options retenues : Hermes Kanban, GitHub Issues, au plus deux writers, gates lourdes sérialisées, aucun auto-merge, et une branche, un worktree, une issue et une pull request propres à chaque tâche.
- Le 2026-07-31, l'utilisateur confirme que la cible couvre les versions 0.4.8 à 1.0.0.
- Le 2026-07-31, l'utilisateur précise que les sélecteurs de topologie backend/frontend ne s'appliquent pas à ce framework CLI/skills Python/Hermes.
- Le 2026-07-31, l'utilisateur donne son approbation explicite et son sign-off de phase 1.
- Le 2026-07-31, l'utilisateur donne le go explicite pour la future fusion de la pull request #47 ; ce go ne déroge pas aux checks, à la review ni au traitement des fils exigés par `AC-272` à `AC-275`.
- Le 2026-07-31, l'utilisateur confirme les réponses exactes à `Q-007` à `Q-010` consignées ci-dessous.

## Open Questions

- (aucune)

## Resolved Questions

- **Q-001** — Quel ordonnanceur durable doit piloter l'exécution parallèle ?
  - Réponse utilisateur : « Hermes Kanban ».
  - Résolue le : 2026-07-31.
- **Q-002** — Quel outil doit suivre les features et tâches ?
  - Réponse utilisateur : « GitHub Issues ».
  - Résolue le : 2026-07-31.
- **Q-003** — Quel plafond de jobs écrivains doit s'appliquer sur le VPS ?
  - Réponse utilisateur : « max 2 writers ».
  - Résolue le : 2026-07-31.
- **Q-004** — Les gates lourdes peuvent-elles s'exécuter en parallèle ?
  - Réponse utilisateur : « gates lourdes sérialisées ».
  - Résolue le : 2026-07-31.
- **Q-005** — Une pull request peut-elle être fusionnée automatiquement ?
  - Réponse utilisateur : « aucun auto-merge ».
  - Résolue le : 2026-07-31.
- **Q-006** — Quelle topologie d'application faut-il retenir ?
  - Réponse utilisateur : le sélecteur est non applicable, car le périmètre est un framework CLI/skills Python/Hermes, pas une application Spring ou frontend.
  - Résolue le : 2026-07-31.
- **Q-007** — La migration du contrat runtime, du schéma d'état et du profil doit-elle être protégée par un feature flag avec une procédure de retour arrière, ou l'utilisateur approuve-t-il une dérogation explicite ?
  - Réponse utilisateur : « double lecture v1/v2, écriture v2, rollback par retour au profil précédent tout en conservant la compatibilité v1 ».
  - Résolue le : 2026-07-31.
- **Q-008** — Quelles catégories exactes doivent être expurgées des logs d'un job : secrets et tokens seulement, ou aussi données personnelles, chemins locaux et contenu métier ?
  - Réponse utilisateur : « expurger secrets, tokens, données personnelles, chemins absolus et contenu métier ».
  - Résolue le : 2026-07-31.
- **Q-009** — Quelles formes de glob doivent être considérées comme ambiguës et refusées par le garde de périmètre ?
  - Réponse utilisateur : « interdire tout glob dans files_in_scope et exiger des chemins littéraux relatifs au dépôt ».
  - Résolue le : 2026-07-31.
- **Q-010** — Quelle preuve objective définit « validé », « travail validé » et « pilote réussi » aux jalons de publication et de mise à jour du VPS ?
  - Réponse utilisateur : « validation = CI obligatoire verte, tests/contrats verts, review approve, aucun fil actionnable ; pilote réussi seulement après onboard→ship, parallélisme prouvé, reprise cohérente, sans OOM ni perte ».
  - Résolue le : 2026-07-31.

## Sign-off

- [x] Tous les AC sont atomiques et testables.
- [x] Toutes les `Q-NNN` sont résolues ou explicitement différées avec justification.
- [x] La source est consignée.
- [x] Revue et approbation de phase 1 effectuées par l'utilisateur le 2026-07-31.
