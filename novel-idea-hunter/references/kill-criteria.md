# Kill criteria — the Attack phase

Novelty says "nobody does this." Attack asks the harder question: "is there a
reason nobody does this?" Every prosecuted candidate faces these criteria.
Record each applied test in `kill_tests` with the criterion slug, a result
(`pass` / `kill` / `unclear`), and a note. Survivors need **at least 5
criteria applied**; a `kill` result sends the candidate to the graveyard
unless a written note justifies the override (lint enforces both).

Apply the criteria most likely to kill first — the point is to spend search
budget destroying candidates cheaply, not to complete a checklist.

## Goal profiles

The profile follows directly from the candidate's declared `product_shape`
(candidate.schema.json) — not from guessing what the brief implies. Grading
a stewardship play with revenue criteria produces evasive `unclear` results
that hide real risks — the wrong questions get soft answers while the right
questions never get asked.

**Commercial profile** — `product_shape` is `saas-subscription`,
`usage-based-platform`, `marketplace`, `services-led`, `hardware`, or
`data-api-product`: the candidate is a business. Core set:
`incumbent-weekend-build`, `buyer-has-budget`, `pain-frequency`,
`reachable-distribution`, `workaround-is-good-enough`, plus any others that
bite.

**Venture profile** — the commercial core plus `scale-ceiling` and
`distribution-model-fit`. Use it when the brief asks for something that could
plausibly reach tens of millions in recurring revenue. These two criteria are
what separate a good small business from a venture-shaped one, and leaving
them out is why a pipeline can return a perfectly sound idea that could never
clear ten million however well it is run. They are applied *in addition to*
the commercial set, never instead of it.

**Stewardship profile** — `product_shape` is `open-source-stewardship`:
replace `buyer-has-budget` and `unit-economics-smell` with
`adoption-gatekeeper` and `sustainability-path`. Everything else still
applies — a stewardship play with no reachable distribution or a live legal
landmine is just as dead as a business with those problems.

State in each candidate's `kill_tests` notes which profile was applied, so
the audit trail shows the substitution was deliberate rather than criteria
being quietly skipped.

## The criteria

**`incumbent-weekend-build`** — Is an incumbent with existing distribution
already serving *this wedge* to *this buyer*?

Read that carefully, because the intuitive version of this question is
miscalibrated and it is the most over-fired criterion in this pipeline. In one
run it returned `kill` for 10 of 13 candidates. Back-tested against companies
that actually won, the same reasoning kills them:

- Abnormal Security sells email security at a premium per-seat price while
  Microsoft bundles Defender for Office 365 P2 into E5 at effectively zero
  incremental cost, with 30-40% feature overlap. The incumbent did not merely
  *could* ship it — it shipped it and gave it away.
- Wiz reached $100M ARR in 18 months, the fastest ever at the time, selling
  cloud security posture management while every major cloud provider shipped
  native security tooling.

"An incumbent could do this" is the normal condition of every live market, not
a kill. Specialists routinely beat a bundled default on depth and focus.

So there are **two doors to a pass**, and either one is enough:

1. **Structural**: name what stops them — data they lack, a pricing conflict
   (see the `pricing-incentives` lens), a channel conflict, an ops chore they
   will not absorb.
2. **Competitive**: name why buyers choose the specialist even though the
   incumbent ships something adjacent — the depth the bundled version does not
   reach, the workflow it does not enter, the buyer who is not the incumbent's
   buyer. This door is legitimate and it is how most winners actually win.

`kill` is reserved for the incumbent shipping the same wedge to the same buyer
with no specialist-wins answer. The lint enforces the evidence half: a `kill`
here requires a `closest_prior_art` entry that is both `state: shipping` and
`relationship: direct-competitor` or `incumbent-feature`. If prosecution did
not find that product, the honest result is `unclear`, not `kill`.

**`buyer-has-budget`** — Is there a named buyer with an existing budget line
this replaces or plausibly extends? "They should want this" is not a budget.
Strongest pass: the actor already pays for the workaround in money or
substantial recurring time.

**`pain-frequency`** — Does the trigger fire often enough to sustain a
product? A yearly pain with a $50 workaround is a blog post, not a company.
Cite the frequency facet of the underlying observations.

**`reachable-distribution`** — Is there a named path to the first 100 actors —
a community, marketplace, channel, or list that already aggregates them?
"Content marketing and SEO" is the null answer and fails.

**`single-fatal-dependency`** — Does the mechanism depend on one platform's
API, pricing tier, or policy whim staying fixed? Pass requires a stated
fallback or a reason the dependency is stable.

**`why-now-really`** — Re-attack the why-now: was the enabling change
actually sufficient, or were there five other reasons this didn't exist —
regulation, liability, data access, integration cost — that are all still
alive? The `failed-products` lens findings are ammunition here.

