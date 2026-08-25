# Taskly-lite (Rust) -- Design D starter

A minimal "Taskly-lite" (users + tasks) built as a Cargo workspace whose
organizing principle is an **explicit, typed dependency graph** -- Design D.
The point of this repo is not the todo-app functionality; it's that the
allowed dependency graph is declared once, in a place the compiler and a
small tool both read, and it is impossible to silently drift from it.

```
starters/rust/
  Cargo.toml            workspace: crates/core, crates/users, crates/tasks, crates/app, xtask
  crates/core/           <- ONE home for cross-cutting primitives
    src/base62.rs         base62 id encoder/decoder
    src/validate.rs       title + email validators
  crates/users/           <- domain: depends on core ONLY
  crates/tasks/           <- domain: depends on core ONLY
  crates/app/             <- composition root: the only crate allowed to
                             depend on more than one domain
  xtask/                  boundary enforcer + manifest generator (no deps)
  MANIFEST.md             GENERATED: capability -> file, and dep edges
  justfile, .github/workflows/ci.yml   build + test + lint + drift-check
```

Zero crates.io dependencies anywhere in the workspace (see every
`Cargo.toml`). Nothing here needs registry access, so `cargo build/test`
and `xtask` all run fully offline with `--offline`.

## Where the typed edges actually live

In a Cargo workspace, "depends on" is not a suggestion -- it's a compiler
fact. Each crate's `[dependencies]` table in its `Cargo.toml` **is** an edge
in the dependency graph, and `rustc`/`cargo` refuse to compile code that
`use`s a crate not listed there. That's what makes this "Design D" rather
than just "a Rust workspace with a nice README": the graph is typed and
compiler-enforced, not a diagram that can rot.

| crate | package name | `[dependencies]` | meaning |
|---|---|---|---|
| `crates/core` | `corelib` | *(empty)* | leaf of the graph; depends on nothing workspace-local |
| `crates/users` | `users` | `corelib = { path = "../core" }` | domain -> core only |
| `crates/tasks` | `tasks` | `corelib = { path = "../core" }` | domain -> core only |
| `crates/app` | `app` | `corelib`, `users`, `tasks` | composition root: the only crate allowed to see more than one domain |
| `xtask` | `xtask` | *(empty, stdlib only)* | reads the graph above; not part of the product |

(The package inside `crates/core` is named `corelib`, not `core` -- naming
it literally `core` would collide with Rust's own sysroot `core` crate at
every `use core::...` call site. The *directory* is still `crates/core` to
match the required layout.)

Notice `crates/tasks` has no dependency on `users` at all, and a `Task`
references its assignee as an opaque `assignee_id: Option<String>`, never
as a `users::User`. That absence is the "domains may depend on core but not
each other" rule made real: there is no `users` line in
`crates/tasks/Cargo.toml` to remove, because the design never needed one.

## Rule 1 -- one home per cross-cutting concern

`corelib::base62` is the only base62 encoder in the workspace, and
`corelib::validate` is the only place `validate_title`/`validate_email`
are defined. `users` and `tasks` both call into `corelib` for id
generation and input validation (see `crates/users/src/lib.rs` and
`crates/tasks/src/lib.rs`) -- they do not reimplement either.

## Rule 2 -- domains don't depend on each other; app is the composition root

Enforced two ways simultaneously:

- **Structurally**: `crates/users/Cargo.toml` and `crates/tasks/Cargo.toml`
  each have exactly one workspace dependency, `corelib`. There is nothing
  to `use` from the other domain even if someone tried -- the compiler
  would reject `use tasks::...` inside `crates/users/src` with "unresolved
  import" because `tasks` was never added to `[dependencies]`.
- **By convention + lint**: `crates/app` is the one crate whose
  `Cargo.toml` legitimately lists more than one domain (`users` *and*
  `tasks`, plus `corelib`). `xtask boundary-lint` checks this explicitly.

## Rule 3 -- the boundary enforcer (`xtask boundary-lint`)

`xtask/src/main.rs` is the idiomatic Rust answer to "a tool that reads
`cargo metadata`-shaped info and asserts the graph": rather than shelling
out to `cargo metadata` (which would need JSON parsing) it reads each
crate's `Cargo.toml` directly with a small hand-rolled reader (no `toml`
crate -- see "no external dependencies" below) and asserts, from the
literal files on disk:

1. **No domain-to-domain edge**: for each domain in `{users, tasks}`,
   the *other* domain's package name must not appear in its workspace
   dependencies.
2. **Domain deps == exactly `{corelib}`**: not more (e.g. accidentally
   depending on `app`), not less (e.g. silently losing the core dependency
   and reimplementing something).
