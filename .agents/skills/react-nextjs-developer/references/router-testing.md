# Tests App Router

Tester le comportement observable de navigation, pas l'intérieur de Next.js.

- Tester un Client Component utilisant `useRouter` seulement si le dépôt possède déjà un mock stable.
- Rendre les liens et vérifier leur nom accessible et leur destination.
- Utiliser Playwright pour redirections, routes dynamiques, chargement, not-found et frontières serveur/client.
- Retester l'autorisation au point d'entrée serveur ; une redirection navigateur ne suffit pas.

```ts
await page.goto('/products/42');
await expect(page.getByRole('heading', {name: 'Product 42'})).toBeVisible();
await page.getByRole('link', {name: 'Edit'}).click();
await expect(page).toHaveURL('/products/42/edit');
```

Éviter de mocker tout le router lorsqu'un test navigateur est plus simple et représentatif.

Référence officielle :
[Next.js testing guides](https://nextjs.org/docs/app/guides/testing).
