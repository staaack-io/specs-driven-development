# Context Providers

Use a Context provider for dynamic values shared by a subtree, such as a client
theme or an existing client-side store. Keep the provider as deep as possible.

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

Do not use Context for server data that can be read directly by a Server
Component. Keep provider values stable and split unrelated contexts so updates
do not rerender unrelated consumers.

Official reference:
[Scaling up with reducer and context](https://react.dev/learn/scaling-up-with-reducer-and-context).
