# Fondamentaux des tests React et Next.js

Inspecter le runner et les scripts avant d'écrire. Réutiliser Jest ou Vitest et
React Testing Library lorsqu'ils existent. Ne pas ajouter de dépendance sans accord.

Tester le comportement via une sortie accessible :

```tsx
render(<Counter />);
await user.click(screen.getByRole('button', {name: 'Add one'}));
expect(screen.getByRole('button', {name: '1'})).toBeVisible();
```

- Rechercher par rôle, nom accessible, libellé ou texte avant `data-testid`.
- Utiliser `userEvent` pour l'interaction lorsqu'il est configuré.
- Attendre un changement observable, jamais un délai fixe.
- Mocker les frontières réseau ou framework, pas les détails internes.
- Garder les tests déterministes et vérifier le critère d'acceptation.

La recommandation Next.js est de tester les Server Components asynchrones dans le
navigateur si le runner unitaire ne les rend pas fidèlement. Utiliser Playwright
pour intégration serveur/client, routage et hydratation.

Référence officielle :
[Next.js testing guides](https://nextjs.org/docs/app/guides/testing).
