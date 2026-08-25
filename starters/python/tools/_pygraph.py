"""Stdlib-only helper for walking the project's real Python module graph.

Shared by tools/boundary_check.py (the boundary enforcer) and
tools/gen_manifest.py (the manifest generator) so both tools derive their
view of "what imports what" and "what is defined where" from the same
single parse of the source tree, instead of two hand-maintained lists.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

LAYER_ROOTS = ("core", "domains", "app")


def repo_root() -> Path:
    """The starters/python/ directory (parent of tools/)."""
    return Path(__file__).resolve().parent.parent


def discover_py_files(root: Path, include_tests: bool = True) -> List[Path]:
    """All project .py files under core/, domains/, app/ (sorted, deterministic)."""
    files: List[Path] = []
    for layer in LAYER_ROOTS:
        layer_dir = root / layer
        if not layer_dir.is_dir():
            continue
        for path in layer_dir.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            if not include_tests and "tests" in path.parts:
                continue
            files.append(path)
    return sorted(files)


def module_name_for_path(root: Path, path: Path) -> str:
    """Dotted module name for a file, relative to repo root."""
    rel = path.relative_to(root)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][: -len(".py")]
    return ".".join(parts)


def layer_and_domain(module_name: str) -> Tuple[Optional[str], Optional[str]]:
    """('core'|'domains'|'app'|'tools'|None, domain-name-or-None)."""
    parts = module_name.split(".")
    if not parts or not parts[0]:
        return None, None
    top = parts[0]
    if top == "core":
        return "core", None
    if top == "app":
        return "app", None
    if top == "tools":
        return "tools", None
    if top == "domains":
        return "domains", parts[1] if len(parts) > 1 else None
    return None, None


def _package_for_module(module_name: str, is_init: bool) -> str:
    if is_init:
        return module_name
    if "." not in module_name:
        return ""
    return module_name.rsplit(".", 1)[0]


def _resolve_relative(package: str, level: int, module: Optional[str]) -> str:
    if level == 0:
        # Absolute import: "from domains.tasks import service".
        return module or ""
    pkg_parts = package.split(".") if package else []
    keep = max(len(pkg_parts) - (level - 1), 0)
    base_parts = pkg_parts[:keep]
    if module:
        base_parts = base_parts + module.split(".")
    return ".".join(p for p in base_parts if p)


def parse_imports_raw(path: Path) -> List[str]:
    """All import 'candidate' dotted strings referenced by a file (unresolved)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    is_init = path.name == "__init__.py"
    # module name is computed by the caller normally, but we only need the
    # package for relative-import resolution here.
    root = repo_root()
    module_name = module_name_for_path(root, path)
    package = _package_for_module(module_name, is_init)

    candidates: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                candidates.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            base = _resolve_relative(package, node.level, node.module)
            candidates.append(base)
            for alias in node.names:
                if alias.name == "*":
                    continue
                candidates.append(f"{base}.{alias.name}" if base else alias.name)
    return candidates


def resolve_project_local(candidate: str, known_modules: Iterable[str]) -> Optional[str]:
    """Longest prefix of `candidate` that names a real project module, else None."""
    known = set(known_modules)
    parts = candidate.split(".")
    for i in range(len(parts), 0, -1):
        cand = ".".join(parts[:i])
        if cand in known:
            return cand
    return None


def _kind(node) -> str:
    return "class" if isinstance(node, ast.ClassDef) else "function"


def top_level_defs(path: Path) -> List[Tuple[str, int, str]]:
    """(name, lineno, kind) for module-level def/class statements only."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.append((node.name, node.lineno, _kind(node)))
    return out


def all_defs(path: Path) -> List[Tuple[str, int, str]]:
    """(name, lineno, kind) for every def/class anywhere in the file (any nesting)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.append((node.name, node.lineno, _kind(node)))
    return out
