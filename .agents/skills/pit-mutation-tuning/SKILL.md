---
name: pit-mutation-tuning
description: Configurer et interpréter les tests de mutation PIT ciblés sur le code modifié. Utiliser pour ajouter la porte de mutation, lire `mutations.xml` ou ajuster les seuils.
when_to_use:
  - Phases 5 et 6 — exécuter `mvn -Ppit pitest:mutationCoverage` et analyser les résultats.
  - Ajouter la mutation à un projet brownfield avec un périmètre incrémental.
authoritative_references:
  - https://pitest.org/
  - https://github.com/hcoles/pitest
---

# Réglage des mutations PIT

## Pourquoi tester les mutations

La couverture prouve que le code a été exécuté. **La mutation prouve que le test
aurait détecté un vrai défaut.** Un mutant modifie légèrement le code. Un mutant
tué fait échouer un test ; un mutant survivant révèle un angle mort.

## Configuration par défaut

```xml
<plugin>
    <groupId>org.pitest</groupId>
    <artifactId>pitest-maven</artifactId>
    <version>1.17.0</version>
    <configuration>
        <targetClasses><param>com.example.shop.*</param></targetClasses>
        <targetTests><param>com.example.shop.*</param></targetTests>
        <mutators><mutator>STRONGER</mutator></mutators>
        <outputFormats><param>HTML</param><param>XML</param></outputFormats>
        <timestampedReports>false</timestampedReports>
        <features><feature>+GIT(from[HEAD~1])</feature></features>
        <mutationThreshold>80</mutationThreshold>
        <coverageThreshold>90</coverageThreshold>
    </configuration>
    <dependencies>
        <dependency>
            <groupId>org.pitest</groupId>
            <artifactId>pitest-junit5-plugin</artifactId>
            <version>1.2.1</version>
        </dependency>
    </dependencies>
</plugin>
```

## Périmètre incrémental

Les exécutions PIT complètes sont lentes. Toujours cibler le code modifié :

- localement et pendant refactor : `+GIT(from[HEAD~1])` ;
- en CI pour une PR : `+GIT(from[origin/main])` ;
- la nuit : exécution complète, informative et non bloquante.

## Traiter les mutants survivants

Pour chaque mutant survivant dans les packages modifiés :

1. examiner la ligne et le type de mutation ;
2. écrire un test qui aurait échoué sous cette mutation ;
3. relancer PIT et vérifier que le mutant est tué ;
4. consigner le nouveau test dans `06-test-plan.md`.

Si un mutant est réellement équivalent, donc impossible à tuer, l'exclure avec
`@CoverageIgnore` sur la **méthode précise**, avec un commentaire explicatif et
une dérogation suivie dans `08-code-review.md`.

## Mutations importantes

| Mutateur | Exemple | Signal |
|---|---|---|
| `NegateConditionals` | `x > 0` devient `x <= 0` | Tests de frontière manquants. |
| `ReturnVals` | `return x` devient `return null` | L'appelant ne vérifie pas la nullité. |
| `MathMutator` | `a + b` devient `a - b` | Arithmétique insuffisamment testée. |
| `VoidMethodCalls` | supprime un appel | Effet de bord non vérifié. |

`spring-validator` analyse `mutations.xml` et liste chaque mutant `SURVIVED` des
fichiers modifiés dans `07-validation-report.md`.

## Anti-patterns

- Abaisser `mutationThreshold` pour verdir le build.
- Exclure des packages entiers parce qu'ils sont difficiles à tester.
- Déclarer un mutant équivalent sans justification d'une ligne.
- Exécuter PIT sur tout le code à chaque build.
