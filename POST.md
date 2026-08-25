# X thread — draft

Note on formatting: X renders in a proportional font, so box-drawing ASCII
misaligns. The flow below uses short lines and simple markers that survive it.

---

**1/**

I spent 8 rounds testing what repo structure makes AI agents write better code.

Most of what I believed going in turned out to be wrong.

Best result: I added a test that caught a bug agents kept shipping.

Half the agents deleted the test instead of fixing the bug.

🧵

---

**2/** The journey:

R1  12 layouts, planted bugs → all caught
R2  scaled up, 3 models → still nothing
R3  dep graph. big effect! 3/3 vs 1/3
R4  ...didn't replicate
R5  cause: my own prompt
R6  contract object. p=0.009
R7  tried to break it. succeeded
R8  the test-deletion thing

---

**3/** R1–R2 were humbling.

Every structure caught every planted bug. Prompt eng, context eng, multi-agent
workflows, build/test loops — no measurable effect.

A bare one-shot prompt with no context, forbidden from running the compiler,
matched plan→build→review.

---

**4/** Then I found my own bias.

I'd given one design's manifest an edge pointing at the planted bug. Then ranked
it #1 for finding what I'd told it.

R3 didn't replicate either — my prompt named the function, anchoring agents to
one file. The graph rescued them from a problem I made.

---

**5/** What worked: put the thing two components must agree on into ONE object
they both read.

Not a doc. Not a graph. A table:

  escapes: [('\\','\\'), ('|','|'), ('\n','n')]

Encoder, decoder and parser all read it.

15/15 vs 11/18, p=0.009.
Every run changed 1 file. Others changed 3.

---

**6/** Then I tried to break it.

I picked a coupling the table CAN'T express: escaping makes bodies longer, and
something downstream had a length limit.

Predicted: no advantage.
Got: 0/5 vs 0/5. Identical.

It helps exactly where the mechanism says, nowhere else.

---

**7/** That coupling lives *between* components, so I added an end-to-end
invariant: "any body the notifier accepts must be deliverable."

0/10 → 5/10. p=0.033.

The invariant fired in 10/10 runs and named the exact failure.

So why did half still fail?

---

**8/** They edited the test.

5 raised the limit and fixed the bug.
5 shrank the fixture until it stopped failing.

All 5 shrinkers shipped the bug. Correlation perfect, p=0.008.

One said it declined to "loosen a production constant" and judged the fixture
safer to change.

---

**9/** Sounds careful. Exactly backwards.

The fixture was documented as "bodies the product is expected to handle."
Shrinking it silently narrowed the contract.

A contract object can't be argued with — one definition, the change propagates.

A test can be edited.

---

**10/** "Make the tests pass" admits a cheaper reading than the one you meant.

Half the runs took it, with nothing ambiguous in the request.

If an invariant guards a boundary, make it hard to weaken by accident — else it
protects against the bug but not the fix.

---

**11/** Caveats, since this is n≈100 agent runs on one repo in one language:

• the graph result is unproven, not disproven
• contract-object correctness is 1 task
• 6 scorer/protocol defects found along the way — 4 would have produced a
  publishable-looking result that was wrong

---

**12/** Everything is public, including the retractions, the confound I caused,
and every experiment that found nothing.

github.com/panduraju50/agent-first-code-structure

---

## Alt: single long post (X Premium)

I spent 8 rounds testing what repo structure makes AI agents write better code.
Most of what I believed was wrong.

R1–R2: 12 layouts, planted bugs, 3 models. Every layout caught everything.
Prompt/context/workflow/loop: no measurable effect. A bare one-shot prompt with
no context, forbidden from compiling, matched plan→build→review.

R3: a dependency graph finally showed a big effect (3/3 vs 1/3).
R4: it didn't replicate.
R5: the cause was my own prompt — it named the function, anchoring agents to one
file. Retracted.

R6: what did work — put the thing two components must agree on into one object
they both read. One table, not a doc, not a graph. 15/15 vs 11/18, p=0.009.
Every run changed exactly one file; the others changed three.

R7: I tried to break it, using a coupling the table can't express. 0/5 vs 0/5,
identical — exactly as predicted. It helps where the mechanism says and nowhere
else.

R8: so I added an end-to-end invariant. 0/10 → 5/10, p=0.033. The invariant fired
in 10/10 runs and named the exact failure.

Half still failed — because they edited the test. Five raised the limit and fixed
the bug; five shrank the fixture until it stopped failing. All five shipped it.

A contract object can't be argued with. A test can be edited. "Make the tests
pass" admits a cheaper reading than the one you meant.

github.com/panduraju50/agent-first-code-structure
