//! Scientific meal categorization — mirrors ``meal_categorizer.py``.

use std::collections::HashMap;

#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
pub enum Cat {
    B1,
    B1D,
    B2,
    B2D,
    B3D,
    B3,
}

impl Cat {
    pub fn as_str(self) -> &'static str {
        match self {
            Cat::B1 => "1",
            Cat::B1D => "1D",
            Cat::B2 => "2",
            Cat::B2D => "2D",
            Cat::B3D => "3D",
            Cat::B3 => "3",
        }
    }

    pub const ALL: [Cat; 6] = [
        Cat::B1,
        Cat::B1D,
        Cat::B2,
        Cat::B2D,
        Cat::B3D,
        Cat::B3,
    ];
}

pub struct FoodInput {
    pub food_name: String,
    pub serving_size: f64,
    pub nutrients: HashMap<String, f64>,
    pub category_value: Option<String>,
}

#[derive(Clone, Debug)]
pub enum FactorValue {
    Num(f64),
    Str(String),
}

pub struct ScientificOutput {
    pub recommended_category: String,
    pub confidence: f64,
    pub reasoning: Vec<String>,
    pub nutritional_rationale: String,
    pub alternative_categories: Vec<(String, f64, String)>,
    pub scientific_factors: HashMap<String, FactorValue>,
}

fn nget(n: &HashMap<String, f64>, key: &str) -> f64 {
    *n.get(key).unwrap_or(&0.0)
}

fn analyze_meal_nutrition(foods: &[FoodInput]) -> HashMap<String, FactorValue> {
    let total_weight: f64 = foods.iter().map(|f| f.serving_size).sum();
    if total_weight <= 0.0 {
        return empty_nutrition_analysis();
    }

    let mut energy = 0.0;
    let mut protein = 0.0;
    let mut fat_total = 0.0;
    let mut sat_fat = 0.0;
    let mut carbs = 0.0;
    let mut sugars = 0.0;
    let mut fiber = 0.0;
    let mut sodium = 0.0;

    for food in foods {
        let w = food.serving_size;
        let nn = &food.nutrients;
        energy += nget(nn, "ENERGY (KILOCALORIES)") * w / 100.0;
        protein += nget(nn, "PROTEIN") * w / 100.0;
        fat_total += nget(nn, "FAT, TOTAL") * w / 100.0;
        sat_fat += nget(nn, "FATTY ACIDS, SATURATED, TOTAL") * w / 100.0;
        carbs += nget(nn, "CARBOHYDRATE, TOTAL") * w / 100.0;
        sugars += nget(nn, "SUGARS, TOTAL") * w / 100.0;
        fiber += nget(nn, "FIBRE, TOTAL DIETARY") * w / 100.0;
        sodium += nget(nn, "SODIUM") * w / 100.0;
    }
    let d = total_weight / 100.0;
    let energy_kcal = energy / d;
    let protein = protein / d;
    let fat_total = fat_total / d;
    let saturated_fat = sat_fat / d;
    let carbohydrates = carbs / d;
    let sugars = sugars / d;
    let fiber = fiber / d;
    let sodium = sodium / d;

    let liquid_percentage = calculate_liquid_percentage(foods);
    let processing_level = assess_overall_processing_level(foods);
    let natural_content_score = calculate_natural_content_score(foods);
    let satiety_index = meal_satiety_index(protein, fiber, liquid_percentage);
    let nutritional_density = calculate_nutritional_density(energy_kcal, protein, fiber, sugars);

    let mut out = HashMap::new();
    macro_rules! num {
        ($k:expr, $v:expr) => {
            out.insert($k.into(), FactorValue::Num($v));
        };
    }
    num!("energy_kcal", energy_kcal);
    num!("protein", protein);
    num!("fat_total", fat_total);
    num!("saturated_fat", saturated_fat);
    num!("carbohydrates", carbohydrates);
    num!("sugars", sugars);
    num!("fiber", fiber);
    num!("sodium", sodium);
    num!("total_weight", total_weight);
    num!("liquid_percentage", liquid_percentage);
    num!("satiety_index", satiety_index);
    num!("nutritional_density", nutritional_density);
    num!("natural_content_score", natural_content_score);

    out.insert(
        "energy_density_level".into(),
        FactorValue::Str(categorize_energy_density(energy_kcal)),
    );
    out.insert(
        "protein_level".into(),
        FactorValue::Str(categorize_protein_content(protein)),
    );
    out.insert(
        "fat_level".into(),
        FactorValue::Str(categorize_fat_content(fat_total)),
    );
    out.insert(
        "sugar_level".into(),
        FactorValue::Str(categorize_sugar_content(sugars)),
    );
    out.insert(
        "sodium_level".into(),
        FactorValue::Str(categorize_sodium_content(sodium)),
    );
    out.insert(
        "fiber_level".into(),
        FactorValue::Str(categorize_fiber_content(fiber)),
    );
    out.insert(
        "processing_level".into(),
        FactorValue::Str(processing_level),
    );
    out
}

