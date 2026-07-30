# Controlled Client Forms

Use a controlled Client Component when the UI needs immediate cross-field
behavior before submission. Keep the form model explicit and validate again on
the server.

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

- Use `useState` for a few independent fields.
- Use `useReducer` when transitions across many related fields must be explicit.
- Do not mix controlled and uncontrolled ownership for the same input.
- Keep values as strings while the browser edits them; parse domain numbers and
  dates at a validation boundary.
- Associate errors with controls using `aria-describedby` and announce
  submission status appropriately.

Prefer the native form + Server Action pattern when client ownership adds no
observable value.

Official reference:
[React input](https://react.dev/reference/react-dom/components/input).
