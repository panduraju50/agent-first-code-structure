#!/usr/bin/env python3
"""Generate manifest.json from the REAL module graph — never hand-authored.

manifest.json records:
  - capabilities: every public top-level function/class -> the one file
    that defines it (derived from core/, domains/*, app/ source, excluding
    tests).
  - edges: every project-local "module A imports module B" edge, derived
    the same way tools/boundary_check.py derives its view of the graph.

Run with --check to verify the committed manifest.json still matches what
the source tree would generate (the CI drift-check gate: fails if code
changed but nobody ran `make manifest`).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from tools._pygraph import (
    discover_py_files,
    module_name_for_path,
    parse_imports_raw,
    repo_root,
    resolve_project_local,
    top_level_defs,
)

MANIFEST_PATH_NAME = "manifest.json"


def build_manifest(root: Path) -> dict:
    files = discover_py_files(root, include_tests=False)
    known_modules = {module_name_for_path(root, p) for p in files}

    capabilities = {}
    for path in files:
        rel = path.relative_to(root).as_posix()
        module = module_name_for_path(root, path)
        for name, _lineno, kind in top_level_defs(path):
            if name.startswith("_"):
                continue
            capabilities[f"{module}.{name}"] = {"file": rel, "kind": kind}

    edges = set()
    for path in files:
        module = module_name_for_path(root, path)
        seen = set()
        for candidate in parse_imports_raw(path):
            target = resolve_project_local(candidate, known_modules)
            if target is None or target == module or target in seen:
                continue
            seen.add(target)
            edges.add((module, target))

    return {
        "generated_by": "tools/gen_manifest.py (auto-generated - do not hand-edit)",
        "capabilities": dict(sorted(capabilities.items())),
        "edges": [
            {"from": a, "to": b} for a, b in sorted(edges)
        ],
    }


def render(manifest: dict) -> str:
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def main() -> int:
    root = repo_root()
    manifest = build_manifest(root)
    rendered = render(manifest)
    manifest_path = root / MANIFEST_PATH_NAME

    if "--check" in sys.argv[1:]:
        if not manifest_path.exists():
            print(f"manifest_check: {MANIFEST_PATH_NAME} does not exist. "
                  f"Run `make manifest` and commit it.")
            return 1
        current = manifest_path.read_text(encoding="utf-8")
        if current != rendered:
            print(f"manifest_check: {MANIFEST_PATH_NAME} is stale — the "
                  f"module graph changed but the manifest was not "
                  f"regenerated. Run `make manifest` and commit the diff.")
            import difflib
            diff = difflib.unified_diff(
                current.splitlines(keepends=True),
                rendered.splitlines(keepends=True),
                fromfile=f"{MANIFEST_PATH_NAME} (committed)",
                tofile=f"{MANIFEST_PATH_NAME} (regenerated)",
            )
            sys.stdout.writelines(diff)
            return 1
        print(f"manifest_check: {MANIFEST_PATH_NAME} is up to date "
              f"({len(manifest['capabilities'])} capabilities, "
              f"{len(manifest['edges'])} edges)")
        return 0

    manifest_path.write_text(rendered, encoding="utf-8")
    print(f"wrote {MANIFEST_PATH_NAME} "
          f"({len(manifest['capabilities'])} capabilities, "
          f"{len(manifest['edges'])} edges)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
