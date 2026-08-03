# Contrat de `06-test-plan.md`

Le plan contient une matrice critères × types avec, pour chaque test, un chemin
concret, un nom descriptif, `@Tag("AC-NNN")` et `@DisplayName`. Il indique les
tests unitaires, d'intégration, d'architecture et les besoins Testcontainers.

Avec `--gap`, chaque défaut devient un identifiant stable `Gap-NNN`. Chaque gap
référence soit le test ajouté, soit une justification explicite `Won't fix`.
Aucun gap ne reste sans résolution.

Les preuves de gate conservent des argv structurés, le code de retour, une
sortie expurgée et seulement le résultat `PASS` ou `FAIL`. Un plan ne prétend
pas prouver AC-196 à AC-209 sans référencer les méthodes de test exécutables du
runtime.
