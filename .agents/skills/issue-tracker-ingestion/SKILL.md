---
name: issue-tracker-ingestion
description: Récupérer via MCP les détails d’une issue, pull request ou ticket Jira, GitHub, Linear ou Azure Boards dans `## Source` de `01-spec.md`. Utiliser au début de `$spec` lorsqu’un ticket externe est référencé.
when_to_use:
  - Phase 1, Specify — transformer un identifiant de ticket en spécification.
  - Vérifier que `## Source` reflète fidèlement le ticket.
authoritative_references:
  - docs/codex-migration.md
  - .codex/templates/spec.template.md
---

# Ingestion d'un ticket

## Sources prises en charge

| Source | Serveur MCP | Forme de l'identifiant |
|---|---|---|
| Jira (Atlassian) | `atlassian` | `SHOP-1422` |
| GitHub Issues | `github` | `owner/repo#42` ou URL |
| GitHub Pull Requests | `github` | `owner/repo!42` ou URL |
| Linear | `linear` | `ENG-123` |
| Azure Boards | `azure-devops` | `AB#54321` |

Si aucun MCP n'est configuré, utiliser le texte fourni par l'utilisateur. Ne jamais inventer de ticket.

## Procédure par source

1. Résoudre l'identifiant puis récupérer le ticket via MCP.
2. Capturer le titre, la description, le statut, les labels, le responsable, les
   dix derniers commentaires, les noms des pièces jointes, l'URL et l'horodatage.
3. Écrire un bloc fidèle dans `01-spec.md` :

   ```markdown
   ## Source

   - **System:** Jira
   - **ID:** SHOP-1422
   - **URL:** https://example.atlassian.net/browse/SHOP-1422
   - **Title:** Appliquer une carte cadeau au paiement
   - **Status:** In Progress
   - **Fetched:** 2026-04-18T10:00:00Z

   ### Description (verbatim)
   > Les utilisateurs peuvent appliquer une carte cadeau pendant le paiement.

   ### Comments (last N, verbatim)
   > [PM, 2026-04-15] : seuls les acheteurs authentifiés sont concernés.
   ```

4. Extraire les AC candidats **uniquement du texte fidèle**. Ne pas reformuler les
   exigences : citer la ligne source et placer l'AC dessous. Sans ligne source,
   placer le candidat sous `## Open Questions` comme `Q-NNN`.

## Absence d'invention

Si un champ source manque, par exemple des critères d'acceptation, l'agent ne le
complète pas. Il écrit une `Q-NNN`, puis `$spec` s'arrête et interroge l'utilisateur.

## Mise à jour après modification du ticket

- Récupérer à nouveau le ticket.
- Consigner le diff sous `## Out-of-Band Inputs` avec la date et la nature du changement.
- Ajouter une `Q-NNN` pour toute nouvelle exigence absente des AC.

## Anti-patterns

- Affirmer que le ticket dit X sans le citer.
- Résumer les commentaires au lieu de les citer.
- Déduire un AC du seul titre.
- Ignorer silencieusement un commentaire qui contredit la description.
- Supposer que le responsable du ticket est l'auteur de la spécification.
