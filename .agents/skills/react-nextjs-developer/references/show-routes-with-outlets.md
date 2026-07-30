# Layouts et emplacements de route

Utiliser `layout.tsx` pour rendre l'interface partagée autour des routes descendantes :

```tsx
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <DashboardNavigation />
      <main>{children}</main>
    </>
  );
}
```

Les dossiers et layouts imbriqués remplacent les outlets. Utiliser Parallel Routes
uniquement si une URL rend des emplacements navigables indépendamment. Leurs dossiers commencent par `@`.

Ne pas introduire Parallel Routes pour une composition ordinaire. Définir un
fallback `default.tsx` si un rechargement pourrait laisser un emplacement sans correspondance.

Références officielles :
[Layouts and pages](https://nextjs.org/docs/app/getting-started/layouts-and-pages) and
[Parallel Routes](https://nextjs.org/docs/app/api-reference/file-conventions/parallel-routes).