pub fn nutrition_get_num(m: &HashMap<String, FactorValue>, key: &str) -> f64 {
    match m.get(key) {
        Some(FactorValue::Num(x)) => *x,
        _ => 0.0,
    }
}

fn nutrition_get_str(m: &HashMap<String, FactorValue>, key: &str) -> String {
    match m.get(key) {
        Some(FactorValue::Str(s)) => s.clone(),
        _ => "unknown".into(),
    }
}

fn empty_nutrition_analysis() -> HashMap<String, FactorValue> {
    let mut m = HashMap::new();
    for (k, v) in [
        ("energy_kcal", 0.0),
        ("protein", 0.0),
        ("fat_total", 0.0),
        ("saturated_fat", 0.0),
        ("carbohydrates", 0.0),
        ("sugars", 0.0),
        ("fiber", 0.0),
        ("sodium", 0.0),
        ("total_weight", 0.0),
        ("liquid_percentage", 0.0),
        ("satiety_index", 1.0),
        ("natural_content_score", 0.0),
        ("nutritional_density", 0.0),
    ] {
        m.insert(k.into(), FactorValue::Num(v));
    }
    for (k, v) in [
        ("energy_density_level", "unknown"),
        ("protein_level", "unknown"),
        ("fat_level", "unknown"),
        ("sugar_level", "unknown"),
        ("sodium_level", "unknown"),
        ("fiber_level", "unknown"),
        ("processing_level", "unknown"),
    ] {
        m.insert(k.into(), FactorValue::Str(v.into()));
    }
    m
}

fn categorize_energy_density(energy_kcal: f64) -> String {
    if energy_kcal < 100.0 {
        "very_low".into()
    } else if energy_kcal < 200.0 {
        "low".into()
    } else if energy_kcal < 400.0 {
        "moderate".into()
    } else if energy_kcal < 600.0 {
        "high".into()
    } else {
        "very_high".into()
    }
}

fn categorize_protein_content(protein: f64) -> String {
    if protein < 3.0 {
        "very_low".into()
    } else if protein < 8.0 {
        "low".into()
    } else if protein < 15.0 {
        "moderate".into()
    } else if protein < 25.0 {
        "high".into()
    } else {
        "very_high".into()
    }
}

fn categorize_fat_content(fat: f64) -> String {
    if fat < 3.0 {
        "very_low".into()
    } else if fat < 10.0 {
        "low".into()
    } else if fat < 20.0 {
        "moderate".into()
    } else if fat < 35.0 {
        "high".into()
    } else {
        "very_high".into()
    }
}

fn categorize_sugar_content(sugar: f64) -> String {
    if sugar < 5.0 {
        "low".into()
    } else if sugar < 15.0 {
        "moderate".into()
    } else if sugar < 25.0 {
        "high".into()
    } else {
        "very_high".into()
    }
}

fn categorize_sodium_content(sodium: f64) -> String {
    if sodium < 200.0 {
        "low".into()
    } else if sodium < 600.0 {
        "moderate".into()
    } else if sodium < 1000.0 {
        "high".into()
    } else {
        "very_high".into()
    }
}

fn categorize_fiber_content(fiber: f64) -> String {
    if fiber < 2.0 {
        "low".into()
    } else if fiber < 6.0 {
        "moderate".into()
    } else if fiber < 10.0 {
        "high".into()
    } else {
        "very_high".into()
    }
}

