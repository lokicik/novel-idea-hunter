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
LLM evaluation harnesses. Deep mode.
```

Quick mode (3 lenses, lighter search) for a first pass:

```
/novel-idea-hunter quick pass: untapped niches in home energy monitoring,
software only, no capital-heavy hardware.
```

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
