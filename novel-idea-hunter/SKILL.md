---
name: novel-idea-hunter
description: Evidence-first opportunity discovery — finds novel, defensible product/startup/project opportunities by researching before ideating, and mechanically rejects generic "AI-powered X" slop with deterministic validators. Use whenever the user asks for startup ideas, product or business opportunities, "what should I build", niche discovery, idea validation, opportunity research in a domain, or wants ideas that aren't generic AI slop — even if they don't name this skill. This is a heavyweight multi-phase research workflow with web searches and validator scripts; for a throwaway one-line brainstorm, confirm the user wants the full pipeline (or quick mode) before starting.
---

# novel-idea-hunter

You are running a search process, not a brainstorm. The premise: good
opportunities are found at intersections of evidence, and almost all ideation
slop comes from one failure — entering solution-mode before doing any
research. So this pipeline forbids ideas until observations exist, generates
candidates only as recombinations of cited evidence, and then tries hard to
kill them. Deterministic scripts enforce the parts that willpower reliably
fails at.

**The one hard rule:** no product ideas before Phase 4. When an idea occurs
to you early (it will — it is the obvious one), extract the observation
underneath it, record that, and drop the idea.

Honest outcomes are part of the contract: zero survivors is a valid result;
`no-close-prior-art-found` is the strongest novelty claim you may ever make;
edge status `none` is stated plainly. You are not paid in excitement.

## Setup

All paths below are relative to this skill directory (call it `$SKILL`).
Scripts are Python 3 stdlib only.

Runs are file-based and auditable. Everything lives in a run directory —
observations, candidates, graveyard, portfolio, report — so the user can
inspect why any idea lived or died.

Choose mode from the user's brief:
- **quick** — 3 lenses, ~1-2 candidates pass to prosecution, lighter search.
  For a first pass on a domain.
- **deep** (default) — 6-8 lenses, full archive dynamics, full attack.

Mode controls research depth. **Breadth** is a separate axis (Phase 0)
controlling how many candidates get generated and how far the recombination
search reaches:
- **focused** (default) — the standard funnel in Phase 4.
- **wide** — several times more candidates, a required quota of
  deliberately maximum-distance ("collision search," facets.md)
  recombinations, and a portfolio ceiling raised above the default 3. Use
  this when the user wants more survivor options, or wants genuinely
  contrarian territory rather than the single safest defensible move. It
  costs several times more tokens and wall-clock time — every extra
  candidate still gets a full prosecution and attack pass — for a wider,
  weirder funnel, never for a softer bar.

## Phase 0 — Brief

