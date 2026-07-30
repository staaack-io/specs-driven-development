# Spécification : <FEATURE-ID> — <titre court>

> Responsable : `spec-author` · Phase 1 · Modèle : `.codex/templates/spec.template.md`
>
> **Aucune invention.** Si une information ne figure ni dans le ticket source, ni dans la conversation, ni dans le code existant, l'enregistrer comme `Q-NNN` et interroger l'utilisateur.

## Source

- Outil de suivi : <Jira | GitHub | Linear | Azure Boards | ad-hoc>
- Identifiant : <par exemple SHOP-1422 ou owner/repo#123>
- URL : <lien>
- Date de capture : <YYYY-MM-DD>
- Résumé de la capture :
  > <titre et description du ticket, cités ou reformulés>

## Goal

<un paragraphe décrivant le résultat visible par l'utilisateur>

## Acceptance Criteria

Utiliser les formes EARS-lite décrites dans `docs/spec-format.md`. Une condition par AC. Les identifiants restent stables et ne sont jamais réutilisés.

- AC-001 : <Le système doit…> | <Quand…, le système doit…> | <Si…, alors le système doit…> | <Pendant que…, le système doit…> | <Lorsque la fonctionnalité…, le système doit…>
- AC-002 : …

## Domain Entities and Relationships

> Modèle conceptuel uniquement : vocabulaire métier, sans détails de classes, tables ou bibliothèques. Si une information manque, ajouter une `Q-NNN`.

### Entités

- **<Nom de l'entité>** — rôle : <ce qu'elle représente> ; attributs métier principaux : <liste>

### Relations

- **<Entité A> 1..* <Entité B>** — sens : <règle métier>
- **<Entité C> 0..1 <Entité D>** — sens : <règle d'association optionnelle>

## Non-Goals

- <élément explicitement hors périmètre>

## Glossary

- **Terme** — définition.

## Assumptions

> Uniquement les hypothèses explicitement fournies par l'utilisateur ou le ticket source. L'agent n'ajoute jamais d'hypothèse silencieusement.

- (aucune)

## Out-of-Band Inputs

> Toute information fournie pendant la session mais absente du ticket source, par exemple une capture d'écran ou une précision dans le chat. Elle est consignée pour assurer la traçabilité.

- (aucune)

## Open Questions

> Toute incertitude DOIT être consignée ici. L'agent ne choisit pas de valeur par défaut.

- Q-001 : <question>
  - Pourquoi c'est important : <impact sur la conception ou le comportement>
  - Options candidates identifiées : <option-A>, <option-B>
  - Statut : open

## Resolved Questions

> Rempli par l'agent après la réponse de l'utilisateur, avec le texte exact et l'horodatage.

- (aucune pour le moment)

## Sign-off

- [ ] Tous les AC sont atomiques et testables.
- [ ] Toutes les `Q-NNN` sont résolues ou explicitement différées avec justification.
- [ ] La source est consignée.
- [ ] Revue effectuée par l'utilisateur le <YYYY-MM-DD>.
