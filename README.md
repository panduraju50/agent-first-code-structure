# How Should Code Be Structured *for AI Agents*?

An experiment. Human repo conventions (`src/services/...`) are optimized for human
reading. But when an AI agent writes, reviews, and maintains the code, the
constraints are different: an agent is a **local reasoner with a bounded context
window and no persistent memory of the repo**. It duplicates code it can't
retrieve, reviews only what's in front of it, and stops at the first green.

This repo asks: *what repo structure makes an agent build code with less
duplication, easier review, and easier testing?* — and tries to answer it
empirically by generating the **same program** in many structural layouts,
planting **identical bugs** in every one, and having **isolated agents** work each
layout cold.

It is published with its own failures intact. Two early conclusions were
withdrawn after I found I had leaked the answer into one contestant and had
measured cost with a metric that turned out to be an artifact. The strongest
result is a negative one that undercuts the premise. Both are recorded below
rather than quietly fixed.

## Method

1. **One canonical program**, emitted into N structural designs by a deterministic
   generator. Only the *layout* differs between variants; the code and the planted
   bugs are byte-for-byte identical.
2. **Isolated, same-capability agents** each receive **one** variant cold — no
   answer key, blind to sibling variants — and must add a feature and audit the
   code. This measures real *adoptability*, not opinion.
3. A **synthesis** pass ranks designs by planted-bug catch rate, whether the agent
   introduced *new* duplication, and navigation cost.

## Two rounds

### Experiment 1 — tiny (`experiment/`)
Link-shortener, ~4 files, **10 designs A–J**. Planted: a duplicated base62 encoder
(one copy with a silent collision bug) and a `validate_url` that accepts non-URLs.
See [`experiment/RESULTS.md`](experiment/RESULTS.md).

### Experiment 2 — scaled + model comparison + control (`experiment2/`)
"Taskly" task/project API, ~26 units / up to 27 files, **8 designs**, each reviewed
across **Opus / Sonnet / Haiku**, plus a **no-instruction control**: three empty
folders where each model built the app in *its own* structure.
5 planted bugs: duplicated id-encoder, duplicated date-formatter, weak email
validation, missing authorization on assign, off-by-one pagination.
See [`experiment2/RESULTS.md`](experiment2/RESULTS.md).

### Experiment 3 — do prompt/context/workflow/loop matter? (`experiment3/`)
A Rust workspace, a feature with seven traps, and decoys that compile but behave
differently. Scored entirely by a program: hidden acceptance tests, a
missing-edge duplication check, and decoy detection. The answer was no — the
worst condition matched the best, twice.
See [`experiment3/RESULTS.md`](experiment3/RESULTS.md).

## Designs tested

| ID | Structure |
|----|-----------|
| A | Flat files + single `INDEX.json` manifest |
| B | Vertical slices, duplication tolerated |
| C | Spec-as-source (`spec/*.md` ↔ `gen/*.py`) |
| D | Addressable dependency **graph** with typed edges |
| E | Capability registry monorepo (`packages/*`) |
| F | Fractal manifests (manifest-of-manifests) |
| G | Contract-bus (interface files + impl) |
| H | Unit-owns-its-infra (deploy co-located) |
| I | Effect-tagged units |
| J | Append-only versioned units |
| K | RAG-chunked (per-file summary cards, no manifest) |
| L | Single-file monolith + table-of-contents anchors |

## Findings — and what survived scrutiny

Read the limitations below before quoting any of this. Several early conclusions
did not survive, and the strongest result is a negative one.

**What holds:**

- **Given an empty folder, models converge.** Opus, Sonnet, and Haiku each built
  the same app with no structure imposed, and all three independently produced a
  skeleton none of the twelve designed layouts had: a **manifest, real imports,
  and exactly one home per cross-cutting concern**. This is the most trustworthy
  result here precisely because nothing was imposed.
