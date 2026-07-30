# App Router Routes

The Next.js App Router derives routes from folders under `app/` or `src/app/`.

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

- `page.tsx` exposes a route.
- `layout.tsx` wraps descendant segments and preserves shared UI.
- `[id]` is a dynamic segment; `[...slug]` is catch-all.
- Route groups such as `(shop)` organize files without changing the URL.
- `route.ts` defines a Route Handler with Web `Request` and `Response` APIs.

Do not create a parallel Pages Router configuration for an App Router feature.
Avoid a `route.ts` and `page.tsx` at the same segment level.

Official references:
[Project structure](https://nextjs.org/docs/app/getting-started/project-structure) and
[Route Handlers](https://nextjs.org/docs/app/getting-started/route-handlers).
