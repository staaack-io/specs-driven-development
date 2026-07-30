# Rendering Strategies

Next.js App Router routes use Server Components by default. Choose rendering and
caching from data requirements, not from a blanket application-wide mode.

- Prerender static content when all required data is build-time safe.
- Render dynamically when the response depends on request-time data.
- Stream uncached or slow sections behind `loading.tsx` or `<Suspense>`.
- Add Client Components only for interactivity and browser APIs.
- Use explicit cache directives and invalidation only when freshness
  requirements are known.

Do not mark an entire page `"use client"` merely because one control is
interactive. Isolate the control and pass serializable props from the server.

Official references:
[Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components),
[Fetching data](https://nextjs.org/docs/app/getting-started/fetching-data), and
[Linking and navigating](https://nextjs.org/docs/app/getting-started/linking-and-navigating).
