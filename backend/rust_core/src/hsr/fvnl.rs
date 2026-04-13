//! Nuanced FVNL % — mirrors `fvnl_calculator.py` after CNF row is resolved in Python.

use once_cell::sync::Lazy;
use regex::Regex;

const FVNL_GROUP_CODES: [i32; 4] = [9, 11, 12, 16];

fn in_fvnl_groups(code: i32) -> bool {
    FVNL_GROUP_CODES.contains(&code)
}

static HIGH_PROC: Lazy<Vec<Regex>> = Lazy::new(|| {
    [
        r"\b(battered|breaded|fried|deep.?fried)\b",
        r"\b(candied|sweetened.*syrup|extra heavy syrup)\b",
        r"\b(jam|jelly|preserve|marmalade)\b",
    ]
    .into_iter()
    .map(|p| Regex::new(p).unwrap())
    .collect()
});

static MEDIUM_PROC: Lazy<Vec<Regex>> = Lazy::new(|| {
    [
        r"\bcanned.*(?:heavy syrup|light syrup|syrup pack)\b",
        r"\b(canned|preserved|pickled)\b",
        r"\b(dried|dehydrated|freeze.?dried)\b",
        r"\b(frozen.*sweetened|frozen.*heated)\b",
    ]
    .into_iter()
    .map(|p| Regex::new(p).unwrap())
    .collect()
});

static LIGHT_PROC: Lazy<Vec<Regex>> = Lazy::new(|| {
    [
        r"\bcanned.*(?:water pack|juice pack|no.*sugar)\b",
        r"\b(frozen.*unsweetened|frozen.*unprepared)\b",
        r"\bunsweetened\b",
        r"\b(cooked|boiled|steamed|baked|roasted|grilled|drained)\b",
    ]
    .into_iter()
    .map(|p| Regex::new(p).unwrap())
    .collect()
});

static MINIMAL_PROC: Lazy<Vec<Regex>> = Lazy::new(|| {
    [r"\b(raw|fresh)\b", r"\bwith skin\b", r"\bunprepared\b"]
        .into_iter()
        .map(|p| Regex::new(p).unwrap())
        .collect()
});

fn matches_any(res: &[Regex], s: &str) -> bool {
    res.iter().any(|r| r.is_match(s))
}

fn cnf_processing_factor(food_name: &str) -> f64 {
    if matches_any(&HIGH_PROC, food_name) {
        return 0.5;
    }
    if matches_any(&MEDIUM_PROC, food_name) {
        return 0.75;
    }
    if matches_any(&LIGHT_PROC, food_name) {
        return 0.95;
    }
    if matches_any(&MINIMAL_PROC, food_name) {
        return 1.0;
    }
    0.9
}

fn base_fvnl_for_group(food_group_id: i32, food_name: &str) -> f64 {
    if food_group_id == 9 {
        if ["juice", "nectar", "drink", "cocktail"]
            .iter()
            .any(|t| food_name.contains(t))
        {
            if food_name.contains("concentrate") {
                return 50.0;
            }
            return 67.0;
        }
        if ["dried", "dehydrated"].iter().any(|t| food_name.contains(t)) {
            return 90.0;
        }
        return 100.0;
    }
    if food_group_id == 11 || food_group_id == 12 || food_group_id == 16 {
        return 100.0;
    }
    0.0
}

