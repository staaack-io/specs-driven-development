#!/usr/bin/env bash
# auto-format-touched.sh
# Codex PostToolUse hook for apply_patch (also matched by Edit|Write aliases).
# Runs Spotless against the touched file (if it's Java) so the harness format gate passes.
# Best effort — don't fail the agent's edit on a formatting error; surface it instead.

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

  # Only run if Maven and Spotless are configured.
  if [ -f pom.xml ] && grep -q 'spotless-maven-plugin' pom.xml; then
    mvn -q spotless:apply -DspotlessFiles="$file_path" >/dev/null 2>&1 || \
      echo "WARN: Spotless apply failed on $file_path (continuing)" >&2
  fi
done <<< "$paths"

exit 0
