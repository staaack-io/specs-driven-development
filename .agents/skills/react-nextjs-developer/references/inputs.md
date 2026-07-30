# Props

Props carry data from a parent to a child. Define a specific TypeScript type and
destructure only what the component needs.

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

- Treat props as immutable.
- Keep required props required; use optional props only when absence is valid.
- Pass serializable values across a Server-to-Client boundary.
- Prefer composition with `children` over many boolean configuration props.
- Do not copy props into state unless the user can intentionally diverge from
  the latest prop value.

Official reference:
[Passing props to a component](https://react.dev/learn/passing-props-to-a-component).
