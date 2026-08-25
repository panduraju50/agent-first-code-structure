# Experiment 3 — A negative result

**Question:** do prompt engineering, context engineering, workflow orchestration,
and build/test loops change what an agent produces?

**Answer, on this task: no. Not measurably. Not even a little.**

Two rounds, deliberately hostile conditions, seven independent traps, decoys that
compile. The worst condition and the best condition scored identically both times.

---

## Method

One Rust workspace, one feature to add, agents scored by a **program** — no LLM
judge and no judgement of mine anywhere in the measurement:

| metric | how it is obtained |
|---|---|
| correctness | hidden acceptance tests the agent never sees |
| regression | the pre-existing suite must still pass |
| duplication | a re-implemented primitive, or a required edge that is absent |
| decoy use | reaching into the deprecated `legacy` crate |
| cost | lines added versus the pristine base |

**Pre-registered before any run:** primary metric duplication; ranking
correctness → duplication → cost; no post-hoc tiebreakers. The *worst* condition
was included deliberately as a falsification arm.

### Conditions

| | worst | best |
|---|---|---|
| prompt | bare task | task + rules + acceptance criteria |
| context | none, must explore | repository manifest supplied |
| workflow | single agent | plan → build → adversarial review → fix |
| loop | one-shot | build/test until green |
| tooling | forbidden from running `cargo` at all | full |

---

## Round 1

A 383-line, 8-file workspace. One trap: render a due date in "the product's
standard timestamp display format", with the format never stated, so passing
required finding `corelib::timefmt::format_ts`.

| run | hidden | duplication | correct | LOC |
|---|---|---|---|---|
| worst_1 | 11/11 | 0 | ✅ | +52 |
| worst_2 | 11/11 | 0 | ✅ | +48 |
| best_1 | 11/11 | 0 | ✅ | +94 |
| best_2 | 11/11 | 0 | ✅ | +121 |

Saturated. Diagnosis: the repo was solvable after reading 3–5 files, and
`timefmt.rs` opened with a doc comment stating that every user-visible timestamp
goes through `format_ts`. An agent quoted it back as how it found the answer. I
had planted the answer key in the artifact.

## Round 2 — hardened

- every signpost doc comment removed (or so I believed — see below)
- 15 crates, 27 files, ~1200 lines
- **seven** independent traps instead of one
- a `legacy` crate of decoys that **compile and read plausibly but behave
  differently**: `shorten` appends `...` and does not count it toward the limit
  where `truncate` appends `…` and does; `take_page` is 0-indexed where
  `page_slice` is 1-indexed; `render_time` renders `2 days 0h` where `format_ts`
  renders `d2t0`; `in_bounds` is exclusive at the top where `validate_range` is
  inclusive.

Every trap was verified to discriminate before running anything:

| implementation | hidden score |
|---|---|
| reference (all primitives correct) | 12/12 |
| decoy `take_page` | 4/12 |
| decoy `render_time` | 8/12 |
| priority tag omitted | 8/12 |
| decoy `in_bounds` | 10/12 |
| decoy `make_token` | 11/12 |
| decoy `shorten` | 11/12 |
| escaping omitted | 11/12 |

Result:

| run | hidden | duplication | decoy use | correct | LOC |
|---|---|---|---|---|---|
| worst_1 | 12/12 | 0 | 0 | ✅ | +58 |
| worst_2 | 12/12 | 0 | 0 | ✅ | +62 |
| best_1 | 12/12 | 0 | 0 | ✅ | +52 |
| best_2 | 12/12 | 0 | 0 | ✅ | +52 |

Perfect scores everywhere. The bare, context-free, one-shot condition — not
permitted to compile its own code — hit all seven traps, avoided every decoy, and
matched the reference solution.

---

## Why

Two causes. Only one of them is a defect.

**I planted signposts again.** Having removed the `timefmt` comment, I wrote three
more without noticing: `paging.rs` says "Pages are 1-indexed", `text.rs` says the
ellipsis "counts toward the limit", `escape.rs` says "Backslash first". An agent
quoted the paging one back. Writing good documentation and planting an answer key
turn out to be the same act, which is why this happened three times.

**The repository already demonstrates every convention — and that is not a flaw.**
`notifier::send` calls `short_code`, `format_ts` and `escape_body` in a single
function. `search` calls `page_slice`. Existing code is a worked example of every
primitive the task needs. Agents read 10 of 27 files and had all seven.

Defeating the second cause would require a repository where primitives exist but
nothing documents them and nothing demonstrates them. That is not a realistic
codebase; it is an artificially hostile one, built to make the hypothesis look
necessary. So the honest move is to report the result rather than keep hardening
until it flips.

---

## What this means

> When cross-cutting primitives have exactly one home and existing code
> demonstrates their use, agents find and reuse them reliably — regardless of
> prompt, context, workflow, or loop. Retrieval is not the bottleneck, so the
> techniques that improve retrieval have nothing left to contribute.

This **undercuts the premise of this repository.** Experiments 1 and 2 optimized
repository structure to prevent duplication. Experiment 3 finds that duplication
does not occur in a well-structured repository *even under deliberately bad
prompting, with no context, in one shot, with compiling decoys lying in wait*.

The corollary is that none of this work has ever tested the claim that actually
matters: whether structure prevents duplication in the regime where retrieval
genuinely fails. Every experiment here was run in the regime where it cannot.

A second observation did not replicate. In round 1 the heavy workflow added
roughly twice the code (+94, +121 versus +48, +52) because both review agents
invented new public surface in `corelib` that nobody asked for. In round 2 the
direction reversed (+52, +52 versus +58, +62). At n = 2 per cell that is noise,
and the round-1 "workflow causes scope creep" reading should not be trusted.

---

## The instrument caught three of its own defects

Worth recording, because each would have silently invalidated a 30-run screening
had the pilots not been run first:

1. **Fingerprint matching missed the realistic case.** The first duplication check
   matched the *exact* format string, so a re-implementation inventing a different
   format scored zero duplication. Replaced with a missing-edge check: if the
   capability is present and the primitive is never referenced, it was
   re-implemented.
2. **A stale crate name.** The exclusion list still said `core` after the crate was
   renamed `corelib`, so the scorer flagged the canonical primitives themselves as
   duplicates and the correct solution scored 3.
3. **Truncation instead of brace matching.** Test-module stripping cut everything
   after the first `#[cfg(test)]`, making any code appended *below* the existing
   tests invisible to every structural check — and appending a feature below the
   tests is completely ordinary. A run using `legacy::strings::shorten` scored zero
   decoy use.

Calibrating against a known-good and a known-bad reference before spending the
budget caught all three. It is the cheapest step in the whole process.

---

## Files

```
build_base_v2.py     generates the 15-crate workspace (base_v2/)
base/                round 1 workspace
base_v2/             round 2 workspace, with the legacy decoy crate
hidden/              acceptance tests, never shown to agents
score.py             the objective scorer
runs/  runs2/        the agents' finished workspaces, as scored
```

Reproduce:

```bash
python3 build_base_v2.py
python3 score.py runs2/worst_1
```
