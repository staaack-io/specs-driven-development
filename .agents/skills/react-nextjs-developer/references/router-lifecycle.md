# Navigation State

The App Router does not expose the former router event API. Compose current URL
hooks in a small Client Component when analytics or UI state must react after
navigation:

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

Use `loading.tsx`, Suspense, and `useLinkStatus` for pending navigation feedback.
Do not recreate a global event bus for ordinary route loading. Keep analytics
effects isolated and exclude sensitive query values.

Official reference:
[useRouter](https://nextjs.org/docs/app/api-reference/functions/use-router).