fn meal_satiety_index(protein: f64, fiber: f64, liquid_percentage: f64) -> f64 {
    let mut base = 1.0_f64;
    if protein >= 20.0 {
        base *= 1.2;
    } else if protein >= 15.0 {
        base *= 1.15;
    } else if protein >= 10.0 {
        base *= 1.1;
    }
    if fiber >= 10.0 {
        base *= 1.2;
    } else if fiber >= 6.0 {
        base *= 1.15;
    } else if fiber >= 3.0 {
        base *= 1.1;
    }
    if liquid_percentage > 0.5 {
        base *= 0.8;
    } else if liquid_percentage > 0.2 {
        base *= 0.9;
    }
    base.clamp(0.5, 1.5)
}

fn calculate_nutritional_density(
    energy_kcal: f64,
    protein: f64,
    fiber: f64,
    sugars: f64,
) -> f64 {
    if energy_kcal == 0.0 {
        return 0.0;
    }
    let beneficial = protein * 4.0 + fiber * 8.0 + sugars.min(10.0) * 2.0;
    let density = beneficial / energy_kcal * 100.0;
    (density / 50.0).min(1.0)
}

fn assess_overall_processing_level(foods: &[FoodInput]) -> String {
    let mut scores = Vec::new();
    for food in foods {
        let name = food.food_name.to_lowercase();
        let score = if ["raw", "fresh", "whole", "natural"]
            .iter()
            .any(|t| name.contains(t))
        {
            1
        } else if ["canned", "frozen", "dried", "cooked"]
            .iter()
            .any(|t| name.contains(t))
        {
            2
        } else if ["processed", "enriched", "flavored", "instant"]
            .iter()
            .any(|t| name.contains(t))
        {
            3
        } else {
            2
        };
        scores.push(score);
    }
    let avg = scores.iter().sum::<i32>() as f64 / scores.len().max(1) as f64;
    if avg <= 1.3 {
        "minimally_processed".into()
    } else if avg <= 2.3 {
        "processed".into()
    } else {
        "ultra_processed".into()
    }
}

fn calculate_liquid_percentage(foods: &[FoodInput]) -> f64 {
    let total: f64 = foods.iter().map(|f| f.serving_size).sum();
    if total <= 0.0 {
        return 0.0;
    }
    let mut liquid = 0.0_f64;
    for food in foods {
        let name = food.food_name.to_lowercase();
        if ["juice", "drink", "beverage", "milk", "water"]
            .iter()
            .any(|t| name.contains(t))
        {
            liquid += food.serving_size;
        } else if name.contains("soup") {
            liquid += food.serving_size * 0.7;
        }
    }
    liquid / total
}

fn calculate_natural_content_score(foods: &[FoodInput]) -> f64 {
    let mut scores = Vec::new();
    for food in foods {
        let name = food.food_name.to_lowercase();
        let s = if ["fresh", "raw", "whole", "natural", "organic"]
            .iter()
            .any(|t| name.contains(t))
        {
            1.0
        } else if ["fruit", "vegetable", "nut", "seed"]
            .iter()
            .any(|t| name.contains(t))
        {
            0.8
        } else if ["processed", "artificial", "synthetic"]
            .iter()
            .any(|t| name.contains(t))
        {
            0.2
        } else {
            0.5
        };
        scores.push(s);
    }
    scores.iter().sum::<f64>() / scores.len() as f64
}

#[derive(Clone, Copy)]
struct Profile {
    energy: (f64, f64),
    protein: (f64, f64),
    fat: (f64, f64),
    liq_min: Option<f64>,
    liq_max: Option<f64>,
    proc_tol: ProcTol,
}

#[derive(Clone, Copy)]
enum ProcTol {
    Any,
    Processed,
}

