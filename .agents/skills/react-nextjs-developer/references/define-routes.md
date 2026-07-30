# Routes App Router

App Router déduit les routes des dossiers sous `app/` ou `src/app/`.

```text
app/
├── layout.tsx
├── page.tsx
├── products/
│   ├── page.tsx
│   └── [id]/
│       ├── page.tsx
│       ├── loading.tsx
│       ├── error.tsx
│       └── not-found.tsx
└── api/
    └── products/
        └── route.ts
```

- `page.tsx` expose une route.
- `layout.tsx` enveloppe les segments descendants et conserve l'interface partagée.
- `[id]` est dynamique ; `[...slug]` capture la suite du chemin.
- Un groupe comme `(shop)` organise les fichiers sans changer l'URL.
- `route.ts` définit un Route Handler avec les API Web `Request` et `Response`.

Ne pas créer une configuration Pages Router parallèle pour une fonctionnalité App
Router. Éviter `route.ts` et `page.tsx` au même niveau de segment.

Références officielles :
[Project structure](https://nextjs.org/docs/app/getting-started/project-structure) and
[Route Handlers](https://nextjs.org/docs/app/getting-started/route-handlers).
