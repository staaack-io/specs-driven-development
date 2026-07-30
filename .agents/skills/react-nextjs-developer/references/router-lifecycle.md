# État de navigation

App Router n'expose pas l'ancienne API d'événements. Composer les hooks de l'URL
dans un petit Client Component lorsque les analytics ou l'interface doivent réagir après navigation :

```tsx
'use client';

import {useEffect} from 'react';
import {usePathname, useSearchParams} from 'next/navigation';

export function NavigationAnalytics() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    recordPageView(pathname, searchParams.toString());
  }, [pathname, searchParams]);

  return null;
}
```

Utiliser `loading.tsx`, Suspense et `useLinkStatus` pour l'attente. Ne pas recréer
un bus global pour un chargement ordinaire. Isoler les effets analytics et exclure les valeurs sensibles.

Référence officielle :
[useRouter](https://nextjs.org/docs/app/api-reference/functions/use-router).
