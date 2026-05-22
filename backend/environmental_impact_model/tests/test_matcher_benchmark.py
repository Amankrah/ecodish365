"""Shape-pinning tests for the matcher benchmark JSON artefact.

Asserts the structure of `matcher_benchmark_<rev>_<utc>.json` so a future
refactor that breaks the schema is caught. Does NOT pin numerical accuracy
values — those drift with LLM behaviour by design.

When NO benchmark file exists, the tests are skipped (the benchmark requires
an OpenAI key and a network call; we don't gate CI on it).
"""
from __future__ import annotations

import glob
import json
import math
import os
import unittest

_BACKEND = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
_DATA_DIR = os.path.join(_BACKEND, 'environmental_impact_model', 'data')


def _latest_benchmark_path() -> str | None:
    """Return the most-recent benchmark JSON, or None if none exist."""
    paths = sorted(glob.glob(os.path.join(_DATA_DIR, 'matcher_benchmark_*.json')))
    return paths[-1] if paths else None


_BENCH_PATH = _latest_benchmark_path()


@unittest.skipUnless(_BENCH_PATH is not None,
                     'No matcher_benchmark_*.json artefact found; run _smoke_matcher_benchmark.py first')
class MatcherBenchmarkShapeTests(unittest.TestCase):
    """The artefact's structure (schema, summary keys, per-food fields)."""

    @classmethod
    def setUpClass(cls):
        with open(_BENCH_PATH, 'r', encoding='utf-8') as fh:
            cls.b = json.load(fh)

    def test_top_level_schema(self):
        b = self.b
        self.assertEqual(b['_schema_version'], '1.0')
        for key in ('generated_at_utc', 'git_rev', 'matcher_pack_version',
                    'sample_size', 'seed', 'summary', 'per_food'):
            self.assertIn(key, b, msg=f'top-level key missing: {key}')

    def test_summary_keys(self):
        s = self.b['summary']
        for key in ('overall', 'by_group', 'by_confidence_band',
                    'total_cost_usd', 'median_latency_seconds', 'mean_latency_seconds'):
            self.assertIn(key, s, msg=f'summary key missing: {key}')

    def test_overall_counts_sum_to_sample_size(self):
        o = self.b['summary']['overall']
        for key in ('clean', 'borderline', 'flagged', 'total'):
            self.assertIn(key, o)
        self.assertEqual(o['clean'] + o['borderline'] + o['flagged'], o['total'])
        self.assertEqual(o['total'], self.b['sample_size'])

    def test_by_group_counts_sum_to_sample_size(self):
        by_group = self.b['summary']['by_group']
        total = sum(g['n'] for g in by_group.values())
        self.assertEqual(total, self.b['sample_size'])
        for g, b in by_group.items():
            self.assertEqual(b['clean'] + b['borderline'] + b['flagged'], b['n'],
                             msg=f'group {g} counts do not sum')

    def test_by_confidence_band_counts_sum_to_sample_size(self):
        by_band = self.b['summary']['by_confidence_band']
        total = sum(b['n'] for b in by_band.values())
        self.assertEqual(total, self.b['sample_size'])
        for band, b in by_band.items():
            self.assertEqual(b['clean'] + b['borderline'] + b['flagged'], b['n'],
                             msg=f'band {band} counts do not sum')
            self.assertIn('flagged_rate', b)
            self.assertTrue(0.0 <= b['flagged_rate'] <= 1.0)

    def test_cost_and_latency_are_finite(self):
        s = self.b['summary']
        self.assertTrue(math.isfinite(s['total_cost_usd']))
        self.assertTrue(math.isfinite(s['median_latency_seconds']))
        self.assertGreater(s['total_cost_usd'], 0)

    def test_every_per_food_row_has_required_fields(self):
        required = {
            'food_id', 'cnf_name', 'cnf_group', 'matched', 'ciqual_code',
            'lci_name', 'matched_agribalyse_group', 'confidence', 'justification',
            'group_consistency_pass', 'magnitude_pass', 'token_overlap_pass',
            'automated_verdict', 'reviewer_verdict', 'reviewer_notes',
            'matched_gw_per_100g', 'cnf_group_default_gw_per_100g',
            'magnitude_ratio', 'latency_seconds',
        }
        for r in self.b['per_food']:
            self.assertTrue(required.issubset(r.keys()),
                            msg=f'food_id={r.get("food_id")} missing fields: {required - set(r.keys())}')

    def test_per_food_verdicts_are_in_expected_set(self):
        valid = {'clean', 'borderline', 'flagged'}
        for r in self.b['per_food']:
            self.assertIn(r['automated_verdict'], valid)

    def test_confidence_in_unit_interval(self):
        for r in self.b['per_food']:
            self.assertTrue(0.0 <= r['confidence'] <= 1.0,
                            msg=f'food_id={r["food_id"]} confidence={r["confidence"]} out of [0,1]')

    def test_sample_size_matches_per_food_length(self):
        self.assertEqual(self.b['sample_size'], len(self.b['per_food']))


if __name__ == '__main__':
    unittest.main()
