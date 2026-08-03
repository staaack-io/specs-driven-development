---
name: sdd-review
description: >-
  Produire une revue technique SDD informative à partir de lectures Spring et
  React/Next.js déléguées. Utiliser avec /sdd-review [<feature-id>] [--base <ref>].
---

# Revue technique SDD

Exécuter `/sdd-review [<feature-id>] [--base <ref>]` après la validation lorsque
l'utilisateur demande cet audit facultatif. Les arguments restent des valeurs
structurées validées par `scripts/review_guard.py`; ils ne deviennent jamais une
commande shell.

## Références obligatoires

- [contrat de délégation](references/delegation-contract.md) ;
- [contrat de revue](references/review-contract.md) ;
- [rôle Spring](references/role-spring-code-reviewer.md) ;
- [rôle React/Next.js](references/role-react-nextjs-code-reviewer.md) ;
- [modèle de rapport](templates/code-review.template.md).

## Processus

1. Identifier la feature facultative et calculer le diff depuis la base.
2. Router les sources Java/Kotlin/POM/SQL vers le rôle Spring et les sources
   JavaScript/TypeScript/React/Next.js vers le rôle React/Next.js.
3. Fournir à chaque rôle uniquement le diff et les artefacts en lecture seule.
4. Valider l'absence de changement délégué, puis consolider et dédupliquer les
   constats structurés.
5. Expurger les preuves, rendre un verdict `approve|request-changes` informatif
   et publier atomiquement l'unique `08-code-review.md`.

## Limites

Les rôles délégués n'écrivent aucun fichier et ne reçoivent aucun handle vers le
rapport. Le garde principal est l'unique writer. La revue ne bloque ni commit,
ni push, ni pull request, ni fusion. Elle ne sollicite aucun reviewer humain et
n'exécute aucune opération réseau, VPS ou déploiement.

## Terminé lorsque

Les lectures spécialisées requises ont convergé, chaque constat possède une
sévérité fermée et une correction, les doublons sont retirés et le rapport
unique expurgé est publié atomiquement.
