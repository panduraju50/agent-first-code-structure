#!/usr/bin/env bash
# Runs the Design D boundary enforcer against the repo root.
set -euo pipefail
cd "$(dirname "$0")"

./build.sh
java -cp out tools.BoundaryCheck ..
