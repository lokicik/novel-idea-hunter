"""Unit tests for the novel-idea-hunter validator scripts.

Run from the repo root:  python3 -m unittest discover tests -v
"""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "novel-idea-hunter" / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPTS))

import check_portfolio  # noqa: E402
import init_run  # noqa: E402
import lint_candidate  # noqa: E402
import provoke  # noqa: E402


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def has_error(errors, substring):
    return any(substring in e for e in errors)


class TestLintValidCandidate(unittest.TestCase):
    def setUp(self):
        self.cand = load_fixture("valid_candidate.json")

    def test_valid_candidate_passes(self):
        errors, _ = lint_candidate.lint_candidate(self.cand)
        self.assertEqual(errors, [])

    def test_observation_cross_check_flags_missing(self):
        on_disk = {"OBS-capability-shifts-01", "OBS-manual-workflows-01"}  # workarounds-02 missing
        errors, _ = lint_candidate.lint_candidate(self.cand, on_disk)
        self.assertTrue(has_error(errors, "not found on disk"))

    def test_observation_cross_check_passes_when_complete(self):
        on_disk = {"OBS-capability-shifts-01", "OBS-manual-workflows-01", "OBS-workarounds-02"}
        errors, _ = lint_candidate.lint_candidate(self.cand, on_disk)
        self.assertEqual(errors, [])

    def test_crowded_survivor_allowed_without_proprietary_edge(self):
        # Occupancy is not by itself disqualifying: a crowded candidate that
        # names what stops the incumbent and how it reaches the buyer survives
        # even with edge 'none', which is what a public-web run always yields.
        cand = copy.deepcopy(self.cand)
        cand["novelty"]["verdict"] = "crowded"
        cand["edge"] = {"status": "none"}
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertEqual(errors, [])

    def test_crowded_survivor_needs_incumbent_and_distribution_passing(self):
        cand = copy.deepcopy(self.cand)
        cand["novelty"]["verdict"] = "crowded"
        cand["edge"] = {"status": "none"}
        for t in cand["kill_tests"]:
            if t["criterion"] == "reachable-distribution":
                t["result"] = "unclear"
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "reachable-distribution"))

    def test_crowded_survivor_needs_those_criteria_applied_at_all(self):
        cand = copy.deepcopy(self.cand)
        cand["novelty"]["verdict"] = "crowded"
        cand["edge"] = {"status": "none"}
        cand["kill_tests"] = [t for t in cand["kill_tests"]
                              if t["criterion"] != "incumbent-weekend-build"]
        # keep the survivor kill-test count valid so only the new rule fires
        cand["kill_tests"].append({"criterion": "why-now-really", "result": "pass", "note": "n/a"})
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "did not apply 'incumbent-weekend-build'"))

    def test_duplicated_on_dead_prior_art_rejected(self):
        # A predecessor that died makes the space contested, not closed.
        cand = copy.deepcopy(self.cand)
        cand["status"] = "prosecuted"
        cand["kill_tests"] = []
        cand["novelty"]["verdict"] = "duplicated"
        for art in cand["novelty"]["closest_prior_art"]:
            art["state"] = "abandoned"
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "contested, not closed"))

    def test_duplicated_on_live_prior_art_allowed(self):
        cand = copy.deepcopy(self.cand)
        cand["status"] = "prosecuted"
        cand["kill_tests"] = []
        cand["novelty"]["verdict"] = "duplicated"
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertEqual(errors, [])

    def test_prior_art_state_vocabulary_enforced(self):
        cand = copy.deepcopy(self.cand)
        cand["novelty"]["closest_prior_art"][0]["state"] = "sort-of-alive"
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "state 'sort-of-alive'"))

    def test_survivor_duplicated_cannot_survive(self):
        cand = copy.deepcopy(self.cand)
        cand["novelty"]["verdict"] = "duplicated"
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "a live product already serves this actor"))

    def test_unjustified_kill_override_fails_survivor(self):
        cand = copy.deepcopy(self.cand)
        cand["kill_tests"][0] = {"criterion": "incumbent-weekend-build", "result": "kill", "note": ""}
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "un-overridden kill result"))

    def test_venture_survivor_needs_scale_and_fit(self):
        errors, _ = lint_candidate.lint_candidate(self.cand, required_ambition="venture")
        self.assertTrue(has_error(errors, "did not apply 'scale-ceiling'"))

    def test_venture_survivor_passes_with_both(self):
        cand = copy.deepcopy(self.cand)
        cand["kill_tests"] += [
            {"criterion": "scale-ceiling", "result": "pass",
             "note": "~40k ML platform teams at $6k/yr clears the target with room."},
            {"criterion": "distribution-model-fit", "result": "pass",
             "note": "Self-serve signup from the tracker audience, per-workspace monthly, seat expansion."},
        ]
        errors, _ = lint_candidate.lint_candidate(cand, required_ambition="venture")
        self.assertEqual(errors, [])

    def test_venture_survivor_rejected_on_failing_ceiling(self):
        cand = copy.deepcopy(self.cand)
        cand["kill_tests"] += [
            {"criterion": "scale-ceiling", "result": "kill", "note": "400 buyers at $2k caps at $800k."},
            {"criterion": "distribution-model-fit", "result": "pass", "note": "coherent"},
        ]
        errors, _ = lint_candidate.lint_candidate(cand, required_ambition="venture")
        self.assertTrue(has_error(errors, "scale-ceiling"))

    def test_lifestyle_run_ignores_venture_criteria(self):
        errors, _ = lint_candidate.lint_candidate(self.cand, required_ambition="lifestyle")
        self.assertEqual(errors, [])

    def test_probe_id_required(self):
        cand = copy.deepcopy(self.cand)
        del cand["probe_id"]
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "probe_id"))

    def test_probe_must_resolve_when_probes_given(self):
        errors, _ = lint_candidate.lint_candidate(self.cand, probes_on_disk={})
        self.assertTrue(has_error(errors, "not found on disk"))

    def test_clear_probe_needs_no_response(self):
        probes = {"PROBE-01": load_fixture("probe_clear.json")}
        errors, _ = lint_candidate.lint_candidate(self.cand, probes_on_disk=probes)
        self.assertEqual(errors, [])

    def test_occupied_probe_requires_probe_response(self):
        cand = copy.deepcopy(self.cand)
        cand["probe_id"] = "PROBE-02"
        probes = {"PROBE-02": load_fixture("probe_occupied.json")}
        errors, _ = lint_candidate.lint_candidate(cand, probes_on_disk=probes)
        self.assertTrue(has_error(errors, "specific difference from what is already shipping"))

    def test_contested_probe_requires_probe_response(self):
        cand = copy.deepcopy(self.cand)
        cand["probe_id"] = "PROBE-03"
        probes = {"PROBE-03": load_fixture("probe_contested.json")}
        errors, _ = lint_candidate.lint_candidate(cand, probes_on_disk=probes)
        self.assertTrue(has_error(errors, "what killed the earlier attempts"))

    def test_probe_response_satisfies_occupied_probe(self):
        cand = copy.deepcopy(self.cand)
        cand["probe_id"] = "PROBE-02"
        cand["probe_response"] = ("Existing vendors answer questionnaires from a library; none diff "
                                  "incoming clauses against prior answers to flag what changed.")
        probes = {"PROBE-02": load_fixture("probe_occupied.json")}
        errors, _ = lint_candidate.lint_candidate(cand, probes_on_disk=probes)
        self.assertEqual(errors, [])

    def test_product_shape_required(self):
        cand = copy.deepcopy(self.cand)
        del cand["product_shape"]
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "product_shape"))

    def test_product_shape_invalid_value_rejected(self):
        cand = copy.deepcopy(self.cand)
        cand["product_shape"] = "vibes-based-platform"
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "product_shape"))

    def test_require_shape_mismatch_rejected(self):
        errors, _ = lint_candidate.lint_candidate(self.cand, required_shape="marketplace")
        self.assertTrue(has_error(errors, "does not match this run's required shape"))

    def test_require_shape_match_passes(self):
        errors, _ = lint_candidate.lint_candidate(self.cand, required_shape="saas-subscription")
        self.assertEqual(errors, [])

    def test_survivor_requires_recheck(self):
        cand = copy.deepcopy(self.cand)
        del cand["novelty"]["recheck"]
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "without novelty.recheck"))

    def test_overturned_recheck_blocks_survivor(self):
        cand = copy.deepcopy(self.cand)
        cand["novelty"]["recheck"]["outcome"] = "overturned"
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "overturned re-check"))

    def test_recheck_optional_below_survivor(self):
        cand = copy.deepcopy(self.cand)
        cand["status"] = "prosecuted"
        cand["kill_tests"] = []
        del cand["novelty"]["recheck"]
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertEqual(errors, [])

    def test_recheck_bad_outcome_rejected(self):
        cand = copy.deepcopy(self.cand)
        cand["novelty"]["recheck"]["outcome"] = "confirmed-unique"
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "recheck.outcome"))

    def test_harness_as_noun_not_flagged(self):
        cand = copy.deepcopy(self.cand)
        cand["mechanism"]["steps"][0] = "Parse the team's eval harness configuration and record baseline scores per task"
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertEqual(errors, [])

    def test_harness_as_filler_verb_still_flagged(self):
        cand = copy.deepcopy(self.cand)
        cand["mechanism"]["steps"][0] = "Harness the power of AI to improve results across the entire workflow"
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "vague"))