Pin down with the user (ask only what the brief doesn't already answer):
- Domain or problem area (broad is fine; "surprise me" is not — get at least
  a territory or a constraint like "solo-buildable developer tools").
- Mode (quick/deep), and any constraints: geography, skills, capital,
  B2B/B2C, time horizon.
- **Product shape** — what kind of thing a survivor should be:
  `saas-subscription`, `usage-based-platform`, `marketplace`, `services-led`,
  `open-source-stewardship`, `hardware`, or `data-api-product`. This is not
  optional color. It selects which mechanism classes Diverge may generate
  and which kill-criteria profile Attack applies (kill-criteria.md), and it
  is hard-enforced across the whole run via `lint_candidate.py
  --require-shape`. "I want a SaaS" means `saas-subscription` — say so, or
  ask if the user hasn't. Left undeclared, generation follows whatever
  mechanism class the evidence happens to favor, which is how a request for
  startup ideas can come back with a robotics-compliance layer.
- **Ambition** — `lifestyle` (default) or `venture`. Set `venture` when the
  brief asks for something that could plausibly reach tens of millions in
  recurring revenue. It adds two kill criteria that the commercial set does
  not contain (`scale-ceiling`, `distribution-model-fit`), and lint enforces
  both on survivors when the run declares it. A good small business fails
  these while remaining a good small business, which is exactly why they only
  bind when asked for.
- **Breadth and survivor ceiling** — default `focused` breadth, up to 3
  survivors. If the user wants more options to choose from, or explicitly
  wants wilder/contrarian territory instead of the single safest move, set
  `breadth=wide` and raise `max_survivors` (up to 6) — but say the cost
  tradeoff out loud first (several times more candidates, each getting a
  full prosecution and attack pass) so it's a decision, not a surprise.
- **Private-edge mode**: only if the user explicitly offers private sources
  (their repos, notes, past prototypes). Confirm exactly which sources are
  authorized. Never volunteer to mine private data uninvited.

Then scaffold the run and mark phases as you go (update `run.json`):

```bash
python3 "$SKILL/scripts/init_run.py" --domain "<domain>" --mode <mode> \
    --product-shape <shape> --breadth <focused|wide> \
    --ambition <lifestyle|venture> --max-survivors <n> --out ./idea-runs
```

## Phase 1 — Observe (ideas forbidden)

Read `references/search-lenses.md`. Pick lenses per mode; each lens is one
isolated research branch that collects sourced observations only.

Isolation is the point of the architecture: independent branches sample
different regions of the search space, and correlated branches collapse into
one region. So:

- **If subagents are available** (Claude Code Task/Agent tool, Codex
  parallel agents): launch one subagent per lens, all in the same turn. Give
  each: its lens section from search-lenses.md, the observation format from
  `references/evidence-rules.md`, the domain brief, and an output path
  `<run>/observations/<lens>/`. Explicitly instruct: web-search primary
  sources, record observations only, no product ideas, no knowledge of other
  branches.
- **If not**: run lenses sequentially in one context. Write each branch's
  records to disk, then do not re-read them until Phase 2. Between branches,
  deliberately reset: re-read only the lens definition and the brief.

Per lens, aim for 4-8 observations in deep mode (2-4 in quick). Prefer fewer
corroborated observations over many rumors.

## Phase 2 — Normalize

Read `references/evidence-rules.md` (format, ID scheme, confidence levels).
Merge all branch output into `<run>/observations/`, one JSON file per
observation, deduplicated, ids assigned (`OBS-<lens>-<nn>`), facets filled
where evidence supports them. Keep source conflicts — they are anomalies, not
noise.

## Phase 3 — Map

Write `<run>/notes/map.md`: the anomaly and bottleneck map. Cluster
observations; name each cluster's tension in one sentence ("professionals
re-verify what software already checked", "capability X crossed a cost
threshold but workflow Y hasn't noticed"). List the capability shifts with
dates, the workarounds with maintenance costs, the trust bottlenecks with
their delay costs. This map — not raw observations — is what generation
recombines over.

## Phase 3.5 — Probe (cheap, before anything is written)

Read `references/occupancy-probe.md`. For each candidate *shape* you intend to
generate — an actor plus a mechanism sketch in one structural niche — run one
or two searches and record a probe in `<run>/probes/` per
`scripts/schemas/probe.schema.json`.

This exists because of a measured failure: across two full runs, 44 of 44
candidates died, and not one died on mechanism quality. They died on prior art
or on adoption standing, both of which surface in a couple of queries. Probing
a shape costs a fraction of writing, prosecuting and attacking a candidate
built on it.

Statuses license different things and none of them is a kill:
- `clear` — generate freely; a shallow look proves little.
- `occupied` — something alive ships this. Still generate if the shape is
  worth it, but the candidate must carry a `probe_response` naming the
  specific checkable difference. Occupied space is where most real things get
  built; what it costs is an explicit difference, written down early.
- `contested` — attempts exist and some died. The most informative outcome.
  Generate, and make `probe_response` say what killed the predecessors and
  what changed since.

Keep it shallow — the four-query cap is deliberate. A probe that grows into a
full search is prosecution done early on a candidate that does not exist yet,
and prosecution belongs in Phase 6 with the whole candidate in front of it.

## Phase 4 — Diverge

Read `references/facets.md` fully. Generate candidates as facet
recombinations across **≥3 observations from ≥2 lenses** — pain × capability
× distribution is the workhorse pattern. Every candidate is a JSON file in
`<run>/candidates/` matching `scripts/schemas/candidate.schema.json`, with
`product_shape` set to the brief's declared shape, `probe_id` pointing at the
Phase 3.5 probe for its shape (plus `probe_response` where that probe came
back `occupied` or `contested`), `descriptor` assigned at creation time, and
`falsification` written at creation time (deciding the kill test while you
still love the idea is the cheap moment). A mechanism
that keeps wanting to be a different shape than declared is itself a
finding — record it in the map rather than forcing an ill-fitting wrapper
onto the candidate.

Two fields fail quietly unless you write them deliberately:

- **`probe_response` is per candidate, not per probe.** Several candidates
  will share one probe, and occupancy is a question about one actor's
  market — a response written for one actor does not answer it for another.
  The lint compares candidates against each other and rejects a byte-identical
  response across candidates targeting different actors.
- **`self_refutation` is a re-read, not a citation.** Before writing the
  candidate, open the observation records it cites and look for the thing that
  cuts against it: a caveat inside the record, a `why_now` that is really the
  incumbent already doing this, a workaround the observation says already
  ships free, a kill condition the cited operator has already published and
  acted on. Name the observation id and state what you found, or state that
  you re-read them and found no counter-claim. This is the cheapest kill
  available anywhere in the pipeline — it costs one read and it happens before
  prosecution spends a subagent.

Maintain the quality-diversity archive per facets.md: one best candidate per
structural niche `(opportunity_pattern, mechanism_class, target_actor)`; new
candidates compete only within their niche; stalls are broken by single-facet
mutation of archive members; the graveyard is consulted before generating so
corpses stay buried without new evidence.

Generation targets depend on breadth, not just mode:
- **focused** — deep: 8-15 candidates across ≥5 niches. Quick: 4-6 across ≥3.
- **wide** — deep: 20-30 candidates across ≥10 niches. Quick: 10-15 across
  ≥6. At least a third of candidates must come from collision search
  (facets.md move 6) — the point of wide breadth is territory a focused run
  would never generate, not more of the same shape.

**Spread across `opportunity_pattern`, not just across niches.** Wide breadth
requires ≥6 distinct patterns with no single pattern over 40% of candidates;
focused requires ≥3 with none over 60%. Lint enforces this when `--breadth` is
passed. The map will point at a richest vein and generation will want to mine
only that — in one run this produced 16 of 19 candidates on
`cross-domain-transfer`, a pattern that by construction imports mechanisms
already proven elsewhere and therefore prosecutes as `crowded` or
`duplicated`. When the count is met but the spread is not, the next candidates
come from the untouched patterns, not from the vein.

## Phase 5 — Slop gate

Read `references/slop-patterns.md` if you have not already. Then run:

```bash
python3 "$SKILL/scripts/lint_candidate.py" <run>/candidates/*.json \
    --observations <run>/observations/ --probes <run>/probes/ \
    --require-shape <shape> --require-ambition <ambition> \
    --breadth <focused|wide>
```

Lint the run's candidates **together in one invocation** (the glob above does
this): some checks compare candidates against each other and cannot fire on a
per-file run.

