# Forms with Server Actions

Use native forms and Server Actions when submission belongs on the server. A
Server Action receives `FormData` and must authenticate, authorize, validate,
and return expected errors as data.

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

Use `useActionState` in the smallest Client Component that needs pending and
returned state:

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

Use `useFormStatus` only inside a component rendered within the form whose
submission it observes. Use `useOptimistic` only when rollback and error
behavior are defined.

Never trust native client validation as the server boundary. Revalidate data,
permissions, and mutation preconditions in the action. Do not add a form library
unless the project already uses it or the user approves it.

Official reference:
[Forms with Server Actions](https://nextjs.org/docs/app/guides/forms).
