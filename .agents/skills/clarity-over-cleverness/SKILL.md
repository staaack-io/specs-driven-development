---
name: clarity-over-cleverness
description: Réécrire en privilégiant la clarté à l’astuce, pour qu’un ingénieur junior comprenne le code immédiatement. Utiliser pendant la simplification de `$build` et avec `$code-simplify`. Ne jamais affaiblir le comportement ; la suite doit rester verte.
when_to_use:
  - Phase 4, Build — étape simplify de `$build <task-id>`.
  - À la demande — `$code-simplify` ou demande de rendre le code plus simple et lisible.
  - Pendant la revue — signaler le code trop astucieux en `minor` avec une réécriture proposée.
authoritative_references:
  - .agents/skills/spring-code-review-rubric/SKILL.md
---

# La clarté plutôt que l'astuce

## Règle pratique

Si un ingénieur compétent qui découvre le code a besoin de plus de cinq secondes
pour comprendre une ligne, elle mérite une réécriture. L'objectif n'est pas moins
de caractères, mais moins de surprises.

## Cibles, dans cet ordre

### 1. Défaire les ternaires imbriqués

Mauvais :

```java
return a ? (b ? x : y) : (c ? z : w);
```

Mieux :

```java
if (a) {
    return b ? x : y;
}
return c ? z : w;
```

Lorsque les formes correspondent, un `switch` explicite peut être encore plus clair.

### 2. Utiliser les streams seulement s'ils sont plus lisibles qu'une boucle

Une boucle explicite avec des noms métier est préférable à une chaîne de
collecteurs difficile à lire. Si l'équipe emploie les streams de façon cohérente,
respecter sa convention : le but est la lisibilité, pas l'interdiction.

### 3. Intégrer les helpers à usage unique

Si une méthode privée n'a qu'un appelant et que son nom n'ajoute aucune
information, intégrer son contenu. À l'inverse, extraire une phase reconnaissable
d'une longue méthode avec un nom métier.

### 4. Supprimer les options qui n'ont qu'une valeur utilisée

Ne pas conserver des booléens ou modes que tous les appelants passent toujours
de la même façon. Réintroduire la dimension lorsqu'un deuxième besoin réel existe.

### 5. Employer les noms du domaine

Remplacer `processX`, `handleData` ou `doWork` par `redeemGiftCard`,
`priceWithDiscount` ou `rejectIfExpired`, à partir du glossaire de `01-spec.md`.

### 6. Supprimer l'abstraction prématurée

- Une interface avec une implémentation et un appelant, sans frontière de test : utiliser la classe concrète.
- Un paramètre générique utilisé par un seul type : utiliser ce type.
- Un builder pour deux champs : utiliser un constructeur ou un record.

### 7. Préférer les retours anticipés aux `if` imbriqués

```java
if (x == null) return defaultValue;
if (!x.valid()) return defaultValue;
return x.value();
```

### 8. Supprimer le code inutilisé

Le minimum de code qui passe le test est la bonne quantité. Une méthode sans
appelant réel est du poids mort. Un test tautologique qui vérifie seulement qu'une
méthode renvoie une constante n'est **pas** un consommateur réel ; tester à une
frontière réelle, comme un contrôleur, un cycle JPA, une tâche planifiée ou un listener.

Les points d'entrée appelés indirectement par le framework, comme les contrôleurs,
`@PrePersist`, `@PostLoad`, tâches planifiées et `@EventListener`, sont des
consommateurs légitimes.

### 9. Extraire les littéraux répétés

Toute chaîne ou valeur numérique qui apparaît **au moins deux fois** dans un même
fichier devient une constante `private static final` au nom métier, placée en tête
de classe. Cette règle vaut pour le code de production et les tests.

```java
private static final String ENDPOINT_PATH = "/api/gift-cards";
private static final int MAX_PAGE_SIZE = 100;
```

## Ce que ce skill ne fait jamais

- Changer le comportement ; la suite reste verte après chaque réécriture.
- Réduire la couverture ou supprimer un test sans vérifier que l'AC reste couvert.
- Modifier des fichiers hors des `Files in scope`.
- Renommer une API publique entre modules ; cela exige une tâche de refactorisation.

## Processus pendant simplify

1. Relire le diff de la tâche.
2. Pour chaque fonction modifiée, vérifier qu'un junior la comprend en cinq secondes.
3. Appliquer les réécritures une par une et exécuter les tests entre chacune.
4. Ajouter un bloc `simplify` au journal avec les changements significatifs.

## Invocation « simplifier le code »

Traiter la demande comme `$code-simplify` sur le fichier ouvert ou les derniers
fichiers de la fonctionnalité active. Garder la suite verte, résumer le diff et ne
pas commiter automatiquement.
