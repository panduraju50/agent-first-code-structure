#!/usr/bin/env bash
# The one command CI (and you) run: build + test + boundary-lint +
# manifest-drift-check. Entirely offline — only javac/java from the JDK.
set -euo pipefail
cd "$(dirname "$0")"

echo "### 1/4 build ###"
./build.sh

echo
echo "### 2/4 test ###"
./test.sh

echo
echo "### 3/4 boundary-lint ###"
./tools/boundary-check.sh

echo
echo "### 4/4 manifest-drift-check ###"
./tools/generate-manifest.sh --check

echo
echo "CI OK"
