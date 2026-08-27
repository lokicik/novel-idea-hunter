#!/usr/bin/env python3
"""Structural-redundancy and concentration audit for a run's final portfolio.

Plain top-N scoring reliably promotes near-duplicate top picks. This audit
compares survivors by their structural descriptor coordinates, not their
wording, so a portfolio of near-clones fails even when every individual
candidate lints clean. The survivor ceiling itself is per-run
(portfolio.max_survivors, default 3, up to 6 via init_run.py
--max-survivors) — raising it widens what a run may return, it does not
loosen this audit. Exit code 0 = clean, 1 = errors found, 2 = usage/IO.

Usage:
    python3 check_portfolio.py RUN_DIR [--json]

Expects the layout created by init_run.py:
    RUN_DIR/portfolio/portfolio.json
    RUN_DIR/candidates/CAND-XX.json
    RUN_DIR/observations/*.json
    RUN_DIR/graveyard/*.json
"""

import argparse
import itertools
import json
import re
import sys
from pathlib import Path

from lint_candidate import lint_candidate, load_observation_ids, load_probes

MODES = {"quick", "deep"}
JACCARD_WARN_THRESHOLD = 0.5
_WORD_RE = re.compile(r"[a-z0-9]+")


def _norm(value):
    return " ".join(str(value or "").lower().split())


def _tokens(text):
    return set(_WORD_RE.findall(str(text or "").lower()))


def _jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def audit_portfolio(portfolio, candidates_by_id, observation_ids=None, graveyard_count_on_disk=None,
                    probes=None):
    """Return (errors, warnings). candidates_by_id maps CAND id -> candidate dict."""
    errors, warnings = [], []

    for key in ("run_id", "domain", "mode", "max_survivors", "survivors", "candidates_considered", "graveyard_count"):
        if key not in portfolio:
            errors.append(f"portfolio missing required field '{key}'")
    if portfolio.get("mode") not in MODES:
        errors.append(f"portfolio.mode '{portfolio.get('mode')}' not in {sorted(MODES)}")

    max_survivors = portfolio.get("max_survivors", 3)
    if not isinstance(max_survivors, int) or not (1 <= max_survivors <= 6):
        errors.append(f"portfolio.max_survivors '{max_survivors}' must be an integer from 1 to 6")

    survivors = portfolio.get("survivors") or []
    if len(survivors) > max_survivors:
        errors.append(f"{len(survivors)} survivors listed; this run declared a ceiling of {max_survivors} — "
                      "forced concentration is the point even when the ceiling is raised")
    if len(survivors) != len(set(survivors)):
        errors.append("duplicate ids in survivors list")

    resolved = []
    for cid in survivors:
        cand = candidates_by_id.get(cid)
        if cand is None:
            errors.append(f"survivor {cid} has no candidate file in candidates/")
            continue
        if cand.get("status") != "survivor":
            errors.append(f"{cid} is listed as a survivor but its status is '{cand.get('status')}'")
        cand_errors, _ = lint_candidate(cand, observation_ids, None, probes)
        for e in cand_errors:
            errors.append(f"{cid}: {e}")
        resolved.append(cand)

    # Pairwise structural redundancy.
    for a, b in itertools.combinations(resolved, 2):
        da, db = a.get("descriptor") or {}, b.get("descriptor") or {}
        shared = [k for k in ("opportunity_pattern", "mechanism_class", "target_actor")
                  if _norm(da.get(k)) and _norm(da.get(k)) == _norm(db.get(k))]
        pair = f"{a.get('id')} and {b.get('id')}"
        if len(shared) == 3:
            errors.append(f"{pair} share opportunity_pattern, mechanism_class, AND target_actor — "
                          "the same idea wearing different words; keep one, replace the other")
        elif len(shared) == 2:
            warnings.append(f"{pair} share {shared[0]} and {shared[1]} — verify they fail together or succeed separately")
        sim = _jaccard(_tokens(a.get("name", "") + " " + a.get("one_liner", "")),
                       _tokens(b.get("name", "") + " " + b.get("one_liner", "")))
        if sim > JACCARD_WARN_THRESHOLD:
            warnings.append(f"{pair} read {sim:.0%} alike in name/one_liner — check they are structurally distinct")

    # Concentration across the whole portfolio.
    if len(resolved) >= 2:
        for key in ("opportunity_pattern", "target_actor"):
            values = {_norm((c.get("descriptor") or {}).get(key)) for c in resolved}
            if len(values) == 1:
                warnings.append(f"every survivor has the same {key} — one wrong assumption kills the whole portfolio")

    # Bookkeeping honesty.
    considered = portfolio.get("candidates_considered")
    if isinstance(considered, int) and considered < len(candidates_by_id):
        warnings.append(f"candidates_considered={considered} but {len(candidates_by_id)} candidate files exist on disk")
    if isinstance(considered, int) and considered > 0 and considered == len(survivors):
        warnings.append("every candidate considered became a survivor — the gates did not bite; "
                        "either generation was too timid or the gates were skipped")
    if graveyard_count_on_disk is not None:
        claimed = portfolio.get("graveyard_count")
        if isinstance(claimed, int) and claimed != graveyard_count_on_disk:
            warnings.append(f"graveyard_count={claimed} but {graveyard_count_on_disk} files in graveyard/")

    return errors, warnings


def load_run(run_dir):
    run = Path(run_dir)
    portfolio_path = run / "portfolio" / "portfolio.json"
    portfolio = json.loads(portfolio_path.read_text(encoding="utf-8"))
    candidates_by_id = {}
    for p in sorted((run / "candidates").glob("*.json")):
        try:
            cand = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"unreadable candidate file {p}: {exc}") from exc
        if isinstance(cand, dict) and cand.get("id"):
            candidates_by_id[cand["id"]] = cand
    obs_dir = run / "observations"
    observation_ids = load_observation_ids(obs_dir) if obs_dir.is_dir() else None
    probe_dir = run / "probes"
    probes = load_probes(probe_dir) if probe_dir.is_dir() else None
    graveyard = run / "graveyard"
    graveyard_count = len(list(graveyard.glob("*.json"))) if graveyard.is_dir() else None
    return portfolio, candidates_by_id, observation_ids, graveyard_count, probes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", help="run directory created by init_run.py")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    try:
        portfolio, candidates_by_id, observation_ids, graveyard_count, probes = load_run(args.run_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    errors, warnings = audit_portfolio(portfolio, candidates_by_id, observation_ids, graveyard_count, probes)

    if args.json:
        print(json.dumps({"errors": errors, "warnings": warnings, "ok": not errors}, indent=2, ensure_ascii=False))
    else:
        verdict = "FAIL" if errors else "PASS"
        print(f"[{verdict}] portfolio audit for {args.run_dir}: {len(errors)} error(s), {len(warnings)} warning(s)")
        for e in errors:
            print(f"  ERROR   {e}")
        for w in warnings:
            print(f"  warning {w}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