- **Name-based duplicate detection is blind to a renamed copy.** A lint matching
  `to_base62` misses a copy called `shortcode`. Detecting the behaviour — the
  alphabet literal, the `% 62` arithmetic — catches it. Verified adversarially,
  and it matters because the bug planted in these experiments *was* a renamed
  copy.
- **Prompt, context, workflow and loop did not change the outcome** on a
  well-structured repository. Two rounds, seven traps, decoys that compile: a
  bare one-shot prompt with no context scored identically to plan→build→review
  with a manifest and a test loop. See [experiment 3](experiment3/RESULTS.md).

**What did not hold:**

- **The ranking of designs A–J is void.** Only design D's manifest was given
  `SHOULD_use_but_does_not` edges pointing at the planted bugs — an answer key
  written into one contestant. It was then ranked first partly *for finding what
  it had been told*.
- **"Detection saturates at scale" was an artifact**, not a finding. The repos
  were small enough to read exhaustively, so the variable had no room to act.
- **"Navigation cost" was measuring the wrong thing.** Files-read ranked the
  2-file monolith cheapest, but it contained *more bytes* than the 29-file
  layout. It measured how the code was chunked, not what it cost to read. Tokens
  were never measured.

## Limitations

- Every experiment ran in the regime where retrieval **cannot** fail: repositories
  small enough to read end to end in one session. Structure plausibly matters most
  when that stops being true, and that regime was never tested.
- The core claim — that structure prevents duplication over a long project with
  many sessions — is longitudinal. What was measured is a single cold session.
  Those are barely the same question.
- Experiments 1 and 2 measured **detection** (can an agent find a planted bug) and
  drew conclusions about **prevention** (does the structure stop the bug being
  written). Different mechanisms.
- Signposts were planted three separate times — a doc comment naming a primitive
  as canonical is an answer key. Writing good documentation and leaking the answer
  turn out to be the same act.

Taken together, experiment 3 **undercuts the premise of the earlier work**: it
finds no duplication to prevent in a well-structured repository, even under
deliberately bad prompting.

## Layout

```
experiment/          tiny round: generate.py, variants/A..J, RESULTS.md, reviews.json
experiment2/         scaled round:
  generate_v2.py       deterministic generator (~26 units)
  variants/            8 designs @ sonnet (agents edited their copies)
  variants_opus/       anchor designs A,D,L reviewed by Opus
  variants_haiku/      anchor designs A,D,L reviewed by Haiku
  native/{opus,sonnet,haiku}/   no-instruction control builds
  RESULTS.md           full synthesis report
  reviews.json         14 raw structured reviews
  natives.json         3 native-build self-reports
experiment3/         factor round (prompt / context / workflow / loop):
  build_base_v2.py     generates the 15-crate Rust workspace
  base/  base_v2/      round 1 and round 2 workspaces (v2 has the decoy crate)
  hidden/              acceptance tests, never shown to the agents
  score.py             the objective scorer (no LLM judge anywhere)
  runs/  runs2/        the agents' finished workspaces, as scored
  RESULTS.md           the negative result, and the scorer bugs calibration caught
```

### Also here

- `starters/` — the D structure hand-built in six languages, each enforced by
  that language's own dependency mechanism, with the boundary lints adversarially
  verified.
- `generator/` — `scaffold.py`, a single stdlib-only file that emits the same
  structure into Go, Rust, Java, Python or TypeScript from one spec. A tool built
  on the hypothesis, not evidence for it.

## Reproduce

```bash
cd experiment  && python3 generate.py      # rebuild the 10 tiny variants
cd experiment2 && python3 generate_v2.py   # rebuild the 8 scaled variants
cd experiment3 && python3 build_base_v2.py && python3 score.py runs2/worst_1
```

Reviews were run by isolated Claude Code agents; the structured results are
captured in the `*.json` and `RESULTS.md` files.

---

*Generated with [Claude Code](https://claude.com/claude-code).*
