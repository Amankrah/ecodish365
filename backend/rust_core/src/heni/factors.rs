//! HENI (Health Nutritional Index) characterisation factors.
//!
//! ## Source
//!
//! Stylianou KS, Fulgoni VL III, Jolliet O. *Small targeted dietary changes can
//! yield substantial gains for human health and the environment.* Nat Food.
//! 2021;2(8):616–627. doi:10.1038/s43016-021-00343-4.
//!
//! - **DRF values**: Supplementary Information, Suppl. Table 3 (p. 8) — 16 risk
//!   components (15 GBD 2016 dietary risks + a fibre source split per S2.9 pp.
//!   35–36 to avoid double-counting). μDALY per gram of risk component.
//! - **TMRELs**: Supplementary Information, Suppl. Table 1 (pp. 4–5).
//! - **Disease attribution**: equal-share-per-outcome rederivation from C15-SI
//!   Table 1 (pp. 4–5). The full Stylianou methodology derives per-stratum
//!   weights from the 6,195-pair GBD 2016 RR matrix; rederivation against that
//!   matrix is logged as a follow-up task in `code_action_items.md`
//!   HENI-CODE-1.x.
//!
//! ## Sign convention
//!
//! Stylianou's published DRF convention is **NEGATIVE = beneficial**
//! (consumption reduces disease burden) and **POSITIVE = detrimental**
//! (consumption increases disease burden). The HENI engine multiplies the
//! signed sum Σ DRF × g by `MINUTES_PER_UDALY = -0.5256` so the user-facing
//! `health_impact_minutes` reads "positive minutes = beneficial". See
//! `engine.rs` for the conversion.
//!
//! ## Epidemiology vintage
//!
//! GBD 2016 (the vintage Stylianou et al. 2021 actually used for the Suppl.
//! Table 3 values). GBD 2019 (Cardinaals et al., Front Sustain Food Syst.
//! 2024;8:1304752) and GBD 2023 (with the revised trans-fat TMREL; *Lancet*
//! 2025;406:1873–1922 p. 1880) are documented upgrade paths but not yet
//! implemented.

use once_cell::sync::Lazy;
use std::collections::HashMap;

/// Stylianou et al. 2021 DRF point estimates in μDALY per gram of risk
/// component. 95 % confidence-interval bounds live in `HENI_FACTOR_BOUNDS`.
///
/// Sign convention: negative = beneficial, positive = detrimental. See module
/// docstring.
pub static HENI_FACTORS: Lazy<HashMap<&'static str, f64>> = Lazy::new(|| {
    let mut m = HashMap::new();
    // Beneficial (negative DRF) — Stylianou 2021 SI Table 3 p. 8
    m.insert("omega_3", -81.0); // CI -37 to -110 (EPA + DHA from seafood)
    m.insert("calcium", -5.1); // CI -4.0 to -6.2
    m.insert("nuts_seeds", -1.5); // CI -1.1 to -1.9
    m.insert("fiber_other", -0.99); // CI -0.71 to -1.3 (CRC + IHD)
    m.insert("polyunsaturated_fatty_acids", -0.60); // CI -0.26 to -0.94
    m.insert("whole_grains", -0.34); // CI -0.28 to -0.40
    m.insert("legumes", -0.23); // CI -0.10 to -0.34
    m.insert("fiber_fvlw", -0.19); // CI -0.11 to -0.26 (CRC only)
    m.insert("fruits", -0.18); // CI -0.12 to -0.22
    m.insert("vegetables", -0.083); // CI -0.042 to -0.11
    m.insert("milk", -0.0077); // CI -0.0027 to -0.012 (dairy only)
    // Detrimental (positive DRF) — Stylianou 2021 SI Table 3 p. 8
    m.insert("sugar_sweetened_beverages", 0.066); // CI 0.043 to 0.089
    m.insert("red_meat", 0.099); // CI 0.038 to 0.15
    m.insert("processed_meat", 0.86); // CI 0.41 to 1.1
    m.insert("trans_fat", 4.4); // CI 3.3 to 5.6
    m.insert("sodium", 13.9); // CI 11.5 to 16.1
    m
});

