# Plan de livraison : <FEATURE-ID>

> Responsable : `spring-code-reviewer` · Phase 8 · Skills : `shipping-and-launch`, `spring-security-baseline`, `flyway-or-liquibase-detection`
>
> Hygiène avant déploiement. L'agent ne déploie jamais : il produit ce plan et affiche la commande que l'utilisateur pourra exécuter.

## Inputs

- Spécification : `01-spec.md`
- Conception : `03-design.md`, ADR sous `adr/`
- Tâches : `04-tasks.md`
- Validation : `07-validation-report.md` ; le verdict doit être `PASS`
- Revue de code : `08-code-review.md` ; le verdict doit être `Approve` ou `Approve with waivers`
- Diff : <plage git, par exemple `origin/main...HEAD`>

## 1. Pre-ship gates

| Porte | Source | Résultat | Notes |
|---|---|---|---|
| Validation | `07-validation-report.md` | PASS / FAIL | <lien> |
| Revue de code | `08-code-review.md` | Approve / Approve-with-waivers / FAIL | <lien> |
| Questions ouvertes | section `## Open Questions` de la spécification et de la conception | 0 / N | <liste> |
| Régression de référence | `.specs/_baseline.json` comparé au harness | aucune / N | <liste> |
| Périmètre du diff | `files_in_scope` de chaque tâche | conforme / dérive | <fichiers hors périmètre> |

Si une ligne vaut FAIL, **s'arrêter** et ne pas remplir la suite du modèle.

## 2. Feature-flag posture

- **Nom du flag :** <nom ou `none — reason: ...`>
- **Valeur par défaut en production :** off / on
- **Interrupteur d'urgence :** <variable d'environnement ou clé de configuration distante>
- **Responsable :** <personne nommée, pas « l'équipe »>
- **Plan de retrait :** <date ou condition de suppression du flag>

Si la valeur est `none`, la justifier en une ligne, par exemple « correction purement additive couverte par l'alerte existante ».

## 3. Migration safety

| Script | Classe | Procédure de retour arrière |
|---|---|---|
| `Vxxx__name.sql` | forward-only / expand / contract / breaking | <SQL ou étape de contrat> |

Contraintes :

- [ ] Aucun script de migration déjà livré n'a été renommé ou modifié.
- [ ] Chaque script `breaking` possède un ADR.
- [ ] Pour chaque étape `contract`, l'étape `expand` correspondante est en production depuis la durée convenue.

## 4. Observability sign-off

Pour chaque nouvel endpoint, handler ou tâche planifiée :

| Surface | Métrique Micrometer | Clé de journal structuré | Alerte | Tableau de bord |
|---|---|---|---|---|
| `<METHOD> <path>` | `<metric.name>` (Timer avec histogramme) | `feature_id`, `ac_id` | <nom + seuil> | <lien> |

Si une ligne ne possède pas d'alerte, en indiquer explicitement la raison.

## 5. Rollback plan

1. **Détection.** Comment savoir que le déploiement est défectueux ? <alerte et seuil ; canal de remontée utilisateur ; anomalie de métrique>
2. **Limiter les dégâts en 5 minutes maximum.** <bascule du flag ; retour arrière ; réduction de capacité ; coupe-circuit>
3. **Restaurer l'état.** <annuler le commit ; rejouer les événements depuis l'offset N ; tâche de réconciliation ; SQL manuel>

« Annuler le commit » ne suffit pas au point 3 si une migration a été exécutée : préciser l'étape de contrat ou le SQL.

## 6. Staged rollout

| Étape | Cohorte | Critères d'entrée | Critères d'abandon | Fenêtre d'observation | Surveillant |
|---|---|---|---|---|---|
| Canary | ~1 % (1 instance) | portes vertes | taux d'erreur > X %, p95 > Y ms | 30 min | <astreinte> |
| Étape 1 | 10 % | canari sain pendant la fenêtre | identiques | 1 h | <astreinte> |
| Étape 2 | 50 % | étape 1 saine | identiques | 4 h | <astreinte> |
| Complet | 100 % | étape 2 saine | identiques | régime permanent | <astreinte> |

Pour un changement protégé par flag, la « cohorte » correspond au segment d'utilisateurs ou de tenants ciblé. Adapter le contenu du tableau sans en changer la structure.

## 7. Release notes

### Externes, pour les utilisateurs

- <point 1 en français simple>
- <point 2 en français simple>
- <point 3 facultatif>

### Internes, pour l'équipe technique

- **AC couverts :** <AC-NNN, AC-NNN, ...>
- **Résumé du diff :** <un paragraphe>
- **ADR :** <liens>
- **Classe de migration :** <forward-only / expand / contract / breaking>
- **Nom du flag :** <nom ou `none`>
- **Tableau de bord :** <lien>
- **Commits :** `git log <base>..HEAD --oneline`

## 8. Deploy command (for the user to run)

```
<commande proposée, par exemple déclenchement du pipeline de livraison, kubectl rollout ou mvn deploy>
```

L'agent ne l'exécute pas. L'utilisateur l'exécute.

## Sign-off

- [ ] Toutes les portes sont PASS.
- [ ] Le responsable du flag, les seuils d'alerte et les cohortes ont été confirmés par une personne.
- [ ] Les notes de livraison externes ont été relues par une personne.
- [ ] L'astreinte a été informée et a confirmé la fenêtre de déploiement.

Date : <YYYY-MM-DD> · Approuvé par : <nom>
