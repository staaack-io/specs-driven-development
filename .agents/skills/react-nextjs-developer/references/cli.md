# Next.js CLI

Use the package manager and scripts already selected by the repository.

Create an application with the official CLI:

```bash
npx create-next-app@latest <app-name> --ts --eslint --app --turbopack --yes
```

Common framework commands are normally exposed as package scripts:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }
}
```

- `next dev` starts development mode.
- `next build` creates a production build.
- `next start` serves a completed production build.
- `next typegen` generates route-aware types without a full build when supported
  by the installed Next.js version.

Run lint and tests through the project's configured linter and test scripts.
Do not assume `next lint` exists. Do not start a long-running server unless the
task requires it.

Official references:
[create-next-app](https://nextjs.org/docs/app/api-reference/cli/create-next-app) and
[Next.js CLI](https://nextjs.org/docs/app/api-reference/cli/next).
