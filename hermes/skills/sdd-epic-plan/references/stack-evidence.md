# Preuves de stack

Détecter un framework depuis son contenu et son lien avec les AC, jamais depuis
le seul nom d'un outil de build ou d'un dossier générique.

## Périmètre

Établir les modules, routes, composants et contrats concernés depuis la
spécification et les décisions résolues. Dans un monorepo, relier chaque preuve
au périmètre par un chemin cité, un import, un module ou la cartographie de
`.specs/_onboarding.md`. Une preuve située dans un autre module ne suffit pas.

## Spring

Exiger au moins une preuve forte reliée au périmètre :

- plugin, dépendance ou artefact `org.springframework.boot`/`spring-boot-*` ;
- `@SpringBootApplication` ou imports `org.springframework.*` cohérents ;
- onboarding identifiant Spring avec ses fichiers de preuve.

Ne jamais accepter seuls `pom.xml`, `build.gradle*`, Java ou `src/main/java/`.
Ne pas router Quarkus, Micronaut, Jakarta EE ou Java seul vers Spring.

## React et Next.js

Exiger au moins une preuve forte reliée au périmètre :

- dépendance `react` ;
- dépendances `next` et `react` pour Next.js ;
- imports `react`, `react-dom` ou `next/*` cohérents ;
- onboarding identifiant React/Next.js avec ses fichiers de preuve.

Ne jamais accepter seuls `package.json`, TypeScript, `app/` ou `pages/`. Ne pas
router Vue, Angular, Svelte ou Node sans React vers ce rôle.

## Résultat

- `spring` : preuve Spring reliée au périmètre ;
- `react-nextjs` : preuve React/Next.js reliée au périmètre ;
- `full-stack` : les deux familles sont prouvées et concernées ;
- `unknown` : preuve absente, générique, non reliée ou contradictoire.

Avec `unknown`, ne déléguer aucun rôle. Montrer les preuves inspectées et
demander une clarification ou un onboarding.
