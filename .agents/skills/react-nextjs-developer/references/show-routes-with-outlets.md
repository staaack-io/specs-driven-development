# Layouts and Route Slots

Use `layout.tsx` to render shared UI around descendant routes:

```tsx
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <DashboardNavigation />
      <main>{children}</main>
    </>
  );
}
```

Nested folders and layouts replace nested router outlets. Use Parallel Routes
only when one URL must render independently navigable slots. Parallel slot
folders start with `@` and are passed as named layout props.

Do not introduce Parallel Routes for ordinary component composition. Define a
`default.tsx` fallback for a slot when a hard reload could otherwise leave the
slot unmatched.

Official references:
[Layouts and pages](https://nextjs.org/docs/app/getting-started/layouts-and-pages) and
[Parallel Routes](https://nextjs.org/docs/app/api-reference/file-conventions/parallel-routes).
