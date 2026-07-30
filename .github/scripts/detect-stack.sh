#!/usr/bin/env bash
# detect-stack.sh
# Détecte la stack du projet et produit un document JSON qui la décrit.
# Utilisé par spring-architect, spring-onboarding et le harness.

set -euo pipefail

POM="${1:-pom.xml}"

if [ ! -f "$POM" ]; then
  echo '{"error":"pom.xml introuvable","searched":"'"$POM"'"}'
  exit 1
fi

has_dep() { grep -Eq "<artifactId>$1</artifactId>" "$POM"; }
get_prop() { sed -n "s|.*<$1>\\(.*\\)</$1>.*|\\1|p" "$POM" | head -n 1; }

java_version="$(get_prop 'java.version')"
boot_version="$(get_prop 'spring-boot.version')"
[ -z "$boot_version" ] && boot_version="$( { grep -A1 '<artifactId>spring-boot-starter-parent</artifactId>' "$POM" || true; } | sed -n 's|.*<version>\(.*\)</version>.*|\1|p' | head -n 1)"

# Moteurs de base de données.
db_engines=()
for d in postgresql mysql-connector-j mariadb-java-client h2 ojdbc8 ojdbc11 mssql-jdbc; do
  if has_dep "$d"; then db_engines+=("$d"); fi
done

# Outil de migration.
flyway=$(has_dep 'flyway-core' && echo true || echo false)
liquibase=$(has_dep 'liquibase-core' && echo true || echo false)
flyway_dir=$([ -d src/main/resources/db/migration ] && echo true || echo false)
liquibase_dir=$([ -d src/main/resources/db/changelog ] && echo true || echo false)

migration="none"
if $flyway && $liquibase; then
  migration="both"
elif $flyway || $flyway_dir; then
  migration="flyway"
elif $liquibase || $liquibase_dir; then
  migration="liquibase"
fi

testcontainers=$(grep -Eq '<artifactId>(testcontainers|spring-boot-testcontainers|testcontainers-[a-z0-9-]+)</artifactId>' "$POM" && echo true || echo false)
junit5=$(grep -Eq '<artifactId>(junit-jupiter|spring-boot-starter-test|spring-boot-starter-webmvc-test|spring-boot-starter-webflux-test)</artifactId>' "$POM" && echo true || echo false)
archunit=$(has_dep 'archunit' && echo true || echo false)
springdoc=$(has_dep 'springdoc-openapi-starter-webmvc-ui' && echo true || echo false)
openapi_spec=$([ -f src/main/resources/openapi/openapi.yaml ] && echo true || echo false)
spotless=$(has_dep 'spotless-maven-plugin' && echo true || echo false)
checkstyle=$(has_dep 'maven-checkstyle-plugin' && echo true || echo false)
spotbugs=$(has_dep 'spotbugs-maven-plugin' && echo true || echo false)
jacoco=$(has_dep 'jacoco-maven-plugin' && echo true || echo false)
pit=$(has_dep 'pitest-maven' && echo true || echo false)
depcheck=$(has_dep 'dependency-check-maven' && echo true || echo false)

# Projets voisins : détecter les applications non-JVM à côté du module Maven afin
# que l'artefact d'onboarding les consigne comme contexte (frontend, infra, etc.).
ROOT_DIR="$(dirname "$(cd "$(dirname "$POM")" && pwd)")"
MODULE_DIR="$(cd "$(dirname "$POM")" && pwd)"
siblings=()
if [ -d "$ROOT_DIR" ] && [ "$ROOT_DIR" != "$MODULE_DIR" ]; then
  for d in "$ROOT_DIR"/*/; do
    [ -d "$d" ] || continue
    name="$(basename "$d")"
    [ "$d" = "$MODULE_DIR/" ] && continue
    case "$name" in .*|target|node_modules) continue;; esac
    kind=""
    [ -f "$d/package.json" ] && kind="node"
    if [ -f "$d/next.config.js" ] || [ -f "$d/next.config.mjs" ] ||
       [ -f "$d/next.config.ts" ] ||
       { [ -f "$d/package.json" ] && grep -Eq '"next"[[:space:]]*:' "$d/package.json"; }; then
      kind="nextjs"
    fi
    [ -f "$d/pom.xml" ] && kind="maven"
    [ -f "$d/build.gradle" ] || [ -f "$d/build.gradle.kts" ] && kind="${kind:-gradle}"
    [ -n "$kind" ] && siblings+=("{\"name\":\"$name\",\"kind\":\"$kind\"}")
  done
fi

# Produire le JSON.
cat <<EOF
{
  "module_path": "${MODULE_DIR#$ROOT_DIR/}",
  "siblings": [$(IFS=,; echo "${siblings[*]:-}")],
  "java_version": "${java_version:-unknown}",
  "spring_boot_version": "${boot_version:-unknown}",
  "db_engines": [$(printf '"%s",' "${db_engines[@]}" | sed 's/,$//')],
  "migration": "$migration",
  "test": {
    "junit5": $junit5,
    "testcontainers": $testcontainers,
    "archunit": $archunit
  },
  "openapi": {
    "springdoc": $springdoc,
    "spec_file": $openapi_spec
  },
  "harness_layers": {
    "spotless": $spotless,
    "checkstyle": $checkstyle,
    "spotbugs": $spotbugs,
    "jacoco": $jacoco,
    "pit": $pit,
    "dependency_check": $depcheck
  }
}
EOF
