---
name: onboard
description: "Inspecter et classer un dépôt Spring avant sa première fonctionnalité SDD. Utiliser lorsque l’utilisateur invoque $onboard ou demande d’intégrer un projet existant."
---

# $onboard

**Phase :** 0 — préparation
**Agent responsable :** `.codex/agents/spring-onboarding.toml`
**Skills utilisés :** `brownfield-onboarding`, `maven-harness-pom`,
`flyway-or-liquibase-detection`, `harness-report-parsing`,
`archunit-rules`

## Objectif

Inspecter le dépôt, le classer comme greenfield ou brownfield, capturer une
référence du harness et produire `.specs/_onboarding.md`.

## Entrées

Aucune obligation. Un chemin facultatif limite l’analyse :

- dépôt simple : aucun argument, lecture de `./pom.xml` ;
- Maven multi-module : chemin du sous-module ;
- monorepo polyglotte : chemin du module Maven. Les applications voisines sont
  enregistrées sous `siblings` comme contexte ; elles gardent leur pipeline.

## Lectures

- `pom.xml` et sous-modules ;
- comptage de `src/main/**` et `src/test/**` ;
- migrations ou changelogs ;
- artefacts `.specs/` existants.

## Écritures

- `.specs/_onboarding.md` ;
- `.specs/_stack.json` produit par `detect-stack.sh` ;
- `.specs/_baseline.json` si des tests existent.

## Processus

1. Résoudre le module et exécuter la détection. Refuser
   `migration == "both"`.
2. Classer greenfield si aucun vrai code de production n’existe en dehors du
   squelette Initializr ; brownfield sinon.
3. Pour un brownfield, exécuter le harness en mode `--baseline` sans corriger
   ses échecs.
4. Comparer le POM au fragment du harness et lister les couches absentes.
5. Écrire classification, module, applications voisines, stack, portes de
   référence, couches manquantes et point de départ `$spec`.

## Refuser si

- Flyway et Liquibase sont tous deux détectés ;
- aucun `pom.xml` n’existe au chemin résolu.

## Terminé lorsque

`.specs/_onboarding.md` existe et que l’utilisateur reçoit un résumé court
avec la prochaine commande.