fn profile_for_cat(c: Cat) -> Profile {
    use ProcTol::*;
    match c {
        Cat::B1 => Profile {
            energy: (0.0, 200.0),
            protein: (0.0, 3.0),
            fat: (0.0, 1.0),
            liq_min: Some(0.8),
            liq_max: None,
            proc_tol: Processed,
        },
        Cat::B1D => Profile {
            energy: (30.0, 150.0),
            protein: (2.0, 8.0),
            fat: (0.0, 6.0),
            liq_min: Some(0.7),
            liq_max: None,
            proc_tol: Processed,
        },
        Cat::B2 => Profile {
            energy: (50.0, 800.0),
            protein: (0.0, 50.0),
            fat: (0.0, 50.0),
            liq_min: None,
            liq_max: Some(0.3),
            proc_tol: Any,
        },
        Cat::B2D => Profile {
            energy: (50.0, 400.0),
            protein: (3.0, 30.0),
            fat: (0.0, 25.0),
            liq_min: None,
            liq_max: Some(0.2),
            proc_tol: Processed,
        },
        Cat::B3D => Profile {
            energy: (200.0, 450.0),
            protein: (10.0, 35.0),
            fat: (15.0, 35.0),
            liq_min: None,
            liq_max: Some(0.1),
            proc_tol: Processed,
        },
        Cat::B3 => Profile {
            energy: (300.0, 900.0),
            protein: (0.0, 5.0),
            fat: (30.0, 100.0),
            liq_min: None,
            liq_max: Some(0.2),
            proc_tol: Any,
        },
    }
}

fn evaluate_category_fitness(nutrition: &HashMap<String, FactorValue>) -> HashMap<Cat, f64> {
    let e = nutrition_get_num(nutrition, "energy_kcal");
    let p = nutrition_get_num(nutrition, "protein");
    let f = nutrition_get_num(nutrition, "fat_total");
    let liq = nutrition_get_num(nutrition, "liquid_percentage");
    let proc = nutrition_get_str(nutrition, "processing_level");

    let mut out = HashMap::new();
    for cat in Cat::ALL {
        let profile = profile_for_cat(cat);
        let mut score = 0.0_f64;
        let mut max_score = 0.0_f64;

        let (emin, emax) = profile.energy;
        if emin <= e && e <= emax {
            score += 20.0;
        } else if e < emin {
            score += (20.0 - (emin - e) / 10.0).max(0.0);
        } else {
            score += (20.0 - (e - emax) / 20.0).max(0.0);
        }
        max_score += 20.0;

        let (pmin, pmax) = profile.protein;
        if pmin <= p && p <= pmax {
            score += 15.0;
        } else if p < pmin {
            score += (15.0 - (pmin - p) * 2.0).max(0.0);
        } else {
            score += (15.0 - (p - pmax) / 2.0).max(0.0);
        }
        max_score += 15.0;

        let (fmin, fmax) = profile.fat;
        if fmin <= f && f <= fmax {
            score += 15.0;
        } else if f < fmin {
            score += (15.0 - (fmin - f) * 2.0).max(0.0);
        } else {
            score += (15.0 - (f - fmax) / 3.0).max(0.0);
        }
        max_score += 15.0;

        if let Some(lmin) = profile.liq_min {
            if liq >= lmin {
                score += 25.0;
            } else {
                score += liq / lmin * 25.0;
            }
        } else if let Some(lmax) = profile.liq_max {
            if liq <= lmax {
                score += 25.0;
            } else {
                let excess = liq - lmax;
                score += (25.0 - excess * 50.0).max(0.0);
            }
        }
        max_score += 25.0;

        match profile.proc_tol {
            ProcTol::Any => score += 15.0,
            ProcTol::Processed => {
                if proc != "ultra_processed" {
                    score += 15.0;
                } else {
                    score += 10.0;
                }
            }
        }
        max_score += 15.0;

        if cat == Cat::B3D && p >= 15.0 && f >= 15.0 {
            score += 10.0;
            max_score += 10.0;
        } else if (cat == Cat::B1 || cat == Cat::B1D) && liq > 0.8 {
            score += 10.0;
            max_score += 10.0;
        } else if cat == Cat::B3 && f > 50.0 {
            score += 10.0;
            max_score += 10.0;
        }

        out.insert(cat, if max_score > 0.0 { score / max_score } else { 0.0 });
    }
    out
}

#[derive(Clone, Debug)]
struct ConflictRes {
    has_conflicts: bool,
    tie_breaker: Option<TieBreaker>,
    #[allow(dead_code)]
    top_category: Cat,
    #[allow(dead_code)]
    top_score: f64,
}

#[derive(Clone, Debug)]
struct TieBreaker {
    winner: Cat,
}