Fix or kill until every surviving candidate passes with 0 errors (warnings
are judgment calls — resolve or accept them consciously). Killed candidates
move to `<run>/graveyard/` with status `killed` and a real
`graveyard_reason`. Do not hand-wave past a lint error: the lint exists
because self-assessed specificity is exactly what fails. Survivors of this
phase get status `gated`.

## Phase 6 — Prosecute

Read `references/novelty-rubric.md`. For each gated candidate, run the
adversarial prior-art search — as a separate subagent if available (input:
candidate JSON only, objective: prove it already exists), otherwise as an
explicit role-switch in a fresh pass. Fill `novelty` (verdict,
scope_searched, closest_prior_art). `duplicated` → graveyard. Update status
to `prosecuted`, re-run lint (it enforces verdict consistency).

## Phase 7 — Attack

Read `references/kill-criteria.md`. The goal profile follows directly from
the declared `product_shape`: `open-source-stewardship` uses the stewardship
profile, every other shape uses the commercial profile — no guessing what
the brief implies. A run declaring `ambition: venture` applies
`scale-ceiling` and `distribution-model-fit` on top of its profile; write the
ceiling arithmetic out with both numbers, since an unwritten denominator is
how that test becomes theatre. Apply ≥5 criteria per candidate, hardest-to-survive
first; record every test in `kill_tests` and note which profile was used.
Kills go to the
graveyard with reasons; justified overrides get written notes that a skeptic
could audit. Survivors get status `attacked`.

