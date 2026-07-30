# Preuves de stack

Détecter un framework à partir de son contenu, jamais à partir du seul nom d'un
outil de build ou d'un dossier générique.

## Périmètre fonctionnel

Une preuve de framework n'est utilisable que si elle concerne aussi la
fonctionnalité approuvée. Établir d'abord son périmètre à partir des AC, des
décisions résolues et des modules, routes, composants ou fichiers qu'ils
désignent.

Dans un monorepo, relier ensuite chaque preuve forte à ce périmètre par au moins
un élément concret : module concerné, chemin cité par la spécification, import
depuis le code visé ou cartographie explicite dans `.specs/_onboarding.md`.
La simple présence de Spring, React ou Next.js dans un autre module du dépôt ne
prouve pas la stack de la fonctionnalité.

Si le lien entre une preuve forte et le périmètre ne peut pas être établi,
demander une clarification. Sans clarification, classer la stack `unknown` et
ne déléguer aucun rôle.

## Spring

Accepter Spring lorsqu'au moins une preuve forte existe :

- `pom.xml` ou un fichier Gradle déclare le plugin `org.springframework.boot`,
  une dépendance `org.springframework.boot` ou un artefact `spring-boot-*` ;
- le code source contient une application `@SpringBootApplication` ou des
  imports `org.springframework.*` cohérents avec le périmètre ;
- `.specs/_onboarding.md` identifie explicitement Spring et cite ses fichiers de
  preuve.

`pom.xml`, `build.gradle*`, Java ou `src/main/java/` seuls ne prouvent pas
Spring. Quarkus, Micronaut, Jakarta EE et Java sans framework ne doivent pas
être routés vers `spring-architect`.

## React et Next.js

Accepter React ou Next.js lorsqu'au moins une preuve forte existe :

- `package.json` déclare `react` dans `dependencies` ou `devDependencies` ;
- pour Next.js, `package.json` déclare `next` et `react` ;
- le code importe `react`, `react-dom` ou `next/*` de manière cohérente avec le
  périmètre ;
- `.specs/_onboarding.md` identifie explicitement React ou Next.js et cite ses
  fichiers de preuve.

`package.json`, JavaScript, TypeScript, `app/` ou `pages/` seuls ne prouvent pas
React ou Next.js. Vue, Angular, Svelte et Node sans interface React ne doivent
pas être routés vers `react-nextjs-architect`.

## Résultat

- `spring` : Spring est prouvé et concerne la fonctionnalité, sans périmètre
  React ou Next.js concerné ;
- `react-nextjs` : React ou Next.js est prouvé et concerne la fonctionnalité,
  sans périmètre Spring concerné ;
- `full-stack` : les deux familles sont prouvées et concernent la
  fonctionnalité ;
- `unknown` : preuve absente, générique ou contradictoire.

Avec `unknown`, ne déléguer aucun architecte. Montrer les preuves inspectées et
demander une clarification ou un onboarding au lieu de deviner.
