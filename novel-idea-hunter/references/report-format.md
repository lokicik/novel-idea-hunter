# Final report format

The report is the run's only user-facing deliverable. Write it to `report.md`
in the run directory. Its audience is the user deciding where to spend their
next month — not a pitch audience. Flat, evidenced, and falsifiable beats
exciting.

## Report skeleton

```markdown
# Opportunity report: <domain> (<mode> mode, <date>)

## How this run went
One paragraph: lenses run, observation count, candidates generated,
graveyard count, survivors. Note anything that limited the run (thin
sources, unreachable communities, time caps).

## Survivors
One dossier per survivor (format below). Order by your confidence, and say
one sentence about why that ordering.

## Worth a mention
2-4 sentences on the most interesting graveyard entries — candidates killed
for reasons that could expire (a missing capability, a pending regulation).
These are the re-run triggers.

## What would change these conclusions
3-5 bullets: the observations that, if wrong, unwind the most.

## Suggested next actions
The falsification experiments, ordered by information-per-dollar.
```

## Survivor dossier format

Every survivor gets this exact structure. Every factual claim cites
observation ids; the reader must be able to walk from any sentence back to a
source.

```markdown
### <name>

**One-liner.** <the mechanism-template sentence>

**Observed behavior.** What people concretely do today. [OBS-…, OBS-…]

**Underlying problem.** Why that behavior exists; the structural cause.

**Why now.** The evidenced change. [OBS-…]

**Non-obvious connection.** Which unrelated observations collided to produce
this — name the lenses. This section is the novelty story told as evidence.

**Mechanism.** The 2-4 steps, concrete.

**Current alternative.** The workaround and what it costs. [OBS-…]

**Closest prior art.** Top entries from prosecution, each with its checkable
difference. State the verdict plainly (`differentiated`, `crowded` + edge,
or `no-close-prior-art-found` + scope searched).

**Incumbent response.** The strongest attack-phase objection and the answer
that kept the candidate alive. Include any overridden kill honestly.

**Edge.** Status, the asset, why it is hard to copy, and the proof metric.
If `none`: say "no proprietary edge; wins on execution" in those words.

**Falsification.** The test, its cost, timebox, and the pre-committed kill
condition.

**Death conditions.** What would invalidate the thesis after launch, beyond
the first test.
```

## Language rules

- Controlled vocabulary only for novelty and edge claims. Never "unique",
  "no competition", "first ever" — lint bans them upstream and the report
  must not smuggle them back in.
- No numeric novelty scores anywhere.
- Uncertainty is stated, not hedged into mush: "corroborated by two forum
  threads; not verified against filings" beats both false confidence and
  "may or may not".
- If the portfolio is empty, the report says so and presents the best
  graveyard entries with their kill reasons. A run that honestly finds
  nothing beats three zombies — and its observation corpus remains an asset
  for the next run.

## Final gate

Before delivering: `portfolio/portfolio.json` written, and
`python3 <skill>/scripts/check_portfolio.py <run-dir>` exits 0. A report on
an unaudited portfolio is not done.
