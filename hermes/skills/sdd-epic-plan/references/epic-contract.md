# Contrat des artefacts Epic

## Identifiants

- Conserver les `Q-NNN`, `CR-NNN` et `S-NNN` dont l'objet ne change pas.
- Qualifier les IDs locaux par rôle avant de les renuméroter globalement.
- Refuser tout doublon local ou global.
- Attribuer les nouveaux `S-NNN` au-dessus du `high_water_mark` ; ne jamais
  réutiliser un ID présent dans `retired_ids`.
- Utiliser des jalons `M-NNN` stables sans leur attribuer un comportement absent
  de la spécification.

Pour les questions de deux rôles, construire d'abord les clés d'origine
`spring-architect:Q-NNN` et `react-nextjs-architect:Q-NNN`. Refuser un doublon
dans une même sortie, fusionner les questions strictement identiques en
conservant toutes leurs origines, puis attribuer un `Q-NNN` global au-dessus du
plus grand ID déjà présent. Consigner l'origine avec la question et préserver
ce mapping pendant chaque reprise.

## Tranches

Décrire un résultat visible ou vérifiable de bout en bout. Éviter les tranches
« backend complet », « frontend complet » ou « base de données » sans résultat
utilisateur autonome. Associer chaque tranche à au moins un AC existant.

Lister les dépendances avec des `S-NNN` existants. Vérifier le graphe acyclique
et conserver un ordre topologique dans le backlog. Une dépendance full-stack
doit découler d'un contrat ou d'une exigence approuvée.

## Couverture

- Reprendre exactement tous les `AC-NNN` de `01-spec.md`.
- Couvrir chaque AC dans au moins une tranche.
- Faire correspondre la matrice `AC Coverage` au backlog.
- Refuser un AC inconnu, manquant ou déclaré couvert par une tranche absente.

## Reprise

Lire le candidat avant le final. Conserver le registre, les décisions, les
questions résolues et les demandes de changement. Lorsqu'une tranche disparaît,
placer son ID dans `retired_ids` au lieu de le réattribuer.

Ne jamais détailler les tâches `T-NNN` au niveau Epic. Le plan détaillé d'une
tranche reste la responsabilité de `/sdd-plan` après approbation.
