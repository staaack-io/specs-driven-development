# Accessibilité React

Préférer le HTML sémantique avant ARIA. Utiliser les contrôles natifs lorsqu'ils
correspondent au comportement. En JSX, les attributs `aria-*` gardent leurs tirets.

Pour un pattern interactif personnalisé :

1. Suivre le pattern WAI-ARIA Authoring Practices correspondant.
2. Implémenter ensemble clavier, focus, rôles, états et propriétés.
3. Garder le nom accessible stable et relier libellés, descriptions et erreurs par ID.
4. Tester rôles, noms, clavier, focus et au moins un parcours navigateur.

Ne pas remplacer un contrôle natif par ARIA uniquement pour le style ni ajouter
de package headless sans accord. Si le projet en utilise un, préserver sa composition et son clavier.

Pour les statuts dynamiques et validations, utiliser une live region adaptée et ne déplacer le focus que si nécessaire.

Références officielles :
[React DOM components](https://react.dev/reference/react-dom/components) and
[WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/patterns/).
