# Runbook local S-008 avant pilote VPS

Ce document est une porte de lecture locale. Il matérialise les preuves
T-032-T1 à T-032-T7 sans exécuter d'opération externe. Le contrat associé
prouve les 57/57 critères de S-008 et la partition 286/286 de l'Epic.

## Résultat de l'audit local

- T-030 et T-031 sont les deux seuls writers locaux parallèles ; leurs scopes
  sont littéraux, relatifs au dépôt et disjoints.
- T-032 est leur fan-in local unique et ne fait que lire les artefacts
  versionnés.
- T-033 à T-038 restent `pending` et `external-blocked`, dans cet ordre
  strictement séquentiel.
- Le validateur de politique et le dry-run sont inertes : ils n'ouvrent aucune
  connexion et n'exécutent aucune commande.

## Barrière avant toute mise à jour VPS

T-033 reste inadmissible tant que toutes les preuves suivantes ne sont pas
présentes simultanément : profil 0.9.0 fusionnée, version 0.9.0 publiée,
gate verte et go explicite. Une PR ouverte, une CI verte ou une demande
générale de poursuite ne satisfait aucune de ces conditions.

Les credentials requis constituent une précondition externe supplémentaire.
Ils ne sont jamais écrits dans l'état, le journal ou les documents versionnés.

## Séquence externe bloquée

Après admission explicite seulement, la séquence prévue est T-033 → T-034 →
T-035 → T-036 → T-037 → T-038. Chaque tâche attend la réussite prouvée de la
précédente. La publication 1.0.0 exige en plus la réussite du pilote et un go de
publication distinct.

## Frontière de sécurité de T-032

Cet audit local ne sollicite aucun reviewer humain et ne réalise aucune fusion,
aucun SSH, aucun gateway et aucun déploiement. Il ne met pas à jour le VPS, ne
publie aucune version et ne déduit aucune autorisation d'une preuve technique.

En cas d'écart, conserver cartes, branches, worktrees, logs, journaux et preuves.
Le retour arrière prévu reste le profil 0.9.0 ; aucune donnée de travail n'est
supprimée par cet audit.