3. **Core depends on nothing workspace-local** -- it must stay the leaf.
4. **No duplicate base62 implementation**: every `crates/*/src/**/*.rs`
   file *outside* `crates/core` is grepped for base62-shaped markers
   (`base62`, `% 62`, `ALPHABET`, ...). Any hit fails the build with the
   offending file and line -- this is the grep-based "SHOULD-use-but-does-not"
   rule from the assignment: a domain crate *should* call
   `corelib::base62::encode` and never accidentally reinvent it, and this
   lint is what turns "should" into "will fail CI if it doesn't".

Run it directly:

```sh
cargo run -p xtask --offline -- boundary-lint
```

To see it actually catch something (rather than just trusting the code),
try breaking the graph yourself and watch it fail:

```sh
# from starters/rust/
echo 'tasks = { path = "../tasks" }' >> crates/users/Cargo.toml
cargo run -p xtask --offline -- boundary-lint
# ERROR: boundary violation: crates/users/Cargo.toml depends on crate 'tasks' ...
# ERROR: boundary violation: crates/users/Cargo.toml workspace deps are {"corelib", "tasks"} ...
git checkout -- crates/users/Cargo.toml   # (or just delete the line you added)
```

`xtask`'s own test suite (`xtask/src/main.rs`, `mod tests`) also asserts
`boundary_lint(&workspace_root()) == Ok(())` on this exact repo, so a
regression here fails `cargo test` too, not just the standalone lint step.

## Rule 4 -- the generated manifest (`MANIFEST.md`)

`MANIFEST.md` at the workspace root is **not hand-authored**. It's produced
by `xtask manifest-gen`, which:

1. Walks every crate's `src/` tree looking for `/// capability: <name>` doc
   comments (a lightweight, greppable convention used throughout
   `crates/core`, `crates/users`, and `crates/tasks`), and records the
   file + line number of the item each comment documents.
2. Re-parses every crate's `Cargo.toml` (same reader `boundary-lint` uses)
   to list the real, current dependency edges.
3. Renders both into `MANIFEST.md` as two tables: **capability -> owning
   file** and **dependency edges**.

Because it's derived, it can go stale the moment someone adds a capability
or changes a dependency without regenerating it -- which is exactly what
`xtask manifest-check` catches: it regenerates the manifest **in memory**
and fails if that differs one byte from the `MANIFEST.md` committed to the
repo. This is the drift check from rule 4 ("fails if code changed but the
manifest was not regenerated"), and it also has its own `#[test]` in
`xtask/src/main.rs` so a plain `cargo test` catches drift too.

```sh
cargo run -p xtask --offline -- manifest-gen     # regenerate MANIFEST.md
cargo run -p xtask --offline -- manifest-check   # fail if it's stale
```

## Rule 5 -- at least one test per domain

- `crates/users/src/lib.rs` -- `create_and_get_roundtrip`,
  `rejects_invalid_email_via_core_validator`, `rejects_empty_name`,
  `get_unknown_id_returns_none`.
- `crates/tasks/src/lib.rs` -- `create_list_and_assign`,
  `rejects_empty_title_via_core_validator`, `assign_unknown_task_is_an_error`.
- `crates/core/src/{base62,validate}.rs` also carry their own unit tests
  for the primitives domains depend on.
- `xtask/src/main.rs` tests the enforcer and the manifest against this
  very repo, so the tooling is covered too, not just the product code.

## Rule 7 -- one command for everything

```sh
just ci          # build + test + boundary-lint + manifest-check
# or, without `just`:
cargo build --workspace --offline
cargo test --workspace --offline
cargo run -p xtask --offline -- boundary-lint
cargo run -p xtask --offline -- manifest-check
```

`.github/workflows/ci.yml` runs the same four steps on every push/PR.

## Why xtask has zero dependencies

The assignment asks to keep dependencies to the standard toolchain +
stdlib, with no external cargo crates and no network installs. `xtask`
honors that literally: no `toml` crate for reading `Cargo.toml`, no `clap`
for argument parsing, no `walkdir` for directory traversal -- just
`std::fs`, `std::path`, and a ~15-line hand-rolled TOML-section reader that
is good enough for *this workspace's own, hand-written* manifests. That
reader is not a general TOML parser and does not try to be one; it exists
to prove the boundary check is real code reading real files, not a stub.

## Try it

```sh
cargo run -p app --offline
```

```
created user 1 <ada@example.com> "Ada Lovelace"

tasks:
  [1] 'Write the first published algorithm' assigned_to=Some("1")
  [2] 'Review Babbage's engine notes' assigned_to=None

looked up assignee of 'Write the first published algorithm': User { id: "1", name: "Ada Lovelace", email: "ada@example.com" }

'Review Babbage's engine notes' remains unassigned: true
```
