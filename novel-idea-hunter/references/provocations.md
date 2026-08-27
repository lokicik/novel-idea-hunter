# Provocations — making generation reach past the model's prior

## Why "generate crazier ideas" does not work

Telling a model to be more creative asks the thing that is narrowing to
un-narrow itself. It does not, for two documented reasons.

**Mode collapse is a property of alignment, not of effort.** Post-training on
preference data inherits a *typicality bias*: annotators systematically favour
familiar text, so the aligned model concentrates on typical answers. The fix
that works is structural, not motivational — prompting the model to verbalise
a *distribution* over answers with their probabilities, rather than to produce
an answer, recovers 1.6-2.1x diversity in creative writing and 2-3x more
broadly, at equal quality, with no training. More capable models benefit more.
([Verbalized Sampling, arXiv 2510.01171](https://arxiv.org/abs/2510.01171))

**Diversity saturates as generation scales.** In a 100+ researcher study, LLM
ideas were judged *more* novel than expert human ideas — but generating more
of them produced repetition rather than range, and the authors name lack of
diversity under inference-time scaling as an open problem, alongside idea
homogenisation. ([Si, Yang & Hashimoto, arXiv 2409.04109](https://arxiv.org/abs/2409.04109))

Read together: the ceiling is not candidate count and it is not the model's
capability. Raising `--max-survivors` or generating 40 instead of 20 buys
repetition. What buys range is forcing the generator off its own distribution.

## Move 1 — Verbalized sampling: generate the distribution, keep the tail

Do not ask for the candidate for a niche. Ask for **five candidates with the
probability you would have produced each**, then build out the ones in the low
tail — and record that probability on the candidate.

The typical answer is not wrong, it is *already known*, which in this pipeline
means it prosecutes as `crowded` or `duplicated`. The tail is where the
candidate that survives prosecution lives, and it is unreachable by asking
harder for a single answer.

Record the number. A run whose surviving candidates all came from the head of
the distribution has learned something about the territory; a run that never
generated a tail has learned nothing and should say so.

## Move 2 — Forced briefs, drawn outside the model

```bash
python3 "$SKILL/scripts/provoke.py" --run <run-dir> --count <n> --write
```

Each slot fixes three things the generator does not get to choose: an
`opportunity_pattern` the run has not mined, one of Altshuller's 40 TRIZ
inventive principles, and an inversion directive. The draw is seeded from the
run id, so it is reproducible and it is not taste.

TRIZ matters here because it is a catalogue distilled from patent analysis
rather than from business writing, so it sits outside the prior a model brings
to "startup idea" — the same reason TRIZ-structured prompting has been found
to produce better-justified conceptual directions than open-ended generation
([AutoTRIZ, arXiv 2403.13002](https://arxiv.org/html/2403.13002v2)).

Apply the principle to the **tension your map named for that cluster**, not to
the domain in general. The map's one-sentence tensions are contradictions in
the TRIZ sense already — "the work is real, continuous, and currently done for
free by people who are visibly running out" is a contradiction, and asking
what *Blessing in disguise* or *Preliminary action* does to it is a different
question from "what product solves this".

The physically literal principles are kept on purpose. Forcing *Thermal
expansion* or *Porous materials* onto a market mechanism is precisely the move
a model will not make unprompted, and the translation effort is where the
non-obvious candidate comes from. Sometimes it produces nothing.

**A brief that produces nothing is a result.** Record the slot and what you
tried. Do not silently reassign yourself an easier brief — quietly swapping a
hard slot for a comfortable one is how the funnel collapses back onto the
pattern the map flagged as richest.

## Move 3 — Gap-directed retrieval

Phase 1 searches the *domain*. After the first candidate wave, search what the
*current set lacks*: plan retrieval specifically to raise the novelty and
diversity of the candidates you already have, then generate against what comes
back. Iterating planning-and-search this way produced 2.5x more top-rated
ideas than the prior state of the art
([Nova, arXiv 2410.14255](https://arxiv.org/abs/2410.14255)).

Concretely: list the patterns and mechanism classes with zero candidates, and
run one narrow search per gap asking what exists in that corner of the
territory. This is cheap — it is the same shape as the Phase 3.5 occupancy
probe, and it feeds the same decision.

## What this does not buy

Range is not quality. The Stanford study found LLM ideas more novel *and*
slightly weaker on feasibility, which is exactly the failure mode a wider
funnel amplifies. Everything generated here still goes through the same slop
gate, the same prosecution, and the same attack. Widening generation without
the downstream filters produces confident nonsense at scale; the filters
without the widening produce this pipeline's characteristic result, which is
an honest zero.
