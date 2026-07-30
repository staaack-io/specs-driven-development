---
name: sdd-spec-review
description: "Relire et approuver une spécification SDD."
---

# Revue de spécification SDD

Auditer `01-spec.md`, demander la décision finale de l'utilisateur et produire
`02-spec-review.md`. Ne jamais corriger silencieusement la spécification.

## Entrée

- accepter un `feature-id` facultatif ;
- sans argument, choisir le dossier de fonctionnalité contenant le
  `01-spec.md` le plus récemment modifié ;
- refuser si `.specs/<feature-id>/01-spec.md` n'existe pas ;
- refuser d'écraser `02-spec-review.md`, sauf avec l'option explicite
  `--continue`.

## Références à charger

Lire avant la revue :

- [checklist de revue](references/review-checklist.md) ;
- [modèle de rapport](templates/spec-review.template.md) ;
- `.specs/<feature-id>/01-spec.md`.

Lire également `docs/spec-format.md` s'il existe dans le projet. Utiliser la
checklist embarquée comme source de secours.

## Processus

1. Capturer l'horodatage de la revue et, si le projet est sous Git, le SHA
   courant. Ne jamais exiger un commit.
2. Compter les critères `AC-NNN`, vérifier leur unicité et conserver leurs
   identifiants exacts.
3. Appliquer chaque ligne de la checklist avec le résultat
   `pass | fail | n/a` et une justification courte fondée sur le fichier.
4. Pour chaque échec, créer un constat `F-NNN` avec sa sévérité, les lignes ou
   sections concernées, la preuve et la correction demandée.
5. Rechercher les questions `Q-NNN` encore au statut `open`. Une seule question
   ouverte impose `request-changes`.
6. Consigner les ambiguïtés découvertes sous `## New Questions Raised`. Ne pas
   les ajouter soi-même à `01-spec.md`.
7. Déterminer le verdict technique provisoire :
   - `request-changes` si un constat `blocker` ou `major` existe, si un AC
     échoue, ou si une question reste ouverte ;
   - `ready-for-approval` dans les autres cas.
8. Remplir `02-spec-review.md` avec le modèle.
9. Si le verdict est `ready-for-approval`, présenter le résumé à l'utilisateur
   et demander explicitement `approve` ou `request-changes`. Ne jamais déduire
   son accord du seul lancement de la commande.
10. Inscrire la décision, le nom fourni ou `utilisateur`, et la date dans le
    rapport. Le verdict final doit être exactement `approve` ou
    `request-changes`.

## Contraintes d'écriture

- Écrire uniquement `.specs/<feature-id>/02-spec-review.md`.
- Ne jamais modifier `01-spec.md`, du code, des tests, un design ou des tâches.
- Ne pas inventer de source, de règle métier ou d'approbation utilisateur.
- Conserver les constats précédents lors d'un `--continue` et marquer leur état
  `open | resolved | accepted` au lieu de les supprimer.

## Résultat

Le rapport doit contenir ces champs stables :

- `verdict` ;
- `acs_total` ;
- `acs_failed` ;
- `open_questions` ;
- `reviewer` ;
- `reviewed_at` ;
- `next_command`.

Avec `approve`, proposer `/sdd-plan` ou `/sdd-epic-plan` selon la taille de la
fonctionnalité, en précisant si la commande n'est pas installée. Avec
`request-changes`, proposer
`/sdd-spec --continue <feature-id>` et s'arrêter.
