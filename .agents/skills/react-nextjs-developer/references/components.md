# React and Next.js Components

Use function components. In the Next.js App Router, pages and layouts are Server
Components by default.

```tsx
type ProfileProps = {
  name: string;
};

export function Profile({name}: ProfileProps) {
  return <h2>{name}</h2>;
}
```

Use a Client Component only when it needs state, effects, event handlers, custom
hooks, or browser APIs:

```tsx
'use client';

import {useState} from 'react';

export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount((value) => value + 1)}>{count}</button>;
}
```

Keep `"use client"` boundaries small. Props passed from Server Components to
Client Components must be serializable. Render lists with stable domain keys,
not array indexes when item identity can change. Prefer explicit conditional JSX
and extract complex branches into named components.

Official references:
[React components](https://react.dev/reference/react/components) and
[Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components).
