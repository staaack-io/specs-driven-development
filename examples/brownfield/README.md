# Exemple brownfield : legacy-orders

Un service Spring existant dans lequel la boîte à outils vient d’être ajoutée.
Il compile, mais plusieurs couches du harness manquent, aucun outil de migration
n’est raccordé et la couverture est inégale. Cet exemple montre le résultat de
`$onboard` et le parcours conseillé avant toute nouvelle fonctionnalité.

## État fictif du projet

- Spring Boot 3.2, avec une migration vers 4.x hors du périmètre de
  `$onboard`.
- Un module Maven et environ 30 000 lignes sous
  `src/main/java/com/legacy/orders/...`.
- Un seul paquet racine, sans frontières de modules.
- JUnit 5 présent, sans Testcontainers ; H2 en mémoire pour les tests
  d’intégration, alors que la production utilise un moteur réel.
- `application.yaml` référence `jdbc:postgresql://...` : PostgreSQL en
  production.
- Ni Flyway ni Liquibase ; le schéma est géré manuellement.
- Spotless, Checkstyle, SpotBugs, JaCoCo et PIT absents de `pom.xml`.
- Environ 480 tests unitaires et 12 tests d’intégration ; couverture inconnue
  avant la référence.

## Ce que fait `$onboard`

1. Exécuter `.github/scripts/detect-stack.sh` et écrire
   `.specs/_stack.json`.
2. Détecter `migration == "none"` malgré PostgreSQL et signaler une
   modernisation prioritaire. Ce n’est pas fatal ; détecter les deux outils le
   serait.
3. Compter les sources et tests, puis classer le dépôt comme brownfield.
4. Exécuter `.github/scripts/harness.sh --baseline` pour capturer la réalité
   actuelle. Une couche absente vaut `skipped`, pas `fail`.
5. Écrire [`.specs/_onboarding.md`](./.specs/_onboarding.md) avec l’ordre
   recommandé.

## Ordre de modernisation recommandé

`$onboard` conseille approximativement :

1. **Ajouter Flyway**, établir une référence sur le schéma de production actuel
   et arrêter la gestion manuelle.
2. **Raccorder le fragment Maven du harness** : Spotless, Checkstyle, SpotBugs
   et JaCoCo. Partir de la couverture observée, pas de 90 %, puis relever le
   seuil à chaque itération. Garder PIT désactivé jusqu’à 80 %.
3. **Remplacer les tests H2 par Testcontainers PostgreSQL** lorsqu’ils exécutent
   du SQL.
4. **Introduire ArchUnit** avec une première règle interdisant les cycles, puis
   ajouter progressivement les frontières.
5. Attendre que les étapes 1 à 4 soient vertes avant d’exécuter `$spec`.

La méthodologie n’exige pas de rendre un projet brownfield parfait en une seule
fois. Elle capture la réalité, puis l’améliore délibérément.
