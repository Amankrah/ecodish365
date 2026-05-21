"""Pin the EF 3.1 → ReCiPe 2016 H mapping table (AGRIBALYSE-INGEST).

Invariants verified:
  1. Every key in EF_TO_RECIPE_DIRECT is one of the 16 EF columns AND
     resolves to a real ReCiPe key in cnf_integrator group-default returns
     OR is one of the three parallel climate sub-columns.
  2. The EF_TO_RECIPE_DIRECT keys ∪ EF_INCOMPATIBLE_WITH_RECIPE ∪
     {EF_SINGLE_SCORE_COLUMN} exactly partitions the set of known EF columns.
  3. The mapping version is set.
"""

from __future__ import annotations

import unittest

from environmental_impact_model.etl.ef_to_recipe_mapping import (
    EF_INCOMPATIBLE_WITH_RECIPE,
    EF_SINGLE_SCORE_COLUMN,
    EF_TO_RECIPE_DIRECT,
    MAPPING_VERSION,
    all_ef_columns,
)


# Expected EF column-header titles from the Synthese tab of the Tableur
# Aout25 workbook (sharedStrings.xml [30]-[49]). Pinning this prevents
# silent drift if the mapping module is edited without updating tests.
EXPECTED_EF_COLUMN_HEADERS = frozenset({
    "Score unique EF 3.1",
    "Changement climatique",
    "Appauvrissement de la couche d'ozone",
    "Rayonnements ionisants",
    "Formation photochimique d'ozone",
    "Particules fines",
    "Effets toxicologiques sur la santé humaine : substances non-cancérogènes",
    "Effets toxicologiques sur la santé humaine : substances cancérogènes",
    "Acidification terrestre et eaux douces",
    "Eutrophisation eaux douces",
    "Eutrophisation marine",
    "Eutrophisation terrestre",
    "Écotoxicité pour écosystèmes aquatiques d'eau douce",
    "Utilisation du sol",
    "Épuisement des ressources eau",
    "Épuisement des ressources énergétiques",
    "Épuisement des ressources minéraux",
    "Changement climatique - émissions biogéniques",
    "Changement climatique - émissions fossiles",
    "Changement climatique - émissions liées au changement d'affectation des sols",
})


# Standard ReCiPe 2016 H midpoint keys produced by cnf_integrator
# group-default returns. Used to validate that the right-hand side of
# EF_TO_RECIPE_DIRECT maps to real consumed keys (or to one of the new
# parallel climate sub-keys that the matcher injects).
EXPECTED_RECIPE_MIDPOINT_KEYS = frozenset({
    "Global warming",
    "Stratospheric ozone depletion",
    "Ionizing radiation",
    "Ozone formation, Human health",
    "Fine particulate matter formation",
    "Ozone formation, Terrestrial ecosystems",
    "Terrestrial acidification",
    "Freshwater eutrophication",
    "Marine eutrophication",
    "Terrestrial ecotoxicity",
    "Freshwater ecotoxicity",
    "Marine ecotoxicity",
    "Human carcinogenic toxicity",
    "Human non-carcinogenic toxicity",
    "Land use",
    "Mineral resource scarcity",
    "Fossil resource scarcity",
    "Water consumption",
})


PARALLEL_CLIMATE_SUBKEYS = frozenset({
    "Global warming (fossil)",
    "Global warming (biogenic)",
    "Global warming (LUC)",
})


class EfToRecipeMappingTests(unittest.TestCase):
    def test_partition_exhaustive_over_known_ef_columns(self):
        """The mapping + incompatible-set + single-score column must partition
        the full set of 20 known EF columns published in Synthese."""
        partition = set(EF_TO_RECIPE_DIRECT) | EF_INCOMPATIBLE_WITH_RECIPE | {EF_SINGLE_SCORE_COLUMN}
        self.assertSetEqual(partition, EXPECTED_EF_COLUMN_HEADERS,
                            "EF→ReCiPe mapping partition must cover exactly the published EF columns")
        # Mapped + incompatible + single must be mutually disjoint.
        self.assertEqual(len(EF_TO_RECIPE_DIRECT) + len(EF_INCOMPATIBLE_WITH_RECIPE) + 1,
                         len(partition),
                         "mapped, incompatible, and single-score buckets must be disjoint")

    def test_direct_mapping_values_resolve_to_recipe_or_climate_subkeys(self):
        """Every value of EF_TO_RECIPE_DIRECT must be a real ReCiPe midpoint
        key (consumed by the pipeline aggregation loop) OR one of the parallel
        climate sub-keys (surfaced but not aggregated)."""
        allowed = EXPECTED_RECIPE_MIDPOINT_KEYS | PARALLEL_CLIMATE_SUBKEYS
        for ef_key, recipe_key in EF_TO_RECIPE_DIRECT.items():
            with self.subTest(ef=ef_key):
                self.assertIn(recipe_key, allowed,
                              f"{recipe_key!r} from EF {ef_key!r} not in ReCiPe + parallel-climate set")

    def test_direct_mapping_keys_are_known_ef_columns(self):
        for ef_key in EF_TO_RECIPE_DIRECT:
            self.assertIn(ef_key, EXPECTED_EF_COLUMN_HEADERS)

    def test_incompatible_set_is_disjoint_from_direct_map(self):
        self.assertSetEqual(
            EF_INCOMPATIBLE_WITH_RECIPE & set(EF_TO_RECIPE_DIRECT),
            set(),
        )

    def test_all_ef_columns_helper_matches_pinned_set(self):
        self.assertSetEqual(set(all_ef_columns()), EXPECTED_EF_COLUMN_HEADERS)

    def test_climate_change_maps_to_global_warming(self):
        """The single most-relied-upon mapping: EF Changement climatique ≡
        ReCiPe Global warming (both IPCC AR5 GWP100, kg CO2 eq)."""
        self.assertEqual(EF_TO_RECIPE_DIRECT["Changement climatique"], "Global warming")

    def test_mapping_version_is_set(self):
        self.assertIsInstance(MAPPING_VERSION, str)
        self.assertGreater(len(MAPPING_VERSION), 3)


if __name__ == "__main__":
    unittest.main()
