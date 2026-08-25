# Design D Starters — one dependency-graph structure, six languages

Design D won the experiment because its manifest models **edges between units**,
not just a list of units — so duplication becomes a *graph property* instead of a
reading exercise. Its weakness was that `graph.json` was hand-written and drifted.

These starters fix that. The insight:

> **The dependency graph already exists in every modern language — it is the
> module/import system.** You don't author it; you *derive* the manifest from it,
> and you add the one thing the language does not give you: a rule that a
> cross-cutting primitive has exactly one home.

Every starter is the same tiny "Taskly-lite" (core id-encoder + validators, a
`users` domain, a `tasks` domain, a composition root) in six languages, each
built from that language's own graph mechanism.

## The three rules

1. **One home per cross-cutting concern.** The base62 encoder and validators live
   only in `core`. This is what makes the duplicate-encoder bug *unwritable*.
2. **Domains depend on core, never on each other.** The composition root is the
   only layer allowed broad imports.
3. **The manifest is generated from the real module graph**, and CI fails if code
   changed without regenerating it. A derived manifest cannot drift.

## How each language provides the graph

| Language | Typed edges come from | Boundary enforcer | Manifest source |
|---|---|---|---|
| **Python** | package imports | `.importlinter` contracts + stdlib `ast` checker | `ast` walk → `manifest.json` |
| **TypeScript** | tsconfig **project references** | `.dependency-cruiser.js` + stdlib Node checker | import scan → `manifest.json` |
| **Next.js** | App-router graph + `"use client"` boundary | `eslint-plugin-boundaries` config + stdlib checker | module scan → `MANIFEST.generated.json` |
| **Rust** | **Cargo workspace** crate deps | `xtask boundary-lint` over `Cargo.toml` graph | `/// capability:` markers + dep table → `MANIFEST.md` |
| **Java** | **JPMS `module-info.java`** `requires`/`exports` — compiler-enforced | `BoundaryCheck` over `module-info` | module scan → `manifest.json` |
| **Pascal** | **unit `uses` clauses** — an explicit dependency declaration | `boundary_lint.sh` parsing `uses` | `uses` graph → `manifest.json` |

Java and Pascal are notable: `module-info.java` and the `uses` clause *are*
Design D expressed natively, and in Java's case the **compiler itself** rejects a
forbidden edge before any linter runs.

## Verified, not assumed

Every enforcer was adversarially tested — a violation was injected, the lint was
required to fail, then the change was reverted:

| Starter | CI green | Rejects domain→domain edge | Rejects duplicate primitive |
|---|---|---|---|
| Python | ✅ | ✅ | ✅ (name **and** signature) |
| TypeScript | ✅ | ✅ | ✅ |
| Next.js | ✅ | ✅ | ✅ |
| Rust | ✅ (15 tests) | ✅ | ✅ |
| Java | ✅ | ✅ | ✅ |
| Pascal | lint+manifest ✅ | ✅ | ✅ (name **and** signature) |

*Pascal's build step needs `fpc`, which is not installed here; its lint and
manifest gates run and pass without it.*

### A finding worth keeping

Testing exposed **two duplicate-detection strategies with opposite blind spots**:

- **Name-based** (matches `to_base62`, `Base62Encode`) catches a same-name
  redefinition but is **blind to a renamed copy**.
- **Signature-based** (matches the alphabet literal or `% 62` arithmetic) catches
  a renamed copy but misses a stub.

This matters because the bug planted in the original experiment *was* a renamed
copy — `genid` vs `encode`. A name-only enforcer would have missed the very bug
this project is about. Python and Pascal originally shipped name-only rules and
were **fixed to check both**; the other four already did.

## Run any of them

```bash
cd python     && make ci    # build + test + boundary-lint + manifest-drift-check
cd typescript && make ci
cd nextjs     && make ci
cd java       && make ci
cd rust       && cargo test --workspace   # or: just ci
cd pascal     && make ci    # build step requires fpc
```

Each starter's own `README.md` maps its files back to Design D in detail.

## Adapting this to a real project

The starters are deliberately dependency-free so the *structure* is the subject.
In a real repo, swap the stdlib checkers for the ecosystem tools they mirror —
`import-linter` (Python), `dependency-cruiser` / `eslint-plugin-boundaries`
(TS/Next), ArchUnit (Java) — and keep the generated-manifest drift check exactly
as-is. The rules do not change; only the enforcer does.
