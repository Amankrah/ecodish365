//! DALY / HENI numeric core.

use super::factors::{
    age_adjustment, is_nutrient_factor, DISEASE_BURDEN_ATTRIBUTION, EFFECTIVE_INTAKE_RANGES,
    HENI_FACTORS, RISK_FACTOR_DISEASE_MAPPING,
};
use std::collections::HashMap;

const MINUTES_PER_UDALY: f64 = 0.5256;

#[derive(Debug, Clone)]
pub struct HeniComputed {
    pub total_heni_score: f64,
    pub heni_per_100_kcal: f64,
    pub heni_per_100_grams: f64,
    pub heni_per_serving: f64,
    pub food_group_contributions: HashMap<String, f64>,
    pub nutrient_contributions: HashMap<String, f64>,
    pub disease_burden_breakdown: HashMap<String, f64>,
    pub effective_range_warnings: Vec<String>,
    pub health_impact_minutes: f64,
    pub health_impact_description: String,
}

fn effective_amount_and_warning(risk_factor: &str, amount: f64) -> (f64, Option<String>) {
    if let Some(&(min_r, max_r)) = EFFECTIVE_INTAKE_RANGES.get(risk_factor) {
        let _ = min_r;
        if amount > max_r {
            let msg = format!(
                "{}: {:.2}g exceeds effective range (max: {:.2}g)",
                risk_factor, amount, max_r
            );
            let eff = max_r + (amount - max_r) * 0.5;
            return (eff, Some(msg));
        }
        return (amount, None);
    }
    (amount, None)
}

fn disease_breakdown(risk_factor_amounts: &HashMap<String, f64>) -> HashMap<String, f64> {
    let mut disease_breakdown: HashMap<String, f64> = DISEASE_BURDEN_ATTRIBUTION
        .iter()
        .map(|(k, _)| ((*k).to_string(), 0.0))
        .collect();

    for (risk_factor, amount) in risk_factor_amounts {
        let Some(factor) = HENI_FACTORS.get(risk_factor.as_str()) else {
            continue;
        };
        let Some(diseases) = RISK_FACTOR_DISEASE_MAPPING.get(risk_factor.as_str()) else {
            continue;
        };
        let risk_contribution = amount * factor;
        let n = diseases.len() as f64;
        for disease in diseases {
            if let Some(weight) = DISEASE_BURDEN_ATTRIBUTION.get(disease) {
                let key = (*disease).to_string();
                if let Some(acc) = disease_breakdown.get_mut(&key) {
                    *acc += risk_contribution * weight / n;
                }
            }
        }
    }
    disease_breakdown
}

fn health_interpretation(
    health_impact_minutes: f64,
    risk_factor_amounts: &HashMap<String, f64>,
) -> String {
    let (category, mut description): (&str, String) = if health_impact_minutes > 20.0 {
        (
            "Highly Beneficial",
            format!(
                "This food provides significant health benefits, adding approximately {:.1} minutes to healthy life expectancy.",
                health_impact_minutes.abs()
            ),
        )
    } else if health_impact_minutes > 5.0 {
        (
            "Moderately Beneficial",
            format!(
                "This food provides moderate health benefits, adding approximately {:.1} minutes to healthy life expectancy.",
                health_impact_minutes.abs()
            ),
        )
    } else if health_impact_minutes > 0.0 {
        (
            "Mildly Beneficial",
            format!(
                "This food provides mild health benefits, adding approximately {:.1} minutes to healthy life expectancy.",
                health_impact_minutes.abs()
            ),
        )
    } else if health_impact_minutes > -5.0 {
        (
            "Neutral",
            "This food has minimal impact on health outcomes.".to_string(),
        )
    } else if health_impact_minutes > -20.0 {
        (
            "Mildly Detrimental",
            format!(
                "This food may reduce healthy life expectancy by approximately {:.1} minutes.",
                health_impact_minutes.abs()
            ),
        )
    } else {
        (
            "Highly Detrimental",
            format!(
                "This food may significantly reduce healthy life expectancy by approximately {:.1} minutes.",
                health_impact_minutes.abs()
            ),
        )
    };

    let mut dominant: Vec<(String, f64)> = Vec::new();
    for (factor, amount) in risk_factor_amounts {
        if *amount <= 0.0 {
            continue;
        }
        if let Some(hf) = HENI_FACTORS.get(factor.as_str()) {
            let contribution = amount * hf * MINUTES_PER_UDALY;
            if contribution.abs() > 2.0 {
                dominant.push((factor.clone(), contribution));
            }
        }
    }
    dominant.sort_by(|a, b| b.1.abs().partial_cmp(&a.1.abs()).unwrap_or(std::cmp::Ordering::Equal));

    if let Some((top_factor, top_contribution)) = dominant.first() {
        let label = top_factor.replace('_', " ");
        if *top_contribution > 0.0 {
            description.push_str(&format!(" Primary benefit comes from {}.", label));
        } else {
            description.push_str(&format!(" Primary concern is {}.", label));
        }
    }

    format!("{}: {}", category, description)
}

