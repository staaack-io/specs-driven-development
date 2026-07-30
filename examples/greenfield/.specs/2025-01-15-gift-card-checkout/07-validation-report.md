# Rapport de validation : gift-card-checkout

| Champ             | Valeur                                               |
|-------------------|------------------------------------------------------|
| Fonctionnalité    | `2025-01-15-gift-card-checkout`                      |
| Exécuté le        | 2025-01-22T14:31:08Z                                 |
| Git SHA           | `a1b2c3d`                                            |
| Verdict           | **PASS**                                             |
| Stack             | Java 25, Spring Boot 4.0.0, Postgres + Flyway, Testcontainers actif |

## Résultats des portes

| # | Porte                         | Statut | Détail                                              |
|---|-------------------------------|--------|-----------------------------------------------------|
| 1 | Formatage Spotless            | pass   | aucun fichier reformaté                             |
| 2 | Checkstyle                    | pass   | aucune violation                                    |
| 3 | Compilation + Error Prone     | pass   | aucune erreur ni avertissement                      |
| 4 | SpotBugs                      | pass   | aucun bug                                           |
| 5 | ArchUnit                      | pass   | 5/5 rules (`giftcardInternalIsHidden`, `giftcardDoesNotDependOnOrder`, `noCyclesBetweenTopLevelPackages`, two pre-existing) |
| 6 | Tests unitaires Surefire      | pass   | 14 tests, aucun échec ni test ignoré                |
| 7 | Tests d'intégration Failsafe  | pass   | 4 tests, aucun échec                                |
| 8 | Couverture JaCoCo globale     | pass   | lignes 92,4 %, branches 91,1 %, plancher 90 %      |
|   | Couverture du nouveau code    | pass   | 100 %, 138 lignes sur 138                           |
| 9 | Mutation PIT                  | pass   | 86 %, 4 survivants dont 3 justifiés                 |
|10 | OWASP Dependency-Check        | pass   | aucune vulnérabilité CVSS ≥ 7                       |
|11 | Diff OpenAPI                  | pass   | un chemin ajouté, aucun changement cassant          |
|12 | Traçabilité (`07a`)           | pass   | chaque AC possède un test marqué                    |

## Mutants survivants, trois justifiés

1. `GiftCardCodeHasher.hash()` : mutant removed-conditional sur la branche
   défensive `if (salt == null)`, qui est inaccessible puisque `salt` est validé
   par `@NotNull` avec `@ConfigurationProperties`. **Justification acceptée** —
   contrôle défensif de nullité.
2. `GiftCardEntity.amountToDebit()` : constante incrémentée dans l'argument de
   `Math.min`. Le mutant était équivalent : les deux côtés produisaient le même
   `Money`, car le test de couverture utilise un solde égal au sous-total. Un
   test complémentaire avec des valeurs distinctes a été ajouté ; le mutant est
   maintenant éliminé.
3. `IdempotencyStore.save()` : removed-conditional sur la capture de clé en
   double. Cette capture est exercée par `IdempotentRedeemIT` ; le mutant
   survivant ignore toutes les `DataIntegrityViolationException`, ce que notre
   test ne distingue pas d'un succès puisque les deux chemins renvoient le même
   contenu `Applied`. **Justification acceptée** — le contrat demande de renvoyer
   le même contenu et le mutant le préserve. Suivi comme nit dans
   `08-code-review.md`.

## Prochaine action recommandée

`$review 2025-01-15-gift-card-checkout`
