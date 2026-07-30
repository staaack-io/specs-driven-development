# Autorisation des routes

Une redirection client n'est pas une autorisation. Imposer authentification et
autorisation à chaque accès serveur, Server Action et Route Handler.

```tsx
import {redirect} from 'next/navigation';

export default async function AdminPage() {
  const session = await verifySession();
  if (!session) {
    redirect('/login');
  }
  if (!session.permissions.includes('admin:read')) {
    return <p>Access denied</p>;
  }
  return <AdminDashboard />;
}
```

Centraliser l'accès sécurisé dans des fonctions serveur, mais contrôler chaque
point d'entrée public. Traiter les Route Handlers comme des API publiques.

Utiliser l'interception uniquement pour un routage grossier ou contrôle optimiste,
jamais comme seule frontière. Ne pas exposer secrets ou logique fiable au client.

Référence officielle :
[Authentication](https://nextjs.org/docs/app/guides/authentication).
