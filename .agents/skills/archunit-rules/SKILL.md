---
name: archunit-rules
description: Encoder les invariants d’architecture sous forme de règles ArchUnit. Utiliser pour définir ou relire les frontières de couches, dépendances de paquets, conventions de nommage ou accès entre modules.
when_to_use:
  - Phase 5, Test — ajouter les suites architecturales transverses.
  - Onboarding brownfield — capturer l’architecture existante puis appliquer un cliquet.
  - Toute revue où un import `.internal.` paraît suspect.
authoritative_references:
  - https://www.archunit.org/userguide/html/000_Index.html
---

# Règles ArchUnit

## Règles par défaut en greenfield

Ces règles supposent un **regroupement par fonctionnalité avec sous-packages
typés** : chaque package de premier niveau sous la racine de l'application est une
fonctionnalité ou un domaine, avec un sous-package publié `api` et des packages
privés `internal`, `model`, `repository` et `service`. Aucun package de premier
niveau `controller`, `service` ou `repository`.

Placer les règles suivantes dans `src/test/java/.../arch/ArchitectureTest.java` :

```java
@AnalyzeClasses(packages = "com.example.shop", importOptions = ImportOption.DoNotIncludeTests.class)
class ArchitectureTest {

    @ArchTest
    static final ArchRule internalIsPrivateToItsFeature =
        slices().matching("com.example.shop.(*)..")
                .should().notDependOnEachOther()
                .ignoreDependency(
                    JavaClass.Predicates.resideInAPackage("..internal.."),
                    JavaClass.Predicates.resideInAPackage("..api.."));

    @ArchTest
    static final ArchRule no_internal_access_across_features =
        noClasses().that().resideOutsideOfPackages(
                "..(*).internal..", "..(*).model..", "..(*).repository..", "..(*).service..")
               .should().dependOnClassesThat().resideInAnyPackage(
                "..internal..", "..model..", "..repository..", "..service..");

    @ArchTest
    static final ArchRule no_field_injection =
        noFields().should().beAnnotatedWith("org.springframework.beans.factory.annotation.Autowired");

    @ArchTest
    static final ArchRule no_by_layer_root_packages =
        noClasses().should().resideInAnyPackage(
            "com.example.shop.controller..", "com.example.shop.service..",
            "com.example.shop.repository..", "com.example.shop.model..",
            "com.example.shop.dto..", "com.example.shop.util..");

    @ArchTest
    static final ArchRule entities_in_feature_private_package =
        classes().that().areAnnotatedWith("jakarta.persistence.Entity")
                 .should().resideInAnyPackage("..internal..", "..model..");

    @ArchTest
    static final ArchRule no_cycles_between_features =
        slices().matching("com.example.shop.(*)..").should().beFreeOfCycles();
}
```

Les règles d'accès interne et de cycles imposent les frontières sans dépendance
d'exécution supplémentaire. Exécuter ces règles dans la porte d'architecture,
couche 4 du harness.

## Cliquet brownfield

Si le projet possède des violations, ne pas affaiblir la règle :

1. exécuter la règle et capturer les violations ;
2. ne pas utiliser `.allowEmptyShould(true)` ;
3. utiliser le mode de gel :

```java
@ArchTest
static final ArchRule no_field_injection_frozen =
    FreezingArchRule.freeze(no_field_injection);
```

Le gel place l'existant dans `archunit_store/`. L'ancien code ne bloque pas, mais
toute nouvelle violation fait échouer le build.

## Règles spécifiques à ajouter selon le projet

- Nommage : suffixes `Service`, `Repository` et `Controller`.
- Interdire `java.util.Date` et `java.text.SimpleDateFormat`, utiliser `java.time`.
- Interdire `System.out` et `System.err` en production.
- Interdire `@Transactional` sur les contrôleurs et `@Autowired` sur les constructeurs.
- Interdire Lombok. En brownfield, geler la règle avec `FreezingArchRule.freeze(...)`.

## Auto-vérification

- [ ] Les règles par défaut, notamment cycles et accès internes, sont présentes.
- [ ] Les violations brownfield sont gelées, pas ignorées.
- [ ] Aucun `ArchTest` n'est `@Disabled`.
