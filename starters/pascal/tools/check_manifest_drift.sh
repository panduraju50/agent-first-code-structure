#!/usr/bin/env bash
# check_manifest_drift.sh — CI gate: fails if manifest.json is stale.
#
# Regenerates the manifest into a temp file and diffs it against the
# committed manifest.json. Any change to src/*.pas that isn't followed by
# `make manifest` (and committing the result) fails this check.
set -euo pipefail
cd "$(dirname "$0")/.."

tmp="$(mktemp -t manifest_check.XXXXXX)"
trap 'rm -f "$tmp"' EXIT

./tools/gen_manifest.sh > "$tmp"

if [ ! -f manifest.json ]; then
  echo "manifest-drift-check FAILED: manifest.json does not exist. Run 'make manifest'." >&2
  exit 1
fi

if ! diff -u manifest.json "$tmp" > "$tmp.diff" 2>&1; then
  cat "$tmp.diff"
  rm -f "$tmp.diff"
  echo "----------------------------------------" >&2
  echo "manifest-drift-check FAILED: manifest.json is out of date with src/*.pas." >&2
  echo "Run 'make manifest' and commit the result." >&2
  exit 1
fi
rm -f "$tmp.diff"

echo "manifest-drift-check OK: manifest.json matches the generated module graph"
