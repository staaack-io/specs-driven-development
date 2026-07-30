# Nested Providers

React resolves Context from the nearest provider above a consumer. A nested
provider can intentionally override a value for one subtree.

```tsx
<ThemeContext value="light">
  <Header />
  <ThemeContext value="dark">
    <Editor />
  </ThemeContext>
</ThemeContext>
```

Use nested providers only when the scope is meaningful and visible in the
component tree. Avoid provider stacks that hide unrelated global state.

In Next.js, keep Client providers below the root `<html>` and `<body>` when
possible so static Server Component content remains optimizable. Never store
request-specific authentication or secrets in a shared client provider.

Official reference:
[Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components#context-providers).
