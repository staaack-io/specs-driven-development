# Next.js CLI

Utiliser le gestionnaire de paquets et les scripts déjà choisis par le dépôt.

Créer une application avec le CLI officiel :

```bash
npx create-next-app@latest <app-name> --ts --eslint --app --turbopack --yes
```

Les commandes courantes du framework sont généralement exposées comme scripts du package :

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }
}
```

- `next dev` démarre le mode développement.
- `next build` crée un build de production.
- `next start` sert un build de production terminé.
- `next typegen` génère les types liés aux routes sans build complet si la version installée le prend en charge.

Exécuter le lint et les tests via les scripts configurés par le projet. Ne pas
supposer que `next lint` existe ni démarrer de serveur persistant sauf nécessité.

Références officielles :
[create-next-app](https://nextjs.org/docs/app/api-reference/cli/create-next-app) and
[Next.js CLI](https://nextjs.org/docs/app/api-reference/cli/next).
