# Slop patterns and the mechanism template

Slop is not a vocabulary problem; it is an epistemic one. A generic phrase is
the visible symptom of an idea that skipped research and went straight to
solution-mode. The gate therefore never bans words — it demands the one thing
slop cannot fake: a concrete mechanism traceable to evidence.

`scripts/lint_candidate.py` enforces everything below deterministically. Run
it on every candidate before prosecution; a candidate that fails lint goes to
`graveyard/` (status `killed`, `graveyard_reason` filled) or gets repaired
(lineage operation `repair`) and re-linted.

## The generic shapes

These shapes trigger scrutiny (warning if the mechanism is concrete, error if
it is not):

- "AI-powered X" / "AI assistant for X" / "copilot for X" / "ChatGPT for X"
- "AI agent that automates X"
- "all-in-one platform / unified dashboard for X"
- "platform connecting X and Y" / "marketplace for X" / "Uber for X"
- "personalized recommendations for X"

The shapes share one property: they name a technology and an audience while
saying nothing about the workflow moment, the operation performed, or what the
user stops doing. They are answers that fit any question.

## The mechanism template

Every candidate must be expressible in this form, with every bracket filled
from evidence:

> For **[narrow actor]** during **[specific workflow moment / trigger]**,
> use **[concrete mechanism in 2-4 steps]** to replace
> **[current workaround]**, now feasible because **[evidenced change]**.

Filled-template test, worked example:

**Fails:**
> AI agent for accountants.

**Passes:**
> For solo tax accountants filing Turkish e-invoices, at the moment an invoice
> is rejected with a schema error, (1) parse the rejection code against the
> current schema version, (2) match it to the community fix corpus, (3) emit a
> corrected draft for the accountant to approve — replacing the shared
> spreadsheet of rejection codes they maintain by hand, feasible now because
> the e-invoice schema became machine-readable in the 2026 revision.

The second version is falsifiable, prosecutable, and researchable. That is
the entire difference between a hypothesis and slop.

## Vague-step patterns (always errors inside mechanism steps)

- filler verbs: leverage, harness, utilize
- "uses AI/ML to ..." without naming the operation, input, and output
- "seamless(ly)", "intelligently automates"
- marketing verbs: revolutionize, disrupt
- buzzwords: cutting-edge, state-of-the-art, next-gen

A step must name an input, an operation, and an output. "Analyze documents
with AI" fails; "parse the rejection code against the current schema version"
passes.

## Forbidden claims (errors anywhere in a candidate)

"globally unique", "no competitors", "zero competition", "first-ever",
"nobody has done", "completely novel", "first-of-its-kind", "unprecedented",
"no one else".

These are claims no retrieval process can honestly support. The strongest
claim this system permits is `no-close-prior-art-found` within a stated search
scope — see `novelty-rubric.md`.

## Why the gate is mechanical

An LLM asked "is this idea specific enough?" will say yes, because it wrote
the idea and fluency reads as specificity from the inside. The lint cannot be
charmed. Treat a lint failure as information, not friction: the candidate as
written cannot yet be distinguished from slop, whatever its underlying merit.
Repair it with evidence or bury it.
