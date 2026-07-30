# Porte de décision humaine

Un contrôle technique réussi ne constitue jamais une approbation. La décision
finale suit obligatoirement deux temps séparés par une réponse utilisateur.

## Premier temps : rapport provisoire

Lors d'une première revue, ou d'une nouvelle revue avec `--continue` :

1. écrire le rapport complet avec `verdict: ready-for-approval` ;
2. écrire `en attente` pour le reviewer, la date, la prochaine commande, la
   décision, la preuve explicite et son mode ;
3. exécuter :

   ```bash
   python3 <skill-dir>/scripts/review_decision_guard.py validate-provisional \
     --report .specs/<feature-id>/02-spec-review.md
   ```

4. conserver le token retourné, présenter le résumé et demander une réponse
   exacte `approve` ou `request-changes` ;
5. arrêter le tour. Ne pas finaliser le rapport dans la même réponse.

Même avec zéro échec et zéro question, l'invocation de `/sdd-spec-review` ne
vaut pas décision. Il en va de même pour le silence, `continue`, `go`, une
approbation donnée avant le rapport provisoire ou une valeur déduite du contexte.

## Second temps : décision explicite

Deux preuves sont acceptées :

- `direct-response` : le message suivant de l'utilisateur vaut exactement
  `approve` ou `request-changes`, sans tenir compte de la casse ou des espaces ;
- `decision-option` : sur un rapport déjà provisoire, l'utilisateur lance
  `/sdd-spec-review --continue <feature-id> --decision approve` ou la variante
  `request-changes`.

`--continue` sans `--decision` relance une revue provisoire et ne finalise rien.
`--decision` est refusé si aucun rapport provisoire valide ne préexiste.

Après la preuve explicite, capturer à nouveau le token du rapport avec
`validate-provisional`, puis exécuter le garde sans modifier le rapport à la
main :

```bash
python3 <skill-dir>/scripts/review_decision_guard.py finalize \
  --report .specs/<feature-id>/02-spec-review.md \
  --expected-token <sha256:...> \
  --decision approve \
  --evidence approve \
  --evidence-mode direct-response \
  --reviewer utilisateur \
  --decision-at <ISO-8601> \
  --next-command "/sdd-plan <feature-id>"
```

`<skill-dir>` désigne le dossier absolu contenant le présent skill ; ne pas
interpréter ce chemin relativement au projet utilisateur.

Le garde exige que la preuve normalisée soit exactement la décision, refuse une
commande complète comme preuve, vérifie l'absence de question avant `approve`,
sérialise les finalisations avec `.spec-review.lock`, détecte une modification
concurrente et remplace le rapport atomiquement. Le nom `utilisateur` est
seulement une valeur de repli après cette validation.

Après succès, exécuter `validate-final`. Si un contrôle échoue, conserver le
rapport provisoire, ne proposer aucune étape suivante et montrer l'erreur.