class TestLintSlopCandidate(unittest.TestCase):
    def setUp(self):
        self.errors, self.warnings = lint_candidate.lint_candidate(load_fixture("slop_candidate.json"))

    def test_slop_candidate_fails_hard(self):
        self.assertGreaterEqual(len(self.errors), 8)

    def test_generic_shape_with_broken_mechanism(self):
        self.assertTrue(has_error(self.errors, "generic shape"))

    def test_vague_steps_flagged(self):
        self.assertTrue(has_error(self.errors, "vague"))

    def test_insufficient_observations(self):
        self.assertTrue(has_error(self.errors, "observation_ids"))

    def test_unverified_novelty_at_survivor(self):
        self.assertTrue(has_error(self.errors, "unverified"))

    def test_first_mover_edge_rejected(self):
        self.assertTrue(has_error(self.errors, "first-mover"))

    def test_compounding_without_loop_rejected(self):
        self.assertTrue(has_error(self.errors, "accumulation_loop"))

    def test_missing_falsification(self):
        self.assertTrue(has_error(self.errors, "falsification.test"))


class TestLintMissingEvidence(unittest.TestCase):
    def setUp(self):
        self.errors, self.warnings = lint_candidate.lint_candidate(load_fixture("missing_evidence_candidate.json"))

    def test_too_few_observations(self):
        self.assertTrue(has_error(self.errors, "at least 3 required"))

    def test_single_lens_rejected(self):
        self.assertTrue(has_error(self.errors, "lens"))

    def test_no_prior_art_claim_needs_wide_scope(self):
        self.assertTrue(has_error(self.errors, "query families"))


