# Taskly-lite — Design D starter (Next.js)

A minimal, REAL app ("Taskly-lite": users + tasks) scaffolded to demonstrate
**Design D**: an agent-first repo structure whose organizing principle is an
explicit, *typed* dependency graph, rather than folder convention alone.

Everything below is actually wired up and actually runs — see
[Offline verification](#offline-verification).

## The shape

```
src/
  core/                    # ONE home for cross-cutting primitives
    id/base62.ts           #   base62 id encoder — lives ONLY here
    validation/validators.ts  # title/email validators — live ONLY here
    index.ts                  # public barrel

  features/
    users/                 # domain: depends on core only
      types.ts repository.ts service.ts index.ts service.test.ts
    tasks/                 # domain: depends on core only
      types.ts repository.ts service.ts index.ts service.test.ts
      # NOTE: no import of `users` anywhere. assignTask(taskId, assigneeId)
      # takes a bare string, not a `User` — the domain has no way to even
      # express "I depend on users".

  composition/
    root.ts                # the ONE file allowed to import BOTH domains
    run.ts                 # tiny CLI entry that runs the wired scenario

  app/                     # Next.js App Router — imports composition, not features
    layout.tsx page.tsx
    tasks/page.tsx          # server component
    tasks/TaskForm.tsx      # "use client" component
```

## Where each Design D requirement lives

### 1. One home per cross-cutting concern

`src/core/id/base62.ts` is the only file that encodes base62. `src/core/validation/validators.ts`
is the only file that validates a title or an email. `users/service.ts` and
`tasks/service.ts` both **import** `nextId`/`validateEmail`/`validateTitle`
from `../../core` — neither re-implements them.

### 2. Typed dependency edges + no domain-to-domain edge

The allowed edges are one small table, defined **once** and used by *two*
independent enforcers so they can't drift into disagreement:

```
core        -> core
users       -> core, users            (never tasks)
tasks       -> core, tasks            (never users)
composition -> core, users, tasks, composition   (the one broad-import file)
app         -> core, composition, app (never features/* directly)
```

- `eslint.config.mjs` — `boundaries/element-types` rule, the idiomatic tool
  (`eslint-plugin-boundaries`).
- `scripts/lib/rules.mjs` — the same table, consumed by the stdlib fallback
  checker. Its file-level doc comment says explicitly that it mirrors the
  ESLint config.

`src/composition/root.ts` is the only file in the repo that imports from both
`src/features/users` and `src/features/tasks`. That's also where the one
real cross-domain concern — "does this assignee id actually belong to a
user?" — gets checked, because that's the only place both domains are even
visible.

### 3. The boundary enforcer

**`scripts/check-boundaries.mjs`** (stdlib-only, zero dependencies) walks the
real `src/` tree via `scripts/lib/graph.mjs`, parses every `import`/`export
... from` statement with plain regex (no compiler needed), and calls the pure
`checkBoundaries()` function in `scripts/lib/rules.mjs`. It fails the build
(non-zero exit) when:

- **(a) a domain imports a domain it isn't allowed to** — in particular the
  forbidden `users <-> tasks` edge. Rule id: `domain-edge`.
- **(b) any file outside `src/core` defines a base62 encoder or duplicates a
  core validation primitive.** Rule id: `duplicate-primitive` — it scans file
  content (outside `core`) for code-shaped patterns like
  `function toBase62(` or the base62 alphabet string literal, or a
  `function validateEmail`/`validateTitle` declaration.
- A bonus check not in the original spec but a natural extension: **(c) a
  `"use client"` file imports the server-only composition root.** Rule id:
  `client-server-boundary` — this is the App Router server/client boundary,
  enforced the same way.
- **(d) the same `// @capability` marker is declared twice** — `duplicate-capability`,
  the mechanical version of "one home per concern": if two files claim the
  same capability id, that *is* a duplicate primitive by definition.

This is the "SHOULD-use-but-does-not" rule realized concretely: Design D
doesn't just wire correct edges when you follow the pattern, it makes the
*wrong* edge (a domain reimplementing a primitive, or reaching sideways into
a sibling domain) fail a script that's `node scripts/check-boundaries.mjs`
away — no editor, no LLM judgment call, no code review needed to catch it.

`scripts/check-boundaries.test.mjs` proves the enforcer isn't decorative: it
feeds `checkBoundaries()` synthetic fixtures for each forbidden shape (a
`users -> tasks` import, a re-implemented `toBase62`, a duplicated
capability marker, a client component reaching into composition) and asserts
each one is caught, plus that clean graphs pass. Those are real, currently
green tests — see [Offline verification](#offline-verification) — you can
also break `src/features/tasks/service.ts` yourself (add
`import { getUser } from "../users";`) and watch
`node scripts/check-boundaries.mjs` fail with exactly that message.

`eslint.config.mjs` is the idiomatic-tool version of the identical rule
table, for when `eslint` + `eslint-plugin-boundaries` are actually installed
(CI installs them; this offline scaffold does not — see below).

### 4. The generated manifest

**`MANIFEST.generated.json`** is produced by `scripts/generate-manifest.mjs`
from the *same* parsed graph the boundary checker uses
(`scripts/lib/graph.mjs`) — never hand-typed. It contains:

- `capabilities`: every `// @capability <id>` marker found in the source,
  mapped to its owning file (mechanically extracted, not curated).
- `domains`: which files belong to `core`/`users`/`tasks`/`composition`/`app`,
  derived from path prefixes.
- `edges.files`: every resolved local import, file → file.
- `edges.domains`: the same edges rolled up to domain → domain (this is the
  typed dependency graph in its most compact form — compare it to the table
  in requirement 2 above).

**Drift check**: `node scripts/generate-manifest.mjs --check` (also
`npm run manifest:check`) regenerates the manifest in memory and does a byte
comparison against the committed `MANIFEST.generated.json`. If source
changed in a way that alters the graph (new capability, new/removed edge, a
file moving domains) and the manifest wasn't regenerated, this exits 1 with
"MANIFEST.generated.json is stale... run ... and commit the result." A
content-only change (e.g. a comment) that doesn't alter the graph is *not*
flagged as drift, because the manifest describes the graph, not the bytes.

### 5. Tests per domain

- `src/features/users/service.test.ts` — 4 tests (id shape, email
  normalization, both invalid-email shapes: missing `@` and missing domain).
- `src/features/tasks/service.test.ts` — 4 tests (id shape, empty-title
  rejection, assignment, unknown-task error).
- `scripts/check-boundaries.test.mjs` — 7 tests proving the enforcer itself
  works (see above).

All run with Node's built-in test runner (`node:test`), zero test-framework
dependency.

### 6. This file

You're reading it.

### 7. CI target: build + test + boundary-lint + manifest-drift-check

Three equivalent entry points, all running the same four steps:

- `node scripts/ci.mjs` (or `npm run ci`)
- `make ci`
- `.github/workflows/ci.yml` — runs the offline steps first, then installs
  just `eslint` + `eslint-plugin-boundaries` (not the `next`/`react` app
  dependencies) and runs the idiomatic-tool boundary lint too, so both the
  fallback and the real tool are wired into CI as required.

## Offline verification

This repo was scaffolded and verified **without running `npm install`**.
Everything below uses only `tsc` (present as a global toolchain binary) and
Node's standard library:

```
node scripts/ci.mjs
# or: make ci
```

which runs, in order:

1. `tsc -p tsconfig.build.json` — compiles `src/**/*.{ts,tsx}` to plain
   CommonJS in `dist/` (a small ambient shim in `src/types/*.d.ts` stands in
   for the `@types/react`/`@types/node` packages that aren't installed, just
   enough surface for the demo components/tests to typecheck).
2. `node --test 'dist/**/*.test.js' 'scripts/**/*.test.mjs'` — 15 tests, all
   passing.
3. `node scripts/check-boundaries.mjs` — 21 files scanned, 0 violations.
4. `node scripts/generate-manifest.mjs --check` — manifest matches the graph.

You can also run the wired scenario directly:

```
node dist/composition/run.js
```

which prints a created user, two created tasks, and one of them assigned —
exercising `users` and `tasks` together exclusively through
`composition/root.ts`.

### What is *not* run offline

`npm run dev` / `npm run build` / `npm run start` need the real Next.js
toolchain (`next`, `react`, `react-dom`, plus their `@types/*` packages),
declared in `package.json` but deliberately not installed here per the
no-network-installs constraint. `tsconfig.json` (as opposed to
`tsconfig.build.json`) is the config that real Next.js toolchain would use —
it's never invoked in this offline verification path. Swap in a real
checkout by running `npm install` and deleting `src/types/*.d.ts`; nothing
in `src/core`, `src/features/*`, or `src/composition` needs to change.
