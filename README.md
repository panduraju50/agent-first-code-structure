# How Should Code Be Structured *for AI Agents*?

An experiment. Human repo conventions (`src/services/...`) are optimized for human
reading. But when an AI agent writes, reviews, and maintains the code, the
constraints are different: an agent is a **local reasoner with a bounded context
window and no persistent memory of the repo**. It duplicates code it can't
retrieve, reviews only what's in front of it, and stops at the first green.

This repo asks: *what repo structure makes an agent build code with less
duplication, easier review, and easier testing?* — and answers it empirically by
generating the **same program** in many structural layouts, planting **identical
bugs** in every one, and having **isolated agents** review each layout cold.

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

## Key findings

- **Detection saturates while the repo is fully readable.** At both tiny and
  ~26-unit scale, *every* design caught *every* planted bug. Structure did not
  change *whether* bugs were found — it changed the **cost** (2 vs 27 files read)
  and the **confidence**. The duplication-class bug is caught by "read everything
  and eyeball two copies," which is O(files) and does **not** survive 10× scale.
- **Structure sets the cost floor; the model sets the insight ceiling.**
  Navigation cost is fixed by layout, not model — a stronger model does not rescue
  a file-explosion layout. Depth and precision of *unplanted* findings are fixed by
  the model, not the layout.
- **The best structure is the one models build unprompted.** Given an empty folder,
  Opus, Sonnet, and Haiku all converged on the same skeleton that none of the 12
  imposed designs had: **a generated manifest + real Python imports + exactly one
  home per cross-cutting concern**. "One home per concern" makes the duplicate-
  encoder bug *unwritable*. Among imposed designs, **D (dependency graph)** is the
  one worth grafting on — it makes duplication a *graph property*, catchable
  without reading both copies.

**In one line:** manifest buys orientation, real imports buy verifiability, and
one-home-per-concern buys structural immunity to the duplication bug class.

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
```

## Reproduce

```bash
cd experiment  && python3 generate.py      # rebuild the 10 tiny variants
cd experiment2 && python3 generate_v2.py   # rebuild the 8 scaled variants
```

Reviews were run by isolated Claude Code agents; the structured results are
captured in the `*.json` and `RESULTS.md` files.

---

*Generated with [Claude Code](https://claude.com/claude-code).*
