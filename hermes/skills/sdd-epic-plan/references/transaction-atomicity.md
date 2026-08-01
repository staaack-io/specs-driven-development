# Atomicité des artefacts Epic

Utiliser exclusivement `scripts/epic_plan_guard.py` pour promouvoir les deux
artefacts finaux.

## Séquence

1. Exécuter `snapshot --feature-dir <dossier>` avant toute délégation.
2. Écrire les deux fichiers `.candidate.md` sans toucher aux finaux.
3. Exécuter `validate-candidates` et demander une décision explicite.
4. Appeler `decide` avec le token du snapshot, la décision, la même preuve,
   l'acteur, le mode de preuve et un horodatage ISO-8601 avec fuseau.

Le garde verrouille `.epic-plan.lock`, compare le token des deux finaux, écrit
`.epic-plan.transaction.json`, remplace les artefacts et écrit le reçu durable
`.epic-plan.commit.json`. Le reçu constitue le marqueur de commit.

Après une interruption, `snapshot` applique une seule issue :

- sans reçu correspondant, restaurer l'ancien ensemble complet ;
- avec reçu correspondant, matérialiser le nouvel ensemble complet.

Ne jamais supprimer le verrou ni le journal à la main. Répéter le même `decide`
après un succès est idempotent. Refuser tout token, contenu ou preuve différent.

`request-changes` actualise seulement le candidat de conception par remplacement
atomique et ne crée aucun artefact final.
