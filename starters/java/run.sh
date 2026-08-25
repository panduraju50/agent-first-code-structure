#!/usr/bin/env bash
# Runs the composition root scenario. Requires build.sh to have run first.
set -euo pipefail
cd "$(dirname "$0")"

java --module-path out -m taskly.app/taskly.app.Main
