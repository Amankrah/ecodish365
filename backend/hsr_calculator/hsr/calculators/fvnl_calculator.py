"""FVNL % from CNF row data; nuance rules live in ``rust_core``."""

from ..utils.data_loader import load_cnf_data
from ..providers.threshold_provider import rust_hsr_backend


def calculate_fvnl_content(food_id: int) -> float:
    """
    FVNL (Fruits, Vegetables, Nuts, Legumes) content percentage.

    Loads CNF rows in Python; percentage is computed in Rust.
    """
    food_name_df, _, _, food_group_df = load_cnf_data()

    try:
        food_row = food_name_df[food_name_df["FoodID"] == food_id].iloc[0]
        food_name = food_row["FoodDescription"].lower()
        food_group_id = food_row["FoodGroupID"]

        food_group_row = food_group_df[food_group_df["FoodGroupID"] == food_group_id].iloc[0]
        food_group_code = food_group_row["FoodGroupCode"]

        rust = rust_hsr_backend()
        return float(
            rust.nuanced_fvnl_percent(
                food_name, int(food_group_code), int(food_group_id)
            )
        )

    except (IndexError, KeyError):
        return 0.0
