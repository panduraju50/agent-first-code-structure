# taskly-lite (TypeScript / Node) — Design D starter

A minimal task tracker whose organizing principle is not "MVC" or "feature
folders" but an **explicit, typed dependency graph**. The graph is the
contract: every edge that is allowed to exist is declared somewhere a tool
can read, and every edge that must not exist is checked by a tool that
fails the build if it appears.

```
packages/
  core/     one home each for cross-cutting primitives (base62 ids, validation)
  users/    domain: create/get users        — depends on core only
  tasks/    domain: create/list/assign tasks — depends on core only
  app/      composition root — the only package allowed to import across domains
```

Run `npm run start` (or `node packages/app/src/main.ts`) to see the wired
scenario: two users, two tasks, one assignment each.

## Design D, piece by piece

### 1. One home per cross-cutting concern → `packages/core`

- `packages/core/src/id.ts` — the base62 encoder/decoder and `nextId()`.
  This is the **only** file in the repo that implements base62 encoding.
- `packages/core/src/validate.ts` — `validateTitle` (non-empty) and
  `validateEmail` (requires an `@` and a dotted domain). This is the
  **only** file that implements these checks.

`users` and `tasks` both need an id and a validator, and both get them by
importing core — never by writing their own copy. That "must import, must
not reimplement" rule is not just a convention here; it's mechanically
checked (see §3).

### 2. Domains depend on core, never on each other

- `packages/users/src/index.ts` imports `../../core/src/id.ts` and
  `../../core/src/validate.ts`. It never imports anything under
  `packages/tasks`.
- `packages/tasks/src/index.ts` imports the same two core modules. It
  never imports anything under `packages/users`.
- `assignTask(taskId, assigneeUserId)` in `packages/tasks/src/index.ts`
  takes a plain `string` user id, not a `User` object — that's how
  `tasks` cooperates with `users` conceptually without ever importing it.
- `packages/app/src/main.ts` is the **one** place that imports both
  `users` and `tasks` and wires them together.

**Where the typed edges live:** `tsconfig.json` (root) references all
four package tsconfigs; each package's own `tsconfig.json` declares, in
its `references` array, exactly which other packages it's allowed to
pull types from:

