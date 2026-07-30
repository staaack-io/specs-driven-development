---
name: sdd-spec-review
description: "Relire et approuver une spécification SDD."
---

# Revue de spécification SDD

Auditer `01-spec.md`, demander la décision finale de l'utilisateur et produire
`02-spec-review.md`. Ne jamais corriger silencieusement la spécification.

## Entrée

- accepter un `feature-id` facultatif ;
- accepter `--decision approve|request-changes` uniquement avec `--continue`
  lorsqu'un rapport provisoire valide existe déjà ;
- sans argument, choisir le dossier de fonctionnalité contenant le
  `01-spec.md` le plus récemment modifié ;
- refuser si `.specs/<feature-id>/01-spec.md` n'existe pas ;
- refuser d'écraser `02-spec-review.md`, sauf avec l'option explicite
  `--continue`.

## Références à charger

Lire avant la revue :

- [checklist de revue](references/review-checklist.md) ;
- [modèle de rapport](templates/spec-review.template.md) ;
- [porte de décision humaine](references/decision-gate.md) ;
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
5. Rechercher les questions `Q-NNN` encore au statut `open` dans la
   spécification.
6. Consigner chaque ambiguïté découverte sous `## New Questions Raised` avec le
   prochain identifiant `Q-NNN` disponible dans la spécification et le rapport,
   et le statut `open`. Ne pas l'ajouter soi-même à `01-spec.md`.
   S'il n'y en a aucune, écrire `(aucune)`.
7. Déterminer le verdict technique provisoire :
   - `request-changes` si un constat `blocker` ou `major` existe, si un AC
     échoue, si une question de la spécification reste ouverte, ou si
     `New Questions Raised` contient une question au statut `open` ;
   - `ready-for-approval` dans les autres cas.
8. Remplir `02-spec-review.md` avec le modèle. `open_questions` est la somme des
   questions ouvertes dans la spécification et des nouvelles questions de la
   revue au statut `open`. Une question `transferred` est comptée uniquement
   depuis la spécification.
9. Si le résultat technique permet une approbation, écrire obligatoirement un
   rapport provisoire avec `verdict: ready-for-approval`, `reviewer: en attente`,
   `reviewed_at: en attente`, `next_command: en attente` et toute la section
   `User Decision` en attente. Valider ce rapport avec
   `scripts/review_decision_guard.py validate-provisional`.
10. Présenter le résumé, demander une réponse exacte `approve` ou
    `request-changes`, puis **arrêter ce tour sans finaliser le rapport**. Le seul
    lancement de la commande, l'absence de réponse, `continue` ou une approbation
    antérieure ne constituent jamais une décision.
11. Finaliser uniquement après une réponse explicite reçue après le rapport
    provisoire, ou avec `--continue <feature-id> --decision <décision>` sur un
    rapport déjà provisoire. Appliquer intégralement
    `references/decision-gate.md` et utiliser le garde ; ne jamais écrire les
    champs finaux directement.
12. Refuser `approve` tant que `open_questions` n'est pas égal à zéro.

## Contraintes d'écriture

- Écrire uniquement `.specs/<feature-id>/02-spec-review.md` ; le garde peut
  créer le verrou technique `.spec-review.lock` dans le même dossier.
- Ne jamais modifier `01-spec.md`, du code, des tests, un design ou des tâches.
- Ne pas inventer de source, de règle métier ou d'approbation utilisateur.
- Ne jamais attribuer `reviewer: utilisateur`, une date finale ou une preuve de
  décision avant que le garde ait accepté une réponse explicite.
- Conserver les constats précédents lors d'un `--continue` et marquer leur état
  `open | resolved | accepted` au lieu de les supprimer.
- Lors d'un `--continue`, conserver aussi les nouvelles questions précédentes.
  Marquer `transferred` une question désormais présente dans `Open Questions`
  de la spécification, ou `resolved` si elle apparaît dans `Resolved Questions`.
  La compter depuis la spécification après transfert, jamais deux fois.

## Résultat

Le rapport doit contenir ces champs stables :

- `verdict` ;
- `acs_total` ;
- `acs_failed` ;
- `open_questions` ;
- `reviewer` ;
- `reviewed_at` ;
- `decision_evidence` ;
- `decision_evidence_mode` ;
- `next_command`.

Avec `approve`, proposer `/sdd-plan` ou `/sdd-epic-plan` selon la taille de la
fonctionnalité, en précisant si la commande n'est pas installée. Avec
`request-changes`, proposer
`/sdd-spec --continue <feature-id>` et s'arrêter.
