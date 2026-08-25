# Taskly-lite (Python) — Design D starter

A minimal, real, runnable app whose organizing principle is an explicit,
**typed dependency graph**, not folders-by-convention. This document maps
every piece of the repo to that principle.

## Layout

```
core/                   # ONE home per cross-cutting primitive
  ids.py                #   base62 encode/decode (to_base62/from_base62/new_id)
  validation.py          #   validate_title, validate_email
  tests/

domains/                # independent business capabilities
  users/                 #   depends on core only
    models.py
    service.py           #   create/get
    tests/
  tasks/                 #   depends on core only
    models.py
    service.py           #   create/list/assign
    tests/

app/
  main.py                # composition root — the ONLY broad-import module

tools/
  _pygraph.py             # shared stdlib AST helper (imports + defs) for the two tools below
  boundary_check.py       # boundary enforcer (dependency-free)
  gen_manifest.py         # manifest generator + drift checker

.importlinter             # declarative import-linter contracts (same rules)
manifest.json              # GENERATED — capability→file map + dependency edges
Makefile
.github/workflows/ci.yml
```

## The typed dependency graph

The graph isn't a diagram someone drew and forgot to update — it *is* the
Python package/import graph, and it is typed by directory:

| Layer               | May import                    | May NOT import                          |
|----------------------|--------------------------------|-------------------------------------------|
| `core.*`             | stdlib only                    | `domains.*`, `app.*`                      |
| `domains.<X>.*`      | `core.*`, `domains.<X>.*`      | `domains.<Y>.*` (Y ≠ X), `app.*`          |
| `app.*`              | anything project-local          | — (this is the one broad-import layer)    |

That table is not just documentation — it is enforced twice (see below),
and it is also what `manifest.json`'s `edges` list shows was actually
produced by the real source tree (open it; there is no `domains.tasks →
domains.users` edge, and no domain has an edge to `app`).

## Rule 1 — one home per cross-cutting concern

- Base62 id encoding lives **only** in `core/ids.py` (`to_base62`,
  `from_base62`, `new_id`).
- Input validation lives **only** in `core/validation.py`
  (`validate_title`: rejects empty/whitespace-only strings;
  `validate_email`: requires an `@` **and** a dotted domain, so `a@b` is
  rejected but `a@b.com` is accepted).
- `domains/users/service.py` and `domains/tasks/service.py` both *import*
  these from `core` — neither one re-implements them. `tools/boundary_check.py`
  fails the build if a second implementation of any of these ever appears
  outside `core`.

## Rule 2 — domains depend on core, never on each other

`domains/tasks/service.py` needs to know whether an assignee id refers to
a real user to fully validate `assign()` — but it deliberately **does
not** import `domains.users` to find out. That check lives in
`app/main.py::assign_task`, which is allowed to know about both domains
because it *is* the composition root. This is the "should-use-but-does-not"
rule in action: `tasks` *could* reach into `users` to do the check itself,
but the boundary is enforced so it structurally can't, and the
composition root exists specifically to hold the logic that requires
knowing about more than one domain.

## Rule 3 — the boundary enforcer

Two enforcers, same rules, so the repo works with or without network
access:

1. **`.importlinter`** — the idiomatic, declarative expression, using
   [import-linter](https://import-linter.readthedocs.io)'s `layers`
   contract (`app` > `domains` > `core`) and `independence` contract
   (`domains.users` independent of `domains.tasks`). Run with
   `lint-imports --config .importlinter` if the package is installed.
2. **`tools/boundary_check.py`** — a zero-dependency, stdlib-only
   Python script that parses every file's imports and definitions with
   `ast` and enforces the *same* two rules, plus the "duplicate primitive"
   rule from Rule 1:
   - (a) fails if any `domains.<X>` file imports `domains.<Y>` (Y ≠ X), or
     imports `app`, or if `core` imports `domains`/`app`;
   - (b) fails if any file outside `core/ids.py` defines `to_base62`,
     `from_base62`, `new_id`, `validate_title`, `validate_email` — or
     defines *any* function with `base62` in its name outside
     `core/ids.py` (catching a renamed re-implementation, not just an
     exact-name clash).

`make boundary-lint` runs the stdlib script unconditionally (that is the
gate CI actually depends on) and additionally runs `lint-imports` when it
happens to be installed. This scaffold was built with no network installs,
so `import-linter` is *not* installed here — the stdlib checker is the one
enforcing the rule right now, and it was verified against real
violations while building this repo (a fake `domains.users → domains.tasks`
import and a duplicate `to_base62` were both injected and caught, then
removed).

## Rule 4 — the generated manifest + drift check

`manifest.json` is **produced**, not hand-authored, by
`tools/gen_manifest.py`:

- it walks `core/`, `domains/*`, `app/` with `ast`,
- lists every public top-level function/class as a capability, mapped to
  its one owning file (`capabilities`),
- and lists every project-local import edge it finds (`edges`) — the same
  edges `boundary_check.py` uses to enforce Rule 2, from the same shared
  `tools/_pygraph.py` walker (one parse, two consumers).

`make manifest` regenerates it. `make manifest-check`
(`gen_manifest.py --check`) regenerates it in memory and diffs against the
committed file — it fails the build if source changed without the
manifest being regenerated and committed. That's the drift check, and
it's what `.github/workflows/ci.yml` runs as its last step.

## Rule 5 — tests

- `domains/users/tests/test_users.py` — create/get, unique ids, both
  invalid-email shapes (`no-at-sign`, `no-domain`), missing-user lookup.
- `domains/tasks/tests/test_tasks.py` — create/list, unique ids,
  empty-title rejection, assign, missing-task assign.
- `core/tests/` — round-trip base62 encode/decode and both validators,
  since core is the one place these primitives are allowed to exist.

## Rule 6 — this document. See above.

## Rule 7 — one command runs everything

```
make ci
```

runs, in order: `build` (stdlib `compileall`), `test` (`unittest
discover`), `boundary-lint` (the enforcer), `manifest-check` (the drift
check). `.github/workflows/ci.yml` runs the same four steps on every push
and PR. Individually:

```
make build            # compile-check every module
make test             # run all unit tests
make boundary-lint     # enforce the dependency graph + one-home rules
make manifest           # regenerate manifest.json
make manifest-check      # fail if manifest.json is stale
make run                # execute the tiny end-to-end scenario in app/main.py
```

## Try it

```
cd starters/python
make run
```

```
Users:
  1  alice@example.com
  2  bob@example.com
Tasks:
  1  'Write the Design D README'  assignee=1
  2  'Wire the boundary enforcer into CI'  assignee=2
```

Everything here — no third-party dependencies required — runs with just
`python3` (stdlib) from the standard toolchain.