fn resolve_conflicts(
    foods: &[FoodInput],
    fitness: &HashMap<Cat, f64>,
    nutrition: &HashMap<String, FactorValue>,
) -> ConflictRes {
    let mut sorted: Vec<(Cat, f64)> = fitness.iter().map(|(c, s)| (*c, *s)).collect();
    sorted.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

    let (top_category, top_score) = sorted[0];
    let mut conflicts = Vec::new();
    for (cat, sc) in sorted.iter().skip(1) {
        if (sc - top_score).abs() < 0.15 {
            conflicts.push((*cat, *sc));
        }
    }

    let tie_breaker = if !conflicts.is_empty() {
        Some(apply_tie_breaking_rules(
            top_category,
            &conflicts,
            foods,
            nutrition,
        ))
    } else {
        None
    };

    ConflictRes {
        has_conflicts: !conflicts.is_empty(),
        tie_breaker,
        top_category,
        top_score,
    }
}

fn apply_tie_breaking_rules(
    top_category: Cat,
    conflicts: &[(Cat, f64)],
    foods: &[FoodInput],
    nutrition: &HashMap<String, FactorValue>,
) -> TieBreaker {
    let mut tb = TieBreaker {
        winner: top_category,
    };

    let liquid_percentage = calculate_liquid_percentage(foods);
    if liquid_percentage > 0.6 {
        for (category, _) in conflicts {
            if *category == Cat::B1 || *category == Cat::B1D {
                tb.winner = *category;
                return tb;
            }
        }
    }

    let p = nutrition_get_num(nutrition, "protein");
    let f = nutrition_get_num(nutrition, "fat_total");
    let e = nutrition_get_num(nutrition, "energy_kcal");
    if p >= 15.0 && f >= 15.0 {
        for (category, _) in conflicts {
            if *category == Cat::B3D || *category == Cat::B2D {
                tb.winner = *category;
                return tb;
            }
        }
    }

    if e > 500.0 && f > 40.0 {
        for (category, _) in conflicts {
            if *category == Cat::B3 {
                tb.winner = Cat::B3;
                return tb;
            }
        }
    }

    for (category, _) in conflicts {
        if *category == Cat::B2 {
            tb.winner = Cat::B2;
            return tb;
        }
    }

    tb
}

fn select_category(cr: &ConflictRes, fitness: &HashMap<Cat, f64>) -> Cat {
    if cr.has_conflicts {
        if let Some(ref tb) = cr.tie_breaker {
            return tb.winner;
        }
    }
    let mut best = Cat::B1;
    let mut best_score = f64::NEG_INFINITY;
    for c in Cat::ALL {
        let s = fitness.get(&c).copied().unwrap_or(0.0);
        if s > best_score {
            best_score = s;
            best = c;
        }
    }
    best
}

fn calculate_confidence(
    recommended: Cat,
    fitness: &HashMap<Cat, f64>,
    nutrition: &HashMap<String, FactorValue>,
) -> f64 {
    let base = fitness.get(&recommended).copied().unwrap_or(0.0);
    let profile = profile_for_cat(recommended);

    let mut bonus = 0.0_f64;
    let e = nutrition_get_num(nutrition, "energy_kcal");
    let liq = nutrition_get_num(nutrition, "liquid_percentage");
    let (emin, emax) = profile.energy;
    if emin <= e && e <= emax {
        bonus += 0.1;
    }
    if let Some(lmin) = profile.liq_min {
        if liq >= lmin {
            bonus += 0.1;
        }
    } else if let Some(lmax) = profile.liq_max {
        if liq <= lmax {
            bonus += 0.1;
        }
    }
    if matches!(profile.proc_tol, ProcTol::Any) {
        bonus += 0.05;
    }

    let mut penalty = 0.0_f64;
    if nutrition_get_num(nutrition, "protein") == 0.0 {
        penalty += 0.05;
    }
    if nutrition_get_num(nutrition, "fiber") == 0.0 {
        penalty += 0.03;
    }

    (base + bonus - penalty).clamp(0.1, 1.0)
}

