# Contrat de délégation

Chaque rôle reçoit une copie minimale de son contexte et aucun handle vers les
artefacts partagés. Les rôles ne peuvent jamais écrire `04-tasks.md`,
`.tdd-state.json` ni `05-implementation-log.md`. Le coordinateur refuse toute
écriture rapportée sur ces fichiers avant de publier l'événement correspondant.
