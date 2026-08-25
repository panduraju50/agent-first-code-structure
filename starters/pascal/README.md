# Taskly-lite (Pascal) — Design D: the dependency graph as the repo structure

A minimal Users + Tasks app whose module boundaries are enforced by the same
mechanism the compiler uses to resolve them: Free Pascal `unit`/`program`
declarations and their `uses` clauses. There is no separate "architecture
description" to keep in sync by hand — the typed edges of the dependency
graph *are* the source code, and the tooling here reads them back out of it.

## Layout

```
src/
  core.pas    unit Core     — base62 id encoder + title/email validators (ONE home)
  users.pas   unit Users    — uses Core only
  tasks.pas   unit Tasks    — uses Core only
  app.pas     program App   — the composition root; the only file allowed to
                              uses both Users and Tasks at once
tests/
  test_core.pas, test_users.pas, test_tasks.pas
tools/
  lib_graph.sh              — shared parsing of unit/program/uses/primitives
  boundary_lint.sh           — the boundary enforcer (rules 1 and 2 below)
  gen_manifest.sh            — derives manifest.json from the real graph
  check_manifest_drift.sh    — CI gate: fails if manifest.json is stale
manifest.json                 — generated; do not hand-edit
Makefile                      — build / test / boundary-lint / manifest-check / ci
.github/workflows/ci.yml      — runs `make ci` on push/PR
```

## Where the typed edges live

In Pascal, a `unit`'s `uses` clause is not documentation of a dependency —
it is the dependency declaration. `fpc` refuses to compile `users.pas` if it
references `Tasks.SomeFunction` without `uses Tasks;`, and it refuses to link
two units that both export the same public identifier into a scope that uses
them both unqualified. That is exactly the "explicit, typed dependency graph"
Design D asks for, provided natively by the language and toolchain, with
nothing bolted on:

- `src/core.pas` declares `unit Core;` and exports `Base62Encode`,
  `IsNonEmptyTitle`, `IsValidEmail` from its `interface` section. It has no
  `uses` clause naming any domain — core depends on nothing in this repo.
- `src/users.pas` declares `unit Users;` and its implementation section says
  `uses Core;` — one edge, Users → Core. It has no way to reach `Tasks` types
  because it never names `Tasks` in a `uses` clause.
- `src/tasks.pas` declares `unit Tasks;` and `uses Core;` — one edge,
  Tasks → Core. Symmetric to Users.
- `src/app.pas` declares `program App;` and `uses SysUtils, Core, Users,
  Tasks;` — the composition root is the one place with edges to both
  domains, because wiring domains together is its entire job.

## How the "should-use-but-does-not" rule is realized

Design D's rule 2 ("domains may depend on core but not on each other") is a
*negative* constraint the compiler alone can't enforce — `fpc` will happily
compile `Users` importing `Tasks` if you write that `uses` clause. The
enforcer is `tools/boundary_lint.sh`, a POSIX-ish shell/awk script (tested
against bash 3.2, the macOS default) that:

1. Reads every `src/*.pas` file's `unit`/`program` name and `uses` clause
   with plain `grep`/`sed` (`tools/lib_graph.sh`).
2. Classifies each file as `core` (`src/core.pas`), `root` (a `program`, i.e.
   `app.pas`), or `domain` (everything else under `src/`) — a structural
   rule, not a hardcoded list of domain names, so a third domain added later
   is picked up automatically.
3. For every `domain` file, checks that none of the units it `uses` are
   themselves classified `domain` (other than itself). If `users.pas` ever
   gains `uses Tasks;`, this fails the build.
4. Separately, reads `core.pas`'s own `interface` section to get the exact
   list of primitives it owns (`Base62Encode`, `IsNonEmptyTitle`,
   `IsValidEmail` — read from the code, not hardcoded), then greps every
   *other* `src/*.pas` file for a top-level `function`/`procedure`
   declaration with the same name. A rogue `function Base62Encode` dropped
   into `users.pas` fails the build even though it would compile fine.

Rule 3, "composition root is the only place allowed broad imports," is
realized by construction: `classify()` only forbids `domain → domain`
edges. `root → domain` and `root → core` are never checked, so `app.pas` is
free to `uses` anything.

Both failure modes were exercised by hand while building this repo (adding
`uses Tasks;` to `users.pas`, and adding a duplicate `function
Base62Encode` to `users.pas`) — `boundary_lint.sh` caught both, with the
exact error messages shown above, before the changes were reverted. Try it
yourself: add either one temporarily and re-run `make boundary-lint`.

## How the manifest is derived (not hand-authored)

`tools/gen_manifest.sh` sources the same `lib_graph.sh` functions and emits
`manifest.json` with three sections, all read out of `src/*.pas` at
generation time:

- `capabilities`: every primitive declared in `core.pas`'s `interface`
  section, mapped to `src/core.pas`.
- `modules`: every unit/program found under `src/`, with its file and its
  `core`/`root`/`domain` classification.
- `edges`: every `(from unit, to unit, file)` triple read from each file's
  `uses` clause — including edges to stdlib units like `SysUtils`, which are
  simply units not declared anywhere in this repo.

`tools/check_manifest_drift.sh` regenerates the manifest into a temp file
and diffs it against the committed `manifest.json`; a mismatch fails CI. So
if you edit `src/tasks.pas`'s `uses` clause and forget to run `make
manifest`, `make ci` fails with a unified diff showing exactly what changed.

## Running it

```sh
make build            # fpc compiles src/app.pas (and its unit deps) into bin/App
make test             # compiles + runs tests/test_core.pas, test_users.pas, test_tasks.pas
make boundary-lint     # tools/boundary_lint.sh
make manifest          # regenerate manifest.json from src/*.pas
make manifest-check    # fail if manifest.json is stale
make ci                 # boundary-lint -> manifest-check -> build -> test, in that order
```

`.github/workflows/ci.yml` installs `fpc` via `apt-get` (the only network
step in this repo, and only inside CI) and then runs `make ci`.

Requires Free Pascal (`fpc`) to build/test. `boundary-lint`, `manifest`, and
`manifest-check` are pure shell/awk and need no compiler at all — they run
directly against the source text, so a violation is caught before a single
`.pas` file is compiled.
