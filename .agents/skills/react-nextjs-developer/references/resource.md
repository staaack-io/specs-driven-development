# Data Fetching and Streaming

Fetch server-owned data in an async Server Component by default:

```tsx
export default async function Page() {
  const response = await fetch('https://api.example.com/products');
  if (!response.ok) {
    throw new Error('Unable to load products');
  }
  const products: Product[] = await response.json();
  return <ProductList products={products} />;
}
```

Current Next.js behavior must be read from the installed version and official
docs. Do not assume a request is cached. Add `"use cache"`, cache lifetime, or
invalidation only when the product requirement defines the freshness behavior.

Use `loading.tsx` or `<Suspense>` to stream meaningful fallback UI. Fetch in a
Client Component only when the interaction truly requires client ownership; use
the project's existing client data library if one is already configured.

Handle non-success responses explicitly and keep credentials on the server.

Official reference:
[Fetching data](https://nextjs.org/docs/app/getting-started/fetching-data).
