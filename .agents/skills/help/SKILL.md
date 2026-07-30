---
name: help
description: "Expliquer les skills disponibles du workflow SDD. Utiliser lorsque l’utilisateur invoque $help ou demande comment utiliser le framework."
---

# $help

**Phase :** méta — lecture seule
**Agent responsable :** aucun

## Objectif

Afficher le catalogue des skills de workflow et l’ordre recommandé. Expliquer
facultativement un skill en détail.

## Entrées

- `<skill-name>` facultatif, sans le préfixe `$`.

## Lectures

- `.agents/skills/` ;
- le `SKILL.md` demandé le cas échéant.

## Écritures

Aucune.

## Processus

- Sans argument, afficher le tableau des workflows et les formulations en
  langage naturel.
- Avec un argument, résumer objectif, entrées, lectures, écritures, processus,
  refus et condition de fin du skill.

## Refuser si

Jamais.

## Terminé lorsque

L’aide est affichée.
