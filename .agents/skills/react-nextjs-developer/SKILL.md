---
name: react-nextjs-developer
description: Generate and review React and Next.js App Router code. Use for React components, Server and Client Components, routing, data fetching, Server Actions, forms, accessibility, styling, testing, performance, or Next.js CLI work.
---

# React and Next.js Developer

Inspect `package.json`, the lockfile, `next.config.*`, `tsconfig.json`, the app
directory, and existing scripts before proposing code. Preserve the installed
React and Next.js versions, package manager, directory layout, linter, styling
strategy, and test tools. Do not add a dependency without explicit approval.

Use the App Router when the project already uses it or for a new application.
Keep pages and layouts as Server Components by default. Add `"use client"` only
at the smallest boundary that needs state, effects, event handlers, custom hooks,
or browser APIs. Keep secrets, authorization, and trusted data access on the
server.

Run the repository's own lint, typecheck, test, build, and e2e scripts after
changes. Inspect scripts rather than inventing command names. A production build
must pass before declaring framework code complete.

## References

Read only the references relevant to the task:

- Components and composition: [components.md](references/components.md),
  [inputs.md](references/inputs.md), [outputs.md](references/outputs.md), and
  [host-elements.md](references/host-elements.md).
- State and effects: [signals-overview.md](references/signals-overview.md),
  [linked-signal.md](references/linked-signal.md), and
  [effects.md](references/effects.md).
- Forms: [signal-forms.md](references/signal-forms.md),
  [reactive-forms.md](references/reactive-forms.md), and
  [template-driven-forms.md](references/template-driven-forms.md).
- Context and reusable modules:
  [di-fundamentals.md](references/di-fundamentals.md),
  [creating-services.md](references/creating-services.md),
  [defining-providers.md](references/defining-providers.md),
  [injection-context.md](references/injection-context.md), and
  [hierarchical-injectors.md](references/hierarchical-injectors.md).
- Routing and rendering: [define-routes.md](references/define-routes.md),
  [loading-strategies.md](references/loading-strategies.md),
  [show-routes-with-outlets.md](references/show-routes-with-outlets.md),
  [navigate-to-routes.md](references/navigate-to-routes.md),
  [route-guards.md](references/route-guards.md),
  [data-resolvers.md](references/data-resolvers.md),
  [router-lifecycle.md](references/router-lifecycle.md),
  [rendering-strategies.md](references/rendering-strategies.md), and
  [route-animations.md](references/route-animations.md).
- Data fetching: [resource.md](references/resource.md).
- Styling, motion, and accessibility:
  [component-styling.md](references/component-styling.md),
  [react-ui-motion.md](references/react-ui-motion.md), and
  [react-accessibility.md](references/react-accessibility.md).
- Testing: [testing-fundamentals.md](references/testing-fundamentals.md),
  [component-harnesses.md](references/component-harnesses.md),
  [router-testing.md](references/router-testing.md), and
  [e2e-testing.md](references/e2e-testing.md).
- Tooling: [cli.md](references/cli.md) and [mcp.md](references/mcp.md).

Use official [React](https://react.dev/reference/react) and
[Next.js App Router](https://nextjs.org/docs/app) documentation when a
version-sensitive detail is not covered locally.
