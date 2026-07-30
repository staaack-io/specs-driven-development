# User-Centric Component Interaction

Use the repository's React Testing Library helpers as the component interaction
surface. Queries should resemble how a user or assistive technology finds the
control.

Preferred order:

1. `getByRole` with an accessible name.
2. `getByLabelText` for form controls.
3. `getByText` for visible content.
4. `getByTestId` only when no semantic selector exists.

Create a small reusable test helper only when multiple tests repeat a meaningful
user workflow. Do not wrap every component in a custom harness or expose private
component state.

```ts
const saveButton = screen.getByRole('button', {name: 'Save'});
await user.click(saveButton);
expect(await screen.findByText('Saved')).toBeVisible();
```

If the project uses a component library, prefer its supported testing approach
without coupling assertions to generated CSS classes or DOM depth.

Official reference:
[Next.js testing guides](https://nextjs.org/docs/app/guides/testing).
