# Rapport de validation : <FEATURE-ID>

> Responsable : `spring-validator` · Phase 6 · Généré par `.github/scripts/harness.sh` et le skill `harness-report-parsing`.

## Summary

- Version du harness : <version>
- Exécuté le : <YYYY-MM-DDTHH:MM:SSZ>
- Commit : <git-sha>
- Résultat : ✅ green | ⚠️ yellow | ❌ red
- Régressions par rapport à la référence : <nombre>
- Échecs préexistants de la référence, à titre informatif : <nombre>

## Gates

| N° | Couche | Outil | Résultat | Régressions | Préexistants |
|---|---|---|---|---|---|
| 1 | Formatage et lint | Spotless / Checkstyle | ✅ | 0 | 0 |
| 2 | Compilation | Maven | ✅ | 0 | 0 |
| 3 | Analyse statique | SpotBugs / Error Prone | ✅ | 0 | 0 |
| 4 | Architecture | ArchUnit | ✅ | 0 | 0 |
| 5 | Tests unitaires et par tranche | JUnit 5 / Surefire | ✅ | 0 | 0 |
| 6 | Intégration | JUnit 5 / Failsafe / Testcontainers | ✅ | 0 | 0 |
| 7 | Couverture | JaCoCo | ✅ | 0 | 0 |
| 8 | Mutation | PIT (incrémental) | ✅ | 0 | 0 |
| 9 | Contrat | diff OpenAPI | ✅ | 0 | 0 |
| 10 | Sécurité | OWASP Dependency Check | ✅ | 0 | 0 |

## Coverage detail

| Périmètre | Lignes | Branches | Statut |
|---|---|---|---|
| Global | <pct> | <pct> | ✅ ≥ 95 / ⚠️ 90–95 / ❌ < 90 |
| Par package modifié | … | … | … |
| Nouveau code | <pct> | <pct> | ✅ ≥ 95 / ❌ < 95 |

## Mutation detail

| Package | Mutateurs | Tués | Survivants | Score |
|---|---|---|---|---|

Les mutants survivants dans les packages modifiés sont listés sous `## Findings` avec la sévérité `major`.

## Contract diff

- Source : <api/openapi.yaml | generated>
- Changements cassants : <aucun | liste>
- Changements compatibles : <aucun | liste>

## Security findings

- CVE critiques ou hautes : <nombre>
- Exclusions pendant cette exécution : <nombre> ; chacune doit être suivie dans `dependency-check-suppressions.xml`.

## Findings

> Chaque constat possède un identifiant stable, une sévérité et une piste de correction.

- F-001 (sévérité : <blocker|major|minor|nit>) : <description> — correction : <piste>

## Baseline diff

- Fichier de référence : `.specs/_baseline.json`
- Entrées ajoutées pendant cette exécution : <nombre> ; toute entrée qui masque un nouvel échec est elle-même un constat `major` en revue de code.
- Entrées supprimées car résolues : <nombre>

## Sign-off

- [ ] Toutes les portes requises réussissent ou sont acceptées comme dette préexistante.
- [ ] Aucune nouvelle entrée de référence sans ADR.
- [ ] `07a-traceability.md` est produit et complet.
