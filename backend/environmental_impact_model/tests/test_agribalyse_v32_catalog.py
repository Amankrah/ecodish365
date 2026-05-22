"""Tests for the v32 Agribalyse catalog (AGRIBALYSE-INGEST).

Verifies the deterministically-generated catalog conforms to the dual-namespace
schema and that the matcher + LCA pipeline integrations behave correctly:
  - catalog loads with provenance fields
  - every row has Global warming OR a documented warning
  - errata-flagged Ciqual codes are surfaced
  - MatchResult.to_audit() carries ef31_indicators + catalog_version
  - LifeCycleAssessment suppresses Canadian regional scaling on matched rows
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock

import numpy as np

from environmental_impact_model.src.lca_matcher import (
    DEFAULT_BOOTSTRAP_CATALOG_PATH,
    DEFAULT_META_PATH,
    AgribalyseIndex,
    EmbeddingRetriever,
    LCAMatcher,
)


def _has_v32_catalog() -> bool:
    return os.path.exists(DEFAULT_BOOTSTRAP_CATALOG_PATH) and os.path.exists(DEFAULT_META_PATH)


@unittest.skipUnless(_has_v32_catalog(), "v32 catalog not generated; run the ETL first")
class V32CatalogTests(unittest.TestCase):
    """Pin the v32 catalog file's structure and provenance."""

    @classmethod
    def setUpClass(cls):
        with open(DEFAULT_BOOTSTRAP_CATALOG_PATH, "r", encoding="utf-8") as fh:
            cls.payload = json.load(fh)
        with open(DEFAULT_META_PATH, "r", encoding="utf-8") as fh:
            cls.meta = json.load(fh)

    def test_payload_schema_version(self):
        self.assertEqual(self.payload.get("_schema_version"), "2.0")
        self.assertIn("entries", self.payload)
        self.assertGreater(len(self.payload["entries"]), 2000)
        self.assertLess(len(self.payload["entries"]), 3000)

    def test_meta_provenance_fields(self):
        for key in ("source_file", "source_file_sha256", "source_sheet",
                    "etl_git_rev", "mapping_version", "total_rows",
                    "rows_with_warnings", "duplicate_ciquals_dedup_kept_last",
                    "ademe_errata_ciqual_codes_flagged"):
            self.assertIn(key, self.meta, f"meta missing {key!r}")
        # SHA-256 is 64 hex chars.
        self.assertRegex(self.meta["source_file_sha256"], r"^[0-9a-f]{64}$")
        # Mapping version is set.
        self.assertTrue(self.meta["mapping_version"].startswith("v"))
        # total_rows in meta matches catalog length.
        self.assertEqual(self.meta["total_rows"], len(self.payload["entries"]))

    def test_every_row_has_climate_or_warning(self):
        """Per the plan: every row must have a Global warming midpoint
        value OR carry a documented warning that explains why it doesn't."""
        for entry in self.payload["entries"]:
            recipe = entry.get("recipe2016_midpoints_per_100g", {})
            warnings = entry.get("warnings", [])
            if "Global warming" not in recipe:
                self.assertIn("missing_climate_change_value", warnings,
                              f"CIQUAL {entry['ciqual_code']} missing climate w/o warning")

    def test_every_row_has_dual_namespace(self):
        """v32 rows carry BOTH `recipe2016_midpoints_per_100g` (subset) AND
        `ef31_indicators_per_100g` (full EF set), plus unit_metadata."""
        for entry in self.payload["entries"]:
            self.assertIn("recipe2016_midpoints_per_100g", entry)
            self.assertIn("ef31_indicators_per_100g", entry)
            self.assertIn("unit_metadata", entry)
            self.assertIsInstance(entry["recipe2016_midpoints_per_100g"], dict)
            self.assertIsInstance(entry["ef31_indicators_per_100g"], dict)

    def test_ciqual_codes_are_strings(self):
        for entry in self.payload["entries"]:
            self.assertIsInstance(entry["ciqual_code"], str)
            self.assertTrue(entry["ciqual_code"])  # non-empty

    def test_entries_sorted_by_ciqual_code(self):
        codes = [e["ciqual_code"] for e in self.payload["entries"]]
        self.assertEqual(codes, sorted(codes), "entries must be sorted by ciqual_code for deterministic output")

    def test_per_100g_conversion_applied(self):
        """Spot-check that values are per-100g (not per-kg). Climate change
        on a typical animal product should be in the 0.04–10 kg CO2/100g
        range — per-kg would be 0.4–100."""
        for entry in self.payload["entries"]:
            gw = entry.get("recipe2016_midpoints_per_100g", {}).get("Global warming")
            if gw is None:
                continue
            self.assertLess(abs(gw), 25.0,
                            f"CIQUAL {entry['ciqual_code']} Global warming {gw} "
                            "looks like per-kg, not per-100g")


