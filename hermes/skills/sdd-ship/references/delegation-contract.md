# Contrat de capacité de `/sdd-ship`

`/sdd-ship` ne délègue aucune action de livraison. Les preuves utilisées pour
préparer le plan lui sont transmises comme données structurées en lecture seule.

Le garde ne reçoit aucun runner, callback d'exécution, client réseau, credential,
handle VPS ou handle de déploiement. Le seul handle d'écriture autorisé cible
`.specs/<feature-id>/09-ship-plan.md` via le writer atomique canonique.

Une commande de pipeline, `kubectl` ou Maven peut figurer dans le document sous
forme de texte expurgé. Elle n'est transmise à aucun interpréteur et n'est jamais
exécutée par le skill.
