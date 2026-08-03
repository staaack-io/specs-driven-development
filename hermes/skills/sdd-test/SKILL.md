---
name: sdd-test
description: >-
  Construire ou compléter le plan de test SDD sans modifier la production.
  Utiliser avec /sdd-test <feature-id> [--gap].
---

# Plan et renforcement des tests SDD

Exécuter `/sdd-test <feature-id> [--gap]` après les tâches de build. Accepter
exactement un identifiant de feature et l'option facultative `--gap`; refuser
tout autre argument.

## Références obligatoires

- [contrat du plan de test](references/test-plan-contract.md) ;
- [contrat de délégation](references/delegation-contract.md) ;
- [modèle du plan](templates/test-plan.template.md).

## Processus

1. Lire la spécification, la conception, les tâches et les rapports existants.
2. Construire la matrice AC × types et les besoins Testcontainers.
3. Avec `--gap`, relier chaque `Gap-NNN` à un test ou à une justification
   `Won't fix`.
4. Déléguer uniquement les fichiers de test concrets autorisés.
5. Exécuter chaque gate lourde avec des argv structurés sous le verrou global
   canonique, puis conserver une sortie expurgée et un résultat `PASS|FAIL`.
6. Publier atomiquement `06-test-plan.md`, puis régénérer la traçabilité.

## Limites

Autoriser uniquement `src/test/**` et le `06-test-plan.md` de la feature.
Refuser `src/main/**`, les liens symboliques, les sorties du dépôt, les options
de contournement de tests et toute commande shell composée. Ne jamais commiter,
fusionner, demander une review, publier ou déployer.

## Terminé lorsque

Chaque AC possède un test nommé et tagué ou un gap résolu, les tests sont verts,
le plan est publié atomiquement et la matrice de traçabilité est régénérée.
