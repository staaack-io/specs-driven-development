---
name: harness-report-parsing
description: Lire les rapports du harness Surefire, Failsafe, JaCoCo, PIT, Checkstyle, SpotBugs, OpenAPI et Dependency Check dans un résumé structuré. Utiliser pour `07-validation-report.md` ou pour expliquer un échec de CI.
when_to_use:
  - Phase 6, Validate — `$validate` exécute le harness et analyse chaque rapport.
  - Diagnostiquer un échec de CI depuis les journaux.
authoritative_references:
  - https://maven.apache.org/surefire/maven-surefire-plugin/xsd/surefire-test-report.xsd
  - https://www.jacoco.org/jacoco/trunk/coverage/report.dtd
---

# Analyse des rapports du harness

## Fichiers d'entrée

| Couche | Chemin | Format |
|---|---|---|
| Spotless | `target/spotless/` | code de sortie |
| Checkstyle | `target/checkstyle-result.xml` | XML |
| SpotBugs | `target/spotbugsXml.xml` | XML |
| Error Prone | stderr du compilateur | texte |
| ArchUnit | `target/surefire-reports/.../ArchitectureTest.xml` | XML Surefire |
| Surefire, unitaire | `target/surefire-reports/TEST-*.xml` | XML Surefire |
| Failsafe, intégration | `target/failsafe-reports/TEST-*.xml` | XML Surefire |
| JaCoCo | `target/site/jacoco/jacoco.xml` | XML JaCoCo |
| PIT | `target/pit-reports/mutations.xml` | XML PIT |
| Diff OpenAPI | `target/openapi-diff.json` | JSON |
| Dependency-Check | `target/dependency-check-report.json` | JSON |

## Forme de sortie de `harness-summary.json`

`.github/scripts/harness.sh --report` produit un document JSON unique consommé
par `spring-validator`. Les clés et valeurs techniques, comme `pass`, `error` et
`skipped`, restent en anglais car elles font partie du contrat machine.

## Règles d'analyse

- Un rapport **manquant** pour une couche configurée vaut `error`, pas `pass`.
- Une erreur d'analyse du rapport vaut `error`.
- Un test `skipped` sans commentaire source `# DisabledReason:` vaut `error`.

## Recette XML Surefire/Failsafe

```xpath
/testsuite/@tests        -> total
/testsuite/@failures     -> échecs d'assertion
/testsuite/@errors       -> exceptions
/testsuite/@skipped      -> tests ignorés
/testsuite/testcase[skipped]/@name  -> liste des tests ignorés
```

## Calcul JaCoCo du nouveau code

1. Exécuter `git diff --unified=0 origin/main...HEAD -- '*.java'` pour obtenir les fichiers et plages.
2. Pour chaque fichier, trouver dans `jacoco.xml` la classe et son `sourcefilename`.
3. Dans `<line nr="N" mi="X" ci="Y" mb="A" cb="B"/>`, `mi` représente les
   instructions manquées et `ci` les instructions couvertes. La ligne est couverte
   si `ci > 0`, manquée si `mi > 0` et `ci == 0`.
4. Calculer couvert ÷ (couvert + manqué) uniquement sur les lignes du diff.

## Mutants PIT dans les packages modifiés

```xpath
/mutations/mutation[@status='SURVIVED' and contains(mutatedClass, 'changed.package')]
```

Déduire `changed.package` en reliant les chemins du diff aux noms pleinement qualifiés.

## Anti-patterns

- Produire `pass` pour un rapport vide ; zéro test peut signaler une mauvaise configuration.
- Compter `skipped` comme `pass`.
- Agréger plusieurs modules sans détail par module.
- Masquer des erreurs en avertissements.
