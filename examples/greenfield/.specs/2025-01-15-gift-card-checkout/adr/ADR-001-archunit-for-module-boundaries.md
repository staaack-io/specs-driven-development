# ADR-001 : utiliser ArchUnit seul pour les frontières des modules

- **Statut :** accepté
- **Date :** 2025-01-15
- **Décideurs :** spring-architect, responsable technique

## Context

Le service `checkout` est structuré autour de packages de premier niveau
(`giftcard`, `order`, `shared`) qui représentent des contextes délimités. Il
faut garantir que :

1. Un module n'importe jamais le sous-package `internal` d'un autre module.
2. Il n'existe aucune dépendance cyclique entre les packages de premier niveau.
3. Les dépendances autorisées (par exemple `order` → `giftcard.api`) sont
   documentées et vérifiées lors de la construction.

## Options considered

1. **Aucun contrôle** — s'appuyer uniquement sur la revue de code. Rejeté :
   les violations s'accumulent avec le temps, surtout sous la pression des
   délais.
2. **Script de construction personnalisé** — écrire un contrôle Groovy/Bash
   qui analyse les imports. Rejeté : cela introduirait encore un DSL à maintenir.
3. **Spring Modulith** — annotations et vérificateur, avec une expérience de
   développement agréable, mais qui ajoute une dépendance d'exécution, lie la
   déclaration des modules aux fichiers package-info et recouvre les capacités
   déjà fournies par ArchUnit.
4. **ArchUnit seul** — une dépendance de test uniquement, suffisamment
   expressive pour encoder « les sous-packages internal sont privés »,
   « aucun cycle » et les dépendances explicitement autorisées.

## Decision

Adopter **l'option 4 : ArchUnit seul**. Chaque contexte délimité est un package
de premier niveau sous `com.example.checkout`. Dans chaque module, un
sous-package `internal` contient l'implémentation privée au package, tandis
qu'un sous-package `api` contient la surface publiée. La porte d'architecture
du harness (couche 4) exécute les règles suivantes dans `ArchitectureTests` :

- `giftcardInternalIsHidden` — aucune classe extérieure à
  `..giftcard.internal..` ne peut dépendre de classes qui s'y trouvent.
- `giftcardDoesNotDependOnOrder` — dépendance directionnelle uniquement.
- `noCyclesBetweenTopLevelPackages` —
  `slices().matching("com.example.checkout.(*)..").should().beFreeOfCycles()`.

Ces règles utilisent la dépendance ArchUnit déjà présente dans le POM parent.
Aucune nouvelle dépendance d'exécution n'est ajoutée.

## Consequences

- **Positif :** aucun coût à l'exécution ; une source unique pour les règles
  d'architecture ; gel d'une référence initiale possible pour l'existant ;
  règles lisibles comme de la prose.
- **Négatif :** les frontières des modules sont exprimées dans le code de test
  plutôt que dans des fichiers package-info ; chaque nouveau module exige des
  ajouts ArchUnit explicites.
- **Suivi :** encoder cet ensemble de règles dans la skill `archunit-rules`
  afin que les futures fonctionnalités utilisent les mêmes valeurs par défaut.