class TestSelfRefutation(unittest.TestCase):
    """Iteration-7: 4 of 19 candidates in the AI-slop run were killed by
    evidence sitting in the observations they themselves cited."""

    def test_missing_self_refutation_fails(self):
        cand = load_fixture("valid_candidate.json")
        cand.pop("self_refutation", None)
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "self_refutation missing"))

    def test_too_short_self_refutation_fails(self):
        cand = load_fixture("valid_candidate.json")
        cand["self_refutation"] = "Re-read them, all fine."
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "self_refutation missing or under"))

    def test_self_refutation_must_name_a_cited_observation(self):
        cand = load_fixture("valid_candidate.json")
        cand["self_refutation"] = (
            "I re-read the evidence base carefully and considered the counter-arguments "
            "in general terms, and nothing in it undercuts the mechanism as written here.")
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "names no observation id"))

    def test_self_refutation_naming_a_foreign_observation_fails(self):
        cand = load_fixture("valid_candidate.json")
        cand["self_refutation"] = (
            "Re-read OBS-not-cited-here-99 and found that its caveat about thin files "
            "materially narrows the population this mechanism can serve at all.")
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "names no observation id"))

    def test_valid_self_refutation_passes(self):
        cand = load_fixture("valid_candidate.json")
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertFalse(has_error(errors, "self_refutation"))


