# Tests de bout en bout

Utiliser Playwright lorsqu'il est configuré par le projet. Garder les specs dans
l'emplacement e2e existant et utiliser le script du dépôt.

```ts
import {expect, test} from '@playwright/test';

test('opens a product', async ({page}) => {
  await page.goto('/products');
  await page.getByRole('link', {name: 'Product 42'}).click();
  await expect(page).toHaveURL('/products/42');
  await expect(
    page.getByRole('heading', {name: 'Product 42'}),
  ).toBeVisible();
});
```

- Préférer les locators par rôle, libellé et texte.
- Initialiser ou isoler les données de façon déterministe.
- Attendre un état observable de l'interface ou du réseau, jamais un délai fixe.
- Couvrir Server Actions, redirections, chargement, frontières d'erreur et parcours clavier critiques dans le navigateur.
- Capturer trace, capture ou vidéo uniquement selon la configuration existante.

Référence officielle :
[Playwright with Next.js](https://nextjs.org/docs/app/guides/testing/playwright).
