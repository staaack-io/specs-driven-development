---
name: shipping-and-launch
description: Préparation pré-déploiement d’une fonctionnalité Spring Boot 4, avec portes, retour arrière, observabilité, notes et déploiement progressif. Utiliser avec `$ship` après approbation de `$review`. L’agent ne déploie jamais.
when_to_use:
  - Phase 8, Ship — commande `$ship` après approbation de `$review`.
  - Revue pré-déploiement brownfield nécessitant un plan de lancement structuré.
authoritative_references:
  - .agents/skills/ship/SKILL.md
  - .codex/templates/ship-plan.template.md
  - .agents/skills/spring-security-baseline/SKILL.md
  - .agents/skills/flyway-or-liquibase-detection/SKILL.md
---

# Livraison et lancement

> Plus vite peut être plus sûr : les changements petits, réversibles et observables se livrent souvent et cassent moins.

## Production du skill

Créer `.specs/<feature-id>/09-ship-plan.md` depuis son modèle avec :

1. le résultat PASS/FAIL des portes pré-livraison ;
2. la posture de feature flag : nom, valeur par défaut, arrêt d'urgence, responsable ;
3. la sécurité des migrations et leur procédure de retour arrière ;
4. la validation de l'observabilité : métriques, journaux, alertes, tableau de bord ;
5. le plan de retour arrière ;
6. la mise en production progressive du canari jusqu'à 100 % ;
7. les notes externes et internes de livraison.

## Portes pré-livraison

| Porte | Source de vérité | Arrêt si |
|---|---|---|
| Validation | verdict de `07-validation-report.md` | différent de `PASS` |
| Revue de code | verdict de `08-code-review.md` | différent de `Approve` ou dérogations sans ADR |
| Questions ouvertes | `## Open Questions` de la spec et de la conception | au moins une `Q-NNN` non résolue |
| Régression de référence | `_baseline.json` contre le dernier harness | nouvel échec absent de la référence |
| Périmètre du diff | `git diff origin/main...HEAD` | fichier hors des `files_in_scope` |

À la première porte en échec, **s'arrêter**, indiquer la commande de reprise
`$build`, `$test`, `$validate` ou `$review`, et ne pas écrire de plan partiel.

## Feature flags

Pour tout nouveau chemin d'exécution :

- flag requis si le changement est risqué, irréversible ou sur un chemin critique ;
- désactivé par défaut en production jusqu'au succès du canari ;
- interrupteur documenté via variable d'environnement ou configuration distante ;
- responsable humain nommé, jamais « l'équipe ».

Consigner aussi l'absence de flag avec sa justification.

## Sécurité des migrations

Détecter l'outil avec `flyway-or-liquibase-detection` et classer chaque script :

| Classe | Définition | Action |
|---|---|---|
| **Forward-only safe** | colonne nullable, table, index ou vue ajouté | continuer |
| **Expand step** | écrit ancien + nouveau, lit ancien | continuer et créer le ticket de contract |
| **Contract step** | lit nouveau, supprime ancien | vérifier qu'expand a vécu la durée convenue en production |
| **Breaking** | suppression, renommage ou rétrécissement | arrêter sans ADR, flag et retour arrière |

Ne jamais modifier un script déjà livré. Annuler le commit ne suffit pas après
une migration : préciser le SQL ou l'étape de contrat qui restaure le schéma.

## Validation de l'observabilité

Pour chaque endpoint, handler ou tâche de fond :

- métrique `MeterRegistry` stable et de faible cardinalité ;
- journal structuré à la frontière avec feature-id et AC-NNN ;
- alerte, ou justification explicite de son absence ;
- lien vers le tableau de bord ;
- histogramme des temps de réponse HTTP via Micrometer.

S'il manque un élément, arrêter et recommander `$build` ou `$test`.

## Plan de retour arrière

Répondre par écrit à trois questions :

1. Comment détecter la panne, avec alerte et seuil ?
2. Comment limiter les dégâts en moins de cinq minutes ?
3. Comment restaurer l'état, y compris après migration ?

« Nous verrons à ce moment-là » bloque le plan.

## Déploiement progressif

Forme par défaut, modifiable seulement par ADR :

```text
canari, ~1 % → 10 % → 50 % → 100 %
      30 min     1 h     4 h     régime permanent
```

Pour chaque étape, consigner les critères d'entrée, d'abandon et la personne qui
surveille. Avec un flag sans impact de schéma, faire progresser la cohorte selon la même forme.

## Notes de livraison

- **Externes** : une à trois puces en français simple, sans jargon interne.
- **Internes** : résumé du diff, AC-NNN, ADR, classe de migration, flag et tableau de bord.

Les générer depuis `git log origin/main..HEAD`, `## Goal` et les titres de tâches.
L'utilisateur relit les notes externes avant publication.

## Signaux bloquants

- Migration d'une version précédente renommée ou modifiée.
- Valeur par défaut d'un flag déjà déployé modifiée sans ADR.
- Nouvel endpoint sans métrique ni alerte.
- Retour arrière limité à « annuler le commit » malgré une migration.
- Notes externes non relues par une personne.
- `Q-NNN` encore ouverte.

## Processus dans `$ship`

1. Vérifier les portes et s'arrêter au premier FAIL avec une commande de reprise.
2. Inspecter le diff, classer les migrations, endpoints et métriques.
3. Remplir chaque section du modèle ; `n/a` exige une justification d'une ligne.
4. Demander les décisions humaines manquantes sans les inventer.
5. Afficher la commande de déploiement proposée, sans jamais l'exécuter.

## Vérification

- [ ] Les sept sections sont remplies sans placeholder.
- [ ] Chaque porte vaut `PASS`.
- [ ] Chaque migration est classée avec un retour arrière nommé.
- [ ] Chaque endpoint possède métrique et alerte, ou justification.
- [ ] Les notes externes et internes existent.
- [ ] L'utilisateur a confirmé responsable du flag, seuils d'alerte et cohortes.
