# Novelty prosecution

The generator never grades its own novelty. Generators fall in love; and LLM
judges systematically overrate the novelty of LLM-generated ideas (the
"novelty mirage"). So novelty here is established adversarially, by retrieval,
under a prosecutor whose explicit objective is:

> **Prove this idea already exists. Success is measured by how thoroughly you
> destroy it.**

Run prosecution as a separate subagent where available; otherwise switch roles
explicitly in a fresh pass that takes only the candidate JSON as input — not
the generation context, which is contaminated with the reasons the idea seems
good.

## Query families

Search at least these families before any verdict. Record which were actually
searched in `novelty.scope_searched` (use these slugs):

1. `exact-product-shape` — the product as described, in several phrasings
2. `same-actor-same-workflow` — anything serving this actor in this workflow,
   regardless of mechanism
3. `same-mechanism-adjacent-actor` — this mechanism sold to neighbors
4. `same-pain-different-mechanism` — how the pain is being attacked otherwise
5. `open-source` — GitHub/GitLab implementations, including half-finished ones
6. `failed-products` — dead companies and shut-down products in this space
7. `academic` — papers and research prototypes
8. `incumbent-roadmap` — incumbents' changelogs, public roadmaps, and their
   users' feature requests begging for exactly this
9. `patent` — only where the mechanism is plausibly patentable

Where to look: general web, GitHub, Product Hunt, Hacker News (site-search
"Show HN"), YC company directory, app marketplaces of adjacent incumbents,
Crunchbase-style shutdown lists, Google Scholar.

## Verdict vocabulary

Exactly one of (lint enforces the vocabulary and its consistency rules):

- `duplicated` — a live product does substantially this, for this actor.
  Terminal: a duplicate cannot survive to the portfolio.
- `crowded` — several products adjacent enough that winning requires beating
  incumbents at their own game. Survivable **only** with edge status
  `credible` or better.
- `differentiated` — close prior art exists and is listed, with a specific,
  checkable difference per item. The normal good outcome.
- `no-close-prior-art-found` — nothing close found **after searching at least
  4 query families**, all listed in scope_searched. This is the system's
  ceiling claim. It is a statement about a search, never about the world.
- `unverified` — prosecution not yet run. Blocks advancement past `gated`.

For every verdict except `no-close-prior-art-found` and `unverified`,
`closest_prior_art` must be non-empty — a verdict must point at what it found.
Each entry carries a `difference` that is specific and checkable ("does not
watch provider version metadata"), not comparative fluff ("ours is better /
more integrated / smarter").

## Prosecution discipline

- Search before reading the candidate's own why-it's-novel notes, to avoid
  anchoring on the generator's framing.
- A near-miss is a finding, not a defeat: adjacent products define the
  differentiation surface, and their gaps are evidence.
- Finding a **failed** attempt is good news twice over: it validates demand
  existed and poses the question the candidate must answer — what killed them,
  and has that cause expired? Feed the answer back into `why_now`.
- Do not stop at the first hit. `duplicated` requires substantial overlap for
  the same actor; one adjacent product is `differentiated` material, not
  grounds for early exit.
- Numeric novelty scores ("novelty: 9.3/10") are banned. A score without
  retrieval behind it is an opinion wearing a costume.

## Honesty floor

If time or access constraints prevented a real search of 4+ families, the
verdict stays `unverified` and the candidate stays `gated`. An unverified
candidate can be interesting; it just cannot be called anything else yet.
