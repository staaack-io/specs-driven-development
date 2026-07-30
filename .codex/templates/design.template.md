# Conception : <FEATURE-ID>

> Responsable : `spring-architect` · Phase 3 · Modèle : `.codex/templates/design.template.md`
>
> **Aucune invention.** Si une décision est nécessaire mais absente des demandes de l'utilisateur et du code existant, consigner une `Q-NNN` et poser la question. Les ADR rendent les décisions explicites.

## Inputs

- Révision de `01-spec.md` : <git-sha ou horodatage>
- État de la stack fourni par `.github/scripts/detect-stack.sh` :
  - Outil de build : <maven | gradle>
  - Version de Java : <25>
  - Version de Spring Boot : <4.x>
  - Moteur de base de données : <postgres | mysql | h2 | …>
  - Outil de migration : <flyway | liquibase | none>
  - Testcontainers : <present | absent>
  - Serveurs MCP disponibles : <jira | github | linear | …>

## Architecture Overview

<3 à 6 phrases décrivant la forme générale du changement, avec des références aux modules et ADR.>

## ADRs

> Format MADR. Chaque ADR se trouve dans `.specs/<feature-id>/adr/NNN-<slug>.md`.

- ADR-001 : <titre> — statut : <proposed | accepted | superseded>
- ADR-002 : …

## Spring Component Map

> Les composants sont regroupés **par fonctionnalité** dans les packages de premier niveau. Dans chaque fonctionnalité, les classes résident sous `api` (publié) ou `internal` (privé). Ne pas introduire de packages de premier niveau `controller`/`service`/`repository`/`model`.

| Fonctionnalité | Visibilité | Composant | Responsabilité |
|---|---|---|---|
| `<feature>` | api | `<feature>.api.XService` (interface) | surface publiée |
| `<feature>` | api | `<feature>.api.XEvent` | événement de domaine |
| `<feature>` | internal | `<feature>.internal.XController` | adaptateur HTTP |
| `<feature>` | internal | `<feature>.internal.XServiceImpl` | logique métier |
| `<feature>` | internal | `<feature>.internal.XRepository` | persistance |

## Module Boundaries

> Chaque package de premier niveau est un module. Lister les modules touchés et le sens de leurs dépendances. ArchUnit impose les frontières (voir le skill `archunit-rules`) : les packages `..internal..` sont privés et les cycles entre packages de premier niveau sont interdits.

- `<module>` — package d'API publique : `<...api>` ; dépend de : `<autres modules>` ; événements publiés : `<événements>`

## Entity Relationship Model

> Relier les entités conceptuelles de `01-spec.md` aux décisions de persistance de la conception.

| Entité | Rôle | Attributs principaux | Relations (cardinalité) | Notes de persistance |
|---|---|---|---|---|
| `<entité>` | `<rôle métier>` | `<attributs>` | `<A 1..* B, A 0..1 C>` | `<racine d'agrégat / propriété / règles de cascade>` |

## OpenAPI Sketch

```yaml
paths:
  /<resource>:
    post:
      summary: ...
      requestBody: { ... }
      responses:
        '201': { ... }
        '400': { description: entrée invalide, ... }
        '409': { description: conflit, ... }
```

## Data Model + Migrations

- Tables ou collections touchées : <liste>
- Outil de migration : <flyway | liquibase>
- Fichiers de migration : `db/migration/V<N>__<slug>.sql` (Flyway) ou `db/changelog/<slug>.xml` (Liquibase)
- Réversibilité : <reversible | forward-only avec justification>

## Security Posture

- Authentification : <none | JWT | session | OAuth2 resource server>
- Règles d'autorisation : <rôles ou scopes>
- Données personnelles traitées : <champs>
- Secrets : <lieu de stockage>

## Risks + Rollback

| Risque | Probabilité | Impact | Réduction du risque | Retour arrière |
|---|---|---|---|---|

## Non-Functional Requirements

> Uniquement les exigences non fonctionnelles explicitement formulées par l'utilisateur ou la source. Sinon, créer une `Q-NNN`.

- (aucune)

## Open Questions

- Q-001 : …

## Resolved Questions

- (aucune pour le moment)

## Sign-off

- [ ] Chaque AC de `01-spec.md` est couverte par au moins un composant ou une tâche.
- [ ] Toutes les `Q-NNN` sont résolues ou différées avec justification.
- [ ] Revue effectuée par l'utilisateur le <YYYY-MM-DD>.
