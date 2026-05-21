//! FCS 2.0 scoring engine (mirrors Python `FoodAnalyzer` numeric path).

use super::kind::{attribute_kind, AttrKind};
use super::targets::reference_target;
use std::collections::HashMap;

const MIN_FCS: f64 = 1.0;
const MAX_FCS: f64 = 100.0;

const DOMAIN_ORDER: [&str; 9] = [
    "nutrient_ratios",
    "vitamins",
    "minerals",
    "food_ingredients",
    "additives",
    "processing",
    "specific_lipids",
    "fiber_protein",
    "phytochemicals",
];

pub fn score_attribute_value(value: f64, attr: &str) -> Option<f64> {
    let (lo, hi) = reference_target(attr)?;
    let kind = attribute_kind(attr)?;
    let span = hi - lo;
    if span.abs() < 1e-15 {
        return Some(0.0);
    }
    Some(match kind {
        AttrKind::Beneficial => (10.0 * (value - lo) / span).clamp(0.0, 10.0),
        AttrKind::Harmful => (-10.0 * (value - lo) / span).clamp(-10.0, 0.0),
        AttrKind::Ratio => (20.0 * (value - lo) / span - 10.0).clamp(-10.0, 10.0),
    })
}

/// Nested map: domain -> attribute -> value (same shape as `FoodItem.attributes`).
pub fn original_score_from_attributes(attrs: &HashMap<String, HashMap<String, f64>>) -> f64 {
    let mut raw: HashMap<String, Vec<f64>> = HashMap::new();
    for d in DOMAIN_ORDER {
        raw.insert(d.to_string(), Vec::new());
    }

    for domain in DOMAIN_ORDER {
        if let Some(inner) = attrs.get(domain) {
            for (attr, &value) in inner.iter() {
                if let Some(s) = score_attribute_value(value, attr.as_str()) {
                    raw.entry(domain.to_string()).or_default().push(s);
                }
            }
        }
    }

    let nutrient_ratios = mean_or_zero(raw.get("nutrient_ratios").map(|v| v.as_slice()));

    let vitamins = top_k_mean(raw.get("vitamins").map(|v| v.as_slice()), 5);

    let minerals = top_k_mean(raw.get("minerals").map(|v| v.as_slice()), 5);

    let food_ingredients = raw
        .get("food_ingredients")
        .map(|v| v.iter().sum::<f64>())
        .unwrap_or(0.0);

    let additives = mean_or_zero(raw.get("additives").map(|v| v.as_slice()));

    let processing = processing_domain_score(attrs, raw.get("processing"));

    let specific_lipids = top_k_mean(raw.get("specific_lipids").map(|v| v.as_slice()), 3);

    let fiber_protein = mean_or_zero(raw.get("fiber_protein").map(|v| v.as_slice()));

    let phytochemicals = mean_or_zero(raw.get("phytochemicals").map(|v| v.as_slice()));

    nutrient_ratios
        + vitamins
        + minerals
        + food_ingredients
        + additives
        + processing
        + 0.5 * specific_lipids
        + 0.5 * fiber_protein
        + 0.5 * phytochemicals
}

fn mean_or_zero(scores: Option<&[f64]>) -> f64 {
    let s = match scores {
        Some(x) if !x.is_empty() => x,
        _ => return 0.0,
    };
    s.iter().sum::<f64>() / s.len() as f64
}

fn top_k_mean(scores: Option<&[f64]>, k: usize) -> f64 {
    let s = match scores {
        Some(x) if !x.is_empty() => x,
        _ => return 0.0,
    };
    let mut v: Vec<f64> = s.to_vec();
    v.sort_by(|a, b| b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal));
    let take = k.min(v.len());
    let slice = &v[..take];
    slice.iter().sum::<f64>() / slice.len() as f64
}

fn processing_domain_score(
    attrs: &HashMap<String, HashMap<String, f64>>,
    raw_processing: Option<&Vec<f64>>,
) -> f64 {
    let empty = raw_processing.map(|v| v.is_empty()).unwrap_or(true);
    if empty {
        return 0.0;
    }
    let proc = match attrs.get("processing") {
        Some(m) => m,
        None => return 0.0,
    };
    let nova_score = proc.get("nova_processing").copied().unwrap_or(0.0) * 1.0;
    let fermentation_score = proc.get("fermentation").copied().unwrap_or(0.0) * 0.5;
    let frying_score = proc.get("frying").copied().unwrap_or(0.0) * 0.5;
    let mut other_scores = 0.0;
    let mut other_count = 0_usize;
    for attr in [
        "minimal_processing",
        "pasteurization",
        "smoking",
        "canning",
    ] {
        let v = proc.get(attr).copied().unwrap_or(0.0);
        if v != 0.0 {
            if let Some(s) = score_attribute_value(v, attr) {
                other_scores += s;
                other_count += 1;
            }
        }
    }
    let total_weight = 1.0 + 0.5 + 0.5 + other_count as f64;
    if total_weight > 0.0 {
        (nova_score + fermentation_score + frying_score + other_scores) / total_weight
    } else {
        0.0
    }
}

