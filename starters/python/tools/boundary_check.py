#!/usr/bin/env python3
"""Boundary enforcer for Design D.

Fails (non-zero exit) if:
  (a) a domain imports another domain (domains.users <-> domains.tasks), or
  (b) any file outside core/ defines a base62 encoder or one of core's
      other protected primitives (id encoding, title/email validation).

This is the stdlib-only fallback/companion to the .importlinter config in
the repo root: import-linter expresses the same "layers + independent
domains" rules declaratively, but may not be installed in an offline
environment. This script has no third-party dependencies at all, so it is
the enforcement gate that `make boundary-lint` and CI actually rely on.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from tools._pygraph import (
    all_defs,
    discover_py_files,
    layer_and_domain,
    module_name_for_path,
    parse_imports_raw,
    repo_root,
    resolve_project_local,
)

# name -> the one file (relative to repo root) allowed to define it
PROTECTED_DEFS = {
    "to_base62": "core/ids.py",
    "from_base62": "core/ids.py",
    "new_id": "core/ids.py",
    "validate_title": "core/validation.py",
    "validate_email": "core/validation.py",
}


# The base62 alphabet, and base62-radix arithmetic, are the two tells of a
# re-implemented codec. Matching on these (not just on the name) is what catches
# a *renamed* copy — the failure mode a name-only rule is blind to.
B62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
B62_ARITHMETIC = re.compile(r"[%/]\s*62\b|//\s*62\b")


def check_primitive_signatures(root: Path, files) -> list:
    """Catch a re-implemented base62 codec even when it is renamed."""
    violations = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        if rel == "core/ids.py":
            continue
        src = path.read_text(encoding="utf-8")
        if B62_ALPHABET in src:
            violations.append(
                f"{rel}: contains core's base62 alphabet literal — the encoder "
                f"has one home (core/ids.py). Import it instead of copying it."
            )
        elif B62_ARITHMETIC.search(src):
            violations.append(
                f"{rel}: performs base62-radix arithmetic (% 62 or // 62) "
                f"outside core/ids.py — looks like a duplicate encoder."
            )
    return violations


def check_protected_defs(root: Path, files) -> list:
    violations = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        for name, lineno, kind in all_defs(path):
            owner = PROTECTED_DEFS.get(name)
            if owner is not None and rel != owner:
                violations.append(
                    f"{rel}:{lineno}: defines '{name}', which core already owns "
                    f"(one home: {owner}). Import it from core instead of "
                    f"redefining it."
                )
            elif kind == "function" and "base62" in name.lower() and rel != "core/ids.py":
                violations.append(
                    f"{rel}:{lineno}: defines '{name}' — looks like a base62 "
                    f"encoder outside its one home (core/ids.py)."
                )
    return violations


def check_layering_and_domain_independence(root: Path, files) -> list:
    violations = []
    known_modules = {module_name_for_path(root, p) for p in files}

    for path in files:
        rel = path.relative_to(root).as_posix()
        module = module_name_for_path(root, path)
        from_layer, from_domain = layer_and_domain(module)

        seen_targets = set()
        for candidate in parse_imports_raw(path):
            target = resolve_project_local(candidate, known_modules)
            if target is None or target == module or target in seen_targets:
                continue
            seen_targets.add(target)
            to_layer, to_domain = layer_and_domain(target)

            if from_layer == "core" and to_layer in ("domains", "app"):
                violations.append(
                    f"{rel}: core imports '{target}' — core must not depend on "
                    f"domains or app (layering violation)."
                )
            elif from_layer == "domains" and to_layer == "app":
                violations.append(
                    f"{rel}: domain '{from_domain}' imports app ('{target}') — "
                    f"only the composition root may depend on domains, not the "
                    f"reverse."
                )
            elif (
                from_layer == "domains"
                and to_layer == "domains"
                and from_domain != to_domain
            ):
                violations.append(
                    f"{rel}: domain '{from_domain}' imports domain "
                    f"'{to_domain}' ('{target}') — domains must depend on core "
                    f"only, never on each other."
                )
    return violations


def main() -> int:
    root = repo_root()
    files = discover_py_files(root, include_tests=True)

    violations = []
    violations += check_layering_and_domain_independence(root, files)
    violations += check_protected_defs(root, files)
    violations += check_primitive_signatures(root, files)

    if violations:
        print(f"boundary_check: {len(violations)} violation(s) found:\n")
        for v in violations:
            print(f"  - {v}")
        print("\nDesign D rules: domains -> core only; no domain -> domain "
              "edges; app is the only broad-import layer; cross-cutting "
              "primitives (base62 ids, validators) live in core only.")
        return 1

    print(f"boundary_check: OK ({len(files)} files, 0 violations)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
