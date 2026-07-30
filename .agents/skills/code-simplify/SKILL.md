---
name: code-simplify
description: "Simplifier le code de production dans le périmètre sans changer son comportement. Utiliser lorsque l’utilisateur invoque $code-simplify ou demande un code plus clair."
---

# $code-simplify

**Phase :** méta — passe de clarté
**Agent responsable :** `.codex/agents/spring-code-reviewer.toml`
**Skills utilisés :** `clarity-over-cleverness`,
`tdd-red-green-refactor`

## Objectif

Appliquer les règles de clarté à un fichier ou dossier tout en gardant les tests
verts. C’est la même passe que l’étape de simplification de `$build`, exécutée
à la demande.

## Entrées

- `<path>`, fichier ou dossier sous `src/main/**` ;
- `--dry-run` facultatif pour proposer sans écrire.

## Lectures

- cible ;
- `clarity-over-cleverness`, checklist de référence.

## Écritures

- fichiers ciblés ;
- résumé dans le journal d’implémentation ou dans
  `clarity-pass-<date>.md` sans fonctionnalité active.

## Processus

1. Exiger `mvn test` vert.
2. Pour chaque fichier :
   1. remplacer les ternaires imbriqués par des conditions ;
   2. préférer une boucle lorsqu’elle est plus claire qu’un stream ;
   3. intégrer les helpers utilisés une seule fois ;
   4. remplacer les options booléennes par des méthodes distinctes ;
   5. nommer les concepts métier précisément ;
   6. retirer les abstractions prématurées ;
   7. préférer les retours anticipés aux imbrications profondes.
3. Relancer les tests après chaque fichier. En cas de régression, annuler les
   modifications de ce fichier et le consigner comme ignoré.
4. Résumer fichiers, catégories de réécriture, tests et régressions.

## Refuser si

- les tests ne sont pas verts au départ ;
- le chemin cible `src/test/**`, dont la clarté relève de `$test`.

## Terminé lorsque

Chaque fichier du périmètre est simplifié ou explicitement ignoré et les tests
sont verts.
