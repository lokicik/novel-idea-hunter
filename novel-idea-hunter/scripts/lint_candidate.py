#!/usr/bin/env python3
"""Deterministic lint for candidate JSON files.

This is the slop gate. It cannot judge whether an idea is good, but it can
mechanically reject the shapes that bad ideas reliably arrive in: no traceable
evidence, vague mechanisms, self-graded novelty, and edge claims without
assets. Exit code 0 = clean, 1 = errors found, 2 = usage/IO problem.

Usage:
    python3 lint_candidate.py CANDIDATE.json [CANDIDATE2.json ...]
        [--observations DIR] [--require-shape SHAPE] [--json]

--observations points at a directory of observation record JSON files; when
given, every cited observation ID must resolve to a real file. Without it the
lint still checks ID format and lens diversity (the lens is embedded in the ID).

--require-shape hard-enforces that every candidate's product_shape matches
the run's declared shape (e.g. the user asked for "saas-subscription" and
generation must not wander into a differently-shaped idea). Every candidate
always needs a valid product_shape regardless of this flag; the flag adds a
per-run consistency check on top.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# --- Controlled vocabularies (mirror scripts/schemas/*.schema.json) ---

LENSES = {
    "capability-shifts", "manual-workflows", "workarounds", "trust-bottlenecks",
    "ecosystem-breakage", "pricing-incentives", "failed-products", "cross-domain",
    "private-edge",
}
STATUSES = {"draft", "gated", "prosecuted", "attacked", "survivor", "killed"}
OPPORTUNITY_PATTERNS = {
    "capability-threshold-crossing", "workaround-productization", "workflow-collapse",
    "trust-gap", "unbundling", "rebundling", "cross-domain-transfer",
    "data-exhaust-capture", "regulatory-wedge", "incumbent-incentive-gap",
    "failed-idea-revival", "expert-labor-compression",
}
MECHANISM_CLASSES = {
    "pipeline-automation", "verification-layer", "monitoring-alerting",
    "translation-bridge", "coordination-marketplace", "generation-tooling",
    "decision-support", "compliance-automation", "infrastructure-primitive",
    "embedded-workflow-tool",
}
NOVELTY_VERDICTS = {"duplicated", "crowded", "differentiated", "no-close-prior-art-found", "unverified"}
RECHECK_OUTCOMES = {"upheld", "overturned"}
PRIOR_ART_RELATIONSHIPS = {
    "direct-competitor", "adjacent-product", "incumbent-feature", "open-source",
    "failed-attempt", "academic", "patent",
}
EDGE_STATUSES = {"none", "potential", "credible", "compounding"}
PRODUCT_SHAPES = {
    "saas-subscription", "usage-based-platform", "marketplace",
    "services-led", "open-source-stewardship", "hardware", "data-api-product",
}

OBS_ID_RE = re.compile(r"^OBS-([a-z0-9-]+)-([0-9]{2,})$")
CAND_ID_RE = re.compile(r"^CAND-[0-9]{2,}$")

# Generic product shapes. Matching one is not fatal by itself — the words are a
# symptom, not the disease — but a match plus an incomplete mechanism is fatal.
SLOP_SHAPES = [
    (re.compile(r"\bai[- ]powered\b", re.I), "ai-powered X"),
    (re.compile(r"\bai (assistant|copilot|companion) for\b", re.I), "AI assistant for X"),
    (re.compile(r"\bcopilot for\b", re.I), "copilot for X"),
    (re.compile(r"\ball[- ]in[- ]one\b", re.I), "all-in-one platform"),
    (re.compile(r"\bplatform (that )?connect(s|ing)?\b", re.I), "platform connecting X and Y"),
    (re.compile(r"\buber for\b", re.I), "Uber for X"),
    (re.compile(r"\bchatgpt for\b", re.I), "ChatGPT for X"),
    (re.compile(r"\bmarketplace for\b", re.I), "marketplace for X"),
    (re.compile(r"\bpersonalized (ai )?(recommendations|assistant)\b", re.I), "personalized recommendations"),
    (re.compile(r"\bai agents? (that|to|which) automat", re.I), "AI agent that automates X"),
    (re.compile(r"\b(unified|centralized) dashboard\b", re.I), "dashboard for X"),
]

# Words that appear in steps when the author does not actually know how the
# product works. A mechanism step containing one of these is an error.
VAGUE_STEP_PATTERNS = [
    (re.compile(r"\b(leverage|utilize)(s|d|ing)?\b", re.I), "filler verb (leverage/utilize)"),
    (re.compile(r"\bharness(es|ed|ing)?\s+(the|ai|ml|llms?|machine learning|power)\b", re.I),
     "filler verb (harnessing AI/the power of...)"),
    (re.compile(r"\buses? (ai|ml|machine learning|artificial intelligence|llms?) to\b", re.I), "'uses AI to' without a concrete operation"),
    (re.compile(r"\bai[- ]powered\b", re.I), "'AI-powered' inside a mechanism step"),
    (re.compile(r"\bseamless(ly)?\b", re.I), "'seamless' is a hope, not a step"),
    (re.compile(r"\b(revolutioniz|disrupt(s|ing)?\b)", re.I), "marketing verb in a mechanism step"),
    (re.compile(r"\b(cutting[- ]edge|state[- ]of[- ]the[- ]art|next[- ]gen(eration)?)\b", re.I), "buzzword in a mechanism step"),
    (re.compile(r"\bintelligent(ly)? automat", re.I), "'intelligently automates' without saying how"),
]

# Claims no retrieval process can honestly support. Anywhere in the candidate.
FORBIDDEN_NOVELTY_CLAIMS = [
    re.compile(p, re.I) for p in [
        r"\bglobally unique\b", r"\bno competitors?\b", r"\bzero competition\b",
        r"\bfirst[- ]ever\b", r"\bnobody (has|is doing)\b", r"\bcompletely novel\b",
        r"\bfirst[- ]of[- ]its[- ]kind\b", r"\bunprecedented\b", r"\bno one else\b",
    ]
]

# Edge claims that are not actually the user's to keep.
INVALID_EDGE_PATTERNS = [
    (re.compile(r"\bfirst[- ]mover\b", re.I), "first-mover advantage is not an asset"),
    (re.compile(r"\b(my|the|our) employer'?s?\b", re.I), "employer-owned assets are not the user's edge"),
    (re.compile(r"\bcustomer('s)? (data|secrets?|confidential)\b", re.I), "customer-confidential material is not a usable edge"),
    (re.compile(r"\btemporary (api )?access\b", re.I), "temporary access is not a durable edge"),
]

PROSECUTED_STATUSES = {"prosecuted", "attacked", "survivor"}
SURVIVOR_MIN_KILL_TESTS = 5


def _text_fields_for_slop_scan(cand):
    parts = [cand.get("name", ""), cand.get("one_liner", "")]
    mech = cand.get("mechanism") or {}
    parts.extend(mech.get("steps") or [])
    return " \n".join(str(p) for p in parts)


def _lens_of(obs_id):
    m = OBS_ID_RE.match(obs_id)
    return m.group(1) if m else None


def lint_candidate(cand, observation_ids_on_disk=None, required_shape=None):
    """Return (errors, warnings) lists of strings for one candidate dict.

    required_shape, when given, hard-enforces that this candidate's
    product_shape matches it (the run-level --require-shape constraint)."""
    errors, warnings = [], []

    def need(cond, msg):
        if not cond:
            errors.append(msg)
        return cond

    # --- identity / status ---
    if not isinstance(cand, dict):
        return ["candidate is not a JSON object"], warnings
    cid = cand.get("id", "")
    need(CAND_ID_RE.match(str(cid)), f"id '{cid}' does not match CAND-<nn>")
    status = cand.get("status", "")
    need(status in STATUSES, f"status '{status}' not in {sorted(STATUSES)}")
    need(len(str(cand.get("name", ""))) >= 3, "name missing or too short")
    need(len(str(cand.get("one_liner", ""))) >= 20,
         "one_liner missing or under 20 chars — it must state actor + moment + mechanism")

    # --- product shape ---
    pshape = cand.get("product_shape", "")
    need(pshape in PRODUCT_SHAPES, f"product_shape '{pshape}' not in controlled vocabulary {sorted(PRODUCT_SHAPES)} — "
                                   "declare what kind of thing this is meant to be, it is not optional color")
    if required_shape is not None:
        need(pshape == required_shape, f"product_shape '{pshape}' does not match this run's required shape "
                                       f"'{required_shape}' — generation wandered outside what the user asked for")

    # --- evidence trail ---
    obs_ids = cand.get("observation_ids") or []
    need(len(obs_ids) >= 3, f"only {len(obs_ids)} observation_ids cited; at least 3 required — "
                            "an idea that cannot cite its observations does not exist")
    bad_ids = [o for o in obs_ids if not OBS_ID_RE.match(str(o))]
    need(not bad_ids, f"malformed observation ids: {bad_ids}")
    lenses = {_lens_of(o) for o in obs_ids if OBS_ID_RE.match(str(o))}
    unknown_lenses = {l for l in lenses if l not in LENSES}
    if unknown_lenses:
        warnings.append(f"observation ids reference unknown lenses: {sorted(unknown_lenses)}")
    need(len(lenses) >= 2, f"cited observations come from only {len(lenses)} lens(es); "
                           "at least 2 distinct lenses required so the idea is a recombination, not one source retold")
    if observation_ids_on_disk is not None:
        missing = [o for o in obs_ids if o not in observation_ids_on_disk]
        need(not missing, f"cited observations not found on disk: {missing}")

    # --- mechanism ---
    mech = cand.get("mechanism") or {}
    need(len(str(mech.get("actor", ""))) >= 8, "mechanism.actor missing or not narrow enough (under 8 chars)")
    need(len(str(mech.get("trigger", ""))) >= 8, "mechanism.trigger missing — name the workflow moment the product enters")
    steps = mech.get("steps") or []
    need(2 <= len(steps) <= 4, f"mechanism.steps has {len(steps)} steps; 2-4 required")
    for i, step in enumerate(steps):
        s = str(step)
        if len(s) < 20 or len(s.split()) < 5:
            errors.append(f"mechanism.steps[{i}] too thin ('{s[:40]}...') — each step names an input, an operation, and an output")
        for pat, label in VAGUE_STEP_PATTERNS:
            if pat.search(s):
                errors.append(f"mechanism.steps[{i}] is vague: {label}")
    need(len(str(mech.get("replaces_workaround", ""))) >= 10,
         "mechanism.replaces_workaround missing — if the actor does nothing today, the pain is probably not real")
    why = mech.get("why_now") or {}
    need(len(str(why.get("change", ""))) >= 15, "mechanism.why_now.change missing or too thin")
    why_ev = why.get("evidence_observation_ids") or []
    need(len(why_ev) >= 1, "mechanism.why_now cites no observation ids — 'why now' needs evidence, not vibes")
    if observation_ids_on_disk is not None:
        missing = [o for o in why_ev if o not in observation_ids_on_disk]
        need(not missing, f"why_now evidence observations not found on disk: {missing}")

    # --- slop gate ---
    scan_text = _text_fields_for_slop_scan(cand)
    matched_shapes = [label for pat, label in SLOP_SHAPES if pat.search(scan_text)]
    mechanism_broken = any(e.startswith("mechanism") for e in errors)
    for label in matched_shapes:
        if mechanism_broken:
            errors.append(f"generic shape '{label}' with an incomplete mechanism — this is the exact form slop takes; "
                          "fill the mechanism template or kill the candidate")
        else:
            warnings.append(f"generic shape '{label}' in name/one_liner/steps — mechanism is concrete, "
                            "but rephrase so the description carries the mechanism, not the trope")

    # --- forbidden novelty claims (anywhere) ---
    whole = json.dumps(cand, ensure_ascii=False)
    for pat in FORBIDDEN_NOVELTY_CLAIMS:
        m = pat.search(whole)
        if m:
            errors.append(f"forbidden novelty claim '{m.group(0)}' — this system's strongest permitted claim is "
                          "'no-close-prior-art-found' within a stated search scope")

    # --- descriptor ---
    desc = cand.get("descriptor") or {}
    op = desc.get("opportunity_pattern", "")
    mc = desc.get("mechanism_class", "")
    need(op in OPPORTUNITY_PATTERNS, f"descriptor.opportunity_pattern '{op}' not in controlled vocabulary")
    need(mc in MECHANISM_CLASSES, f"descriptor.mechanism_class '{mc}' not in controlled vocabulary")
    for key in ("target_actor", "workflow", "bottleneck"):
        need(len(str(desc.get(key, ""))) >= 3, f"descriptor.{key} missing")

    # --- novelty ---
    nov = cand.get("novelty") or {}
    verdict = nov.get("verdict", "")
    need(verdict in NOVELTY_VERDICTS, f"novelty.verdict '{verdict}' not in controlled vocabulary {sorted(NOVELTY_VERDICTS)}")
    scope = nov.get("scope_searched") or []
    prior = nov.get("closest_prior_art") or []
    if status in PROSECUTED_STATUSES:
        need(verdict != "unverified", f"status is '{status}' but novelty.verdict is 'unverified' — "
                                      "prosecution must complete before this status")
    if verdict in {"duplicated", "crowded", "differentiated"}:
        need(len(prior) >= 1, f"verdict '{verdict}' with empty closest_prior_art — the verdict must point at what was found")
    if verdict == "no-close-prior-art-found":
        need(len(scope) >= 4, f"'no-close-prior-art-found' claimed after searching only {len(scope)} query families; "
                              "at least 4 required — absence of evidence needs a real search behind it")
    for i, art in enumerate(prior):
        for key in ("name", "url", "relationship", "difference"):
            need(len(str((art or {}).get(key, ""))) >= 2, f"novelty.closest_prior_art[{i}].{key} missing")
        rel = (art or {}).get("relationship", "")
        if rel and rel not in PRIOR_ART_RELATIONSHIPS:
            errors.append(f"novelty.closest_prior_art[{i}].relationship '{rel}' not in controlled vocabulary")

    # --- survivor re-check (second narrow prior-art pass) ---
    recheck = nov.get("recheck")
    if recheck is not None:
        outcome = (recheck or {}).get("outcome", "")
        need(outcome in RECHECK_OUTCOMES, f"novelty.recheck.outcome '{outcome}' not in {sorted(RECHECK_OUTCOMES)}")
        need(len((recheck or {}).get("queries") or []) >= 1, "novelty.recheck.queries empty — record what was actually searched")
    if status == "survivor":
        if recheck is None:
            errors.append("survivor without novelty.recheck — one prosecution pass is one sample; "
                          "run the narrow re-check from novelty-rubric.md before promotion")
        elif (recheck or {}).get("outcome") == "overturned":
            errors.append("survivor with an overturned re-check — the differentiation claim broke; "
                          "send the candidate back to prosecution with the new evidence")

    # --- kill tests ---
    kill_tests = cand.get("kill_tests") or []
    kills = [t for t in kill_tests if (t or {}).get("result") == "kill"]
    if status in {"attacked", "survivor"}:
        need(len(kill_tests) >= (SURVIVOR_MIN_KILL_TESTS if status == "survivor" else 1),
             f"status '{status}' but only {len(kill_tests)} kill tests applied"
             + (f"; survivors need at least {SURVIVOR_MIN_KILL_TESTS}" if status == "survivor" else ""))
    for t in kills:
        if status == "survivor" and not str((t or {}).get("note", "")).strip():
            errors.append(f"survivor carries an un-overridden kill result on '{(t or {}).get('criterion', '?')}' — "
                          "either justify the override in note or move the candidate to the graveyard")
        elif status == "survivor":
            warnings.append(f"survivor overrode a kill on '{(t or {}).get('criterion', '?')}' — make sure the note holds up")

    # --- edge ---
    edge = cand.get("edge") or {}
    estatus = edge.get("status", "")
    need(estatus in EDGE_STATUSES, f"edge.status '{estatus}' not in {sorted(EDGE_STATUSES)}")
    rank = {"none": 0, "potential": 1, "credible": 2, "compounding": 3}.get(estatus, 0)
    if rank >= 1:
        need(len(str(edge.get("asset", ""))) >= 10, f"edge.status '{estatus}' requires a concrete asset description")
    if rank >= 2:
        for key in ("control", "copy_difficulty", "proof_metric"):
            need(len(str(edge.get(key, ""))) >= 10, f"edge.status '{estatus}' requires edge.{key}")
        need(len(edge.get("evidence_observation_ids") or []) >= 1,
             f"edge.status '{estatus}' requires evidence_observation_ids — an edge nobody observed is a wish")
    if estatus == "compounding":
        need(len(str(edge.get("accumulation_loop", ""))) >= 20,
             "edge.status 'compounding' requires an accumulation_loop (usage -> unique data -> better result -> retention -> more usage)")
    edge_text = " ".join(str(edge.get(k, "")) for k in ("asset", "control", "copy_difficulty"))
    for pat, label in INVALID_EDGE_PATTERNS:
        if pat.search(edge_text):
            if rank >= 2:
                errors.append(f"edge claim invalid: {label}")
            else:
                warnings.append(f"edge claim suspect: {label}")

    # --- falsification ---
    fals = cand.get("falsification") or {}
    need(len(str(fals.get("test", ""))) >= 20, "falsification.test missing — every candidate ships with the cheapest experiment that could kill it")
    need(len(str(fals.get("kill_condition", ""))) >= 10, "falsification.kill_condition missing — decide what failure looks like before running the test")

    # --- terminal states ---
    if status == "killed":
        need(len(str(cand.get("graveyard_reason", ""))) >= 10, "status 'killed' requires graveyard_reason")
    if status == "survivor":
        if verdict == "duplicated":
            errors.append("survivor with verdict 'duplicated' — a duplicate cannot survive")
        if verdict == "crowded" and rank < 2:
            errors.append("survivor in a crowded space with edge below 'credible' — "
                          "crowded is only survivable with a verified edge")

    return errors, warnings


def load_observation_ids(obs_dir):
    """Collect observation ids from obs_dir, including per-lens subdirectories
    (scout branches write into subfolders before the Normalize merge)."""
    ids = set()
    for p in Path(obs_dir).rglob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        records = data if isinstance(data, list) else [data]
        for rec in records:
            if isinstance(rec, dict) and "id" in rec:
                ids.add(rec["id"])
    return ids


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("candidates", nargs="+", help="candidate JSON file(s)")
    ap.add_argument("--observations", help="directory of observation record JSON files")
    ap.add_argument("--require-shape", choices=sorted(PRODUCT_SHAPES),
                     help="fail any candidate whose product_shape isn't this run's declared shape")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    obs_ids = load_observation_ids(args.observations) if args.observations else None
    results, any_errors = [], False
    for path in args.candidates:
        try:
            cand = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: cannot read {path}: {exc}", file=sys.stderr)
            return 2
        errors, warnings = lint_candidate(cand, obs_ids, args.require_shape)
        any_errors = any_errors or bool(errors)
        results.append({"file": path, "id": cand.get("id"), "errors": errors, "warnings": warnings})

    if args.json:
        print(json.dumps({"results": results, "ok": not any_errors}, indent=2, ensure_ascii=False))
    else:
        for r in results:
            verdict = "FAIL" if r["errors"] else "PASS"
            print(f"[{verdict}] {r['file']} ({r['id'] or 'no id'}): {len(r['errors'])} error(s), {len(r['warnings'])} warning(s)")
            for e in r["errors"]:
                print(f"  ERROR   {e}")
            for w in r["warnings"]:
                print(f"  warning {w}")
    return 1 if any_errors else 0


if __name__ == "__main__":
    sys.exit(main())
