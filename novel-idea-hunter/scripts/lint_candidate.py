#!/usr/bin/env python3
"""Deterministic lint for candidate JSON files.

This is the slop gate. It cannot judge whether an idea is good, but it can
mechanically reject the shapes that bad ideas reliably arrive in: no traceable
evidence, vague mechanisms, self-graded novelty, and edge claims without
assets. Exit code 0 = clean, 1 = errors found, 2 = usage/IO problem.

Usage:
    python3 lint_candidate.py CANDIDATE.json [CANDIDATE2.json ...]
        [--observations DIR] [--probes DIR] [--require-shape SHAPE] [--json]

--observations points at a directory of observation record JSON files; when
given, every cited observation ID must resolve to a real file. Without it the
lint still checks ID format and lens diversity (the lens is embedded in the ID).

--probes points at a directory of occupancy-probe records. With it, every
candidate's probe_id must resolve, and a candidate whose probe came back
`occupied` or `contested` must carry a probe_response saying what is different
or what killed the predecessors. Without it the lint still requires a
well-formed probe_id, because the probe is meant to happen before the
candidate exists at all.

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
PRIOR_ART_STATES = {"shipping", "stalled", "abandoned", "proposed-unadopted"}
EDGE_STATUSES = {"none", "potential", "credible", "compounding"}
PRODUCT_SHAPES = {
    "saas-subscription", "usage-based-platform", "marketplace",
    "services-led", "open-source-stewardship", "hardware", "data-api-product",
}

AMBITIONS = {"lifestyle", "venture"}
VENTURE_CRITERIA = ("scale-ceiling", "distribution-model-fit")
PROBE_STATUSES = {"clear", "occupied", "contested"}
PROBE_NEEDS_RESPONSE = {"occupied", "contested"}

OBS_ID_RE = re.compile(r"^OBS-([a-z0-9-]+)-([0-9]{2,})$")
CAND_ID_RE = re.compile(r"^CAND-[0-9]{2,}$")
PROBE_ID_RE = re.compile(r"^PROBE-[0-9]{2,}$")

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
SELF_REFUTATION_MIN_CHARS = 60
KILL_NOTE_MIN_CHARS = 40
# Pattern-spread floors, applied across a whole invocation (see
# lint_candidate_set). Measured from a wide run where 16 of 19 candidates shared
# one opportunity_pattern: cross-domain-transfer, which by construction imports
# mechanisms already proven elsewhere and so is pre-disposed to prosecute as
# 'crowded' or 'duplicated'. Breadth in the research is worthless if generation
# throws it away.
PATTERN_SPREAD = {           # breadth -> (min distinct patterns, max share of one)
    "wide": (6, 0.40),
    "focused": (3, 0.60),
}
PATTERN_SPREAD_MIN_CANDIDATES = 8


def _text_fields_for_slop_scan(cand):
    parts = [cand.get("name", ""), cand.get("one_liner", "")]
    mech = cand.get("mechanism") or {}
    parts.extend(mech.get("steps") or [])
    return " \n".join(str(p) for p in parts)


def _lens_of(obs_id):
    m = OBS_ID_RE.match(obs_id)
    return m.group(1) if m else None


def lint_candidate(cand, observation_ids_on_disk=None, required_shape=None, probes_on_disk=None,
                   required_ambition=None):
    """Return (errors, warnings) lists of strings for one candidate dict.

    required_shape, when given, hard-enforces that this candidate's
    product_shape matches it (the run-level --require-shape constraint).
    probes_on_disk, when given, maps probe id -> probe record so the lint can
    resolve probe_id and demand a probe_response where the probe found
    occupancy."""
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

    # --- self-refutation ---
    # In the AI-slop run, 4 of 19 candidates were killed by evidence sitting in
    # the observations they themselves cited: a caveat inside the cited record,
    # a why_now that was the incumbent already doing it, a gate already shipping
    # free in an observed tool, a kill condition the cited operator had already
    # published. Citing an observation is not the same as re-reading it, so the
    # re-read is made a written artifact. See references/facets.md.
    selfref = str(cand.get("self_refutation", ""))
    if need(len(selfref) >= SELF_REFUTATION_MIN_CHARS,
            f"self_refutation missing or under {SELF_REFUTATION_MIN_CHARS} chars — re-read the cited "
            "observations and state what in them cuts against this candidate, or state that you "
            "re-read them and found no counter-claim. Citing evidence is not reading it"):
        cited_here = [o for o in obs_ids if str(o) in selfref]
        need(cited_here,
             "self_refutation names no observation id from this candidate's own observation_ids — "
             "it must point at the specific record it re-read, not gesture at the evidence in general")

    # --- occupancy probe ---
    # 44 of 44 candidates across two full runs died on prior art or standing
    # rather than on mechanism quality, so the cheap look happens before the
    # expensive write. See references/occupancy-probe.md.
    pid = cand.get("probe_id", "")
    need(PROBE_ID_RE.match(str(pid)), f"probe_id '{pid}' missing or malformed — probe the shape before writing "
                                      "the candidate; the probe is what makes a dead shape cheap to discover")
    if probes_on_disk is not None and PROBE_ID_RE.match(str(pid)):
        probe = probes_on_disk.get(pid)
        if need(probe is not None, f"probe {pid} not found on disk"):
            pstatus = (probe or {}).get("status", "")
            if pstatus not in PROBE_STATUSES:
                errors.append(f"probe {pid} has status '{pstatus}' not in {sorted(PROBE_STATUSES)}")
            elif pstatus in PROBE_NEEDS_RESPONSE:
                need(len(str(cand.get("probe_response", ""))) >= 25,
                     f"probe {pid} came back '{pstatus}' but the candidate carries no probe_response — "
                     + ("state the specific difference from what is already shipping"
                        if pstatus == "occupied" else
                        "state what killed the earlier attempts and what has changed since"))

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
        st = (art or {}).get("state", "")
        if st and st not in PRIOR_ART_STATES:
            errors.append(f"novelty.closest_prior_art[{i}].state '{st}' not in {sorted(PRIOR_ART_STATES)}")

    # A dead competitor is not a fatal competitor. 'duplicated' is terminal, so it
    # must rest on something still alive; prior art that is entirely abandoned or
    # merely proposed is evidence about a contested space, not a closed one.
    if verdict == "duplicated" and prior:
        states = [(art or {}).get("state") for art in prior]
        if states and all(s in {"abandoned", "stalled", "proposed-unadopted"} for s in states if s) \
                and any(s for s in states):
            errors.append("verdict 'duplicated' but every dated prior-art entry is abandoned, stalled or "
                          "merely proposed — a dead predecessor makes the space contested, not closed; "
                          "use 'crowded' or 'differentiated' and record what killed them")

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

    # A kill ends a candidate, so it owes a reason someone else can audit.
    for t in kills:
        crit = (t or {}).get("criterion", "?")
        if len(str((t or {}).get("note", "")).strip()) < KILL_NOTE_MIN_CHARS:
            errors.append(f"kill on '{crit}' carries no substantive note (under {KILL_NOTE_MIN_CHARS} chars) — "
                          "a criterion slug is not a reason; write what a skeptic would need to check")

    # Backtested recalibration: 'the incumbent could ship this' killed 10 of 13
    # candidates in one run, but the same reasoning kills companies that in fact
    # won against an incumbent shipping the capability bundled at zero marginal
    # price. So a kill here must rest on prior art prosecution actually found
    # shipping — not on the hypothetical that an incumbent might move.
    # See references/kill-criteria.md.
    iwb = [t for t in kills if (t or {}).get("criterion") == "incumbent-weekend-build"]
    if iwb and verdict:
        live_same_wedge = [a for a in prior
                           if (a or {}).get("state") == "shipping"
                           and (a or {}).get("relationship") in {"direct-competitor", "incumbent-feature"}]
        need(live_same_wedge,
             "kill on 'incumbent-weekend-build' but no prior-art entry is both state 'shipping' and "
             "relationship 'direct-competitor' or 'incumbent-feature' — an incumbent that *could* move is "
             "the normal condition of a live market, not a kill. Name the shipping product serving this "
             "wedge, or record the result as 'unclear'")

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
            errors.append("survivor with verdict 'duplicated' — a live product already serves this actor")
        if verdict == "crowded":
            # Being occupied is not by itself disqualifying: most businesses enter
            # occupied space. What a crowded candidate owes is a reason the incumbent
            # will not serve this wedge and a path to the buyer — which the attack
            # phase already measures. Requiring a proprietary edge instead made every
            # crowded candidate in a public-web run die by arithmetic rather than by
            # judgement, since edge-verification caps such runs at 'none'.
            results_by_criterion = {t.get("criterion"): t.get("result")
                                    for t in kill_tests if isinstance(t, dict)}
            for criterion in ("incumbent-weekend-build", "reachable-distribution"):
                res = results_by_criterion.get(criterion)
                if res is None:
                    errors.append(f"survivor in a crowded space did not apply '{criterion}' — "
                                  "entering an occupied space requires naming what stops the incumbent "
                                  "and how the buyer is reached")
                elif res != "pass":
                    errors.append(f"survivor in a crowded space has '{criterion}' = '{res}' — "
                                  "an occupied space is survivable only when both of these pass")

        # A venture run additionally asks whether the arithmetic allows the target
        # at all, and whether the selling motion and the pricing cohere. Both are
        # judgements a good small business can fail while remaining a good small
        # business, so they only bind when the brief asked for venture scale.
        if required_ambition == "venture":
            results_by_criterion = {t.get("criterion"): t.get("result")
                                    for t in kill_tests if isinstance(t, dict)}
            for criterion in VENTURE_CRITERIA:
                res = results_by_criterion.get(criterion)
                if res is None:
                    errors.append(f"venture run: survivor did not apply '{criterion}' — "
                                  "the brief asked for venture scale, so the ceiling arithmetic and the "
                                  "motion-pricing fit both have to be on the record")
                elif res != "pass":
                    errors.append(f"venture run: survivor has '{criterion}' = '{res}' — "
                                  "a candidate that cannot clear the target or whose motion and pricing "
                                  "do not cohere is a fine business but not this run's answer")

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


def lint_candidate_set(cands, breadth=None):
    """Cross-candidate checks that no single candidate file can catch.

    Takes a list of candidate dicts. Returns a dict mapping candidate id ->
    list of error strings; run-level findings are keyed under "*".

    Today this catches one failure with a real track record: a probe_response
    written once per probe and pasted onto every candidate sharing that probe.
    In the AI-slop run three candidates carried a response answering the
    occupancy question for a different actor entirely, and the per-file lint
    passed all three because the field was present and long enough. Occupancy
    is a question about a specific actor's market, so one text cannot answer it
    for two different actors.
    """
    errors = {}
    groups = {}
    for c in cands:
        if not isinstance(c, dict):
            continue
        pid, resp = c.get("probe_id"), str(c.get("probe_response", ""))
        if pid and resp:
            groups.setdefault((pid, resp), []).append(c)
    for (pid, _resp), members in groups.items():
        if len(members) < 2:
            continue
        actors = {str(((m.get("descriptor") or {}).get("target_actor") or "")) for m in members}
        if len(actors) < 2:
            continue  # same actor, same probe: one response legitimately covers both
        ids = sorted(str(m.get("id")) for m in members)
        for m in members:
            errors.setdefault(str(m.get("id")), []).append(
                f"probe_response is byte-identical across {ids} — all sharing {pid} but targeting "
                f"{len(actors)} different actors. Occupancy is a question about one actor's market; "
                "write the response per candidate, not per probe")

    # --- pattern spread ---
    spread = PATTERN_SPREAD.get(breadth or "")
    live = [c for c in cands if isinstance(c, dict) and c.get("status") != "killed"]
    if spread and len(live) >= PATTERN_SPREAD_MIN_CANDIDATES:
        min_distinct, max_share = spread
        pats = [str(((c.get("descriptor") or {}).get("opportunity_pattern") or "")) for c in live]
        counts = {}
        for p in pats:
            counts[p] = counts.get(p, 0) + 1
        if len(counts) < min_distinct:
            errors.setdefault("*", []).append(
                f"{breadth} breadth used only {len(counts)} distinct opportunity_pattern(s) across "
                f"{len(live)} candidates; at least {min_distinct} required. Unused: "
                f"{sorted(OPPORTUNITY_PATTERNS - set(counts))}. Breadth is a property of the funnel, "
                "not of the research that fed it")
        top, n = max(counts.items(), key=lambda kv: kv[1])
        if n / len(live) > max_share:
            errors.setdefault("*", []).append(
                f"opportunity_pattern '{top}' covers {n}/{len(live)} candidates "
                f"({n / len(live):.0%}), over the {max_share:.0%} ceiling for {breadth} breadth — "
                "this is premature convergence at the pattern level; generate the next candidates "
                "from patterns the map has not been mined for")
    return errors


def load_probes(probe_dir):
    """Map probe id -> probe record from a directory of probe JSON files."""
    probes = {}
    for p in Path(probe_dir).rglob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for rec in (data if isinstance(data, list) else [data]):
            if isinstance(rec, dict) and "id" in rec:
                probes[rec["id"]] = rec
    return probes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("candidates", nargs="+", help="candidate JSON file(s)")
    ap.add_argument("--observations", help="directory of observation record JSON files")
    ap.add_argument("--probes", help="directory of occupancy-probe record JSON files")
    ap.add_argument("--require-shape", choices=sorted(PRODUCT_SHAPES),
                     help="fail any candidate whose product_shape isn't this run's declared shape")
    ap.add_argument("--require-ambition", choices=sorted(AMBITIONS),
                     help="venture: survivors must additionally pass scale-ceiling and distribution-model-fit")
    ap.add_argument("--breadth", choices=sorted(PATTERN_SPREAD),
                     help="enforce the opportunity_pattern spread floors for this run's declared breadth")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    obs_ids = load_observation_ids(args.observations) if args.observations else None
    probes = load_probes(args.probes) if args.probes else None
    results, loaded = [], []
    for path in args.candidates:
        try:
            cand = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: cannot read {path}: {exc}", file=sys.stderr)
            return 2
        errors, warnings = lint_candidate(cand, obs_ids, args.require_shape, probes,
                                          args.require_ambition)
        loaded.append(cand)
        results.append({"file": path, "id": cand.get("id"), "errors": errors, "warnings": warnings})

    # Cross-candidate checks run over the whole invocation, so lint the run's
    # candidates together (the Phase 5 command globs them) rather than one file
    # at a time — a per-file invocation cannot see these.
    run_level = []
    for cid, errs in lint_candidate_set(loaded, args.breadth).items():
        if cid == "*":
            run_level.extend(errs)
            continue
        for r in results:
            if str(r["id"]) == cid:
                r["errors"].extend(errs)
    any_errors = bool(run_level) or any(r["errors"] for r in results)

    if args.json:
        print(json.dumps({"results": results, "run_errors": run_level, "ok": not any_errors},
                         indent=2, ensure_ascii=False))
    else:
        for e in run_level:
            print(f"[FAIL] run-level: {e}")
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
