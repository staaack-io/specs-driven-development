---
name: sdd-ship
description: Préparer un plan de livraison complet sans exécuter de déploiement.
---

# `/sdd-ship [<feature-id>] [--base <ref>]`

Prépare le plan facultatif de livraison d'une fonctionnalité validée et revue.
La commande publie uniquement `.specs/<feature-id>/09-ship-plan.md`.

## Entrées

- `<feature-id>` est facultatif ; sans valeur, sélectionner la fonctionnalité la
  plus récente dont la validation et la review sont approuvées ;
- `--base <ref>` est facultatif et vaut `origin/main` par défaut ;
- les identifiants et références sont validés comme des données, sans
  interpolation ni interprétation.

## Contrats chargés

Lire avant toute action :

- `references/delegation-contract.md` ;
- `references/shipping-contract.md` ;
- `templates/ship-plan.template.md` ;
- `scripts/ship_guard.py`.

## Processus

1. Résoudre la fonctionnalité et la base sans lancer de commande.
2. Construire les preuves structurées de validation, review, questions,
   baseline, scope et diff à partir des artefacts déjà fournis.
3. Appeler `validate_preconditions`; au premier refus, préserver le plan
   précédent et rendre la commande de reprise comme donnée.
4. Préparer le rollback, l'observabilité, la posture de feature flag et les
   notes externes et internes.
5. Valider le plan complet, puis publier le fichier unique par remplacement
   atomique sous le verrou runtime canonique.
6. Afficher la commande de livraison en tant que texte destiné à l'utilisateur.

## Frontière de capacité

Ce skill possède **aucune primitive shell**, **aucun accès réseau**,
aucun accès VPS et aucune capacité de fusion ou de déploiement. La commande de
livraison est une **commande affichée uniquement** : elle reste une donnée et
n'est jamais exécutée. Aucun secret, token ou chemin absolu ne doit entrer dans
le plan ou les notes.

## Résultat

- succès : exactement un `09-ship-plan.md` complet et atomique ;
- refus : aucun plan partiel et le plan précédent reste inchangé ;
- jamais : shell, réseau, VPS, merge, push, pipeline ou déploiement.
