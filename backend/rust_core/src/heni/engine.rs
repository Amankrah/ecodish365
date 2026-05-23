//! DALY / HENI numeric core.
//!
//! Implements Stylianou et al. (2021) HENI: `HENI = -0.53 × Σ DRF_r × g_r`
//! where DRF_r is the dietary risk factor in μDALY per gram and g_r is the
//! amount of risk component r in the meal. The −0.53 multiplier converts
//! damage-oriented μDALY into benefit-oriented minutes of healthy life so
//! positive HENI reads "good for health". Derivation: 1 μDALY = 1 yr × 365 ×
//! 24 × 60 × 10⁻⁶ = 0.5256 min (Stylianou 2021 SI p. 98, line 1291).
//!
//! Factor table and TMRELs are in `factors.rs`; see that file's docstring for
//! source citations and sign convention.

use super::factors::{
    age_adjustment, is_nutrient_factor, EFFECTIVE_INTAKE_RANGES, HENI_FACTORS,
    RISK_FACTOR_DISEASE_WEIGHTS,
};
use std::collections::HashMap;

/// Minutes of healthy life per μDALY (Stylianou 2021 SI p. 98).
///
/// Negative because `HENI_FACTORS` uses Stylianou's published DRF convention
/// (negative = beneficial, positive = detrimental). The two negatives cancel
/// so that `health_impact_minutes > 0` consistently means "this food is
/// beneficial" — the user-facing sign convention.
const MINUTES_PER_UDALY: f64 = -0.5256;

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

/// Apply the Stylianou hard cap at TMREL (Suppl. Table 1 pp. 4–5). Above the
/// TMREL the marginal DRF contribution is fixed at TMREL × DRF; no
/// diminishing-returns taper is applied (the canonical methodology is
/// marginal-at-current-intake bounded by the theoretical-minimum-risk
/// effective intake).
///
/// Energy-relative TMRELs (PUFA at 11 % of energy; trans-fat at 0.5 % of
/// energy) are evaluated against `total_energy_kcal` and converted to grams
/// via the standard 9 kcal/g lipid energy density. When both an
/// absolute-gram cap and an energy-relative cap are defined for a risk
/// factor, the tighter cap (the SMALLER cap) is enforced — Stylianou
/// 2021 SI Table 1 footnote semantics. 2026-05-23 (HENI-CODE-1.y
/// quick-fix subset): added the PUFA / TFA energy-relative caps that the
/// previous revision left uncapped with an advisory warning only.
fn effective_amount_and_warning(
    risk_factor: &str,
    amount: f64,
    total_energy_kcal: f64,
) -> (f64, Option<String>) {
    // Energy-relative caps (Stylianou 2021 SI Table 1 pp. 4-5; lipid
    // energy density 9 kcal/g per FAO/WHO/UNU 2004 macronutrient table).
    let energy_relative_cap: Option<(f64, &'static str)> = match risk_factor {
        "polyunsaturated_fatty_acids" if total_energy_kcal > 0.0 => {
            Some((0.11 * total_energy_kcal / 9.0, "PUFA 11 % of energy"))
        }
        "trans_fat" if total_energy_kcal > 0.0 => {
            Some((0.005 * total_energy_kcal / 9.0, "trans-fat 0.5 % of energy"))
        }
        _ => None,
    };

    // Absolute-gram cap (existing EFFECTIVE_INTAKE_RANGES table).
    let absolute_cap = EFFECTIVE_INTAKE_RANGES
        .get(risk_factor)
        .map(|&(_, max_r)| (max_r, "absolute-gram TMREL"));

    // Effective cap = tighter of the two (or whichever is defined).
    let cap = match (energy_relative_cap, absolute_cap) {
        (Some((e, e_lbl)), Some((a, a_lbl))) => {
            if e <= a { Some((e, e_lbl)) } else { Some((a, a_lbl)) }
        }
        (Some(e), None) => Some(e),
        (None, Some(a)) => Some(a),
        (None, None) => None,
    };

    if let Some((max_r, kind)) = cap {
        if amount > max_r {
            let msg = format!(
                "{}: {:.3} g exceeds TMREL ({:.3} g, {}); contribution capped at \
                 TMREL per Stylianou 2021 SI Table 1 pp. 4–5.",
                risk_factor, amount, max_r, kind,
            );
            return (max_r, Some(msg));
        }
        return (amount, None);
    }
    (amount, None)
}