@unittest.skipUnless(_has_v32_catalog(), "v32 catalog not generated; run the ETL first")
class V32IndexAndMatcherTests(unittest.TestCase):
    """End-to-end: load the v32 catalog through AgribalyseIndex + match it via LCAMatcher."""

    def setUp(self):
        # Use a fresh embeddings cache per test so we don't pollute the real
        # v32 npy file.
        self.tmpdir = tempfile.TemporaryDirectory()
        self.embeddings_path = os.path.join(self.tmpdir.name, "emb.npy")

    def tearDown(self):
        self.tmpdir.cleanup()

    def _make_mock_embedder(self):
        client = MagicMock()
        # Deterministic 64-dim embeddings based on ciqual_code hash so the
        # retrieval works for any query (the test only checks structure, not
        # semantic accuracy — that's covered by integration tests with the
        # real API).
        rng = np.random.default_rng(seed=42)

        def _embed(*, model, input):  # noqa: A002
            vectors = []
            for text in input:
                # Deterministic per-text vector.
                h = abs(hash(text)) % (2**31)
                rng_local = np.random.default_rng(seed=h)
                v = rng_local.standard_normal(64).astype(np.float32)
                vectors.append(v.tolist())
            return MagicMock(data=[MagicMock(embedding=v) for v in vectors])

        client.embeddings.create.side_effect = _embed
        return client

    def test_index_loads_v32_with_meta(self):
        client = self._make_mock_embedder()
        index = AgribalyseIndex(
            catalog_path=DEFAULT_BOOTSTRAP_CATALOG_PATH,
            embeddings_cache_path=self.embeddings_path,
            embedding_client=client,
        )
        self.assertGreater(len(index), 2000)
        self.assertTrue(index.catalog_version.startswith("agribalyse_v32:"))

    def test_matcher_to_audit_carries_ef31_and_catalog_version(self):
        embed_client = self._make_mock_embedder()
        index = AgribalyseIndex(
            catalog_path=DEFAULT_BOOTSTRAP_CATALOG_PATH,
            embeddings_cache_path=self.embeddings_path,
            embedding_client=embed_client,
        )
        retriever = EmbeddingRetriever(index, embedding_client=embed_client)

        # Mock the LLM ranking to pick the first retrieved candidate with
        # high confidence — without inspecting which Ciqual code that is.
        ranking_client = MagicMock()

        def _rank(*args, **kwargs):
            # Read the candidate list out of the prompt and pick the first.
            prompt = kwargs.get("messages", [{}, {}])[1].get("content", "")
            for line in prompt.splitlines():
                line = line.strip()
                if line and line[0].isdigit() and ":" in line:
                    code = line.split(":", 1)[0].strip()
                    payload = json.dumps({"ciqual_code": code, "confidence": 0.9,
                                          "justification": "ok"})
                    msg = MagicMock(content=payload)
                    return MagicMock(choices=[MagicMock(message=msg)])
            return MagicMock(choices=[MagicMock(message=MagicMock(
                content='{"ciqual_code":"","confidence":0.0,"justification":"none"}'))])
        ranking_client.chat.completions.create.side_effect = _rank

        matcher = LCAMatcher(
            index=index, retriever=retriever, ranking_client=ranking_client,
            confidence_threshold=0.6, top_k=5,
        )
        result = matcher.match(food_id=2003, food_description="Atlantic salmon raw farmed")
        self.assertTrue(result.matched, f"expected matched=True, got {result.to_audit()}")
        audit = result.to_audit()
        self.assertIn("ef31_indicators", audit)
        self.assertIn("unit_metadata", audit)
        self.assertIn("catalog_version", audit)
        self.assertTrue(audit["catalog_version"].startswith("agribalyse_v32:"))
        self.assertIn("dqr", audit)
        self.assertIn("warnings", audit)


