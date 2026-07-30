# Navigation

Utiliser `<Link>` pour la navigation interne déclarative :

```tsx
import Link from 'next/link';

export function ProductLink({id}: {id: string}) {
  return <Link href={'/products/' + id}>View product</Link>;
}
```

Utiliser `redirect` ou `permanentRedirect` dans Server Components, Server Actions
ou Route Handlers. Réserver `useRouter` au Client Component pour une logique purement client.

```tsx
'use client';

import {useRouter} from 'next/navigation';

export function CloseButton() {
  const router = useRouter();
  return <button onClick={() => router.back()}>Close</button>;
}
```

Ne jamais passer une URL non fiable à `router.push` ou `router.replace`. Utiliser
`usePathname` et `useSearchParams` uniquement côté client et préférer l'URL pour
les filtres et paginations partageables.

Référence officielle :
[Linking and navigating](https://nextjs.org/docs/app/getting-started/linking-and-navigating).
