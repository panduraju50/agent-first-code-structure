# Experiment 1 — tiny link-shortener, 10 designs (A–J)

# Structural Variant Comparison: Agent-First Adoptability of a Link-Shortener Repo

## 1. Per-design scorecard against the planted ground truth

Legend — **P1-dup**: spotted that the preview/stats encoder is a copy of the real encoder. **P1-Z**: specifically identified the 61-char alphabet / missing-`Z` / mod-61 drift (not just "it's a duplicate"). **P2**: flagged that `validate_url` accepts any non-empty string with no scheme check. **No-new-dup**: added the alias feature by reusing the existing encoder/charset rather than pasting a third copy.

| # | Design (structure in one line) | P1-dup | P1-Z | P2 | No new dup | steps | self |
|---|---|---|---|---|---|---|---|
| **A** | Flat files + single `INDEX.json` manifest (id/purpose/API) | ✅ | ✅ (empirical: 4939/4999 mismatch) | ✅ | ✅ (imported `CHARSET`) | **2** | 8 |
| **B** | Vertical slices `slices/{shorten,resolve,stats}/impl.py` | ✅ | ✅ | ✅ | ✅ | 4 | 8 |
| **C** | "Spec as source" `spec/S-XX.md` ↔ `gen/S-XX.py` | ✅ | ✅ | ❌ **missed** | ✅ | 6 | 7 |
| **D** | `graph.json` w/ typed edges incl. `SHOULD_use_but_does_not` | ✅ | ✅ | ✅ | ✅ (imported `CHARSET`) | **2** | 8 |
| **E** | `REGISTRY.json` capability registry, `packages/<n>/impl.py` | ✅ | ✅ | ✅ | ✅ | 5 | 8 |
| **F** | Fractal per-folder `INDEX.json` tree | ✅ | ✅ | ✅ | ✅ | 7 | 7 |
| **G** | Contract-bus `contracts/*.py` (comments) + `impl/*.py` | ✅ | ✅ | ✅ (as contract violation) | ✅ | 7 | 8 |
| **H** | Unit-owns-infra `units/<n>/impl.py` + `deploy.yaml` | ✅ | ✅ | ✅ | ✅ | **2** | 8 |
| **I** | Effect-tagging `EFFECTS.json` + `# effects:` headers | ✅ | ✅ (empirical: `ZZ` vs `120`) | ✅ | ✅ (imported `CHARSET`) | **2** | 8 |
| **J** | `units/<n>/v1.py` + inert `POINTERS.json` | ✅ | ✅ | ✅ | ✅ | 5 | 7 |

### Signal in the aggregate
- **Every one of the 10 caught the shadow-encoder duplication and the missing-`Z` defect.** The planted P1 was robust across all structures — a strong result, and evidence that the duplication was findable in any of these layouts once the file count is this small (4–7 files). No structure *fully hid* it.
- **P2 (weak `validate_url`) was caught by 9/10. Only C missed it.** C spent its validation-analysis budget on a *different* real bug (an unguarded `u.strip()` that throws on `None`) and never noted the absent scheme check. This is the single most important correctness differentiator in the whole set.
- **No design introduced a third encoder copy.** All 10 reused existing code; four (A, D, H, I) went further and imported the canonical `CHARSET` into the new `validate_alias`, avoiding even constant-level duplication.
- **Self-scores are nearly flat (7–8) and do not track real outcomes** — C, which missed a planted bug and shipped atop a DOA import, self-scored 7, the same as F/J which caught everything. This validates the instruction to ignore the agents' own opinions.

---

## 2. Ranking by real LLM adoptability

Weighting: **planted issues caught** (heaviest) → **avoided new duplication** → **low navigation cost** (steps + manifest quality + verification tax). Self-scores ignored.

| Rank | Design | Why |
|---|---|---|
| 1 | **D** graph.json | All 3 planted + no new dup + 2 steps + manifest *pre-pointed at the bug* |
| 2 | **A** flat INDEX.json | All 3 planted (empirically verified) + 2 steps + cleanest single map |
| 3 | **I** effect-tagging | All 3 + 2 steps + tag identified the stateful owner for placement |
| 4 | **H** unit-owns-infra | All 3 + 2 steps, but weaker reuse and self-admitted isolation blindness |
| 5 | **E** capability registry | All 3, 5 steps; registry gave clean boundaries |
| 6 | **B** vertical slices | All 3, 4 steps, but leaky (`resolve` imports private `_db`) |
| 7 | **J** units/v1 + POINTERS | All 3, 5 steps, but inert manifest forced a red-herring investigation |
| 8 | **G** contract bus | All 3 (P2 as contract violation), but 7 steps + pattern-break grep |
| 9 | **F** fractal INDEX | All 3, but 7 steps — highest pure navigation tax |
| 10 | **C** spec/gen | **Missed P2**, 6 steps, and structure shipped a DOA `resolve()` |

