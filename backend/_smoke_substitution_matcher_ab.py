#!/usr/bin/env python
"""A/B test for CNFMatcher retrieval_only=True (substitution discovery path).

For every unique ingredient appearing in the user-supplied saved-days export,
compares two matcher modes back-to-back:

  - full       : matcher.match(q, top_k=10)                (embed + LLM rank)
  - retrieval  : matcher.match(q, top_k=10, retrieval_only=True)  (embed only)

Reports per-ingredient timing delta and whether the alternatives food_id list
(what substitution_discovery._matcher_alternative_candidates actually consumes)
diverges between the two paths.
"""
from __future__ import annotations

import os
import sys
import time

import django

import dish_project.env_bootstrap  # noqa: F401  — load .env

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
django.setup()

from api.services.cnf_matcher import get_default_matcher  # noqa: E402

# Unique ingredient descriptions from both days in the export.
QUERIES = [
    'Egg, chicken, whole, cooked, scrambled or omelet',
    'Butter, regular',
    'Milk, fluid, partly skimmed, 2% M.F.',
    'Orange juice, chilled, includes from concentrate',
    'Grains, rice, white, long-grain, parboiled, cooked',
    'Chicken, broiler, thigh, meat and skin, roasted',
    'Yogourt (yogurt), Balkan style, 4-6% M.F., plain',
    'Onion, yellow, sauteed',
    'Butter, Clarified butter (ghee)',
    'Tomato, red, ripe, raw, year round average',
    'Garlic, raw',
    'Ginger root, raw',
    'Cereal, hot, oats (oatmeal), large flakes, prepared, Quaker',
    'Banana, raw',
    'Mango, nectar, canned',
    'Yogourt (yogurt), 2-3.9% M.F., plain',
    'Cassava, tuber, white flesh, boiled* (without salt), drained',
    'Plantain, yellow cooked',
    'Water, municipal',
    'Peanut butter, smooth type, fat, sugar and salt added',
    'Chicken, stewing, meat and skin, stewed',
    'Onion, raw',
    'Vegetable oil, palm',
]

# substitution_discovery filters alternatives below this cosine before
# emitting candidates — apply the same gate here so the comparison
# reflects what discovery actually sees.
MIN_MATCHER_COSINE = 0.65
ALT_LIMIT = 3  # default discovery limit (max(2, max_per_ingredient // 2))


def _clear_result_cache(matcher) -> None:
    with matcher._cache_lock:  # noqa: SLF001
        matcher._cache.clear()  # noqa: SLF001
        matcher._cache_order.clear()  # noqa: SLF001


def _alt_ids_discovery_filtered(result) -> list[int]:
    """Same gate as substitution_discovery._matcher_alternative_candidates."""
    out: list[int] = []
    seen: set[int] = set()
    if result.matched and result.food_id and result.food_id not in seen:
        seen.add(result.food_id)
    for alt in result.alternatives:
        if alt.food_id in seen:
            continue
        if alt.similarity < MIN_MATCHER_COSINE:
            continue
        seen.add(alt.food_id)
        out.append(alt.food_id)
        if len(out) >= ALT_LIMIT:
            break
    return out


def main() -> int:
    matcher = get_default_matcher()
    print(f'Matcher: chat_client={matcher.chat_json_client.__class__.__name__ if matcher.chat_json_client else None} '
          f'model={matcher.model} corpus_rows={len(matcher.corpus.food_ids)}')
    print()
    header = f'{"#":>2} {"full ms":>8} {"retr ms":>8} {"speedup":>8}  {"alt-set":>10}  query'
    print(header)
    print('-' * len(header))

    rows = []
    for i, q in enumerate(QUERIES, 1):
        # Warm the embedding so timing reflects marginal LLM-rank cost only.
        # (In production, after process warmup, repeated identical ingredient
        # queries get embedding-cache hits — this matches that steady state.)
        _ = matcher.match(q, top_k=10, retrieval_only=True)
        _clear_result_cache(matcher)

        # Full mode (embed cached, LLM rank cold).
        t0 = time.perf_counter()
        full = matcher.match(q, top_k=10)
        full_ms = (time.perf_counter() - t0) * 1000
        _clear_result_cache(matcher)

        # Retrieval-only mode (embed cached, no LLM call).
        t0 = time.perf_counter()
        retr = matcher.match(q, top_k=10, retrieval_only=True)
        retr_ms = (time.perf_counter() - t0) * 1000

        full_ids = _alt_ids_discovery_filtered(full)
        retr_ids = _alt_ids_discovery_filtered(retr)
        set_match = '=' if set(full_ids) == set(retr_ids) else 'DIFF'
        order_match = 'order=' if full_ids == retr_ids else 'order!='
        speedup = (full_ms / retr_ms) if retr_ms > 0 else float('inf')

        print(f'{i:>2} {full_ms:>8.1f} {retr_ms:>8.1f} {speedup:>7.1f}x  '
              f'{set_match:>4} {order_match:>6}  {q[:60]}')
        rows.append({
            'q': q, 'full_ms': full_ms, 'retr_ms': retr_ms,
            'full_ids': full_ids, 'retr_ids': retr_ids,
            'full_used_ai': full.used_ai_ranking,
            'full_matched': full.matched,
        })

    print()
    total_full = sum(r['full_ms'] for r in rows)
    total_retr = sum(r['retr_ms'] for r in rows)
    set_eq = sum(1 for r in rows if set(r['full_ids']) == set(r['retr_ids']))
    order_eq = sum(1 for r in rows if r['full_ids'] == r['retr_ids'])
    print(f'Aggregate over {len(rows)} ingredients:')
    print(f'  full        total = {total_full:>8.1f} ms   avg = {total_full/len(rows):>6.1f} ms')
    print(f'  retrieval   total = {total_retr:>8.1f} ms   avg = {total_retr/len(rows):>6.1f} ms')
    print(f'  speedup     {total_full/total_retr:>5.1f}x  '
          f'(saved {total_full - total_retr:.0f} ms per analyze request)')
    print(f'  alt-set identical (food_id set):    {set_eq}/{len(rows)}')
    print(f'  alt-set identical (order matters):  {order_eq}/{len(rows)}')

    # Spotlight any ingredients where the discovery-consumed set diverged.
    diffs = [r for r in rows if set(r['full_ids']) != set(r['retr_ids'])]
    if diffs:
        print()
        print('Set divergences (discovery would see different candidates):')
        for r in diffs:
            print(f'  {r["q"][:60]}')
            print(f'    full: {r["full_ids"]}')
            print(f'    retr: {r["retr_ids"]}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
