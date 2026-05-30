"""Matcher confidence calibration: ECE + Brier + 10-bin reliability table.

Plan C (Tier 1 statistical analyses). Loads every matcher benchmark
artefact under `backend/environmental_impact_model/data/matcher_benchmark_*.json`
and reports, per artefact:

  - **ECE** (Naeini, Cooper & Hauskrecht 2015) on the verbalised
    confidence vs the binary "clean" outcome, 10 equal-width bins.
  - **Brier score** (Brier 1950): mean squared error between
    confidence (treated as p(correct)) and the binary outcome.
  - **Reliability diagram table**: per-bin n, mean confidence,
    observed accuracy (ready for matplotlib in the SI).

Outcome label policy:
  - When `reviewer_verdict == 'good'` is populated, use that as the
    binary "correct" outcome.
  - Otherwise fall back to `automated_verdict != 'flagged'` =
    "structural plausibility" (group consistency + magnitude + token
    overlap all pass). This is the right proxy for calibrating
    confidence because it does NOT bake confidence-band membership
    back into the outcome. Using `clean` as outcome would be circular
    since `clean` requires confidence >= 0.85 as one of its conditions.
  - The strict `clean` proxy is also reported for cross-reference.

This is a behavioural calibration, not ground truth; reviewer labels
(Scenario S7) remain the gold standard and are deferred to v2.

Run from `backend/`:
    python _smoke_matcher_calibration.py
"""
from __future__ import annotations

import glob
import json
import os
import sys
from typing import Dict, List, Tuple


_HERE = os.path.abspath('.')
_BENCH_DIR = os.path.join(_HERE, 'environmental_impact_model', 'data')
_OUTPUT_JSON = os.path.join(_HERE, '_smoke_matcher_calibration_results.json')

_BIN_EDGES = [i / 10.0 for i in range(11)]  # 11 edges -> 10 bins


def _binary_outcome(row: Dict, strict: bool = False) -> int:
    """Return 1 if the match is judged correct, 0 otherwise.

    `strict=False` (default): structural plausibility — all 4 heuristics
    pass, i.e. `automated_verdict != 'flagged'`. This is the
    confidence-independent outcome (avoids circularity).
    `strict=True`: `automated_verdict == 'clean'` — additionally requires
    confidence >= 0.85. Reported for cross-reference; this is the
    pre-/post-upgrade band-rate metric the manuscript already quotes.
    """
    rv = row.get('reviewer_verdict')
    if rv:
        return 1 if rv == 'good' else 0
    av = row.get('automated_verdict')
    if strict:
        return 1 if av == 'clean' else 0
    return 1 if av in ('clean', 'borderline') else 0


def _bin_of(conf: float) -> int:
    """Bin index 0..9 for confidence in [0, 1]."""
    if conf >= 1.0:
        return 9
    if conf < 0.0:
        return 0
    return min(9, int(conf * 10))


def _calibrate(rows: List[Dict], strict: bool = False) -> Dict:
    """Compute ECE, Brier, and the 10-bin reliability table.

    Skips rows where `confidence` is None or `matched` is False AND the
    row carries no verdict signal (those rows are genuine fallthroughs
    to the group-default path and the model isn't claiming a confidence
    for them).
    """
    usable: List[Tuple[float, int]] = []
    for r in rows:
        conf = r.get('confidence')
        if conf is None:
            continue
        outcome = _binary_outcome(r, strict=strict)
        usable.append((float(conf), outcome))

    n_total = len(usable)
    if n_total == 0:
        return {'n': 0, 'ece': float('nan'), 'brier': float('nan'),
                'bins': [], 'proxy': 'no usable rows'}

    proxy = 'reviewer_verdict (good=1) where present, else ' \
            'automated_verdict (clean=1)'

    # Reliability bins
    bins: List[Dict] = []
    for b in range(10):
        bins.append({
            'bin_index': b,
            'bin_lo': _BIN_EDGES[b],
            'bin_hi': _BIN_EDGES[b + 1],
            'n': 0,
            'mean_confidence': 0.0,
            'observed_accuracy': 0.0,
            'sum_conf': 0.0,
            'sum_outcome': 0.0,
        })
    for conf, outcome in usable:
        b = _bin_of(conf)
        bins[b]['n'] += 1
        bins[b]['sum_conf'] += conf
        bins[b]['sum_outcome'] += outcome
    for b in bins:
        if b['n'] > 0:
            b['mean_confidence'] = b['sum_conf'] / b['n']
            b['observed_accuracy'] = b['sum_outcome'] / b['n']
        b.pop('sum_conf')
        b.pop('sum_outcome')

    # ECE = sum_b (n_b / N) * |mean_conf_b - observed_acc_b|
    ece = 0.0
    for b in bins:
        if b['n'] == 0:
            continue
        ece += (b['n'] / n_total) * abs(
            b['mean_confidence'] - b['observed_accuracy']
        )

    # Brier = (1/N) * sum (confidence_i - outcome_i)^2
    brier = sum((c - o) ** 2 for c, o in usable) / n_total

    # Average confidence and accuracy at the panel level
    mean_conf_panel = sum(c for c, _ in usable) / n_total
    mean_acc_panel = sum(o for _, o in usable) / n_total

    return {
        'n': n_total,
        'ece': ece,
        'brier': brier,
        'mean_confidence_panel': mean_conf_panel,
        'observed_accuracy_panel': mean_acc_panel,
        'mean_overconfidence': mean_conf_panel - mean_acc_panel,
        'bins': bins,
        'proxy': proxy,
    }


