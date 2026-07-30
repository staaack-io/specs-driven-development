# Providers de contexte

Utiliser un provider Context pour les valeurs dynamiques partagées dans un
sous-arbre, comme le thème client. Placer le provider aussi bas que possible.

```tsx
'use client';

import {createContext, useContext, useState} from 'react';

type Theme = 'light' | 'dark';
const ThemeContext = createContext<Theme | null>(null);

export function ThemeProvider({children}: {children: React.ReactNode}) {
  const [theme] = useState<Theme>('light');
  return <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const theme = useContext(ThemeContext);
  if (theme === null) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return theme;
}
```

Ne pas utiliser Context pour des données que le Server Component peut lire
directement. Garder les valeurs stables et séparer les contextes sans lien pour
éviter des rerenders inutiles.

Référence officielle :
[Scaling up with reducer and context](https://react.dev/learn/scaling-up-with-reducer-and-context).
