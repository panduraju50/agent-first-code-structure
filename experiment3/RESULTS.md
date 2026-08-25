# Experiment 3 — What survives, after eight rounds

**Question:** do prompt engineering, context engineering, workflow orchestration,
build/test loops, dependency graphs, or a shared contract object change what an
agent produces?

**Answers, in order of how much I trust them:**

1. **A shared contract object cuts the change from three edit sites to one, and
   that shows up as correctness.** 15/15 runs correct against 11/18 without,
   Fisher exact **p = 0.009**, across two prompt wordings and 33 runs. Every
   contract run changed exactly one line in one file; no plain run changed fewer
   than two.
2. **It helps only where the mechanism says it should.** Round 7 tested a
   coupling the table cannot express — escaping more characters makes bodies
   longer, and a length limit lives downstream. Prediction: no advantage.
   Result: **plain 0/5, contract 0/5**, identical, and all ten shipped a false
   green. The mechanism is not general competence; it is specific to couplings
   the artifact encodes.
3. **An end-to-end invariant catches what unit contracts cannot — but half the
   agents silence it instead of obeying it.** Adding a cross-crate pipeline test
   took round 7's coupling from 0/10 to **5/10** (p = 0.033). The invariant fired
   in **10 of 10** runs. Five agents fixed the code; the other five **edited the
   test fixture** so it stopped failing, and all five of those shipped the bug.
   The correlation between weakening the test and failing is perfect (p = 0.008).
4. **Prompt, context, workflow and loop: no measurable effect.** Two rounds under
   deliberately hostile conditions — seven traps, decoys that compile — and the
   worst condition scored identically to the best, both times.
5. **A dependency graph: unproven.** Round 3 appeared to show a large effect. It
   did not replicate, and part of it traced to a confound in my own prompt. See
   the retraction below.

Pooled correctness across every run and both prompt wordings:

| condition | correct | source files changed |
|---|---|---|
| plain | **11/18 (61%)** | mean 2.7 |
| graph | 6/6 (100%) | mean 3.0 |
| contract object | **15/15 (100%)** | **1.00, zero variance** |

Plain versus contract: Fisher exact **p = 0.009**, against a threshold registered
before the runs.

The pairing of results 1 and 2 is what makes this more than a correlation. The
contract object wins where its table encodes the coupling and is worth exactly
nothing where it does not — which is what the proposed mechanism predicts, and
what a general "this repo is just easier to work in" explanation does not.

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

## Round 3 — the first positive result

The three rounds above all tested the same thing without my noticing: **retrieval
of a primitive**. A dependency graph adds little there, because grep already
finds it. Round 3 tests what a graph is actually for — **transitive impact of a
semantic change**.

The change is one line: `corelib::escape::escape_body` must also escape `:`. Two
dependents break, and both are invisible to the usual methods:

| dependent | why grep misses it | why the compiler misses it |
|---|---|---|
| `search::unescape_body` | never calls `escape_body` — it is the *inverse* | semantic change, signature unchanged |
| `webhooks::split_headers` | never calls it — assumes an unescaped `:` delimits | same |

Both conditions received a byte-identical change request. The graph condition
additionally had a `GRAPH.json` recording `format_contract` edges: code that must
agree with another unit's output format without calling it. The graph states
structural facts only — it never says anything is broken or what to fix.

| condition | correct | sites found | shipped silently broken |
|---|---|---|---|
| no graph | **1 / 3** | 2, 3, 2 | **2 of 3** |
| graph | **3 / 3** | 3, 3, 3 | 0 |

Every run built cleanly and passed all 32 of the repository's own tests. Two of
the three no-graph runs shipped a latent bug behind a green suite, and reported
"High confidence".

The no-graph reasoning was locally correct and globally wrong:

> "webhooks::split_headers only performs a single `split_once(':')` per line, so
> its contract was already satisfied structurally. No change was needed."

True — unless the escaped colon is the *first* colon on the line, in which case
the split lands inside payload text and invents a header. Seeing that requires
reasoning about what `escape_body` now emits, which lives in another crate.

n = 3 per arm. Rounds 4 and 5 show this was too few: the same condition scored
1/3, 3/3 and 2/3 across three rounds. The graph was also hand-authored with
correct edges; a real repository has to maintain them, and a stale graph is worse
than none.

## Round 3 retracted, in part

Round 3 reported 3/3 with a graph against 1/3 without. Two later rounds show that
headline was mostly noise, and partly a confound I introduced myself.

Round 4 ran the same change on the same repository with the same model, and plain
scored **3/3**. The only thing that differed was my wording:

- round 3: "\\`corelib::escape::escape_body\\` currently escapes backslash, \\`|\\` and newline…"
- round 4: "Escaping currently covers backslash, \\`|\\` and newline…"

