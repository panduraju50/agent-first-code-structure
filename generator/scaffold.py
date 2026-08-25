#!/usr/bin/env python3
"""scaffold.py — generate an agent-first project skeleton in any language.

The structure it emits combines two designs from the experiments in this repo:

  Design D (dependency graph)  the spec declares typed edges between units, and
                               the emitted project expresses those edges in the
                               target language's OWN dependency mechanism
                               (Cargo.toml deps, module-info requires, Go
                               packages, TS project references, Python imports).

  Design I (effect tags)       every unit declares its side effects. Effects
                               propagate along the dependency edges, so declared
                               effects can be checked against transitive ones,
                               and infrastructure is *derived* rather than
                               hand-maintained.

One spec in, a working skeleton out — plus a generated manifest and a boundary
checker that re-verifies the emitted code against the spec.

Usage:
    scaffold.py init  <spec.json>                 write an example spec
    scaffold.py check <spec.json>                 validate the spec's graph rules
    scaffold.py gen   <spec.json> --lang go --out DIR
    scaffold.py verify <spec.json> --lang go --out DIR

Stdlib only. Add a language by writing one emitter and registering it in
EMITTERS — nothing else changes.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Spec model
#
# A spec is a graph. Units are nodes; `uses` are edges. Each unit sits in a
# layer, owns named capabilities, and declares its effects.
# --------------------------------------------------------------------------

LAYERS = ("core", "domains", "app")

EXAMPLE_SPEC = {
    "project": "taskly",
    "module": "example.com/taskly",
    "units": [
        {"name": "ids", "layer": "core", "capabilities": ["encode_id"], "effects": [], "uses": []},
        {"name": "validation", "layer": "core", "capabilities": ["validate_email", "validate_title"], "effects": [], "uses": []},
        {"name": "users", "layer": "domains", "capabilities": ["create_user", "get_user"], "effects": ["store"], "uses": ["ids", "validation"]},
        {"name": "tasks", "layer": "domains", "capabilities": ["create_task", "list_tasks"], "effects": ["store"], "uses": ["ids", "validation"]},
        {"name": "notifier", "layer": "domains", "capabilities": ["notify"], "effects": ["net"], "uses": ["ids"]},
        {"name": "app", "layer": "app", "capabilities": ["run"], "effects": ["store", "net"], "uses": ["users", "tasks", "notifier"]},
    ],
}

# effect -> what infrastructure that effect implies
EFFECT_INFRA = {
    "store": "persistent volume or database",
    "net": "network egress",
    "secret": "secret mount",
    "queue": "message queue",
    "fs": "writable filesystem",
}


class SpecError(Exception):
    """A spec that violates the D+I rules."""


def load_spec(path: Path) -> dict:
    spec = json.loads(path.read_text(encoding="utf-8"))
    validate(spec)
    return spec


def units_by_name(spec: dict) -> dict:
    return {u["name"]: u for u in spec["units"]}


# --------------------------------------------------------------------------
# The rules. These are the whole point: a spec that breaks them cannot be
# generated, so the structure is correct by construction rather than by review.
# --------------------------------------------------------------------------

def validate(spec: dict) -> None:
    problems: list[str] = []
    units = spec.get("units", [])
    names = [u["name"] for u in units]
    index = {u["name"]: u for u in units}

    if len(names) != len(set(names)):
        problems.append("duplicate unit names")

    # D: one home per capability. A capability may be owned by exactly one unit.
    owners: dict[str, str] = {}
    for u in units:
        for cap in u.get("capabilities", []):
            if cap in owners:
                problems.append(
                    f"capability '{cap}' is owned by both '{owners[cap]}' and "
                    f"'{u['name']}' — one home per capability"
                )
            owners[cap] = u["name"]

    for u in units:
        layer = u.get("layer")
        if layer not in LAYERS:
            problems.append(f"unit '{u['name']}': unknown layer '{layer}'")
            continue

        for dep in u.get("uses", []):
            if dep not in index:
                problems.append(f"unit '{u['name']}' uses unknown unit '{dep}'")
                continue
            dep_layer = index[dep]["layer"]

            # D: layering. core depends on nothing; domains depend on core only;
            # app is the sole layer allowed to depend on domains.
            if layer == "core" and dep_layer != "core":
                problems.append(
                    f"'{u['name']}' (core) uses '{dep}' ({dep_layer}) — core must not "
                    f"depend on outer layers"
                )
            elif layer == "domains" and dep_layer == "domains":
                problems.append(
                    f"'{u['name']}' uses '{dep}' — domain-to-domain edges are "
                    f"forbidden; both must depend on core only"
                )
            elif layer == "domains" and dep_layer == "app":
                problems.append(f"'{u['name']}' (domain) uses '{dep}' (app) — inverted edge")

    problems.extend(_cycles(index))
    problems.extend(_effect_problems(index))

    if problems:
        raise SpecError("\n".join(f"  - {p}" for p in problems))


def _cycles(index: dict) -> list[str]:
    """Depth-first cycle detection over the `uses` edges."""
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {n: WHITE for n in index}
    found: list[str] = []

    def walk(node: str, trail: list[str]) -> None:
        colour[node] = GREY
        for dep in index[node].get("uses", []):
            if dep not in index:
                continue
            if colour[dep] == GREY:
                cycle = trail[trail.index(dep):] if dep in trail else [dep]
                found.append("dependency cycle: " + " -> ".join(cycle + [dep]))
            elif colour[dep] == WHITE:
                walk(dep, trail + [dep])
        colour[node] = BLACK

    for n in index:
        if colour[n] == WHITE:
            walk(n, [n])
    return found


def transitive_effects(index: dict, name: str, seen: set | None = None) -> set:
    """Effects a unit actually has: its own, plus everything it depends on."""
    seen = seen or set()
    if name in seen or name not in index:
        return set()
    seen.add(name)
    effects = set(index[name].get("effects", []))
    for dep in index[name].get("uses", []):
        effects |= transitive_effects(index, dep, seen)
    return effects


def _effect_problems(index: dict) -> list[str]:
    """Design I: a unit must declare every effect it transitively has.

    This is what makes effects reviewable — an undeclared effect is a spec
    error, not something a reader has to notice.
    """
    problems = []
    for name, unit in index.items():
        declared = set(unit.get("effects", []))
        actual = transitive_effects(index, name)
        missing = actual - declared
        if missing:
            problems.append(
                f"unit '{name}' declares effects {sorted(declared)} but "
                f"transitively has {sorted(actual)} — undeclared: {sorted(missing)}"
            )
        unknown = declared - set(EFFECT_INFRA)
        if unknown:
            problems.append(f"unit '{name}': unknown effect(s) {sorted(unknown)}")
    return problems


# --------------------------------------------------------------------------
# Manifest — derived from the spec, never hand-written.
# --------------------------------------------------------------------------

def build_manifest(spec: dict) -> dict:
    index = units_by_name(spec)
    capabilities = [
        {"capability": cap, "unit": u["name"], "layer": u["layer"]}
        for u in spec["units"]
        for cap in u.get("capabilities", [])
    ]
    edges = [
        {"from": u["name"], "to": dep}
        for u in spec["units"]
        for dep in u.get("uses", [])
    ]
    infra = sorted({
        EFFECT_INFRA[e]
        for u in spec["units"]
        for e in transitive_effects(index, u["name"])
        if e in EFFECT_INFRA
    })
    return {
        "generated_by": "scaffold.py — do not hand-edit",
        "project": spec["project"],
        "capabilities": sorted(capabilities, key=lambda c: c["capability"]),
        "edges": sorted(edges, key=lambda e: (e["from"], e["to"])),
        "effects": {
            u["name"]: sorted(transitive_effects(index, u["name"]))
            for u in spec["units"]
        },
        "derived_infrastructure": infra,
    }


# --------------------------------------------------------------------------
# Emitters. One function per language; each returns {relative_path: content}.
#
# Every emitter has the same job: express the spec's edges in the target
# language's native dependency mechanism, and put each unit's effects in a
# header where both a reader and a checker can see them.
# --------------------------------------------------------------------------

def _header(unit: dict, comment: str) -> str:
    caps = ", ".join(unit.get("capabilities", [])) or "(none)"
    uses = ", ".join(unit.get("uses", [])) or "(none)"
    eff = ", ".join(unit.get("effects", [])) or "(none)"
    return (
        f"{comment} unit: {unit['name']} ({unit['layer']})\n"
        f"{comment} capabilities: {caps}\n"
        f"{comment} effects: {eff}\n"
        f"{comment} uses: {uses}\n"
        f"{comment} GENERATED SKELETON — edges are declared in the project spec.\n"
    )


def _fn(name: str) -> str:
    return name


def _camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(p.title() for p in rest)


def _pascal(name: str) -> str:
    return "".join(p.title() for p in name.split("_"))


def emit_go(spec: dict) -> dict:
    """Go: package imports are the graph; `internal/` blocks outside access."""
    mod = spec.get("module", f"example.com/{spec['project']}")
    files = {"go.mod": f"module {mod}\n\ngo 1.21\n"}
    for u in spec["units"]:
        pkg = u["name"]
        if u["layer"] == "app":
            path, header = "cmd/app/main.go", "package main\n\n"
        else:
            path = f"internal/{u['layer']}/{pkg}/{pkg}.go"
            header = f"package {pkg}\n\n"
        imports = "".join(
            f'\t"{mod}/internal/{units_by_name(spec)[d]["layer"]}/{d}"\n'
            for d in u.get("uses", [])
            if units_by_name(spec)[d]["layer"] != "app"
        )
        body = _header(u, "//") + "\n" + header
        if imports:
            body += f"import (\n{imports})\n\n"
            # Go rejects an unused import, so a declared edge must actually be
            # referenced. Anchoring each dependency here keeps the emitted
            # skeleton compilable and proves the edge is real.
            index = units_by_name(spec)
            for d in u.get("uses", []):
                dep = index[d]
                if dep["layer"] == "app" or not dep.get("capabilities"):
                    continue
                body += f"var _ = {d}.{_pascal(dep['capabilities'][0])}\n"
            body += "\n"
        for cap in u.get("capabilities", []):
            fname = _pascal(cap)
            if u["layer"] == "app" and cap == "run":
                body += "func main() {\n\t// composition root: wire the domains here\n}\n\n"
            else:
                body += f"func {fname}() error {{\n\treturn nil // TODO\n}}\n\n"
        files[path] = body
    return files


def emit_rust(spec: dict) -> dict:
    """Rust: a Cargo workspace. Each crate's [dependencies] IS the edge list."""
    members = ", ".join(f'"crates/{u["name"]}"' for u in spec["units"])
    files = {
        "Cargo.toml": f"[workspace]\nresolver = \"2\"\nmembers = [{members}]\n",
    }
    for u in spec["units"]:
        name = u["name"]
        deps = "".join(f'{d} = {{ path = "../{d}" }}\n' for d in u.get("uses", []))
        files[f"crates/{name}/Cargo.toml"] = (
            f'[package]\nname = "{name}"\nversion = "0.1.0"\nedition = "2021"\n\n'
            f"[dependencies]\n{deps}"
        )
        body = _header(u, "//") + "\n"
        for cap in u.get("capabilities", []):
            body += f"pub fn {_fn(cap)}() -> Result<(), String> {{\n    Ok(()) // TODO\n}}\n\n"
        target = "src/main.rs" if u["layer"] == "app" else "src/lib.rs"
        if u["layer"] == "app":
            body += "fn main() {\n    // composition root: wire the domains here\n}\n"
        files[f"crates/{name}/{target}"] = body
    return files