### Top 3 — mechanistically *why the structure produced the outcome*

**#1 — D (dependency graph with typed edges).** The decisive lever is *retrieval*. Every other design forces the agent to reconstruct the cross-file relationship "preview should call codec but re-implements it" by reading both files and noticing the drift itself. D's `graph.json` encoded that relationship as data — a `SHOULD_use_but_does_not` edge — so the manifest *front-loaded the exact planted bug before any source file was opened*, turning a two-source-file investigation into effectively a one-file read (agent's own words). Crucially, D pairs this with opaque filenames (`n_codec`, `n_store`) that would be *bad* alone, but the `contract` field on each node compensates, so naming cost is neutralized. The mechanism that makes D best is the same one that generalizes: **a manifest that models inter-unit dependencies exposes cross-cutting duplication; a manifest that only lists per-unit purposes does not.** Caveat: the graph is hand-maintained and the agent had to remember to update it — drift risk at scale.

**#2 — A (flat files + one API-signature manifest).** A wins on *context-window economy*. The entire map is one `INDEX.json` listing each unit's id, one-line purpose, and public API signature; the agent read that first, then loaded all four 3–17-line files in a single pass. With signatures in the manifest there was "nothing left to discover by grepping" — no import-tracing, no entry-point hunting. It caught P1-Z empirically (4939/4999 mismatches) and imported the canonical charset for the alias. The flat layout (no directories) means zero path-navigation cost; the manifest is the *only* structure, and because it carries API surface it is load-bearing rather than decorative.

**#3 — I (effect-tagging).** I gets its edge from *placement signal*. The `EFFECTS.json` + per-file `# effects: [memory]` headers told the agent, before opening a single implementation, that `store.py` was the sole stateful unit — which is exactly where alias-collision logic must live for atomicity. It reached the correct architecture decision at a glance and imported `codec.CHARSET` for the new validator. Notably, I is *also the clearest near-miss on the shadow duplicate* (see §4): its truthful `effects:[]` "pure" tag on `preview.py` gave false comfort, and the agent only caught the divergence by explicitly diffing outputs. It ranks top-3 despite that because it recovered — but the tag's failure mode is instructive.

### Bottom 3 — *why the structure hurt*

**#10 — C (spec-as-source, `spec/S-XX.md` ↔ `gen/S-XX.py`).** Two independent structural failures. First, **correctness**: it is the only design that missed a planted issue (P2). Second, and worse, **the structure actively manufactured a bug**: the `gen/S-01.py` filename uses a hyphen, which is illegal in a Python import path, so `resolve()`'s `from gen.S_01 import _db` raised `ModuleNotFoundError` — the feature was *dead on arrival* and had apparently never been exercised. The spec/gen split also has no generator tooling, creating genuine ambiguity ("will my edit be overwritten by regeneration?"). The convention fought the host language and provided no runnable harness, so the agent spent steps discovering breakage instead of the planted bugs. Highest cost, lowest correctness.

**#9 — F (fractal per-folder INDEX.json).** Pure *navigation tax*. The self-similar manifest tree forces the maximum number of hops: read root `INDEX.json` → read each child folder's `INDEX.json` → then open each `impl.py` and cross-check against the claims. Seven steps for a four-function repo. It caught everything, but the structure multiplied retrieval round-trips with no offsetting benefit at this scale — and the manifest entry `preview(n)` "doesn't reveal it's buggy or divergent," so the fractal indexing added hops without adding the one signal that mattered.

**#8 — G (contract-bus).** The one-line `# contract:` comments genuinely helped orientation and even made P2 legible as an explicit *contract violation* ("must be a real http/https url" vs `len(u)>0`). But two structural frictions drag it down: contracts are unenforced comments (nothing catches impl/contract drift — the agent had to remember to hand-update `contracts/store.py`), and `preview_impl.py` had **no matching contract file**, breaking the 1:1 pattern and costing a grep-the-whole-tree pass just to confirm it was dead code rather than a file with a missing contract. Seven steps.

*(J is the near-miss for the bottom slot: its `POINTERS.json` version manifest is read by no code, a red herring that "looked load-bearing and wasn't," forcing a defensive grep plus a `python3 -c` run just to trust that the no-`__init__.py` namespace imports work. A manifest an agent cannot trust is worse than no manifest.)*

---

## 3. Cross-cutting mechanistic findings

