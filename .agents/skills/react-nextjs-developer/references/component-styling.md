# Styles des composants

Conserver le système de styles existant. Next.js prend en charge le CSS global et
les CSS Modules locaux sans dépendance d'exécution supplémentaire.

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

- Importer le CSS global uniquement depuis l'emplacement prévu par le projet.
- Utiliser les CSS Modules pour les règles locales au composant.
- Utiliser `className` et `style` selon les conventions DOM de React.
- Garder les indicateurs de focus visibles et encoder l'état via data ou ARIA.
- Ne pas ajouter Tailwind, CSS-in-JS, Sass ou autre dépendance sans choix existant ou accord utilisateur.

Référence officielle :
[CSS](https://nextjs.org/docs/app/getting-started/css).
