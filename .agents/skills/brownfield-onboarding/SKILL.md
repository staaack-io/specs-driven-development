---
name: brownfield-onboarding
description: Intégrer une base Spring existante au workflow piloté par les spécifications sans bloquer le premier jour. Établir `_baseline.json`, des règles à cliquet et une conception de départ fidèle au code.
when_to_use:
  - L’utilisateur exécute `$onboard` ou demande d’ajouter le workflow à un projet existant.
  - Première fonctionnalité d’un dépôt sans dossier `.specs/`.
authoritative_references:
  - docs/methodology.md
  - .agents/skills/maven-harness-pom/SKILL.md
  - .github/scripts/detect-stack.sh
---

# Onboarding brownfield

## Objectif

Atteindre un état où `$spec` fonctionne pour la prochaine fonctionnalité, où le
harness est vert ou n'affiche que des écarts de référence documentés, sans bloquer
l'équipe sur des années de dette de lint ou de couverture.

## Étapes

1. **Détecter la stack.** Exécuter `.github/scripts/detect-stack.sh >
   .specs/_stack.json`. Consigner Java, Spring Boot, le moteur de base de données,
   l'outil de migration, la stack de test, l'outil de build et la présence d'OpenAPI.

2. **Exécuter le harness une seule fois et capturer les références.**

   ```bash
   ./.githu.github/scripts/harness.sh --baseline > .specs/_baseline.json
   ```

   Le résultat commité contient l'horodatage, le SHA Git et les valeurs de
   référence pour Checkstyle, SpotBugs, JaCoCo, PIT, ArchUnit, OpenAPI et Dependency-Check.

3. **Ajouter les couches manquantes au POM** avec `maven-harness-pom`, en les
   calant sur les valeurs actuelles et non sur les cibles :
   - minimum JaCoCo à la couverture actuelle moins 1 %, pour le cliquet ;
   - PIT dans un profil `-Ppit`, limité au périmètre incrémental ;
   - règles ArchUnit avec `FreezingArchRule.freeze(...)` ;
   - Spotless en mode `check` limité au nouveau code avec `<ratchetFrom>origin/main</ratchetFrom>`.

4. **Générer une conception de départ.** `spring-architect` écrit
   `.specs/_starter-design.md` à partir du code réel : modules, patterns dominants
   et écarts notables. Les futures conceptions suivent cette référence sauf ADR contraire.

5. **Documenter les lacunes.** Écrire `.specs/_known-debt.md` avec les contrôles en
   échec ou proches du seuil : violations ArchUnit gelées, couverture et cible du
   cliquet, dérogations de CVE et injection de champs à corriger progressivement.

6. **Première fonctionnalité.** Exécuter `$spec` sur un petit ticket. L'agent lit
   `_baseline.json` et `_starter-design.md` sans proposer silencieusement un travail qui les dégrade.

## Politique de cliquet

- Couverture : augmenter d'un point le seuil par package à chaque PR fusionnée qui le touche.
- ArchUnit : les violations gelées ne peuvent que diminuer ; ne jamais en ajouter.
- Mutation : périmètre incrémental dès le premier jour ; exécution complète nocturne à titre informatif.
- Dérogations CVE : chacune possède une expiration et un ticket de suivi.

## Anti-patterns

- « Nous corrigerons la couverture plus tard » sans valeur de cliquet.
- Désactiver une couche bruyante du harness ; ajuster le seuil et consigner la dette.
- Dégrader les références sans ADR.
- Commiter une baisse de métrique dans `_baseline.json` sans explication.
