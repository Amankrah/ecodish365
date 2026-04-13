"""
HENI risk-factor **names** used in Python (CNF mapping, rule/LLM categorizers).

**Numeric weights, effective ranges, and disease attribution** are canonical in Rust only:
``backend/rust_core/src/heni/factors.rs`` and ``engine.rs`` (exposed as ``rust_core.heni.compute_heni``).

``HENI_FACTORS`` remains a **keys-only** dict so legacy ``key in HENI_FACTORS`` checks keep working;
do not use dict values for scoring.
"""

HENI_RISK_FACTOR_KEYS = frozenset(
    {
        "nuts_seeds",
        "whole_grains",
        "fruits",
        "vegetables",
        "milk",
        "sugar_sweetened_beverages",
        "red_meat",
        "processed_meat",
        "omega_3",
        "calcium",
        "fiber",
        "polyunsaturated_fatty_acids",
        "trans_fat",
        "sodium",
    }
)

HENI_FACTORS = dict.fromkeys(sorted(HENI_RISK_FACTOR_KEYS), None)
