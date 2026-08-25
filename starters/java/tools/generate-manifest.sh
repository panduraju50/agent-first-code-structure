#!/usr/bin/env bash
# Regenerates manifest.json at the repo root from the real module graph.
# Usage: tools/generate-manifest.sh          (writes ../manifest.json)
#        tools/generate-manifest.sh --check  (drift check, see ci.sh)
set -euo pipefail
cd "$(dirname "$0")"

./build.sh

if [[ "${1:-}" == "--check" ]]; then
    tmp=$(mktemp)
    java -cp out tools.ManifestGen .. > "$tmp"
    if diff -u ../manifest.json "$tmp" > /dev/null; then
        echo "manifest-drift-check: OK — manifest.json matches the generated source of truth"
        rm -f "$tmp"
    else
        echo "manifest-drift-check: FAILED — manifest.json is stale."
        echo "The module graph or source changed but manifest.json was not regenerated."
        echo "Diff (committed manifest.json vs freshly generated):"
        diff -u ../manifest.json "$tmp" || true
        echo
        echo "Fix: run tools/generate-manifest.sh (no flag) and commit the result."
        rm -f "$tmp"
        exit 1
    fi
else
    java -cp out tools.ManifestGen .. > ../manifest.json
    echo "manifest.json regenerated at $(cd .. && pwd)/manifest.json"
fi
