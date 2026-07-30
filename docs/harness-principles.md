# Principes du harness

> **L’agent valide son propre travail.** Un humain relit le résultat, pas chaque
> ligne.

## Pourquoi un harness plutôt que de simples impressions

Les agents génératifs peuvent être très sûrs d’eux tout en se trompant. La seule
protection durable est un harness déterministe, composé de plusieurs couches,
qui s’exécute toujours de la même manière et dont les rapports sont lus
automatiquement avant qu’un agent déclare une tâche terminée. Si une couche
régresse, l’agent doit la corriger avant d’avancer.

Les agents Codex, le développement local et la CI appellent tous le **même**
script `.github/scripts/harness.sh`. Il n’existe pas de seconde source de
vérité.

## Différence entre hooks et harness

Un **hook** est un garde-fou court, déclenché automatiquement avant ou après une
action Codex précise. Il répond immédiatement à une question ciblée : « cette
édition est-elle autorisée ? », « le fichier appartient-il au périmètre ? » ou
« cette commande contourne-t-elle les tests ? ». Un hook peut bloquer l’action
avant qu’elle ne produise ses effets.

Le **harness** est une campagne de validation complète. Il compile le projet,
exécute les tests et contrôle la qualité, l’architecture, la couverture, les
mutations, les contrats et la sécurité. Il s’exécute à la demande, via
`$validate`, depuis le terminal ou en CI.

En une phrase : **les hooks sécurisent chaque geste ; le harness démontre la
qualité de l’état obtenu**.

## Propriétés

1. **Déterministe.** Même commit, même résultat. Aucune décision aléatoire ni
   dépendance à l’heure ; `junit5-testcontainers-patterns` définit notamment
   les horloges et identifiants contrôlés.
2. **À plusieurs couches, avec arrêt rapide.** Les contrôles les moins coûteux
   passent d’abord afin de fournir rapidement le retour le plus utile.
3. **Incrémental lorsque cela compte.** PIT et la couverture peuvent cibler les
   paquets modifiés ou le nouveau code pour garder une boucle locale rapide ; la
   CI exécute la totalité.
4. **Lisible par une machine.** Chaque couche produit un rapport structuré :
   XML Surefire, JaCoCo, PIT, Checkstyle ou SpotBugs, et JSON OpenAPI.
   `harness-report-parsing` et `requirements-traceability` les consomment.
5. **Conscient de la référence.** Un dépôt brownfield consigne ses échecs
   préexistants dans `.specs/_baseline.json`. Seules les régressions bloquent.
6. **Auto-validé, jamais auto-fusionné.** L’agent doit produire une validation et
   une revue vertes, mais un humain approuve toujours la pull request.

## Les dix couches

| Nº | Couche | Outil | Signification d’un échec |
| --- | --- | --- | --- |
| 1 | Format et lint | Spotless, Checkstyle | dérive de style ou de format |
| 2 | Compilation | `javac` avec Maven | le code ne compile pas |
| 3 | Analyse statique | SpotBugs, Error Prone | motif susceptible de produire un bug |
| 4 | Architecture | ArchUnit | violation de frontière ou de couche |
| 5 | Tests unitaires et de tranche | JUnit 5, Surefire | régression logique |
| 6 | Tests d’intégration | JUnit 5, Failsafe, Testcontainers | régression de base, broker ou service externe |
| 7 | Couverture | JaCoCo | moins de 90 % lignes et branches, ou moins de 95 % sur le nouveau code |
| 8 | Mutation | PIT | mutants survivants dans les paquets modifiés |
| 9 | Contrat | générateur et diff OpenAPI | rupture d’API |
| 10 | Sécurité | OWASP Dependency Check | CVE connue dans les dépendances |

Les couches 1 à 6 s’exécutent toujours. Les couches 7 à 10 sont obligatoires
pour `$validate`. PIT est incrémental en local et complet la nuit en CI.

## Politique de couverture

- **Plancher strict : 90 %** des lignes et branches, par paquet et au global,
  code généré exclu. Le harness échoue en dessous.
- **Objectif : 95 à 100 %.** Un paquet entre 90 et 95 % apparaît en jaune dans
  `07-validation-report.md` et en constat mineur dans `08-code-review.md`,
  ou majeur s’il fait partie du changement.
- **Incrémental :** le code ajouté par la fonctionnalité doit atteindre **95 %**
  via le contrôle de couverture du diff.

## Politique de mutation

- PIT cible en local les paquets touchés par la tâche active.
- Un mutant survivant dans du code modifié devient un constat majeur.
- La CI nocturne analyse tous les modules et actualise la référence.

## Références brownfield

`.specs/_baseline.json` est versionné afin que l’agent puisse le lire sans
accès réseau :

```json
{
  "generated_at": "2026-04-18T10:00:00Z",
  "harness_version": "1.0",
  "failures": {
    "checkstyle": ["..."],
    "spotbugs": ["..."],
    "coverage_below_threshold": ["com.example.legacy"],
    "pit_surviving": ["..."]
  }
}
```

Un échec n’est une **régression** que s’il ne figure pas dans cette référence.
Ajouter une entrée uniquement pour masquer un nouvel échec constitue un constat
majeur, sauf ADR expliquant cette décision.

## Règles strictes

- `mvn -DskipTests`, `-Dcheckstyle.skip`, `-Dpit.skip` et
  `--no-verify` sont bloqués partout.
- Un `@Disabled` sans commentaire
  `# DisabledReason: <link-to-issue>` est bloquant.
- Abaisser les seuils de couverture est bloquant sans ADR.
- Retirer une assertion ou un appel `verify(*)` est bloquant sans ADR.
- `08-code-review.md` doit exister et être plus récent que la dernière
  modification du code avant `git commit`.

Ces règles sont appliquées par les hooks `block-*` et `forbid-*` configurés
dans `.codex/hooks.json` et implémentés sous `.codex/hooks/`.
