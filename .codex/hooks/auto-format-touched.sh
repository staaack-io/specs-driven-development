#!/usr/bin/env bash
# auto-format-touched.sh
# Hook Codex PostToolUse pour apply_patch, également associé aux alias Edit|Write.
# Exécute Spotless sur le fichier modifié s'il est en Java afin que la porte de
# formatage du harness réussisse. Au mieux : une erreur de formatage est signalée
# sans faire échouer la modification de l'agent.

set -euo pipefail

input="$(cat)"
hook_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$hook_dir/lib.sh"
codex_hook_cd_repo_root

paths="$(codex_hook_paths "$input")"
[ -z "$paths" ] && exit 0

while IFS= read -r file_path; do
  case "$file_path" in
    *.java) ;;
    *) continue ;;
  esac

  # Exécuter uniquement si Maven et Spotless sont configurés.
  if [ -f pom.xml ] && grep -q 'spotless-maven-plugin' pom.xml; then
    mvn -q spotless:apply -DspotlessFiles="$file_path" >/dev/null 2>&1 || \
      echo "AVERTISSEMENT : Spotless a échoué sur $file_path ; poursuite en cours" >&2
  fi
done <<< "$paths"

exit 0
