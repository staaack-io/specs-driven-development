# Context Boundaries

`useContext` is a React Hook. Call it only at the top level of a function
component or custom hook, never conditionally or inside an event handler.

Context is resolved from the closest matching provider above the consumer in the
render tree. A provider returned by the same component cannot affect a context
read made earlier in that component.

In Next.js, React context is a client-side capability. Put the provider in a
Client Component and render it from a Server Component layout. Pass serializable
initial values across that boundary.

Do not use Context as a hidden service locator. Expose a focused custom hook that
validates provider presence and gives consumers a typed API.

Official references:
[useContext](https://react.dev/reference/react/useContext) and
[Context providers in Next.js](https://nextjs.org/docs/app/getting-started/server-and-client-components#context-providers).