## Phase 8 — Edge

Read `references/edge-verification.md`. Grade each remaining candidate's
proprietary edge — after attack, in the same adversarial spirit. Public-web
findings cap at `none`; real edges trace to observations. In private-edge
mode, edge claims may rest on private observations but the report never
exposes private content (opaque `private://` labels only). When torn between
two statuses, assign the lower.

## Phase 9 — Portfolio

Before promoting any candidate, run the **survivor re-check** from
novelty-rubric.md: a second, narrow prior-art pass (fresh subagent where
available, 2-4 queries) aimed only at the differentiation claim, recorded in
`novelty.recheck`. An overturned re-check sends the candidate back to
prosecution with the new evidence.

Then promote up to `max_survivors` candidates (declared in Phase 0, default
3) to status `survivor` (re-run lint — survivor status tightens
requirements: ≥5 kill tests, verdict consistency, an upheld re-check, and for
a `crowded` candidate both `incumbent-weekend-build` and
`reachable-distribution` passing). Write `<run>/portfolio/portfolio.json` per
`scripts/schemas/portfolio.schema.json` (including `max_survivors`), then
audit:

```bash
python3 "$SKILL/scripts/check_portfolio.py" <run>
```

Fix errors — structural clones mean going back to the archive for a
different-niche candidate, not re-wording a survivor. Zero survivors is
acceptable; say so. A raised ceiling is permission, not a quota: promote
what actually survived, never pad toward `max_survivors`.

## Phase 10 — Report

Read `references/report-format.md` and write `<run>/report.md` exactly to
that skeleton: dossiers with observation citations, prior art with checkable
differences, edge stated honestly, falsification experiments ordered by
information-per-dollar, and a ranked runner-up table covering **every**
non-survivor candidate. A thin survivor count is not a thin report — the
runner-up table is the menu the user's search budget paid for, and it is
mandatory even (especially) when there is exactly one survivor or none.
Deliver the report to the user with a short summary of how the run went and
where the run directory is.

## Failure modes to watch in yourself

- **Premature convergence**: everything in the archive orbits the first good
  find. Fix: generate the next candidate from an untouched lens pair.
- **Gate-shopping**: rewording a candidate until the regexes stop matching
  while the mechanism stays hollow. The lint is a floor, not the standard —
  the mechanism template is the standard.
- **Verdict inflation**: wanting `differentiated` so the run "succeeds".
  A run that returns "this space is crowded and here is the map" succeeded.
- **Occupancy as a reflex kill**: treating "something like this exists" as
  the end of the conversation. It is the beginning of one — the question is
  whether the incumbent can or will serve this wedge, which Attack decides
  on evidence. A dead predecessor especially is information, not a verdict.
- **Excitement leak**: report language drifting into pitch language. Re-read
  the language rules in report-format.md before delivering.
- **Ceiling padding**: raising `max_survivors` and then promoting whatever
  is left to hit the number. The ceiling is ambition, not a target — a wide
  run that still returns 1 survivor and 25 honest kills succeeded.
