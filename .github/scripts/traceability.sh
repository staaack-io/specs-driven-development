#!/usr/bin/env bash
# traceability.sh
# Construit la matrice AC-NNN → tests + code pour une fonctionnalité et écrit
# .specs/<feature>/07a-traceability.md.
#
# Utilisation : scripts/traceability.sh <feature-id>

set -euo pipefail

FEATURE="${1:-}"
if [ -z "$FEATURE" ]; then
  echo "Utilisation : $0 <feature-id>" >&2
  exit 2
fi

SPEC="$(ls .specs/$FEATURE/01-*.md 2>/dev/null | head -n 1)"
if [ -z "$SPEC" ] || [ ! -f "$SPEC" ]; then
  echo "ERREUR : spécification introuvable dans .specs/$FEATURE/01-*.md" >&2
  exit 2
fi

OUT=".specs/$FEATURE/07a-traceability.md"

# Extraire les titres AC-NNN depuis la spécification.
mapfile -t acs < <(grep -E '^### AC-[0-9]+' "$SPEC" | sed -E 's/^### (AC-[0-9]+)[[:space:]]*[:.-][[:space:]]*(.*)/\1|\2/')

{
  echo "# Traçabilité : $FEATURE"
  echo
  echo "Généré le : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "| AC | Titre | Tests | Code de production |"
  echo "|----|-------|-------|--------------------|"
  for entry in "${acs[@]}"; do
    ac="${entry%%|*}"
    title="${entry#*|}"
    # Tests : chercher @Tag("AC-NNN") dans src/test.
    tests=$(grep -RIl --include='*.java' "@Tag(\"$ac\")" src/test 2>/dev/null \
      | sed -E 's|^src/test/java/||; s|\.java$||; s|/|.|g' | tr '\n' ',' | sed 's/,$//')
    # Code : au mieux, classes de production référencées par les imports des tests.
    test_files=$(grep -RIl --include='*.java' "@Tag(\"$ac\")" src/test 2>/dev/null || true)
    code=""
    if [ -n "$test_files" ]; then
      code=$(grep -h -E '^import [a-z]' $test_files 2>/dev/null \
        | grep -v '^import (java\.|org\.junit|org\.springframework\.test|org\.testcontainers|static )' \
        | sed -E 's/^import (.+);$/\1/' | sort -u | tr '\n' ',' | sed 's/,$//')
    fi
    echo "| $ac | ${title:-(sans titre)} | ${tests:-_(aucun)_} | ${code:-_(inconnu)_} |"
  done
  echo
  echo "## Notes"
  echo
  echo "- Un AC sans test constitue un échec strict de validation."
  echo "- La colonne du code de production est heuristique et repose sur les imports des tests ; vérifier manuellement."
} > "$OUT"

echo "Fichier $OUT écrit"
