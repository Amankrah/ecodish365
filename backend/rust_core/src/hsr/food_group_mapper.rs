//! Mirrors `food_group_mapper.py` — `FoodGroupMapper.get_category` logic.

use once_cell::sync::Lazy;
use regex::Regex;

fn alternation_word_boundary(keywords: &[&str]) -> Regex {
    let mut v: Vec<&str> = keywords.to_vec();
    v.sort_by_key(|k| std::cmp::Reverse(k.len()));
    let inner: String = v
        .iter()
        .map(|k| regex::escape(k))
        .collect::<Vec<_>>()
        .join("|");
    Regex::new(&format!(r"(?i)\b(?:{})\b", inner)).expect("keyword regex")
}

static CHEESE_RE: Lazy<Regex> = Lazy::new(|| {
    alternation_word_boundary(&[
        "cottage cheese",
        "cream cheese",
        "cheese",
        "cheddar",
        "mozzarella",
        "parmesan",
        "brie",
        "camembert",
        "gouda",
        "swiss",
        "blue",
        "feta",
        "ricotta",
        "provolone",
        "gruyere",
    ])
});

static DAIRY_BEVERAGE_RE: Lazy<Regex> = Lazy::new(|| {
    alternation_word_boundary(&[
        "yogurt drink",
        "flavoured milk",
        "chocolate milk",
        "milk shake",
        "dairy drink",
        "buttermilk",
        "kefir",
        "milk",
    ])
});

static BEVERAGE_RE: Lazy<Regex> = Lazy::new(|| {
    alternation_word_boundary(&[
        "beverage",
        "smoothie",
        "lemonade",
        "cocktail",
        "alcohol",
        "coffee",
        "shake",
        "soda",
        "cola",
        "water",
        "tea",
        "juice",
        "drink",
        "beer",
        "wine",
    ])
});

static OIL_SPREAD_RE: Lazy<Regex> = Lazy::new(|| {
    alternation_word_boundary(&[
        "vegetable oil",
        "olive oil",
        "cooking fat",
        "margarine",
        "shortening",
        "spread",
        "butter",
        "ghee",
        "lard",
        "oil",
    ])
});

// FIX (HSR-CATEG-1 2026-05-23): CNF FoodGroup 1 is officially
// "Dairy and Egg Products" — it includes whole eggs, yolks, and whites
// alongside actual dairy. The base rule routes FG1 → Cat 2D (Other dairy
// foods), and our existing keyword overrides only catch dairy / cheese
// keywords. Eggs are NOT dairy under HSRAC v9 — they're general foods
// (Cat 2). This regex catches the egg products in FG1 and reroutes them.
static EGG_RE: Lazy<Regex> = Lazy::new(|| {
    alternation_word_boundary(&[
        "egg",
        "eggs",
        "egg white",
        "egg yolk",
    ])
});

fn base_category_value(food_group_id: i32) -> &'static str {
    match food_group_id {
        1 => "2D",
        4 => "3",
        14 => "1",
        _ => "2",
    }
}

