# Spécification : gift-card-checkout

| Champ | Valeur |
|---|---|
| Identifiant | `2025-01-15-gift-card-checkout` |
| Responsable | checkout-team |
| Statut | `PASS`, validé le 2025-01-22 |
| Source | Texte produit : « Permettre aux utilisateurs d'utiliser une carte cadeau au paiement, avant calcul des taxes. Une carte peut être partiellement utilisée. » |

## Objectif métier

Améliorer la conversion au paiement en acceptant les cartes cadeaux. Elles
réduisent le montant payable avant calcul des taxes et peuvent être utilisées
partiellement sur plusieurs commandes.

## Acteur principal

Client authentifié sur la page `/checkout`.

## Dans le périmètre

- Accepter un code de carte cadeau de 16 caractères au paiement.
- Valider que la carte existe, est active et possède un solde.
- Appliquer le solde au sous-total avant les taxes.
- Consigner une utilisation partielle lorsque le sous-total est inférieur au solde.
- Présenter une erreur métier si la carte est invalide, expirée ou épuisée.

## Hors périmètre explicite

- Émission ou recharge d'une carte cadeau.
- Remboursement vers une carte cadeau.
- Combinaison de plusieurs cartes sur une commande, différée à la v2.

## Acceptance Criteria

### AC-001 : appliquer une carte valide

**Pendant qu'**un client authentifié paie un panier non vide, **quand** il fournit
un code valide et actif avec un solde suffisant, **le système doit** réduire le
sous-total du montant de la commande si la carte le couvre, ou du solde complet
sinon, recalculer les taxes et persister un `GiftCardRedemption` reliant commande,
carte et montant appliqué.

### AC-002 : refuser un code inconnu

**Quand** un client fournit un code absent, **le système doit** refuser avec HTTP
422 et le code `gift_card.unknown`, sans modifier le total du panier.

### AC-003 : refuser une carte expirée

**Quand** le code correspond à une carte dont `expires_at` est passé, **le système
doit** refuser avec HTTP 422 et `gift_card.expired`.

### AC-004 : refuser une carte épuisée

**Quand** le solde restant est nul, **le système doit** refuser avec HTTP 422 et
`gift_card.depleted`.

### AC-005 : utilisation partielle

**Pendant que** le solde d'une carte est inférieur au sous-total, **quand**
l'utilisation réussit, **le système doit** débiter exactement le sous-total et
laisser la différence comme nouveau solde. Cette formulation reprend le chemin
partiel d'AC-001 afin de lui donner un test comptable dédié.

### AC-006 : nouvelle tentative idempotente

**Quand** un client fournit deux fois le même code avec le même en-tête
`Idempotency-Key` dans les 24 heures, **le système doit** appliquer la carte une
seule fois et renvoyer la même réponse au second appel.

## Exigences non fonctionnelles

- **Latence :** p95 ≤ 150 ms côté serveur sous 50 RPS.
- **Débit :** au moins 100 utilisations par seconde sur un pod 4 vCPU.
- **Sécurité :** les codes sont des secrets assimilés à des données personnelles,
  jamais journalisés en clair et hachés en SHA-256 avec sel propre au déploiement.
- **Observabilité :** compteurs `gift_card.redeem.success` et
  `gift_card.redeem.failure{reason}`, plus une ligne INFO structurée avec l'ID de
  carte, jamais le code, et l'ID de commande.
- **Audit :** chaque ligne d'utilisation est en ajout seul, sans mise à jour ni suppression.

## Open Questions

*(aucune — toutes ont été résolues avant le verdict PASS)*

## Resolved Questions

- **Q-001, résolue le 2025-01-15 :** plusieurs cartes par commande ? Non, différé à la v2.
- **Q-002, résolue le 2025-01-15 :** si le sous-total devient nul, les taxes sont calculées sur ce sous-total et valent donc zéro.
