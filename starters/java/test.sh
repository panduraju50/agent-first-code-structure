#!/usr/bin/env bash
# Compiles each domain module with its test sources layered on top of its
# main sources (same package, same module — no framework, no network
# install) and runs each test's main() as a module. Fails on the first
# test that exits non-zero.
set -euo pipefail
cd "$(dirname "$0")"

rm -rf out-test
mkdir -p out-test

echo "==> compiling taskly.core (for tests)"
javac -d out-test/taskly.core $(find core/src/main/java -name '*.java')

echo "==> compiling taskly.users + tests"
javac -d out-test/taskly.users --module-path out-test \
    $(find users/src/main/java users/src/test/java -name '*.java')

echo "==> compiling taskly.tasks + tests"
javac -d out-test/taskly.tasks --module-path out-test \
    $(find tasks/src/main/java tasks/src/test/java -name '*.java')

echo "==> running taskly.users tests"
java --module-path out-test -m taskly.users/taskly.users.UserServiceTest

echo "==> running taskly.tasks tests"
java --module-path out-test -m taskly.tasks/taskly.tasks.TaskServiceTest

echo "==> all tests passed"