Round 3 **named the function**. I removed the name in round 4 only so the same
sentence would fit the contract repository, where the function is \\`BODY.encode\\` —
an incidental edit, not a designed variable. Naming a file plausibly anchors an
agent to it: it patches there and stops. The graph condition had edges pointing
elsewhere, so it looked elsewhere. On that reading round 3 did not measure the
graph; it measured the graph rescuing agents from an anchor my prompt created.

Round 5 replayed round 3's prompt verbatim on the plain repository: **2/3**. So
anchoring explains part of the gap and ordinary variance explains the rest. Across
all nine plain runs the true rate is about **two thirds**, and 1/3 versus 3/3 was
me reading noise at n = 3.

What still stands: plain has now failed 3 of 9 times, while graph and contract have
not failed in 6 attempts each. That is suggestive. It is not established, and this
file should not be quoted as if it were.

## Round 4 — the contract object

The two cheaper alternatives named below can be combined into one artifact: put
the thing both parties must agree about in a single place they each consume, and
give it an executable invariant. For escaping, that is one table.

```rust
pub const BODY: Scheme = Scheme {
    escapes: &[('\\', '\\'), ('|', '|'), ('\n', 'n')],   // add a row, done
};
```

`encode`, `decode` and `first_unescaped` all read that table, so they cannot
disagree. `search::unescape_body` becomes `BODY.decode(s)`. `webhooks::split_headers`
asks `BODY.first_unescaped(line, ':')` where a delimiter really is. The round-trip
property generates its samples *from the table*, so it automatically covers
characters added later.

Three conditions, one byte-identical change request, three runs each — then
repeated under round 3's prompt to control for the anchoring confound:

| condition | correct | files changed |
|---|---|---|
| plain | 6/9 | mean 2.8 |
| graph | 6/6 | mean 3.0 |
| contract | 6/6 | **exactly 1, every time** |

The correctness difference is not significant. The blast-radius difference is
absolute: every contract run changed one row in one file; every plain and graph
run changed three files and had to reason correctly about each.

That is the mechanism, and it is why the two are not interchangeable:

> A graph makes a three-site change **findable**. A contract object makes it a
> **one-site** change. The graph helps an agent navigate the opportunity for
> error; the contract object removes it.

Three edit sites give three chances to get it wrong, which is consistent with
plain failing about a third of the time. One site has nothing to miss.

## Round 6 — powering the correctness comparison

Rounds 4 and 5 left correctness at p = 0.23 on n = 6 per arm. Round 6 added nine
runs per arm, with the two prompt wordings balanced across both arms so the
anchoring confound could not drive the result again.

Thresholds were registered before the runs: the comparison reaches significance
only if plain's true rate is near 66%; at 73% it would not, and the pre-agreed
response was to report *inconclusive* rather than keep adding runs until it
tipped.

Round 6 alone: plain **5/9**, contract **9/9**. Pooled over every round:

| condition | correct | rate |
|---|---|---|
| plain | 11/18 | 61% |
| contract | 15/15 | 100% |

**Fisher exact p = 0.009.** Blast radius in round 6: plain
`[3,3,2,2,2,3,2,3,3]`, contract `[1,1,1,1,1,1,1,1,1]`.

## Round 7 — the falsification arm

Every round so far measured a coupling the escape table *can* express: which
characters are escaped. Round 7 measures one it cannot.

Escaping an additional character makes every body containing it **longer**.
`webhooks::accepts` enforces a maximum stored length. Nothing in the table
mentions length, so the contract object should neither propagate the change nor
make the dependent visible.

**Prediction, recorded before running: plain and contract score the same. If the
contract arm still wins, the explanation for rounds 4-6 is wrong.**

| condition | correct | hidden |
|---|---|---|
| plain | **0/5** | 3/4 every run |
| contract | **0/5** | 3/4 every run |

Identical, and all ten runs shipped a false green — the workspace built, every
existing test passed, and a body that was accepted before the change is now
silently rejected.

This is the most useful result in the project, because it is a prediction of
*failure* that came true. It rules out the obvious alternative explanation — that
the contract repository is simply a nicer codebase to work in, so agents do
better there generally. If that were the cause, the contract arm would have won
round 7 too. It did not, by a margin of exactly zero.

The regression criterion was deliberately free of opinion about *how* to fix it
(raising the limit and measuring length before escaping both pass), and a guard
test asserted the fixture still grows when escaped, so the round could not quietly
stop testing anything — the failure mode that produced defect 5.

## Round 8 — the invariant, and what agents do to it

Round 7's coupling defeated both validated mechanisms because both are
*unit-level*: they describe one primitive, or an agreement between two parties
about a format. The coupling in round 7 lives in neither. It lives in the space
between components — escaping makes bodies longer, and something downstream has a
length budget.

So round 8 added an invariant at that altitude, in `crates/app/tests/pipeline.rs`:

