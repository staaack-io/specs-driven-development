---
name: spec
description: "Transformer une intention ou un ticket en spécification SDD au format EARS. Utiliser lorsque l’utilisateur invoque $spec ou demande de spécifier une fonctionnalité."
---

# $spec

**Phase :** 1 — spécification
**Agent responsable :** `.codex/agents/spec-author.toml`
**Skills utilisés :** `ears-spec-authoring`, `issue-tracker-ingestion`,
`requirements-traceability`

## Objectif

Transformer une intention brute, une phrase, un paragraphe ou l’URL d’un ticket
en spécification EARS complète sous
`.specs/<feature-id>/01-spec.md`.

## Entrées

Fournir soit :

- un texte libre décrivant la fonctionnalité ;
- une référence de ticket : `JIRA-123`, URL d’issue GitHub, identifiant Linear
  ou URL Azure Boards.

Pour un ticket, le récupérer via le serveur MCP configuré décrit dans
`issue-tracker-ingestion` et traiter son contenu comme source.

## Lectures

- texte ou ticket fourni ;
- `.specs/_onboarding.md` pour le contexte de stack ;
- `.codex/templates/spec.template.md` ;
- `.codex/checklists/spec-review.md`.

## Écritures

- `.specs/<feature-id>/01-spec.md`, avec un identifiant en `kebab-case`
  préfixé par la date `YYYY-MM-DD-`.

## Processus

1. Déduire `<feature-id>`. Refuser si le dossier existe déjà, sauf avec
   `--continue`.
2. Extraire l’objectif métier, l’acteur principal, le périmètre et les
   exclusions explicites.
3. Écrire des critères `AC-001`, `AC-002`, etc., selon les formes EARS.
   Chaque critère doit être testable.
4. Consigner les exigences non fonctionnelles avec des valeurs mesurables.
   Si elles sont inconnues, ouvrir une question au lieu de deviner.
5. Créer les questions `Q-001`, `Q-002`, etc. **Ne jamais inventer de
   réponse.** S’arrêter et les présenter à l’utilisateur.
6. Produire le fichier avec le modèle.

## Refuser si

- l’entrée contient moins de trois noms ou verbes distincts et reste trop vague ;
- un critère exige une supposition non formulée.

## Terminé lorsque

- `01-spec.md` existe avec au moins un critère et aucune réponse inventée ;
- toutes les ambiguïtés figurent sous `## Open Questions` avec un identifiant ;
- l’utilisateur sait que l’étape suivante est `$spec-review`, après résolution
  des questions.
