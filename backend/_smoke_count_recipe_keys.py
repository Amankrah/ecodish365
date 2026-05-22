"""Verify the claim: every Agribalyse v32 catalog row contributes AT MOST
the 5 ReCiPe keys named in EF_TO_RECIPE_DIRECT (and nothing else).

Scans every row of the catalog and reports:
  - the union of all ReCiPe keys observed across the catalog,
  - per-row counts (how many rows carry 0, 1, 2, ..., 5 keys),
  - any "outlier" key not in EF_TO_RECIPE_DIRECT.values() (would be a bug).
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
for sub in ("environmental_impact_model", "dish_cnf_db_pipeline"):
    p = os.path.join(_HERE, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

from environmental_impact_model.etl.ef_to_recipe_mapping import EF_TO_RECIPE_DIRECT

CATALOG_PATH = os.path.join(
    _HERE, "environmental_impact_model", "data", "agribalyse_v32_catalog.json"
)

with open(CATALOG_PATH, "r", encoding="utf-8") as fh:
    payload = json.load(fh)
entries = payload.get("entries", payload if isinstance(payload, list) else [])
print(f"Catalog rows: {len(entries)}")
print(f"EF_TO_RECIPE_DIRECT values (expected universe): "
      f"{sorted(EF_TO_RECIPE_DIRECT.values())}")
print()

allowed = set(EF_TO_RECIPE_DIRECT.values())
union_keys: set = set()
per_row_key_count = Counter()
per_key_population_count: Counter = Counter()  # how often each key appears
outlier_keys: Counter = Counter()
empty_recipe_rows = 0
empty_ef_rows = 0

for entry in entries:
    recipe = entry.get("recipe2016_midpoints_per_100g") or {}
    ef = entry.get("ef31_indicators_per_100g") or {}
    if not recipe:
        empty_recipe_rows += 1
    if not ef:
        empty_ef_rows += 1
    union_keys |= set(recipe.keys())
    per_row_key_count[len(recipe)] += 1
    for k in recipe:
        per_key_population_count[k] += 1
        if k not in allowed:
            outlier_keys[k] += 1

print(f"Union of ReCiPe keys observed across all rows: {sorted(union_keys)}")
print(f"  |union| = {len(union_keys)}  vs  |EF_TO_RECIPE_DIRECT| = {len(EF_TO_RECIPE_DIRECT)}")
print()
print(f"Outlier keys (NOT in EF_TO_RECIPE_DIRECT.values()): "
      f"{dict(outlier_keys) if outlier_keys else 'none'}")
print()
print("Distribution of recipe2016_midpoints_per_100g size per row:")
for n in sorted(per_row_key_count):
    print(f"  {n} keys: {per_row_key_count[n]:>5} rows")
print()
print(f"Rows with empty recipe dict : {empty_recipe_rows}")
print(f"Rows with empty EF31 dict   : {empty_ef_rows}")
print()
print("Per-key population (how many of 2,425 rows carry each key):")
for k in sorted(per_key_population_count):
    print(f"  {k:>40}: {per_key_population_count[k]:>5}")

# Strict assertion: matcher overlay can NEVER touch a key outside this set.
assert union_keys.issubset(allowed), (
    f"Catalog has keys outside EF_TO_RECIPE_DIRECT.values(): "
    f"{union_keys - allowed}"
)
print("\nCONFIRMED: every row's recipe overlay is a subset of the 5 EF-direct keys.")