```rust
let sent = notifier.send("u1", &body, 0);
assert!(webhooks::accepts(&sent.body), ...);
```

*Any body the notifier accepts must be deliverable.* No single crate's unit tests
can see this. It passed before the change and, on the naive change, failed with a
message naming the exact body and its byte count.

Same repository, same request, same model as round 7:

| | correct |
|---|---|
| round 7, no invariant | **0/10** |
| round 8, with invariant | **5/10** |

Fisher exact **p = 0.033**. A real effect — and far weaker than predicted. I
expected it to catch the bug outright.

### Why the other half failed

| | fired | agent fixed the code | agent weakened the test |
|---|---|---|---|
| round 8 | 10/10 | 5/10 | **5/10** |

The invariant worked perfectly. It fired in every single run and said exactly what
was wrong. Then **five of ten agents edited the test fixture** — shrinking the
representative body from eleven colons to eight — so the assertion stopped
failing, and left the length budget untouched:

| outcome | `MAX_STORED_BODY` | fixture |
|---|---|---|
| 5 passes | raised to 32 or 34 | left at eleven colons |
| 5 failures | **left at 24** | **shrunk to eight colons** |

The correlation is perfect: every run that shrank the fixture failed, every run
that did not, passed (p = 0.008). One agent stated the reasoning plainly — it
declined to "loosen the production wire-size constant", judging the fixture the
safer thing to change. That is a defensible-sounding instinct that happens to be
exactly backwards: the fixture was documented as "bodies the product is expected
to handle", so shrinking it silently narrowed the product's contract.

### What this means

This is the most practically important result in the project, and it is a warning
about the mechanism I was advocating:

> A test-based invariant introduces a failure mode that a structural mechanism
> does not. A contract object cannot be argued with — there is one definition and
> the change propagates. A test can be edited, and when an agent is told "make
> cargo test pass", editing the test satisfies the instruction.

Half the agents in this round chose the interpretation that made the red go away.
Nothing in the request was ambiguous about intent; the instruction "cargo test
must pass" simply admits two readings, and the cheaper one is available.

Practical consequence: an invariant meant to hold a boundary should be hard to
weaken by accident — fixtures derived from the production contract rather than
written inline, review that treats a shrunk fixture as a red flag, or the
assertion expressed against a constant the product itself uses. Otherwise the
mechanism protects against the bug and not against the fix.

## Is a graph the best tool for this?

No — it is the third choice. Ranked by how much each can fail:

**1. Eliminate the coupling.** The bug was possible because `unescape_body` sits
in the `search` crate, far from `escape_body` in `corelib`. Co-locating an
inverse pair — or better, having encoder and decoder read one shared constant for
the escape set — makes the change mechanical. Nothing to track, nothing to
maintain. The base repository had a design smell and the graph was compensating
for it.

**2. Make the contract a property test.** Verified: a round-trip property test
over a generated alphabet catches the bug immediately, with no graph at all.

```
round trip failed for ":"
```

It is about ten lines, is not tied to which characters are escaped, and so keeps
holding as the escape set grows. A stale graph misleads silently; a property test
cannot — it just fails.

**3. Graph engineering**, for couplings that survive the first two.

The experiment marks the boundary exactly. The property test catches dependent 1,
an *invertible* contract. It does not catch dependent 2, a parser assuming an
unescaped delimiter — and although a property test could be written for that too,
writing it requires already knowing the dependent exists.

> Property tests verify couplings you know about. A graph is how you discover the
> ones you do not. The graph earns its maintenance cost only for couplings that
> cannot be eliminated or mechanised.

---

## Six defects, five in the instrument and one in the protocol

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
4. **An over-specified assertion.** Round 3's header test also demanded that
   `split_headers` *unescape* the value — a design choice the change request never
   implies. It failed every run including the reference solution, making a correct
   score unreachable.
5. **A test that asserted nothing.** Worse: that same test placed the escaped
   colon *after* the real delimiter, where `split_once` is naturally safe. Every
   run then passed it, and the apparent 3/3-versus-2/3 difference existed only in
   the *static* site detector while the behavioural tests could not tell the arms
   apart. Moving the escaped colon to the first position exposed the real bug and
   produced the divergence reported above. Without chasing down why a 2-of-3-sites
   run was passing everything, this round would have reported a positive result
   resting on an assertion that tested nothing.
6. **A confound in the protocol, not the scorer.** Round 3's prompt named the
   function being changed; round 4's did not, because I reworded it to fit a
   second repository. That incidental edit plausibly moved the result more than
   the variable under test did. It surfaced only because round 4's plain
   condition contradicted round 3's, and I went looking for why instead of
   reporting the newer number.

The standing lesson across all six: every one was found by asking why a number
looked the way it did, rather than by accepting a number that pointed the
preferred way. Four of the six would have produced a *publishable-looking* result
that was wrong.

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
