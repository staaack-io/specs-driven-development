# Checklist des portes de validation

Utilisée par `spring-validator` pour autoriser la sortie de la phase 6.

## Portes strictes (doivent réussir ou être acceptées comme dette préexistante)

- [ ] Formatage et lint (Spotless, Checkstyle).
- [ ] Compilation (`compile`, `test-compile`).
- [ ] Analyse statique (SpotBugs, Error Prone).
- [ ] Architecture (règles ArchUnit : frontières, absence de cycles, isolation des packages internes).
- [ ] Tests unitaires et par tranche (Surefire).
- [ ] Tests d'intégration (Failsafe + Testcontainers, s'ils existent).
- [ ] Couverture : au moins 90 % lignes et branches, globalement et par package ; nouveau code au moins 95 %.
- [ ] Mutation : aucun mutant survivant dans les packages modifiés, sauf justification par ADR.
- [ ] Contrat : le diff OpenAPI ne contient aucun changement cassant, sauf justification par ADR.
- [ ] Sécurité : aucune nouvelle CVE haute ou critique ; les exclusions sont suivies dans `dependency-check-suppressions.xml`.

## Rapports analysés

- [ ] XML Surefire (`target/surefire-reports/`)
- [ ] XML Failsafe (`target/failsafe-reports/`)
- [ ] XML JaCoCo (`target/site/jacoco/jacoco.xml`)
- [ ] XML PIT (`target/pit-reports/mutations.xml`)
- [ ] XML Checkstyle (`target/checkstyle-result.xml`)
- [ ] XML SpotBugs (`target/spotbugsXml.xml`)
- [ ] JSON du diff OpenAPI
- [ ] Rapport Dependency-Check

## Traçabilité

- [ ] `07a-traceability.md` est produit.
- [ ] Aucun AC sans test associé.
- [ ] Aucun test orphelin.
- [ ] Aucun symbole de code orphelin, c'est-à-dire modifié dans le diff mais non couvert par un test.

## Hygiène de la référence

- [ ] `.specs/_baseline.json` a été consulté.
- [ ] Toute nouvelle entrée est signalée pour la revue de code (`major`, sauf justification par ADR).

## Validation

- [ ] `07-validation-report.md` est écrit et passe sa propre checklist.
- [ ] La ligne de résultat utilise ✅ / ⚠️ / ❌ avec la bonne justification.
