#!/usr/bin/env bash
# log-tdd-state-transition.sh
# Codex PostToolUse hook for apply_patch (also matched by Edit|Write aliases).
# When .tdd-state.json is touched OR an implementation log block is appended,
# write a one-line audit entry to .specs/<feature>/.tdd-audit.log so transitions
# are reviewable later.

set -euo pipefail

input="$(cat)"
hook_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$hook_dir/lib.sh"
codex_hook_cd_repo_root

paths="$(codex_hook_paths "$input")"
[ -z "$paths" ] && exit 0

ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

while IFS= read -r file_path; do
  case "$file_path" in
    *.specs/*/.tdd-state.json)
      feature_dir="$(dirname "$file_path")"
      audit="$feature_dir/.tdd-audit.log"
      active="$(jq -r '.active_task // "?"' "$file_path" 2>/dev/null || echo '?')"
      phase="$(jq -r --arg t "$active" '.tasks[$t].phase // "?"' "$file_path" 2>/dev/null || echo '?')"
      echo "$ts task=$active phase=$phase" >> "$audit"
      ;;
    *.specs/*/05-implementation-log.md)
      feature_dir="$(dirname "$file_path")"
      audit="$feature_dir/.tdd-audit.log"
      last_block="$(grep -E '^### T-' "$file_path" | tail -n 1 || true)"
      echo "$ts log_block=$last_block" >> "$audit"
      ;;
  esac
done <<< "$paths"

exit 0
