#!/usr/bin/env bash

set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <base-commit>" >&2
  exit 2
fi

base_commit="$1"
if ! git cat-file -e "${base_commit}^{commit}" 2>/dev/null; then
  echo "base commit is unavailable: ${base_commit}" >&2
  exit 2
fi

diff_range="${base_commit}...HEAD"
git diff --check "${diff_range}"

markdown_paths="$(mktemp)"
trap 'rm -f "$markdown_paths"' EXIT HUP INT TERM
git diff --name-only --diff-filter=ACMR -z "${diff_range}" -- '*.md' >"$markdown_paths"

if [ ! -s "$markdown_paths" ]; then
  echo "No changed Markdown files to lint."
  exit 0
fi

xargs -0 npx --yes markdownlint-cli2@0.18.1 -- <"$markdown_paths"