@unittest.skipUnless(_has_v32_catalog(), "v32 catalog not generated; run the ETL first")
class MatcherOverlayAuditTrailTests(unittest.TestCase):
    """The unsourced Canadian midpoint multipliers were retired when the
    methodology pack landed (per the ReCiPe2016 integration plan). What
    remains is the matched-vs-group-default merge logic + per-food audit
    trail, which these tests pin in place. Country-aware adaptation now
    lives at the endpoint conversion step (`life_cycle_assessment._ef`)
    and is exercised in test_lca_default_behavior_parity.py."""

    def test_matched_overlay_replaces_group_default_for_overlapping_key(self):
        from unittest.mock import patch
        from environmental_impact_model.src.life_cycle_assessment import LifeCycleAssessment

        food_a = MagicMock()
        food_a.food_id = 1
        food_a.food_name = "matched food"
        food_a.food_group = "Beef Products"
        food_a.quantity = 100.0

        meal = MagicMock()
        meal.foods = [food_a]
        meal.calculate_total_calories.return_value = 200.0

        match = MagicMock()
        match.matched = True
        match.midpoint_factors = {"Global warming": 5.0}  # per 100 g
        match.ef31_indicators = {"Changement climatique": 5.0}
        match.unit_metadata = {"Changement climatique": "kg CO2 eq/kg de produit"}
        match.dqr = 2.4
        match.warnings = []
        match.ciqual_code = "21510"
        match.confidence = 0.85
        match.to_audit = lambda: {
            "food_id": 1, "matched": True, "ciqual_code": "21510",
            "lci_name": "beef", "confidence": 0.85, "justification": "x",
            "fallback_reason": None, "n_candidates_considered": 1,
            "dqr": 2.4, "warnings": [], "catalog_version": "agribalyse_v32:test",
            "ef31_indicators": {"Changement climatique": 5.0},
            "unit_metadata": {"Changement climatique": "kg CO2 eq/kg"},
        }
        matcher = MagicMock()
        matcher.match.return_value = match

        # Stub group-default factors with one overlapping key (Global warming
        # — matched overlay wins) and one non-overlapping key (Land use —
        # group default flows through).
        stub_group_defaults = {"Global warming": 1.0, "Land use": 4.0}

        lca = LifeCycleAssessment(meal, matcher=matcher)
        with patch.object(lca.cnf_integrator, "get_environmental_impact_factors",
                          return_value=stub_group_defaults):
            midpoints = lca.perform_lcia()

        # Global warming: matched value 5.0/100g × 100g = 5.0 raw × functional
        # unit (100/200=0.5) = 2.5. No regional multipliers anywhere now.
        self.assertAlmostEqual(midpoints["Global warming"], 2.5, places=4,
                               msg="matched value should drive Global warming")

        # Land use: group-default 4.0/100g × 100g = 4.0 raw × functional unit
        # (0.5) = 2.0. The retired Canadian 0.78× multiplier no longer applies.
        self.assertAlmostEqual(midpoints["Land use"], 2.0, places=4,
                               msg="group-default category receives no midpoint multiplier")

        # Audit trail records per-(food, category) accounting.
        self.assertEqual(len(lca.matcher_decisions), 1)
        dec = lca.matcher_decisions[0]
        # Regional scaling at midpoint is retired — flag is permanently False.
        self.assertFalse(dec["regional_scaling_applied"])
        self.assertEqual(dec["categories_from_match"], 1)  # Global warming only
        self.assertGreater(dec["categories_from_group_default"], 0)  # Land use etc.

    def test_unmatched_food_uses_only_group_defaults(self):
        from environmental_impact_model.src.life_cycle_assessment import LifeCycleAssessment

        food_a = MagicMock()
        food_a.food_id = 2
        food_a.food_name = "unmatched food"
        food_a.food_group = "Vegetables and Vegetable Products"
        food_a.quantity = 100.0

        meal = MagicMock()
        meal.foods = [food_a]
        meal.calculate_total_calories.return_value = 200.0

        # No matcher: existing group-default path; midpoints flow through
        # without any regional scaling. Smoke check only.
        lca_no_matcher = LifeCycleAssessment(meal, matcher=None)
        midpoints = lca_no_matcher.perform_lcia()
        self.assertIsInstance(midpoints, dict)
        self.assertEqual(lca_no_matcher.matcher_decisions, [])


if __name__ == "__main__":
    unittest.main()
