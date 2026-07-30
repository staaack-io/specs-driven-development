# React State Overview

Use the smallest state primitive that matches the behavior:

- `useState` for independent local state.
- `useReducer` for related transitions with explicit actions.
- Context for values needed by a distant subtree.
- URL state for shareable navigation and filter state.
- Server Components for server-owned data.

Derive values during render instead of storing duplicate state:

```tsx
const visibleItems = items.filter((item) => item.active);
```

State is a snapshot. Use functional updates when the next value depends on the
previous one:

```tsx
setCount((count) => count + 1);
```

Do not mutate arrays or objects held in state. Replace them with new values.
Avoid global state packages unless the existing project already chose one or the
user explicitly approves a dependency.

Official references:
[Managing state](https://react.dev/learn/managing-state) and
[Built-in hooks](https://react.dev/reference/react/hooks).
