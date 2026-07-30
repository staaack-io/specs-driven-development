# Route Authorization

Client-side redirects are not authorization. Enforce authentication and
authorization at every server-side data access, Server Action, and Route Handler.

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

Centralize secure data access in server-only functions, but call the check from
each public entry point. Treat Route Handlers like public API endpoints.

Use a request interception layer only for coarse routing or optimistic checks;
do not rely on it as the sole authorization boundary. Never expose secrets or
trusted permission logic to a Client Component.

Official reference:
[Authentication](https://nextjs.org/docs/app/guides/authentication).
