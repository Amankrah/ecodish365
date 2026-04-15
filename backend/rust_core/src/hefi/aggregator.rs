//! HEFI input aggregation from a pre-indexed meal batch.
//!
//! Mechanical port of
//! `HEFICNFIntegrator.aggregate_inputs` in
//! `backend/hefi_calculator/hefi/cnf_integrator.py`.
//!
//! The pandas-side data access stays in Python — this module assumes the
//! caller has already groupby'd the CNF nutrient table into a
//! `{food_id: {nutrient_name: value_per_100g}}` index and resolved each
//! food_id to `(amount_g, food_group_id, food_description)`. Once that
//! prep work is done, the per-food loop runs entirely in Rust with
//! HashMap O(1) nutrient lookups instead of O(N) pandas filters.
//!
//! RA classification reuses `classifier::classify` directly — no FFI
//! crossings during the hot loop.

use std::collections::HashMap;

use super::classifier::classify;

/// One food row passed in from Python, already resolved against the CNF
/// food table.
pub struct FoodRow<'a> {
    pub food_id: i64,
    pub amount_g: f64,
    pub food_group_id: i32,
    pub food_description: &'a str,
}

/// HEFI inputs produced from a batch of foods. Shape mirrors the dict
/// returned by the Python `aggregate_inputs`.
#[derive(Default, Debug)]
pub struct AggregatedInputs {
    pub total_foods_ra: f64,
    pub vf_ra: f64,
    pub whole_grains_ra: f64,
    pub total_grains_ra: f64,
    pub protein_foods_ra: f64,
    pub plant_protein_foods_ra: f64,
    pub total_beverages_g: f64,
    pub recommended_beverages_g: f64,
    pub energy_kcal: f64,
    pub sfa_g: f64,
    pub mufa_g: f64,
    pub pufa_g: f64,
    pub free_sugars_g: f64,
    pub sodium_mg: f64,
}

// CNF food group constants — must match the Python class constants in
// `HEFICNFIntegrator`. Kept as a private module so the source of truth is
// obvious and diffable.
mod groups {
    pub const FRUITS: i32 = 9;
    pub const VEGETABLES: i32 = 11;
    pub const BEVERAGES: i32 = 14;
    pub const LEGUMES: i32 = 16;
    pub const CEREALS_GRAINS: &[i32] = &[18, 20];
    pub const FINISH_SHELLFISH: i32 = 15;
    pub const NUTS_SEEDS: i32 = 12;
    pub const DAIRY_EGGS: i32 = 1;
    pub const MEAT_PORK_BEEF_POULTRY: &[i32] = &[5, 7, 10, 13, 17];
    pub const FATS_OILS: i32 = 4;
}

fn contains_any(haystack: &str, needles: &[&str]) -> bool {
    needles.iter().any(|n| haystack.contains(n))
}

/// Look up a single nutrient (per-100g) for one food, or 0.0 if missing.
/// Matches Python's `.empty` fallback.
fn nutrient_of(
    nutrients_by_food: &HashMap<i64, HashMap<String, f64>>,
    food_id: i64,
    name: &str,
) -> f64 {
    nutrients_by_food
        .get(&food_id)
        .and_then(|m| m.get(name).copied())
        .unwrap_or(0.0)
}

pub fn aggregate(
    foods: &[FoodRow<'_>],
    nutrients_by_food: &HashMap<i64, HashMap<String, f64>>,
    ra_amounts: &HashMap<String, f64>,
) -> AggregatedInputs {
    let mut out = AggregatedInputs::default();

    // First pass (aligned with Python): nutrients summed per food.
    // `sum_nutr_with_amounts(name)` runs once per nutrient in Python, but the
    // numerics are additive so we can fuse all six nutrients into one loop
    // over `foods` here without changing results.
    for f in foods {
        let amount_over_100 = f.amount_g / 100.0;
        out.energy_kcal +=
            nutrient_of(nutrients_by_food, f.food_id, "ENERGY (KILOCALORIES)") * amount_over_100;
        out.sfa_g += nutrient_of(nutrients_by_food, f.food_id, "FATTY ACIDS, SATURATED, TOTAL")
            * amount_over_100;
        out.mufa_g += nutrient_of(
            nutrients_by_food,
            f.food_id,
            "FATTY ACIDS, MONOUNSATURATED, TOTAL",
        ) * amount_over_100;
        out.pufa_g += nutrient_of(
            nutrients_by_food,
            f.food_id,
            "FATTY ACIDS, POLYUNSATURATED, TOTAL",
        ) * amount_over_100;
        out.free_sugars_g +=
            nutrient_of(nutrients_by_food, f.food_id, "SUGARS, TOTAL") * amount_over_100;
        out.sodium_mg +=
            nutrient_of(nutrients_by_food, f.food_id, "SODIUM") * amount_over_100;
    }
    // Python sets `free_sugars_g = total_sugars_g` — already captured above.

    // Second pass: RA buckets + beverage buckets + total_foods_ra.
    for f in foods {
        let ra_category = classify(f.food_description, f.food_group_id);
        let ra_amount_g = ra_amounts.get(ra_category).copied().unwrap_or(100.0);
        let food_ra = f.amount_g / ra_amount_g;

        let gid = f.food_group_id;
        let desc_upper = f.food_description.to_uppercase();

        // NOTE: elif ordering matches Python exactly. The plant-protein
        // branch for legumes is unreachable (protein branch consumes them
        // first) — preserved to stay bit-identical.
        if gid == groups::FRUITS || gid == groups::VEGETABLES {
            out.vf_ra += food_ra;
        } else if groups::CEREALS_GRAINS.contains(&gid) {
            out.total_grains_ra += food_ra;
            if contains_any(&desc_upper, &["WHOLE", "BROWN", "BRAN", "WHEAT GERM", "OAT"]) {
                out.whole_grains_ra += food_ra;
            }
        } else if groups::MEAT_PORK_BEEF_POULTRY.contains(&gid)
            || gid == groups::FINISH_SHELLFISH
            || gid == groups::DAIRY_EGGS
            || gid == groups::LEGUMES
        {
            out.protein_foods_ra += food_ra;
        } else if gid == groups::LEGUMES || gid == groups::NUTS_SEEDS {
            out.plant_protein_foods_ra += food_ra;
        } else if gid == groups::BEVERAGES {
            out.total_beverages_g += f.amount_g;
            if contains_any(
                &desc_upper,
                &["WATER", "MILK", "SOY DRINK", "SOY MILK", "UNSWEETENED"],
            ) {
                out.recommended_beverages_g += f.amount_g;
            }
        }

        // total_foods_ra excludes beverages and fats/oils (group 4)
        if gid != groups::BEVERAGES && gid != groups::FATS_OILS {
            out.total_foods_ra += food_ra;
        }
    }

    out
}
