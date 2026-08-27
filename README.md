# novel-idea-hunter

An evidence-first opportunity-discovery skill for coding agents (Claude Code
and Codex). It finds novel, defensible product/startup/project opportunities
by forcing research before ideation, and mechanically rejects generic
"AI-powered X" slop with deterministic validator scripts.

## Why it exists

Almost all LLM ideation slop comes from one failure: the model enters
solution-mode before doing any research. This skill inverts the order:

```
brief → isolated observation branches → evidence normalization
      → anomaly map → facet recombination → deterministic slop gate
      → adversarial prior-art prosecution → market/incumbent attack
      → proprietary-edge verification → ≤3 non-redundant survivors
      → falsification experiments
```

Design lineage: isolated divergent branches (ADHD), capability-wedge and
kill-filter thinking (HypoKiln), facet recombination (Scideator),
retrieve-and-compare novelty checking (Idea Novelty Checker), plus
quality-diversity archive dynamics and private-edge mining.

Three properties do most of the anti-slop work:

1. **No ideas before evidence.** Candidates must cite ≥3 sourced
   observations from ≥2 research lenses, or the lint rejects them.
2. **Novelty is prosecuted, not scored.** A separate adversarial pass tries
   to prove each idea already exists; verdicts come from a controlled
   vocabulary whose ceiling is `no-close-prior-art-found` — never "unique".
3. **The gates are scripts, not vibes.** `lint_candidate.py` and
   `check_portfolio.py` fail with exit code 1; a model cannot charm a regex.

## Layout

```
novel-idea-hunter/
├── SKILL.md                 # the workflow (phases 0-10)
├── agents/openai.yaml       # Codex metadata (explicit invocation only)
├── references/              # lenses, facets, evidence rules, slop patterns,
│                            # novelty rubric, kill criteria, edge rules, report format
├── scripts/                 # Python 3 stdlib only
│   ├── init_run.py          # scaffold an auditable run workspace
│   ├── lint_candidate.py    # schema + slop gate (exit 1 on errors)
│   ├── check_portfolio.py   # structural-redundancy audit of survivors
│   └── schemas/             # observation / candidate / portfolio JSON schemas
└── evals/evals.json         # test prompts + expectations
tests/                       # unit tests for the scripts (repo only, not installed)
```

## Install

### Claude Code (macOS/Linux)

```bash
ln -s "$(pwd)/novel-idea-hunter" ~/.claude/skills/novel-idea-hunter
```

(or copy the folder instead of symlinking). Invoke with
`/novel-idea-hunter <brief>`, or just describe an ideation task — the skill
description makes it trigger on substantial opportunity-discovery requests.

### Codex

```bash
mkdir -p ~/.agents/skills
cp -R novel-idea-hunter ~/.agents/skills/
```

Invoke explicitly: `$novel-idea-hunter <brief>`. Implicit invocation is
disabled in `agents/openai.yaml` because the workflow is expensive.

### Windows (PowerShell)

```powershell
Copy-Item -Recurse .\novel-idea-hunter "$HOME\.agents\skills\novel-idea-hunter"
Copy-Item -Recurse .\novel-idea-hunter "$HOME\.claude\skills\novel-idea-hunter"
```

## Usage

```
/novel-idea-hunter discover non-obvious developer-tool opportunities around
LLM evaluation harnesses. Deep mode. I want a SaaS I can charge a monthly
subscription for.
```

Quick mode (3 lenses, lighter search) for a first pass:

```
/novel-idea-hunter quick pass: untapped niches in home energy monitoring,
software only, no capital-heavy hardware. SaaS subscription, not a
marketplace or a one-time-purchase product.
```

**Product shape is a required, hard-enforced input** — `saas-subscription`,
`usage-based-platform`, `marketplace`, `services-led`,
`open-source-stewardship`, `hardware`, or `data-api-product`. If you don't
state one, the skill will ask rather than guess: without it, candidate
generation follows whatever mechanism class the evidence happens to favor,
which can return a robotics-compliance layer when what you wanted was a
recognizable B2B SaaS. Every candidate is tagged with its declared shape and
`lint_candidate.py --require-shape` rejects any candidate that drifted off
it. The kill-criteria goal profile (commercial vs stewardship) also follows
from this field instead of being inferred.

**The report always includes a ranked runner-up table**, not just the
survivors — every candidate that was generated and killed, ordered
closest-to-survival first, with a checkable condition that would revive
each one. A run that returns one survivor (or zero) still hands you the
full field it considered, not a single verdict.