class TestCrossCandidateProbeResponse(unittest.TestCase):
    """Iteration-7: a probe_response written once per probe and pasted onto
    every candidate sharing it passed the per-file lint three times."""

    def _pair(self, actor_a, actor_b, resp_a, resp_b):
        a = load_fixture("valid_candidate.json")
        b = copy.deepcopy(a)
        a["id"], b["id"] = "CAND-01", "CAND-02"
        a["probe_id"] = b["probe_id"] = "PROBE-03"
        a["probe_response"], b["probe_response"] = resp_a, resp_b
        a["descriptor"]["target_actor"] = actor_a
        b["descriptor"]["target_actor"] = actor_b
        return [a, b]

    def test_identical_response_different_actors_fails(self):
        shared = "The probe found the shape contested; this candidate answers the dead precedent."
        errs = lint_candidate.lint_candidate_set(
            self._pair("marketplace operators", "advertising platforms", shared, shared))
        self.assertIn("CAND-01", errs)
        self.assertIn("CAND-02", errs)
        self.assertTrue(any("byte-identical" in e for e in errs["CAND-01"]))

    def test_identical_response_same_actor_is_allowed(self):
        shared = "The probe found the shape contested; this candidate answers the dead precedent."
        errs = lint_candidate.lint_candidate_set(
            self._pair("marketplace operators", "marketplace operators", shared, shared))
        self.assertEqual(errs, {})

    def test_distinct_responses_pass(self):
        errs = lint_candidate.lint_candidate_set(
            self._pair("marketplace operators", "advertising platforms",
                       "Listing permits are posted against the seller's own inventory.",
                       "The publisher is paid back through a per-impression discount."))
        self.assertEqual(errs, {})

    def test_single_candidate_never_flagged(self):
        one = load_fixture("valid_candidate.json")
        one["probe_response"] = "The probe found the shape contested and this is the response."
        self.assertEqual(lint_candidate.lint_candidate_set([one]), {})


class TestPatternSpread(unittest.TestCase):
    """Iteration-8: a wide run put 16 of 19 candidates on one
    opportunity_pattern while the observations were evenly spread."""

    def _set(self, patterns):
        out = []
        for i, p in enumerate(patterns):
            c = load_fixture("valid_candidate.json")
            c["id"] = f"CAND-{i + 1:02d}"
            c["descriptor"]["opportunity_pattern"] = p
            c.pop("probe_response", None)
            c["provocation"] = {"slot": i + 1, "opportunity_pattern": p,
                                "triz_principle": "Feedback",
                                "inversion": "Invert who pays."}
            out.append(c)
        return out

    def test_wide_run_dominated_by_one_pattern_fails(self):
        pats = ["cross-domain-transfer"] * 16 + ["unbundling", "trust-gap", "rebundling"]
        errs = lint_candidate.lint_candidate_set(self._set(pats), breadth="wide")
        self.assertIn("*", errs)
        self.assertTrue(any("premature convergence" in e for e in errs["*"]))

    def test_wide_run_with_too_few_patterns_fails(self):
        pats = (["cross-domain-transfer"] * 4 + ["unbundling"] * 4 +
                ["trust-gap"] * 4 + ["rebundling"] * 4)
        errs = lint_candidate.lint_candidate_set(self._set(pats), breadth="wide")
        self.assertIn("*", errs)
        self.assertTrue(any("distinct opportunity_pattern" in e for e in errs["*"]))

    def test_well_spread_wide_run_passes(self):
        pats = ["cross-domain-transfer", "unbundling", "trust-gap", "rebundling",
                "regulatory-wedge", "workaround-productization", "data-exhaust-capture",
                "workflow-collapse", "incumbent-incentive-gap"]
        errs = lint_candidate.lint_candidate_set(self._set(pats), breadth="wide")
        self.assertNotIn("*", errs)

    def test_focused_run_tolerates_more_concentration(self):
        pats = ["cross-domain-transfer"] * 5 + ["unbundling"] * 3 + ["trust-gap"]
        self.assertNotIn("*", lint_candidate.lint_candidate_set(self._set(pats), breadth="focused"))
        self.assertIn("*", lint_candidate.lint_candidate_set(self._set(pats), breadth="wide"))

    def test_no_breadth_declared_skips_the_check(self):
        pats = ["cross-domain-transfer"] * 16
        self.assertEqual(lint_candidate.lint_candidate_set(self._set(pats)), {})

    def test_small_run_is_not_penalised(self):
        pats = ["cross-domain-transfer"] * 5
        self.assertEqual(lint_candidate.lint_candidate_set(self._set(pats), breadth="wide"), {})

    def test_killed_candidates_do_not_count_toward_spread(self):
        cands = self._set(["cross-domain-transfer"] * 16 + ["unbundling"] * 3)
        for c in cands[:14]:
            c["status"] = "killed"
        # 5 live: 2 cross-domain-transfer + 3 unbundling, under the floor of 8
        self.assertEqual(lint_candidate.lint_candidate_set(cands, breadth="wide"), {})


