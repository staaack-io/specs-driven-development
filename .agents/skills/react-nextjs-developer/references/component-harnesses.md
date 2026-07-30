# Interaction avec les composants centrée utilisateur

Utiliser les helpers React Testing Library du dépôt comme surface d'interaction.
Les requêtes doivent refléter la manière dont une personne ou une technologie
d'assistance trouve le contrôle.

Ordre préféré :

1. `getByRole` avec un nom accessible.
2. `getByLabelText` pour les contrôles de formulaire.
3. `getByText` pour le contenu visible.
4. `getByTestId` seulement sans sélecteur sémantique.

Créer un petit helper réutilisable uniquement lorsque plusieurs tests répètent un
parcours utilisateur significatif. Ne pas envelopper chaque composant dans un
harness personnalisé ni exposer son état privé.

```ts
const saveButton = screen.getByRole('button', {name: 'Save'});
await user.click(saveButton);
expect(await screen.findByText('Saved')).toBeVisible();
```

Si le projet utilise une bibliothèque de composants, suivre son approche de test
sans coupler les assertions aux classes CSS générées ni à la profondeur du DOM.

Référence officielle :
[Next.js testing guides](https://nextjs.org/docs/app/guides/testing).
