# Evidence rules

Every claim in this pipeline traces back to observation records. Ideas are
downstream artifacts; observations are the ground truth. If a candidate cannot
cite its observations, it does not exist — that single rule kills most slop,
because slop is precisely ideation unmoored from evidence.

## Observation record format

One JSON file per observation in the run's `observations/` directory, matching
`scripts/schemas/observation.schema.json`. File name = the observation's id.

```json
{
  "id": "OBS-workarounds-03",
  "lens": "workarounds",
  "claim": "Solo tax accountants maintain shared spreadsheets mapping e-invoice rejection codes to fixes",
  "detail": "Three separate forum threads describe the same spreadsheet pattern; one has 40k views. Maintainers complain about keeping it current after each schema update.",
  "sources": [
    {"url": "https://...", "quote": "we all just copy Deniz's rejection-code sheet", "date_accessed": "2026-08-24", "type": "forum"}
  ],
  "observed_actor": "solo tax accountants filing e-invoices",
  "observed_behavior": "maintain and share manual rejection-code mapping spreadsheets",
  "facets": {
    "actor": "solo tax accountants",
    "friction": "rejection codes are undocumented and change with schema updates",
    "current_workaround": "community-maintained spreadsheet",
    "frequency": "every filing cycle"
  },
  "confidence": "corroborated"
}
```

## ID scheme

`OBS-<lens-slug>-<nn>` — the lens slug is embedded in the id on purpose: the
lint derives lens diversity from ids alone, and a reader can see an idea's
evidence mix at a glance. Number sequentially within a lens, zero-padded to
two digits.

## What qualifies as an observation

- A **behavior**: someone concretely does X (with evidence they do).
- A **change**: something became possible, cheap, legal, broken, or urgent at
  a nameable point in time.
- A **contradiction**: two facts that shouldn't coexist but do (a $200/hr
  professional doing $15/hr copy-paste work).
- An **absence**, only when bounded: "no tool in ecosystem X does Y" is an
  observation only if you searched X and can list what you checked.

Not observations: opinions about the future, market-size estimates from
secondary reports, product ideas, "X is a growing trend."

## Sourcing standards

- Every observation carries at least one source with a working URL. Quotes
  stay under 15 words.
- `confidence` is honest: `reported` (one source), `corroborated` (2+
  independent sources — different authors, not the same press release twice),
  `verified` (you checked directly: ran the code, read the regulation, loaded
  the pricing page).
- Candidates that survive to the portfolio should rest mostly on
  `corroborated`/`verified` observations. A candidate built on stacked
  `reported` singles is a rumor with a business model.
- Date-stamp everything. "Recently" rots; `2026-08` does not.

## Branch isolation

Observation branches (subagents or sequential passes) must not see each
other's output. When running sequentially in one context, write each branch's
records to disk, then deliberately do not re-read them until the Normalize
phase. The point is statistical: independent samples from different regions of
the search space. Correlated samples — branch B riffing on branch A's find —
collapse the diversity that the whole architecture exists to preserve.

## Normalization pass

After all branches return: deduplicate (same fact from two branches → keep
both sources on one record), assign final ids, fill facets where evidence
supports them, and mark each record's confidence. Do not average away
disagreement — if two sources conflict, keep both and note the conflict in
`detail`; conflicts are often the most interesting anomalies on the map.