class TestProvocationRequired(unittest.TestCase):
    """Iteration-9: asking a model for crazier ideas reproduces its prior, so
    wide breadth generates against briefs drawn outside the model."""

    def _cand(self, provocation, status="gated"):
        c = load_fixture("valid_candidate.json")
        c["status"] = status
        c.pop("probe_response", None)
        if provocation is not None:
            c["provocation"] = provocation
        return [c]

    def test_wide_breadth_without_provocation_fails(self):
        errs = lint_candidate.lint_candidate_set(self._cand(None), breadth="wide")
        self.assertTrue(any("no provocation recorded" in e for e in errs.get("CAND-01", [])))

    def test_focused_breadth_does_not_require_provocation(self):
        self.assertEqual(lint_candidate.lint_candidate_set(self._cand(None), breadth="focused"), {})

    def test_killed_candidate_is_exempt(self):
        self.assertEqual(
            lint_candidate.lint_candidate_set(self._cand(None, status="killed"), breadth="wide"), {})

    def test_improvised_triz_principle_fails(self):
        errs = lint_candidate.lint_candidate_set(
            self._cand({"slot": 1, "triz_principle": "Vibes Maximization"}), breadth="wide")
        self.assertTrue(any("not one of the 40 principles" in e for e in errs.get("CAND-01", [])))

    def test_real_triz_principle_passes(self):
        errs = lint_candidate.lint_candidate_set(
            self._cand({"slot": 1, "triz_principle": "Blessing in disguise",
                        "sampled_probability": 0.04}), breadth="wide")
        self.assertEqual(errs, {})

    def test_out_of_range_probability_fails(self):
        errs = lint_candidate.lint_candidate_set(
            self._cand({"slot": 1, "triz_principle": "Feedback", "sampled_probability": 1.7}),
            breadth="wide")
        self.assertTrue(any("outside [0, 1]" in e for e in errs.get("CAND-01", [])))


class TestProvokeScript(unittest.TestCase):
    def test_vocabulary_matches_lint(self):
        self.assertEqual(set(provoke.OPPORTUNITY_PATTERNS), lint_candidate.OPPORTUNITY_PATTERNS)

    def test_forty_principles(self):
        self.assertEqual(len(provoke.TRIZ), 40)
        self.assertEqual(len({n for n, _ in provoke.TRIZ}), 40)

    def test_draw_is_deterministic(self):
        a = provoke.draw("run-x", 8, {})
        b = provoke.draw("run-x", 8, {})
        self.assertEqual(a, b)

    def test_different_runs_draw_differently(self):
        a = [d["triz_principle"] for d in provoke.draw("run-x", 8, {})]
        b = [d["triz_principle"] for d in provoke.draw("run-y", 8, {})]
        self.assertNotEqual(a, b)

    def test_mined_patterns_are_deprioritised(self):
        used = {"cross-domain-transfer": 16}
        drawn = [d["opportunity_pattern"] for d in provoke.draw("run-x", 6, used)]
        self.assertNotIn("cross-domain-transfer", drawn)

    def test_briefs_spread_across_patterns(self):
        drawn = [d["opportunity_pattern"] for d in provoke.draw("run-x", 12, {})]
        self.assertEqual(len(set(drawn)), 12)


class TestIncumbentWeekendBuildEvidence(unittest.TestCase):
    """Iteration-8: back-testing showed this criterion kills companies that
    in fact won against an incumbent shipping the capability bundled free."""

    def _attacked(self, art_state, art_rel):
        c = load_fixture("valid_candidate.json")
        c["status"] = "attacked"
        c["novelty"]["verdict"] = "crowded"
        c["novelty"]["closest_prior_art"] = [{
            "name": "Incumbent Suite", "url": "https://example.com/suite",
            "relationship": art_rel, "state": art_state,
            "difference": "bundles an adjacent capability at zero incremental price"}]
        c["kill_tests"] = [{
            "criterion": "incumbent-weekend-build", "result": "kill",
            "note": "The incumbent could plausibly ship this as a feature given its distribution."}]
        return c

    def test_kill_without_shipping_same_wedge_prior_art_fails(self):
        errors, _ = lint_candidate.lint_candidate(self._attacked("stalled", "adjacent-product"))
        self.assertTrue(has_error(errors, "incumbent that *could* move"))

    def test_kill_with_shipping_incumbent_feature_passes(self):
        errors, _ = lint_candidate.lint_candidate(self._attacked("shipping", "incumbent-feature"))
        self.assertFalse(has_error(errors, "incumbent that *could* move"))

    def test_kill_needs_a_substantive_note(self):
        cand = self._attacked("shipping", "direct-competitor")
        cand["kill_tests"][0]["note"] = "too crowded"
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "no substantive note"))