/// Lower and upper 95 % CI bounds for each DRF in `HENI_FACTORS`, in the same
/// sign convention. Used by the Monte Carlo uncertainty layer (manuscript
/// §3.6) to sample log-normal DRF distributions.
pub static HENI_FACTOR_BOUNDS: Lazy<HashMap<&'static str, (f64, f64)>> = Lazy::new(|| {
    let mut m = HashMap::new();
    // (lower_ci, upper_ci) — Stylianou 2021 SI Table 3 p. 8.
    m.insert("omega_3", (-37.0, -110.0));
    m.insert("calcium", (-4.0, -6.2));
    m.insert("nuts_seeds", (-1.1, -1.9));
    m.insert("fiber_other", (-0.71, -1.3));
    m.insert("polyunsaturated_fatty_acids", (-0.26, -0.94));
    m.insert("whole_grains", (-0.28, -0.40));
    m.insert("legumes", (-0.10, -0.34));
    m.insert("fiber_fvlw", (-0.11, -0.26));
    m.insert("fruits", (-0.12, -0.22));
    m.insert("vegetables", (-0.042, -0.11));
    m.insert("milk", (-0.0027, -0.012));
    m.insert("sugar_sweetened_beverages", (0.043, 0.089));
    m.insert("red_meat", (0.038, 0.15));
    m.insert("processed_meat", (0.41, 1.1));
    m.insert("trans_fat", (3.3, 5.6));
    m.insert("sodium", (11.5, 16.1));
    m
});

/// Theoretical-minimum-risk effective intake (TMREL) per risk component, in
/// grams per day. Above the TMREL the marginal DRF contribution is capped:
/// `effective = min(amount, max_r)`.
///
/// Source: Stylianou et al. 2021 Supplementary Information, Suppl. Table 1
/// (pp. 4–5), in turn from Gakidou et al. 2017 (GBD 2016).
///
/// PUFA and trans_fat TMRELs are energy-relative (% of total energy) and
/// therefore not in this absolute-gram table. The engine emits an advisory
/// warning when the per-meal energy share exceeds the published cap but does
/// not modify the contribution. Energy-relative caps are logged as future
/// work.
pub static EFFECTIVE_INTAKE_RANGES: Lazy<HashMap<&'static str, (f64, f64)>> = Lazy::new(|| {
    let mut m = HashMap::new();
    // (min, max_TMREL) in g/day. min is informational; only the max is enforced.
    m.insert("omega_3", (0.0, 0.250)); // 250 mg/day EPA + DHA from seafood
    m.insert("calcium", (0.0, 1.25));
    m.insert("fiber_other", (0.0, 23.5));
    m.insert("fiber_fvlw", (0.0, 23.5));
    m.insert("whole_grains", (0.0, 125.0));
    m.insert("legumes", (0.0, 60.0));
    m.insert("fruits", (0.0, 250.0));
    m.insert("vegetables", (0.0, 360.0));
    m.insert("milk", (0.0, 435.0));
    m.insert("nuts_seeds", (0.0, 20.5));
    m.insert("sodium", (0.0, 3.49)); // urinary→dietary factor 0.85 (Stylianou SI S1.2)
    m.insert("sugar_sweetened_beverages", (0.0, 2.5));
    m.insert("red_meat", (0.0, 22.5));
    m.insert("processed_meat", (0.0, 2.0));
    // PUFA and trans_fat: energy-relative TMRELs (11 % and 0.5 % of energy).
    // Left out of this absolute-gram table on purpose; see module docstring.
    m
});

