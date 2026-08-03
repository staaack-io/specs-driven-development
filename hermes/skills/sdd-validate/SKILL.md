---
name: sdd-validate
description: "Exécuter le harness SDD et agréger une validation technique traçable."
---

# `/sdd-validate [<feature-id>]`

## Objectif

Exécuter les portes techniques applicables, agréger les résultats Spring et
React/Next.js, puis publier un verdict unique. Cette commande ne demande aucune
review et ne fusionne ni ne déploie rien.

## Préconditions

- Exiger le harness installé et exécutable, toutes les tâches `done` et des
  résultats frais non marqués comme contournés.
- Refuser tout argument de contournement de tests ou de quality gate.
- Déduire la feature des changements depuis `origin/main` quand
  `<feature-id>` est absent ; sinon accepter uniquement un identifiant sûr.

## Routage

- Sources Java/Kotlin ou `pom.xml` : validateur Spring.
- Sources JavaScript/TypeScript ou `package.json` : validateur React/Next.js.
- Sources mixtes : les deux validateurs, sans handle vers les rapports
  communs, conformément à [la délégation](references/delegation-contract.md).

Les responsabilités spécialisées sont détaillées dans
[le rôle Spring](references/role-spring-validator.md) et
[le rôle React/Next.js](references/role-react-nextjs-validator.md).

## Processus

1. Appliquer les préconditions de
   [`validation_guard.py`](scripts/validation_guard.py).
2. Sérialiser séparément Maven, Next, PIT et OWASP avec le verrou global du
   runtime canonique.
3. Collecter uniquement des résultats structurés en lecture seule.
4. Agréger gates, couverture, mutation et traçabilité selon le
   [contrat de validation](references/validation-contract.md).
5. Faire écrire par le fan-in unique exactement
   `07-validation-report.md` et `07a-traceability.md`, à partir des
   [modèle de validation](templates/validation-report.template.md) et
   [modèle de traçabilité](templates/traceability.template.md).

## Terminé lorsque

Le verdict technique vaut exactement `PASS` ou `FAIL`, la décision vaut
exactement `approve` ou `request-changes`, les preuves sont expurgées et aucun
fichier hors des deux rapports autorisés n'a été écrit.