def emit_java(spec: dict) -> dict:
    """Java: module-info.java requires/exports — the compiler enforces the graph."""
    proj = spec["project"]
    files = {}
    for u in spec["units"]:
        name = u["name"]
        mod = f"{proj}.{name}"
        pkg = f"{proj}.{name}"
        requires = "".join(f"    requires {proj}.{d};\n" for d in u.get("uses", []))
        # javac's --module-source-path resolves a module by directory name, so
        # the directory must be the module name, not the bare unit name.
        files[f"{mod}/src/main/java/module-info.java"] = (
            _header(u, "//") + f"\nmodule {mod} {{\n{requires}    exports {pkg};\n}}\n"
        )
        cls = _pascal(name)
        methods = "".join(
            f"    public static void {_camel(cap)}() {{\n        // TODO\n    }}\n\n"
            for cap in u.get("capabilities", [])
        )
        main = ""
        if u["layer"] == "app":
            main = ("    public static void main(String[] args) {\n"
                    "        // composition root: wire the domains here\n    }\n\n")
        files[f"{mod}/src/main/java/{pkg.replace('.', '/')}/{cls}.java"] = (
            _header(u, "//") + f"\npackage {pkg};\n\npublic final class {cls} {{\n"
            f"    private {cls}() {{}}\n\n{main}{methods}}}\n"
        )
    return files


