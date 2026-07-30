# Callback Props

Use callback props for child-to-parent communication. Name callbacks for the
event the parent handles.

```tsx
type QuantityPickerProps = {
  value: number;
  onValueChange: (value: number) => void;
};

export function QuantityPicker({value, onValueChange}: QuantityPickerProps) {
  return (
    <button type="button" onClick={() => onValueChange(value + 1)}>
      Add one
    </button>
  );
}
```

- Use native events for native controls.
- Pass domain values rather than leaking implementation-specific DOM details.
- Do not create state in both parent and child for the same source of truth.
- For server mutations, prefer a form action or Server Action over threading a
  client callback through a Server Component boundary.

Official reference:
[Responding to events](https://react.dev/learn/responding-to-events).
