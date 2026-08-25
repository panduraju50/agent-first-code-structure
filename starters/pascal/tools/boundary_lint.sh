#!/usr/bin/env bash
# boundary_lint.sh — the Design D boundary enforcer.
#
# Two rules, both read straight off the real `uses` graph (see lib_graph.sh),
# nothing hand-maintained:
#
#   (a) a domain unit (anything under src/ that isn't core.pas or the
#       `program` root) must not `uses` another domain unit. Only core and
#       the composition root may be depended on by a domain.
#
#   (b) no file other than src/core.pas may define a function/procedure
#       whose name matches one of core.pas's own primitives (Base62Encode,
#       IsNonEmptyTitle, IsValidEmail, and anything added there later —
#       the list is read from core.pas itself, never hardcoded here).
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=./lib_graph.sh
source tools/lib_graph.sh

CORE_FILE="$SRC_DIR/core.pas"
errors=0

echo "== boundary-lint: domain independence (no domain-to-domain uses) =="
for f in $(list_src_files); do
  kind="$(classify "$f")"
  [ "$kind" = "domain" ] || continue
  self="$(unit_name_of "$f")"

  while IFS= read -r used; do
    [ -z "$used" ] && continue
    used_file="$(find_file_for_unit "$used" || true)"
    [ -z "$used_file" ] && continue   # not declared in this repo (e.g. SysUtils) -> external, ignore

    used_kind="$(classify "$used_file")"
    if [ "$used_kind" = "domain" ] && [ "$used" != "$self" ]; then
      echo "ERROR: $f (unit $self) uses domain unit $used ($used_file)." >&2
      echo "       Domains may depend on core only, never on each other." >&2
      errors=$((errors + 1))
    fi
  done < <(uses_of "$f")
done

echo "== boundary-lint: no duplicate primitives outside core =="
while IFS= read -r prim; do
  [ -z "$prim" ] && continue
  for f in $(list_src_files); do
    [ "$f" = "$CORE_FILE" ] && continue
    if grep -qE "^[[:space:]]*(function|procedure)[[:space:]]+${prim}\\b" "$f"; then
      echo "ERROR: $f redefines '$prim', which is owned by $CORE_FILE." >&2
      echo "       core.pas is the only home for this primitive." >&2
      errors=$((errors + 1))
    fi
  done
done < <(primitives_of "$CORE_FILE")

# The name rule above only catches a copy that kept core's name. A *renamed*
# copy is caught here instead, by its two behavioural tells: core's base62
# alphabet literal, and base62-radix arithmetic (mod/div 62).
echo "== boundary-lint: no re-implemented base62 codec outside core =="
B62_ALPHABET='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
for f in $(list_src_files); do
  [ "$f" = "$CORE_FILE" ] && continue
  if grep -qF "$B62_ALPHABET" "$f"; then
    echo "ERROR: $f contains core's base62 alphabet literal." >&2
    echo "       The encoder has one home ($CORE_FILE); use it instead of copying it." >&2
    errors=$((errors + 1))
  elif grep -qE '\b(mod|div)[[:space:]]+62\b' "$f"; then
    echo "ERROR: $f performs base62-radix arithmetic (mod/div 62) outside $CORE_FILE." >&2
    echo "       Looks like a duplicate encoder." >&2
    errors=$((errors + 1))
  fi
done

echo "=========================================="
if [ "$errors" -gt 0 ]; then
  echo "boundary-lint FAILED: $errors violation(s)" >&2
  exit 1
fi
echo "boundary-lint OK: no domain-to-domain edges, no duplicate primitives"
