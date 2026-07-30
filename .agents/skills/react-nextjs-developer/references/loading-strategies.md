# Chargement du code et prefetch

App Router découpe le code par route. Utiliser ses conventions de fichiers avant d'ajouter un chargement différé manuel.

- Utiliser `<Link>` pour la navigation et le prefetch intégré.
- Ajouter `loading.tsx` aux routes dynamiques qui nécessitent un retour immédiat et du streaming.
- Utiliser `next/dynamic` pour un grand Client Component seulement si le bénéfice est mesuré.
- Utiliser `prefetch={false}` uniquement si l'absence de prefetch est une exigence explicite.

Ne pas importer dynamiquement un Server Component pour forcer un comportement
client. Garder la frontière explicite et mesurer le bundle avant d'affirmer une optimisation.

Référence officielle :
[Linking and navigating](https://nextjs.org/docs/app/getting-started/linking-and-navigating).