static FVNL_MIXED: Lazy<Vec<(Regex, f64)>> = Lazy::new(|| {
    let pairs: &[(&str, f64)] = &[
        (
            r"\b(apple|apricot|banana|berry|blueberry|blackberry|cherry|cranberry|grape|grapefruit|lemon|lime|orange|peach|pear|pineapple|plum|strawberry|watermelon|melon)\b",
            45.0,
        ),
        (r"\bfruit\b", 35.0),
        (
            r"\b(tomato|carrot|broccoli|spinach|lettuce|onion|pepper|potato|sweet potato|corn|peas|beans|bean|celery|mushroom|cabbage|cucumber|asparagus)\b",
            40.0,
        ),
        (r"\bvegetable\b", 35.0),
        (
            r"\b(almond|walnut|peanut|cashew|pecan|hazelnut|pine nut|coconut|sesame|sunflower)\b",
            25.0,
        ),
        (r"\bnut\b", 20.0),
        (
            r"\b(lentil|chickpea|kidney bean|lima bean|navy bean|black bean|soy|tofu)\b",
            30.0,
        ),
        (r"\bsalad\b", 70.0),
        (r"\bsoup.*(?:vegetable|tomato|pea|bean|lentil)\b", 45.0),
        (r"\bstir.?fry\b", 35.0),
        (r"\bchow mein\b", 25.0),
        (
            r"\bpot roast.*(?:potato|peas|corn)\b",
            30.0,
        ),
        (
            r"\bsauce.*(?:tomato|onion|pepper|mushroom)\b",
            40.0,
        ),
    ];
    pairs
        .iter()
        .map(|(p, v)| (Regex::new(p).unwrap(), *v))
        .collect()
});

static WITH_VEG: Lazy<Vec<Regex>> = Lazy::new(|| {
    vec![
        Regex::new(r"\bwith.*(?:potato|peas|corn|carrot|onion|pepper|tomato|mushroom|vegetable)\b").unwrap(),
        Regex::new(r"\band.*(?:potato|peas|corn|carrot|onion|pepper|tomato|mushroom|vegetable)\b").unwrap(),
    ]
});

fn estimate_mixed_food_fvnl(food_name: &str, food_group_id: i32) -> f64 {
    let mut max_fvnl = 0.0_f64;
    for (re, val) in FVNL_MIXED.iter() {
        if re.is_match(food_name) {
            max_fvnl = max_fvnl.max(*val);
        }
    }
    for re in WITH_VEG.iter() {
        if re.is_match(food_name) {
            max_fvnl = max_fvnl.max(25.0);
        }
    }

    if food_group_id == 22 {
        if max_fvnl == 0.0 {
            return 5.0;
        }
        return (max_fvnl * 1.2).min(80.0);
    }
    if food_group_id == 6 {
        if [
            "vegetable", "tomato", "onion", "mushroom", "celery",
        ]
        .iter()
        .any(|t| food_name.contains(t))
        {
            return max_fvnl.max(35.0);
        }
        if food_name.contains("soup") && max_fvnl == 0.0 {
            return 10.0;
        }
    }
    if food_group_id == 18 {
        if max_fvnl > 0.0 {
            return (max_fvnl * 0.7).min(60.0);
        }
    }
    if food_group_id == 21 {
        if max_fvnl > 0.0 {
            return (max_fvnl * 0.8).min(50.0);
        }
    }
    max_fvnl
}

fn nuanced_inner(food_name: &str, food_group_code: i32, food_group_id: i32) -> f64 {
    let food_name = food_name.to_lowercase();
    if in_fvnl_groups(food_group_code) {
        let base = base_fvnl_for_group(food_group_id, &food_name);
        let factor = cnf_processing_factor(&food_name);
        return base * factor;
    }
    estimate_mixed_food_fvnl(&food_name, food_group_id)
}

/// Same inputs as `_calculate_nuanced_fvnl` after loading the CNF row in Python.
pub fn nuanced_fvnl_percent(food_name: &str, food_group_code: i32, food_group_id: i32) -> f64 {
    nuanced_inner(food_name, food_group_code, food_group_id)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fruit_group_fresh_apple() {
        let v = nuanced_fvnl_percent("Apple, raw, with skin", 9, 9);
        assert!((v - 100.0).abs() < 1e-9);
    }

    #[test]
    fn fruit_juice_regular() {
        let v = nuanced_fvnl_percent("apple juice, canned", 9, 9);
        assert!((v - 67.0 * 0.75).abs() < 1e-6);
    }

    #[test]
    fn vegetable_hundred() {
        let v = nuanced_fvnl_percent("spinach, raw", 11, 11);
        assert!((v - 100.0).abs() < 1e-9);
    }
}
