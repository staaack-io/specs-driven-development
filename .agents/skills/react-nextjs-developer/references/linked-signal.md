# État dérivé et réinitialisable

Ne pas recopier par défaut les props ou données serveur dans l'état local.
Calculer les valeurs dérivées pures pendant le rendu.

```tsx
const selected = options.find((option) => option.id === selectedId) ?? options[0];
```

Lorsque l'état doit être réinitialisé parce que l'entité change, représenter
explicitement son identité. Une `key` peut réinitialiser un sous-arbre :

```tsx
<Editor key={documentId} documentId={documentId} />
```

Si une sélection peut survivre à de nouvelles options, stocker seulement son ID
stable et dériver l'objet. Valider l'ID pendant la transition qui change les
options, sans effet destiné uniquement à synchroniser deux états.

Référence officielle :
[Choosing the state structure](https://react.dev/learn/choosing-the-state-structure).