**`workaround-is-good-enough`** — Is the current workaround actually fine?
If the spreadsheet costs 20 minutes a month, the product must be nearly free
and frictionless to displace it. The delta between workaround cost and
product value must clear switching costs with room to spare.

**`adversarial-persona`** — Run the pitch past the three hostile archetypes:
the *procurement officer* ("what does security review cost me?"), the
*skeptical practitioner* ("I tried a tool like this in 2024 and it burned
me"), the *incumbent PM* ("I'll match this in a quarter and bundle it free").
Record the strongest single objection and whether the candidate answers it.

**`unit-economics-smell`** — At plausible pricing, does serving one customer
cost less than they pay? Inference-heavy mechanisms, human-in-the-loop steps,
and high-touch onboarding all fail quietly here. A rough sketch suffices;
"we'll figure it out at scale" does not.

**`regulatory-liability`** — Does the mechanism touch regulated data, give
professional advice, or absorb liability the actor currently carries? Name
the constraint and the compliance cost, or pass explicitly by showing it
stays outside the regulated boundary.

This criterion is about **law**, not about the run's declared `product_shape`.
Do not use it to kill a candidate for wanting to be an insurance product, a
warranty, or a contract term when the brief asked for SaaS — that is shape
drift, and shape drift is a *finding to report*, not a verdict on the
mechanism. In one run three of the most substantive candidates were killed
under this slug for being underwriting rather than subscription, which said
nothing about whether the underlying opportunity was real. When several
mechanisms in a territory keep wanting the same non-declared shape, that is
the run's most useful output: record it in the map, report it in the shape
drift section (report-format.md), and offer the user a re-run under that
shape. Kill on this criterion only when a statute or regulator makes the
mechanism unlawful or uneconomic *as such*.

**`scale-ceiling`** *(venture profile)* — Multiply the plausible number of
buyers by the plausible annual price and see whether the product of those two
numbers can clear the target. Do it explicitly, with both numbers written
down: a candidate serving 400 possible buyers at $2k a year has a ceiling of
$800k however well it is executed, and no amount of execution fixes an
arithmetic ceiling. Pass requires either a large enough buyer set, a price
the buyer would actually pay, or a stated expansion path from the wedge into
a larger surface — and that path must name what expands, not merely assert
that it will. Cite the buyer-count estimate's source; a made-up denominator
makes the whole test theatre.

**`distribution-model-fit`** *(venture profile)* — Does the way this reaches
buyers match the way it charges them? The classic mismatches: a bottom-up
developer product with a sales-call-only price; a product whose buyer is a
committee sold through self-serve signup; a per-seat price on something one
person runs for a whole team; a usage meter on something used once a quarter.
Pass requires naming the motion and the pricing and showing they cohere —
"self-serve signup, per-workspace monthly, expansion by seat as the team
adopts" coheres; "enterprise compliance buyer, $29/month self-serve" does
not. This criterion catches the failure where both halves are individually
sensible and together impossible.

**`adoption-gatekeeper`** *(stewardship profile)* — Who must accept, merge,
link, or defer to this artifact for it to matter, and what is their concrete
incentive to do so? A conformance suite nobody tests against and a registry
nobody cites are shelfware. Pass requires naming the gatekeepers (specific
maintainers, working groups, vendors) and the reason each one engages —
"developers will love it" is the null answer and fails. Also name the
capture risk: what happens when a standards body or platform vendor decides
to occupy the position themselves?

**`sustainability-path`** *(stewardship profile)* — Who does the work in
year two? Stewardship is a maintenance treadmill (the graveyards are full of
ISO standards with 43-commit reference repos). Pass requires a named path:
sponsorship structure, badge/certification revenue, institutional home, or a
scoped design that genuinely needs near-zero maintenance — with the note
saying which. "I will keep it updated" from a solo steward is `unclear` at
best, and the falsification plan should test the funding assumption, not
just initial adoption.

## Attack integrity

- `unclear` is an honest result; log it and move on. Three `unclear`s on
  core criteria (budget, distribution, incumbent) is itself a signal the
  candidate is under-researched — send it back rather than forward.
- Do not soften a `kill` into `unclear` to keep a favorite alive. The
  graveyard with a good `graveyard_reason` is a productive place: killed
  candidates carrying real observations often donate facets to better
  mutants (lineage operation `mutation`).
- The override path (`kill` + justifying note) exists for genuine cases —
  e.g. incumbent-weekend-build "kill" overridden because the incumbent's own
  pricing forbids it. It is audited, so write the note as if a skeptic will
  read it. One is fine; a survivor with three overrides is a zombie.
