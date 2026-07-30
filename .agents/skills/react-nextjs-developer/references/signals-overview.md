# Vue d'ensemble de l'état React

Utiliser la plus petite primitive d'état adaptée :

- `useState` pour un état local indépendant.
- `useReducer` pour des transitions liées et explicites.
- Context pour un sous-arbre distant.
- URL pour une navigation ou des filtres partageables.
- Server Components pour les données possédées par le serveur.

Dériver les valeurs pendant le rendu au lieu de dupliquer l'état :

```tsx
const visibleItems = items.filter((item) => item.active);
```

L'état est un instantané. Utiliser une mise à jour fonctionnelle si la prochaine valeur dépend de la précédente :

```tsx
setCount((count) => count + 1);
```

Ne pas muter tableaux ou objets en état ; les remplacer. Éviter les packages
d'état global sauf choix existant ou approbation explicite.

Références officielles :
[Managing state](https://react.dev/learn/managing-state) and
[Built-in hooks](https://react.dev/reference/react/hooks).
