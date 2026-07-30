---
name: ship
description: "Préparer le plan facultatif de livraison après commit sans déployer. Utiliser lorsque l’utilisateur invoque $ship ou demande de préparer une fonctionnalité approuvée pour sa livraison."
---

# $ship

**Phase :** 8 — préparation post-commit et pré-déploiement
**Agent responsable :** `.codex/agents/spring-code-reviewer.toml`, réutilisé
sans nouveau rôle
**Skills utilisés :** `shipping-and-launch`,
`spring-security-baseline`, `flyway-or-liquibase-detection`

## Objectif

Après une revue approuvée et le commit humain, produire un plan structuré :
portes pré-déploiement, retour arrière, observabilité, feature flags, déploiement
progressif et notes de version. **Ne jamais déployer** ; afficher seulement la
commande destinée à l’utilisateur.

## Entrées

- `<feature-id>` facultatif, par défaut la fonctionnalité la plus récente dont
  la revue vaut `Approve` ou `Approve with waivers` ;
- `--base <ref>`, par défaut `origin/main`.

## Lectures

- spécification, conception, tâches, validation et revue ;
- `.specs/_baseline.json` ;
- diff et journal Git depuis la base ;
- `shipping-and-launch`, source de vérité ;
- modèle `ship-plan.template.md`.

## Écritures

- `09-ship-plan.md`.

## Processus

1. Résoudre la fonctionnalité ou refuser si aucune revue approuvée n’existe.
2. Vérifier `PASS`, `Approve*`, zéro question ouverte, aucune régression et
   tous les fichiers dans `files_in_scope`. S’arrêter au premier échec avec la
   commande de reprise.
3. Classer chaque migration Flyway ou Liquibase : `forward-only safe`,
   `expand`, `contract` ou `breaking`. Exiger un ADR pour `breaking`.
4. Inventorier endpoints, handlers, tâches planifiées et clients HTTP. Exiger
   une métrique `MeterRegistry` pour chaque nouvelle surface.
5. Remplir toutes les sections du modèle ; `n/a` exige une justification.
6. Présenter comme `Q-NNN` les informations humaines manquantes : responsable
   du flag, seuils et cohortes. Ne rien inventer.
7. Préparer des notes externes en trois puces maximum et des notes internes avec
   diff, critères, ADR, migrations, flag et tableau de bord.
8. Suggérer la commande du pipeline, `kubectl rollout` ou `mvn deploy`, sans
   l’exécuter.

## Refuser si

- validation ou revue non approuvée ;
- question ouverte ;
- migration cassante sans ADR ;
- nouvelle surface sans métrique ;
- modification d’une migration déjà publiée ;
- diff vide.

## Terminé lorsque

Les sept sections sont remplies, toutes les portes valent `PASS`, chaque
migration possède un retour arrière, chaque surface une métrique et une alerte
ou une justification, et les deux catégories de notes existent. Afficher alors
la commande de déploiement à exécuter manuellement.
