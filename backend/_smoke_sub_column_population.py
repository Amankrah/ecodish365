"""Audit: across all 2,425 v32 catalog rows, how often are the three EF climate
sub-components (fossil / biogenic / LUC) populated with a *meaningful* value
versus zero? If most rows are zero, the catalog effectively transfers only
2 ReCiPe categories per food (climate total + stratospheric ozone), and the
manuscript phrase "three published climate sub-components" overstates what
the catalog actually holds.

Also checks the EF accounting identity: in EF 3.1, climate total should equal
fossil + biogenic + LUC. Reports rows where that identity is violated.
"""
from __future__ import annotations

import json
import os
import sys
from statistics import median

_HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_PATH = os.path.join(
    _HERE, "environmental_impact_model", "data", "agribalyse_v32_catalog.json"
)

with open(CATALOG_PATH, "r", encoding="utf-8") as fh:
    payload = json.load(fh)
entries = payload.get("entries", payload if isinstance(payload, list) else [])
print(f"Catalog rows: {len(entries)}\n")

# Population audit -----------------------------------------------------------
TARGET_KEYS = [
    "Global warming",
    "Global warming (fossil)",
    "Global warming (biogenic)",
    "Global warming (LUC)",
    "Stratospheric ozone depletion",
]

zero_counts = {k: 0 for k in TARGET_KEYS}
nonzero_counts = {k: 0 for k in TARGET_KEYS}
nonzero_values: dict = {k: [] for k in TARGET_KEYS}

for e in entries:
    rk = e.get("recipe2016_midpoints_per_100g") or {}
    for k in TARGET_KEYS:
        v = rk.get(k)
        if v is None or v == 0 or v == 0.0:
            zero_counts[k] += 1
        else:
            nonzero_counts[k] += 1
            nonzero_values[k].append(float(v))

print("Per-key population (out of 2,425 rows):")
print(f"  {'key':<40} {'nonzero':>10} {'zero':>10} {'min nz':>12} {'median nz':>12} {'max nz':>12}")
for k in TARGET_KEYS:
    nz = nonzero_values[k]
    nz_min = f"{min(nz):.4g}" if nz else "—"
    nz_med = f"{median(nz):.4g}" if nz else "—"
    nz_max = f"{max(nz):.4g}" if nz else "—"
    print(f"  {k:<40} {nonzero_counts[k]:>10} {zero_counts[k]:>10} {nz_min:>12} {nz_med:>12} {nz_max:>12}")

# Accounting identity: total ?= fossil + biogenic + LUC ----------------------
print("\nEF accounting identity check: total ?= fossil + biogenic + LUC")
exact_match = 0           # |delta| < 1e-9
within_1pct = 0
within_5pct = 0
gross_violation = 0       # |delta|/total > 5%
sub_all_zero_total_nonzero = 0
sample_violations = []

for e in entries:
    rk = e.get("recipe2016_midpoints_per_100g") or {}
    total = rk.get("Global warming")
    f = rk.get("Global warming (fossil)") or 0.0
    b = rk.get("Global warming (biogenic)") or 0.0
    l = rk.get("Global warming (LUC)") or 0.0
    if total is None:
        continue
    sum_sub = f + b + l
    delta = abs(total - sum_sub)
    if delta < 1e-9:
        exact_match += 1
    if total and (delta / abs(total)) <= 0.01:
        within_1pct += 1
    if total and (delta / abs(total)) <= 0.05:
        within_5pct += 1
    if total and (delta / abs(total)) > 0.05:
        gross_violation += 1
        if len(sample_violations) < 10:
            sample_violations.append({
                "ciqual": e.get("ciqual_code"),
                "lci": e.get("lci_name") or e.get("lci_name_fr"),
                "total": total, "fossil": f, "biogenic": b, "LUC": l,
                "sum_sub": sum_sub, "delta": delta,
            })
    if total and total > 0 and (f == 0 and b == 0 and l == 0):
        sub_all_zero_total_nonzero += 1

print(f"  exact match (|delta| < 1e-9)                   : {exact_match:>5}")
print(f"  within 1% of total                              : {within_1pct:>5}")
print(f"  within 5% of total                              : {within_5pct:>5}")
print(f"  gross violation (>5% of total)                  : {gross_violation:>5}")
print(f"  rows w/ total>0 but ALL sub-cols = 0            : {sub_all_zero_total_nonzero:>5}")

if sample_violations:
    print("\nFirst 10 gross-violation rows (informative — beef will sit here):")
    for s in sample_violations:
        print(
            f"  {s['ciqual']:<8} {s['lci'][:42]:<42} "
            f"total={s['total']:.4g}  sum_sub={s['sum_sub']:.4g}  delta={s['delta']:.4g}"
        )

# Beef-stew sanity (ciqual 25065) -------------------------------------------
target = next((e for e in entries if e.get("ciqual_code") == "25065"), None)
if target is not None:
    print("\nDirect look at ciqual 25065 (Beef stew with carrots — the matched row):")
    rk = target.get("recipe2016_midpoints_per_100g") or {}
    for k in TARGET_KEYS:
        print(f"  {k:<40} = {rk.get(k)}")

# Final framing ---------------------------------------------------------------
populated_keys = [k for k in TARGET_KEYS if nonzero_counts[k] > 0]
n_populated_for_typical_row = sum(
    1 for k in TARGET_KEYS if nonzero_counts[k] / len(entries) > 0.5
)
print(
    f"\nEffective ReCiPe-overlay capacity per typical row: "
    f"~{n_populated_for_typical_row} of 5 keys are non-zero in >50% of catalog rows."
)
