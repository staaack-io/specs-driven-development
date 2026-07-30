---
name: openapi-contract-first
description: Workflow OpenAPI contract-first pour rédiger ou actualiser le contrat, exécuter le diff, régénérer les types et écrire le contrôleur. Utiliser lors de l’ajout ou de la modification d’un endpoint HTTP.
when_to_use:
  - Phase 3, Plan — esquisser le delta OpenAPI dans `03-design.md`.
  - Phase 4, Build — générer les types et écrire le contrôleur.
  - Phase 6, Validate — exécuter `openapi-diff` et lire le rapport.
authoritative_references:
  - https://springdoc.org/
  - https://github.com/OpenAPITools/openapi-generator
  - https://github.com/OpenAPITools/openapi-diff
---

# OpenAPI contract-first

## Workflow

1. Modifier `src/main/resources/openapi/openapi.yaml`, ou le chemin détecté par `detect-stack.sh`.
2. Exécuter le **diff OpenAPI** avec la version précédente consignée dans `_baseline.json`.
3. Pour un changement cassant, choisir une solution compatible ou écrire un ADR `adr/NNN-breaking-api-change.md`.
4. Générer les DTO sous forme de records avec le plugin Maven `openapi-generator`.
5. Écrire le contrôleur ; le test par tranche `@WebMvcTest` consomme les records générés.

## Changements compatibles ou cassants

Compatibles, sans ADR :

- ajouter un endpoint ;
- ajouter un champ de requête **optionnel** ;
- ajouter un champ de réponse ;
- assouplir une contrainte ;
- ajouter une valeur d'enum uniquement si les consommateurs déclarent tolérer les inconnues.

Cassants, avec ADR obligatoire :

- supprimer ou renommer un champ ;
- changer un type ;
- durcir une contrainte ;
- changer un chemin ou une méthode HTTP ;
- changer le statut HTTP d'une condition existante ;
- ajouter un champ de requête obligatoire ;
- supprimer une valeur d'enum.

## Contrôle springdoc

Si springdoc est présent, exécuter aussi un contrôle **runtime contre statique** :
démarrer l'application, récupérer `/v3/api-docs` et le comparer à `openapi.yaml`.
Les deux doivent correspondre. Le hook associé est `openapi-runtime-vs-static`.

## Indications de génération

Configurer `openapi-generator` avec :

- `generatorName: spring` ;
- `library: spring-boot` ;
- `useSpringBoot3: true`, compatible Boot 4 au moment de la rédaction ;
- `interfaceOnly: true`, car le générateur ne produit que l'interface et les DTO ;
- `useTags: true` ;
- `dateLibrary: java8`, donc `java.time` ;
- `useJakartaEe: true` ;
- `serializationLibrary: jackson` et le flag `useRecord` lorsqu'il est pris en charge.

## Exemple

```yaml
paths:
  /checkout/{orderId}/gift-card:
    post:
      operationId: applyGiftCard
      tags: [Checkout]
      parameters:
        - name: orderId
          in: path
          required: true
          schema: { type: string, format: uuid }
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/ApplyGiftCardRequest' }
      responses:
        '200': { description: Applied }
        '404': { $ref: '#/components/responses/NotFound' }
        '409': { $ref: '#/components/responses/Conflict' }
```

## Anti-patterns

- Écrire manuellement des DTO qui divergent de la spécification.
- Utiliser `application/x-www-form-urlencoded` pour de nouvelles API.
- Définir `additionalProperties: true` sur les réponses et perdre le typage client.
- Renvoyer 200 pour une erreur avec le statut dans le corps.
- Utiliser un immense `OpenAPI.yaml` sans tags ni regroupement.
