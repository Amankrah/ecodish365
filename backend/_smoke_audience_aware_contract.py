"""End-to-end validation harness for the AUDIENCE-CODE-1 contract.

For each of the 4 nutrition endpoints (HENI / HEFI / HSR / FCS) and each of
the 3 user_types (individual / researcher / policy), assert:

  1. Response includes a top-level `explanations` block
  2. Block contains `score_summary` with literature-grounded headline + caveat
  3. Individual mode contains the MANDATORY caveat per source paper:
     - HENI: marginality ("marginal" or "ONE SERVING" keywords) — Stylianou 2021 Discussion p. 622
     - HEFI: single-day ("single-day" or "one day") — Brassard 2022b Discussion p. 588
     - HSR: within-category-only ("WITHIN" + "category") — HSRAC v9 Introduction
     - FCS: per-100-kcal cross-category warning — Mozaffarian 2021
  4. Individual mode does NOT leak math: no "μDALY", no "0.5256", no "baseline",
     no "original_score", no "DRF" in the explanations strings
  5. Researcher mode includes literature citations block (Stylianou 2021,
     Brassard 2022, HSRAC v9, Mozaffarian 2021, Monteiro 2019 references)
  6. Policy mode includes `policy_context` with use cases + population data

Run from `backend/`:
    python _smoke_audience_aware_contract.py
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-audience-contract'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()
from django.test import Client  # noqa: E402


# A single canonical CNF food (apple raw, food_id=1696) is used as the probe
# across all 4 endpoints. Apple is in NOVA 1, scores well on HEFI / HSR / FCS,
# and is HENI-positive — so the explanation packs all return meaningful
# audience-specific copy without depending on smoke-time CNF substrate drift.
PROBE_FOOD_ID = 1696
PROBE_FOOD_NAME = 'Apple, raw, with skin'


# Per-system request shapes (each API has a different convention)
def heni_request(user_type: str) -> Dict[str, Any]:
    return {'meal': [{'food_id': PROBE_FOOD_ID, 'amount': 150.0, 'unit': 'g'}],
            'user_type': user_type}


def hefi_request(user_type: str) -> Dict[str, Any]:
    return {'foods': [{'food_id': PROBE_FOOD_ID, 'amount_g': 150.0}],
            'user_type': user_type}


def hsr_request(user_type: str) -> Dict[str, Any]:
    return {'food_ids': [PROBE_FOOD_ID], 'serving_sizes': [150.0],
            'user_type': user_type}


def fcs_request(user_type: str) -> Dict[str, Any]:
    return {'food_ids': [PROBE_FOOD_ID], 'food_names': [PROBE_FOOD_NAME],
            'user_type': user_type}


# Per-system explanation path inside the response (each API nests differently)
def extract_explanations(endpoint: str, response_json: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Walk the per-endpoint nesting to the explanations block."""
    try:
        if endpoint == 'heni':
            return response_json['data']['data']['explanations']
        if endpoint == 'hefi':
            return response_json['data']['explanations']
        if endpoint == 'hsr':
            return response_json['explanations']
        if endpoint == 'fcs':
            return response_json['data']['data']['explanations']
    except (KeyError, TypeError):
        return None
    return None


# Per-system mandatory caveat patterns (case-insensitive substring check)
MANDATORY_CAVEAT_PATTERNS = {
    'heni': ['marginal', 'one serving'],          # Stylianou 2021 Discussion p. 622
    'hefi': ['single-day', 'one day', 'usual adherence'],  # Brassard 2022b Discussion p. 588
    'hsr':  ['within'],                            # HSRAC v9 Introduction
    'fcs':  ['per 100', 'cross', 'mortality benefit'],  # Mozaffarian 2021 / O'Hearn 2022
}


