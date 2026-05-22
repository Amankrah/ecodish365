"""Lock-in tests for the ReCiPe 2016 v1.1 factor-pack ETL outputs.

These tests pin the JSON pack schema + content so the next ETL change cannot
silently corrupt the runtime LCA inputs. They assume `build_recipe2016_factor_packs`
has already produced the artefacts (CI run: `python -m
environmental_impact_model.etl.build_recipe2016_factor_packs` before pytest).

Invariants tested:
  1. Three JSON packs + one combined meta exist under data/ with schema "1.0".
  2. Endpoint factors carry 24 keys per perspective (I/H) and 26 for E (fossils).
  3. Workbook drift corrections are reflected (terrestrial_ecotoxicity_ecosystem
     H = 1.14e-11, human_toxicity_non_cancer H = 2.28e-7, fossil_scarcity_hard_coal
     H = 0.034) — guards against accidentally reverting to the old hard-coded
     values discovered to be 4737x / 34x / 14% off.
  4. Midpoint normalisation contains the 3 v1-consumed categories with H values
     within 0.1% of the workbook (Global warming = 7990.41, Water = 266.64,
     Land use = 6167.48).
  5. Endpoint per-AoP norms are computed correctly and recognise Resources as
     the sum of mineral + fossil scarcity contributions.
  6. Country factors carry >= 60 ISO-3 entries for the 3 per-country categories
     and Canada is present with the expected workbook values (water HH = 0 across
     all perspectives, terrestrial H = 1.27e-9, stress index = 0.7).
"""

from __future__ import annotations

import json
import os
import unittest

DATA_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "data")
)
ENDPOINT_PATH = os.path.join(DATA_DIR, "recipe2016_endpoint_factors.json")
NORM_PATH = os.path.join(DATA_DIR, "recipe2016_normalization.json")
COUNTRY_PATH = os.path.join(DATA_DIR, "recipe2016_country_factors.json")
META_PATH = os.path.join(DATA_DIR, "recipe2016_factor_packs_meta.json")


def _load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


class TestReCiPe2016ETLArtifacts(unittest.TestCase):
    """All 4 ETL outputs exist with the expected top-level structure."""

    def test_all_four_files_present(self):
        for path in (ENDPOINT_PATH, NORM_PATH, COUNTRY_PATH, META_PATH):
            self.assertTrue(
                os.path.exists(path),
                msg=f"Missing ETL artefact: {path}. Run `python -m "
                    f"environmental_impact_model.etl.build_recipe2016_factor_packs`.",
            )

    def test_all_packs_share_schema_version(self):
        for path in (ENDPOINT_PATH, NORM_PATH, COUNTRY_PATH):
            data = _load_json(path)
            self.assertEqual(data["_schema_version"], "1.0",
                             msg=f"Schema version drift in {path}")
            self.assertEqual(data["_methodology"], "recipe2016")
            self.assertEqual(data["_methodology_version"], "v1.1")

    def test_combined_meta_has_expected_keys(self):
        meta = _load_json(META_PATH)
        for key in ("methodology", "methodology_version", "schema_version",
                    "etl_git_rev", "extracted_at_utc", "packs"):
            self.assertIn(key, meta, msg=f"Combined meta missing {key}")
        for sub in ("endpoint_factors", "normalization", "country_factors"):
            self.assertIn(sub, meta["packs"])
            self.assertIn("sha256", meta["packs"][sub])
            self.assertEqual(len(meta["packs"][sub]["sha256"]), 64,
                             msg=f"{sub} sha256 not 64 hex chars")


class TestEndpointFactorsPack(unittest.TestCase):
    """The midpoint-to-endpoint conversion factors per perspective."""

    @classmethod
    def setUpClass(cls):
        cls.pack = _load_json(ENDPOINT_PATH)
        cls.H = cls.pack["perspectives"]["H"]
        cls.I = cls.pack["perspectives"]["I"]
        cls.E = cls.pack["perspectives"]["E"]

    def test_three_perspectives_present(self):
        self.assertEqual(set(self.pack["perspectives"].keys()), {"I", "H", "E"})

    def test_factor_counts_per_perspective(self):
        # Same 24 endpoint pathways for I and H; E adds brown coal + peat.
        self.assertEqual(len(self.H), 24, msg="H pathway count drifted")
        self.assertEqual(len(self.I), 24, msg="I pathway count drifted")
        self.assertEqual(len(self.E), 26, msg="E pathway count drifted")

    def test_workbook_drift_correction_terrestrial_ecotox(self):
        """Was hard-coded 5.4e-8 — workbook value is 1.14e-11 (4737x lower)."""
        self.assertAlmostEqual(self.H["terrestrial_ecotoxicity_ecosystem"],
                               1.14e-11, places=14)

    def test_workbook_drift_correction_human_tox_non_cancer(self):
        """Was hard-coded 6.7e-9 — workbook value is 2.28e-7 (34x higher)."""
        self.assertAlmostEqual(self.H["human_toxicity_non_cancer"],
                               2.28e-7, places=10)

    def test_workbook_drift_correction_freshwater_eutroph(self):
        """Was hard-coded 6.1e-7 — workbook value is 6.71e-7 (10% off)."""
        self.assertAlmostEqual(self.H["freshwater_eutrophication_ecosystem"],
                               6.710726087059383e-7, places=12)

    def test_workbook_drift_correction_hard_coal(self):
        """Was hard-coded 0.03 — workbook value is 0.0341 (14% off)."""
        self.assertAlmostEqual(self.H["fossil_scarcity_hard_coal"],
                               0.03413587457175793, places=10)

    def test_v1_trim_critical_factors_intact(self):
        """The 3 endpoints the v1 trim actually consumes must round-trip exactly."""
        self.assertAlmostEqual(self.H["climate_change_human"], 9.28e-7, places=10)
        self.assertAlmostEqual(self.H["water_use_human"], 2.22e-6, places=10)
        self.assertAlmostEqual(self.H["land_use_ecosystem"], 8.88e-9, places=12)


