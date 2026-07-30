# Styling Components

Preserve the project's existing styling system. Next.js supports global CSS and
locally scoped CSS Modules without an additional runtime dependency.

```tsx
import styles from './product-card.module.css';

export function ProductCard({name}: {name: string}) {
  return <article className={styles.card}>{name}</article>;
}
```

```css
.card {
  display: grid;
  gap: 1rem;
}
```

- Import global CSS only from the location supported by the current project.
- Use CSS Modules for component-local rules.
- Use `className` and `style` with React's DOM property conventions.
- Keep focus indicators visible and encode state with data or ARIA attributes.
- Do not add Tailwind, CSS-in-JS, Sass, or another styling dependency unless it
  is already selected or the user approves it.

Official reference:
[CSS](https://nextjs.org/docs/app/getting-started/css).
