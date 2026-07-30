# Formulaires avec Server Actions

Utiliser les formulaires natifs et Server Actions lorsque la soumission appartient
au serveur. Une Server Action reçoit `FormData`, authentifie, autorise, valide et
renvoie les erreurs attendues comme données.

```ts
'use server';

export type FormState = {
  errors?: {
    email?: string[];
  };
  message?: string;
};

export async function createAccount(
  _previousState: FormState,
  formData: FormData,
): Promise<FormState> {
  const email = formData.get('email');
  if (typeof email !== 'string' || !email.includes('@')) {
    return {errors: {email: ['Enter a valid email address']}};
  }

  await saveAccount({email});
  return {message: 'Account created'};
}
```

Utiliser `useActionState` dans le plus petit Client Component qui a besoin de l'attente et de l'état retourné :

```tsx
'use client';

import {useActionState} from 'react';
import {createAccount, type FormState} from './actions';

const initialState: FormState = {};

export function AccountForm() {
  const [state, formAction, pending] = useActionState(
    createAccount,
    initialState,
  );

  return (
    <form action={formAction}>
      <label htmlFor="email">Email</label>
      <input
        id="email"
        name="email"
        type="email"
        required
        aria-describedby={state.errors?.email ? 'email-error' : undefined}
      />
      {state.errors?.email && (
        <p id="email-error" role="alert">
          {state.errors.email.join(', ')}
        </p>
      )}
      <button disabled={pending}>
        {pending ? 'Creating…' : 'Create account'}
      </button>
      {state.message && <p aria-live="polite">{state.message}</p>}
    </form>
  );
}
```

Utiliser `useFormStatus` uniquement dans un composant rendu à l'intérieur du
formulaire observé. Utiliser `useOptimistic` seulement si erreur et retour arrière sont définis.

Ne jamais considérer la validation native client comme frontière serveur.
Revalider données, permissions et préconditions dans l'action. Ne pas ajouter de
bibliothèque de formulaires sans usage existant ou accord utilisateur.

Référence officielle :
[Forms with Server Actions](https://nextjs.org/docs/app/guides/forms).
