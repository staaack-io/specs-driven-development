# Contrat de préparation de livraison

## Préconditions

Le garde refuse au premier échec :

1. le rapport de validation ne vaut pas `PASS` ;
2. la review ne vaut ni `Approve` ni `Approve with waivers` ;
3. des questions `Q-NNN` restent ouvertes ;
4. la baseline contient une nouvelle régression ;
5. le scope contient un chemin hors `files_in_scope` ;
6. le diff est vide.

Aucun fichier partiel n'est écrit lors d'un refus.

## Rollback — AC-152

Le rollback nomme la détection avec alerte et seuil, la limitation des dégâts en
moins de cinq minutes et la restauration de l'état. Un simple revert de commit
ne constitue pas une restauration suffisante.

## Absence de déploiement — AC-153 et AC-235

Le garde produit un document. Il n'importe aucune bibliothèque shell, réseau ou
VPS et n'accepte aucun callback d'exécution. La commande proposée reste une
donnée d'affichage à ligne unique, sans secret.

## observability — AC-261

Chaque surface possède une métrique, les clés de journal `feature_id` et `ac_id`,
une alerte et un dashboard. Une surface non applicable exige une justification
explicite.

## Feature flag — AC-262

La posture de feature flag précise son nom, sa valeur par défaut, son arrêt
d'urgence, son responsable et sa condition de retrait. `none` reste admis
uniquement si ces champs documentent explicitement la justification.

## Release notes — AC-263

Le plan contient une à trois release notes externes en langage simple et des
release notes internes traçant critères, diff, ADR, migrations, flag, dashboard
et commits. Les secrets et credentials sont refusés.
