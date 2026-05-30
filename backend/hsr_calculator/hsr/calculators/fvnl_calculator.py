"""FVNL % from CNF row data; nuance rules live in ``rust_core``."""

import re

from ..utils.data_loader import load_cnf_data
from ..providers.threshold_provider import rust_hsr_backend


# HSR-CODE-1.x-D — Sweet-corn FVNL eligibility classifier (HSRAC v8 update of
# 21 September 2023). v8 broadened FVNL eligibility so sweet corn counts as
# vegetable for HSR purposes regardless of which food group the data source
# places it in. CNF already routes sweet-corn entries to food group 11
# (Vegetables) where the rust kernel's FVNL_GROUP rule gives them ≥ 95 %; the
# fix is forward-looking insurance for non-CNF sources (WAFCT, packaged-food
# decompositions) that may place sweet corn in a non-vegetable group.
#
# Anchored on the specific phrase "sweet corn" / "corn, sweet" — NOT generic
# "corn" — so corn flakes, corn syrup, corn oil etc. continue to score per
# their actual processing level.
_RE_SWEET_CORN = re.compile(r'(?i)\b(?:sweet\s+corn|corn,\s*sweet)\b')

# CNF food group codes treated as already FVNL-eligible. Mirrors
# `FVNL_GROUP_CODES` in `backend/rust_core/src/hsr/fvnl.rs:6` so the override
# is a no-op when the kernel already handles it.
_FVNL_ELIGIBLE_GROUP_CODES = {9, 11, 12, 16}


def calculate_fvnl_content(food_id: int) -> float:
    """
    FVNL (Fruits, Vegetables, Nuts, Legumes) content percentage.

    Loads CNF rows in Python; percentage is computed in Rust. Sweet-corn
    foods that the data source places outside the FVNL groups get a v8
    override applied here.
    """
    food_name_df, _, _, food_group_df = load_cnf_data()

    try:
        food_row = food_name_df[food_name_df["FoodID"] == food_id].iloc[0]
        food_name = food_row["FoodDescription"].lower()
        food_group_id = food_row["FoodGroupID"]

        food_group_row = food_group_df[food_group_df["FoodGroupID"] == food_group_id].iloc[0]
        food_group_code = food_group_row["FoodGroupCode"]

        rust = rust_hsr_backend()
        raw = float(
            rust.nuanced_fvnl_percent(
                food_name, int(food_group_code), int(food_group_id)
            )
        )

        # HSR-CODE-1.x-D: when the data source placed a sweet-corn food OUTSIDE
        # the FVNL-eligible groups (9, 11, 12, 16), re-evaluate it as if it
        # were in food group 11 (Vegetables). The rust kernel already gives
        # ≥ 95 % for in-group sweet corn; this hook closes the gap for
        # out-of-group placements (WAFCT, packaged-food decompositions, etc.).
        # We DELIBERATELY do not override when the kernel already gave us a
        # value (the in-group rule is more nuanced than re-routing through
        # group 11 here).
        if int(food_group_code) not in _FVNL_ELIGIBLE_GROUP_CODES and _RE_SWEET_CORN.search(food_name):
            override = float(
                rust.nuanced_fvnl_percent(food_name, 11, 11)
            )
            if override > raw:
                return override

        return raw

    except (IndexError, KeyError):
        return 0.0
