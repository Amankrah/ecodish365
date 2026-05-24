"""WAFCT 2019 vs CNF per-100g delta harness (WAFCT-EXPLORE Phase 3, 2026-05-24).

Curated empirical comparison: for ~16 deliberately picked foods across 3
sub-panels, compute per-nutrient absolute + percentage delta between
WAFCT 2019 and the Canadian Nutrient File on the 10 core nutrients
shared between the two systems.

  Panel A — Universal raw commodities (calibration baseline; expect 5-15% Δ)
  Panel B — Cooking/preparation variants (reveals method-dependence)
  Panel C — Region-specific (no CNF equivalent — document the gap)

CRITICAL: pairing is a hand-curated lookup table (NOT the LLM matcher) so
the exploration findings are deterministic and re-runnable. Each pair
includes the WAFCT Code and CNF FoodID anchors, plus a free-text
`note` field documenting any equivalence caveats (species mismatch,
fat-content delta, processing convention, etc.).

Outputs:
  - `_explore_wafct_vs_cnf_per100g_results.json` — machine-readable
  - stdout — markdown table for the memo

Run from `backend/`:
    set PYTHONIOENCODING=utf-8 && python _explore_wafct_vs_cnf_per100g.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from statistics import median
from typing import Any, Dict, List, Optional, Tuple

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:  # noqa: BLE001
    pass

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'wafct-vs-cnf'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

import openpyxl  # noqa: E402

WAFCT_PATH = os.path.join(_HERE, 'raw_wafct', 'WAFCT_2019.xlsx')
OUT_PATH = os.path.join(_HERE, '_explore_wafct_vs_cnf_per100g_results.json')

CODE_RE = re.compile(r'^\d{2}_\d+$')


# --- Nutrient bridge (subset for the 10 core shared nutrients) ------------
# (INFOODS tag, CNF NutrientName, unit, display label)
# Order = report order. Picked to span macronutrients + minerals that are
# (a) populated for ≥ 95 % of WAFCT foods, (b) present in CNF for all
# our Panel A/B foods, and (c) meaningful for HEFI / HENI / FCS scoring.
CORE_NUTRIENTS: List[Tuple[str, str, str, str]] = [
    ('ENERC_kcal', 'ENERGY (KILOCALORIES)',               'kcal', 'Energy'),
    ('WATER',      'MOISTURE',                            'g',    'Water'),
    ('PROTCNT',    'PROTEIN',                             'g',    'Protein'),
    ('FAT',        'FAT (TOTAL LIPIDS)',                  'g',    'Fat'),
    ('CHOAVLDF',   'CARBOHYDRATE, TOTAL (BY DIFFERENCE)', 'g',    'Carbs'),
    ('FIBTG',      'FIBRE, TOTAL DIETARY',                'g',    'Fibre'),
    ('CA',         'CALCIUM',                             'mg',   'Ca'),
    ('FE',         'IRON',                                'mg',   'Fe'),
    ('MG',         'MAGNESIUM',                           'mg',   'Mg'),
    ('K',          'POTASSIUM',                           'mg',   'K'),
]


# --- Panel definitions ----------------------------------------------------

@dataclass
class FoodPair:
    panel:        str            # 'A' / 'B' / 'C'
    wafct_code:   str            # e.g. '01_037'
    wafct_name:   str            # human-readable (for the report)
    cnf_food_id:  Optional[int]  # None for Panel C (no CNF equivalent)
    cnf_name:     str            # human-readable
    note:         str = ''       # equivalence caveat


# Panel A — universal raw commodities (~7 foods, expect 5-15% Δ on most nutrients)
PANEL_A: List[FoodPair] = [
    FoodPair('A', '01_037', 'Rice, white, raw',
             4471, 'Grains, rice, white, long-grain, regular, dry',
             'Both raw uncooked white rice'),
    FoodPair('A', '01_043', 'Wheat flour, white, unfortified',
             4501, 'Grains, wheat flour, white, all purpose, bleached',
             'WAFCT unfortified vs CNF bleached + flour-treatment-dependent'),
    FoodPair('A', '08_001', 'Egg, chicken, raw',
             125,  'Egg, chicken, whole, fresh or frozen, raw',
             'Direct match — universal commodity'),
    FoodPair('A', '10_001', 'Milk, cow, whole, pasteurized 3.5% fat',
             113,  'Milk, fluid, whole, pasteurized, homogenized, 3.25% M.F.',
             'WAFCT 3.5% vs CNF 3.25% — expect fat ~8% higher in WAFCT'),
    FoodPair('A', '05_028', 'Banana, yellow flesh, ripe, raw',
             1704, 'Banana, raw',
             'Direct match'),
    FoodPair('A', '01_039', 'Sorghum, whole grains, raw',
             4432, 'Grains, sorghum',
             'Both raw whole-grain sorghum; CNF entry unqualified'),
    FoodPair('A', '09_018', 'Catfish, fillet, raw',
             5966, 'Fish, tilapia, raw',
             'DIFFERENT SPECIES — catfish vs tilapia; both warm-water freshwater'),
]


# Panel B — cooking / preparation variants (sparse — WAFCT cooked entries
# don't always have a direct CNF cooked counterpart for the same food).
PANEL_B: List[FoodPair] = [
    FoodPair('B', '01_069', 'Rice, white, polished, boiled (no salt), drained',
             4475, 'Grains, rice, white, medium-grain, cooked',
             'WAFCT long-grain vs CNF medium-grain — boiled both'),
    FoodPair('B', '09_020', 'Catfish, fillet, grilled (no salt or fat)',
             5966, 'Fish, tilapia, raw',
             'WAFCT cooked vs CNF RAW — expect water Δ + protein concentration'),
]


# Panel C — region-specific WAFCT entries with no CNF equivalent
PANEL_C: List[FoodPair] = [
    FoodPair('C', '01_002', 'Fonio, black, whole grains, raw',
             None, '(no CNF equivalent — West African cereal)',
             'Fonio is a West African staple cereal absent from CNF'),
    FoodPair('C', '04_002', 'Baobab, leaves, dried',
             None, '(no CNF equivalent — West African leaf vegetable)',
             'Baobab leaves are a calcium-dense dried leafy green'),
    FoodPair('C', '03_042', 'African locust bean, fermented (soumbala/dawadawa)',
             None, '(no CNF equivalent — West African fermented seasoning)',
             'Fermented seasoning — high protein, very high sodium, regional staple'),
    FoodPair('C', '02_039', 'Cassava, gari (fermented, grated, toasted, white)',
             None, '(no CNF equivalent for gari specifically)',
             'Gari is a fermented + toasted cassava granule, distinct from CNF cassava'),
    FoodPair('C', '06_013', 'Melon seed (egusi), kernel only, dried, raw',
             None, '(no CNF equivalent — West African oil seed)',
             'Egusi seed — oilseed staple of West African soups'),
    FoodPair('C', '02_038', 'Cassava, flour, fermented (alibo/elubo/lafun)',
             None, '(no CNF equivalent for fermented cassava flour)',
             'Fermented cassava flour, distinct from CNF cassava flour'),
    FoodPair('C', '01_018', 'Pearl millet, IKMV 8201 variety, whole grains, raw',
             None, '(no CNF equivalent — pearl millet is sparse in CNF)',
             'Pearl millet is the West African Sahel cereal; CNF lacks varietals'),
]


# --- WAFCT data loader ---------------------------------------------------

def load_wafct_nv_sum_39() -> Dict[str, Dict[str, Optional[float]]]:
    """Load sheet 03 → {WAFCT_Code: {InfoodsTag: float or None}}.

    Disambiguates the two ENERC columns (kJ vs kcal) by column index +
    the row-0 header text — first ENERC column is kJ, second is kcal.
    """
    wb = openpyxl.load_workbook(WAFCT_PATH, read_only=True, data_only=True)
    ws = wb['03 NV_sum_39 (per 100g EP)']
    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 4:
        return {}
    headers_en = rows[0]
    headers_tag = rows[2]

    # Build column → effective-tag map. ENERC handled specially: first
    # occurrence gets suffix _kJ, second gets _kcal (per header row 0).
    col_to_tag: Dict[int, str] = {}
    enerc_seen = 0
    for i, raw_tag in enumerate(headers_tag):
        if raw_tag is None:
            continue
        tag = str(raw_tag).strip()
        if not tag:
            continue
        if tag == 'ENERC':
            unit_hint = str(headers_en[i] or '').lower()
            if 'kj' in unit_hint:
                col_to_tag[i] = 'ENERC_kJ'
            elif 'kcal' in unit_hint:
                col_to_tag[i] = 'ENERC_kcal'
            else:
                enerc_seen += 1
                col_to_tag[i] = 'ENERC_kJ' if enerc_seen == 1 else 'ENERC_kcal'
            continue
        # Strip ' or [ALT]' inline alternative
        if ' or ' in tag:
            tag = tag.split(' or ', 1)[0].strip()
        tag = tag.strip('[]').strip()
        col_to_tag[i] = tag

    out: Dict[str, Dict[str, Optional[float]]] = {}
    for row in rows[3:]:
        if not row or row[0] is None:
            continue
        code = str(row[0]).strip()
        if not CODE_RE.match(code):
            continue
        nutrients: Dict[str, Optional[float]] = {}
        for col_idx, tag in col_to_tag.items():
            if col_idx >= len(row):
                continue
            v = row[col_idx]
            if v is None or v == '' or (isinstance(v, str) and not v.strip()):
                nutrients[tag] = None
                continue
            # INFOODS convention: a numeric value wrapped in square
            # brackets (e.g. '[10.6]' for egg fat) marks an analytical-
            # method variant (here, FATCE continuous-flow-extraction
            # rather than proximate FAT). Numerically the same per-100g
            # value; strip the brackets so it round-trips as a float.
            if isinstance(v, str):
                v = v.strip()
                if v.startswith('[') and v.endswith(']'):
                    v = v[1:-1].strip()
            try:
                nutrients[tag] = float(v)
            except (TypeError, ValueError):
                # Remaining failures: empty brackets '[]' = true analytical N/A
                nutrients[tag] = None
        # Also pin the food name for display
        nutrients['_name_en'] = str(row[1]) if row[1] else ''   # type: ignore[assignment]
        out[code] = nutrients
    return out


# --- Comparison logic ---------------------------------------------------

@dataclass
class NutrientDelta:
    nutrient_label: str
    unit: str
    wafct: Optional[float]
    cnf:   Optional[float]
    abs_delta: Optional[float]
    pct_delta: Optional[float]
    flagged_large: bool = False

    def to_dict(self) -> Dict[str, Any]:
        def _r(v: Optional[float], nd: int = 2) -> Optional[float]:
            return None if v is None else round(v, nd)
        return {
            'nutrient': self.nutrient_label,
            'unit':     self.unit,
            'wafct':    _r(self.wafct),
            'cnf':      _r(self.cnf),
            'abs_delta': _r(self.abs_delta),
            'pct_delta': _r(self.pct_delta, 1),
            'flagged_large': self.flagged_large,
        }


@dataclass
class FoodComparison:
    pair: FoodPair
    wafct_resolved: bool
    cnf_resolved: bool
    nutrients: List[NutrientDelta] = field(default_factory=list)
    median_abs_pct_delta: Optional[float] = None
    notes: str = ''


def _pct_delta(wafct: Optional[float], cnf: Optional[float]) -> Optional[float]:
    """Δ% relative to the mean of the two values (symmetric, avoids divide-
    by-zero asymmetry when one source is much smaller)."""
    if wafct is None or cnf is None:
        return None
    mean = (wafct + cnf) / 2.0
    if mean == 0:
        return 0.0 if wafct == cnf else None
    return ((wafct - cnf) / mean) * 100.0


def compare_pair(
    pair: FoodPair,
    wafct_data: Dict[str, Dict[str, Optional[float]]],
    pipeline,
) -> FoodComparison:
    """Compute per-nutrient delta for one (WAFCT, CNF) pair."""
    wafct_row = wafct_data.get(pair.wafct_code)
    wafct_resolved = wafct_row is not None
    cnf_nutrients: Dict[str, float] = {}
    cnf_resolved = False
    if pair.cnf_food_id is not None:
        cnf_nutrients = pipeline.nutrients_for(pair.cnf_food_id)
        cnf_resolved = bool(cnf_nutrients)

    deltas: List[NutrientDelta] = []
    if pair.panel == 'C' or not cnf_resolved:
        # WAFCT-only — report WAFCT values verbatim, no delta
        if wafct_resolved and wafct_row:
            for infoods_tag, _cnf_name, unit, label in CORE_NUTRIENTS:
                w = wafct_row.get(infoods_tag)
                if isinstance(w, (int, float)):
                    deltas.append(NutrientDelta(
                        nutrient_label=label, unit=unit,
                        wafct=float(w), cnf=None,
                        abs_delta=None, pct_delta=None,
                    ))
        return FoodComparison(
            pair=pair,
            wafct_resolved=wafct_resolved,
            cnf_resolved=cnf_resolved,
            nutrients=deltas,
            notes='WAFCT-only (no CNF counterpart)' if pair.panel == 'C'
                  else 'CNF lookup failed',
        )

    if not wafct_resolved or not wafct_row:
        return FoodComparison(
            pair=pair, wafct_resolved=False, cnf_resolved=cnf_resolved,
            nutrients=[], notes=f'WAFCT code {pair.wafct_code!r} not found',
        )

    pct_deltas_seen: List[float] = []
    for infoods_tag, cnf_name, unit, label in CORE_NUTRIENTS:
        w = wafct_row.get(infoods_tag)
        c = cnf_nutrients.get(cnf_name)
        w_f = float(w) if isinstance(w, (int, float)) else None
        c_f = float(c) if isinstance(c, (int, float)) else None
        abs_delta = (w_f - c_f) if (w_f is not None and c_f is not None) else None
        pct = _pct_delta(w_f, c_f)
        flagged = pct is not None and abs(pct) > 25.0
        if pct is not None:
            pct_deltas_seen.append(abs(pct))
        deltas.append(NutrientDelta(
            nutrient_label=label, unit=unit,
            wafct=w_f, cnf=c_f,
            abs_delta=abs_delta, pct_delta=pct, flagged_large=flagged,
        ))
    med = round(median(pct_deltas_seen), 1) if pct_deltas_seen else None
    return FoodComparison(
        pair=pair,
        wafct_resolved=True,
        cnf_resolved=True,
        nutrients=deltas,
        median_abs_pct_delta=med,
        notes=pair.note,
    )


# --- Reporter -----------------------------------------------------------

def _print_panel_table(panel_id: str, comps: List[FoodComparison]) -> None:
    print(f'\n## Panel {panel_id}\n')
    # Compact markdown table — header
    nutrient_labels = [lbl for _, _, _, lbl in CORE_NUTRIENTS]
    header_cells = ['Food'] + [f'{lbl}' for lbl in nutrient_labels] + ['Median |Δ%|']
    print('| ' + ' | '.join(header_cells) + ' |')
    print('|' + '|'.join(['---'] * len(header_cells)) + '|')
    for c in comps:
        row_cells = [f'**WAFCT** {c.pair.wafct_code} {c.pair.wafct_name[:40]}']
        for nd in c.nutrients:
            row_cells.append(f'{nd.wafct:.1f}' if nd.wafct is not None else '–')
        row_cells.append('—')
        print('| ' + ' | '.join(row_cells) + ' |')
        if c.cnf_resolved and c.pair.cnf_food_id is not None:
            cnf_cells = [f'CNF {c.pair.cnf_food_id} {c.pair.cnf_name[:40]}']
            for nd in c.nutrients:
                cnf_cells.append(f'{nd.cnf:.1f}' if nd.cnf is not None else '–')
            cnf_cells.append('—')
            print('| ' + ' | '.join(cnf_cells) + ' |')
            delta_cells = ['Δ% (WAFCT − CNF)']
            for nd in c.nutrients:
                if nd.pct_delta is None:
                    delta_cells.append('–')
                else:
                    flag = '⚠' if nd.flagged_large else ''
                    delta_cells.append(f'{nd.pct_delta:+.1f}%{flag}')
            delta_cells.append(f'{c.median_abs_pct_delta:.1f}%' if c.median_abs_pct_delta is not None else '—')
            print('| ' + ' | '.join(delta_cells) + ' |')
        elif c.pair.panel == 'C':
            print(f'| _WAFCT-only — no CNF equivalent_ |' + ' | '.join([''] * len(nutrient_labels)) + ' | — |')
        print()


def _print_aggregate_bias(all_comps: List[FoodComparison]) -> None:
    """Per-nutrient median Δ% across all Panel A + B comparisons."""
    print('\n## Aggregate per-nutrient bias (Panel A + B only)\n')
    per_nutrient: Dict[str, List[float]] = {lbl: [] for _, _, _, lbl in CORE_NUTRIENTS}
    for c in all_comps:
        if not (c.wafct_resolved and c.cnf_resolved):
            continue
        for nd in c.nutrients:
            if nd.pct_delta is not None:
                per_nutrient[nd.nutrient_label].append(nd.pct_delta)
    print('| Nutrient | n | Median Δ% (WAFCT − CNF) | Median |Δ%| | Notes |')
    print('|---|---|---|---|---|')
    for _, _, _, lbl in CORE_NUTRIENTS:
        vals = per_nutrient[lbl]
        if not vals:
            print(f'| {lbl} | 0 | — | — | no comparable pairs |')
            continue
        med_signed = median(vals)
        med_abs = median([abs(v) for v in vals])
        direction = 'WAFCT higher' if med_signed > 5 else ('CNF higher' if med_signed < -5 else 'no systematic bias')
        print(f'| {lbl} | {len(vals)} | {med_signed:+.1f}% | {med_abs:.1f}% | {direction} |')


def main() -> int:
    print('WAFCT vs CNF per-100g delta harness (WAFCT-EXPLORE Phase 3)')
    print('=' * 80)

    print(f'\nLoading WAFCT NV_sum_39 from {WAFCT_PATH} …')
    wafct_data = load_wafct_nv_sum_39()
    print(f'  Loaded {len(wafct_data)} foods')

    print('\nLoading CNF pipeline …')
    from api.cnf_cache import get_api_cnf_pipeline
    pipeline = get_api_cnf_pipeline()
    print(f'  CNF pipeline ready ({len(pipeline.nutrients_by_food)} foods indexed)')

    # Run all 3 panels
    all_panels: Dict[str, List[FoodComparison]] = {}
    for panel_id, panel_list in [('A', PANEL_A), ('B', PANEL_B), ('C', PANEL_C)]:
        comps = [compare_pair(p, wafct_data, pipeline) for p in panel_list]
        all_panels[panel_id] = comps
        _print_panel_table(panel_id, comps)

    # Aggregate bias across A + B
    ab_comps = all_panels['A'] + all_panels['B']
    _print_aggregate_bias(ab_comps)

    # Per-food summary (median Δ% per food)
    print('\n## Per-food agreement (Panel A + B; smaller median Δ% = closer agreement)\n')
    print('| Food | Median |Δ%| | Verdict |')
    print('|---|---|---|')
    rated = [(c, c.median_abs_pct_delta) for c in ab_comps
             if c.median_abs_pct_delta is not None]
    rated.sort(key=lambda x: x[1])
    for c, m in rated:
        verdict = 'STRONG' if m < 15 else ('MODERATE' if m < 30 else 'WEAK')
        print(f'| WAFCT {c.pair.wafct_code} {c.pair.wafct_name[:50]} | {m:.1f}% | {verdict} |')

    # Persist JSON
    report = {
        'harness': 'WAFCT-EXPLORE Phase 3 — per-100g delta (2026-05-24)',
        'wafct_path': WAFCT_PATH,
        'core_nutrients': [
            {'infoods': t, 'cnf': n, 'unit': u, 'label': l}
            for t, n, u, l in CORE_NUTRIENTS
        ],
        'panels': {
            pid: [{
                'panel':       c.pair.panel,
                'wafct_code':  c.pair.wafct_code,
                'wafct_name':  c.pair.wafct_name,
                'cnf_food_id': c.pair.cnf_food_id,
                'cnf_name':    c.pair.cnf_name,
                'note':        c.pair.note,
                'wafct_resolved': c.wafct_resolved,
                'cnf_resolved':   c.cnf_resolved,
                'nutrients':   [nd.to_dict() for nd in c.nutrients],
                'median_abs_pct_delta': c.median_abs_pct_delta,
                'notes':       c.notes,
            } for c in comps]
            for pid, comps in all_panels.items()
        },
    }
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f'\nResults JSON: {OUT_PATH}')
    print(f'File size: {os.path.getsize(OUT_PATH) / 1024:.1f} KB')

    return 0


if __name__ == '__main__':
    sys.exit(main())
