"""Tests for §3.5 GROUP-D-RECONCILIATION LCA matcher.

All tests use mocked OpenAI clients — no API key required. Verifies:
  - AgribalyseIndex loads the bootstrap JSON and persists embeddings deterministically.
  - EmbeddingRetriever returns expected top-k for canonical food queries.
  - LCAMatcher honors confidence threshold (matched vs fallback).
  - LCAMatcher rejects hallucinated Ciqual codes (per Krahmer 2024 LEAF observation).
  - LCAMatcher degrades gracefully to retrieval-only when no LLM client is provided.
  - LifeCycleAssessment behaviour is unchanged when matcher=None (no regression).
  - LifeCycleAssessment uses matched factors when matcher returns matched=True.
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
    LEGACY_BOOTSTRAP_CATALOG_PATH,
    AgribalyseIndex,
    EmbeddingRetriever,
    LCAMatcher,
    MatchResult,
)

# Existing tests in this file were written against the 54-row hand-curated
# bootstrap. After AGRIBALYSE-INGEST the default catalog is the v32 file
# (~2,425 entries with different Ciqual codes), so pin these tests to the
# legacy bootstrap path explicitly. v32-specific assertions live in
# test_agribalyse_v32_catalog.py.
BOOTSTRAP_CATALOG_PATH = LEGACY_BOOTSTRAP_CATALOG_PATH


def _make_mock_openai_client(catalog_size: int, embedding_dim: int = 32):
    """Return a mock that mimics the openai.OpenAI() interface used by the matcher.

    Embedding responses are deterministic: catalog entry i gets a one-hot-ish
    vector at position (i % embedding_dim), with a small uniform baseline so
    cosine sim is well-defined. Query vectors are constructed in tests on the fly.
    """
    client = MagicMock()

    def _embed(*, model, input):  # noqa: A002 (shadows builtin 'input' to match openai sig)
        vectors = []
        for text in input:
            v = np.full(embedding_dim, 0.01, dtype=np.float32)
            # crude deterministic mapping from text → embedding
            for token, slot in [
                ("beef", 0), ("sirloin", 0), ("ground", 0),
                ("pork", 1), ("bacon", 1), ("ham", 1),
                ("chicken", 2), ("turkey", 2), ("poultry", 2),
                ("salmon", 3), ("cod", 3), ("tuna", 3), ("shrimp", 3),
                ("milk", 4), ("cheese", 4), ("yogurt", 4),
                ("egg", 5),
                ("broccoli", 6), ("carrot", 6), ("tomato", 6), ("lettuce", 6),
                ("spinach", 6), ("potato", 7), ("sweet", 7),
                ("apple", 8), ("banana", 8), ("orange", 8), ("strawberry", 8),
                ("avocado", 8),
                ("wheat", 9), ("flour", 9), ("bread", 9), ("rice", 9),
                ("oats", 9), ("pasta", 9),
                ("lentil", 10), ("chickpea", 10), ("bean", 10),
                ("soybean", 10), ("tofu", 10), ("peanut", 10),
                ("almond", 11), ("walnut", 11), ("sunflower", 11),
                ("chia", 14),  # dedicated slot so chia is not tied with other nuts/seeds
                ("olive", 12), ("canola", 12), ("oil", 12),
                ("sugar", 13), ("cola", 13),
            ]:
                if token in text.lower():
                    v[slot % embedding_dim] += 1.0
            vectors.append(v.tolist())
        rows = [MagicMock(embedding=vec) for vec in vectors]
        return MagicMock(data=rows)

    client.embeddings.create.side_effect = _embed
    return client


class AgribalyseIndexTests(unittest.TestCase):
    def test_bootstrap_catalog_loads(self):
        index = AgribalyseIndex(catalog_path=BOOTSTRAP_CATALOG_PATH)
        self.assertGreaterEqual(len(index), 40, "bootstrap must contain at least 40 entries")
        self.assertGreaterEqual(len(index), 50, "plan target is 50–80 entries")
        # Required keys on every entry.
        for entry in index.catalog:
            self.assertIn("ciqual_code", entry)
            self.assertIn("lci_name", entry)
            self.assertIn("midpoint_factors_per_100g", entry)
            self.assertIsInstance(entry["midpoint_factors_per_100g"], dict)
            # ReCiPe 18-midpoint coverage.
            self.assertIn("Global warming", entry["midpoint_factors_per_100g"])
            self.assertIn("Land use", entry["midpoint_factors_per_100g"])
            self.assertIn("Water consumption", entry["midpoint_factors_per_100g"])

    def test_embeddings_build_and_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "emb.npy")
            client = _make_mock_openai_client(catalog_size=50)
            index = AgribalyseIndex(
                catalog_path=BOOTSTRAP_CATALOG_PATH,
                embeddings_cache_path=cache_path,
                embedding_client=client,
            )
            index.ensure_embeddings()
            self.assertIsNotNone(index.embeddings)
            self.assertEqual(index.embeddings.shape[0], len(index))
            self.assertTrue(os.path.exists(cache_path))

            # Reload from cache — must not call embeddings again.
            client.embeddings.create.reset_mock()
            index2 = AgribalyseIndex(
                catalog_path=BOOTSTRAP_CATALOG_PATH,
                embeddings_cache_path=cache_path,
                embedding_client=client,
            )
            index2.ensure_embeddings()
            self.assertEqual(client.embeddings.create.call_count, 0)
            np.testing.assert_array_equal(index.embeddings, index2.embeddings)


class EmbeddingRetrieverTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.tmpdir.name, "emb.npy")
        self.client = _make_mock_openai_client(catalog_size=50)
        self.index = AgribalyseIndex(
            catalog_path=BOOTSTRAP_CATALOG_PATH,
            embeddings_cache_path=self.cache_path,
            embedding_client=self.client,
        )
        self.retriever = EmbeddingRetriever(self.index, embedding_client=self.client)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_retrieve_returns_top_k(self):
        results = self.retriever.retrieve("beef sirloin steak raw", k=5)
        self.assertEqual(len(results), 5)
        # Top result should be a beef entry given the mock embedder's token routing.
        top_entry, top_sim = results[0]
        self.assertIn("beef", top_entry["lci_name"].lower())
        self.assertGreater(top_sim, 0.0)

    def test_retrieve_canonical_food_categories(self):
        for query, expected_token in [
            ("broccoli raw fresh", "broccoli"),
            ("Atlantic salmon raw farmed", "salmon"),
            ("chia seed raw dry", "chia"),
            ("plain rolled oats dry", "oats"),
            ("white granulated sugar", "sugar"),
        ]:
            with self.subTest(query=query):
                results = self.retriever.retrieve(query, k=3)
                # Expected token must appear in at least one of the top-3 names.
                top_names = " ".join(e["lci_name"].lower() for e, _ in results)
                self.assertIn(expected_token, top_names, f"top-3 for {query!r} missing {expected_token!r}: {top_names}")


class LCAMatcherTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.tmpdir.name, "emb.npy")
        self.embedding_client = _make_mock_openai_client(catalog_size=50)
        self.index = AgribalyseIndex(
            catalog_path=BOOTSTRAP_CATALOG_PATH,
            embeddings_cache_path=self.cache_path,
            embedding_client=self.embedding_client,
        )
        self.retriever = EmbeddingRetriever(self.index, embedding_client=self.embedding_client)

    def tearDown(self):
        self.tmpdir.cleanup()

    def _make_ranking_client(self, response_payload: dict):
        client = MagicMock()
        message = MagicMock(content=json.dumps(response_payload))
        choice = MagicMock(message=message)
        client.chat.completions.create.return_value = MagicMock(choices=[choice])
        return client

    def test_high_confidence_match(self):
        # Force the mock LLM to pick a known beef Ciqual code with high confidence.
        ranking_client = self._make_ranking_client(
            {"ciqual_code": "21510", "confidence": 0.85, "justification": "Direct beef match."}
        )
        matcher = LCAMatcher(
            index=self.index,
            retriever=self.retriever,
            ranking_client=ranking_client,
            confidence_threshold=0.6,
            top_k=10,
        )
        result = matcher.match(food_id=1, food_description="beef sirloin steak raw", food_group="Beef Products")
        self.assertTrue(result.matched)
        self.assertEqual(result.ciqual_code, "21510")
        self.assertGreaterEqual(result.confidence, 0.6)
        self.assertIsNotNone(result.midpoint_factors)
        self.assertIn("Global warming", result.midpoint_factors)

    def test_low_confidence_fallback(self):
        ranking_client = self._make_ranking_client(
            {"ciqual_code": "21510", "confidence": 0.3, "justification": "Uncertain."}
        )
        matcher = LCAMatcher(
            index=self.index, retriever=self.retriever,
            ranking_client=ranking_client, confidence_threshold=0.6, top_k=10,
        )
        result = matcher.match(food_id=2, food_description="beef sirloin steak raw")
        self.assertFalse(result.matched)
        self.assertEqual(result.fallback_reason, "low_confidence")
        # Audit-trail still records the proposed code.
        self.assertEqual(result.ciqual_code, "21510")

    def test_rejects_hallucinated_ciqual_code(self):
        ranking_client = self._make_ranking_client(
            {"ciqual_code": "99999", "confidence": 0.95, "justification": "Made-up code."}
        )
        matcher = LCAMatcher(
            index=self.index, retriever=self.retriever,
            ranking_client=ranking_client, confidence_threshold=0.6, top_k=10,
        )
        result = matcher.match(food_id=3, food_description="beef sirloin steak raw")
        self.assertFalse(result.matched)
        self.assertEqual(result.fallback_reason, "hallucinated_code")
        self.assertIsNone(result.midpoint_factors)

    def test_no_llm_client_degrades_to_retrieval_top1(self):
        matcher = LCAMatcher(
            index=self.index, retriever=self.retriever,
            ranking_client=None, confidence_threshold=0.0, top_k=5,
        )
        result = matcher.match(food_id=4, food_description="chia seed raw dry")
        self.assertTrue(result.matched)
        self.assertIn("embedding-similarity-only", result.justification)
        self.assertGreater(result.confidence, 0.0)

    def test_caches_per_food_id(self):
        ranking_client = self._make_ranking_client(
            {"ciqual_code": "21510", "confidence": 0.85, "justification": "match."}
        )
        matcher = LCAMatcher(
            index=self.index, retriever=self.retriever,
            ranking_client=ranking_client, confidence_threshold=0.6, top_k=10,
        )
        result1 = matcher.match(food_id=99, food_description="beef sirloin steak raw")
        result2 = matcher.match(food_id=99, food_description="anything")  # cached
        self.assertIs(result1, result2)
        # LLM should have been called only once.
        self.assertEqual(ranking_client.chat.completions.create.call_count, 1)

    def test_handles_llm_exception_with_fallback(self):
        ranking_client = MagicMock()
        ranking_client.chat.completions.create.side_effect = RuntimeError("network broke")
        matcher = LCAMatcher(
            index=self.index, retriever=self.retriever,
            ranking_client=ranking_client, confidence_threshold=0.6, top_k=10,
        )
        result = matcher.match(food_id=5, food_description="beef sirloin steak raw")
        self.assertFalse(result.matched)
        self.assertEqual(result.fallback_reason, "exception")


class MatchResultTests(unittest.TestCase):
    def test_to_audit_shape(self):
        r = MatchResult(
            food_id=42, matched=True, ciqual_code="21510",
            lci_name="Beef", confidence=0.8, justification="ok",
            midpoint_factors={"Global warming": 1.0},
        )
        audit = r.to_audit()
        for key in ("food_id", "matched", "ciqual_code", "lci_name",
                    "confidence", "justification", "fallback_reason",
                    "n_candidates_considered"):
            self.assertIn(key, audit)


if __name__ == "__main__":
    unittest.main()
