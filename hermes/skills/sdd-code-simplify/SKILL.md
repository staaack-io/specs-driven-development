---
name: sdd-code-simplify
description: "Simplifier le code de production sans changer son comportement."
---

# `/sdd-code-simplify <path> [--dry-run]`

## Objectif

Appliquer une passe de clarté à un fichier ou dossier de production en gardant
la suite de tests verte. Cette commande ne demande aucune review et ne crée
aucun commit.

## Entrées et refus

- Accepter exactement un chemin littéral relatif sous `src/main/**`, suivi de
  `--dry-run` facultatif.
- Refuser `src/test/**`, tout glob, lien symbolique, argument inconnu, chemin
  absolu, sortie du dépôt ou cible absente avant la première écriture.
- Recevoir une commande de tests sous forme d'argv structurés, jamais sous
  forme de chaîne shell.

## Lectures

- la cible normalisée ;
- `references/clarity-checklist.md` ;
- `references/delegation-contract.md` ;
- le runtime v2 canonique sous `hermes/runtime/`.

## Processus

1. Résoudre la cible en fichiers concrets triés.
2. Exécuter la commande de tests validée et refuser toute mutation si la
   baseline n'est pas verte.
3. En écriture, acquérir le lease exact avec le runtime v2 et conserver
   l'empreinte hors scope.
4. Déléguer un fichier à la fois selon le contrat de clarté, puis relancer les
   tests. Restaurer seulement le fichier courant si ses tests régressent.
5. En `--dry-run`, produire le même plan et le même résumé sans lease, sans
   mutation de la cible et sans écriture d'artefact partagé.
6. Expurger les sorties et résumer fichiers, catégories, argv de tests,
   régressions et résultats `simplified` ou `ignored`.

## Terminé lorsque

Chaque fichier est `simplified` ou `ignored`, la suite reste verte et aucun
fichier hors lease n'a changé. Aucun commit ou fusion n'est automatique.
