#!/usr/bin/env bash

set -eu

if [ "$#" -ne 4 ]; then
  echo "usage: $0 <event-name> <pr-base-sha> <before-sha> <head-sha>" >&2
  exit 2
fi

event_name="$1"
pr_base_sha="$2"
before_sha="$3"
head_sha="$4"
zero_sha="0000000000000000000000000000000000000000"

require_commit() {
  commit="$1"
  label="$2"
  if ! git cat-file -e "${commit}^{commit}" 2>/dev/null; then
    echo "${label} commit is unavailable: ${commit}" >&2
    exit 2
  fi
}

require_commit "$head_sha" "head"
markdown_paths="$(mktemp)"
trap 'rm -f "$markdown_paths"' EXIT HUP INT TERM

case "$event_name" in
  pull_request)
    require_commit "$pr_base_sha" "pull request base"
    git diff --check "${pr_base_sha}...${head_sha}"
    git diff --name-only --diff-filter=ACMR -z \
      "${pr_base_sha}...${head_sha}" -- '*.md' >"$markdown_paths"
    ;;
  push)
    if [ "$before_sha" = "$zero_sha" ]; then
      git diff-tree --root --check "$head_sha"
      git diff-tree --root --no-commit-id --name-only -r -z \
        "$head_sha" -- '*.md' >"$markdown_paths"
    else
      require_commit "$before_sha" "push before"
      git diff --check "$before_sha" "$head_sha"
      git diff --name-only --diff-filter=ACMR -z \
        "$before_sha" "$head_sha" -- '*.md' >"$markdown_paths"
    fi
    ;;
  *)
    echo "unsupported GitHub event: ${event_name}" >&2
    exit 2
    ;;
esac

if [ ! -s "$markdown_paths" ]; then
  echo "No changed Markdown files to lint."
  exit 0
fi

xargs -0 npx --yes markdownlint-cli2@0.18.1 -- <"$markdown_paths"
