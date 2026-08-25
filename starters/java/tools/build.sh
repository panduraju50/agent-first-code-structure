#!/usr/bin/env bash
# Compiles the plain-Java tools (BoundaryCheck, ManifestGen) to tools/out.
# These are unnamed-module classpath tools — they inspect the module graph
# from the outside, so they deliberately live outside the JPMS graph itself.
set -euo pipefail
cd "$(dirname "$0")"

rm -rf out
mkdir -p out
javac -d out $(find src -name '*.java')