class TestForbiddenClaims(unittest.TestCase):
    def test_forbidden_claim_anywhere_fails(self):
        cand = load_fixture("valid_candidate.json")
        cand["novelty"]["closest_prior_art"][0]["difference"] = "Ours is first-of-its-kind with no competitors"
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "forbidden novelty claim"))


class _RunDirMixin:
    """Builds a synthetic run directory from the valid fixture."""

    OBS_IDS = ["OBS-capability-shifts-01", "OBS-manual-workflows-01", "OBS-workarounds-02"]

    def make_run(self, root, survivors, max_survivors=3):
        run = Path(root) / "run"
        for sub in ("observations", "candidates", "graveyard", "portfolio"):
            (run / sub).mkdir(parents=True)
        for oid in self.OBS_IDS:
            (run / "observations" / f"{oid}.json").write_text(json.dumps({"id": oid}), encoding="utf-8")
        for cand in survivors:
            (run / "candidates" / f"{cand['id']}.json").write_text(json.dumps(cand), encoding="utf-8")
        portfolio = {
            "run_id": "test-run", "domain": "test", "mode": "quick",
            "max_survivors": max_survivors,
            "survivors": [c["id"] for c in survivors],
            "candidates_considered": max(len(survivors) + 5, 6),
            "graveyard_count": 0,
        }
        (run / "portfolio" / "portfolio.json").write_text(json.dumps(portfolio), encoding="utf-8")
        return run

    def variant(self, cand_id, name, pattern=None, mech_class=None, actor=None):
        cand = load_fixture("valid_candidate.json")
        cand["id"] = cand_id
        cand["name"] = name
        if pattern:
            cand["descriptor"]["opportunity_pattern"] = pattern
        if mech_class:
            cand["descriptor"]["mechanism_class"] = mech_class
        if actor:
            cand["descriptor"]["target_actor"] = actor
        return cand