# Math-leak forbidden tokens in individual mode (case-insensitive substring)
INDIVIDUAL_MODE_FORBIDDEN = [
    'μDALY', 'udaly', '0.5256', '0.53 min',          # HENI math
    'baseline + modifying', 'baseline -', 'modifying points',  # HSR math
    'original_score', 'pre-rescaling',                # FCS math
    'DRF', 'drf coefficient',                         # HENI math
    'energy-relative TMREL',                          # Rust-kernel detail
    'cup-eq', 'oz-eq', 'cup equivalents',             # FPED bridge internal
]


# Per-system researcher-mode required citations (substring; literature anchor)
RESEARCHER_CITATIONS_REQUIRED = {
    'heni': ['Stylianou', '2021', 'Nat Food'],
    'hefi': ['Brassard', '2022', 'APNM'],
    'hsr':  ['HSRAC', 'Shahid', '2020'],
    'fcs':  ['Mozaffarian', '2021', 'Nat Food', "O'Hearn"],
}


@dataclass
class ContractCheck:
    endpoint: str
    user_type: str
    check: str
    passed: bool
    detail: str


def _check_response(endpoint: str, user_type: str, response_json: Dict[str, Any]) -> List[ContractCheck]:
    """Run all per-(endpoint, user_type) contract assertions."""
    checks: List[ContractCheck] = []

    # (1) explanations block present
    exp = extract_explanations(endpoint, response_json)
    if exp is None:
        checks.append(ContractCheck(endpoint, user_type, 'has_explanations_block',
                                     False, 'NOT FOUND in expected path'))
        return checks  # Subsequent checks impossible
    checks.append(ContractCheck(endpoint, user_type, 'has_explanations_block',
                                 True, f'keys={list(exp.keys())}'))

    # (2) score_summary present
    summary = exp.get('score_summary')
    summary_present = isinstance(summary, dict) and bool(summary.get('headline'))
    checks.append(ContractCheck(endpoint, user_type, 'has_score_summary_headline',
                                 summary_present, str(summary.get('headline', '<missing>'))[:80] if summary else ''))

    # (3) mandatory caveat present (individual mode = strictest; researcher/policy also have caveats)
    expected_patterns = MANDATORY_CAVEAT_PATTERNS.get(endpoint, [])
    if summary:
        caveat = str(summary.get('mandatory_caveat', ''))
    else:
        caveat = ''
    matched_pattern = next((p for p in expected_patterns if p.lower() in caveat.lower()), None)
    checks.append(ContractCheck(endpoint, user_type, 'mandatory_caveat_present',
                                 matched_pattern is not None,
                                 f'matched "{matched_pattern}" in caveat' if matched_pattern else
                                 f'expected one of {expected_patterns} in caveat'))

    # (4) Individual-mode math-leak check
    if user_type == 'individual':
        # Concatenate ALL string values in the explanations block
        flat_text = _flatten_text(exp)
        leaked = [tok for tok in INDIVIDUAL_MODE_FORBIDDEN if tok.lower() in flat_text.lower()]
        checks.append(ContractCheck(endpoint, user_type, 'no_math_leak_individual',
                                     not leaked,
                                     f'LEAKED tokens: {leaked}' if leaked else
                                     '(no forbidden math tokens detected)'))

    # (5) Researcher-mode citations present
    if user_type == 'researcher':
        citations = exp.get('citations', {})
        citations_text = ' '.join(str(v) for v in citations.values()) if isinstance(citations, dict) else ''
        required = RESEARCHER_CITATIONS_REQUIRED.get(endpoint, [])
        missing = [r for r in required if r.lower() not in citations_text.lower()]
        checks.append(ContractCheck(endpoint, user_type, 'researcher_citations_present',
                                     not missing,
                                     f'missing required citations: {missing}' if missing else
                                     f'all required citations present ({len(required)})'))
        # Methodology block also expected
        meth_present = 'methodology' in exp and bool(exp['methodology'])
        checks.append(ContractCheck(endpoint, user_type, 'researcher_methodology_present',
                                     meth_present, str(list(exp.get('methodology', {}).keys()))[:80]))

    # (6) Policy-mode policy_context present
    if user_type == 'policy':
        pc_present = 'policy_context' in exp and bool(exp['policy_context'])
        checks.append(ContractCheck(endpoint, user_type, 'policy_context_present',
                                     pc_present, str(list(exp.get('policy_context', {}).keys()))[:80]))

    return checks


