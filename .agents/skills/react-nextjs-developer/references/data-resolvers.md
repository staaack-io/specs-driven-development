# Route Data

In the App Router, load route data in the page, layout, or a nested async Server
Component. Dynamic route `params` and `searchParams` are asynchronous in current
Next.js versions; follow the installed version's generated types.

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

Use `loading.tsx` for route loading UI, `not-found.tsx` with `notFound()` for a
missing resource, and `error.tsx` for unexpected exceptions. Model expected
errors as return values or UI states instead of throwing them.

Official references:
[Fetching data](https://nextjs.org/docs/app/getting-started/fetching-data) and
[Error handling](https://nextjs.org/docs/app/getting-started/error-handling).
