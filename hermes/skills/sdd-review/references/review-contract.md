# Contrat du rapport de revue

`08-code-review.md` contient les entrées, les rubriques appliquées, les constats
dédupliqués, les dérogations documentées et un verdict. Les seules valeurs du
verdict sont `approve` et `request-changes`.

Le verdict est informatif et non bloquant : il ne devient jamais une porte de
commit, push, pull request ou fusion. Les sévérités des constats sont limitées à
`must-fix`, `should-fix`, `nit` et `praise`.

Le rapport est l'unique sortie durable et son writer effectue un remplacement
atomique sous le verrou global canonique. Avant publication, les secrets,
chemins absolus, données personnelles et données métier inutiles sont expurgés.
Un lien symbolique ou une sortie hors de la feature est refusé.
