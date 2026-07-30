# App Router Testing

Test observable navigation behavior, not Next.js internals.

- Use a component test for a Client Component that calls `useRouter` only when
  the repository already has a stable navigation mock.
- Render links and assert their accessible name and destination.
- Use Playwright for redirects, dynamic routes, loading states, not-found
  behavior, and interactions across Server and Client Component boundaries.
- Test authorization again at the server entry point; a redirect-only browser
  test is not sufficient proof.

```ts
await page.goto('/products/42');
await expect(page.getByRole('heading', {name: 'Product 42'})).toBeVisible();
await page.getByRole('link', {name: 'Edit'}).click();
await expect(page).toHaveURL('/products/42/edit');
```

Avoid mocking the whole router when a browser-level test is cheaper and more
representative.

Official reference:
[Next.js testing guides](https://nextjs.org/docs/app/guides/testing).
