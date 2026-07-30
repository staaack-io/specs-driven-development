# Reusable Application Modules

React and Next.js do not require service classes. Put reusable behavior in the
smallest module matching its runtime:

- server-only data access in `lib/` modules imported by Server Components,
  Server Actions, or Route Handlers;
- pure domain functions in framework-independent TypeScript modules;
- reusable client behavior in custom hooks;
- shared subtree state behind an explicit Context provider.

```ts
import 'server-only';

export async function getProduct(id: string): Promise<Product> {
  const response = await fetch('https://api.example.com/products/' + id);
  if (!response.ok) {
    throw new Error('Unable to load product');
  }
  return response.json();
}
```

Do not put secrets in Client Components. Do not create a class or singleton
without a lifecycle or interface that requires one. Inject external effects as
function parameters in domain code when that improves testing.

Official reference:
[Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components).
