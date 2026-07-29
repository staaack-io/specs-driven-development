#!/usr/bin/env bash
# enforce-files-in-scope.sh
# Codex PreToolUse hook for apply_patch (also matched by Edit|Write aliases).
# Blocks edits outside the active task's files_in_scope, EXCEPT:
#   - .specs/** is always allowed (artifacts).
#   - src/test/** is allowed for spring-test-engineer (red step).
#
# This is a defense-in-depth alongside block-impl-without-failing-test.sh which
# already covers src/main/**. This script extends the same check to test files.

set -euo pipefail

input="$(cat)"
hook_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$hook_dir/lib.sh"
codex_hook_cd_repo_root

paths="$(codex_hook_paths "$input")"
[ -z "$paths" ] && exit 0

while IFS= read -r file_path; do
  # Always allow artifact and harness configuration edits.
  case "$file_path" in
    *.specs/*|*/pom.xml|pom.xml|*/checkstyle.xml|checkstyle.xml|*/dependency-check-suppressions.xml|dependency-check-suppressions.xml)
      continue
      ;;
  esac

  # Only check src/test/** here (src/main/** is handled by the sibling hook).
  case "$file_path" in
    */src/test/*|src/test/*) ;;
    *) continue ;;
  esac

state_file="$(ls -t .specs/*/.tdd-state.json 2>/dev/null | head -n 1 || true)"
[ -z "$state_file" ] && exit 0  # no active feature; let it through (e.g. test-plan author)

active_task="$(jq -r '.active_task // empty' "$state_file")"
[ -z "$active_task" ] && exit 0

in_scope="$(jq -r --arg t "$active_task" --arg f "$file_path" '
  .tasks[$t].files_in_scope // []
  | map(select(. == $f or ($f | endswith(.))))
  | length
' "$state_file")"

  if [ "$in_scope" = "0" ]; then
    echo "BLOCKED: $file_path is not in task $active_task files_in_scope. Edit only the declared test paths, or update 04-tasks.md and re-plan." >&2
    exit 2
  fi
done <<< "$paths"

exit 0
