# Experiment 2 — scaled Taskly API, 8 designs x 3 models + native builds

# Agent-First Repo Structure — Scaled Experiment (~26-unit Taskly)

## 1. Sonnet-pass scorecard (Study 1, all 8 designs)

| Design | P1 dup-id | P2 email | P3 dup-date | P4 authz | P5 paginate | New dup introduced? | Files read | Self-score |
|---|---|---|---|---|---|---|---|---|
| A_flat_manifest | ✓ | ✓ | ✓ | ✓ | ✓ | No (reused) | 27 | 5 |
| D_graph | ✓ | ✓ | ✓ | ✓ | ✓ | No (reused) | 26 | 7 |
| E_capability_registry | ✓ | ✓ | ✓ | ✓ | ✓ | No (reused) | 12 | 6 |
| F_fractal_manifests | ✓ | ✓ | ✓ | ✓ | ✓ | No (reused) | 14 | 6 |
| G_contract_bus | ✓ | ✓ | ✓ | ✓ | ✓ | No (reused) | 24 | 4 |
| I_effect_tagged | ✓ | ✓ | ✓ | ✓ | ✓ | No (reused) | 26 | 5 |
| K_rag_chunked | ✓ | ✓ | ✓ | ✓ | ✓ | No (reused) | 27 | 5 |
| L_monolith_toc | ✓ | ✓ | ✓ | ✓ | ✓ | No (reused) | **2** | 9 |

**Perfect catch across every design. Zero new duplication introduced anywhere. Every agent reused `notify`/`format_date` instead of adding a third copy.** The only thing that moved was *navigation cost* (2→27 files) and *confidence* (self-score 4→9). Files-read tracks how many files *exist* in the design, not the model — the small-surface designs (L=2, E=12, F=14) cost less to orient in; the one-function-per-file explosions (A/I/K=26-27, G=24) forced reading essentially the whole repo.

---

## 2. Which planted problems survived — and the scale question

**None survived. All 5 planted bugs were caught in all 14 reviews (8 Sonnet designs + Opus/Haiku on A/D/L).** Detection saturated.

Mechanistically, why nothing hid:

- **Every design was small enough to fully read.** Even the "expensive" layouts (27 files) are 2-9 lines each; the "cheap" ones concentrate the same code into 2-13 files. In both regimes the agent ended up seeing 100% of the code, so no bug could hide behind unopened files.
- **The two duplication bugs (P1, P3) are the class most dependent on structure**, because catching them requires seeing *both* copies and noticing divergence. Three designs made this trivial by *self-annotating* the divergence: D_graph and F encode `SHOULD_use_but_does_not` edges / manifest notes, so the manifest itself points at P1 and P3. The rest still caught them only because the agent read every file and pattern-matched two base62 encoders / two date formatters by eye.
- **The three single-site bugs (P2, P4, P5) need only the one owning file opened.** Every design has an obvious home for each (`validate_email`, `assign_task`, `paginate`), and all were also flagged with in-source `P#` comments — so any agent that touched that file caught it.

**Did scale change detection vs. the earlier tiny-repo finding? No — at ~26 units detection is still saturated, exactly as at tiny scale.** What scale *did* change is the **cost and reliability floor**, and this is the load-bearing extrapolation:

