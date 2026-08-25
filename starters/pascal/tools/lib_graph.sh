#!/usr/bin/env bash
# lib_graph.sh — shared parsing of the Pascal module graph.
#
# Design D's typed edges ARE the `unit`/`program` name and the `uses` clause
# of every .pas file: that's not a metaphor imposed on top of the code, it's
# literally how fpc resolves dependencies. This library reads exactly that —
# nothing hand-maintained — so boundary_lint.sh and gen_manifest.sh both work
# off the real graph. Sourced by other tools/*.sh scripts, not run directly.
#
# Written against bash 3.2 semantics on purpose (no associative arrays, no
# `mapfile`): the default /bin/bash on macOS is still 3.2, and this repo's
# tooling should run there without asking anyone to install a newer bash.

SRC_DIR="${SRC_DIR:-src}"

# unit_name_of FILE -> the name after `unit` or `program` in FILE
unit_name_of() {
  local file="$1"
  grep -m1 -E '^(unit|program)[[:space:]]+[A-Za-z_][A-Za-z0-9_]*[[:space:]]*;' "$file" \
    | sed -E 's/^(unit|program)[[:space:]]+([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*;.*/\2/'
}

# uses_of FILE -> one unit name per line, from FILE's (single-line) uses clause
uses_of() {
  local file="$1"
  grep -m1 -E '^[[:space:]]*uses[[:space:]]' "$file" \
    | sed -E 's/^[[:space:]]*uses[[:space:]]+//; s/;.*$//' \
    | tr ',' '\n' \
    | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' \
    | sed '/^$/d'
}

# primitives_of FILE -> function/procedure names declared in FILE's interface
# section (between `interface` and `implementation`). Scoped to the interface
# on purpose: that's the public capability list. Without this scope, a unit's
# implementation section would re-match its own interface declarations and
# every capability would be double-counted.
primitives_of() {
  local file="$1"
  awk '/^interface[[:space:]]*$/ {flag=1; next} /^implementation[[:space:]]*$/ {flag=0} flag' "$file" \
    | grep -E '^[[:space:]]*(function|procedure)[[:space:]]+[A-Za-z_][A-Za-z0-9_]*' \
    | sed -E 's/^[[:space:]]*(function|procedure)[[:space:]]+([A-Za-z_][A-Za-z0-9_]*).*/\2/'
}

# list_src_files -> every .pas file under SRC_DIR, one per line, sorted
list_src_files() {
  find "$SRC_DIR" -maxdepth 1 -name '*.pas' | sort
}

# classify FILE -> "core" | "root" | "domain"
#   core   = the one file that owns cross-cutting primitives (src/core.pas)
#   root   = the composition root (a `program`, e.g. src/app.pas)
#   domain = everything else under src/ (a `unit` that isn't core)
classify() {
  local file="$1"
  if [ "$file" = "$SRC_DIR/core.pas" ]; then
    echo "core"
  elif grep -qE '^program[[:space:]]' "$file"; then
    echo "root"
  else
    echo "domain"
  fi
}

# find_file_for_unit NAME -> the src/*.pas file that declares `unit NAME;` or
# `program NAME;`. Prints nothing (and returns 1) for names not declared in
# this repo, e.g. stdlib units like SysUtils — those are external, not part
# of the graph this tool enforces.
find_file_for_unit() {
  local name="$1" f
  for f in $(list_src_files); do
    if [ "$(unit_name_of "$f")" = "$name" ]; then
      echo "$f"
      return 0
    fi
  done
  return 1
}