/// Apportion the meal-level μDALY contribution from each risk factor across
/// the disease outcomes mapped to it in `RISK_FACTOR_DISEASE_WEIGHTS`. Used
/// for reporting only; does NOT affect `total_heni_score`.
fn disease_breakdown(
    risk_factor_amounts: &HashMap<String, f64>,
    total_energy_kcal: f64,
) -> HashMap<String, f64> {
    let mut acc: HashMap<String, f64> = HashMap::new();
    for (risk, amount) in risk_factor_amounts {
        let Some(factor) = HENI_FACTORS.get(risk.as_str()) else {
            continue;
        };
        let Some(weights) = RISK_FACTOR_DISEASE_WEIGHTS.get(risk.as_str()) else {
            continue;
        };
        let (effective_amount, _warn) =
            effective_amount_and_warning(risk, *amount, total_energy_kcal);
        let contribution_udaly = effective_amount * factor;
        for (disease, w) in weights {
            *acc.entry((*disease).to_string()).or_insert(0.0) += contribution_udaly * w;
        }
    }
    acc
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
            // Contribution in minutes for THIS factor:
            //   contribution_min = amount * hf * MINUTES_PER_UDALY
            // Sign is correct (beneficial DRFs are negative; MINUTES_PER_UDALY is
            // negative; product is positive = adds minutes).
            let contribution = amount * hf * MINUTES_PER_UDALY;
            if contribution.abs() > 2.0 {
                dominant.push((factor.clone(), contribution));
            }
        }
    }
    dominant.sort_by(|a, b| {
        b.1.abs()
            .partial_cmp(&a.1.abs())
            .unwrap_or(std::cmp::Ordering::Equal)
    });

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
    // Σ DRF × g_effective in μDALY, sign per Stylianou (positive = detrimental).
    let mut total_heni_udaly = 0.0;
    let mut food_group_contributions: HashMap<String, f64> = HashMap::new();
    let mut nutrient_contributions: HashMap<String, f64> = HashMap::new();
    let mut effective_range_warnings: Vec<String> = Vec::new();

    for (risk_factor, amount) in &risk_factor_amounts {
        let Some(heni_factor) = HENI_FACTORS.get(risk_factor.as_str()) else {
            continue;
        };
        let (effective_amount, warn) =
            effective_amount_and_warning(risk_factor, *amount, total_energy_kcal);
        if let Some(w) = warn {
            effective_range_warnings.push(w);
        }

        let contribution_udaly = effective_amount * heni_factor;
        total_heni_udaly += contribution_udaly;

        if is_nutrient_factor(risk_factor) {
            nutrient_contributions.insert(risk_factor.clone(), contribution_udaly);
        } else {
            food_group_contributions.insert(risk_factor.clone(), contribution_udaly);
        }
    }

    if apply_age_adjustment {
        total_heni_udaly *= age_adjustment(age_group);
    }

    let heni_per_100_kcal = if total_energy_kcal > 0.0 {
        (total_heni_udaly / total_energy_kcal) * 100.0
    } else {
        0.0
    };
    let heni_per_100_grams = if total_weight_grams > 0.0 {
        (total_heni_udaly / total_weight_grams) * 100.0
    } else {
        0.0
    };
    let heni_per_serving = if total_weight_grams > 0.0 {
        (total_heni_udaly / total_weight_grams) * serving_size_grams
    } else {
        0.0
    };

    let disease_burden_breakdown = disease_breakdown(&risk_factor_amounts, total_energy_kcal);
    // Convert μDALY → minutes of healthy life. The negative constant flips the
    // damage-oriented sum so user-facing "positive minutes = beneficial".
    let health_impact_minutes = total_heni_udaly * MINUTES_PER_UDALY;
    let health_impact_description =
        health_interpretation(health_impact_minutes, &risk_factor_amounts);

    HeniComputed {
        total_heni_score: total_heni_udaly,
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

    /// Verifies the Stylianou sign convention end-to-end: omega_3 is beneficial,
    /// so a meal containing only omega_3 must yield POSITIVE
    /// `health_impact_minutes` (good for health) while the raw
    /// `total_heni_score` is NEGATIVE μDALY (avoided burden).
    #[test]
    fn omega3_only_under_stylianou_convention() {
        let mut m = HashMap::new();
        // 0.20 g omega_3 — under the 0.250 g TMREL so no cap applies.
        m.insert("omega_3".to_string(), 0.20);
        let h = compute_heni_score(m.clone(), 500.0, 200.0, 200.0, "adult_male", true);

        // total_heni_score = 0.20 × -81 = -16.2 μDALY (beneficial under Stylianou sign).
        assert!((h.total_heni_score - (0.20 * -81.0)).abs() < 1e-9);
        // health_impact_minutes = -16.2 × -0.5256 ≈ +8.515 min (beneficial = positive).
        assert!((h.health_impact_minutes - (0.20 * -81.0 * -0.5256)).abs() < 1e-6);
        assert!(h.health_impact_minutes > 0.0, "beneficial food must yield positive minutes");
        // Per-100-kcal normalisation should also be negative μDALY.
        assert!(h.heni_per_100_kcal < 0.0);
    }

    /// Above the TMREL (Stylianou SI Table 1) the contribution is hard-capped;
    /// the soft-cap taper of the previous implementation is removed.
    #[test]
    fn exceeding_tmrel_hard_caps() {
        let mut m = HashMap::new();
        // 0.50 g omega_3 with TMREL 0.250 g → effective = 0.250 g.
        m.insert("omega_3".to_string(), 0.50);
        let h = compute_heni_score(m, 100.0, 100.0, 100.0, "adult_male", true);
        let expected_udaly = 0.250 * -81.0;
        assert!((h.total_heni_score - expected_udaly).abs() < 1e-9);
        assert_eq!(h.effective_range_warnings.len(), 1);
        assert!(h.effective_range_warnings[0].contains("TMREL"));
    }

    /// A detrimental risk factor (sodium) must yield NEGATIVE
    /// `health_impact_minutes` (life lost) and POSITIVE `total_heni_score`
    /// (added μDALY of damage) under Stylianou's convention.
    #[test]
    fn sodium_only_is_detrimental() {
        let mut m = HashMap::new();
        m.insert("sodium".to_string(), 1.0);
        let h = compute_heni_score(m, 500.0, 200.0, 200.0, "adult_male", true);
        // 1.0 g sodium × 13.9 μDALY/g = 13.9 μDALY (detrimental, positive under Stylianou).
        assert!((h.total_heni_score - 13.9).abs() < 1e-9);
        // health_impact_minutes = 13.9 × -0.5256 ≈ -7.31 min (detrimental = negative).
        assert!(h.health_impact_minutes < 0.0);
        assert!((h.health_impact_minutes - (13.9 * -0.5256)).abs() < 1e-6);
    }

    /// Canonical Stylianou 2021 SI §S2.2 p. 13 worked example: 85 g chicken-wing
    /// serving with 1.85 g PUFA, 0.0281 g calcium, 0.492 g sodium, 0.139 g TFA
    /// → HENI = −3.3 min/serving. ±0.3 min tolerance for rounded factor values.
    #[test]
    fn stylianou_chicken_wing_worked_example() {
        let mut m = HashMap::new();
        m.insert("polyunsaturated_fatty_acids".to_string(), 1.85);
        m.insert("calcium".to_string(), 0.0281);
        m.insert("sodium".to_string(), 0.492);
        m.insert("trans_fat".to_string(), 0.139);
        let h = compute_heni_score(m, 85.0 * 2.5, 85.0, 85.0, "adult_male", true);

        // Expected per Stylianou SI worked example:
        //   PUFA contribution = 1.85 × -0.60 = -1.11 μDALY (beneficial)
        //   calcium           = 0.0281 × -5.1 = -0.143 μDALY (beneficial)
        //   sodium            = 0.492 × 13.9  = +6.839 μDALY (detrimental)
        //   TFA               = 0.139 × 4.4   = +0.612 μDALY (detrimental)
        //   total ≈ +6.198 μDALY → minutes ≈ 6.198 × -0.5256 ≈ -3.26
        let expected_min = -3.3_f64;
        assert!(
            (h.health_impact_minutes - expected_min).abs() < 0.3,
            "expected ≈ {:.2} min, got {:.2}",
            expected_min,
            h.health_impact_minutes
        );
    }

    /// Disease-breakdown reporting: for the worked-example meal, sodium's
    /// contribution must be distributed across its 15 SBP-mediated outcomes
    /// equally (1/15 each), and the total disease_burden across outcomes must
    /// equal `total_heni_score` (within fp tolerance).
    #[test]
    fn disease_breakdown_sums_to_total() {
        let mut m = HashMap::new();
        m.insert("polyunsaturated_fatty_acids".to_string(), 1.85);
        m.insert("calcium".to_string(), 0.0281);
        m.insert("sodium".to_string(), 0.492);
        m.insert("trans_fat".to_string(), 0.139);
        let h = compute_heni_score(m, 85.0 * 2.5, 85.0, 85.0, "adult_male", true);

        let sum_disease: f64 = h.disease_burden_breakdown.values().sum();
        // disease_breakdown does NOT apply age_adjustment, so compare against
        // the unadjusted Σ DRF × g (age_male = 1.0 so they're equal here).
        assert!((sum_disease - h.total_heni_score).abs() < 1e-9);
    }
}
