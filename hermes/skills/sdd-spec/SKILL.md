---
name: sdd-spec
description: "Spécifier une fonctionnalité SDD avec EARS-lite."
---

# Spécification SDD

Transformer une intention, un ticket ou une description en
`.specs/<feature-id>/01-spec.md`, sans inventer d'exigence.

Cette phase reste pilotée par l'agent Hermes principal : elle peut nécessiter
des réponses de l'utilisateur et ne doit pas être déléguée intégralement à un
sous-agent.

## Entrée

Accepter soit :

- une description libre ;
- une référence Jira, GitHub, Linear ou Azure Boards ;
- l'option explicite `--continue <feature-id>` pour reprendre une spécification
  existante.

Refuser une entrée trop vague lorsqu'elle ne contient pas assez d'information
pour identifier au moins un acteur, un objectif ou un comportement observable.
Expliquer alors précisément ce qui manque.

## Références à charger

Lire avant de rédiger :

- [EARS-lite](references/ears-lite.md) ;
- [ingestion d'un ticket](references/issue-tracker.md) si une référence externe
  est fournie ;
- [checklist de spécification](references/spec-review.md) ;
- [modèle de spécification](templates/spec.template.md).

Lire aussi, lorsqu'ils existent dans le projet utilisateur :

- `.specs/_onboarding.md` ;
- `docs/artifact-contract.md` ;
- `docs/spec-format.md`.

Avec `--continue <feature-id>`, lire d'abord le `01-spec.md` existant puis
`.specs/<feature-id>/02-spec-review.md` s'il existe.

Les références incluses dans ce skill restent la source de secours lorsque ces
documents projet n'existent pas.

## Identifiant de fonctionnalité

Produire un identifiant `kebab-case` de 40 caractères au maximum :

- avec un ticket, commencer par sa clé normalisée puis ajouter un slug court ;
- sans ticket, commencer par la date `YYYY-MM-DD-` puis ajouter un slug court.

Si le dossier existe déjà, refuser sauf si l'utilisateur a fourni `--continue`.

## Reprise après une revue

Lorsque `--continue` trouve `02-spec-review.md` :

1. extraire les constats `F-NNN` encore `open` et les entrées de
   `## New Questions Raised` au statut `open` ;
2. présenter à l'utilisateur les décisions métier encore nécessaires ;
3. modifier `01-spec.md` uniquement avec les preuves déjà disponibles ou les
   nouvelles réponses de l'utilisateur ;
4. pour chaque nouvelle question de revue, conserver son identifiant `Q-NNN` :
   l'ajouter à `## Open Questions` si elle reste ouverte, ou à
   `## Resolved Questions` avec la réponse et la date si elle est résolue ;
5. ne jamais marquer soi-même un constat comme résolu dans le rapport de revue ;
   cette vérification appartient à `/sdd-spec-review --continue` ;
6. résumer les modifications de la spécification en les reliant aux `F-NNN` et
   `Q-NNN` concernés.

Ne jamais traiter une correction demandée par la revue comme une nouvelle
source métier. Une information absente reste une question pour l'utilisateur.

## Processus

1. Récupérer la source via le connecteur ou MCP réellement disponible. Si aucun
   accès n'est configuré, demander le texte du ticket ; ne jamais simuler sa
   lecture.
2. Capturer la source, son URL et sa date. Les citations directes doivent rester
   courtes ; reformuler le reste fidèlement.
3. Extraire l'objectif métier, l'acteur, le périmètre et les exclusions
   explicites.
4. Décrire les entités et relations en vocabulaire métier, sans classe, table ou
   bibliothèque.
5. Créer des critères atomiques et testables `AC-001`, `AC-002`, etc. selon les
   formes EARS-lite. Ne jamais renuméroter un identifiant existant.
6. Transformer toute ambiguïté en question `Q-001`, `Q-002`, etc. Ne jamais
   choisir silencieusement une base de données, une authentification, une
   pagination, un format d'erreur, une unité, une devise, un seuil ou une durée.
7. Remplir le modèle et écrire `.specs/<feature-id>/01-spec.md`.
8. Appliquer la checklist. Corriger uniquement ce qui est prouvé par la source
   ou la conversation.
9. Si des questions restent ouvertes, les présenter clairement à l'utilisateur
   et s'arrêter. Après chaque réponse, déplacer la question dans
   `## Resolved Questions` avec la réponse et la date.

## Contraintes d'écriture

- Écrire uniquement `.specs/<feature-id>/01-spec.md`.
- Ne pas créer de design, de tâches, de code ou de test pendant cette phase.
- Ne pas utiliser de valeur par défaut non fournie.
- Ne pas publier de secret, de session ou de donnée d'authentification.

## Terminé lorsque

- `01-spec.md` existe et respecte le modèle ;
- il contient au moins un `AC-NNN` atomique et testable ;
- toutes les ambiguïtés sont identifiées comme `Q-NNN` ;
- l'utilisateur connaît les questions à résoudre ;
- une fois les questions résolues, proposer `/sdd-spec-review --continue
  <feature-id>` si un rapport de revue existe déjà, sinon `/sdd-spec-review
  <feature-id>` ; si la commande n'est pas installée, annoncer l'étape comme à
  venir.
