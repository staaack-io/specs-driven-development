# Providers imbriqués

React résout Context depuis le provider le plus proche au-dessus du consommateur.
Un provider imbriqué peut remplacer volontairement une valeur pour un sous-arbre.

```tsx
<ThemeContext value="light">
  <Header />
  <ThemeContext value="dark">
    <Editor />
  </ThemeContext>
</ThemeContext>
```

Utiliser les providers imbriqués uniquement lorsque leur périmètre est clair dans
l'arbre. Éviter les empilements qui masquent un état global sans lien.

Dans Next.js, placer si possible les providers client sous `<html>` et `<body>`
afin que le contenu serveur statique reste optimisable. Ne jamais stocker
authentification propre à une requête ou secrets dans un provider client partagé.

Référence officielle :
[Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components#context-providers).
