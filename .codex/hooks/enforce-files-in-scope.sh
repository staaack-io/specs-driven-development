#!/usr/bin/env bash
# enforce-files-in-scope.sh
# Hook Codex PreToolUse pour apply_patch, également associé aux alias Edit|Write.
# Bloque les modifications hors du files_in_scope de la tâche active, SAUF :
#   - .specs/** est toujours autorisé pour les artefacts ;
#   - src/test/** est autorisé à spring-test-engineer pendant l'étape red.
#
# C'est une protection supplémentaire à block-impl-without-failing-test.sh, qui
# couvre déjà src/main/**. Ce script étend le contrôle aux fichiers de test.

set -euo pipefail

input="$(cat)"
hook_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$hook_dir/lib.sh"
codex_hook_cd_repo_root

paths="$(codex_hook_paths "$input")"
[ -z "$paths" ] && exit 0

while IFS= read -r file_path; do
  # Toujours autoriser les artefacts et la configuration du harness.
  case "$file_path" in
    *.specs/*|*/pom.xml|pom.xml|*/checkstyle.xml|checkstyle.xml|*/dependency-check-suppressions.xml|dependency-check-suppressions.xml)
      continue
      ;;
  esac

  # Contrôler seulement src/test/** ici ; le hook voisin traite src/main/**.
  case "$file_path" in
    */src/test/*|src/test/*) ;;
    *) continue ;;
  esac

state_file="$(ls -t .specs/*/.tdd-state.json 2>/dev/null | head -n 1 || true)"
[ -z "$state_file" ] && exit 0  # aucune fonctionnalité active : autoriser, par exemple pour le plan de test

active_task="$(jq -r '.active_task // empty' "$state_file")"
[ -z "$active_task" ] && exit 0

in_scope="$(jq -r --arg t "$active_task" --arg f "$file_path" '
  .tasks[$t].files_in_scope // []
  | map(select(. == $f or ($f | endswith(.))))
  | length
' "$state_file")"

  if [ "$in_scope" = "0" ]; then
    echo "BLOQUÉ : $file_path n'est pas dans files_in_scope pour la tâche $active_task. Modifiez uniquement les chemins de test déclarés, ou mettez 04-tasks.md à jour puis relancez la planification." >&2
    exit 2
  fi
done <<< "$paths"

exit 0
