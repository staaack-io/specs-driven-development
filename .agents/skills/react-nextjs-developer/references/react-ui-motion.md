# React UI Motion

Prefer native CSS transitions and keyframes for enter, exit, hover, focus, and
state changes. Toggle a class or data attribute from React state.

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

Respect `prefers-reduced-motion`. Use the Web Animations API through a ref only
when CSS cannot express the interaction. Do not add a motion library without
explicit approval, and do not animate layout in a way that blocks input or
causes avoidable layout shifts.

Official reference:
[React DOM components](https://react.dev/reference/react-dom/components).
