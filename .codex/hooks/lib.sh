#!/usr/bin/env bash

# Afficher chaque chemin ciblé par une charge utile de hook Codex ou historique.
# Codex transmet apply_patch dans tool_input.command ; les anciens outils peuvent
# transmettre un seul tool_input.file_path ou tool_input.path.
codex_hook_paths() {
  local input="$1"
  local direct_path
  local patch

  direct_path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.path // empty')"
  if [ -n "$direct_path" ]; then
    printf '%s\n' "$direct_path"
  fi

  patch="$(printf '%s' "$input" | jq -r '.tool_input.command // empty')"
  [ -z "$patch" ] && return 0

  printf '%s\n' "$patch" | sed -nE \
    -e 's/^\*\*\* (Add|Update|Delete) File: //p' \
    -e 's/^\*\*\* Move to: //p'
}

codex_hook_cd_repo_root() {
  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  cd "$root"
}
