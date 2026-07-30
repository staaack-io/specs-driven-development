# Effects

Use `useEffect` only to synchronize a Client Component with an external system:
browser APIs, subscriptions, timers, analytics, or non-React widgets.

```tsx
'use client';

import {useEffect} from 'react';

export function OnlineStatusLogger() {
  useEffect(() => {
    const log = () => console.info(navigator.onLine);
    window.addEventListener('online', log);
    window.addEventListener('offline', log);
    return () => {
      window.removeEventListener('online', log);
      window.removeEventListener('offline', log);
    };
  }, []);

  return null;
}
```

Do not use an effect to:

- derive render data;
- handle a user event;
- keep two React state values synchronized;
- fetch data that belongs in a Server Component.

Include every reactive dependency and implement cleanup that mirrors setup.
Effects do not run in Server Components.

Official reference:
[Synchronizing with effects](https://react.dev/learn/synchronizing-with-effects).
