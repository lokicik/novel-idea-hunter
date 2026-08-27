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
6. **Collision search (maximum-distance pairing)**: deliberately pick the
   two clusters on the map that share the *least* — different lens,
   different actor, different vocabulary, no obvious reason to mention them
   in the same sentence — and force a mechanism connecting them anyway. This
   is where genuinely wild candidates come from: the reader's first reaction
   should be "wait, how do those connect?", answered by a mechanism that
   holds up under exactly the same rules as every other candidate. Wildness
   lives entirely in facet *distance* — never in relaxed evidence, a thinner
   mechanism, or a skipped falsification test. A collision-search candidate
   still needs ≥3 observations from ≥2 lenses and a real 2-4 step mechanism;
   the only thing that changed is how far apart the ingredients started. Hit
   rate is low by design — most attempts won't produce a real mechanism, and
   that is fine. Discard the ones that don't; a stalled attempt costs little
   and the occasional hit is worth more than another safe pain×capability
   candidate, because the archive already has plenty of those.

Moves 1-5 are the default funnel (any breadth). Move 6 is required in
proportion when a run declares `breadth: wide` (see SKILL.md Phase 4) —
that is the mechanical difference between asking for "more ideas" and
asking for "wilder ideas": more of moves 1-5 gives you more of the same
shape; a quota of move 6 forces the search into territory the safer moves
never reach.

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

## Self-refutation: read the evidence you are citing

Generation recombines the *map*, and the map is a compression. The compression
is where refutations go missing: the summary line survives into the candidate
and the caveat attached to it does not.

In one wide venture run, 4 of 19 candidates were killed by evidence sitting in
the observation records they themselves cited, in four distinct ways:

- **The caveat inside the cited record.** A candidate built on longitudinal
  baselines cited the observation establishing that mechanism — whose own text
  says baselines are worthless on thin files. Most of the candidate's target
  population had thin files.
- **A `why_now` that was the incumbent already doing it.** A candidate cited a
  marketplace refusing submissions in saturated categories as evidence the
  moment had arrived. That is the incumbent shipping the mechanism.
- **A workaround the map already recorded as free.** A candidate's gate ships
  as one rule among 34 in an anti-slop tool the run had itself observed.
- **A kill condition the cited operator had already published.** A candidate
  cited a bug-bounty closure as its trigger; the maintainer who closed it had
  publicly evaluated this exact mechanism, called it hostile, and closed the
  programme instead.

None of these needed a search to find. All four needed a re-read.

So before writing a candidate, open its cited observation records — the JSON,
not your memory of the map — and look specifically for the thing that cuts
against it. Write what you find into `self_refutation`, naming the observation
id. If the re-read genuinely turns up no counter-claim, say that, naming the
records you re-read. The lint requires the field and requires it to name an id
the candidate actually cites.

Two things this is not. It is not prior-art search — that is Phase 6, and it
costs a subagent. It is not a reason to drop the candidate: a named
counter-claim you can answer makes a stronger candidate, and answering it in
`self_refutation` is the point. What it eliminates is the candidate that dies
in prosecution to a fact you had already collected and filed.

## Descriptor discipline

Assign `descriptor` fields when the candidate is created, from the controlled
vocabularies in `candidate.schema.json` — not retroactively at portfolio time.
The descriptors are what stand between the portfolio and three-clones-in-a-
trenchcoat; late labeling degenerates into labeling whatever makes the
portfolio look diverse.
