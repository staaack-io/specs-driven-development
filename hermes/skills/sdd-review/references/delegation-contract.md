# Contrat de délégation `/sdd-review`

Le routeur choisit `spring-code-reviewer`, `react-nextjs-code-reviewer` ou les
deux d'après les fichiers du diff. Chaque rôle reçoit seulement les chemins
modifiés et les artefacts SDD requis en lecture seule.

La requête ne contient aucun handle, callback, writer ou chemin cible vers
`08-code-review.md`. Les rôles retournent des constats structurés avec stack,
sévérité, fichier, ligne, preuve et correction. Le garde principal vérifie que
les delegates n'ont produit aucun changement avant le fan-in.

Seul le garde principal déduplique les résultats, expurge les preuves et écrit
le rapport partagé. Aucune demande de reviewer humain, écriture Git, fusion,
opération VPS ou action de déploiement n'est déléguée.
