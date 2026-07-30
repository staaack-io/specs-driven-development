# Stratégies de rendu

Les routes App Router utilisent les Server Components par défaut. Choisir rendu
et cache depuis les besoins des données, pas depuis un mode global arbitraire.

- Prérendre le contenu statique lorsque toutes les données sont sûres au build.
- Rendre dynamiquement lorsque la réponse dépend de la requête.
- Diffuser les sections lentes derrière `loading.tsx` ou `<Suspense>`.
- Ajouter des Client Components uniquement pour interaction ou API navigateur.
- Utiliser cache et invalidation explicites seulement lorsque la fraîcheur est définie.

Ne pas marquer toute une page `"use client"` pour un seul contrôle interactif.
Isoler ce contrôle et lui passer des props sérialisables depuis le serveur.

Références officielles :
[Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components),
[Fetching data](https://nextjs.org/docs/app/getting-started/fetching-data), and
[Linking and navigating](https://nextjs.org/docs/app/getting-started/linking-and-navigating).