**Want more options, or genuinely wild territory?** Ask for `wide` breadth:

```
/novel-idea-hunter deep mode, wide breadth, up to 5 survivors: SaaS
opportunities in home energy monitoring. Give me some real reaches, not
just the safest move.
```

`breadth: wide` widens the candidate funnel several times over (deep mode:
20-30 candidates across ≥10 structural niches, vs 8-15/≥5 focused) and
requires at least a third of them to come from *collision search* —
deliberately pairing the two least-related evidence clusters on the map and
forcing a mechanism between them, instead of the safer pain×capability
combinations. This is where the wild ideas come from, and it is the only
thing that changes: every candidate, however weird its origin, still needs
the same ≥3-observation evidence trail, the same 2-4 step mechanism, the
same adversarial prosecution, and the same falsification test as a focused
run. Wide breadth raises the portfolio ceiling (`--max-survivors`, up to 6)
so a wider funnel can actually return more survivors — but the ceiling is
a permission, not a quota: a wide run that returns one real survivor and 25
honest kills did its job. It also costs several times more tokens and
wall-clock time, since every extra candidate gets its own full prosecution
and attack pass — say so before running it.

Private-edge mode (opt-in — the skill never mines private data uninvited):

```
/novel-idea-hunter private-edge
Mine my authorized sources: ~/repos, my notes in ~/notes/ideas.
Cross them with public evidence for opportunities I'm unusually positioned
to pursue. Do not reveal private details in the report.
```

Each run leaves an auditable directory (default `./idea-runs/<timestamp>-<slug>/`)
with every observation, candidate, kill reason, and the final `report.md` —
you can trace any surviving idea back to its sources, and any dead one to its
cause of death.

## Honest limitations

- `no-close-prior-art-found` is a claim about a search, never about the
  world. Nothing here proves global novelty.
- Public-web research alone cannot make an idea *proprietary*. The edge
  phase grades that honestly: most public-only candidates get edge `none`.
- The pipeline constrains the model; it does not replace judgment. Treat
  survivors as researched hypotheses with pre-written falsification tests,
  not as decisions.

## Development

```bash
python3 -m unittest discover tests -v
```

Evals follow the Anthropic skill-creator conventions (`evals/evals.json`,
with-skill vs without-skill A/B runs graded against expectations).

## Benchmark (iteration 1, 2026-08-24)

Two evals ("LLM eval tooling, quick mode" and a slop-bait prompt), one run per
configuration, same model (claude-fable-5), graded against the eval
expectations:

| Metric | With skill | Baseline | Delta |
|---|---|---|---|
| Expectation pass rate | 100% (15/15) | 22% (3/15) | +78 pts |
| Wall time (avg) | ~19 min | ~2.6 min | ~7x |
| Tokens (avg) | ~165k | ~44k | ~3.7x |

Honest caveats: single run per configuration (no variance data); the
expectations encode this skill's contract, so the delta measures contract
compliance, not raw idea quality; the base model already avoids surface-level
slop phrasing on its own — the discriminating value is traceable evidence,
adversarial prior-art verdicts, and pre-committed falsification tests, which
the baseline produced none of.

## Iteration 3 (2026-08-26) — product shape and runner-up reporting

A deep-mode run against Y Combinator's Fall 2026 Request for Startups
returned a single survivor (a robotics-fleet compliance layer) out of 8
candidates — technically defensible (7 others died to named competitors,
several from recent YC batches), but the user wanted SaaS specifically and
had asked for options, not one verdict. Two gaps caused this:

1. **No mechanical way to declare product shape.** The brief could say
   "B2B, low capital" but nothing constrained *what kind of thing* a
   survivor should be, so Diverge followed the evidence into whatever
   mechanism class it favored. Fixed: `product_shape` is now a required
   field on every candidate (`candidate.schema.json`), declared at
   `init_run.py --product-shape` and hard-enforced across a run via
   `lint_candidate.py --require-shape`. The Attack goal profile now follows
   directly from it instead of being inferred from the brief.
2. **The report only surfaced survivors.** With one survivor, the user saw
   one idea — the seven researched, evidenced, then-killed alternatives
   were compressed into "2-4 sentences on the most interesting entries."
   Fixed: `report-format.md` now requires a ranked runner-up table covering
   every non-survivor candidate, mandatory precisely when the survivor
   count is thin.

