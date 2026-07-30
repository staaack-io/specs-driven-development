---
name: jacoco-coverage-policy
description: Configurer et appliquer la politique JaCoCo, avec un plancher de 90 % lignes et branches, un objectif de 95 % et 95 % sur le nouveau code. Utiliser pour raccorder JaCoCo ou lire `jacoco.xml`.
when_to_use:
  - Phases 5 et 6 — porte de couverture.
  - Onboarding brownfield — consigner la référence existante sans bloquer le premier jour.
authoritative_references:
  - https://www.jacoco.org/jacoco/trunk/doc/maven.html
---

# Politique de couverture JaCoCo

## Valeurs par défaut du framework

| Métrique | Plancher strict | Cible | Nouveau code |
|---|---|---|---|
| Couverture des lignes | 90 % | 95–100 % | 95 % des lignes ajoutées ou modifiées |
| Couverture des branches | 90 % | 95–100 % | 95 % |

Le plancher strict fait échouer le build. La cible est suivie sans être imposée.
Le nouveau code correspond aux lignes ajoutées ou modifiées par rapport à `origin/main`.

## Configuration Maven

```xml
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.12</version>
    <executions>
        <execution><id>prepare</id><goals><goal>prepare-agent</goal></goals></execution>
        <execution><id>report</id><phase>verify</phase><goals><goal>report</goal></goals></execution>
        <execution>
            <id>check</id><phase>verify</phase><goals><goal>check</goal></goals>
            <configuration><rules>
                <rule><element>BUNDLE</element><limits>
                    <limit><counter>LINE</counter><value>COVEREDRATIO</value><minimum>0.90</minimum></limit>
                    <limit><counter>BRANCH</counter><value>COVEREDRATIO</value><minimum>0.90</minimum></limit>
                </limits></rule>
                <rule><element>PACKAGE</element><limits>
                    <limit><counter>LINE</counter><value>COVEREDRATIO</value><minimum>0.85</minimum></limit>
                </limits></rule>
            </rules></configuration>
        </execution>
    </executions>
</plugin>
```

## Seules exclusions autorisées

- `**/*Application.class`, la classe `main` ;
- code généré sous `**/generated/**` et `**/openapi/**` ;
- DTO qui sont des records sans logique, uniquement pour la couverture de branches.

`**/config/**` n'est **pas** exclu : la configuration est du vrai code.

## Onboarding brownfield

Si la couverture actuelle est inférieure à 90 % :

1. mesurer les valeurs par package et les écrire dans `.specs/_baseline.json` ;
2. définir les seuils Maven à la valeur actuelle moins 1 %, pour le cliquet ;
3. exiger que chaque fonctionnalité maintienne ou améliore les packages touchés ;
4. imposer 95 % au nouveau code, indépendamment de la référence.

## Nouveau code à 95 %

Le harness croise les plages de `git diff --unified=0 origin/main...HEAD` avec les
entrées JaCoCo `<line nr="N" mi="0" ci="3" mb="0" cb="2"/>`. Une ligne du diff où
`mi > 0` compte comme non couverte. Le seuil est 95 %.

Cette logique se trouve dans `.github/scripts/check-new-code-coverage.sh`.

## Anti-patterns

- Exclure une classe parce qu'elle est difficile à tester.
- Exclure les services, qui sont précisément du code à tester.
- Traiter la couverture comme un objectif : c'est un plancher ; la mutation fournit le signal réel.
