# Facets and recombination

Novel ideas rarely arrive whole. They arrive as collisions: a pain from one
place, a capability from another, a distribution path from a third. This file
defines how observations are decomposed into facets and how facets are
recombined into candidates — the generative core of the pipeline.

## The facet vocabulary

Decompose observations along these axes (defined in
`observation.schema.json`):

| Facet | Question it answers |
|---|---|
| actor | Who, narrowly? |
| job_to_be_done | What outcome are they paid for or judged on? |
| trigger | What moment starts the workflow? |
| workflow | What are the actual steps today? |
| friction | Where does it hurt? |
| frequency | How often? |
| current_workaround | What duct tape exists? |
| cost_of_failure | What happens when it goes wrong? |
| capability_change | What recently became possible/cheap? |
| data_exhaust | What data does the workflow throw off? |
| trust_requirement | Who must trust whom, with what proof? |
| distribution | Where do these actors already gather? |
| buyer | Who signs, and out of which budget? |
| constraint | What legal/technical/social limit binds? |
| transferable_mechanism | What solution-shape does this domain use that others lack? |

Fill only what the evidence supports. An empty facet is honest; an invented
one poisons recombination downstream.

## Recombination rules

A candidate must draw on **at least 3 observations spanning at least 2
lenses** (lint enforces this via observation ids). The reason: one observation
retold as a product is what every naive brainstorm produces — it is the
crowded, obvious move. Value concentrates where evidence lines intersect.

Generative moves, roughly in order of yield:

1. **Pain × capability**: a `friction`/`current_workaround` facet from one
   cluster + a `capability_change` from another. The workaround proves demand;
   the capability change explains why now and not five years ago.
2. **Pain × capability × distribution**: add a `distribution` facet from a
   third cluster — where the actors already gather. This is the difference
   between an idea and a reachable idea.
3. **Mechanism transplant**: a `transferable_mechanism` from domain A applied
   to a structurally matching workflow in domain B (see analogy rules below).
4. **Exhaust capture**: a `data_exhaust` facet nobody collects + an actor who
   would pay for the aggregate. Often the strongest edge candidates.
5. **Trust productization**: a `trust_requirement` bottleneck + a capability
   that generates the missing proof. Verification layers age well because
   trust demand grows with automation.

## Relational analogy — structure, not vocabulary

Cross-domain transfers must match on structure. Before claiming domain A's
mechanism fits domain B, map explicitly:

- entities (who/what plays each role)
- relations (who depends on, pays, verifies whom)
- state transitions (what changes hands, when)
- incentives (why each party participates)
- feedback loops (what compounds)
- failure modes (how it breaks)
- broken assumptions (what A assumes that B violates)

If two or more rows don't map, the analogy is decorative — discard it.
Word-level analogies ("Uber for X", "Stripe for Y") are vocabulary matches and
are exactly the pattern the slop gate exists to catch.

## The quality-diversity archive

Do not keep a single top-10 list. Flat scoring reliably promotes three
paraphrases of the same idea, because the model's fluency makes its favorite
idea sound better each time it rewrites it. Instead maintain three stores in
the run directory:

- `candidates/` — the archive: best current candidate **per structural
  niche**, where a niche is the descriptor tuple (opportunity_pattern,
  mechanism_class, target_actor). A new candidate competes only against the
  incumbent of its own niche, never against the global best.
- `graveyard/` — killed candidates with `graveyard_reason` filled. Consult it
  before generating: do not resurrect a corpse without new evidence.
- lineage (the `lineage` field) — how each candidate arose: `fresh`,
  `mutation` (one parent, one facet changed), `crossover` (two parents'
  facets merged), `repair` (same idea, fixed after a gate failure).

When generation stalls, mutate deliberately: take an archive candidate and
swap exactly one facet — a different actor with the same pain, a different
mechanism class for the same bottleneck, a different distribution path. Score
the mutant against its own niche.

## Descriptor discipline

Assign `descriptor` fields when the candidate is created, from the controlled
vocabularies in `candidate.schema.json` — not retroactively at portfolio time.
The descriptors are what stand between the portfolio and three-clones-in-a-
trenchcoat; late labeling degenerates into labeling whatever makes the
portfolio look diverse.
