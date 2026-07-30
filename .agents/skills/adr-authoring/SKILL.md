---
name: adr-authoring
description: Rédiger des décisions d’architecture au format MADR sous `.specs/<feature-id>/adr/`. Utiliser pour toute décision technique non évidente, valeur par défaut remplacée ou dérogation accordée.
when_to_use:
  - Phase 3, Plan — consigner toute décision de conception qui présente des alternatives.
  - Phase 6, Validate — déroger à une porte du harness.
  - Phase 7, revue de code — accepter un constat sans le corriger.
authoritative_references:
  - https://adr.github.io/madr/
  - .codex/templates/adr.template.md
---

# Rédaction des ADR

## Quand en écrire un

Écrire un ADR si au moins une condition est vraie :

- la décision présente des alternatives plausibles qu'un autre ingénieur pourrait préférer ;
- elle remplace une valeur par défaut du framework ;
- elle accorde une dérogation à une porte du harness : mutation, couverture, rupture OpenAPI ou CVE ;
- elle contraint les travaux futurs, par exemple l'exclusion de Kafka d'un module.

Ne pas écrire d'ADR pour un choix imposé de façon unique par le ticket source ou
pour une décision mécanique triviale comme le nom d'une variable.

## Emplacement

`.specs/<feature-id>/adr/NNN-<slug>.md`, où `NNN` est complété par des zéros et unique dans la fonctionnalité.

## Sections requises par MADR

- **Title** — court et formulé comme une décision.
- **Status** — `proposed` | `accepted` | `rejected` | `superseded by NNN` | `deprecated`.
- **Context** — problème, contraintes et informations connues.
- **Decision drivers** — forces en présence : performance, expérience de l'équipe, coût, sécurité.
- **Considered options** — au moins deux.
- **Decision outcome** — option choisie et justification en un paragraphe.
- **Consequences** — positives ET négatives.
- **Pros and cons of each option** — tableau symétrique.
- **Links** — vers `01-spec.md`, la section de `03-design.md`, les ADR liés et les références externes.

## Exemples de noms

```text
.specs/shop-1422-gift-card-checkout/adr/
├── 001-use-liquibase-for-migrations.md
├── 002-redeem-balance-stored-as-cents-int.md
├── 003-waive-mutation-on-config-classes.md
└── 004-breaking-api-change-error-envelope.md
```

## Anti-patterns

- Un ADR avec une seule option : c'est une note, pas une décision.
- Un ADR sans section `Consequences`, notamment sans conséquence négative.
- « X est meilleur » sans facteur ni raison mesurable.
- Un ADR écrit après la fusion du code ; l'écrire pendant Plan et l'affiner pendant Validate.
- Modifier un ADR `accepted` ; le marquer `superseded by NNN` et en écrire un nouveau.

## Cycle des statuts

```text
proposed → accepted → (plus tard) superseded
                ↓
              rejected
```

Un ADR `proposed` peut être fusionné car il documente la direction actuelle. Un
ADR `rejected` reste utile : il explique pourquoi l'option évidente a été écartée.
