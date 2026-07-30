# Derived and Resettable State

Do not mirror props or server data in local state by default. Compute pure
derived values during render.

```tsx
const selected = options.find((option) => option.id === selectedId) ?? options[0];
```

When state must reset because an entity changes, model identity explicitly. A
`key` can reset a subtree:

```tsx
<Editor key={documentId} documentId={documentId} />
```

When a user's selection may survive new options, store only the stable selected
ID and derive the selected object. Validate the ID during the event or data
transition that changes the options; do not use an effect merely to synchronize
two state variables.

Official reference:
[Choosing the state structure](https://react.dev/learn/choosing-the-state-structure).