def emit_python(spec: dict) -> dict:
    """Python: package imports are the graph."""
    files = {}
    for u in spec["units"]:
        name, layer = u["name"], u["layer"]
        path = "app/main.py" if layer == "app" else f"{layer}/{name}/__init__.py"
        imports = "".join(
            f"from {units_by_name(spec)[d]['layer']}.{d} import *  # noqa: F401,F403\n"
            for d in u.get("uses", [])
            if units_by_name(spec)[d]["layer"] != "app"
        )
        body = _header(u, "#") + "\n" + imports + ("\n" if imports else "")
        for cap in u.get("capabilities", []):
            body += f"def {_fn(cap)}():\n    raise NotImplementedError\n\n\n"
        if layer == "app":
            body += 'if __name__ == "__main__":\n    pass  # composition root\n'
        files[path] = body
        if layer != "app":
            files[f"{layer}/__init__.py"] = ""
    return files


def emit_typescript(spec: dict) -> dict:
    """TypeScript: tsconfig project references are the build DAG."""
    files = {"tsconfig.base.json": json.dumps(
        {"compilerOptions": {"composite": True, "strict": True, "target": "ES2022",
                             "module": "NodeNext", "declaration": True}}, indent=2) + "\n"}
    for u in spec["units"]:
        name = u["name"]
        refs = [{"path": f"../{d}"} for d in u.get("uses", [])]
        files[f"packages/{name}/tsconfig.json"] = json.dumps(
            {"extends": "../../tsconfig.base.json",
             "compilerOptions": {"outDir": "dist", "rootDir": "src"},
             "include": ["src"], "references": refs}, indent=2) + "\n"
        body = _header(u, "//") + "\n"
        for d in u.get("uses", []):
            body += f'import * as {_camel(d)} from "../../{d}/src/index.js";\n'
        if u.get("uses"):
            body += "\n"
        for cap in u.get("capabilities", []):
            body += f"export function {_camel(cap)}(): void {{\n  // TODO\n}}\n\n"
        files[f"packages/{name}/src/index.ts"] = body
    return files


