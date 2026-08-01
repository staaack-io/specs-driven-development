# Transaction, reprise et idempotence

Le garde utilise le répertoire Git commun afin que tous les worktrees partagent
le même verrou. Il ouvre le verrou sans suivre de lien symbolique.

## Commit

1. Vérifier `HEAD`, le token du worktree, `_stack.json`, le scope, les empreintes
   et les candidats.
2. Exécuter les gates pré-commit en série dans une archive temporaire sûre de
   `HEAD` avec les candidats appliqués.
3. Écrire un journal durable contenant les versions avant/après, modes et
   empreintes.
4. Remplacer chaque cible par fichier temporaire, `fsync` et `os.replace`.
5. Exécuter les gates post-commit en série et vérifier que leur exécution n'a
   modifié aucun autre fichier.
6. Marquer le journal `committed`, écrire le reçu cumulatif, puis supprimer le
   journal.

Le reçu ne contient ni chemin absolu, transcript, sortie brute ou secret. Les
sorties de gates sont représentées par leur code et une empreinte SHA-256.

## Reprise

- journal `committed` : rematérialiser toutes les versions après et le reçu ;
- tout autre état : restaurer toutes les versions avant ;
- empreinte de payload, chemin, schéma ou cible incohérente : refuser sans
  toucher au projet ;
- journal présent avec `--dry-run` : refuser et demander une reprise non sèche.

Une interruption donne donc l'ancien ou le nouvel ensemble complet, jamais un
mélange. Un échec de gate post-commit restaure immédiatement l'ancien ensemble.

## Replay

Un second commit du même plan vérifie le reçu, chaque cible et chaque candidat
avant de retourner `unchanged: true`. Il ne réécrit aucun fichier et ne relance
aucune gate. Une cible ou un candidat modifié invalide le replay.
