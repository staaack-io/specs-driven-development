---
name: ears-spec-authoring
description: Rédiger des critères d’acceptation EARS-lite avec identifiants AC-NNN stables et questions Q-NNN explicites. Utiliser pour créer ou modifier `01-spec.md`, transformer un ticket en critères ou produire une spécification.
when_to_use:
  - Phase 1, Specify — transformer une demande de fonctionnalité en AC testables.
  - Rendre concrète toute exigence vague comme « rapide » ou « sécurisé ».
authoritative_references:
  - https://alistair.cockburn.us/coffee-cups-and-the-EARS-syntax/
  - .codex/templates/spec.template.md
  - docs/spec-format.md
---

# Rédaction de spécifications EARS-lite

## Les cinq formes

Chaque AC suit une des formes suivantes :

| Forme | Squelette | Quand l'utiliser |
|---|---|---|
| **Universelle** | Le système doit `<réponse>`. | Invariant toujours vrai. |
| **Événementielle** | Quand `<déclencheur>`, le système doit `<réponse>`. | Un événement externe provoque un comportement. |
| **Pilotée par l'état** | Pendant `<état>`, le système doit `<réponse>`. | Le comportement tient pendant tout un état. |
| **Fonctionnalité optionnelle** | Lorsque `<fonctionnalité incluse>`, le système doit `<réponse>`. | Dépend de la configuration. |
| **Comportement indésirable** | Si `<condition indésirable>`, alors le système doit `<atténuation>`. | Gestion d'erreur ou d'échec. |

## Règles imposées par `spec-review.md`

1. **Un AC = une condition + un résultat.** Scinder tout critère qui combine plusieurs comportements.
2. **Identifiants stables.** Format `AC-NNN`, sans jamais renuméroter. Une insertion prend le prochain numéro.
3. **Aucune implémentation.** Ni classe, colonne, bibliothèque ni valeur par défaut.
4. **Aucune exigence vague.** « Rapide » devient par exemple `< 200 ms p95 sous 50 RPS`, ou une `Q-NNN`.
5. **Aucune valeur par défaut silencieuse.** Si l'utilisateur n'a pas choisi le comportement, écrire une `Q-NNN`.
6. **Protéger les bascules risquées par un feature flag.** Pour toute migration ou
   substitution visible par l'utilisateur, créer une `Q-NNN` sur le flag et la
   procédure de retour arrière. Utiliser un flag par défaut, sauf dérogation explicite.

## Issue de secours Q-NNN

Lorsque vous devriez autrement inventer :

```markdown
## Open Questions
- **Q-001** — Le ticket indique que « les utilisateurs obtiennent une remise » sans préciser si les visiteurs non authentifiés sont concernés. Une décision est nécessaire avant d'écrire AC-005.
```

Après la réponse directe de l'utilisateur, déplacer la question sous
`## Resolved Questions` avec la réponse et la date.

## Exemple

Ticket source : les utilisateurs peuvent appliquer une carte cadeau au paiement,
elle réduit le total et une carte déjà utilisée provoque une erreur.

Mauvais :

> AC-001 : le système utilise une entité `GiftCard` avec une colonne `usedAt` et renvoie 400 lorsque `usedAt != null`.

Ce critère invente une classe, une colonne et un statut HTTP.

Bon :

```markdown
## Acceptance Criteria

- **AC-001** — Quand un acheteur authentifié fournit un code de carte cadeau avec sa commande, le système doit réduire le total du solde restant de la carte, sans dépasser le sous-total.
- **AC-002** — Quand le solde d'une carte cadeau fournie est épuisé, le système doit refuser la demande et en informer l'acheteur.
- **AC-003** — Quand le code fourni n'existe pas, le système doit refuser la demande et signaler que le code est inconnu.
- **AC-004** — Tant qu'une carte possède un solde, le système doit permettre son utilisation sur plusieurs commandes jusqu'à épuisement.

## Open Questions
- **Q-001** — Les paiements invités peuvent-ils utiliser une carte cadeau ?
- **Q-002** — Quel est le nombre maximal de cartes par commande ?
- **Q-003** — Quel format d'erreur l'acheteur voit-il dans l'interface ?
```

## Auto-vérification avant la revue

- [ ] Un testeur junior peut-il écrire un Étant donné/Quand/Alors pour chaque AC sans poser de question ?
- [ ] La suppression d'un AC changerait-elle un comportement visible ?
- [ ] Un AC combine-t-il plusieurs conditions ou résultats qui devraient être séparés ?
- [ ] Tous les détails inventés ont-ils été transformés en `Q-NNN` ?
