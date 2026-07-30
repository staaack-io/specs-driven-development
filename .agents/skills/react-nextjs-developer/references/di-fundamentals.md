# Composition et dépendances

Préférer les imports de modules et paramètres de fonctions à un conteneur d'injection.

- Importer directement les fonctions stables du framework et du domaine.
- Passer les effets remplaçables comme paramètres aux frontières métier.
- Utiliser React Context pour les valeurs d'exécution d'un sous-arbre.
- Garder les données propres à une requête côté serveur, jamais dans un singleton mutable global.

```ts
type SaveOrder = (order: Order) => Promise<void>;

export function createCheckout(saveOrder: SaveOrder) {
  return async (order: Order) => {
    validateOrder(order);
    await saveOrder(order);
  };
}
```

Ne pas introduire de bibliothèque d'injection sans accord de l'utilisateur et besoin de l'architecture existante.

Référence officielle :
[Passing data deeply with context](https://react.dev/learn/passing-data-deeply-with-context).