| package | `references` in its tsconfig.json |
|---|---|
| `packages/core` | *(none — it's the leaf)* |
| `packages/users` | `../core` |
| `packages/tasks` | `../core` |
| `packages/app` | `../core`, `../users`, `../tasks` |

`npm run build` runs `tsc -b .`, TypeScript's **composite project
build**. This isn't just a compiler — it's a build orchestrator that
walks the reference graph and, crucially, **only lets a project see
source files belonging to a project it references**. If `users`
imported from `tasks` without `../tasks` in its `references` array, the
build fails with `TS6059`/`TS6307` ("File is not listed within the file
list of project ...") — not because we banned it after the fact, but
because the compiler literally does not know how to resolve the file
without a declared edge. Try it:

```sh
# in packages/users/src/index.ts, add:
#   import { listTasks } from "../../tasks/src/index.ts";
npm run build
# TS6059: File '.../tasks/src/index.ts' is not under 'rootDir' ...
# TS6307: File '.../tasks/src/index.ts' is not listed within the file
#         list of project '.../users/tsconfig.json' ...
```

### 3. The boundary enforcer

Two tools check the same two rules — "no domain imports another domain"
and "no duplicate primitive outside core" — from two different angles:

- **`.dependency-cruiser.js`** — the idiomatic tool for this job
  ([dependency-cruiser](https://github.com/sverweij/dependency-cruiser)).
  Real `forbidden` rules: `no-users-importing-tasks`,
  `no-tasks-importing-users`, `core-must-not-depend-on-domains-or-app`,
  `no-duplicate-base62-outside-core`. This is what you'd actually run day
  to day (`npx depcruise packages --config .dependency-cruiser.js`) — but
  it needs `npm install` (a `devDependency`), which this sandbox can't do
  offline.
- **`tools/boundary-lint.mjs`** — a ~130-line script using **only Node's
  standard library** (`node:fs`, `node:path`), so it runs in CI with zero
  installed packages. It parses every `.ts` file under `packages/*/src`
  and `packages/*/test`, resolves each relative import to the package it
  points at, and fails (`process.exit(1)`) if:
  - (a) a domain package (anything under `packages/` that isn't `core`
    or `app`) imports from a *different* domain package, or `core`
    imports from a domain/`app`;
  - (b) any file outside `packages/core` declares a top-level
    function/const/class whose name matches `/base62/i`, or shadows one
    of core's exported names (`encodeBase62`, `validateEmail`, ...).

Both are wired into CI (`.github/workflows/ci.yml`); `boundary-lint.mjs`
is what the offline-guaranteed pipeline actually gates on, since it needs
no `node_modules`. Run `npm run lint:boundaries` to try it — or break a
rule on purpose and watch it fail:

```sh
# packages/tasks/src/index.ts
function encodeBase62Duplicate(n: number) { return n.toString(); }
```
```
$ npm run lint:boundaries
boundary-lint: 1 violation(s) found
  [no-duplicate-base62-outside-core] packages/tasks/src/index.ts
      declares "encodeBase62Duplicate" — base62 encoding has exactly one
      home: packages/core/src/id.ts.
```

**Why regex, not a real parser:** `boundary-lint.mjs` and
`gen-manifest.mjs` (§4) share `tools/lib/scan.mjs`, which extracts
imports and top-level declarations with a couple of targeted regexes
instead of a real TypeScript AST. For a small, idiomatically-written
starter repo that's precise enough, and it means the enforcement and the
manifest generation both run with **zero dependencies**. The real,
AST-aware version of the same two rules is `.dependency-cruiser.js`.

### 4. The generated manifest

`manifest.json` is **produced from the module graph, not hand-written**.
`tools/gen-manifest.mjs` walks the same `packages/*/src` and
`packages/*/test` files as the linter and emits:

- `capabilities` — every exported top-level declaration, mapped to the
  file that owns it (`{ capability, kind, package, file }`). This is the
  capability-to-owning-file map: e.g. `encodeBase62` → `core` →
  `packages/core/src/id.ts`.
- `packageEdges` — deduplicated, package-level dependency edges derived
  from real relative imports (`users → core`, `tasks → core`,
  `app → users`, `app → tasks`). No `users → tasks` edge exists, because
  none exists in the source.
- `fileEdges` — the same, at file granularity, for full traceability.

The output is deterministic (sorted, no timestamps), so running it twice
with no code changes produces a byte-identical file. That's what makes
the drift check possible:

```sh
npm run generate:manifest   # writes manifest.json (tools/gen-manifest.mjs --write)
npm run check:manifest      # regenerates in memory and diffs against the
                             # committed file (tools/gen-manifest.mjs --check);
                             # exits 1 if they differ
```

`npm run ci` (and CI itself) runs `check:manifest` as its last step: if
you add a capability or an import and forget to run
`generate:manifest`, the build fails with "manifest.json is out of date
with packages/".

### 5. Tests

At least one test per domain, plus core:

- `packages/core/test/id.test.ts`, `validate.test.ts`
- `packages/users/test/users.test.ts` — includes "rejects an invalid
  email via core's validator", proving `users` delegates to core rather
  than validating itself.
- `packages/tasks/test/tasks.test.ts` — includes "assignTask attaches an
  assignee id by reference only (no users import)", proving the
  domain-independence design choice, not just the enforcer that checks
  it.

Tests run directly against the TypeScript source with Node's built-in
test runner (`node --test`, Node ≥ 22 strips TS types natively — no
`ts-node`, no build step required to test).

### 6. This section

...is the map you're reading. See the table in §2 for where the typed
edges live, §3 for how the enforcer realizes "should-use-but-does-not",
and §4 for how the manifest is derived.

### 7. CI

`.github/workflows/ci.yml` runs, in order: **build → test →
boundary-lint (stdlib, then dependency-cruiser) → manifest-drift-check**.
`npm run ci` / `make ci` run the offline-safe subset (build, test,
stdlib boundary-lint, manifest check) locally in the same order.

## Commands

| command | what it does |
|---|---|
| `npm run build` | `tsc -b .` — builds the typed project-reference DAG |
| `npm run test` | runs all `*.test.ts` files with `node --test` |
| `npm run start` | runs the composition root (`packages/app/src/main.ts`) |
| `npm run lint:boundaries` | stdlib-only boundary enforcer |
| `npm run generate:manifest` | regenerates `manifest.json` from the module graph |
| `npm run check:manifest` | fails if `manifest.json` has drifted from the graph |
| `npm run ci` / `make ci` | build + test + lint:boundaries + check:manifest |

Everything above except the `dependency-cruiser` step in CI runs with
**zero installed dependencies** — `tsc` and `node` are the only
requirements (Node ≥ 22, TypeScript ≥ 5.7 for
`allowImportingTsExtensions` + `emitDeclarationOnly`, used so the exact
same `.ts` sources both type-check via `tsc -b` and run directly via
`node`, with no separate JS build artifacts to keep in sync).