EMITTERS = {
    "go": emit_go,
    "rust": emit_rust,
    "java": emit_java,
    "python": emit_python,
    "typescript": emit_typescript,
}

# How to find a dependency reference in emitted source, per language. Used by
# `verify` to confirm the real code's edges match the spec's edges.
IMPORT_PATTERNS = {
    "go": re.compile(r'"[^"]*/internal/\w+/(\w+)"'),
    "rust": re.compile(r'^(\w+)\s*=\s*\{\s*path', re.M),
    "java": re.compile(r"^\s*requires\s+[\w.]*?\.?(\w+);", re.M),
    "python": re.compile(r"^from\s+\w+\.(\w+)\s+import", re.M),
    "typescript": re.compile(r'from\s+"\.\./\.\./(\w+)/'),
}


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

def write_files(out: Path, files: dict) -> None:
    for rel, content in files.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def cmd_gen(spec: dict, lang: str, out: Path) -> int:
    emit = EMITTERS[lang]
    files = emit(spec)
    files["MANIFEST.json"] = json.dumps(build_manifest(spec), indent=2) + "\n"
    files["project.spec.json"] = json.dumps(spec, indent=2) + "\n"
    write_files(out, files)
    manifest = build_manifest(spec)
    print(f"generated {len(files)} files for {lang} in {out}")
    print(f"  units: {len(spec['units'])}  "
          f"capabilities: {len(manifest['capabilities'])}  "
          f"edges: {len(manifest['edges'])}")
    if manifest["derived_infrastructure"]:
        print("  infrastructure implied by declared effects:")
        for item in manifest["derived_infrastructure"]:
            print(f"    - {item}")
    return 0


