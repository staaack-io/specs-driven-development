# Formulaires natifs non contrôlés

Utiliser des contrôles natifs non contrôlés pour les formulaires simples. Donner
un `name` à chaque contrôle soumis et lire `FormData` dans l'action ou le handler.

```tsx
export function SearchForm() {
  return (
    <form action="/search">
      <label htmlFor="query">Search</label>
      <input id="query" name="query" type="search" required />
      <button type="submit">Search</button>
    </form>
  );
}
```

Utiliser `defaultValue` ou `defaultChecked` pour l'initialisation. Ne pas basculer ensuite la même entrée en mode contrôlé.

Préférer les attributs de validation natifs pour un retour immédiat, mais répéter
toute validation côté serveur. Utiliser libellés sémantiques, fieldsets, legends
et erreurs décrites. Éviter la lecture impérative du DOM si `FormData` suffit.

Références officielles :
[React form](https://react.dev/reference/react-dom/components/form) and
[Next.js forms](https://nextjs.org/docs/app/guides/forms).
