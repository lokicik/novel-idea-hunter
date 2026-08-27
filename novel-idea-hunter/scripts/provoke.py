#!/usr/bin/env python3
"""Deterministic generation provocations for Phase 4.

The problem this solves: asking a model to "be more creative" reproduces the
model's prior, because mode collapse is a property of the model, not of its
effort. Post-training alignment favours typical text (typicality bias in
preference data), and idea diversity is known to saturate as generation is
scaled up — more candidates do not mean more different candidates.

So the provocation comes from outside the model. This script draws generation
briefs deterministically from the run id: an opportunity_pattern the run has
not mined, a TRIZ inventive principle to force onto the cluster's tension, and
an inversion directive. The draw is reproducible (same run, same briefs) and
it is not chosen by taste.

Usage:
    python3 provoke.py --run ./idea-runs/<run-id> --count 12
    python3 provoke.py --run <dir> --count 8 --write   # also writes notes/provocations.md

See references/provocations.md for what to do with the output.
"""

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

# Mirrors lint_candidate.OPPORTUNITY_PATTERNS; a test asserts they stay in sync.
OPPORTUNITY_PATTERNS = [
    "capability-threshold-crossing", "cross-domain-transfer", "data-exhaust-capture",
    "expert-labor-compression", "failed-idea-revival", "incumbent-incentive-gap",
    "rebundling", "regulatory-wedge", "trust-gap", "unbundling",
    "workaround-productization", "workflow-collapse",
]

# Altshuller's 40 inventive principles, distilled from patent analysis, each with
# a gloss for market mechanisms. The physical ones (thermal expansion, porous
# materials) are kept deliberately: forcing a literal-physical principle onto a
# market mechanism is exactly the move a model will not make unprompted, and the
# translation effort is where the non-obvious candidate comes from.
TRIZ = [
    ("Segmentation", "split the thing into independent parts that can be priced or gated separately"),
    ("Taking out", "extract only the troublesome part and treat it separately from the rest"),
    ("Local quality", "make different parts of the system serve different conditions instead of one uniform rule"),
    ("Asymmetry", "deliberately treat two sides of the transaction unequally"),
    ("Merging", "bring identical or adjacent operations together in time or place"),
    ("Universality", "make one element perform several functions so others can be removed"),
    ("Nested doll", "place one mechanism inside another that already has distribution"),
    ("Anti-weight", "pair the heavy thing with something that lifts it, rather than making it lighter"),
    ("Preliminary anti-action", "pre-load the opposite stress so the real stress is absorbed"),
    ("Preliminary action", "do the required change before it is needed, at a moment when it is cheap"),
    ("Beforehand cushioning", "prepare the remedy in advance because reliability will be low"),
    ("Equipotentiality", "remove the need to lift at all by changing the operating conditions"),
    ("The other way round", "invert the action: the moving part becomes fixed, the payer becomes the paid"),
    ("Spheroidality", "replace a straight line or flat rule with a curve, a cycle, or a rotation"),
    ("Dynamics", "make a fixed characteristic adjustable at runtime by whoever is closest"),
    ("Partial or excessive action", "if the right amount is hard, do slightly less or wildly more"),
    ("Another dimension", "move from one axis to two, or stack what was laid out in a line"),
    ("Mechanical vibration", "oscillate a parameter instead of holding it constant"),
    ("Periodic action", "replace continuous operation with pulses, and use the gaps"),
    ("Continuity of useful action", "eliminate idle time: make every part work at full load all the time"),
    ("Skipping", "run the harmful or costly phase at very high speed to pass through it"),
    ("Blessing in disguise", "use the harmful factor itself to obtain a positive effect"),
    ("Feedback", "introduce a loop, or if one exists, change its sign or its gain"),
    ("Intermediary", "insert a temporary intermediate carrier that is removed afterwards"),
    ("Self-service", "make the object serve itself, performing its own maintenance or verification"),
    ("Copying", "use a cheap copy in place of the fragile, expensive or unavailable original"),
    ("Cheap short-living objects", "replace an expensive durable thing with many disposable ones"),
    ("Mechanics substitution", "swap the physical channel for a field: reputation, price, or information"),
    ("Pneumatics and hydraulics", "replace solid parts with something that flows and takes the shape of its container"),
    ("Flexible shells and thin films", "isolate the object from its environment with a thin boundary"),
    ("Porous materials", "make the thing porous, or fill its existing holes with something useful"),
    ("Color changes", "change what is visible: make the invisible legible, or hide what is distracting"),
    ("Homogeneity", "make interacting objects out of the same material so the seam disappears"),
    ("Discarding and recovering", "let a part vanish after use, or restore it in place during operation"),
    ("Parameter changes", "change the degree of flexibility, concentration, temperature or granularity"),
    ("Phase transitions", "exploit what happens at the boundary between two states, not within either"),
    ("Thermal expansion", "use the fact that things change size under load, and use that change as the signal"),
    ("Strong oxidants", "enrich the environment so the reaction that was slow becomes fast"),
    ("Inert atmosphere", "replace the reactive surroundings with a neutral one to stop the reaction"),
    ("Composite materials", "replace a uniform structure with a layered one tuned per layer"),
]

