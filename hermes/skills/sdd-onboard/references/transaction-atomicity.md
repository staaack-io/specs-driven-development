# Atomicité de l'onboarding

Le garde embarqué est l'unique chemin d'écriture des cinq artefacts.

## Snapshot

`inspect` prend un verrou exclusif non bloquant dans le gitdir, récupère une
transaction éventuelle, vérifie le worktree, capture `HEAD` et calcule un token
sur les cinq versions courantes.

Le worktree peut contenir uniquement les cinq fichiers non indexés produits par
le dernier reçu exact. Toute autre modification est refusée.

## Commit

`commit` reprend le verrou et revérifie :

1. le SHA attendu ;
2. le token CAS ;
3. le worktree ;
4. les cinq noms, formats, SHA et sections des candidats ;
5. l'absence de lien symbolique.

Il écrit un journal durable avec versions précédentes, versions cibles et modes.
Chaque cible passe par un fichier temporaire, `fsync` et `os.replace`. Un
marqueur dans le gitdir est écrit en dernier : c'est le point de commit. Le reçu
final autorise un second run avant même que les artefacts soient commités dans
Git.

## Reprise

- marqueur attendu : restaurer les cinq versions précédentes ;
- marqueur cible : matérialiser les cinq versions cibles ;
- autre valeur ou marqueurs identiques : arrêter et préserver le journal.

Une cible identique à l'état courant retourne `unchanged: true` sans journal ni
remplacement.
