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

    def test_survivor_crowded_requires_real_edge(self):
        cand = copy.deepcopy(self.cand)
        cand["novelty"]["verdict"] = "crowded"
        cand["edge"] = {"status": "none"}
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "crowded"))

    def test_survivor_duplicated_cannot_survive(self):
        cand = copy.deepcopy(self.cand)
        cand["novelty"]["verdict"] = "duplicated"
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "duplicate cannot survive"))

    def test_unjustified_kill_override_fails_survivor(self):
        cand = copy.deepcopy(self.cand)
        cand["kill_tests"][0] = {"criterion": "incumbent-weekend-build", "result": "kill", "note": ""}
        errors, _ = lint_candidate.lint_candidate(cand)
        self.assertTrue(has_error(errors, "un-overridden kill result"))

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

    def make_run(self, root, survivors):
        run = Path(root) / "run"
        for sub in ("observations", "candidates", "graveyard", "portfolio"):
            (run / sub).mkdir(parents=True)
        for oid in self.OBS_IDS:
            (run / "observations" / f"{oid}.json").write_text(json.dumps({"id": oid}), encoding="utf-8")
        for cand in survivors:
            (run / "candidates" / f"{cand['id']}.json").write_text(json.dumps(cand), encoding="utf-8")
        portfolio = {
            "run_id": "test-run", "domain": "test", "mode": "quick",
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
            portfolio, cands, obs, gy = check_portfolio.load_run(run)
            errors, _ = check_portfolio.audit_portfolio(portfolio, cands, obs, gy)
        self.assertEqual(errors, [])

    def test_structural_clones_fail(self):
        a = self.variant("CAND-01", "Eval Drift Sentry")
        b = self.variant("CAND-02", "Model Regression Watchdog")  # same pattern/class/actor
        b["one_liner"] = "Watches hosted model builds and replays regression checks so platform teams catch changes early."
        with tempfile.TemporaryDirectory() as tmp:
            run = self.make_run(tmp, [a, b])
            portfolio, cands, obs, gy = check_portfolio.load_run(run)
            errors, _ = check_portfolio.audit_portfolio(portfolio, cands, obs, gy)
        self.assertTrue(has_error(errors, "same idea wearing different words"))

    def test_more_than_three_survivors_fail(self):
        cands = [self.variant(f"CAND-0{i}", f"Idea {i}") for i in range(1, 5)]
        with tempfile.TemporaryDirectory() as tmp:
            run = self.make_run(tmp, cands)
            portfolio, by_id, obs, gy = check_portfolio.load_run(run)
            errors, _ = check_portfolio.audit_portfolio(portfolio, by_id, obs, gy)
        self.assertTrue(has_error(errors, "at most 3"))

    def test_missing_survivor_file_fails(self):
        a = self.variant("CAND-01", "Eval Drift Sentry")
        with tempfile.TemporaryDirectory() as tmp:
            run = self.make_run(tmp, [a])
            portfolio = json.loads((run / "portfolio" / "portfolio.json").read_text())
            portfolio["survivors"].append("CAND-99")
            (run / "portfolio" / "portfolio.json").write_text(json.dumps(portfolio))
            portfolio, by_id, obs, gy = check_portfolio.load_run(run)
            errors, _ = check_portfolio.audit_portfolio(portfolio, by_id, obs, gy)
        self.assertTrue(has_error(errors, "no candidate file"))

    def test_non_survivor_status_fails(self):
        a = self.variant("CAND-01", "Eval Drift Sentry")
        a["status"] = "attacked"
        with tempfile.TemporaryDirectory() as tmp:
            run = self.make_run(tmp, [a])
            portfolio, by_id, obs, gy = check_portfolio.load_run(run)
            errors, _ = check_portfolio.audit_portfolio(portfolio, by_id, obs, gy)
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
