# Props

Les props transportent les données du parent vers l'enfant. Définir un type
TypeScript précis et ne déstructurer que ce dont le composant a besoin.

```tsx
type ProductCardProps = {
  product: {
    id: string;
    name: string;
  };
  featured?: boolean;
};

export function ProductCard({product, featured = false}: ProductCardProps) {
  return <article data-featured={featured}>{product.name}</article>;
}
```

- Traiter les props comme immuables.
- Garder obligatoires les props requises ; ne rendre optionnelle qu'une absence valide.
- Transmettre des valeurs sérialisables du serveur au client.
- Préférer la composition avec `children` à de nombreux booléens de configuration.
- Ne pas copier les props dans l'état sauf divergence volontaire de l'utilisateur.

Référence officielle :
[Passing props to a component](https://react.dev/learn/passing-props-to-a-component).
