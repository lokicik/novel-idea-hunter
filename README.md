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
