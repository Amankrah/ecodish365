"""Calibration probe — does the configured LLM provider/model actually vary
its self-reported confidence with composite difficulty?

Empirically (2026-05-22) gpt-4o-mini anchored decomposition_confidence at
0.40 on 7/8 probes regardless of difficulty — a hard model-default bias
that made the original 0.60 confidence gate unreachable. After the move to
gpt-4.1-mini (or claude-haiku-4-5 via LLM_PROVIDER=anthropic), we want to
verify whether the new model actually calibrates: harder composites should
report lower confidence than trivial ones.

Probe panel: 8 CNF composites spanning the difficulty spectrum from
trivial (lasagna — a near-direct Agribalyse match) to hard (tourtière —
French-Canadian, only loosely represented in v32's French-curated
catalogue). Each composite is run through the decomposer with the
production system prompt; the self-reported `decomposition_confidence`
is collected.

Acceptance signals for a well-calibrated provider:
  - ≥ 4 distinct confidence values across the 8 probes (was 1 on gpt-4o-mini)
  - Std dev ≥ 0.10 across the panel
  - Trivial composites (lasagna, mac and cheese) > median
  - Hard composites (tourtière, bannock) < median

Run from `backend/`:
  python _smoke_confidence_probe.py                          # uses LLM_PROVIDER env (default openai)
  LLM_PROVIDER=anthropic python _smoke_confidence_probe.py   # exercises the anthropic path

Output: stdout summary + JSON artefact to
  environmental_impact_model/data/confidence_probe_<provider>_<model>_<utc>.json
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone

_BACKEND = os.path.dirname(os.path.abspath(__file__))
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    p = os.path.join(_BACKEND, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_BACKEND, '.env'))
except Exception:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()


# Probe panel: 8 composites ordered approximately by expected difficulty.
# `difficulty_score` is a hand-labelled prior (0 = trivial direct match,
# 1 = hard / no canonical recipe in v32). Used for rank-correlation.
PROBES = [
    # (food_id, label, qty_g, hand-labelled difficulty 0..1)
    (502049, 'Lasagna with meat and tomato sauce',           250, 0.10),
    (6730, 'Macaroni and cheese, prepared',                250, 0.20),
    (6754, 'Chicken noodle soup, canned, prepared',        250, 0.30),
    (6772, 'Poutine',                                      250, 0.55),
    (6773, "Shepherd's pie with corn",                     250, 0.60),
    (4082,   'Bannock',                                      100, 0.75),
    (6621, 'Butter tart, with raisins, homemade',           50, 0.80),
    (6883, 'Tourtiere, homemade',                          150, 0.85),
]


def _resolve_provider_info():
    """Return (provider, model) from env / ChatJSONClient defaults."""
    from environmental_impact_model.src.llm_client import (
        _PROVIDER_DEFAULT_MODELS, build_chat_json_client,
    )
    provider = (os.environ.get('LLM_PROVIDER') or 'openai').lower()
    client = build_chat_json_client()
    model = getattr(client, 'model', None) or _PROVIDER_DEFAULT_MODELS.get(provider, '?')
    return provider, model, client


def main():
    provider, model, chat_client = _resolve_provider_info()
    if chat_client is None:
        print(f'No API key available for LLM_PROVIDER={provider}; aborting.')
        return 1
    print('=' * 78)
    print(f'Confidence calibration probe — provider={provider}  model={model}')
    print(f'Panel: {len(PROBES)} composites (difficulty {PROBES[0][3]:.2f} -> {PROBES[-1][3]:.2f})')
    print('=' * 78)

    # Build the decomposer directly so we get raw confidence values without
    # going through the API view's mass-aggregation layer.
    from environmental_impact_model.src.lca_matcher import (
        AgribalyseIndex, EmbeddingRetriever, build_default_matcher,
    )
    from environmental_impact_model.src.recipe_decomposer import RecipeDecomposer

    matcher = build_default_matcher()
    if matcher is None:
        print('Could not construct LCAMatcher (missing OPENAI_API_KEY for embeddings).')
        return 1
    decomposer = RecipeDecomposer(
        index=matcher.index,
        retriever=matcher.retriever,
        chat_json_client=chat_client,
    )

    per_probe = []
    t_start = time.time()
    for fid, label, qty, difficulty in PROBES:
        t = time.time()
        result = decomposer.decompose(
            food_id=fid, food_description=label, food_quantity_g=qty,
            food_group='Mixed Dishes',  # composite-group route
        )
        elapsed = time.time() - t
        conf = result.decomposition_confidence if result else 0.0
        n_ing = result.ingredient_count if result else 0
        resolved = bool(result and result.matched)
        per_probe.append({
            'food_id': fid, 'label': label, 'quantity_g': qty,
            'hand_difficulty': difficulty,
            'decomposition_confidence': conf,
            'ingredient_count': n_ing,
            'resolved': resolved,
            'fallback_reason': result.fallback_reason if result else 'no_result',
            'latency_seconds': round(elapsed, 2),
        })
        print(f'  [{difficulty:.2f}] {label[:48]:<48} conf={conf:.3f}  '
              f'ing={n_ing}  resolved={resolved}  ({elapsed:.1f}s)')

    total_elapsed = time.time() - t_start
    confs = [p['decomposition_confidence'] for p in per_probe]
    distinct = sorted({round(c, 3) for c in confs})
    mean = statistics.mean(confs) if confs else 0.0
    median = statistics.median(confs) if confs else 0.0
    stdev = statistics.stdev(confs) if len(confs) > 1 else 0.0

    # Rank correlation between hand-labelled difficulty and reported
    # confidence (Spearman-ish — we use 1 - (n_inversions/max_inversions)).
    # Negative correlation expected: harder → lower confidence.
    diffs = [p['hand_difficulty'] for p in per_probe]
    rank_corr = _spearman(diffs, confs)

    # Tally trivial vs hard against the median.
    trivial = [p for p in per_probe if p['hand_difficulty'] <= 0.30]
    hard = [p for p in per_probe if p['hand_difficulty'] >= 0.70]
    trivial_above_median = sum(1 for p in trivial if p['decomposition_confidence'] > median)
    hard_below_median = sum(1 for p in hard if p['decomposition_confidence'] < median)

    summary = {
        'provider': provider,
        'model': model,
        'sample_size': len(PROBES),
        'distinct_confidence_values': len(distinct),
        'confidence_values_sorted': distinct,
        'mean': round(mean, 3),
        'median': round(median, 3),
        'stdev': round(stdev, 3),
        'spearman_rho_difficulty_vs_conf': round(rank_corr, 3),
        'trivial_above_median_count': trivial_above_median,
        'hard_below_median_count': hard_below_median,
        'total_elapsed_seconds': round(total_elapsed, 1),
    }

    # Acceptance signals
    acceptance = {
        'distinct_ge_4': len(distinct) >= 4,
        'stdev_ge_0_10': stdev >= 0.10,
        'spearman_negative': rank_corr < 0,  # harder → lower confidence
    }

    print()
    print('=' * 78)
    print('SUMMARY')
    print('=' * 78)
    for k, v in summary.items():
        print(f'  {k}: {v}')
    print()
    print('Acceptance signals (well-calibrated provider):')
    for k, v in acceptance.items():
        flag = 'PASS' if v else 'FAIL'
        print(f'  [{flag}] {k}')

    # Persist artefact.
    data_dir = os.path.join(_BACKEND, 'environmental_impact_model', 'data')
    os.makedirs(data_dir, exist_ok=True)
    utc = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    safe_model = model.replace('/', '_').replace(':', '_')
    out_path = os.path.join(data_dir, f'confidence_probe_{provider}_{safe_model}_{utc}.json')
    payload = {
        '_schema_version': '1.0',
        'generated_at_utc': utc,
        'summary': summary,
        'acceptance': acceptance,
        'per_probe': per_probe,
    }
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)
    print(f'\nArtefact written to: {os.path.relpath(out_path, _BACKEND)}')
    print('=' * 78)
    # Exit non-zero if no signals pass — useful for CI gating later.
    return 0 if any(acceptance.values()) else 2


def _spearman(xs, ys):
    """Quick rank-correlation. Returns rho in [-1, 1]. Lightweight stand-in
    for scipy.stats.spearmanr — no need for the dep for an 8-point panel."""
    n = len(xs)
    if n < 2:
        return 0.0
    rx = _ranks(xs)
    ry = _ranks(ys)
    mean_x = sum(rx) / n
    mean_y = sum(ry) / n
    num = sum((rx[i] - mean_x) * (ry[i] - mean_y) for i in range(n))
    den_x = (sum((rx[i] - mean_x) ** 2 for i in range(n))) ** 0.5
    den_y = (sum((ry[i] - mean_y) ** 2 for i in range(n))) ** 0.5
    if den_x == 0 or den_y == 0:
        return 0.0
    return num / (den_x * den_y)


def _ranks(values):
    """Ascending dense ranks; ties get averaged rank."""
    pairs = sorted(enumerate(values), key=lambda p: p[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][1] == pairs[i][1]:
            j += 1
        avg_rank = (i + j) / 2 + 1  # 1-indexed
        for k in range(i, j + 1):
            ranks[pairs[k][0]] = avg_rank
        i = j + 1
    return ranks


if __name__ == '__main__':
    sys.exit(main())
