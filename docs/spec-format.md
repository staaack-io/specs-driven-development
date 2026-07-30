# Format des spécifications — EARS-lite

La boîte à outils utilise **EARS-lite**, une version simplifiée de
« Easy Approach to Requirements Syntax », pour les critères d’acceptation. Une
spécification doit rester courte, testable et traçable.

## Pourquoi EARS-lite

- **Atomique.** Une condition et un résultat, faciles à relier à un test.
- **Testable.** La forme de chaque proposition se transforme directement en test
  Étant donné/Quand/Alors ou en assertion par propriétés.
- **Traçable.** Chaque critère possède un identifiant stable `AC-001`,
  référencé depuis les tâches, tests, symboles et rapports.

Le sous-ensemble utilisé contient cinq formes, sans grammaire formelle ni
dépendance à un outil.

## Les cinq formes

```text
Universel :       Le système doit <action>.
Événement :       Lorsque <déclencheur>, le système doit <action>.
État :            Tant que <état>, le système doit <action>.
Optionnel :        Lorsque <fonctionnalité présente>, le système doit <action>.
Indésirable :      Si <condition indésirable>, alors le système doit <mesure>.
```

## Convention des identifiants AC

- Format : `AC-NNN`, avec trois chiffres et une progression monotone dans la
  fonctionnalité.
- Un identifiant n’est **jamais réutilisé**, même après suppression du critère ;
  la suppression laisse une entrée témoin.
- Les tests référencent le critère avec
  `@DisplayName("AC-007: rejects expired card")` ou `@Tag("AC-007")`. La
  matrice de traçabilité reconnaît les deux formes.

## Modèle de spécification

Voir [`.codex/templates/spec.template.md`](../.codex/templates/spec.template.md).
Les noms de sections ci-dessous restent stables car les skills et hooks les
consomment :

```markdown
# Spec: <feature-id> — <titre court>

## Source
- Tracker: <Jira/GitHub/Linear/Azure/ad-hoc>
- ID: <FEATURE-123>
- URL: <lien>
- Snapshot date: <YYYY-MM-DD>

## Goal
<un paragraphe>

## Acceptance Criteria
- AC-001: Lorsque <déclencheur>, le système doit <action>.
- AC-002: Tant que <état>, le système doit <action>.
- AC-003: Si <condition indésirable>, alors le système doit <mesure>.

## Non-Goals
- ...

## Glossary
- **Terme** — définition.

## Open Questions
- Q-001: <question>
  - Why it matters: <impact>
  - Candidate options: <option-A>, <option-B>
  - Status: open

## Resolved Questions
<vide>
```

## Exemple complet

```markdown
# Spec: GIFT-CARD-001 — Appliquer une carte cadeau au paiement

## Source
- Tracker: Jira
- ID: SHOP-1422
- URL: https://example.atlassian.net/browse/SHOP-1422
- Snapshot date: 2026-04-18

## Goal
Permettre à un client d’utiliser une carte cadeau pendant le paiement, sans
jamais rendre le total négatif, et afficher l’utilisation sur le reçu.

## Acceptance Criteria
- AC-001: Lorsque le client applique une carte valide, non expirée et créditée, le système doit réduire le total du minimum entre le solde et le total.
- AC-002: Lorsque l’utilisation réussit, le système doit enregistrer le montant utilisé et le solde restant sur le reçu.
- AC-003: Si le code est inconnu, expiré ou sans solde, le système doit refuser avec GC_INVALID et conserver le total.
- AC-004: Tant que la commande est dans l’état PAID, le système doit refuser toute nouvelle utilisation avec GC_ORDER_LOCKED.
- AC-005: Lorsque deux cartes sont appliquées, le système doit respecter l’ordre reçu et s’arrêter lorsque le total atteint zéro.

## Non-Goals
- Émettre de nouvelles cartes cadeaux.
- Rembourser vers une carte cadeau.
- Convertir plusieurs devises.

## Glossary
- **Carte cadeau** — bon prépayé identifié par un code de 16 caractères, avec un solde non négatif et une date d’expiration.
- **Utilisation** — action de débiter la carte et de réduire le total de la commande.

## Open Questions
- Q-001: Les utilisations d’une commande annulée doivent-elles être inversées automatiquement ou passer par un remboursement séparé ?
  - Why it matters: détermine si le service doit écouter les événements d’annulation.
  - Candidate options: inversion automatique, remboursement manuel, refus d’annuler.
  - Status: open

## Resolved Questions
<vide>
```

## Ce qui n’appartient pas à une spécification

- Les choix d’implémentation, comme une classe, une bibliothèque ou une colonne
  de base de données, appartiennent à `03-design.md`.
- Les seuils de couverture et les portes appartiennent au harness.
- Les estimations de temps appartiennent éventuellement aux tâches.
- Le texte marketing ou une longue justification n’appartient pas à
  `## Goal`.

## Antipatterns refusés par l’auteur de spec

- « Le système doit être rapide. » n’est pas testable. Définir une mesure, par
  exemple une latence p95 inférieure à 200 ms sous N requêtes par seconde, ou ne
  pas en faire un critère.
- « Nous voulons probablement… » devient un `Q-NNN` ; l’agent ne choisit pas.
- Un critère qui regroupe plusieurs conditions doit être découpé.
- Une fuite d’implémentation comme
  « appeler `PaymentService.charge()` » doit être reformulée en comportement
  observable.
