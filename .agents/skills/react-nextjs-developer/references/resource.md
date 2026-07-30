# Chargement et diffusion des données

Charger par défaut les données serveur dans un Server Component asynchrone :

```tsx
export default async function Page() {
  const response = await fetch('https://api.example.com/products');
  if (!response.ok) {
    throw new Error('Unable to load products');
  }
  const products: Product[] = await response.json();
  return <ProductList products={products} />;
}
```

Lire le comportement actuel dans la version installée et sa documentation. Ne pas
supposer qu'une requête est cachée. Ajouter `"use cache"`, durée et invalidation
uniquement si l'exigence produit définit la fraîcheur.

Utiliser `loading.tsx` ou `<Suspense>` avec un fallback utile. Charger côté client
seulement si l'interaction l'exige et réutiliser la bibliothèque déjà configurée.

Traiter explicitement les réponses en échec et garder les identifiants côté serveur.

Référence officielle :
[Fetching data](https://nextjs.org/docs/app/getting-started/fetching-data).
