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
    if food_group_id == 9 && BEVERAGE_RE.is_match(&food_name_lower) {
        return "1";
    }
    if food_group_id == 14 && DAIRY_BEVERAGE_RE.is_match(&food_name_lower) {
        return "1D";
    }
    if OIL_SPREAD_RE.is_match(&food_name_lower) {
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
}
