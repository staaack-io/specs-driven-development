# Classification et preuves

## Greenfield ou brownfield

- `brownfield` : au moins un fichier de code produit est présent hors dossiers
  générés et hors tests ;
- `greenfield` : aucun fichier de code produit n'est trouvé ;
- une structure vide ou un manifeste seul ne prouve pas du code produit.

Cette classification décrit le dépôt observé. Elle ne juge ni sa maturité ni sa
qualité.

## Preuves de framework

| Stack | Preuve suffisante |
| --- | --- |
| Spring | parent, BOM, plugin ou starter `spring-boot-*` dans Maven/Gradle |
| Next.js | dépendance `next` dans `package.json` |
| React | dépendance `react` dans `package.json` |
| Maven | `pom.xml`, sans conclure Spring |
| Gradle | `build.gradle` ou `build.gradle.kts`, sans conclure Spring |
| Node | `package.json`, sans conclure React ou Next.js |

Un nom de dossier tel que `backend`, `frontend`, `app` ou `src` n'est pas une
preuve. Un framework présent dans un module voisin ne prouve pas la stack d'un
autre module.

## Versions et commandes

- Une version vient du manifeste ou du lockfile ; une plage reste une plage.
- Une commande vient d'un script déclaré ou du wrapper de build présent.
- Seul le nom de l'invocation est conservé, jamais le corps arbitraire d'un
  script ni une valeur d'environnement.
- Une preuve absente produit `limited` ou `unknown` et une limite explicite.

## Contradictions

Flyway et Liquibase dans le même module Spring constituent une contradiction
bloquante. Plusieurs gestionnaires de paquets, manifests illisibles ou preuves
incompatibles sont signalés ; l'agent principal demande une décision si cela
change le résultat.
