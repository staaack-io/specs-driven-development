# Mouvement dans l'interface React

Préférer transitions et keyframes CSS natives pour entrée, sortie, survol, focus
et changement d'état. Basculer une classe ou un attribut data depuis l'état React.

```tsx
export function Disclosure({open}: {open: boolean}) {
  return (
    <section data-open={open} className="disclosure">
      Content
    </section>
  );
}
```

```css
.disclosure {
  opacity: 0;
  transform: translateY(0.5rem);
  transition: opacity 150ms ease, transform 150ms ease;
}

.disclosure[data-open='true'] {
  opacity: 1;
  transform: translateY(0);
}
```

Respecter `prefers-reduced-motion`. Utiliser Web Animations via une ref seulement
si CSS ne suffit pas. Ne pas ajouter de bibliothèque sans accord ni animer le layout
d'une manière qui bloque l'entrée ou cause des décalages évitables.

Référence officielle :
[React DOM components](https://react.dev/reference/react-dom/components).
