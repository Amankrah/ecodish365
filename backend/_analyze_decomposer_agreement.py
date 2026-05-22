"""Decomposer-agreement analysis — classify Tier γ attempts to inform the
"decomposer-confirmed direct match" gate refinement (Hypothesis B).

Reads the most-recent `matcher_benchmark_*.json` artefact (written by
_smoke_matcher_benchmark.py --with-decomposer) and partitions every
`decomposer_attempted=True` row into 7 categories:

  A. resolved, n_ing ≥ 2, agreement      — decomp succeeded; first ingredient
                                            equals matcher's choice
  B. resolved, n_ing ≥ 2, no agreement   — decomp succeeded; differs from matcher
  C. resolved, n_ing = 1, agreement      — impossible under current gate (rejected
                                            at min_ingredients=2); included for
                                            future compatibility
  D. REJECTED min_ingredients, agreement — FALSE REJECTIONS — Hypothesis B would
                                            accept these as direct-match confirmations
  E. REJECTED min_ingredients, no agreement — genuine — 1-ingredient decomp
                                            doesn't match matcher's choice
  F. REJECTED mass_too_large             — genuine no-clean-decomposition
  G. REJECTED other (low_confidence,     — expected ~0 under gpt-4.1-mini;
     hallucinated_ciqual, etc.)            flag if non-zero

Run from `backend/`:  python _analyze_decomposer_agreement.py
Output: stdout summary + markdown artefact at
        environmental_impact_model/data/decomposer_agreement_analysis.md

No LLM cost; pure JSON read.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

_BACKEND = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_BACKEND, 'environmental_impact_model', 'data')


def _latest_benchmark_path() -> Optional[str]:
    paths = sorted(glob.glob(os.path.join(_DATA_DIR, 'matcher_benchmark_*.json')))
    return paths[-1] if paths else None


def _first_ingredient_ciqual(row: Dict[str, Any]) -> Optional[str]:
    """Extract the first decomposer ingredient's ciqual_code. Returns None
    if the row has no ingredient list (legacy artefacts pre-Phase A) or the
    list is empty."""
    ings = row.get('decomposer_ingredients')
    if not ings:
        return None
    first = ings[0]
    return first.get('ciqual_code')


def _classify(row: Dict[str, Any], floor: float = 0.75) -> Tuple[str, str]:
    """Return (category_letter, explanation) for one decomposer-attempted row.

    Categories defined in the module docstring. `floor` is the matcher-
    confidence floor for the "agreement" test (Hypothesis B's proposed
    MATCHER_AGREEMENT_CONFIDENCE_FLOOR = 0.75).
    """
    n_ing = row.get('decomposer_n_ingredients') or 0
    resolved = bool(row.get('decomposer_resolved'))
    matcher_ciqual = row.get('ciqual_code')
    matcher_conf = row.get('confidence', 0.0)
    matcher_matched = bool(row.get('matched'))
    fallback = row.get('decomposer_fallback_reason') or ''
    first_ing = _first_ingredient_ciqual(row)

    # Agreement = decomposer's first ingredient equals matcher's choice AND
    # matcher actually matched (not matched=False fallback)
    agreement = (
        first_ing is not None
        and matcher_ciqual is not None
        and first_ing == matcher_ciqual
        and matcher_matched
        and matcher_conf >= floor
    )

    if resolved:
        if n_ing >= 2:
            return ('A' if agreement else 'B', 'resolved + ' + ('agreement' if agreement else 'no agreement'))
        # resolved with n_ing == 1 should be impossible under current gate;
        # included for forward-compat (e.g. after Hypothesis B ships)
        return ('C', 'resolved with n_ing=1 (unexpected pre-Hypothesis-B)')

    # Rejected branches — classify by fallback_reason
    if fallback.startswith('too_few_ingredients'):
        return ('D' if agreement else 'E',
                'rejected min_ingredients + ' + ('agreement (FALSE REJECTION)' if agreement else 'no agreement'))
    if fallback.startswith('unresolved_mass_too_large') or fallback.startswith('excess_unresolved'):
        return ('F', 'rejected mass_too_large (genuine)')
    return ('G', f'rejected other: {fallback or "(unknown)"}')


def analyze(path: str, floor: float = 0.75) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as fh:
        bench = json.load(fh)
    attempts = [r for r in bench['per_food'] if r.get('decomposer_attempted')]
    by_cat: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in attempts:
        cat, _ = _classify(r, floor=floor)
        by_cat[cat].append(r)
    return {
        'benchmark_path': path,
        'git_rev': bench.get('git_rev'),
        'sample_size': bench.get('sample_size'),
        'attempts': len(attempts),
        'floor': floor,
        'by_cat': dict(by_cat),
    }


_CATEGORY_NAMES = {
    'A': 'resolved, n_ing≥2, agreement (decomposer confirmed matcher\'s primary choice)',
    'B': 'resolved, n_ing≥2, no agreement (decomposer disagreed with matcher)',
    'C': 'resolved, n_ing=1, agreement (impossible under current gate)',
    'D': 'REJECTED min_ingredients, AGREEMENT — FALSE REJECTIONS (Hypothesis B would convert)',
    'E': 'REJECTED min_ingredients, no agreement (genuinely lazy 1-ingredient decomp)',
    'F': 'REJECTED mass_too_large (genuine no-clean-decomposition)',
    'G': 'REJECTED other (low_confidence / hallucinated / etc.)',
}


def _render_summary(result: Dict[str, Any]) -> str:
    """Human-readable markdown summary."""
    lines: List[str] = []
    lines.append('# Decomposer-agreement analysis')
    lines.append('')
    lines.append(f'- Benchmark JSON: `{os.path.basename(result["benchmark_path"])}`')
    lines.append(f'- Git rev: `{result["git_rev"]}`')
    lines.append(f'- Sample size: {result["sample_size"]}')
    lines.append(f'- Tier γ attempts: {result["attempts"]}')
    lines.append(f'- Matcher-agreement confidence floor (Hypothesis B): {result["floor"]}')
    lines.append('')
    lines.append('## Classification')
    lines.append('')
    lines.append('| Cat | Count | Description |')
    lines.append('|:---:|:---:|:---|')
    for cat in 'ABCDEFG':
        n = len(result['by_cat'].get(cat, []))
        lines.append(f'| {cat} | {n} | {_CATEGORY_NAMES[cat]} |')
    lines.append('')

    # Per-category details + per-group breakdown
    for cat in 'ABCDEFG':
        rows = result['by_cat'].get(cat, [])
        if not rows:
            continue
        lines.append(f'### Category {cat} — {_CATEGORY_NAMES[cat]}')
        lines.append('')
        lines.append(f'**Count: {len(rows)}**')
        lines.append('')
        # Per-group breakdown
        by_group: Dict[str, int] = defaultdict(int)
        for r in rows:
            by_group[r['cnf_group']] += 1
        if len(by_group) > 1:
            lines.append('Per CNF FoodGroup:')
            for g, c in sorted(by_group.items(), key=lambda kv: -kv[1]):
                lines.append(f'- {g}: {c}')
            lines.append('')
        # Example rows (up to 5)
        lines.append('Examples:')
        for r in rows[:5]:
            first = _first_ingredient_ciqual(r) or '?'
            lines.append(
                f'- `food_id={r["food_id"]}` [{r["cnf_group"]}] '
                f'matcher conf={r["confidence"]} → `[{r["ciqual_code"]}] {r["lci_name"][:40]}` ; '
                f'decomp n={r.get("decomposer_n_ingredients")} first=`[{first}]` '
                f'resolved={r["decomposer_resolved"]} fallback={r.get("decomposer_fallback_reason") or "-"}'
            )
            lines.append(f'    - CNF: {r["cnf_name"]}')
        lines.append('')

    # Decision block
    n_D = len(result['by_cat'].get('D', []))
    n_E = len(result['by_cat'].get('E', []))
    n_F = len(result['by_cat'].get('F', []))
    n_G = len(result['by_cat'].get('G', []))
    lines.append('## Decision rule (Hypothesis B)')
    lines.append('')
    if n_D >= 2 and n_E == 0:
        verdict = 'PROCEED — Hypothesis B is clearly correct.'
    elif n_D >= 2 and n_E > 0:
        verdict = f'PROCEED WITH CARE — {n_D} false rejections vs {n_E} genuine 1-ingredient rejections. Review category E examples before shipping.'
    elif n_D == 1:
        verdict = 'WEAK EVIDENCE — only 1 false rejection found. Implementation is still correct but the payoff is small.'
    elif n_D == 0:
        verdict = 'REJECT HYPOTHESIS B — no false rejections found in this run. The 2 cases from the previous run may have been LLM-call variance.'
    else:
        verdict = 'UNCLEAR — review the table.'
    lines.append(f'**Verdict**: {verdict}')
    lines.append('')
    lines.append(f'- Category D (false rejections that Hypothesis B would convert): **{n_D}**')
    lines.append(f'- Category E (genuine 1-ingredient rejections; B would correctly leave alone): {n_E}')
    lines.append(f'- Category F (genuine mass-balance rejections; B does not affect): {n_F}')
    lines.append(f'- Category G (other rejections): {n_G}')
    if n_D >= 2:
        lines.append('')
        lines.append('**Expected resolve-rate climb after shipping Hypothesis B**:')
        attempts = result['attempts']
        currently_resolved = len(result['by_cat'].get('A', [])) + len(result['by_cat'].get('B', []))
        lines.append(f'- Before: {currently_resolved}/{attempts} = {100*currently_resolved/attempts:.0f}%')
        lines.append(f'- After:  {currently_resolved + n_D}/{attempts} = {100*(currently_resolved + n_D)/attempts:.0f}%')
    return '\n'.join(lines) + '\n'


def main():
    path = _latest_benchmark_path()
    if not path:
        print('No matcher_benchmark_*.json artefact found. Run _smoke_matcher_benchmark.py --with-decomposer first.')
        return 1
    print(f'Analyzing: {os.path.basename(path)}')
    result = analyze(path)
    summary_md = _render_summary(result)

    # Stdout — concise table
    print()
    print('=' * 78)
    print('DECOMPOSER-AGREEMENT CLASSIFICATION')
    print('=' * 78)
    print(f'Tier γ attempts: {result["attempts"]}')
    print(f'Floor: matcher_conf >= {result["floor"]}')
    print()
    print(f'{"Cat":<4} {"Count":>6}  Description')
    print('-' * 78)
    for cat in 'ABCDEFG':
        n = len(result['by_cat'].get(cat, []))
        desc = _CATEGORY_NAMES[cat][:60]
        print(f'{cat:<4} {n:>6}  {desc}')
    print()
    n_D = len(result['by_cat'].get('D', []))
    if n_D >= 2:
        attempts = result['attempts']
        currently_resolved = len(result['by_cat'].get('A', [])) + len(result['by_cat'].get('B', []))
        print(f'After shipping Hypothesis B: resolve-rate climbs '
              f'{currently_resolved}/{attempts} ({100*currently_resolved/attempts:.0f}%) '
              f'-> {currently_resolved + n_D}/{attempts} ({100*(currently_resolved + n_D)/attempts:.0f}%)')

    # Write markdown artefact
    out_path = os.path.join(_DATA_DIR, 'decomposer_agreement_analysis.md')
    with open(out_path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(summary_md)
    print(f'\nMarkdown summary: {os.path.relpath(out_path, _BACKEND)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