def cmd_verify(spec: dict, lang: str, out: Path) -> int:
    """Re-check emitted code against the spec: no edge the spec doesn't declare."""
    pattern = IMPORT_PATTERNS[lang]
    index = units_by_name(spec)
    declared = {(u["name"], d) for u in spec["units"] for d in u.get("uses", [])}
    known = set(index)
    violations = []

    for path in sorted(out.rglob("*")):
        if not path.is_file() or path.suffix not in {".go", ".rs", ".java", ".py", ".ts", ".toml"}:
            continue
        owner = _owner_of(path, out, index)
        if owner is None:
            continue
        for found in pattern.findall(path.read_text(encoding="utf-8")):
            if found not in known or found == owner:
                continue
            if (owner, found) not in declared:
                violations.append(
                    f"{path.relative_to(out)}: '{owner}' -> '{found}' is not a "
                    f"declared edge in the spec"
                )

    manifest_path = out / "MANIFEST.json"
    if manifest_path.exists():
        current = json.loads(manifest_path.read_text(encoding="utf-8"))
        if current != build_manifest(spec):
            violations.append("MANIFEST.json is stale — regenerate it (drift)")
    else:
        violations.append("MANIFEST.json is missing")

    if violations:
        print(f"verify: {len(violations)} violation(s)", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1
    print(f"verify: OK — every edge in the emitted code is declared in the spec")
    return 0


def _owner_of(path: Path, out: Path, index: dict) -> str | None:
    """Which unit does this emitted file belong to?"""
    parts = path.relative_to(out).parts
    for part in parts:
        stem = part[:-len(path.suffix)] if part.endswith(path.suffix) else part
        if stem in index:
            return stem
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="write an example spec")
    p_init.add_argument("spec")

    p_check = sub.add_parser("check", help="validate a spec against the D+I rules")
    p_check.add_argument("spec")

    for name, helptext in (("gen", "generate a skeleton"), ("verify", "check emitted code against the spec")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("spec")
        p.add_argument("--lang", required=True, choices=sorted(EMITTERS))
        p.add_argument("--out", required=True)

    args = ap.parse_args()
    spec_path = Path(args.spec)

    if args.cmd == "init":
        spec_path.write_text(json.dumps(EXAMPLE_SPEC, indent=2) + "\n", encoding="utf-8")
        print(f"wrote example spec to {spec_path}")
        return 0

    try:
        spec = load_spec(spec_path)
    except SpecError as e:
        print(f"spec rejected — the graph rules are violated:\n{e}", file=sys.stderr)
        return 1

    if args.cmd == "check":
        m = build_manifest(spec)
        print(f"spec OK: {len(spec['units'])} units, {len(m['edges'])} edges, "
              f"{len(m['capabilities'])} capabilities, no cycles, effects consistent")
        return 0
    if args.cmd == "gen":
        return cmd_gen(spec, args.lang, Path(args.out))
    return cmd_verify(spec, args.lang, Path(args.out))


if __name__ == "__main__":
    sys.exit(main())