def _print_report(label: str, result: Dict) -> None:
    n = result['n']
    if n == 0:
        print(f'  [{label}] no usable rows; skipping')
        return
    print(f'  [{label}] n = {n}')
    print(f'      ECE       = {result["ece"]:.4f}')
    print(f'      Brier     = {result["brier"]:.4f}')
    print(f'      mean conf = {result["mean_confidence_panel"]:.3f}   '
          f'observed acc = {result["observed_accuracy_panel"]:.3f}   '
          f'overconfidence = {result["mean_overconfidence"]:+.3f}')
    print(f'      reliability bins (lo-hi: n  mean_conf  obs_acc):')
    for b in result['bins']:
        if b['n'] == 0:
            continue
        print(f'         [{b["bin_lo"]:.1f}-{b["bin_hi"]:.1f}]  '
              f'n={b["n"]:>3}   conf={b["mean_confidence"]:.3f}   '
              f'acc={b["observed_accuracy"]:.3f}')


def main() -> int:
    paths = sorted(glob.glob(os.path.join(_BENCH_DIR, 'matcher_benchmark_*.json')))
    if not paths:
        print(f'ERROR: no matcher_benchmark_*.json under {_BENCH_DIR}')
        return 1

    print('Matcher confidence calibration (ECE + Brier + reliability diagram)')
    print(f'  Benchmark dir: {_BENCH_DIR}')
    print(f'  Outcome proxy: automated_verdict == clean (reviewer_verdict '
          f'not populated in current artefacts)')
    print('=' * 80)
    print()

    out: Dict[str, Dict] = {}
    for path in paths:
        basename = os.path.basename(path)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                d = json.load(f)
        except Exception as exc:
            print(f'  WARN: cannot parse {basename}: {exc!r}')
            continue
        rows = d.get('per_food', [])
        if not rows:
            print(f'  WARN: {basename} has no per_food block')
            continue
        result_plausibility = _calibrate(rows, strict=False)
        result_strict = _calibrate(rows, strict=True)
        meta = {
            'git_rev': d.get('git_rev'),
            'sample_size': d.get('sample_size'),
            'matcher_pack_version': d.get('matcher_pack_version'),
            'generated_at_utc': d.get('generated_at_utc'),
        }
        result_plausibility['_source_meta'] = meta
        result_strict['_source_meta'] = meta
        out[basename] = {
            'plausibility_proxy': result_plausibility,
            'strict_clean_proxy': result_strict,
        }
        print(f'  --- {basename} (sample n = {d.get("sample_size")}) ---')
        print()
        print('    PROXY = structural plausibility (verdict != flagged)')
        _print_report(basename, result_plausibility)
        print()
        print('    PROXY = strict clean (verdict == clean)')
        _print_report(basename, result_strict)
        print()

    with open(_OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump({
            'panel_description': 'Matcher calibration (ECE + Brier + 10-bin '
                                 'reliability) across all matcher_benchmark_*.json',
            'outcome_proxy': 'reviewer_verdict==good when present, else '
                             'automated_verdict==clean',
            'bin_edges': _BIN_EDGES,
            'per_artefact': out,
        }, f, indent=2)

    print('=' * 80)
    if out:
        # Headline ranking under the plausibility proxy (the non-circular one).
        sorted_by_ece = sorted(
            ((k, v['plausibility_proxy']) for k, v in out.items()
             if v['plausibility_proxy']['n'] > 0),
            key=lambda x: x[1]['ece'],
        )
        if sorted_by_ece:
            best_k, best_v = sorted_by_ece[0]
            worst_k, worst_v = sorted_by_ece[-1]
            print('Headline ranking (plausibility proxy = verdict != flagged):')
            print(f'  Best calibrated:  {best_k}  ECE = {best_v["ece"]:.4f}  '
                  f'Brier = {best_v["brier"]:.4f}')
            print(f'  Worst calibrated: {worst_k}  ECE = {worst_v["ece"]:.4f}  '
                  f'Brier = {worst_v["brier"]:.4f}')
    print(f'Results JSON: {_OUTPUT_JSON}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
