"""Tier β lock-in tests for state canonicalisation + subgroup routing.

Pins:
  - `_canonicalize_food_state` strips well-known state modifiers from CNF
    descriptions and returns them as a separate state_tag, leaving the
    base name with higher overlap with Agribalyse entries.
  - `_agribalyse_subgroup_for_cnf` maps composite-y CNF FoodGroupNames
    (Babyfoods, Soups, Mixed Dishes, Fast Foods) to the Agribalyse top-level
    group used by retrieval pre-filtering.
  - `EmbeddingRetriever.retrieve(..., agribalyse_group_filter=X)` masks
    out non-matching candidates while remaining safe (falls back to full
    catalogue if filter would starve the ranker).

This is the offline test surface. Embedding-quality regression (the
"median Jaccard >= 0.30" target in the Tier β plan) is exercised by
`backend/_smoke_matcher_coverage.py` separately.
"""
from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

_BACKEND = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
for sub in ("environmental_impact_model", "dish_cnf_db_pipeline"):
    p = os.path.join(_BACKEND, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dish_project.settings")
import django  # noqa: E402
from django.apps import apps as _django_apps  # noqa: E402
if not _django_apps.ready:
    django.setup()

from environmental_impact_model.src.lca_matcher import (  # noqa: E402
    _canonicalize_food_state,
    _agribalyse_subgroup_for_cnf,
    EmbeddingRetriever,
    AgribalyseIndex,
)


class StateCanonicalisationTests(unittest.TestCase):
    """`_canonicalize_food_state` splits state modifiers from the base name."""

    def test_frozen_unprepared(self):
        base, state = _canonicalize_food_state("Squash, summer, crookneck, frozen, unprepared")
        self.assertEqual(base, "Squash summer crookneck")
        self.assertIn("frozen", state)
        self.assertIn("unprepared", state)

    def test_pan_fried_state_extracted(self):
        base, state = _canonicalize_food_state("Beef, brain, pan-fried")
        self.assertEqual(base, "Beef brain")
        self.assertEqual(state, "pan-fried")

    def test_canned_condensed(self):
        base, state = _canonicalize_food_state("Soup, chicken gumbo, canned, condensed, water added")
        # Note: "water added" not a known state token, stays in base.
        self.assertIn("Soup", base)
        self.assertIn("chicken gumbo", base)
        self.assertIn("canned", state)
        self.assertIn("condensed", state)

    def test_no_state_modifier_returns_empty_state(self):
        base, state = _canonicalize_food_state("Apple")
        self.assertEqual(base, "Apple")
        self.assertEqual(state, "")

    def test_empty_description_safe(self):
        base, state = _canonicalize_food_state("")
        self.assertEqual(base, "")
        self.assertEqual(state, "")

    def test_partly_skimmed_milk(self):
        """Multi-word state token ('partly skimmed') is recognised as a unit."""
        base, state = _canonicalize_food_state("Milk, fluid, partly skimmed, 2% M.F.")
        self.assertIn("Milk", base)
        self.assertIn("partly skimmed", state)


class SubgroupRoutingTests(unittest.TestCase):
    """`_agribalyse_subgroup_for_cnf` maps composite-y CNF groups to their
    natural Agribalyse cohort."""

    def test_babyfoods_routes_to_aliments_infantiles(self):
        self.assertEqual(
            _agribalyse_subgroup_for_cnf('Babyfoods'),
            'aliments infantiles',
        )

    def test_soups_routes_to_entrees_et_plats_composes(self):
        self.assertEqual(
            _agribalyse_subgroup_for_cnf('Soups, Sauces and Gravies'),
            'entrées et plats composés',
        )

    def test_fast_foods_routes_to_entrees_et_plats_composes(self):
        self.assertEqual(
            _agribalyse_subgroup_for_cnf('Fast Foods'),
            'entrées et plats composés',
        )

    def test_mixed_dishes_routes_to_entrees_et_plats_composes(self):
        self.assertEqual(
            _agribalyse_subgroup_for_cnf('Mixed Dishes'),
            'entrées et plats composés',
        )

    def test_unrouted_group_returns_none(self):
        # Cereals span multiple Agribalyse subgroups → intentionally un-routed
        self.assertIsNone(_agribalyse_subgroup_for_cnf('Cereals, Grains and Pasta'))
        # Beef Products: clean per-row matches available; no routing needed.
        self.assertIsNone(_agribalyse_subgroup_for_cnf('Beef Products'))

    def test_none_input_safe(self):
        self.assertIsNone(_agribalyse_subgroup_for_cnf(None))


class RetrievalSubgroupFilterTests(unittest.TestCase):
    """`EmbeddingRetriever.retrieve(agribalyse_group_filter=X)` masks non-X
    candidates when at least k matches remain, falls back to full catalogue
    otherwise to avoid starving the LLM ranker."""

    def setUp(self):
        # Stub a 4-entry catalog: 2 in babyfoods, 2 in viandes
        self.index = MagicMock(spec=AgribalyseIndex)
        self.index.catalog = [
            {'ciqual_code': '1', 'lci_name': 'Apple sauce baby', 'agribalyse_group': 'aliments infantiles'},
            {'ciqual_code': '2', 'lci_name': 'Carrot puree baby', 'agribalyse_group': 'aliments infantiles'},
            {'ciqual_code': '3', 'lci_name': 'Beef steak',        'agribalyse_group': 'viandes, œufs, poissons'},
            {'ciqual_code': '4', 'lci_name': 'Pork chop',         'agribalyse_group': 'viandes, œufs, poissons'},
        ]
        self.index.__len__ = lambda s: 4
        self.index.ensure_embeddings.return_value = None
        # Stub embeddings: each entry has a unique 4-dim vector pointing in
        # +x direction with different magnitudes (so cosine sims rank stably).
        import numpy as np
        self.index.embeddings = np.eye(4, dtype=np.float32) + 0.1
        # Stub embedding_client.embeddings.create — return a vector matching entry 2
        # (Carrot puree baby) most strongly.
        client = MagicMock()
        rsp = MagicMock()
        emb = MagicMock(); emb.embedding = [0.0, 1.0, 0.0, 0.0]
        rsp.data = [emb]
        client.embeddings.create.return_value = rsp
        self.index.embedding_client = client
        self.retriever = EmbeddingRetriever(self.index)

    def test_filter_restricts_to_named_subgroup(self):
        results = self.retriever.retrieve(
            "carrot baby food", k=2,
            agribalyse_group_filter='aliments infantiles',
        )
        codes = [c['ciqual_code'] for c, _ in results]
        # Only babyfoods entries (ciqual 1 and 2) should appear.
        self.assertSetEqual(set(codes), {'1', '2'})

    def test_filter_fallback_when_too_few_candidates(self):
        """If the filter would leave < k candidates, retrieval should fall
        back to full catalogue to avoid starving the LLM ranker."""
        # Filter to a non-existent group → 0 matches, k=2 requested
        # → fallback to full catalogue (all 4 entries available).
        results = self.retriever.retrieve(
            "anything", k=2,
            agribalyse_group_filter='zoological catalogue not in v32',
        )
        self.assertEqual(len(results), 2)
        # All catalog entries (not just one group) are eligible.

    def test_no_filter_returns_unfiltered_topk(self):
        results = self.retriever.retrieve("anything", k=2, agribalyse_group_filter=None)
        self.assertEqual(len(results), 2)


if __name__ == '__main__':
    unittest.main()
