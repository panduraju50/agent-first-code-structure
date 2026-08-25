# scaffold.py — one spec, an agent-first skeleton in any language

A single stdlib-only Python file. You describe the system as a **graph**; it emits
a working skeleton in Go, Rust, Java, Python, or TypeScript, plus a generated
manifest and a checker that re-verifies the code against the spec.

It combines two of the structures explored in this repo:

- **Design D — the dependency graph.** The spec declares typed edges between
  units, and the emitted project expresses those edges in the *target language's
  own dependency mechanism*: Cargo `[dependencies]`, `module-info.java`
  `requires`, Go package imports, TS project references, Python imports. The
  graph is not a side-file that drifts — it is the thing the compiler already
  enforces.
- **Design I — effect tags.** Every unit declares its side effects. Effects
  propagate along the edges, so a unit that *transitively* has an effect it did
  not declare is a spec error, and infrastructure is **derived** from the effect
  union instead of hand-maintained.

## Use

```bash
python3 scaffold.py init  taskly.spec.json                        # example spec
python3 scaffold.py check taskly.spec.json                        # validate the graph
python3 scaffold.py gen   taskly.spec.json --lang go --out out/go
python3 scaffold.py verify taskly.spec.json --lang go --out out/go
```

## The spec is the graph

```json
{"name": "users", "layer": "domains",
 "capabilities": ["create_user", "get_user"],
 "effects": ["store"],
 "uses": ["ids", "validation"]}
```

Units are nodes, `uses` are edges, `layer` is one of `core` / `domains` / `app`.

## Rules enforced before any code exists

A spec that breaks these cannot be generated, so the structure is correct by
construction rather than by review:

| Rule | From | Rejects |
|---|---|---|
| One home per capability | D | the duplicate-primitive bug class, *at spec time* |
| No domain → domain edges | D | cross-domain coupling |
| Core depends on nothing outward | D | inverted layering |
| No dependency cycles | D | DFS over the edges |
| Declared effects ⊇ transitive effects | I | an undeclared side effect |
| Known effect names only | I | typos in the effect vocabulary |

Verified — each of these is rejected:

```
domain->domain edge     'users' uses 'tasks' — forbidden
duplicate capability    'encode_id' owned by both 'ids' and 'tasks'
core depends on domain  core must not depend on outer layers
undeclared effect       declares [] but transitively has ['net', 'store']
unknown effect name     unknown effect(s) ['telepathy']
```

## Edges become native dependency declarations

| Language | Edges are expressed as | Compiles |
|---|---|---|
| Go | package imports under `internal/` | `go build ./...` ✅ |
| Rust | Cargo workspace path dependencies | `cargo build` ✅ |
| Java | `module-info.java` `requires` / `exports` | `javac -m` ✅ |
| Python | package imports | import ✅ |
| TypeScript | tsconfig `references` | generated |

Java is the strongest case: `javac` itself rejects a forbidden edge, before any
linter runs.

## Drift is closed in both directions

`verify` re-reads the emitted code and fails when reality and spec disagree.
Both paths are tested:

- an illegal import hand-added to emitted Go → `'users' -> 'tasks' is not a
  declared edge in the spec`
- an edited `MANIFEST.json` → `MANIFEST.json is stale — regenerate it (drift)`

This is the fix for the original Design D weakness: the hand-written `graph.json`
drifted. Here the manifest is derived, so it cannot.

## Committed examples

`examples/` holds the output of the example spec in all five languages —
committed so you can read the emitted shape without running anything. Every file
there is generated; nothing is hand-edited. Go, Rust, Java and Python were
compiled from that directory to confirm the emitted graph is real.

Regenerate any of them with:

```bash
python3 scaffold.py gen taskly.spec.json --lang rust --out examples/rust
```

## Adding a language

Write one emitter returning `{path: content}`, register it in `EMITTERS`, and add
one regex to `IMPORT_PATTERNS` so `verify` can read that language's imports.
Nothing else changes.

## What this does and does not show

It shows the D+I rules can be made **mechanically enforceable** across very
different languages, and that the enforcement can be grounded in each toolchain's
existing dependency model rather than bolted on.

It does **not** show that these rules produce better code. That question is still
open — see the limitations discussion in the repo root. This is a tool built on a
hypothesis, not evidence for it.
