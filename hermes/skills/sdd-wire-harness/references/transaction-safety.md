# Transaction, reprise et idempotence

Le garde utilise le répertoire Git commun afin que tous les worktrees partagent
le même verrou. Journaux et reçus y sont séparés par un namespace dérivé du
chemin réel du worktree, de la branche et du HEAD. Il ouvre le verrou sans suivre
de lien symbolique et le conserve jusqu'à la fin d'un commit ou d'un replay.

## Commit

1. Vérifier `HEAD`, le token du worktree, `_stack.json`, le scope, les empreintes
   et les candidats.
2. Empreinter le contenu complet du dépôt, y compris fichiers ignorés et
   métadonnées Git pertinentes, hors cibles et fichiers techniques du garde.
3. Exécuter les gates pré-commit en série dans une archive temporaire sûre de
   `HEAD` avec les candidats, fichiers reçus et dépendances Node existantes.
4. Écrire un journal durable contenant les versions avant/après, modes et
   empreintes.
5. Remplacer chaque cible par fichier temporaire, `fsync` et `os.replace`.
6. Réexécuter les gates identiques dans un nouveau bac à sable post-commit et
   revérifier l'empreinte complète du dépôt hors cibles.
7. Vérifier les hashes réels des cibles, marquer le journal `committed`, écrire
   le reçu cumulatif namespacé, puis supprimer le
   journal.

Le reçu ne contient ni chemin absolu, transcript, sortie brute ou secret. Les
sorties de gates sont représentées par leur code et une empreinte SHA-256.

## Reprise

- journal `committed` : rematérialiser toutes les versions après et le reçu ;
- tout autre état : restaurer toutes les versions avant ;
- empreinte de payload, chemin, parent, schéma ou cible hors de l'allowlist
  actuelle de `_stack.json` : refuser sans toucher au projet ;
- journal présent avec `--dry-run` : refuser et demander une reprise non sèche.

Une interruption donne donc l'ancien ou le nouvel ensemble complet, jamais un
mélange. Un échec de gate post-commit restaure immédiatement l'ancien ensemble.

## Replay

Un second commit du même plan vérifie le reçu, chaque cible et chaque candidat
avant de retourner `unchanged: true`. Il ne réécrit aucun fichier et ne relance
aucune gate. Une cible ou un candidat modifié invalide le replay.
