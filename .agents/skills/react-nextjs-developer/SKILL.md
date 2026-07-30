---
name: react-nextjs-developer
description: Générer et relire du code React et Next.js App Router. Utiliser pour les composants Server et Client, le routage, les données, Server Actions, formulaires, accessibilité, styles, tests, performance ou le CLI Next.js.
---

# Développement React et Next.js

Inspecter `package.json`, le lockfile, `next.config.*`, `tsconfig.json`, le dossier
de l'application et les scripts existants avant de proposer du code. Conserver les
versions installées de React et Next.js, le gestionnaire de paquets, la structure
des dossiers, le linter, la stratégie de styles et l'outillage de test. Ne pas
ajouter de dépendance sans accord explicite.

Utiliser App Router si le projet l'utilise déjà ou pour une nouvelle application.
Garder les pages et layouts comme Server Components par défaut. Ajouter
`"use client"` uniquement à la plus petite frontière qui nécessite état, effets,
gestionnaires d'événements, hooks personnalisés ou API du navigateur. Garder les
secrets, l'autorisation et l'accès de confiance aux données côté serveur.

Après les modifications, exécuter les scripts propres au dépôt pour le lint, le
typage, les tests, le build et l'e2e. Inspecter les scripts au lieu d'inventer
leurs noms. Un build de production doit réussir avant de déclarer le code terminé.

## Références

Lire uniquement les références utiles à la tâche :

- Composants et composition : [components.md](references/components.md),
  [inputs.md](references/inputs.md), [outputs.md](references/outputs.md) et
  [host-elements.md](references/host-elements.md).
- État et effets : [signals-overview.md](references/signals-overview.md),
  [linked-signal.md](references/linked-signal.md) et [effects.md](references/effects.md).
- Formulaires : [signal-forms.md](references/signal-forms.md),
  [reactive-forms.md](references/reactive-forms.md) et
  [template-driven-forms.md](references/template-driven-forms.md).
- Contexte et modules réutilisables : [di-fundamentals.md](references/di-fundamentals.md),
  [creating-services.md](references/creating-services.md),
  [defining-providers.md](references/defining-providers.md),
  [injection-context.md](references/injection-context.md) et
  [hierarchical-injectors.md](references/hierarchical-injectors.md).
- Routage et rendu : [define-routes.md](references/define-routes.md),
  [loading-strategies.md](references/loading-strategies.md),
  [show-routes-with-outlets.md](references/show-routes-with-outlets.md),
  [navigate-to-routes.md](references/navigate-to-routes.md),
  [route-guards.md](references/route-guards.md),
  [data-resolvers.md](references/data-resolvers.md),
  [router-lifecycle.md](references/router-lifecycle.md),
  [rendering-strategies.md](references/rendering-strategies.md) et
  [route-animations.md](references/route-animations.md).
- Chargement des données : [resource.md](references/resource.md).
- Styles, mouvement et accessibilité :
  [component-styling.md](references/component-styling.md),
  [react-ui-motion.md](references/react-ui-motion.md) et
  [react-accessibility.md](references/react-accessibility.md).
- Tests : [testing-fundamentals.md](references/testing-fundamentals.md),
  [component-harnesses.md](references/component-harnesses.md),
  [router-testing.md](references/router-testing.md) et [e2e-testing.md](references/e2e-testing.md).
- Outillage : [cli.md](references/cli.md) et [mcp.md](references/mcp.md).

Utiliser la documentation officielle de
[React](https://react.dev/reference/react) et de
[Next.js App Router](https://nextjs.org/docs/app) lorsqu'un détail dépendant de la
version n'est pas couvert localement.
