# Contrat de politique du pilote VPS

`vps_pilot_policy.py` valide uniquement des données structurées en mémoire et
retourne un tuple ordonné de codes de violation. Il ne se connecte à aucun
système, n'exécute aucune commande et ne persiste aucune preuve.

## Entrée

La racine contient les sections `evidence`, `hermes`, `delegation`, `sandbox`,
`gateway` et `retention`. Une section ou une valeur de sécurité absente est
refusée ; aucune valeur par défaut permissive n'est appliquée.

## Invariants

- Les preuves excluent secret, token, credential, transcript et chemin absolu.
- Une invocation Hermes non interactive utilise un shell de connexion ou le
  binaire distant `/home/ubuntu/.local/bin/hermes`, cible un board explicite et
  interdit `--yolo`.
- `delegation.max_spawn_depth` vaut exactement `1` et
  `subagent_auto_approve` vaut `false`.
- Une demande d'installation du gateway attend deux jobs sandbox parallèles
  réussis. Le gateway reste utilisateur et n'utilise jamais `sudo`.
- Tant que les preuves ne sont pas complètes, carte, branche, worktree, logs et
  journal restent conservés.

## Frontière de sécurité

Le module n'importe et n'appelle aucune primitive de processus, shell, SSH ou
réseau. Son résultat est une décision locale ; il ne constitue jamais une
autorisation d'accès VPS, de gateway, de pilote, de fusion ou de publication.