/// Returns `Category.value` (`'1'`, `'1D'`, `'2'`, `'2D'`, `'3'`, `'3D'`).
pub fn food_group_category_value(food_group_id: i32, food_name: &str) -> &'static str {
    let food_name_lower = food_name.to_lowercase();
    let base = base_category_value(food_group_id);

    if food_group_id == 1 && CHEESE_RE.is_match(&food_name_lower) {
        return "3D";
    }
    if food_group_id == 1 && DAIRY_BEVERAGE_RE.is_match(&food_name_lower) {
        return "1D";
    }
    // HSR-CATEG-1 fix: eggs in FG1 are general foods (Cat 2), not dairy (2D).
    // Must run AFTER cheese / dairy-beverage checks (so "Egg, chicken, cheese
    // omelette" — if such a thing existed in CNF FG1 — would still hit cheese
    // first), but BEFORE the base rule that would route FG1 → 2D.
    if food_group_id == 1 && EGG_RE.is_match(&food_name_lower) {
        return "2";
    }
    if food_group_id == 9 && BEVERAGE_RE.is_match(&food_name_lower) {
        return "1";
    }
    if food_group_id == 14 && DAIRY_BEVERAGE_RE.is_match(&food_name_lower) {
        return "1D";
    }
    // FIX (HSR-CATEG-4 2026-05-23): the OIL_SPREAD_RE override previously ran
    // for ANY food_group_id, which mis-routed 10/575 (1.7 %) sampled CNF
    // foods in the stress sweep: foods whose names merely *mentioned* oil /
    // butter / margarine / spread as an ingredient or cooking medium got
    // Cat 3 (Oils and spreads) applied — e.g. "Bread, banana, made with
    // margarine" (FG18), "Fish, anchovy, canned with olive oil, drained"
    // (FG15), "Popcorn, oil-popped" (FG25), "Chicken sandwich spread"
    // (FG7). The override now only fires for FG1 (Dairy & egg), which is
    // the case it was actually needed for — to route Butter from FG1's
    // base "2D" → "3". FG4 (Fats and Oils) foods still reach Cat 3 via
    // the base rule above, so this restriction is loss-less for genuine
    // oils/spreads while eliminating the false-positive long tail.
    if food_group_id == 1 && OIL_SPREAD_RE.is_match(&food_name_lower) {
        return "3";
    }

    base
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn beverage_group14_stays_beverage() {
        assert_eq!(food_group_category_value(14, "spring water"), "1");
    }

    #[test]
    fn milk_is_dairy_beverage() {
        assert_eq!(food_group_category_value(1, "whole milk"), "1D");
    }

    #[test]
    fn cheddar_is_cheese() {
        assert_eq!(food_group_category_value(1, "cheddar cheese"), "3D");
    }

    #[test]
    fn fruit_juice_group9() {
        assert_eq!(food_group_category_value(9, "apple juice drink"), "1");
    }

    #[test]
    fn olive_oil_group4() {
        assert_eq!(food_group_category_value(4, "olive oil extra virgin"), "3");
    }

    // HSR-CATEG-1 fix
    #[test]
    fn egg_in_fg1_is_general_food() {
        assert_eq!(food_group_category_value(1, "Egg, chicken, whole, fresh or frozen, raw"), "2");
        assert_eq!(food_group_category_value(1, "Egg, chicken, white, fresh or frozen, raw"), "2");
        assert_eq!(food_group_category_value(1, "Egg, chicken, yolk, fresh or frozen, raw"), "2");
    }

    #[test]
    fn dairy_not_egg_still_2d() {
        // Plain dairy fall-through unchanged
        assert_eq!(food_group_category_value(1, "Sour cream"), "2D");
    }

    // HSR-CATEG-4 fix: OIL_SPREAD_RE no longer fires outside FG1
    #[test]
    fn oil_spread_keyword_does_not_leak_outside_fg1() {
        // Sandwich spreads in FG7 (Sausages & Luncheon Meats) should stay Cat 2
        assert_eq!(food_group_category_value(7, "Chicken spread, canned"), "2");
        assert_eq!(food_group_category_value(7, "Deli-meat, sandwich spread, ham"), "2");
        // Banana bread mentioning margarine (FG18) should stay Cat 2
        assert_eq!(food_group_category_value(18, "Bread, banana, homemade, made with margarine"), "2");
        // Fish canned with olive oil (FG15) — packing liquid, not the food itself
        assert_eq!(food_group_category_value(15, "Fish, anchovy, european, canned with olive oil, drained solids"), "2");
        // Popcorn cooking method "oil-popped" (FG25)
        assert_eq!(food_group_category_value(25, "Snacks, popcorn, oil-popped, microwave, regular flavour, no trans fat"), "2");
        // Confection mentioning peanut butter (FG19)
        assert_eq!(food_group_category_value(19, "Sweets, confectioner's coating or chips, peanut butter"), "2");
        // Fast-food breakfast with butter as topping (FG21)
        assert_eq!(food_group_category_value(21, "Fast foods, breakfast, french toast with butter"), "2");
    }

    // Butter in FG1 must still route to Cat 3 (this is what the keyword was for)
    #[test]
    fn butter_in_fg1_still_oils_and_spreads() {
        assert_eq!(food_group_category_value(1, "Butter, whipped"), "3");
        assert_eq!(food_group_category_value(1, "Butter, salted"), "3");
    }
}
