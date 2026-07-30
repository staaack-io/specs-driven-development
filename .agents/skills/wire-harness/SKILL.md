---
name: wire-harness
description: "Raccorder le harness qualité Maven après l’intégration. Utiliser lorsque l’utilisateur invoque $wire-harness ou demande d’ajouter les portes de qualité du framework."
---

# $wire-harness

**Phase :** 0 — prolongement de l’intégration
**Agent responsable :** `.codex/agents/spring-onboarding.toml`
**Skills utilisés :** `maven-harness-pom`, `jacoco-coverage-policy`,
`pit-mutation-tuning`, `flyway-or-liquibase-detection`,
`harness-report-parsing`

## Objectif

Raccorder dans un module Maven déjà analysé les couches Spotless, Checkstyle,
SpotBugs, Surefire/Failsafe, JaCoCo, PIT, OWASP Dependency Check et l’outil de
migration choisi. Ce skill comble l’espace entre `$onboard`, qui diagnostique,
et `$build`, réservé aux tâches TDD.

## Entrées

Chemin facultatif d’un module Maven, par défaut `.`. Dans un monorepo, fournir
le module backend.

## Lectures

- `pom.xml` du module ;
- `.specs/_stack.json`, obligatoire ;
- artefacts d’intégration, dette connue et ADR ;
- fragment Maven et skills de harness, couverture, mutation et migration.

## Écritures

- `<module>/pom.xml` ;
- `checkstyle.xml` et `dependency-check-suppressions.xml` s’ils manquent ;
- références et détection de stack actualisées ;
- dette connue et conception de départ ;
- un ADR par couche explicitement différée.

## Processus

1. Exiger `_stack.json`. Refuser les deux outils de migration. Si une base est
   détectée sans outil choisi, exiger d’abord un ADR.
2. Vérifier la compatibilité de chaque version de plugin avec Java et Spring
   Boot. Différer sans inventer de contournement, avec ADR.
3. Raccorder les versions et plugins selon `maven-harness-pom` :
   - Spotless, Checkstyle, SpotBugs et FindSecBugs ;
   - Surefire hors `*IT.java` et Failsafe pour `*IT.java` ;
   - JaCoCo avec seuils complets en greenfield ou cliquet brownfield ;
   - PIT dans le profil `pit` ;
   - OWASP dans le profil `security` ;
   - dépendance Flyway ou Liquibase décidée.
4. Créer les fichiers de configuration manquants et corriger l’hygiène évidente
   du POM.
5. Exécuter une fois `spotless:apply`. C’est la seule modification mécanique
   de `src/**` autorisée.
6. Documenter chaque report avec ADR et `DEBT-NNN`.
7. Exécuter `mvn -pl <module> -am verify`, puis le harness en mode référence.
8. Actualiser la stack, la dette et les conventions de départ.

## Refuser si

- l’intégration préalable manque ;
- la migration est ambiguë ou indécise ;
- une édition manuelle de production ou de test serait nécessaire ;
- une compatibilité est inconnue sans décision de report ou version explicite ;
- un seuil devrait baisser sans référence et ADR.

## Terminé lorsque

La vérification Maven est verte, chaque couche raccordée passe ou est
explicitement optionnelle, la référence est actualisée, chaque report possède
sa dette et son ADR, et l’utilisateur connaît l’étape suivante.
