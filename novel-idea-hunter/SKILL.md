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

## Phase 0 — Brief

Pin down with the user (ask only what the brief doesn't already answer):
- Domain or problem area (broad is fine; "surprise me" is not — get at least
  a territory or a constraint like "solo-buildable developer tools").
- Mode (quick/deep), and any constraints: geography, skills, capital,
  B2B/B2C, time horizon.
- **Private-edge mode**: only if the user explicitly offers private sources
  (their repos, notes, past prototypes). Confirm exactly which sources are
  authorized. Never volunteer to mine private data uninvited.

Then scaffold the run and mark phases as you go (update `run.json`):

```bash
python3 "$SKILL/scripts/init_run.py" --domain "<domain>" --mode <mode> --out ./idea-runs
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

## Phase 4 — Diverge

Read `references/facets.md` fully. Generate candidates as facet
recombinations across **≥3 observations from ≥2 lenses** — pain × capability
× distribution is the workhorse pattern. Every candidate is a JSON file in
`<run>/candidates/` matching `scripts/schemas/candidate.schema.json`, with
`descriptor` assigned at creation time and `falsification` written at
creation time (deciding the kill test while you still love the idea is the
cheap moment).

Maintain the quality-diversity archive per facets.md: one best candidate per
structural niche `(opportunity_pattern, mechanism_class, target_actor)`; new
candidates compete only within their niche; stalls are broken by single-facet
mutation of archive members; the graveyard is consulted before generating so
corpses stay buried without new evidence.

Deep mode: target 8-15 candidates across ≥5 niches before gating. Quick
mode: 4-6 across ≥3.

## Phase 5 — Slop gate

Read `references/slop-patterns.md` if you have not already. Then run:

```bash
python3 "$SKILL/scripts/lint_candidate.py" <run>/candidates/*.json --observations <run>/observations/
```

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

Read `references/kill-criteria.md`. Pick the goal profile the brief implies
(commercial vs stewardship — grading an open-standard play on revenue
criteria yields evasive `unclear`s instead of real answers). Apply ≥5
criteria per candidate, hardest-to-survive first; record every test in
`kill_tests` and note which profile was used. Kills go to the
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

Then promote at most 3 candidates to status `survivor` (re-run lint —
survivor status tightens requirements: ≥5 kill tests, verdict consistency,
crowded needs credible edge, upheld re-check). Write
`<run>/portfolio/portfolio.json` per `scripts/schemas/portfolio.schema.json`,
then audit:

```bash
python3 "$SKILL/scripts/check_portfolio.py" <run>
```

Fix errors — structural clones mean going back to the archive for a
different-niche candidate, not re-wording a survivor. Zero survivors is
acceptable; say so.

## Phase 10 — Report

Read `references/report-format.md` and write `<run>/report.md` exactly to
that skeleton: dossiers with observation citations, prior art with checkable
differences, edge stated honestly, falsification experiments ordered by
information-per-dollar. Deliver the report to the user with a short summary
of how the run went and where the run directory is.

## Failure modes to watch in yourself

- **Premature convergence**: everything in the archive orbits the first good
  find. Fix: generate the next candidate from an untouched lens pair.
- **Gate-shopping**: rewording a candidate until the regexes stop matching
  while the mechanism stays hollow. The lint is a floor, not the standard —
  the mechanism template is the standard.
- **Verdict inflation**: wanting `differentiated` so the run "succeeds".
  A run that returns "this space is crowded and here is the map" succeeded.
- **Excitement leak**: report language drifting into pitch language. Re-read
  the language rules in report-format.md before delivering.
