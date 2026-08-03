# Contrat d'exécution isolée d'un job SDD

T-011 matérialise uniquement un job déjà admis par le Kanban Hermes. Il ne
sélectionne aucune tâche et ne possède aucun ordonnanceur.

## Surfaces isolées

La clé `<feature-id>:<task-id>` détermine une branche
`sdd/<feature-id>/<task-id>-<slug>`, un worktree natif sous `.worktrees/`, une
session Hermes, une issue enfant liée au parent et une pull request brouillon.
Le bridge GitHub S-002 reste l'autorité de création et d'enregistrement des
identifiants externes.

Chaque adaptateur applique une opération idempotente `ensure`. Une reprise avec
la même clé réutilise les surfaces existantes. Une ressource divergente est
refusée au lieu d'être remplacée.

## Échec et journal

Une erreur conserve branche, worktree, session, issue, pull request, journaux et
logs déjà produits. Aucun nettoyage automatique n'est disponible. Le journal ne
reçoit que le type de l'erreur et des identifiants techniques bornés ; le message
brut, les secrets, tokens, données personnelles, chemins absolus et contenu
métier ne sont jamais transmis.

## Sécurité Git

L'API ne fournit aucune opération de force-push, reset destructif, suppression
de branche ou worktree, ni fusion de pull request. Ces transitions restent hors
du périmètre du worker.
