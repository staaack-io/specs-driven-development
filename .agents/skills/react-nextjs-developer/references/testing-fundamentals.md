# React and Next.js Testing Fundamentals

Inspect the configured test runner and scripts before writing tests. Use the
existing Jest or Vitest setup and React Testing Library when present. Do not add
a test dependency without approval.

Test behavior through accessible output:

```tsx
render(<Counter />);
await user.click(screen.getByRole('button', {name: 'Add one'}));
expect(screen.getByRole('button', {name: '1'})).toBeVisible();
```

- Query by role, accessible name, label, or visible text before `data-testid`.
- Use `userEvent` for user interaction when configured.
- Await observable UI changes; do not use fixed sleeps.
- Mock network or framework boundaries, not implementation details.
- Keep tests deterministic and assert the acceptance criterion.

Current Next.js guidance recommends browser-level testing for async Server
Components when the unit test tool cannot render them accurately. Use Playwright
for server/client integration, routing, and hydration behavior.

Official reference:
[Next.js testing guides](https://nextjs.org/docs/app/guides/testing).
