# Code Loading and Prefetching

The App Router splits code by route. Use its file conventions before adding
manual lazy loading.

- Use `<Link>` for framework navigation and built-in prefetching.
- Add `loading.tsx` to dynamic routes that need immediate feedback and
  streaming.
- Use `next/dynamic` for a large Client Component only when deferring that
  component has a measured benefit.
- Use `prefetch={false}` only when avoiding prefetch work is an explicit
  requirement.

Do not dynamically import Server Components to force client behavior. Keep the
Server/Client boundary explicit and measure bundle changes before claiming an
optimization.

Official reference:
[Linking and navigating](https://nextjs.org/docs/app/getting-started/linking-and-navigating).
