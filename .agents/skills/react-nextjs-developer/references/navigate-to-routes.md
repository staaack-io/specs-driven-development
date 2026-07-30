# Navigation

Use `<Link>` for declarative internal navigation:

```tsx
import Link from 'next/link';

export function ProductLink({id}: {id: string}) {
  return <Link href={'/products/' + id}>View product</Link>;
}
```

Use `redirect` or `permanentRedirect` in Server Components, Server Actions, or
Route Handlers. Use `useRouter` in a Client Component only for navigation caused
by client-only logic.

```tsx
'use client';

import {useRouter} from 'next/navigation';

export function CloseButton() {
  const router = useRouter();
  return <button onClick={() => router.back()}>Close</button>;
}
```

Never pass an untrusted URL to `router.push` or `router.replace`. Use
`usePathname` and `useSearchParams` only in Client Components. Prefer URL search
parameters for shareable filter and pagination state.

Official reference:
[Linking and navigating](https://nextjs.org/docs/app/getting-started/linking-and-navigating).