fn generate_reasoning(
    recommended: Cat,
    nutrition: &HashMap<String, FactorValue>,
    fitness: &HashMap<Cat, f64>,
) -> Vec<String> {
    let mut r = Vec::new();
    let fs = fitness.get(&recommended).copied().unwrap_or(0.0);
    r.push(format!("Best nutritional profile match (fitness: {:.2})", fs));

    let liq = nutrition_get_num(nutrition, "liquid_percentage");
    let ek = nutrition_get_num(nutrition, "energy_kcal");
    let p = nutrition_get_num(nutrition, "protein");
    let f = nutrition_get_num(nutrition, "fat_total");
    let sati = nutrition_get_num(nutrition, "satiety_index");
    let proc = nutrition_get_str(nutrition, "processing_level");

    match recommended {
        Cat::B1 | Cat::B1D => {
            r.push(format!("High liquid content ({:.1}%)", liq * 100.0));
            if ek < 150.0 {
                r.push("Low energy density appropriate for beverages".into());
            }
        }
        Cat::B3D => {
            r.push(format!("High protein ({:.1}g/100g) and fat ({:.1}g/100g)", p, f));
            r.push("Nutritional profile consistent with cheese products".into());
        }
        Cat::B3 => {
            r.push(format!("Very high energy density ({:.0} kcal/100g)", ek));
            r.push(format!("High fat content ({:.1}g/100g)", f));
        }
        Cat::B2 => {
            r.push("Balanced nutritional profile suitable for general food category".into());
            if liq < 0.3 {
                r.push("Predominantly solid food characteristics".into());
            }
        }
        Cat::B2D => {}
    }

    if sati > 1.1 {
        r.push("High satiety index supports solid food categorization".into());
    }
    if proc == "minimally_processed" {
        r.push("Minimally processed foods align with whole food categories".into());
    }
    r
}

fn nutritional_rationale(recommended: Cat, nutrition: &HashMap<String, FactorValue>) -> String {
    let ek = nutrition_get_num(nutrition, "energy_kcal");
    let liq = nutrition_get_num(nutrition, "liquid_percentage");
    let p = nutrition_get_num(nutrition, "protein");
    let f = nutrition_get_num(nutrition, "fat_total");
    match recommended {
        Cat::B1 => format!(
            "Energy density of {:.0} kcal/100g and {:.1}% liquid content align with beverage standards. Low protein ({:.1}g) and fat ({:.1}g) content consistent with typical beverages.",
            ek, liq * 100.0, p, f
        ),
        Cat::B1D => format!(
            "Moderate energy density ({:.0} kcal/100g) with significant liquid content ({:.1}%) and moderate protein ({:.1}g) typical of dairy beverages.",
            ek, liq * 100.0, p
        ),
        Cat::B3D => format!(
            "High energy density ({:.0} kcal/100g) with substantial protein ({:.1}g) and fat ({:.1}g) content characteristic of cheese products. Low liquid content ({:.1}%) confirms solid dairy product classification.",
            ek, p, f, liq * 100.0
        ),
        Cat::B3 => format!(
            "Very high energy density ({:.0} kcal/100g) dominated by fat content ({:.1}g/100g) with minimal protein ({:.1}g) typical of oils and spreads.",
            ek, f, p
        ),
        Cat::B2 => format!(
            "Balanced nutritional profile with {:.0} kcal/100g energy density, {:.1}g protein, and {:.1}g fat. Predominantly solid composition ({:.1}% liquid) suitable for general food category.",
            ek, p, f, liq * 100.0
        ),
        Cat::B2D => format!(
            "Moderate energy density ({:.0} kcal/100g) with good protein content ({:.1}g) and moderate fat ({:.1}g) consistent with dairy food products.",
            ek, p, f
        ),
    }
}

fn alternative_reason(cat: Cat) -> &'static str {
    match cat {
        Cat::B1 => "If considering liquid characteristics primarily",
        Cat::B1D => "If dairy content is significant",
        Cat::B2 => "If treating as general food product",
        Cat::B2D => "If dairy solids are primary component",
        Cat::B3D => "If high protein/fat content is emphasized",
        Cat::B3 => "If fat content dominates nutritional profile",
    }
}

