# Composants React et Next.js

Utiliser des composants fonctions. Avec App Router, les pages et layouts sont des Server Components par défaut.

```tsx
type ProfileProps = {
  name: string;
};

export function Profile({name}: ProfileProps) {
  return <h2>{name}</h2>;
}
```

Utiliser un Client Component uniquement s'il requiert état, effets, gestionnaires d'événements, hooks personnalisés ou API navigateur :

```tsx
'use client';

import {useState} from 'react';

export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount((value) => value + 1)}>{count}</button>;
}
```

Garder les frontières `"use client"` petites. Les props transmises du serveur au
client doivent être sérialisables. Utiliser des clés métier stables plutôt que
les index et extraire les branches JSX complexes dans des composants nommés.

Références officielles :
[React components](https://react.dev/reference/react/components) and
[Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components).
