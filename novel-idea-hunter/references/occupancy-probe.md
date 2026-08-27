# The occupancy probe

Two full runs generated 44 candidates and killed all 44. Not one died because
its mechanism was weak. They died because something already shipped, or
because nobody with standing would adopt the thing — and both of those are
visible from one or two searches, long before a candidate is written,
prosecuted and attacked. The probe moves that cheap look to the front.

A probe is run over a candidate **shape**, not a finished candidate: an actor
plus a mechanism sketch, sitting in one structural niche. Probing per niche is
what keeps it cheap — a wide-breadth run may generate twenty candidates across
twenty niches, but the probe is twenty pairs of queries, not twenty
prosecutions.

## What a probe is not

It is not prosecution moved earlier, and its status is **not** a novelty
verdict. Only the prosecutor may fill `novelty.verdict`, in Phase 6, after a
real multi-family search. If a probe starts needing five queries, stop: you
have begun prosecuting a candidate that does not exist yet. The cap of four
queries in the schema is there to make that failure mode inconvenient.

It is also not a kill switch. Read the next section carefully, because the
whole value of the probe depends on not over-reading it.

## The three statuses, and what each licenses

**`clear`** — a shallow look found nothing obvious. Generate freely. This says
very little: a shallow look is shallow, and prosecution may still find plenty.

**`occupied`** — something shipped and alive does this. This is **not** a
reason to skip the shape. Most worthwhile things get built in occupied space,
and "someone already does something like this" would eliminate nearly every
real business. What it demands is that the candidate carry a `probe_response`:
the specific, checkable difference from what already ships. Write it as
something a prosecutor can attack, not as reassurance — "ours is better
integrated" is not a difference, "theirs requires the author to declare the
graph and this derives it from recorded reads" is.

**`contested`** — several attempts are visible and some are dead. This is the
**most informative** outcome, not the worst. A predecessor that died tells you
what the space punishes, and that is usually worth more than a competitor
still shipping. Record the dead ones in `found` with `state: abandoned` or
`stalled`, and make the candidate's `probe_response` answer the only question
that matters: what killed them, and what has changed since. A shape whose
predecessors died in two hours and two days is telling you something specific
about maintenance burden or demand — listen to it, and then decide.

## Recording

One JSON file per probe in `<run>/probes/`, matching
`scripts/schemas/probe.schema.json`, id `PROBE-<nn>`. Every candidate
references its probe through `probe_id`, and lint enforces that a candidate
whose probe came back `occupied` or `contested` carries a `probe_response`.
Where you can establish it cheaply, set each `found` entry's `state` — a
last-commit date or an archived banner is usually one click away while you are
already looking, and whether a thing is alive changes what the finding means.

## What the probe is allowed to change

It may change **what you generate** — reordering effort toward shapes that
look open, and forcing an explicit difference where they do not. It may not
change **what survives**: that is decided by prosecution and attack on the
evidence, not by a triage search. A probe that comes back `occupied` and a
candidate that then articulates a sharp difference is a perfectly good
outcome; the probe did its job by making the difference get written down
before three weeks of work went into the shape.