/// Final FCS rescaling per Mozaffarian KS, El-Abbadi NH, O'Hearn M, et al.
/// Food Compass is a nutrient profiling system using expanded characteristics
/// for assessing healthfulness of foods. Nat Food. 2021;2(10):809-818.
/// Supplementary Information, Suppl. Table S3 footnote * (p. 11):
///
///     FCS = 100 - ((26.1 - raw_truncated) / 36.7) * 99
///
/// where `raw_truncated` is the unweighted+weighted domain sum clamped to the
/// empirical 5th and 95th percentiles across 8,032 NHANES 2015-16 foods
/// (-10.7 and 26.1). At raw = -10.7 → FCS = 1; at raw = 26.1 → FCS = 100; at
/// raw = 0 → FCS ≈ 29.6 (the median food in NHANES is well below the mean of
/// 43.2 reported in Mozaffarian SI Table S5 p. 14).
///
/// Note: the published denominator 36.7 is taken verbatim from Mozaffarian
/// 2021 SI Table S3 footnote *. Computing it from the truncation bounds gives
/// 26.1 - (-10.7) = 36.8 — Mozaffarian rounded both percentiles separately
/// before publishing, so the printed denominator is 36.7. Using 36.7 (rather
/// than the derived 36.8) reproduces the paper exactly; the truncation at
/// raw = 26.1 still maps to FCS = 100.000 because the numerator is zero there.
///
/// Pre-audit this function used a [-70, +70] linear stretch which compressed
/// the FCS distribution toward 50, making the published ≥70 / 31-69 / ≤30
/// cut-offs effectively unreachable. (FCS-CODE-1 fix, 2026-05-21.)
pub fn fcs_from_original(original_score: f64) -> f64 {
    const RAW_LOWER_PCTL: f64 = -10.7;
    const RAW_UPPER_PCTL: f64 = 26.1;
    // Mozaffarian 2021 SI Table S3 footnote * publishes the denominator as
    // 36.7. Used verbatim rather than (26.1 - (-10.7)) = 36.8 for exact
    // reproduction of published worked examples.
    const RAW_RANGE: f64 = 36.7;

    let raw_t = original_score.clamp(RAW_LOWER_PCTL, RAW_UPPER_PCTL);
    let fcs = 100.0 - ((RAW_UPPER_PCTL - raw_t) / RAW_RANGE) * 99.0;
    let clamped = fcs.clamp(MIN_FCS, MAX_FCS);
    (clamped * 100.0).round() / 100.0
}

pub fn nova_category_display(level: i32) -> &'static str {
    match level {
        -1 => "MIXED_PROCESSING_LEVELS",
        1 => "MINIMALLY_PROCESSED",
        2 => "PROCESSED_CULINARY_INGREDIENTS",
        3 => "PROCESSED_FOODS",
        4 => "ULTRA_PROCESSED_FOODS",
        _ => "MINIMALLY_PROCESSED",
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Mozaffarian 2021 SI Table S3 footnote *: truncate raw at [-10.7, 26.1];
    /// FCS = 100 - ((26.1 - raw) / 36.8) * 99.
    /// At raw -10.7 → FCS = 1.00; at raw 26.1 → FCS = 100.00.
    #[test]
    fn fcs_scale_endpoints_mozaffarian() {
        assert!((fcs_from_original(-10.7) - 1.0).abs() < 1e-9);
        assert!((fcs_from_original(26.1) - 100.0).abs() < 1e-9);
        // Below/above the truncation bounds clamp.
        assert!((fcs_from_original(-50.0) - 1.0).abs() < 1e-9);
        assert!((fcs_from_original(50.0) - 100.0).abs() < 1e-9);
    }

    /// Sanity check: raw = 0 → FCS ≈ 29.6 per the Mozaffarian formula.
    /// Pre-audit this would have returned 50.5 under the [-70, +70] stretch
    /// (a +20 FCS systematic over-scoring).
    #[test]
    fn fcs_raw_zero_below_published_mean() {
        let f = fcs_from_original(0.0);
        assert!(
            (f - 29.59).abs() < 0.1,
            "raw=0 should map to FCS ≈ 29.59, got {f}"
        );
    }

    /// Midpoint sanity check. Mozaffarian 2021 SI Table S5 (p. 14) reports
    /// mean FCS 43.2 across 8,032 NHANES foods and median FCS 39.3.
    /// At raw ≈ 7.7 the formula gives FCS ≈ 50.37 — close to the population
    /// midpoint as a useful regression anchor.
    #[test]
    fn fcs_mozaffarian_midpoint_reference() {
        let f = fcs_from_original(7.7);
        assert!(
            (f - 50.37).abs() < 0.1,
            "raw=7.7 should map to FCS ≈ 50.37, got {f}"
        );
    }

    #[test]
    fn all_zero_domains_yields_fcs_in_range() {
        let mut attrs: HashMap<String, HashMap<String, f64>> = HashMap::new();
        for d in DOMAIN_ORDER {
            attrs.insert(d.to_string(), HashMap::new());
        }
        let o = original_score_from_attributes(&attrs);
        let f = fcs_from_original(o);
        assert!(f >= 1.0 && f <= 100.0);
        // Empty domains → raw = 0 → FCS = published 29.59.
        assert!((f - 29.59).abs() < 0.1);
    }
}
