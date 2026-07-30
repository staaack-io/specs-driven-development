#!/usr/bin/env bash
# block-progress-on-open-questions.sh
# Hook Codex PreToolUse pour apply_patch, également associé aux alias Edit|Write.
# Refuse de créer ou modifier un artefact .specs de numéro supérieur tant qu'un
# artefact antérieur contient des questions Q-NNN non résolues.

set -euo pipefail

input="$(cat)"
hook_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$hook_dir/lib.sh"
codex_hook_cd_repo_root

paths="$(codex_hook_paths "$input")"
[ -z "$paths" ] && exit 0

while IFS= read -r file_path; do
  # Appliquer uniquement aux artefacts numérotés .specs/<id>/NN-*.md.
  case "$file_path" in
    *.specs/*/[0-9][0-9]*-*.md) ;;
    *) continue ;;
  esac

# Extraire le dossier de la fonctionnalité et le préfixe numérique de la cible.
feature_dir="$(dirname "$file_path")"
target_basename="$(basename "$file_path")"
target_num="${target_basename%%-*}"  # "03"

# Chercher les fichiers de numéro inférieur dans le même dossier.
shopt -s nullglob
for f in "$feature_dir"/[0-9][0-9]*-*.md; do
  base="$(basename "$f")"
  num="${base%%-*}"
  if [[ "$num" < "$target_num" ]]; then
    # Chercher les Q-NNN non résolues sous "## Open Questions", jusqu'au titre "## " suivant.
    open_count="$(awk '
      /^## Open Questions[[:space:]]*$/ { capture=1; next }
      /^## / { capture=0 }
      capture && /^- \*\*Q-[0-9]+\*\*/ { count++ }
      END { print count+0 }
    ' "$f")"
    if [ "$open_count" -gt 0 ]; then
      echo "BLOQUÉ : $f contient $open_count question(s) Q-NNN non résolue(s). Résolvez-les en les déplaçant sous ## Resolved Questions avec réponse et date avant de modifier $file_path." >&2
      exit 2
    fi
  fi
  done
done <<< "$paths"

exit 0
