# Search lenses

Each observation branch runs exactly one lens. A lens is a way of looking, not a
topic: two lenses pointed at the same domain should come back with different
kinds of facts. Run branches in isolation — a branch must not see another
branch's findings, because the first interesting observation otherwise becomes a
gravity well that pulls every other branch toward it.

Branches collect **observations only**. If a branch starts writing product
ideas, that content is discarded. The idea-shaped thought a researcher has
mid-search is almost always the obvious one; the observation underneath it is
the valuable part. Record the observation, drop the idea.

Quick mode: pick the 3 lenses most likely to be information-rich for the
domain. Deep mode: run 6-8. The `private-edge` lens runs only when the user has
explicitly authorized private sources.

For every lens: prefer primary sources (the complaint itself, the changelog
itself, the pricing page itself) over articles about them. Record sources per
`evidence-rules.md`.

## capability-shifts

What became possible, reliable, or an order of magnitude cheaper recently —
and what that specifically unlocks.

Look at: model/provider changelogs and pricing pages, new API surface areas,
hardware cost curves, latency/quality benchmarks crossing usable thresholds,
newly opened data sources, new platform primitives (app stores, extension
points, protocols).

An observation here must name the threshold: "X used to cost/fail at Y, since
DATE it costs/succeeds at Z." "AI is getting better" is not an observation.

## manual-workflows

Work that trained people do by hand, repeatedly, that looks automatable but
is not automated.

Look at: job listings (the tasks section is a confession of manual work),
"day in the life" posts, procedure documents and runbooks, screen-recording
tutorials for internal processes, consultant deliverable templates,
spreadsheet-shaped work in any profession.

Record: who, the exact steps, frequency, time per occurrence, error cost.

## workarounds

Duct tape users built because no product exists. Workarounds are the strongest
demand signal there is: someone already paid with effort.

Look at: browser-extension hacks, popular Zapier/n8n/Make templates, GitHub
repos that glue two products together, "how I automated X with a cron job and
three scripts" posts, template marketplaces, spreadsheet templates people sell.

Record what the workaround does, what it costs to maintain, and where it
breaks.

## trust-bottlenecks

Places where work stalls because a human must verify, sign off, or absorb
liability.

Look at: compliance checklists, audit requirements, review/approval steps in
professional workflows, insurance and liability language, "a human must check
this" statements in docs and regulations, verification-as-a-service offerings.

Record who must trust whom, what evidence would transfer that trust, and what
the delay costs.

## ecosystem-breakage

Things that recently broke, got deprecated, got acquired-and-ruined, or got
priced out — leaving users stranded.

Look at: deprecation notices, pricing-change announcements and the angry
threads under them, "alternatives to X" search spikes, abandoned popular OSS
(high stars, dead commit history, open issues asking "is this maintained?"),
post-acquisition migration guides.

Stranded users are reachable users: they are actively searching.

## pricing-incentives

Mismatches between how incumbents charge and what users actually need —
the gaps incumbents cannot close without cannibalizing themselves.

Look at: per-seat pricing on usage-shaped products (and vice versa), enterprise
gating of features small users need, procurement thresholds, unbundling
opportunities in bloated suites, minimum-contract complaints, "we switched
because of pricing" posts.

Record the incumbent, the pricing structure, and why changing it would hurt
them more than a newcomer.

## failed-products

Products that died whose failure reason has expired.

Look at: shutdown post-mortems, Product Hunt launches from 3-8 years ago with
enthusiasm but no traction, YC company lists filtered to dead companies,
"whatever happened to X" threads.

For each: what was the stated or apparent cause of death — and is that cause
still alive? Too early, too expensive to build, distribution didn't exist yet,
a dependency was missing. A failure whose cause has expired is a pre-validated
idea with a warning label.

## cross-domain

Mechanisms that work in one industry and have no equivalent in a structurally
similar one.

Look at: how adjacent industries solved the same shaped problem (escrow,
clearinghouses, certification regimes, marketplaces, standard file formats,
insurance pools), tools every practitioner of field A has that practitioners
of field B — same workflow shape — lack.

Match structure, not vocabulary: see the relational-analogy rules in
`facets.md`. "Uber for X" is a vocabulary match; "field B has the same
asymmetric-trust structure that escrow solved in field A" is a structural one.

## private-edge (opt-in only)

The user's own repositories, notes, abandoned prototypes, past product ideas,
and recurring personal pain — crossed against public signals.

Rules, non-negotiable:
- Only run over sources the user explicitly authorized in this run's brief.
- Observations reference private material by opaque label
  (`private://repos/foo`), never by content. Private details never appear in
  candidates, reports, or search queries sent to the public web.
- The objective is not "ideas nobody thought of." It is: opportunities the
  user is disproportionately positioned to see or execute. Search for
  intersections between a private asset and a public gap.
