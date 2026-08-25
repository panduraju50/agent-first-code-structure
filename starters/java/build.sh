#!/usr/bin/env bash
# Compiles the module graph in dependency order, entirely offline with the
# JDK's own javac — no build tool, no network.
#
# Each module is compiled with --module-path pointing at what was already
# built, so a module can only see the modules its module-info.java actually
# requires: this is the compiler-enforced half of Design D. If tasks'
# source ever imported taskly.users.*, this step fails with
# "package taskly.users is not visible" because module-info.java for
# taskly.tasks does not requires it.
set -euo pipefail
cd "$(dirname "$0")"

rm -rf out
mkdir -p out

echo "==> compiling taskly.core"
javac -d out/taskly.core $(find core/src/main/java -name '*.java')

echo "==> compiling taskly.users"
javac -d out/taskly.users --module-path out $(find users/src/main/java -name '*.java')

echo "==> compiling taskly.tasks"
javac -d out/taskly.tasks --module-path out $(find tasks/src/main/java -name '*.java')

echo "==> compiling taskly.app"
javac -d out/taskly.app --module-path out $(find app/src/main/java -name '*.java')

echo "==> build OK (out/taskly.core, out/taskly.users, out/taskly.tasks, out/taskly.app)"
