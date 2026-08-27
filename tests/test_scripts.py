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
