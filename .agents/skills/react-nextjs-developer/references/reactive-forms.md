# Formulaires client contrôlés

Utiliser un Client Component contrôlé si l'interface nécessite un comportement
immédiat entre champs avant soumission. Garder le modèle explicite et revalider côté serveur.

```tsx
'use client';

import {useState} from 'react';

export function ProfileForm() {
  const [name, setName] = useState('');

  return (
    <form>
      <label htmlFor="name">Name</label>
      <input
        id="name"
        name="name"
        value={name}
        onChange={(event) => setName(event.target.value)}
      />
    </form>
  );
}
```

- Utiliser `useState` pour quelques champs indépendants.
- Utiliser `useReducer` pour rendre explicites les transitions de nombreux champs liés.
- Ne pas mélanger contrôle et non-contrôle pour la même entrée.
- Garder les valeurs comme chaînes pendant l'édition et parser nombres et dates à une frontière de validation.
- Relier les erreurs avec `aria-describedby` et annoncer correctement l'état de soumission.

Préférer un formulaire natif avec Server Action lorsque le contrôle client n'ajoute aucune valeur observable.

Référence officielle :
[React input](https://react.dev/reference/react-dom/components/input).
