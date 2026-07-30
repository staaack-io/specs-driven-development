# Exemples

Ce dossier contient deux parcours complets de la méthodologie. Il s’agit de
**documentation, pas de projets exécutables**. Chaque artefact — spécification,
conception, tâches, journal d’implémentation et rapport — est un vrai fichier,
produit comme si un humain avait piloté l’agent à travers toutes les commandes.
Utilisez-les pour comprendre le résultat attendu de chaque phase.

## [`greenfield/`](./greenfield/README.md)

Un nouveau service Spring Boot 4 / Spring Framework 7. L’exemple suit la
fonctionnalité `gift-card-checkout` depuis une intention en une phrase jusqu’à
`$spec` → `$spec-review` → `$plan` → `$build` → `$test` →
`$validate` → `$review`. Il contient un squelette `pom.xml` raccordé au
harness, une organisation représentative des modules et un dossier
`.specs/2025-01-15-gift-card-checkout/` complet.

## [`brownfield/`](./brownfield/README.md)

Un service Spring existant sans harness, avec un outil de migration manquant et
des tests partiels. L’exemple montre comment `$onboard` découvre les écarts,
capture une référence et produit `.specs/_onboarding.md` avec un ordre de
modernisation progressif.

## Ce que ces exemples ne contiennent pas

- Du code Java exécutable dans chaque fichier, car il vieillirait rapidement.
  Les extraits illustrent la structure et les artefacts `.specs/`.
- Des suites de tests complètes. Le journal montre des tests représentatifs et
  les passages rouge puis vert.
- Les rapports générés sous `target/**`. Le rapport de validation cite
  directement les résultats des portes.