pub fn compute_heni_score(
    risk_factor_amounts: HashMap<String, f64>,
    total_energy_kcal: f64,
    total_weight_grams: f64,
    serving_size_grams: f64,
    age_group: &str,
    apply_age_adjustment: bool,
) -> HeniComputed {
    let mut total_heni = 0.0;
    let mut food_group_contributions: HashMap<String, f64> = HashMap::new();
    let mut nutrient_contributions: HashMap<String, f64> = HashMap::new();
    let mut effective_range_warnings: Vec<String> = Vec::new();

    for (risk_factor, amount) in &risk_factor_amounts {
        let Some(heni_factor) = HENI_FACTORS.get(risk_factor.as_str()) else {
            continue;
        };
        let (effective_amount, warn) = effective_amount_and_warning(risk_factor, *amount);
        if let Some(w) = warn {
            effective_range_warnings.push(w);
        }

        let contribution = effective_amount * heni_factor;
        total_heni += contribution;

        if is_nutrient_factor(risk_factor) {
            nutrient_contributions.insert(risk_factor.clone(), contribution);
        } else {
            food_group_contributions.insert(risk_factor.clone(), contribution);
        }
    }

    if apply_age_adjustment {
        total_heni *= age_adjustment(age_group);
    }

    let heni_per_100_kcal = if total_energy_kcal > 0.0 {
        (total_heni / total_energy_kcal) * 100.0
    } else {
        0.0
    };
    let heni_per_100_grams = if total_weight_grams > 0.0 {
        (total_heni / total_weight_grams) * 100.0
    } else {
        0.0
    };
    let heni_per_serving = if total_weight_grams > 0.0 {
        (total_heni / total_weight_grams) * serving_size_grams
    } else {
        0.0
    };

    let disease_burden_breakdown = disease_breakdown(&risk_factor_amounts);
    let health_impact_minutes = total_heni * MINUTES_PER_UDALY;
    let health_impact_description = health_interpretation(health_impact_minutes, &risk_factor_amounts);

    HeniComputed {
        total_heni_score: total_heni,
        heni_per_100_kcal,
        heni_per_100_grams,
        heni_per_serving,
        food_group_contributions,
        nutrient_contributions,
        disease_burden_breakdown,
        effective_range_warnings,
        health_impact_minutes,
        health_impact_description,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn omega3_only_matches_python_order_of_magnitude() {
        let mut m = HashMap::new();
        m.insert("omega_3".to_string(), 2.0);
        let h = compute_heni_score(m.clone(), 500.0, 200.0, 200.0, "adult_male", true);
        assert!((h.total_heni_score - 2.0 * 57.0).abs() < 1e-9);
        assert!((h.heni_per_100_kcal - (h.total_heni_score / 500.0) * 100.0).abs() < 1e-9);
    }

    #[test]
    fn exceeding_effective_range_applies_diminishing() {
        let mut m = HashMap::new();
        m.insert("omega_3".to_string(), 10.0);
        let h = compute_heni_score(m, 100.0, 100.0, 100.0, "adult_male", true);
        let eff = 5.0 + (10.0 - 5.0) * 0.5;
        let expected = eff * 57.0;
        assert!((h.total_heni_score - expected).abs() < 1e-6);
        assert_eq!(h.effective_range_warnings.len(), 1);
    }
}
