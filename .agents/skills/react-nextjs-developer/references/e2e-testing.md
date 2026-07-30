# End-to-End Testing

Use Playwright when it is configured by the project. Keep specs in the existing
e2e location and use the repository's package script.

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

- Prefer role, label, and text locators.
- Seed or isolate data deterministically.
- Wait for observable UI or network state, never a fixed timeout.
- Cover Server Action submissions, redirects, loading UI, error boundaries, and
  critical keyboard flows at the browser boundary.
- Capture trace, screenshot, or video only according to the existing config.

Official reference:
[Playwright with Next.js](https://nextjs.org/docs/app/guides/testing/playwright).
