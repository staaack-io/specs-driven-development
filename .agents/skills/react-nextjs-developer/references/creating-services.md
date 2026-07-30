# Modules applicatifs réutilisables

React et Next.js n'exigent pas de classes de service. Placer le comportement
réutilisable dans le plus petit module adapté à son environnement :

- accès aux données serveur dans `lib/`, importé par Server Components, Server Actions ou Route Handlers ;
- fonctions métier pures dans des modules TypeScript indépendants du framework ;
- comportement client réutilisable dans des hooks personnalisés ;
- état partagé d'un sous-arbre derrière un provider Context explicite.

```ts
import 'server-only';

export async function getProduct(id: string): Promise<Product> {
  const response = await fetch('https://api.example.com/products/' + id);
  if (!response.ok) {
    throw new Error('Unable to load product');
  }
  return response.json();
}
```

Ne pas placer de secrets dans les Client Components ni créer de classe ou
singleton sans cycle de vie qui l'exige. Injecter les effets externes comme
paramètres de fonctions métier lorsque cela améliore les tests.

Référence officielle :
[Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components).
