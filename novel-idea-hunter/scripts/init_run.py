#!/usr/bin/env python3
"""Scaffold a run workspace for one novel-idea-hunter discovery run.

Creates the directory layout the other scripts expect and a run.json phase
tracker, so a run leaves an auditable trail instead of living only in the
model's context window.

Usage:
    python3 init_run.py --domain "LLM evaluation tooling" --mode deep \
        --product-shape saas-subscription [--out DIR]

Prints the created run directory path on stdout (last line), so callers can
capture it: RUN_DIR=$(python3 init_run.py ... | tail -1)
"""

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

PHASES = [
    "brief", "observe", "normalize", "map", "diverge",
    "slop-gate", "prosecute", "attack", "edge", "portfolio", "report",
]
SUBDIRS = ["observations", "candidates", "graveyard", "portfolio", "notes"]
# Mirrors lint_candidate.PRODUCT_SHAPES — kept as a plain list here (not an
# import) so this script has no dependency on lint_candidate; a test asserts
# the two stay in sync.
PRODUCT_SHAPES = [
    "saas-subscription", "usage-based-platform", "marketplace",
    "services-led", "open-source-stewardship", "hardware", "data-api-product",
]


def slugify(text, max_len=40):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-") or "run"


def init_run(domain, mode, product_shape, out_dir):
    now = _dt.datetime.now()
    run_id = f"{now:%Y%m%d-%H%M%S}-{slugify(domain)}"
    run_dir = Path(out_dir) / run_id
    if run_dir.exists():
        raise FileExistsError(f"run directory already exists: {run_dir}")
    for sub in SUBDIRS:
        (run_dir / sub).mkdir(parents=True)
    run_meta = {
        "run_id": run_id,
        "domain": domain,
        "mode": mode,
        "product_shape": product_shape,
        "created": now.isoformat(timespec="seconds"),
        "phases": [{"name": p, "status": "pending"} for p in PHASES],
    }
    (run_dir / "run.json").write_text(json.dumps(run_meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (run_dir / "notes" / "PROGRESS.md").write_text(
        f"# Run {run_id}\n\nDomain: {domain}\nMode: {mode}\nProduct shape: {product_shape}\n\n"
        + "".join(f"- [ ] {p}\n" for p in PHASES)
        + "\nUpdate run.json phase statuses (pending -> in-progress -> done) as you go.\n",
        encoding="utf-8",
    )
    return run_dir


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--domain", required=True, help="the search brief's domain or problem area")
    ap.add_argument("--mode", choices=["quick", "deep"], default="deep")
    ap.add_argument("--product-shape", required=True, choices=PRODUCT_SHAPES,
                     help="the kind of thing a survivor should be — drives Diverge and the Attack goal profile")
    ap.add_argument("--out", default="idea-runs", help="parent directory for runs (default ./idea-runs)")
    args = ap.parse_args(argv)
    try:
        run_dir = init_run(args.domain, args.mode, args.product_shape, args.out)
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"created run workspace with subdirs: {', '.join(SUBDIRS)}")
    print(run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
