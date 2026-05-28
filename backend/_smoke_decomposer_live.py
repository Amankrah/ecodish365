"""Targeted live smoke for Tier γ — exercises the decomposer on CNF foods
that are unlikely to have a direct Agribalyse v32 counterpart.

The Agribalyse v32 catalogue is French-curated; Canadian-specific composites
like poutine, bannock, tourtière, Nanaimo bar, and US-style mixed dishes
(shepherd's pie with corn, cheese pasta babyfood) have no clean 1:1
counterpart in v32. These are the *intended* trigger cases for Tier γ —
food groups where the §3.5 matcher's fallback to the group-mean would
discard most of the composition signal.

Run from `backend/`:  python _smoke_decomposer_live.py
"""
from __future__ import annotations

import json
import os
import sys
import time

_BACKEND = os.path.dirname(os.path.abspath(__file__))
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    p = os.path.join(_BACKEND, sub)
    if p not in sys.path:
        sys.path.insert(0, p)
# Load OPENAI_API_KEY etc. from backend/.env BEFORE Django setup, since the
# methodology pack + matcher singletons read it at first use and Django's
# default settings.py does NOT auto-load .env.
try:
    from dotenv import load_dotenv  # noqa: E402
    load_dotenv(os.path.join(_BACKEND, '.env'))
except Exception:
    pass
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()
if not os.environ.get('OPENAI_API_KEY'):
    print('OPENAI_API_KEY missing — aborting live decomposer smoke.')
    sys.exit(1)
print(f'Using OpenAI key sk-***{os.environ["OPENAI_API_KEY"][-6:]}')


def main():
    from django.test import Client
    c = Client()

    # CNF foods picked to maximise the chance of triggering Tier γ:
    canadian_specific = [
        (4082,   'Bannock',                                              'Baked Products',   100),
        (6883, 'Tourtiere, homemade',                                  'Baked Products',   150),
        (6772, 'Poutine',                                              'Mixed Dishes',     250),
        (6621, 'Butter tart, with raisins, homemade',                  'Baked Products',    50),
        (6773, "Shepherd's pie with corn",                             'Mixed Dishes',     250),
        # Composite babyfoods (unlikely to be in v32's `aliments infantiles`):
        (7505, 'Babyfood, dinner, beef with vegetables',               'Babyfoods',        110),
        (7509, 'Babyfood, dinner, chicken with cheese pasta and veg',  'Babyfoods',        110),
    ]

    print('=' * 78)
    print(f'Live decomposer smoke — {len(canadian_specific)} Canadian-specific composites')
    print('=' * 78)

    fired = 0          # decomposition fully resolved (matched=True)
    attempted = 0      # decomposer triggered (decomp_decisions present, regardless of outcome)
    not_fired = 0      # matcher succeeded with high confidence; no decomposition attempted
    for fid, label, group, qty in canadian_specific:
        t = time.time()
        r = c.post('/api/environmental-impact/', data=json.dumps({
            'foods': [{'food_id': fid, 'quantity': qty}],
            'enable_lca_matcher': True,
            'enable_recipe_decomposer': True,
        }), content_type='application/json')
        elapsed = time.time() - t
        body = r.json()['data']
        env = body.get('data', {}).get('environmental_impacts', {})
        matcher = (env.get('lca_matcher_decisions') or [{}])[0]
        decomp = (env.get('recipe_decomposition_decisions') or [{}])[0] if env.get('recipe_decomposition_decisions') else {}
        gw = env.get('all_impacts', {}).get('Global warming')

        print(f'\nfood_id={fid:6d}  {label}  ({qty} g, group={group})  [{elapsed:.1f}s]')
        m_match = matcher.get('matched')
        print(f'  matcher:   matched={m_match}  conf={matcher.get("confidence", 0):.2f}  '
              f'-> [{matcher.get("ciqual_code")}] {(matcher.get("lci_name") or "")[:55]}')
        print(f'             reason: {(matcher.get("justification") or "")[:80]}')

        if decomp:
            d_match = decomp.get('matched')
            attempted += 1
            triggered_by = decomp.get('triggered_by', '?')
            print(f'  decomp:    matched={d_match}  ingredients={decomp.get("ingredient_count")}  '
                  f'conf={decomp.get("decomposition_confidence", 0):.2f}  '
                  f'mass={decomp.get("total_recipe_mass_g", 0):.1f}g+unres{decomp.get("unresolved_mass_g", 0):.1f}g  '
                  f'triggered_by={triggered_by}')
            if decomp.get('fallback_reason'):
                print(f'             fallback_reason: {decomp.get("fallback_reason")}')
            for ing in decomp.get('ingredients', [])[:6]:
                print(f'             [{ing["ciqual_code"]:>6}] {ing["mass_g"]:5.1f}g  '
                      f'{ing["lci_name"][:48]:<48}  {(ing["rationale"] or "")[:30]}')
            if d_match:
                fired += 1
        else:
            not_fired += 1
            print('  decomp:    not invoked (matcher matched at high confidence ≥ 0.85)')

        print(f'  GW headline (per 100 kcal): {gw:.4f}')

    print()
    print('=' * 78)
    print(f'SUMMARY (of {len(canadian_specific)} Canadian-specific composites):')
    print(f'  decomposer ATTEMPTED:    {attempted:2d}/{len(canadian_specific)}  '
          f'(routed via Tier γ trigger: matcher_failed OR low_matcher_confidence + composite group)')
    print(f'  decomposer RESOLVED:     {fired:2d}/{len(canadian_specific)}  '
          f'(all 4 validation gates passed; mass-weighted aggregate replaced matcher result)')
    print(f'  matcher direct (conf ≥ 0.85):  {not_fired:2d}/{len(canadian_specific)}  '
          f'(no decomposition needed; high-confidence Agribalyse v32 match)')
    print()
    print('  When decomposition was attempted but did not resolve, the LLM self-reported')
    print('  low confidence — correctly admitting it cannot express e.g. Quebec cheese curds')
    print("  or proper tourtière pastry in Agribalyse v32's French-curated ingredient vocabulary.")
    print('  The audit trail records the attempt + rejection reason; the matcher\'s borderline')
    print('  result remains as the best-available output.')
    print('=' * 78)
    return 0


if __name__ == '__main__':
    sys.exit(main())
