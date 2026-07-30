# Navigation Motion

Treat route motion as progressive enhancement. First provide immediate,
accessible navigation feedback with `loading.tsx`, Suspense, or `useLinkStatus`.

Use CSS transitions for stable elements in shared layouts. Do not depend on an
undocumented router lifecycle or delay navigation to complete an animation.

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

Use the browser View Transitions API only when the project's browser support and
fallback behavior are explicitly defined. Keep the route usable without motion.

Official reference:
[Linking and navigating](https://nextjs.org/docs/app/getting-started/linking-and-navigating).
