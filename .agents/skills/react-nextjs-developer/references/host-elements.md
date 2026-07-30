# Éléments DOM et refs

Les composants React ne créent pas d'élément hôte implicite. Retourner l'élément
DOM sémantique possédé et transmettre volontairement les props DOM prises en charge.

```tsx
import type {ComponentPropsWithoutRef} from 'react';

type ButtonProps = ComponentPropsWithoutRef<'button'> & {
  tone?: 'primary' | 'quiet';
};

export function Button({tone = 'primary', className, ...props}: ButtonProps) {
  return <button data-tone={tone} className={className} {...props} />;
}
```

Utiliser les refs uniquement pour les interactions impératives : focus, mesure ou
API non React. Ne pas les employer comme deuxième stockage d'état.

Appliquer ARIA à l'élément réellement interactif. Préserver les handlers du
consommateur lors de la composition des props, sans les écraser silencieusement.

Référence officielle :
[Manipulating the DOM with refs](https://react.dev/learn/manipulating-the-dom-with-refs).
