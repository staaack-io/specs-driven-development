---
name: nextjs-new-app
description: Créer une application React avec le CLI officiel create-next-app de Next.js. Utiliser lorsque l’utilisateur demande de générer un nouveau projet App Router.
---

# Créer une application Next.js

1. Confirmer que Node.js est disponible et identifier le gestionnaire de paquets,
   le nom de l'application, la version de Next.js, le linter, le choix de styles,
   l'utilisation de `src/` et l'alias d'import demandés. Interroger l'utilisateur
   au lieu de choisir silencieusement une option importante.
2. Utiliser le package officiel `create-next-app`. Si l'utilisateur demande une
   version, invoquer exactement cette version ; sinon, utiliser le CLI stable
   installé ou le plus récent, sans figer une version du framework dans le code généré.
3. Passer les options non interactives correspondant aux choix résolus. Par exemple :

   ```bash
   npx create-next-app@latest <app-name> --ts --eslint --app --turbopack --yes
   ```

   Ajouter `--src-dir`, `--tailwind`, `--no-tailwind` ou une option de gestionnaire
   de paquets uniquement si cela correspond à la décision de l'utilisateur ou à
   une convention établie dans le workspace.
4. Inspecter le `package.json`, le dossier `app/` ou `src/app/`, `next.config.*`,
   `tsconfig.json` et la configuration du linter générés. Ne pas ajouter de
   bibliothèque ni remplacer l'outillage sans approbation.
5. Suivre les conventions de fichiers App Router pour les pages, layouts, Route
   Handlers et composants. Next.js n'a pas de générateur général de composants ;
   créer uniquement les fichiers requis par la fonctionnalité demandée.
6. Exécuter les scripts de lint et de build générés. Ne pas démarrer de serveur de
   développement persistant sauf demande de l'utilisateur.

Référence officielle :
[create-next-app](https://nextjs.org/docs/app/api-reference/cli/create-next-app).
