# Proprietary-edge verification

"Novel" and "proprietary" are different claims. A novel idea found by
searching the public web is, by construction, findable by anyone else with the
same tools — recent work shows different models converge heavily on the same
open-ended ideas. An edge is what makes an opportunity *disproportionately the
user's*: an asset, access path, or accumulation loop that a competent
competitor cannot cheaply copy.

The right objective is therefore not "an idea nobody has thought of" but:
**"an opportunity the user is disproportionately positioned to see or
execute."**

## Edge statuses

Assign exactly one (requirements enforced by lint):

**`none`** — no defensible edge identified. Honest and common, and **not a
disqualification**. A candidate with `none` can still be a fine business — it
just wins on execution, and the report must say so plainly. Edge answers
"can this be defended over years"; whether it can be started at all is a
different question that belongs to Attack. Note also that a public-web-only
run caps every candidate at `none` by construction, so in such a run this
status carries no information about any individual candidate — treating it
as a signal there is a category error, and it is exactly the error that
silently eliminated nineteen candidates across two early runs.

**`potential`** — a plausible edge is named (`asset` filled) but not yet
verified: e.g. "the user's regression tracker audience could seed
distribution" before checking the audience is real and relevant.

**`credible`** — the edge is verified on four axes:
- `asset` — the concrete thing: a dataset, an audience, an operating
  workflow, rare domain-expertise intersection, a distribution position.
- `control` — the user owns it or has durable, **legally usable** rights.
- `copy_difficulty` — why a competent, funded competitor cannot replicate it
  within a quarter or two.
- `proof_metric` — a measurable check that the edge is real (conversion from
  the audience, accuracy delta from the dataset, cycle-time from the
  workflow).
Plus `evidence_observation_ids`: the edge must trace to observations like
everything else. An edge nobody observed is a wish.

**`compounding`** — credible, **plus** a working accumulation loop:

```
usage → unique data or operational learning → measurably better product
      → stronger retention or distribution → more usage
```

Name each arrow concretely. "More users means more data" is not a loop unless
the data measurably improves the product in a way users notice, and that
improvement measurably drives retention or acquisition.

## What does not count (lint rejects these in credible+ claims)

- **First-mover advantage.** Being early is a head start, not an asset.
- **Employer-owned assets.** Access through a job is not ownership; it
  evaporates with the badge, and using it may be a breach besides.
- **Customer-confidential material.** Not legally usable; also not yours.
- **Temporary API or partner access.** Durable edges survive a partner's
  pricing committee.
- **"We'll have the best model/prompts."** Model access is symmetric;
  prompt quality is replicable by anyone with the output in hand.

## Private-edge handling

When the run includes the `private-edge` lens, edge claims may rest on private
observations. The report still never exposes private content — reference the
opaque labels (`private://...`), describe the *shape* of the asset ("a
three-year corpus of X with Y coverage"), and keep the details out of
candidates and search queries. If the user later shares the report, nothing
in it should leak what only they know.

## Grading discipline

The edge status feeds the survivor rules (a `crowded` market requires
`credible`+), so the temptation to inflate is structural. Counter it: grade
edge **after** prosecution and attack, in the same adversarial spirit — the
question is not "what edge would help?" but "what edge is proven?" When in
doubt between two statuses, assign the lower one and record what evidence
would upgrade it as part of the falsification plan.
