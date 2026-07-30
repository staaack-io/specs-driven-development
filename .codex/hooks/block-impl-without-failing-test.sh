#!/usr/bin/env bash
# block-impl-without-failing-test.sh
# Hook Codex PreToolUse pour apply_patch, également associé aux alias Edit|Write.
# Refuse de modifier src/main/** sauf si .specs/<active>/.tdd-state.json indique
# phase=red, avec red_failure_excerpt non vide et fichier dans files_in_scope.
#
# Entrée : JSON sur stdin, selon le protocole des hooks Codex.
# Sortie : code 0 pour autoriser ; code 2 et message stderr pour bloquer.

set -euo pipefail

input="$(cat)"
hook_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$hook_dir/lib.sh"
codex_hook_cd_repo_root

paths="$(codex_hook_paths "$input")"
[ -z "$paths" ] && exit 0

while IFS= read -r file_path; do
  # Appliquer uniquement à src/main/**.
  case "$file_path" in
    */src/main/*|src/main/*) ;;
    *) continue ;;
  esac

# Trouver la fonctionnalité active : le .tdd-state.json le plus récemment modifié.
state_file="$(ls -t .specs/*/.tdd-state.json 2>/dev/null | head -n 1 || true)"
if [ -z "$state_file" ] || [ ! -f "$state_file" ]; then
  echo "BLOQUÉ : aucun .specs/<feature>/.tdd-state.json trouvé. Exécutez \$build <task-id> afin que l'agent de test écrive d'abord le test en échec." >&2
  exit 2
fi

active_task="$(jq -r '.active_task // empty' "$state_file")"
if [ -z "$active_task" ]; then
  echo "BLOQUÉ : aucune active_task dans $state_file. Exécutez \$build <task-id>." >&2
  exit 2
fi

phase="$(jq -r --arg t "$active_task" '.tasks[$t].phase // empty' "$state_file")"
red_excerpt="$(jq -r --arg t "$active_task" '.tasks[$t].red_failure_excerpt // empty' "$state_file")"

if [ "$phase" != "red" ] && [ "$phase" != "green" ] && [ "$phase" != "refactor" ] && [ "$phase" != "simplify" ]; then
  echo "BLOQUÉ : la phase de la tâche $active_task est '$phase'. Impossible de modifier src/main/** sans test en échec (phase=red)." >&2
  exit 2
fi

if [ "$phase" = "red" ] && [ -z "$red_excerpt" ]; then
  echo "BLOQUÉ : la tâche $active_task est en phase=red mais red_failure_excerpt est vide. Le test en échec n'a pas été exécuté ou il a réussi." >&2
  exit 2
fi

# Vérification des fichiers dans le périmètre.
in_scope="$(jq -r --arg t "$active_task" --arg f "$file_path" '
  .tasks[$t].files_in_scope // []
  | map(select(. == $f or ($f | endswith(.))))
  | length
' "$state_file")"

  if [ "$in_scope" = "0" ]; then
    echo "BLOQUÉ : $file_path n'est pas dans files_in_scope pour la tâche $active_task. Modifiez uniquement les chemins déclarés, ou mettez d'abord la tâche à jour puis relancez \$plan." >&2
    exit 2
  fi
done <<< "$paths"

exit 0