## Iteration 5 (2026-08-27) — probe first, and stop treating occupancy as a kill

Two full deep runs over the same territory produced **44 candidates and 44
deaths, and not one died on mechanism quality.** They died on prior art or on
adoption standing. Two changes follow from that, and the second matters more
than the first.

**1. An occupancy probe before generation (Phase 3.5).** For each candidate
*shape* — an actor plus a mechanism sketch in one structural niche — one or
two searches, recorded in `<run>/probes/` per `probe.schema.json`. Candidates
carry `probe_id`, and lint requires a `probe_response` when the probe came
back `occupied` or `contested`. Probing a shape costs a fraction of writing,
prosecuting and attacking a candidate built on it. The four-query cap is
deliberate: a probe that grows into a full search is prosecution done early
on a candidate that does not exist yet.

**2. Occupancy is no longer a kill — a latent calibration bug is fixed.** The
old rule said a `crowded` candidate survives only with a `credible`
proprietary edge. But `edge-verification.md` caps public-web research at
`none`, so in a public run that rule could fire on *every* crowded candidate
without anyone weighing its merits. Most worthwhile things get built in
occupied space; "someone already does something like this" is not a verdict.
What a crowded candidate now owes is a *reason* rather than an *asset*: lint
requires `incumbent-weekend-build` and `reachable-distribution` to both pass —
a named structural cause the incumbent will not serve this wedge, and a named
path to the buyer. Defence over time is what `edge` measures; whether you can
get in at all is what Attack measures, and conflating them was the bug.