class TestPortfolioAudit(_RunDirMixin, unittest.TestCase):
    def test_distinct_portfolio_passes(self):
        a = self.variant("CAND-01", "Eval Drift Sentry")
        b = self.variant("CAND-02", "Questionnaire Clause Memory",
                         pattern="workaround-productization", mech_class="translation-bridge",
                         actor="small B2B vendor founders")
        b["one_liner"] = "Matches incoming procurement questionnaire clauses to a vendor's prior answers and flags what changed."
        with tempfile.TemporaryDirectory() as tmp:
            run = self.make_run(tmp, [a, b])
            portfolio, cands, obs, gy, probes = check_portfolio.load_run(run)
            errors, _ = check_portfolio.audit_portfolio(portfolio, cands, obs, gy, probes)
        self.assertEqual(errors, [])

    def test_structural_clones_fail(self):
        a = self.variant("CAND-01", "Eval Drift Sentry")
        b = self.variant("CAND-02", "Model Regression Watchdog")  # same pattern/class/actor
        b["one_liner"] = "Watches hosted model builds and replays regression checks so platform teams catch changes early."
        with tempfile.TemporaryDirectory() as tmp:
            run = self.make_run(tmp, [a, b])
            portfolio, cands, obs, gy, probes = check_portfolio.load_run(run)
            errors, _ = check_portfolio.audit_portfolio(portfolio, cands, obs, gy, probes)
        self.assertTrue(has_error(errors, "same idea wearing different words"))

    def test_more_than_default_ceiling_survivors_fail(self):
        cands = [self.variant(f"CAND-0{i}", f"Idea {i}") for i in range(1, 5)]
        with tempfile.TemporaryDirectory() as tmp:
            run = self.make_run(tmp, cands)  # default max_survivors=3
            portfolio, by_id, obs, gy, probes = check_portfolio.load_run(run)
            errors, _ = check_portfolio.audit_portfolio(portfolio, by_id, obs, gy, probes)
        self.assertTrue(has_error(errors, "declared a ceiling of 3"))

    def test_raised_ceiling_allows_more_survivors(self):
        niches = [
            ("capability-threshold-crossing", "monitoring-alerting", "ML platform teams"),
            ("workaround-productization", "translation-bridge", "small B2B vendor founders"),
            ("trust-gap", "verification-layer", "repo maintainers"),
            ("regulatory-wedge", "compliance-automation", "compliance leads"),
        ]
        cands = [self.variant(f"CAND-0{i}", f"Idea {i}", pattern=p, mech_class=mc, actor=a)
                 for i, (p, mc, a) in enumerate(niches, start=1)]
        for c in cands:
            c["one_liner"] = f"{c['one_liner']} (variant {c['id']})"
        with tempfile.TemporaryDirectory() as tmp:
            run = self.make_run(tmp, cands, max_survivors=5)
            portfolio, by_id, obs, gy, probes = check_portfolio.load_run(run)
            errors, _ = check_portfolio.audit_portfolio(portfolio, by_id, obs, gy, probes)
        self.assertEqual(errors, [])

    def test_ceiling_enforced_even_for_structurally_distinct_candidates(self):
        # 4 distinct-niche candidates would otherwise pass the redundancy
        # audit cleanly — the ceiling check must fire independently of it.
        niches = [
            ("capability-threshold-crossing", "monitoring-alerting", "ML platform teams"),
            ("workaround-productization", "translation-bridge", "small B2B vendor founders"),
            ("trust-gap", "verification-layer", "repo maintainers"),
            ("regulatory-wedge", "compliance-automation", "compliance leads"),
        ]
        cands = [self.variant(f"CAND-0{i}", f"Idea {i}", pattern=p, mech_class=mc, actor=a)
                 for i, (p, mc, a) in enumerate(niches, start=1)]
        for c in cands:
            c["one_liner"] = f"{c['one_liner']} (variant {c['id']})"
        with tempfile.TemporaryDirectory() as tmp:
            run = self.make_run(tmp, cands, max_survivors=3)  # default ceiling, not raised
            portfolio, by_id, obs, gy, probes = check_portfolio.load_run(run)
            errors, _ = check_portfolio.audit_portfolio(portfolio, by_id, obs, gy, probes)
        self.assertTrue(has_error(errors, "declared a ceiling of 3"))
        self.assertFalse(has_error(errors, "same idea wearing different words"))

    def test_max_survivors_field_missing_flagged(self):
        a = self.variant("CAND-01", "Eval Drift Sentry")
        with tempfile.TemporaryDirectory() as tmp:
            run = self.make_run(tmp, [a])
            portfolio = json.loads((run / "portfolio" / "portfolio.json").read_text())
            del portfolio["max_survivors"]
            (run / "portfolio" / "portfolio.json").write_text(json.dumps(portfolio))
            portfolio, by_id, obs, gy, probes = check_portfolio.load_run(run)
            errors, _ = check_portfolio.audit_portfolio(portfolio, by_id, obs, gy, probes)
        self.assertTrue(has_error(errors, "missing required field 'max_survivors'"))

    def test_max_survivors_out_of_range_rejected(self):
        a = self.variant("CAND-01", "Eval Drift Sentry")
        with tempfile.TemporaryDirectory() as tmp:
            run = self.make_run(tmp, [a], max_survivors=9)
            portfolio, by_id, obs, gy, probes = check_portfolio.load_run(run)
            errors, _ = check_portfolio.audit_portfolio(portfolio, by_id, obs, gy, probes)
        self.assertTrue(has_error(errors, "must be an integer from 1 to 6"))

    def test_missing_survivor_file_fails(self):
        a = self.variant("CAND-01", "Eval Drift Sentry")
        with tempfile.TemporaryDirectory() as tmp:
            run = self.make_run(tmp, [a])
            portfolio = json.loads((run / "portfolio" / "portfolio.json").read_text())
            portfolio["survivors"].append("CAND-99")
            (run / "portfolio" / "portfolio.json").write_text(json.dumps(portfolio))
            portfolio, by_id, obs, gy, probes = check_portfolio.load_run(run)
            errors, _ = check_portfolio.audit_portfolio(portfolio, by_id, obs, gy, probes)
        self.assertTrue(has_error(errors, "no candidate file"))

    def test_non_survivor_status_fails(self):
        a = self.variant("CAND-01", "Eval Drift Sentry")
        a["status"] = "attacked"
        with tempfile.TemporaryDirectory() as tmp:
            run = self.make_run(tmp, [a])
            portfolio, by_id, obs, gy, probes = check_portfolio.load_run(run)
            errors, _ = check_portfolio.audit_portfolio(portfolio, by_id, obs, gy, probes)
        self.assertTrue(has_error(errors, "status is 'attacked'"))


