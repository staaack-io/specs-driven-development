# Effets

Utiliser `useEffect` uniquement pour synchroniser un Client Component avec un
système externe : API navigateur, abonnement, timer, analytics ou widget non React.

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

Ne pas utiliser un effet pour :

- dériver des données de rendu ;
- traiter un événement utilisateur ;
- synchroniser deux états React ;
- charger des données qui appartiennent à un Server Component.

Inclure chaque dépendance réactive et nettoyer symétriquement ce qui a été
initialisé. Les effets ne s'exécutent pas dans les Server Components.

Référence officielle :
[Synchronizing with effects](https://react.dev/learn/synchronizing-with-effects).
