//! HENI coefficients (mirrors `heni_calculator/heni/config/heni_factors.py`).

use once_cell::sync::Lazy;
use std::collections::HashMap;

pub static HENI_FACTORS: Lazy<HashMap<&'static str, f64>> = Lazy::new(|| {
    let mut m = HashMap::new();
    m.insert("nuts_seeds", 25.0);
    m.insert("whole_grains", 1.7);
    m.insert("fruits", 2.5);
    m.insert("vegetables", 3.2);
    m.insert("milk", 0.15);
    m.insert("sugar_sweetened_beverages", -2.1);
    m.insert("red_meat", -1.5);
    m.insert("processed_meat", -14.2);
    m.insert("omega_3", 57.0);
    m.insert("calcium", 5.1);
    m.insert("fiber", 1.9);
    m.insert("polyunsaturated_fatty_acids", 6.0);
    m.insert("trans_fat", -44.0);
    m.insert("sodium", -8.0);
    m
});

pub static EFFECTIVE_INTAKE_RANGES: Lazy<HashMap<&'static str, (f64, f64)>> = Lazy::new(|| {
    let mut m = HashMap::new();
    m.insert("omega_3", (0.0, 5.0));
    m.insert("calcium", (0.0, 2.5));
    m.insert("fiber", (0.0, 50.0));
    m.insert("polyunsaturated_fatty_acids", (0.0, 30.0));
    m.insert("trans_fat", (0.0, 10.0));
    m.insert("sodium", (0.0, 10.0));
    m.insert("nuts_seeds", (0.0, 50.0));
    m.insert("whole_grains", (0.0, 200.0));
    m.insert("fruits", (0.0, 500.0));
    m.insert("vegetables", (0.0, 500.0));
    m.insert("milk", (0.0, 500.0));
    m.insert("sugar_sweetened_beverages", (0.0, 1000.0));
    m.insert("red_meat", (0.0, 200.0));
    m.insert("processed_meat", (0.0, 100.0));
    m
});

pub static DISEASE_BURDEN_ATTRIBUTION: Lazy<HashMap<&'static str, f64>> = Lazy::new(|| {
    let mut m = HashMap::new();
    m.insert("cardiovascular_diseases", 0.65);
    m.insert("colorectal_cancer", 0.12);
    m.insert("other_cancers", 0.08);
    m.insert("metabolic_disorders", 0.10);
    m.insert("all_cause_mortality", 0.05);
    m
});

pub static RISK_FACTOR_DISEASE_MAPPING: Lazy<HashMap<&'static str, Vec<&'static str>>> =
    Lazy::new(|| {
        let mut m: HashMap<&'static str, Vec<&'static str>> = HashMap::new();
        m.insert("omega_3", vec!["cardiovascular_diseases"]);
        m.insert(
            "calcium",
            vec!["colorectal_cancer", "cardiovascular_diseases"],
        );
        m.insert(
            "fiber",
            vec!["colorectal_cancer", "cardiovascular_diseases"],
        );
        m.insert(
            "polyunsaturated_fatty_acids",
            vec!["cardiovascular_diseases"],
        );
        m.insert("trans_fat", vec!["cardiovascular_diseases"]);
        m.insert("sodium", vec!["cardiovascular_diseases"]);
        m.insert(
            "nuts_seeds",
            vec!["cardiovascular_diseases", "all_cause_mortality"],
        );
        m.insert(
            "whole_grains",
            vec!["cardiovascular_diseases", "metabolic_disorders"],
        );
        m.insert("fruits", vec!["cardiovascular_diseases", "other_cancers"]);
        m.insert(
            "vegetables",
            vec!["cardiovascular_diseases", "other_cancers"],
        );
        m.insert("milk", vec!["colorectal_cancer"]);
        m.insert(
            "sugar_sweetened_beverages",
            vec!["metabolic_disorders", "cardiovascular_diseases"],
        );
        m.insert(
            "red_meat",
            vec!["colorectal_cancer", "cardiovascular_diseases"],
        );
        m.insert(
            "processed_meat",
            vec!["colorectal_cancer", "cardiovascular_diseases"],
        );
        m
    });

pub fn age_adjustment(age_group: &str) -> f64 {
    match age_group {
        "adult_male" => 1.0,
        "adult_female" => 0.95,
        "elderly_male" => 1.15,
        "elderly_female" => 1.10,
        _ => 1.0,
    }
}

pub fn is_nutrient_factor(risk_factor: &str) -> bool {
    matches!(
        risk_factor,
        "omega_3" | "calcium" | "fiber" | "polyunsaturated_fatty_acids"
    )
}
