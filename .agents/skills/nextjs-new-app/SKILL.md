---
name: nextjs-new-app
description: Create a new React application with the official Next.js create-next-app CLI. Use when the user asks to scaffold a new Next.js App Router project.
---

# Create a Next.js App

1. Confirm Node.js is available and identify the requested package manager,
   application name, Next.js version, linter, styling choice, `src/` layout, and
   import alias. Ask instead of silently choosing a material option.
2. Use the official `create-next-app` package. If the user requested a version,
   invoke that exact package version; otherwise use the installed or latest
   stable CLI without pinning a framework version in generated code.
3. Pass non-interactive flags matching the resolved choices. For example:

   `bash
   npx create-next-app@latest <app-name> --ts --eslint --app --turbopack --yes
   `

   Add `--src-dir`, `--tailwind`, `--no-tailwind`, or a package-manager flag only
   when it matches the user's decision or established workspace convention.
4. Inspect the generated `package.json`, `app/` or `src/app/`, `next.config.*`,
   `tsconfig.json`, and linter configuration. Do not add libraries or replace the
   generated tooling without approval.
5. Use App Router file conventions to add pages, layouts, route handlers, and
   components. Next.js has no general component generator; create only the files
   required by the requested feature.
6. Run the generated lint and build scripts. Do not start a long-running
   development server unless the user asks.

Official reference:
[create-next-app](https://nextjs.org/docs/app/api-reference/cli/create-next-app).
