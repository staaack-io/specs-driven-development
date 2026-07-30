# Framework Documentation Tools

Do not assume that Next.js or React provides a project-local MCP server. This
framework has no required React/Next.js MCP integration.

For version-sensitive framework behavior:

1. Inspect `package.json` and the lockfile.
2. Read the matching official Next.js or React documentation.
3. Use the repository's existing Codex MCP configuration only when the project
   explicitly supplies one.
4. Do not create an MCP configuration or install a documentation package merely
   to complete ordinary framework work.

Primary references:

- [Next.js documentation](https://nextjs.org/docs)
- [React documentation](https://react.dev/reference/react)