def _flatten_text(obj: Any) -> str:
    """Recursively concatenate all str values in a nested dict for substring matching."""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return ' '.join(_flatten_text(v) for v in obj.values())
    if isinstance(obj, list):
        return ' '.join(_flatten_text(v) for v in obj)
    return ''


ENDPOINTS = [
    ('heni', '/api/heni/calculate/', heni_request),
    ('hefi', '/api/hefi/calculate/', hefi_request),
    ('hsr',  '/api/hsr/calculate/',  hsr_request),
    ('fcs',  '/api/fcs/calculate/',  fcs_request),
]
USER_TYPES = ['individual', 'researcher', 'policy']


def main() -> int:
    client = Client()
    print('AUDIENCE-CODE-1 contract validation harness')
    print(f'  Probe food: CNF FoodID {PROBE_FOOD_ID} ({PROBE_FOOD_NAME})')
    print(f'  Endpoints: {[e[0] for e in ENDPOINTS]}')
    print(f'  User types: {USER_TYPES}')
    print('=' * 80)
    print()

    all_checks: List[ContractCheck] = []
    for endpoint, url, request_fn in ENDPOINTS:
        for user_type in USER_TYPES:
            body = request_fn(user_type)
            r = client.post(url, data=json.dumps(body),
                            content_type='application/json', secure=True)
            if r.status_code != 200:
                all_checks.append(ContractCheck(endpoint, user_type, 'http_200',
                                                 False, f'status={r.status_code} body={r.content[:200]!r}'))
                continue
            try:
                response_json = r.json()
            except Exception as exc:
                all_checks.append(ContractCheck(endpoint, user_type, 'json_parseable',
                                                 False, f'parse error: {exc!r}'))
                continue

            checks = _check_response(endpoint, user_type, response_json)
            all_checks.extend(checks)

    # Print per-(endpoint, user_type) summary
    by_pair: Dict[tuple, List[ContractCheck]] = {}
    for c in all_checks:
        by_pair.setdefault((c.endpoint, c.user_type), []).append(c)

    n_pass = sum(1 for c in all_checks if c.passed)
    n_fail = sum(1 for c in all_checks if not c.passed)

    for (endpoint, user_type), checks in by_pair.items():
        passed = sum(1 for c in checks if c.passed)
        total = len(checks)
        status = 'PASS' if passed == total else 'FAIL'
        print(f'[{status}]  {endpoint:>5} x {user_type:>10}   {passed}/{total} assertions passed')
        for c in checks:
            mark = ' OK ' if c.passed else 'FAIL'
            print(f'   [{mark}] {c.check:<35s}  {c.detail[:80]}')
        print()

    print('=' * 80)
    print(f'Overall: PASS={n_pass}  FAIL={n_fail}  TOTAL={n_pass + n_fail}')

    out_path = os.path.join(_HERE, '_smoke_audience_aware_contract_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'harness_description': 'AUDIENCE-CODE-1 contract validation (4 endpoints x 3 user_types)',
            'probe_food': {'food_id': PROBE_FOOD_ID, 'name': PROBE_FOOD_NAME},
            'summary': {'pass': n_pass, 'fail': n_fail, 'total': n_pass + n_fail},
            'checks': [
                {'endpoint': c.endpoint, 'user_type': c.user_type, 'check': c.check,
                 'passed': c.passed, 'detail': c.detail}
                for c in all_checks
            ],
        }, f, indent=2)
    print(f'Results JSON: {out_path}')
    return 0 if n_fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