**Measured afterwards, and it changed nothing retrospectively.**
Re-adjudicating all 19 crowded candidates from the two runs under the new
rule: **19 still die.** Not because of arithmetic — 18 of the 19 carry
`incumbent-weekend-build = kill` with evidence-grounded notes naming specific
shipping incumbents ("LangGraph already ships node-level caching inside the
framework"; "the incumbent publishes the destination, names the free tool, and
gives the steps five months ahead"). The old edge rule was **redundant with a
genuine kill in 18 of 19 cases, not decisive.** An earlier draft of this
section claimed the rule "silently eliminated 19 of the 44"; the measurement
refuted that, and the claim is corrected here rather than quietly dropped.
The fix is still right — a rule that *can* fire without judgment should not
exist — but it was not what produced the zero-survivor results. Those
candidates were genuinely in occupied space. That makes the probe, not the
recalibration, the load-bearing half of this iteration: it does not change
which candidates die, it makes them die cheaply.

One latent issue the measurement surfaced: `reachable-distribution` was left
`unclear` or unrecorded in 17 of 19, because under the old regime it never
mattered once a candidate was crowded. Under the new rule an unresolved
criterion fails, which is the correct default — you should not promote a
survivor when you cannot name a path to its buyer — but a run must now
actually resolve it rather than leave it hanging.

Relatedly, prior art now carries a `state` (`shipping` / `stalled` /
`abandoned` / `proposed-unadopted`), and a terminal `duplicated` verdict may
not rest entirely on dead predecessors. Both runs kept calling abandoned
projects duplicates — one matrix attempt abandoned two hours after creation,
one conformance suite two days. A predecessor that died makes a space
contested, not closed, and *what killed it* is usually the most valuable thing
in the file.

The user's immediate follow-up made the actual want explicit: more
survivors, and genuinely wild ones — not just a bigger report about the
same single safe idea. That's a request for more raw material and a wider
search, not a softer gate, so the fix runs upstream of the report:
`breadth: wide` (declared at `init_run.py`, enforced nowhere near the
quality bar) widens Diverge's candidate count several-fold and mandates a
quota of collision-search recombinations (`facets.md`), while
`--max-survivors` (up to 6) raises how many can be promoted *if* that many
actually survive prosecution and attack unchanged. See the Usage section
above for the `wide`-breadth example.

## Iteration 6 (2026-08-27) — venture ambition

`init_run.py --ambition venture` adds two kill criteria to the commercial
core: `scale-ceiling` (buyers × annual price, both numbers written and the
denominator sourced) and `distribution-model-fit` (does the way this reaches
buyers match the way it charges them). Lint enforces both on survivors via
`--require-ambition venture`.

**Measured on the run that motivated them, and they changed nothing.** Across
the 13 candidates that reached Attack, the two criteria fired 11 times —
`distribution-model-fit` was the single most-fired criterion in the run — but
**zero candidates died on them alone.** Every candidate they killed was
already dying on a commercial criterion. The case they exist for, a candidate
that is commercially sound but structurally sub-scale, never arose, because
this territory killed everything commercially first. Two iterations running,
an added rule has turned out to be corroborating rather than decisive; that is
worth stating plainly rather than counting the firings as impact.

## Iteration 7 (2026-08-27) — read the evidence you are citing

A wide venture run on "AI slop as a market" produced 42 observations, 12
probes, 19 candidates and **19 deaths**. Two defects in the run were caught by
prosecutors rather than by the pipeline, and both are now mechanical.

**1. `self_refutation` is a required candidate field.** Four of the 19
candidates were killed by evidence sitting in the observation records they
*themselves cited* — a caveat inside the cited record (baselines are worthless
on thin files, and most of the target population had thin files); a `why_now`
that was the incumbent already shipping the mechanism; a gate already shipping
free in a tool the run had observed; a kill condition published by the
operator the candidate cited as its trigger. None needed a search. All needed
a re-read. Lint now requires a written re-read naming at least one of the
candidate's own `observation_ids`. This is the cheapest kill in the pipeline:
it costs one read and fires before prosecution spends a subagent.

**2. Cross-candidate lint: `probe_response` is per candidate, not per probe.**
The run's generator keyed probe responses by probe id, so candidates sharing a
probe got byte-identical text. Three carried a response answering the
occupancy question for a different actor entirely, and the per-file lint
passed all three because the field was present and long enough. `lint_candidate.py`
now compares candidates within one invocation and rejects an identical
`probe_response` across candidates targeting different actors. Applied
retroactively to the run, it found **two further groups the prosecutors had
not caught** — five candidates in total, against three found by review.

**Also surfaced, as a process failure rather than a tool gap.** The skill
requires re-running lint after prosecution; that step was skipped in this run,
and it hid 26 prior-art `state` values that had drifted off the controlled
vocabulary in subagent output. Prosecutor prompts now carry the enums, but the
real fix was already in the workflow and simply not followed.

## Iteration 8 (2026-08-27) — the filter was harsh in one place, but generation was the problem

Prompted by a direct question: is the filter too strict, is there really no
usable idea, is the brainstorming too narrow? Three measurements, and the
answers were not the expected ones.

**The filter is miscalibrated, and a back-test proves it.**
`incumbent-weekend-build` said: could an incumbent with distribution ship this
in two weeks? If so, they will. It returned `kill` for 10 of 13 attacked
candidates. Applied to companies that actually won, the same reasoning kills
them. [Abnormal Security](https://underdefense.com/blog/abnormal-security-pricing-guide/)
sells email security at a premium per-seat price while Microsoft bundles
Defender for Office 365 P2 into E5 at effectively zero incremental cost with
30-40% feature overlap — the incumbent did not merely *could* ship it, it
shipped it and gave it away. [Wiz](https://www.wiz.io/blog/100m-arr-in-18-months-wiz-becomes-the-fastest-growing-software-company-ever)
reached $100M ARR in 18 months selling cloud security posture management while
every major cloud provider shipped native tooling. This is the same
calibration bug already fixed for the `crowded` novelty verdict in iteration 5
— fixed there, and missed here. The criterion now has two doors to a pass
(structural barrier, *or* a named reason buyers choose the specialist), and
lint requires a `kill` to rest on prior art that is actually `shipping` and
either `direct-competitor` or `incumbent-feature`. Measured on the run: 9 of
10 kills were already evidence-backed, so the evidence half was sound and the
judgment half was not — which is exactly the half a linter cannot fix.

**But the filter is not what produced zero survivors.** Removing
`incumbent-weekend-build` entirely, removing `distribution-model-fit`, and
forgiving the three shape-not-law kills: **still zero.** Every candidate
carries an independent kill on `why-now-really`, `workaround-is-good-enough`,
`buyer-has-budget` or `unit-economics-smell`. The zero is robust to the
filter's known miscalibration, which moves the diagnosis upstream.

**Generation collapsed while research did not.** Observations were healthy —
42 across 7 lenses, exactly 6 per lens. Then **16 of 19 candidates landed on a
single `opportunity_pattern`**, `cross-domain-transfer`, with only 4 of 12
patterns used at all. That concentration was causal, not cosmetic: importing a
mechanism proven in another field means importing a *known* mechanism, so
roughly five in six candidates were pre-disposed to prosecute as `crowded` or
`duplicated` before their merits were assessed. The map named a richest vein
and generation mined only it — the "premature convergence" failure the skill
already warns about, one level up from where it was being watched.
`lint_candidate.py --breadth` now enforces pattern spread across the whole
invocation: wide needs ≥6 distinct patterns with none over 40%, focused ≥3
with none over 60%. Run against the historical candidates it fires on both
counts and would have blocked the slop gate.

**Shape drift is no longer a kill.** Three of the run's more substantive
candidates died under `regulatory-liability` for being insurance instruments
when the brief declared `saas-subscription`. That is a finding about the
territory, not a verdict on the mechanism. `regulatory-liability` is now
reserved for law, report-format.md gains a required **Shape drift** section,
and the user gets offered a re-run under the shape the mechanisms kept
reaching for.

One hypothesis tested and rejected, recorded so it is not re-proposed: that
venture ambition pushed toward large actors and large actors build in-house.
`incumbent-weekend-build` killed large and niche actors at the same rate
(5 and 5).

Tests 71 -> 81.

## Iteration 9 (2026-08-27) — reaching past the model's prior

Iteration 8 stopped the funnel collapsing onto one pattern. It did not make
generation reach anywhere new. Asking for that directly does not work, and the
reason is documented rather than a matter of taste.

**Mode collapse is a property of alignment, not of effort.** Preference data
carries a typicality bias — annotators favour familiar text — so the aligned
model concentrates on typical answers. The remedy that works is structural:
prompting for a *distribution over answers with probabilities* instead of an
answer recovers 1.6-2.1x diversity in creative writing and 2-3x more broadly,
at equal quality, training-free, with more capable models benefiting more
([Verbalized Sampling, arXiv 2510.01171](https://arxiv.org/abs/2510.01171)).

**Diversity saturates as generation scales.** With 100+ NLP researchers
judging, LLM ideas were rated *more* novel than expert human ideas but
repetitive in bulk; the authors name diversity under inference-time scaling as
an open problem ([Si, Yang & Hashimoto, arXiv 2409.04109](https://arxiv.org/abs/2409.04109)).
Generating 40 candidates instead of 20 buys repetition, which is exactly what
this pipeline's own run showed at 19.

So the provocation now comes from **outside the model**:

**`scripts/provoke.py`** draws generation briefs deterministically from the run
id. Each slot fixes an `opportunity_pattern` the run has not mined, one of
Altshuller's 40 TRIZ inventive principles to force onto the cluster's named
tension, and an inversion directive. Reproducible, and not chosen by taste.
TRIZ is used because it is distilled from patent analysis rather than business
writing, so it sits outside the prior a model brings to "startup idea" — the
reason TRIZ-structured prompting produces better-justified directions than
open-ended generation ([AutoTRIZ, arXiv 2403.13002](https://arxiv.org/html/2403.13002v2)).
The physically literal principles (thermal expansion, porous materials) are
kept deliberately: forcing them onto a market mechanism is the move a model
will not make unprompted.

**Verbalized sampling in Phase 4.** Ask for five candidates for a niche with
the probability the generator would have produced each, build out the low tail,
and record the number in `provocation.sampled_probability`. The typical answer
is not wrong — it is already known, which in this pipeline means it prosecutes
as `crowded`.

**Gap-directed retrieval** is documented as the third move: after the first
wave, search what the current *set* lacks rather than the domain, which
produced 2.5x more top-rated ideas in
[Nova, arXiv 2410.14255](https://arxiv.org/abs/2410.14255).

Lint requires a recorded `provocation` on every live candidate at `wide`
breadth, rejects an improvised TRIZ principle that is not one of the 40, and
range-checks the sampled probability. `references/provocations.md` carries the
grounding and the discipline that matters most: **a forced brief that produces
nothing is a recorded result** — quietly swapping a hard slot for a
comfortable one is how the funnel collapsed in the first place.

One thing this explicitly does not buy: the same study found LLM ideas more
novel *and* slightly weaker on feasibility, which a wider funnel amplifies.
Everything still goes through the slop gate, prosecution and attack unchanged.

Tests 81 -> 93.

## Iteration 10 (2026-08-28) — grading someone else's homework

Two runs had returned 29 candidates and 29 kills, with the same party writing
both the candidates and the attack notes. The literature says that is the wrong
shape: feasibility judgments have poor inter-rater agreement (ICC ~0.45 against
0.82 for originality), and self-preference bias is a known failure of
model-as-judge. So the kill record was put to a blind test.

**Method.** All 29 candidates were harmonised into uniform dossiers carrying the
mechanism, actor, trigger, workaround, why-now, and the prior art found by the
*independent* prosecution subagents. Withheld: every verdict, every kill test,
the graveyard reasons, `self_refutation`, `probe_response`, `provocation`, and
which run each came from. Order shuffled on a fixed seed. Three judges, no web
search, same kill-criteria vocabulary. Record: `evals/blind-readjudication-2026-08-28.json`.

**Result: 28 of 29 kills confirmed, by all three judges independently (97%).**
The kill record is not an artifact of self-preference.

**One kill was overturned unanimously, and it was wrong on fact rather than
judgement.** CAND-02's `buyer-has-budget` note claimed no buyer varies review
depth by disclosed production method. Linux and Fedora contribution policies
already carry an `Assisted-by:` trailer, so receivers mark asserted production
method today; SLSA leaves the source-provenance predicate undefined, which is a
standards slot rather than an incumbent's wedge; and the budget line is
enterprise third-party supply-chain assurance against CRA obligations landing
2026-09 and 2027-12. The candidate has been reopened with its kill tests
corrected in place.

**The provoked run scored zero.** Of 29 candidates, the single one any judge
would pursue came from the *self-directed* run. Iteration 9's machinery widened
the funnel measurably (pattern concentration 84% → 30%) and produced nothing a
blind judge wanted. That is the honest verdict on it so far.

**The judges' decisive criteria diverge sharply from the pipeline's**, which is
the most useful finding here:

| criterion | pipeline | judges |
|---|---|---|
| `distribution-model-fit` | 88% of attacked | **1%** of kills |
| `incumbent-weekend-build` | 75-77% | 37% |
| `workaround-is-good-enough` | 46-75% | 25% |

The pipeline's most-fired criterion is almost unused by independent judges.
`distribution-model-fit` appears to be doing rhetorical rather than decisive work
in this author's hands — a candidate for the same recalibration iteration 8
applied to `incumbent-weekend-build`.

**All three judges independently reached three findings nobody asked them for**,
each of which the pipeline had also reached or should have: the 29 read as one
generative template (transplant a mature governance mechanism into an AI-flood
intake domain); between a quarter and a third put capital at risk and so violate
the `saas-subscription` brief before prior art is consulted; and many sell to
operators who are themselves the incumbent.

**Limitations, stated because they matter.** The three judges are the same model
in separate contexts, not independent minds — 100% pairwise agreement on all 29
verdicts is more consistent with a shared prior than with genuine convergence,
and it sits far above what human feasibility agreement looks like. The judges
could not search, so they adjudicated the prosecution's evidence rather than
verifying it. And that evidence was itself produced by subagents of the same
model. This is a check against self-preference within one context, not an
independent audit.

## Iteration 11 (2026-08-28) — two fixes the blind test paid for

**`distribution-model-fit` is recalibrated.** The blind re-adjudication showed it
firing on 88% of attacked candidates here against 1% of independent judges'
kills — the pipeline's most-used criterion is one the judges barely reach for.
A motion/pricing mismatch is nearly always fixable by re-pricing, so it rarely
decides anything. It is now reserved for structural, unfixable mismatches
(broker-placed underwriting cannot be self-serve; multi-party coordination
cannot charge per participant before any participant has value). Otherwise:
record `unclear` with the re-pricing named, and let a substantive criterion
decide. This is the same correction iteration 8 applied to
`incumbent-weekend-build`, one criterion over — which is exactly what the
measurement predicted.

**Private edge is now a standing Phase 0 question, not an optional extra.**
Two runs, 29 candidates, 28 confirmed kills, and every one of them generated
from public-web evidence alone — the `private-edge` mode has never once been
exercised. The empirical literature says that is the worst configuration
available: Shane's study of eight teams commercialising a single widely
publicised MIT invention found each discovered only the opportunity matching
knowledge they already held, and that none of them had been searching for an
opportunity at all. Public evidence is where everyone is already looking; what
makes an opportunity visible to one person and invisible to everyone else is
idiosyncratic prior knowledge. Phase 0 now asks for it in plain terms — what do
you know that isn't googleable — while the privacy rule stays absolute: ask,
never assume, and never volunteer to go looking. A public-only run is now a
stated limitation in the report rather than a silent default.