/// Per-risk-factor disease attribution weights. Values are equal-share per
/// outcome (Σ weights = 1.0 within a risk) derived from Stylianou et al. 2021
/// Supplementary Information, Suppl. Table 1 (pp. 4–5), which lists the
/// disease set associated with each dietary risk. Used by the
/// `disease_breakdown` reporting in `engine.rs`; does NOT affect
/// `total_heni_score`.
///
/// v1 simplification: equal share across all listed outcomes for the risk.
/// The full Stylianou methodology derives per-stratum weights from the
/// 6,195-pair GBD 2016 RR matrix (age × sex × outcome × burden type × modifier);
/// rederivation is logged as HENI-CODE-1.x in `code_action_items.md`.
pub static RISK_FACTOR_DISEASE_WEIGHTS: Lazy<HashMap<&'static str, Vec<(&'static str, f64)>>> =
    Lazy::new(|| {
        let mut m: HashMap<&'static str, Vec<(&'static str, f64)>> = HashMap::new();
        // Beneficial (negative DRF)
        m.insert("omega_3", vec![("ischaemic_heart_disease", 1.00)]);
        m.insert("calcium", vec![("colorectal_cancer", 1.00)]);
        m.insert(
            "fiber_other",
            vec![
                ("ischaemic_heart_disease", 0.50),
                ("colorectal_cancer", 0.50),
            ],
        );
        m.insert("fiber_fvlw", vec![("colorectal_cancer", 1.00)]);
        m.insert(
            "polyunsaturated_fatty_acids",
            vec![("ischaemic_heart_disease", 1.00)],
        );
        m.insert(
            "whole_grains",
            vec![
                ("type_2_diabetes", 0.25),
                ("haemorrhagic_stroke", 0.25),
                ("ischaemic_stroke", 0.25),
                ("ischaemic_heart_disease", 0.25),
            ],
        );
        m.insert("legumes", vec![("ischaemic_heart_disease", 1.00)]);
        m.insert(
            "fruits",
            vec![
                ("colorectal_cancer", 0.10),
                ("ischaemic_heart_disease", 0.10),
                ("haemorrhagic_stroke", 0.10),
                ("ischaemic_stroke", 0.10),
                ("lung_cancer", 0.10),
                ("oesophageal_cancer", 0.10),
                ("mouth_cancer", 0.10),
                ("nasopharynx_cancer", 0.10),
                ("other_pharynx_cancer", 0.10),
                ("larynx_cancer", 0.10),
            ],
        );
        m.insert(
            "vegetables",
            vec![
                ("haemorrhagic_stroke", 1.0 / 3.0),
                ("ischaemic_stroke", 1.0 / 3.0),
                ("ischaemic_heart_disease", 1.0 / 3.0),
            ],
        );
        m.insert("milk", vec![("colorectal_cancer", 1.00)]);
        m.insert(
            "nuts_seeds",
            vec![
                ("type_2_diabetes", 0.50),
                ("ischaemic_heart_disease", 0.50),
            ],
        );
        // Detrimental (positive DRF)
        // Sodium: 15 outcomes mediated via systolic blood pressure
        // (Stylianou SI S1.2 pp. 5–7). Equal share 1/15 across the 15 SBP-mediated
        // outcomes listed in GBD 2016 hypertensive-heart-disease + IHD + stroke
        // family + chronic kidney disease.
        m.insert(
            "sodium",
            vec![
                ("hypertensive_heart_disease", 1.0 / 15.0),
                ("ischaemic_heart_disease", 1.0 / 15.0),
                ("ischaemic_stroke", 1.0 / 15.0),
                ("haemorrhagic_stroke", 1.0 / 15.0),
                ("subarachnoid_stroke", 1.0 / 15.0),
                ("atrial_fibrillation_flutter", 1.0 / 15.0),
                ("aortic_aneurysm", 1.0 / 15.0),
                ("peripheral_artery_disease", 1.0 / 15.0),
                ("rheumatic_heart_disease", 1.0 / 15.0),
                ("endocarditis", 1.0 / 15.0),
                ("non_rheumatic_valvular_disease", 1.0 / 15.0),
                ("cardiomyopathy_myocarditis", 1.0 / 15.0),
                ("chronic_kidney_disease", 1.0 / 15.0),
                ("intracerebral_haemorrhage", 1.0 / 15.0),
                ("other_cardiovascular", 1.0 / 15.0),
            ],
        );
        m.insert("trans_fat", vec![("ischaemic_heart_disease", 1.00)]);
        m.insert(
            "red_meat",
            vec![
                ("type_2_diabetes", 0.50),
                ("colorectal_cancer", 0.50),
            ],
        );
        m.insert(
            "processed_meat",
            vec![
                ("type_2_diabetes", 1.0 / 3.0),
                ("ischaemic_heart_disease", 1.0 / 3.0),
                ("colorectal_cancer", 1.0 / 3.0),
            ],
        );
        // SSB: mediated via BMI; equal share across the 5 highest-burden
        // BMI-mediated outcomes (Stylianou SI S1.2). The full GBD list runs
        // to ~38 outcomes; this v1 simplification preserves rank ordering.
        m.insert(
            "sugar_sweetened_beverages",
            vec![
                ("type_2_diabetes", 0.20),
                ("ischaemic_heart_disease", 0.20),
                ("ischaemic_stroke", 0.20),
                ("hypertensive_heart_disease", 0.20),
                ("colorectal_cancer", 0.20),
            ],
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

/// Stylianou's published "nutrient" vs "food group" split:
/// 6 nutrients (omega-3 seafood, calcium, fibre [split into two source-specific
/// components], PUFA, trans fat, sodium) and 9 food categories (fruits,
/// vegetables, legumes, nuts/seeds, whole grains, milk, red meat, processed
/// meat, SSB beverage). Source: Stylianou 2021 Results pp. 617–618; C18 GBD
/// 2017 Diet Collaborators, Table p. 1960.
pub fn is_nutrient_factor(risk_factor: &str) -> bool {
    matches!(
        risk_factor,
        "omega_3"
            | "calcium"
            | "fiber_other"
            | "fiber_fvlw"
            | "polyunsaturated_fatty_acids"
            | "sodium"
            | "trans_fat"
    )
}
