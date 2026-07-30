# DOM Elements and Refs

React components do not create an implicit host element. Return the semantic DOM
element the component owns and forward supported DOM props deliberately.

```tsx
import type {ComponentPropsWithoutRef} from 'react';

type ButtonProps = ComponentPropsWithoutRef<'button'> & {
  tone?: 'primary' | 'quiet';
};

export function Button({tone = 'primary', className, ...props}: ButtonProps) {
  return <button data-tone={tone} className={className} {...props} />;
}
```

Use refs only for imperative browser interactions such as focus, measurement, or
integration with a non-React API. Do not use refs as a second state store.

Apply ARIA attributes to the actual interactive element. Preserve consumer
handlers when composing props; do not silently overwrite them.

Official reference:
[Manipulating the DOM with refs](https://react.dev/learn/manipulating-the-dom-with-refs).
