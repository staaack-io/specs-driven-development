# Composition and Dependencies

Prefer ordinary module imports and function parameters over a dependency
injection container.

- Import stable framework and domain functions directly.
- Pass replaceable effects through function parameters at domain boundaries.
- Use React Context for runtime values needed by a component subtree.
- Keep request-specific data on the server and never in a process-wide mutable
  singleton.

```ts
type SaveOrder = (order: Order) => Promise<void>;

export function createCheckout(saveOrder: SaveOrder) {
  return async (order: Order) => {
    validateOrder(order);
    await saveOrder(order);
  };
}
```

Do not introduce a DI library unless the user approves the dependency and the
existing architecture requires it.

Official reference:
[Passing data deeply with context](https://react.dev/learn/passing-data-deeply-with-context).