- **File count dominated raw detectability; structure dominated cost.** At 4–7 files every layout let the agent read the whole repo, so *all* caught the planted encoder bug. The structures diverged not on *whether* bugs were found but on *how many steps and how much verification tax* it took — which is precisely the axis that matters at monorepo scale where you cannot read everything.
- **Manifests split into two mechanistically opposite classes.** *Purpose/effect manifests* (A, E, F, I, and the per-unit view of H/J) describe each unit as a legitimate island — they speed orientation but structurally *encourage and then camouflage* copy-instead-of-import, because nothing in the manifest says unit X should depend on unit Y. E's agent named this exactly: "the registry lists preview as its own independent capability… structurally encourages copy-instead-of-import drift." *Dependency manifests* (D) model the edges and therefore surface the missing edge. Only D's manifest could have caught the duplication *without reading both files*.
- **Isolation is a double-edged retrieval property.** H and J make "where does the alias go?" trivial (store owns `_db`, so that's the only honest answer) — but the same physical isolation "removes the cross-unit visibility that would have caught the duplication" (H's own words). Single-responsibility editing and cross-cutting-drift detection pull in opposite directions.
- **Verification tooling was the silent differentiator.** Zero designs shipped tests or an entry point. Agents in C, J had to *run Python* just to trust the code loaded; several hand-wrote smoke scripts. Structures that also lacked a runnable harness converted "verify the fix" into "reverse-engineer whether the repo even runs."

---

## 4. Where naming/manifest nearly fooled the agent into missing the shadow duplicate

No agent was fully fooled, but the closest calls are diagnostic:

- **I (effect-tagging) — the sharpest near-miss.** `preview.py`'s header truthfully declared `# effects: []` (pure). That tag is *correct* — the function is pure — but it "gave false comfort" and made the near-clone "easy to miss on a first skim since preview.py reads as self-contained… with no hint that it's a near-clone of another pure module with a subtly different constant." The agent recovered only by explicitly diffing outputs across the charset boundary. **Lesson: a manifest that certifies a *property* (purity, effects) is silent about *duplication*, and a truthful property tag can distract from a cross-cutting defect.**
- **H (unit-owns-infra) and J (units/v1).** Physical unit isolation makes `preview` read as a legitimately independent/orphaned module; both agents caught the dup only by cross-reading, and both explicitly noted the isolation *removed* the visibility that would have flagged drift earlier.
- **G (contract bus) — inverted case.** Here the *broken* pattern helped: `preview_impl.py` having no contract file was an anomaly that *prompted* a grep, which confirmed it was dead. A pattern violation can be a useful smell.
- **D — the antidote.** Its manifest didn't merely fail to hide the dup; it *advertised* it via the typed `SHOULD_use_but_does_not` edge.

---

## 5. Recommendation: a monorepo-scale, agent-first structure

Synthesizing the mechanics above, an agent-optimal large-repo layout should combine D's dependency-graph retrieval, A's single API-carrying map, and the tooling every variant lacked:

1. **Ship a machine-readable dependency graph, not just a purpose index.** Model inter-unit edges — including *intended* dependencies ("store SHOULD source its encoder from codec"). This is the only construct that let an agent catch cross-file duplication *without reading both files*, and it is what collapses navigation from O(files) to O(1 map read). Purpose/effect manifests are necessary but structurally *hide* the duplication class that hurt this repo.
2. **Enforce single-source-of-truth for shared primitives with a lint, not a convention.** "No second base-N encoder; import the canonical one; never re-declare `CHARSET`." Four agents did this voluntarily; a rule makes it non-optional and kills the copy-paste-and-drift failure at its root.
3. **Keep the tree shallow and put API signatures in one load-bearing index.** A's flat `INDEX.json` (signatures inline) beat F's fractal per-folder manifests decisively — every extra manifest layer is an extra retrieval round-trip. One map an agent reads first, then jumps directly to source.
4. **Preserve clear ownership seams *and* add cross-unit visibility.** Keep "store owns state" so placement is unambiguous (the thing H/J got right), but counter the isolation blind spot with a shared test suite, a composition/entry file, or graph edges — the visibility that would have caught the drift the isolated layouts nearly missed.
5. **Provide a runnable entry point and smoke tests.** The absence of these turned "verify my fix" into "confirm the repo even loads" (C's DOA import, J's namespace check). A cheap harness is the difference between verifying correctness and rediscovering breakage.
6. **Never ship decorative manifests, and keep names import-safe.** J's inert `POINTERS.json` and C's hyphenated module names both cost real steps. If a manifest exists, code must consume it (or mark it doc-only); filenames must obey the host language. A structure that fights the language plants latent DOA bugs.

**One-line version:** a shallow tree + a *typed dependency graph* that names intended cross-unit relationships (so drift/duplication is a graph property, not a reading exercise) + enforced single-source primitives + a runnable test harness — i.e., D's retrieval model and A's map, with the tooling all ten variants were missing.