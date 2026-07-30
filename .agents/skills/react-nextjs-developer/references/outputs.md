# Props de callback

Utiliser des props de callback pour communiquer de l'enfant au parent. Nommer le callback d'après l'événement traité.

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

- Utiliser les événements natifs des contrôles natifs.
- Transmettre des valeurs métier plutôt que des détails DOM.
- Ne pas créer le même état dans le parent et l'enfant.
- Pour une mutation serveur, préférer une action de formulaire ou Server Action à un callback traversant la frontière serveur.

Référence officielle :
[Responding to events](https://react.dev/learn/responding-to-events).
