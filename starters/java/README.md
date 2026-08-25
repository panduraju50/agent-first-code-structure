# taskly-lite (Java) — Design D starter

A minimal, real, buildable "Taskly-lite" whose organizing principle is an
**explicit, typed dependency graph**, not a folder convention. The graph is
the Java Platform Module System (JPMS): every edge you see in
`manifest.json` is a `requires` clause the compiler itself checks — this
repo does not *ask* you to respect module boundaries, it makes disrespecting
them a compile error, backstopped by a second, independent checker for the
things javac can't catch.

Everything here runs with the stock JDK. No build tool, no dependency
download, no network access at any point.

```
core/    taskly.core   — id encoding + input validation. ONE home each.
users/   taskly.users  — domain module. requires taskly.core only.
tasks/   taskly.tasks  — domain module. requires taskly.core only.
app/     taskly.app    — composition root. requires all three.
tools/   plain-Java tools: BoundaryCheck (linter), ManifestGen (generator)
manifest.json           — GENERATED from the module graph, not hand-written
```

## Quick start

```sh
./build.sh   # javac, in dependency order, module by module
./run.sh     # runs the composition-root scenario
./test.sh    # per-domain tests
./ci.sh      # build + test + boundary-lint + manifest-drift-check
```

or `make build`, `make test`, `make boundary-lint`, `make manifest-check`,
`make ci`.

## Design D, piece by piece

### 1. One home per cross-cutting concern

`taskly.core` is the only module that exports anything, and it exports
exactly two packages:

- `taskly.core.id` → `Base62Encoder.encode(long)` / `decode(String)`
- `taskly.core.validate` → `Validators.requireNonEmpty(String, String)` /
  `Validators.requireEmail(String)`

`taskly.users.UserService.create(...)` and `taskly.tasks.TaskService.create(...)`
both call into these — neither redefines an alphabet, a modulo-62 loop, or
an email regex. That's not a convention either module is trusting the other
to follow; it's checked twice (see §3).

### 2. Typed edges, not folder proximity

The dependency graph is not "these directories happen to sit near each
other" — it's the literal `requires` graph read straight out of
`module-info.java`:

```
taskly.users  --requires-->  taskly.core
taskly.tasks  --requires-->  taskly.core
taskly.app    --requires-->  taskly.core, taskly.users, taskly.tasks
```

There is **no** `taskly.users --requires--> taskly.tasks` edge, and no
reverse of it. `Task.assigneeId` is a plain `String` — `taskly.tasks` has no
type-level knowledge of `taskly.users.User` at all, so the missing edge
isn't just undeclared, it's structurally impossible to need. `taskly.app` is
the one place broad imports are allowed: `Main.java` is the only file in the
repo that imports from both domains, and it only ever passes a
`user.id()` (a `String`) into `tasks.assign(...)` — composition at the
value level, never at the type level.

### 3. The boundary enforcer

Design D's rule is "domains **should** depend only on core, but nothing
*physically* stops a domain module-info.java from adding a forbidden
`requires`, or a domain source file from pasting in its own copy of the
base62 alphabet." Two independent layers close that gap:

**Layer 1 — the compiler (free, automatic, unavoidable).**
Because `tasks/src/main/java/module-info.java` does not `requires
taskly.users`, any attempt to `import taskly.users.*` inside
`taskly.tasks` fails to compile:

```
tasks/src/main/java/taskly/tasks/TaskService.java:2: error: package taskly.users is not visible
import taskly.users.User;
             ^
  (package taskly.users is declared in module taskly.users, but module taskly.tasks does not read it)
```

(This is not hypothetical — it was reproduced while building this repo by
temporarily adding that import with no matching `requires` line.)

**Layer 2 — `tools/BoundaryCheck.java` (catches what the compiler can't).**
The compiler *would* happily accept a `requires taskly.users;` line added to
`taskly.tasks`'s module-info.java — that's a legal module graph, just the
wrong one for this design. `BoundaryCheck` parses every domain's
module-info.java and fails the build if a domain requires another domain,
and separately scans every non-core `.java` file for a redefined
`requireEmail`/`requireNonEmpty`, a class named like a base62 encoder, the
literal base62 alphabet string, or `%62`/`/62` arithmetic — the concrete
tells of a re-implemented primitive rather than a reused one. Both checks
strip comments first, so a javadoc example showing what *not* to write can't
trip the linter on itself.

We chose a small plain-Java checker over ArchUnit because ArchUnit isn't
installable in this offline environment (it needs a Maven/Gradle dependency
fetch); the checker is ~150 lines with zero dependencies and runs with
`javac`/`java` alone. Run it directly:

```sh
./tools/boundary-check.sh
```

Try breaking a rule yourself: add `requires taskly.users;` to
`tasks/src/main/java/module-info.java` and run `./tools/boundary-check.sh` —
it fails with a specific, named violation, before `javac` even gets a
chance to weigh in.

### 4. The generated manifest

`manifest.json` at the repo root is **produced by `tools/ManifestGen.java`
from the real module graph** — nobody hand-typed the edge list or the
capability table. It parses every `module-info.java` for its `requires`/
`exports` lines (the same source of truth `javac` compiles against) and
walks each module's `src/main/java` tree to find the first public top-level
type per file, slugifying `PascalCase` → `kebab-case` to name the
capability (`Base62Encoder` → `base62-encoder`, `UserService` →
`user-service`, ...). The generator is deterministic — no timestamps, sorted
output — so running it twice against unchanged sources produces
byte-identical JSON.

```sh
./tools/generate-manifest.sh          # regenerate manifest.json
./tools/generate-manifest.sh --check  # drift check: fails if stale
```

`ci.sh` runs the `--check` form as its last step: it regenerates the
manifest into a temp file and diffs it against the committed
`manifest.json`. If the module graph or the set of public types changed but
nobody re-ran the generator and committed the result, CI fails with the
diff shown. This is what keeps the manifest a live reflection of the code
instead of documentation that quietly rots.

### 5. Tests

- `users/src/test/java/taskly/users/UserServiceTest.java` — id assignment,
  round-trip `get`, and both validators rejecting bad input (invalid email,
  blank name).
- `tasks/src/test/java/taskly/tasks/TaskServiceTest.java` — id assignment,
  `list()`, `assign()` (using a bare `String` id, never a `User`), and the
  title validator rejecting a blank title.

No test framework is downloaded; each test is a `public static void
main(String[] args)` that prints one line per check and exits non-zero on
first failure, compiled straight into its module (via `--patch`-free layering
of `src/test/java` on top of `src/main/java`) and run with
`java --module-path ... -m <module>/<TestClass>`.

### 6. CI

`.github/workflows/ci.yml` and `ci.sh` / `make ci` both run the same four
steps, in order, and stop at the first failure:

1. `build.sh` — compile the JPMS graph (the compiler-enforced half of the
   boundary)
2. `test.sh` — one test binary per domain
3. `tools/boundary-check.sh` — the boundary-lint (the checker-enforced half)
4. `tools/generate-manifest.sh --check` — the manifest-drift check

## Why this is "the structure is the star"

There is no framework here, no dependency-injection library, no ArchUnit,
no build tool beyond `javac`/`java` themselves. The typed graph is JPMS's
own `module-info.java`; the "should-use-but-does-not" rule is enforced by
~150 lines of plain Java that reads that same graph; the manifest is a
second, independent derivation of that same graph, checked for drift. Three
views of one source of truth, all offline, all reproducible with nothing
but the JDK.