class TestInitRun(unittest.TestCase):
    def test_scaffold_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = init_run.init_run("LLM eval tooling", "deep", "saas-subscription", tmp)
            for sub in init_run.SUBDIRS:
                self.assertTrue((run_dir / sub).is_dir(), f"missing {sub}/")
            meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["mode"], "deep")
            self.assertEqual(meta["product_shape"], "saas-subscription")
            self.assertEqual([p["name"] for p in meta["phases"]], init_run.PHASES)
            self.assertTrue((run_dir / "notes" / "PROGRESS.md").exists())

    def test_slug_in_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = init_run.init_run("LLM Eval / Tooling!", "quick", "saas-subscription", tmp)
            self.assertIn("llm-eval-tooling", run_dir.name)

    def test_breadth_and_max_survivors_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = init_run.init_run("Focused idea", "quick", "saas-subscription", tmp)
            meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["breadth"], "focused")
            self.assertEqual(meta["max_survivors"], 3)

    def test_breadth_and_max_survivors_recorded_when_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = init_run.init_run("Wild ideas", "deep", "saas-subscription", tmp,
                                        breadth="wide", max_survivors=5)
            meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["breadth"], "wide")
            self.assertEqual(meta["max_survivors"], 5)
            self.assertIn("Breadth: wide", (run_dir / "notes" / "PROGRESS.md").read_text())


class TestSchemasAndCLI(unittest.TestCase):
    def test_schemas_parse(self):
        for name in ("observation", "candidate", "portfolio"):
            path = SCRIPTS / "schemas" / f"{name}.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("required", schema)

    def test_vocabularies_match_candidate_schema(self):
        schema = json.loads((SCRIPTS / "schemas" / "candidate.schema.json").read_text(encoding="utf-8"))
        props = schema["properties"]
        self.assertEqual(set(props["descriptor"]["properties"]["opportunity_pattern"]["enum"]),
                         lint_candidate.OPPORTUNITY_PATTERNS)
        self.assertEqual(set(props["descriptor"]["properties"]["mechanism_class"]["enum"]),
                         lint_candidate.MECHANISM_CLASSES)
        self.assertEqual(set(props["novelty"]["properties"]["verdict"]["enum"]),
                         lint_candidate.NOVELTY_VERDICTS)
        self.assertEqual(set(props["novelty"]["properties"]["recheck"]["properties"]["outcome"]["enum"]),
                         lint_candidate.RECHECK_OUTCOMES)
        self.assertEqual(set(props["edge"]["properties"]["status"]["enum"]),
                         lint_candidate.EDGE_STATUSES)
        self.assertEqual(set(props["status"]["enum"]), lint_candidate.STATUSES)
        self.assertEqual(set(props["product_shape"]["enum"]), lint_candidate.PRODUCT_SHAPES)

    def test_product_shape_vocab_matches_init_run(self):
        self.assertEqual(set(init_run.PRODUCT_SHAPES), lint_candidate.PRODUCT_SHAPES)

    def test_observation_loading_recurses_subdirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            lens_dir = Path(tmp) / "workarounds"
            lens_dir.mkdir()
            (lens_dir / "OBS-workarounds-01.json").write_text(json.dumps({"id": "OBS-workarounds-01"}))
            (Path(tmp) / "OBS-capability-shifts-01.json").write_text(json.dumps({"id": "OBS-capability-shifts-01"}))
            ids = lint_candidate.load_observation_ids(tmp)
        self.assertEqual(ids, {"OBS-workarounds-01", "OBS-capability-shifts-01"})

    def test_lint_cli_exit_codes(self):
        self.assertEqual(lint_candidate.main([str(FIXTURES / "valid_candidate.json")]), 0)
        self.assertEqual(lint_candidate.main([str(FIXTURES / "slop_candidate.json")]), 1)

    def test_lint_cli_require_shape(self):
        valid = str(FIXTURES / "valid_candidate.json")
        self.assertEqual(lint_candidate.main([valid, "--require-shape", "saas-subscription"]), 0)
        self.assertEqual(lint_candidate.main([valid, "--require-shape", "marketplace"]), 1)


if __name__ == "__main__":
    unittest.main()
