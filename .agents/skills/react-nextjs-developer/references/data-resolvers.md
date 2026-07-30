# Données de route

Avec App Router, charger les données dans la page, le layout ou un Server
Component asynchrone imbriqué. Dans les versions récentes, `params` et
`searchParams` sont asynchrones ; suivre les types générés par la version installée.

```tsx
import {notFound} from 'next/navigation';

export default async function Page({
  params,
}: {
  params: Promise<{id: string}>;
}) {
  const {id} = await params;
  const user = await getUser(id);
  if (!user) {
    notFound();
  }
  return <UserProfile user={user} />;
}
```

Utiliser `loading.tsx` pour le chargement, `not-found.tsx` avec `notFound()` pour
une ressource absente et `error.tsx` pour les exceptions inattendues. Représenter
les erreurs attendues comme valeurs de retour ou états d'interface.

Références officielles :
[Fetching data](https://nextjs.org/docs/app/getting-started/fetching-data) and
[Error handling](https://nextjs.org/docs/app/getting-started/error-handling).