fn identify_alternatives(recommended: Cat, fitness: &HashMap<Cat, f64>) -> Vec<(String, f64, String)> {
    let rec_score = fitness.get(&recommended).copied().unwrap_or(0.0);
    let mut alts = Vec::new();
    for cat in Cat::ALL {
        if cat == recommended {
            continue;
        }
        let score = fitness.get(&cat).copied().unwrap_or(0.0);
        if score < 0.5 {
            continue;
        }
        let diff = rec_score - score;
        let strength = if diff < 0.2 {
            "Strong alternative"
        } else if diff < 0.4 {
            "Viable alternative"
        } else {
            "Possible alternative"
        };
        let reason = alternative_reason(cat);
        alts.push((
            cat.as_str().into(),
            score,
            format!("{}: {}", strength, reason),
        ));
    }
    alts.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
    alts
}

fn single_food_result(food: &FoodInput) -> ScientificOutput {
    let cat = food
        .category_value
        .clone()
        .filter(|s| !s.is_empty())
        .unwrap_or_else(|| "2".into());
    let mut factors = HashMap::new();
    factors.insert(
        "food_name".into(),
        FactorValue::Str(food.food_name.clone()),
    );
    factors.insert("category".into(), FactorValue::Str(cat.clone()));
    factors.insert(
        "serving_size".into(),
        FactorValue::Num(food.serving_size),
    );
    ScientificOutput {
        recommended_category: cat,
        confidence: 1.0,
        reasoning: vec!["Single food item uses pre-assigned category".into()],
        nutritional_rationale: "Individual food categorization maintained".into(),
        alternative_categories: vec![],
        scientific_factors: factors,
    }
}

fn fallback_result(reason: &str) -> ScientificOutput {
    ScientificOutput {
        recommended_category: "2".into(),
        confidence: 0.3,
        reasoning: vec![reason.into()],
        nutritional_rationale: format!("Fallback categorization: {}", reason),
        alternative_categories: vec![],
        scientific_factors: empty_nutrition_analysis(),
    }
}

pub fn determine_scientific_category(foods: &[FoodInput]) -> ScientificOutput {
    if foods.is_empty() {
        return fallback_result("Empty meal");
    }
    if foods.len() == 1 {
        return single_food_result(&foods[0]);
    }

    let nutritional_analysis = analyze_meal_nutrition(foods);
    let category_fitness = evaluate_category_fitness(&nutritional_analysis);
    let conflict_resolution = resolve_conflicts(foods, &category_fitness, &nutritional_analysis);
    let recommended = select_category(&conflict_resolution, &category_fitness);
    let confidence = calculate_confidence(recommended, &category_fitness, &nutritional_analysis);
    let reasoning = generate_reasoning(recommended, &nutritional_analysis, &category_fitness);
    let rationale = nutritional_rationale(recommended, &nutritional_analysis);
    let alternatives = identify_alternatives(recommended, &category_fitness);

    ScientificOutput {
        recommended_category: recommended.as_str().into(),
        confidence,
        reasoning,
        nutritional_rationale: rationale,
        alternative_categories: alternatives,
        scientific_factors: nutritional_analysis,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn food(
        name: &str,
        size: f64,
        kcal: f64,
        protein: f64,
        fat: f64,
    ) -> FoodInput {
        let mut n = HashMap::new();
        n.insert("ENERGY (KILOCALORIES)".into(), kcal);
        n.insert("PROTEIN".into(), protein);
        n.insert("FAT, TOTAL".into(), fat);
        n.insert("FATTY ACIDS, SATURATED, TOTAL".into(), 0.0);
        n.insert("CARBOHYDRATE, TOTAL".into(), 0.0);
        n.insert("SUGARS, TOTAL".into(), 0.0);
        n.insert("FIBRE, TOTAL DIETARY".into(), 0.0);
        n.insert("SODIUM".into(), 0.0);
        FoodInput {
            food_name: name.into(),
            serving_size: size,
            nutrients: n,
            category_value: Some("2".into()),
        }
    }

    #[test]
    fn empty_meal_fallback() {
        let r = determine_scientific_category(&[]);
        assert_eq!(r.recommended_category, "2");
        assert!(r.confidence <= 0.31);
    }

    #[test]
    fn two_foods_runs_multi_path() {
        let foods = vec![
            food("chicken breast cooked", 100.0, 165.0, 31.0, 3.6),
            food("brown rice cooked", 100.0, 123.0, 2.6, 0.9),
        ];
        let r = determine_scientific_category(&foods);
        assert!(!r.recommended_category.is_empty());
        assert!(r.confidence > 0.0);
    }
}