INVERSIONS = [
    "Invert who pays: make the party currently paying the one who is paid.",
    "Invert the gate: admit everything, and charge or verify at exit instead of entry.",
    "Remove the obvious operator: who runs this if the platform refuses to?",
    "Sell the failure: make the thing that happens when the mechanism fails the product.",
    "Collapse the timebox to one day, then stretch it to ten years — which one breaks?",
    "Assume the scarce input is now free and infinite. What becomes scarce instead?",
    "Give the mechanism to the flooding party rather than the drowning party.",
    "Assume the incumbent ships this free next quarter. What is left that they cannot ship?",
    "Make the buyer the person currently treated as the problem.",
    "Delete the largest component of the mechanism and make the rest compensate.",
    "Assume adoption is mandatory by law. Design for the second year, not the launch.",
    "Serve the population everyone else is excluding, using the exclusion as the wedge.",
]


def load_run(run_dir):
    run_dir = Path(run_dir)
    meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    used = {}
    for sub in ("candidates", "graveyard"):
        for f in (run_dir / sub).glob("*.json"):
            try:
                c = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            p = (c.get("descriptor") or {}).get("opportunity_pattern")
            if p:
                used[p] = used.get(p, 0) + 1
    return meta, used


def draw(run_id, count, used_patterns, seed=None):
    """Deterministic given (run_id, count, used_patterns, seed)."""
    if seed is None:
        seed = int(hashlib.sha256(str(run_id).encode("utf-8")).hexdigest()[:12], 16)
    rng = random.Random(seed)
    # Least-mined patterns first, ties broken deterministically by name.
    order = sorted(OPPORTUNITY_PATTERNS, key=lambda p: (used_patterns.get(p, 0), p))
    principles = TRIZ[:]
    rng.shuffle(principles)
    inversions = INVERSIONS[:]
    rng.shuffle(inversions)
    briefs = []
    for i in range(count):
        briefs.append({
            "slot": i + 1,
            "opportunity_pattern": order[i % len(order)],
            "triz_principle": principles[i % len(principles)][0],
            "triz_gloss": principles[i % len(principles)][1],
            "inversion": inversions[i % len(inversions)],
        })
    return briefs


def render(run_id, briefs, used_patterns):
    out = [f"# Generation provocations — {run_id}", ""]
    mined = ", ".join(f"{k} ({v})" for k, v in sorted(used_patterns.items())) or "none yet"
    out += [f"Already mined: {mined}.", "",
            "Each slot is a forced brief, drawn deterministically from the run id — not chosen.",
            "Apply the TRIZ principle to the *tension* your map named for the relevant cluster,",
            "not to the domain in general. A brief that produces nothing is a recorded result:",
            "say so and move on. Do not silently reassign yourself an easier slot.", ""]
    for b in briefs:
        out += [f"## Slot {b['slot']} — pattern `{b['opportunity_pattern']}`",
                f"- **TRIZ {b['triz_principle']}**: {b['triz_gloss']}",
                f"- **Inversion**: {b['inversion']}", ""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True, help="run directory created by init_run.py")
    ap.add_argument("--count", type=int, default=12, help="number of forced briefs to draw")
    ap.add_argument("--seed", type=int, help="override the run-id-derived seed (for a second wave)")
    ap.add_argument("--write", action="store_true", help="also write <run>/notes/provocations.md")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    try:
        meta, used = load_run(args.run)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read run: {exc}", file=sys.stderr)
        return 2

    briefs = draw(meta.get("run_id", args.run), args.count, used, args.seed)
    if args.json:
        print(json.dumps({"run_id": meta.get("run_id"), "briefs": briefs}, indent=2, ensure_ascii=False))
    else:
        text = render(meta.get("run_id", args.run), briefs, used)
        print(text)
        if args.write:
            p = Path(args.run) / "notes" / "provocations.md"
            p.write_text(text + "\n", encoding="utf-8")
            print(f"\nwritten: {p}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