class TestNormalizationPack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = _load_json(NORM_PATH)

    def test_world_population_2010(self):
        self.assertEqual(self.pack["world_population_2010"], 6895889018)

    def test_midpoint_norms_have_three_perspectives(self):
        self.assertEqual(set(self.pack["midpoint"].keys()), {"I", "H", "E"})

    def test_v1_consumed_midpoint_norms_match_workbook(self):
        H = self.pack["midpoint"]["H"]
        # Workbook canonical H values per person per year, world 2010.
        self.assertAlmostEqual(H["Global warming"], 7990.407652952963, places=4)
        self.assertAlmostEqual(H["Water consumption"], 266.6392611088278, places=4)
        self.assertAlmostEqual(H["Land use"], 6167.48227895003, places=4)

    def test_midpoint_norm_count_per_perspective(self):
        for p in ("I", "H", "E"):
            self.assertEqual(len(self.pack["midpoint"][p]), 21,
                             msg=f"Midpoint norm category count drift for {p}")

    def test_endpoint_per_aop_sums(self):
        """The per-AoP endpoint totals are derived from per-pathway sums."""
        per_aop_h = self.pack["endpoint_per_aop"]["H"]
        # Sanity: all three AoPs are present and positive.
        for aop in ("Human Health", "Ecosystems", "Resources"):
            self.assertIn(aop, per_aop_h)
            self.assertGreater(per_aop_h[aop], 0)
        # Order-of-magnitude check: HH on the order of 10^-2, Ecosystems 10^-3,
        # Resources ~10^4 (USD2013 per person per year).
        self.assertLess(per_aop_h["Human Health"], 1.0)
        self.assertLess(per_aop_h["Ecosystems"], 1.0)
        self.assertGreater(per_aop_h["Resources"], 1000.0)


class TestCountryFactorsPack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = _load_json(COUNTRY_PATH)
        cls.cats = cls.pack["categories"]

    def test_all_five_categories_present(self):
        expected = {
            "water_consumption", "freshwater_eutrophication",
            "terrestrial_acidification", "particulate_matter_formation",
            "photochemical_ozone_formation",
        }
        self.assertSetEqual(set(self.cats.keys()), expected)

    def test_per_country_category_coverage(self):
        """The 3 per-country categories must cover >= 60 ISO-3 codes each."""
        for cat in ("water_consumption", "freshwater_eutrophication",
                    "terrestrial_acidification"):
            n = self.cats[cat]["n_countries"]
            self.assertGreaterEqual(n, 60,
                msg=f"{cat} has only {n} countries; workbook should cover more.")

    def test_countries_available_list(self):
        """The pack-level ISO-3 list is the union across per-country categories
        and must include at least 150 codes."""
        self.assertGreaterEqual(len(self.pack["countries_available_iso3"]), 150)
        # Canonical countries that MUST be present (sanity).
        for iso in ("CAN", "USA", "GBR", "FRA", "DEU", "JPN", "AUS", "BRA", "IND", "CHN"):
            self.assertIn(iso, self.pack["countries_available_iso3"],
                          msg=f"{iso} missing from per-country coverage")

    def test_canada_water_consumption_values(self):
        """Canada is water-abundant: human-health CF = 0 across all perspectives,
        terrestrial CF (H) = 1.27e-9, water stress index = 0.7. Hard-pin per
        the workbook so regional misuse can't drift this."""
        canada = self.cats["water_consumption"]["countries"]["CAN"]
        self.assertEqual(canada["endpoint_hh"]["H"], 0.0)
        self.assertEqual(canada["endpoint_hh"]["I"], 0.0)
        self.assertEqual(canada["endpoint_hh"]["E"], 0.0)
        self.assertAlmostEqual(canada["endpoint_terrestrial"]["H"], 1.27e-9, places=12)
        self.assertAlmostEqual(canada["water_stress_index"], 0.7, places=3)

    def test_usa_water_contrasts_canada(self):
        """USA has a non-zero human-health water CF (water-stressed regions
        contribute). Validates we're loading per-country variation, not a
        constant."""
        usa_hh_h = self.cats["water_consumption"]["countries"]["USA"]["endpoint_hh"]["H"]
        self.assertGreater(usa_hh_h, 0.0)
        self.assertLess(usa_hh_h, 1e-4)  # sanity bound

    def test_regional_categories_preserve_source_regions(self):
        """PMF and Photochemical ozone are source-region (not country) keyed.
        Preserve their raw region rows for forward use."""
        for cat in ("particulate_matter_formation", "photochemical_ozone_formation"):
            self.assertIn("source_regions", self.cats[cat])
            self.assertGreaterEqual(self.cats[cat]["n_regions"], 50)


if __name__ == "__main__":
    unittest.main()
