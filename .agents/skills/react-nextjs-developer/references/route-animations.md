# Mouvement de navigation

Traiter le mouvement comme amélioration progressive. Fournir d'abord un retour
immédiat et accessible via `loading.tsx`, Suspense ou `useLinkStatus`.

Utiliser des transitions CSS pour les éléments stables des layouts. Ne pas
dépendre d'un cycle de route non documenté ni retarder la navigation pour une animation.

```css
.navigation-indicator {
  opacity: 0;
  transition: opacity 150ms ease;
}

.navigation-indicator[data-pending='true'] {
  opacity: 1;
}

@media (prefers-reduced-motion: reduce) {
  .navigation-indicator {
    transition: none;
  }
}
```

Utiliser View Transitions uniquement si le support navigateur et le fallback sont
définis. Garder la route utilisable sans mouvement.

Référence officielle :
[Linking and navigating](https://nextjs.org/docs/app/getting-started/linking-and-navigating).
