"""
HENI risk-factor **names** used in Python (CNF mapping, rule/LLM categorizers).

**Numeric weights, effective ranges, and disease attribution** are canonical in
Rust only: ``backend/rust_core/src/heni/factors.rs`` and ``engine.rs`` (exposed
as ``rust_core.heni.compute_heni``).

The 16-component key set corresponds to the 15 GBD 2016 dietary risks
(GBD 2017 Diet Collaborators, Lancet 2019;393:1960) with fibre source-split
per Stylianou 2021 SI §S2.9 (pp. 35-36) to avoid double-counting the IHD
benefit of fibre from fruit / vegetables / legumes / whole grains.

``HENI_FACTORS`` remains a **keys-only** dict so legacy ``key in HENI_FACTORS``
checks keep working; do not use dict values for scoring.
"""

HENI_RISK_FACTOR_KEYS = frozenset(
    {
        # 8 food groups (Stylianou 2021 Results pp. 617-618)
        "fruits",
        "vegetables",
        "legumes",
        "nuts_seeds",
        "whole_grains",
        "milk",
        "red_meat",
        "processed_meat",
        # SSB (food-group-like but a separate GBD risk)
        "sugar_sweetened_beverages",
        # 7 nutrient factors (with fibre source-split per SI §S2.9)
        "omega_3",
        "calcium",
        "fiber_other",
        "fiber_fvlw",
        "polyunsaturated_fatty_acids",
        "trans_fat",
        "sodium",
    }
)

HENI_FACTORS = dict.fromkeys(sorted(HENI_RISK_FACTOR_KEYS), None)
