# Preuves de stack

Détecter un framework à partir de son contenu, jamais à partir du seul nom d'un
outil de build ou d'un dossier générique.

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

- `spring` : Spring uniquement est prouvé ;
- `react-nextjs` : React ou Next.js uniquement est prouvé ;
- `full-stack` : les deux familles sont prouvées et concernées par la feature ;
- `unknown` : preuve absente, générique ou contradictoire.

Avec `unknown`, ne déléguer aucun architecte. Montrer les preuves inspectées et
demander une clarification ou un onboarding au lieu de deviner.