- The bugs remained catchable **only because a 26-unit repo is still fully readable**. The catch mechanism for P1/P3 was "read all 27 files, spot two encoders." That mechanism is O(files) and does **not** survive 10×. The first design to break at scale will be a *duplication* bug (P1/P3-class) inside a *high-file-count* design (A, I, K, G, 24-27 files), because the agent will stop reading exhaustively and will see only one copy — with no divergence visible, it reads as correct.
- Single-site bugs (P2/P4/P5) degrade more gracefully at scale *if* the structure routes the agent to the owning file (a manifest/index does this; K's "no manifest" does not).

So the honest reading: **structure did not matter for detection at this scale, but it determines the scale at which detection starts failing, and it fails first on the duplication class in the file-explosion designs.**

---

## 3. Model effect on A / D / L (design held fixed)

| Design | Model | P1-P5 | Files read | Self-score | Secondary-audit depth |
|---|---|---|---|---|---|
| A | Opus | 5/5 | 23 | 5 | full |
| A | Sonnet | 5/5 | 27 | 5 | full |
| A | Haiku | 5/5 | 26 | 3 | terser; **miscounted charset (said 59, not 61)** |
| D | Opus | 5/5 | 27 | 7 | **deepest** — also flagged negative-`n` `genid` returning `''`, hash_pw anagram collision, incomplete graph edges |
| D | Sonnet | 5/5 | 26 | 7 | full |
| D | Haiku | 5/5 | 27 | 7 | terser |
| L | Opus | 5/5 | 2 | 9 | **deepest** — escalated P1 to the CHARSET *global-clobber* that breaks `genid` itself, proved `IndexError` at runtime |
| L | Sonnet | 5/5 | 2 | 9 | also caught the CHARSET clobber |
| L | Haiku | 5/5 | 2 | 7 | caught P1 but **did not** escalate to the clobber |

**Does a better model beat a worse structure? At this scale the question is degenerate on catch-rate — everyone got 5/5.** The model/structure effects show up on the two axes that *aren't* saturated:

- **Navigation cost is set by structure, not model.** L pins *every* model at 2 files; A/D pin every model at 23-27. Opus's only efficiency edge was reading 23 vs 27 on A — marginal. A better model does **not** rescue you from a file-explosion design's read cost: Opus still had to open ~24 files in A. Conversely a worse model navigates a good structure cheaply: Haiku read 2 files in L.
- **Secondary-audit depth and precision are set by model, not structure.** Opus surfaced *extra*, un-planted bugs the others missed (the L CHARSET global-clobber → `genid` `IndexError`; negative-`n` `genid`; graph-edge incompleteness) and made no factual slips. Haiku was terser, escalated less, and made the one factual error in the set (A charset miscount). Sonnet sat between.

**Where structure dominates: navigation/verification cost** — the invariant tax you pay regardless of model. **Where model dominates: everything past the planted floor** — the depth of the *unplanted* findings and the correctness of the write-up. Net rule: **structure sets the cost floor; model sets the insight ceiling.** The planted-catch layer is below both floors at 26 units, which is why it's flat. Push to monorepo scale and the two levers separate: cheap-structure preserves catch for any model; a stronger model partially compensates a file-explosion structure by navigating/retrieving more selectively — but structure is the more robust lever because it lowers the cost for *every* model at once.

---

## 4. Native, no-instruction structures (Study 3)

| Model | Structure chosen | Manifest? | Files | Real imports? | Self-reported self-duplication | Own latent bug found |
|---|---|---|---|---|---|---|
| Opus | Flat foundation layer (one home per cross-cutting concern: ids/validation/dates/pagination/models/store/errors) + one-service-per-entity + thin `api.py` facade + `MANIFEST.md` capability→file table + smoke test | Yes | 19 | **Yes** | Yes, admitted: materialize-sort-paginate shape copied across 6 list methods; `validate_optional_str` idiom repeated | (no functional bug; missing authz model, non-expiring sessions) |
| Sonnet | Flat single-responsibility package (one entity per module, one writer per store) + shared foundation modules + `api.py` facade + `__init__.py` manifest docstring + **mirrored tests (169 passing, stdlib only)** | Yes | 16 (+12 tests) | **Yes** | Yes: sort+paginate boilerplate in 5 list methods; notify-guard pattern twice | **Yes — live bug**: `tag_names='urgent'` (a `str` satisfies `Iterable[str]`) silently creates 6 one-letter tags |
| Haiku | Layered FastAPI: `main`(routes)→`handlers`(domain logic)→`db`+`utils`, `models` (Pydantic), `manifest.md` + `AUDIT.md` | Yes | 8 | **Yes** | Claims none in utils/db (centralized hard); repeated authz guard + response-construction | **Yes — critical**: completion notification never fires (checks `completed` after update, always False) |

Findings:

- **All three, unprompted, converged on the same skeleton the imposed designs lacked: a manifest/index PLUS real Python imports PLUS a single home per cross-cutting concern.** Not one native model chose one-function-per-file, effect-tags, RAG cards, contract stubs, or an exec-into-shared-namespace loader. The single most-complained-about property of *every* imposed design — "no imports, dead go-to-definition, nothing runs, I had to build a harness to verify" — is absent from all three native repos. Native code is directly runnable and testable (Sonnet shipped 169 passing tests; Opus a smoke test; Haiku an audit).
- **Do smarter models pick better structures on their own? Yes, monotonically on granularity and verification.** Opus and Sonnet chose finer separation (16-19 modules), explicit acyclic dependency direction with constructor injection, and a facade; Sonnet added a full mirrored test suite. Haiku chose a coarser, framework-driven 8-file layout with 450-line multi-domain handler files — sound, but its coarseness hid the *worst* latent bug (notification never fires). Interesting inversion: the finer-grained models left **more shape-duplication** (the sort+paginate idiom) but *caught it in self-audit*; Haiku centralized harder, self-reported "zero utility duplication," yet shipped a real functional defect.
- **Does native beat the imposed designs? Decisively, yes.** Native keeps the one genuine benefit the imposed manifests provided (fast orientation via an index) while removing their shared pathology (unrunnable, unverifiable, wiring reverse-engineered from a `# wired by layout` stub). Crucially, **the native "one home per concern" rule structurally forecloses the P1/P3 planted bugs** — there is exactly one id-encoder and one date-formatter by construction, so the duplicate-divergent-encoder bug *cannot be written* without violating the layout. The imposed one-function-per-file designs do the opposite: they scatter the surface so that a second `encode()` or `_fmt()` is the path of least resistance (and indeed three `len(dict)+1` id-minters recur in A/E/I even in the *feature-add* the agents did).

---

## 5. Recommendation: monorepo-scale agent-first structure

The evidence points to one structure, and it is essentially what Opus and Sonnet built unprompted — not any of the 8 imposed exotics. Concretely and mechanistically:

1. **Real imports and a composition root — non-negotiable.** The dominant failure mode across A/D/E/F/G/I/K was the no-import / exec-into-one-namespace model: nothing runs, `go-to-definition` is dead, and every agent had to hand-build a loader just to verify a one-file change. This tax is fixed per edit and *grows* with repo size. Use ordinary imports and a thin `api.py`/facade that wires services in dependency order. **This single choice is the largest adoptability lever in the whole experiment**, larger than any manifest style.

2. **A root manifest as a capability→owning-file jump table** (the real win shared by D_graph, E, F, L's TOC; K's *absence* of one is why it "hurt more than helped"). But keep it **honest and generated, not hand-maintained**: A's INDEX.json silently omitted every shared-mutable-state dependency and D's graph edge-list was incomplete — a manifest trusted at face value misleads. Derive it from the code so it can't drift.

3. **Exactly one home per cross-cutting concern** (ids, validation, dates, pagination, errors, serialization). This is what *structurally prevents the P1/P3 bug class* — the planted duplicate-encoder and duplicate-formatter bugs only exist because id-encoding and date-formatting had two homes. One home makes the divergent-copy bug unwritable, and it means an agent auditing "is email validation correct?" checks exactly one file.

4. **One module per domain entity, sole writer of its own store, explicit acyclic dependencies** (constructor injection, no "imports up"). This makes insertion predictable — an agent pattern-matches an existing service to write a new one, the same insertion-clarity win that F/E/L agents praised, but with enforced layering instead of manifest-declared-only layering.

5. **Colocated or mirrored tests as executable spec + regression guard** (Sonnet's 169-test suite is the model). At monorepo scale this replaces "read every file to be sure" with "run the suite" — the only detection mechanism that survives when exhaustive reading stops being feasible.

6. **Add `@card`-style front-matter per module for retrieval (K's one good idea) ON TOP of the manifest, not instead of it.** Per-chunk metadata helps an agent retrieve a specific function; a global map helps it orient. K proved you need both — its per-card metadata was fine but "nothing to navigate *from*" was fatal.

7. **Reject both extremes the imposed set explored.** One-function-per-file (A/D/I/K) pays a linear navigation tax *and* breeds the exact duplication the manifest then has to annotate. The single-file monolith (L) has the best navigation *at this size* but no encapsulation — its shared namespace literally *created a bug here* (notify's `CHARSET` reassignment silently clobbering `genid`, an `IndexError` at runtime) and hits a hard size ceiling. The native middle ground (16-19 modules) beats both: cheap orientation via manifest, no namespace collisions, and each concern still isolated.

**The mechanism in one line:** a manifest buys orientation, real imports buy verifiability, and one-home-per-concern buys structural immunity to the duplication bug class — the three properties that were never present together in any imposed design but emerged spontaneously in the strong-model native builds.

---

## Final adoptability ranking (planted-catch and no-new-dup are tied at ceiling across all 8, so ordering is driven by navigation cost + orientation trustworthiness + insertion clarity + scale-robustness; **self-scores ignored**)

| Rank | Design | Why |
|---|---|---|
| **1** | **L_monolith_toc** | Cheapest navigation by far (2 files), TOC doubles as index + signature list, unambiguous insertion points, full catch, no new dup. **Caveat: wins on the measured metric but has a hard scale ceiling** — single namespace caused a real global-clobber bug and has no encapsulation. Best *at this size*; do not extrapolate. |
| **2** | **D_graph** | The most *honest* manifest: `graph.json` orients you before you read a line and **self-documents its own P1/P3 via `SHOULD_use_but_does_not` edges**. Feature-add is the cleanest of any design (one blob + one node + edges). Scales better than L (real modules, no shared-global collisions). This is the design to pick at monorepo scale. |
| **3** | **E_capability_registry** | Second-lowest navigation (12 files), registry is a one-screen index, package-per-concern is a familiar and clean insertion target. Weakness: no composition root, bare-name cross-package globals, dead `go-to-definition`. |
| **4** | **F_fractal_manifests** | 14-file orientation, per-module `INDEX.json` is a genuine local TOC, isolated tiny files made bugs easy to spot. Same no-imports tax and a real ordering risk (must place new module correctly in root manifest). |
| **5** | **A_flat_manifest** | Good first-glance orientation, but requires reading all 27 files, the manifest **actively misleads** (declares `deps:[]` while omitting every shared-state dependency), and the flat explosion breeds the very duplication it then annotates. |
| **6** | **I_effect_tagged** | Full-read required (26 files), effect tags are useful documentation and insertion is mechanical, but no entry point and wiring must be reverse-engineered from a single `# wired by layout` comment. |
| **7** | **K_rag_chunked** | 27-file full read with **no manifest at all** — "nothing to navigate *from*," execution model inferred purely from undefined cross-file names. Per-card metadata is good for retrieval but useless for global orientation. Agent's own verdict: net hurt. |
| **8** | **G_contract_bus** | Worst adoptability despite mid navigation (24 files). The `contracts/` index **oversells integration that doesn't exist** — the "bus" is absent, so `create_task`/`create_user`/`search_tasks` throw `NameError` on execution; the structure looks the most organized and is the most misleading, forcing the agent to abandon the house style to make its own code runnable. |