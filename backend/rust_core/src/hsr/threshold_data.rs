//! HSR threshold tables — pinned to HSRC v9.
//!
//! Source: Health Star Rating Advisory Committee. *Health Star Rating System
//! Implementation Guide.* Version 9. Canberra: Australian Government
//! Department of Health, Disability and Ageing; 10 December 2025.
//! Appendix 1, Tables 1–7.
//!
//! v9 ≡ v8 ≡ … ≡ v6 functionally (per v9 Appendix 5: "No policy changes
//! have been made" between v9 and v8). Cumulative v5→v9 differences are
//! limited to (a) Cat 1 energy rows 0–1 (v4, 29 June 2021) and
//! (b) sweet-corn FVNL eligibility (v8, 21 Sept 2023). The first is reflected
//! here; the second is a per-food classification rule handled upstream in
//! `fvnl.rs::nuanced_fvnl_percent` and is logged as a follow-up.
//!
//! ## Encoding convention
//!
//! Each numeric threshold array encodes the v9 ">X earns the next point"
//! semantics. Scoring (in `mod.rs::calculate_hsr_points_inner`) counts the
//! number of leading thresholds the input value *strictly exceeds*:
//!
//! ```text
//! points = |{ t in thresholds : value > t }|, stopping at the first miss.
//! ```
//!
//! For Cat 1 V points (v9 Table 5 uses ≥ semantics) we use `>` with
//! thresholds reduced by 1 (e.g. v9 "≥25" → 24); exact under integer FVNL%.
//! For the "= 100% FVNL → max points" cases (Table 4 row 8, Table 5 row 10)
//! we use 99.0 as the boundary; integer-FVNL values 96–99 score one below
//! max, 100 scores max.
//!
//! Cat 1 baseline energy (v9 Table 3) has no zero-point bucket — ≤31 kJ
//! still earns 1 point. We prepend `NEG_INFINITY` so the first `>` check
//! always succeeds.

use std::f64;

const INF11: [f64; 11] = [f64::INFINITY; 11];

pub struct ThresholdBundle {
    pub energy: &'static [f64],
    pub sugar: &'static [f64],
    pub saturated_fat: &'static [f64],
    pub sodium: &'static [f64],
    pub fvnl: &'static [f64],
    pub protein: &'static [f64],
    pub fiber: &'static [f64],
    pub star_thresholds: &'static [f64],
}

// =============================================================================
// Shared scales (v9 Table 1: Cat 1D, 2, 2D — and Table 2 borrows energy/sodium)
// =============================================================================

/// v9 Table 1 energy thresholds (kJ per 100 g/mL), points 1–11.
static ENERGY_T1: [f64; 11] = [
    335.0, 670.0, 1005.0, 1340.0, 1675.0, 2010.0, 2345.0, 2680.0, 3015.0, 3350.0, 3685.0,
];

/// v9 Table 1 saturated-fat thresholds (g per 100 g/mL), points 1–30.
static SAT_FAT_T1: [f64; 30] = [
    1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.2, 12.5, 13.9, 15.5, 17.3, 19.3, 21.6,
    24.1, 26.9, 30.0, 33.5, 37.4, 41.7, 46.6, 52.0, 58.0, 64.7, 72.3, 80.6, 90.0,
];

/// v9 Table 1 total-sugar thresholds (g per 100 g/mL), points 1–25.
static SUGAR_T1: [f64; 25] = [
    5.0, 8.9, 12.8, 16.8, 20.7, 24.6, 28.5, 32.4, 36.3, 40.3, 44.2, 48.1, 52.0, 55.9, 59.8, 63.8,
    67.7, 71.6, 75.5, 79.4, 83.3, 87.3, 91.2, 95.1, 99.0,
];

/// v9 Table 1 sodium thresholds (mg per 100 g/mL), points 1–30.
static SODIUM_T1: [f64; 30] = [
    90.0, 180.0, 270.0, 360.0, 450.0, 540.0, 630.0, 720.0, 810.0, 900.0, 990.0, 1080.0, 1170.0,
    1260.0, 1350.0, 1440.0, 1530.0, 1620.0, 1710.0, 1800.0, 1890.0, 1980.0, 2070.0, 2160.0,
    2250.0, 2340.0, 2430.0, 2520.0, 2610.0, 2700.0,
];

/// v9 Table 2 saturated-fat thresholds (g per 100 g/mL), points 1–30 — Cat 3 / 3D.
static SAT_FAT_T2: [f64; 30] = [
    1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0,
    18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0,
];

/// v9 Table 2 total-sugar thresholds (g per 100 g/mL), points 1–10 — Cat 3 / 3D.
static SUGAR_T2: [f64; 10] = [
    5.0, 9.0, 13.5, 18.0, 22.5, 27.0, 31.0, 36.0, 40.0, 45.0,
];

// =============================================================================
// Modifying-point scales (v9 Table 4 Col 2, Table 5, Table 6)
// =============================================================================

/// v9 Table 4 Column 2 (%non-concentrated FVNL), points 1–8, for Cat 1D/2/2D/3/3D.
/// The "=100 → 8 pts" boundary is encoded as 99.0 (exact for integer FVNL%).
static FVNL_NON_CONCENTRATED: [f64; 8] = [40.0, 60.0, 67.0, 75.0, 80.0, 90.0, 95.0, 99.0];

/// v9 Table 5 (%FVNL), points 1–10, for Cat 1. v9 uses ≥ semantics; we
/// approximate via `>` with thresholds reduced by 1 unit (exact under
/// integer FVNL%). The "=100 → 10 pts" boundary is encoded as 99.0.
static FVNL_CAT1: [f64; 10] = [24.0, 32.0, 40.0, 48.0, 56.0, 64.0, 72.0, 80.0, 88.0, 99.0];

/// v9 Table 6 protein thresholds (g per 100 g/mL), points 1–15.
static PROTEIN_T6: [f64; 15] = [
    1.6, 3.2, 4.8, 6.4, 8.0, 9.6, 11.6, 13.9, 16.7, 20.0, 24.0, 28.9, 34.7, 41.6, 50.0,
];

/// v9 Table 6 dietary-fibre thresholds (g per 100 g/mL), points 1–15.
static FIBER_T6: [f64; 15] = [
    0.9, 1.9, 2.8, 3.7, 4.7, 5.4, 6.3, 7.3, 8.4, 9.7, 11.2, 13.0, 15.0, 17.3, 20.0,
];

// =============================================================================
// Cat 1 (non-dairy beverages) — v9 Table 3 + Table 5
// =============================================================================

/// v9 Table 3 Cat 1 energy thresholds (kJ per 100 mL). Energy rows 0–10
/// award points 1–11 (no zero-point bucket per Table 3 — even water-level
/// energy earns ≥ 1 point, the v4 fix that caps diet soft drinks at 3.5 stars).
/// Prepend `NEG_INFINITY` so the first comparison always succeeds.
static ENERGY_CAT1: [f64; 11] = [
    f64::NEG_INFINITY,
    31.0, 61.0, 91.0, 121.0, 151.0, 181.0, 211.0, 241.0, 271.0,
    f64::INFINITY,  // Cap: scores above 271 still earn the same 10 pts; no row 11.
];

/// v9 Table 3 Cat 1 sugar thresholds (g per 100 mL), points 1–10.
static SUGAR_CAT1: [f64; 10] = [
    0.1, 1.6, 3.1, 4.6, 6.1, 7.6, 9.1, 10.6, 12.1, 13.6,
];

/// v9 Table 7 Cat 1 star thresholds.
/// Score-to-stars mapping: 5.0/4.5 are reachable only via name override
/// (Water/Unsweetened Flavoured water), so the first two slots are NEG_INFINITY
/// — unreachable numerically. The numeric scale starts at 4.0 = score ≤ 0.
static STAR_THRESHOLDS_CAT1: [f64; 9] = [
    f64::NEG_INFINITY,
    f64::NEG_INFINITY,
    0.0, 1.0, 3.0, 5.0, 7.0, 9.0, 11.0,
];

pub static CATEGORY_1: ThresholdBundle = ThresholdBundle {
    energy: &ENERGY_CAT1,
    saturated_fat: &INF11,
    sugar: &SUGAR_CAT1,
    sodium: &INF11,  // v9 Cat 1 does NOT score sodium (Table 3 has no sodium column).
    fvnl: &FVNL_CAT1,
    protein: &INF11,  // v9 page 26: "Category 1 — Not eligible for HSR P points".
    fiber: &INF11,    // v9 page 27: "Category 1 and 1D — Not eligible for HSR F points".
    star_thresholds: &STAR_THRESHOLDS_CAT1,
};

// =============================================================================
// Cat 1D (dairy beverages) — v9 Table 1 + Table 4 + Table 6
// =============================================================================

static STAR_THRESHOLDS_CAT1D: [f64; 9] =
    [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0];

pub static CATEGORY_1D: ThresholdBundle = ThresholdBundle {
    energy: &ENERGY_T1,
    saturated_fat: &SAT_FAT_T1,
    sugar: &SUGAR_T1,
    sodium: &SODIUM_T1,
    fvnl: &FVNL_NON_CONCENTRATED,
    protein: &PROTEIN_T6,
    fiber: &INF11,  // v9 page 27: Cat 1D not eligible for HSR F points.
    star_thresholds: &STAR_THRESHOLDS_CAT1D,
};

// =============================================================================
// Cat 2 (general foods) — v9 Table 1 + Table 4 + Table 6
// =============================================================================

static STAR_THRESHOLDS_CAT2: [f64; 9] =
    [-11.0, -7.0, -2.0, 2.0, 6.0, 11.0, 15.0, 20.0, 24.0];

pub static CATEGORY_2: ThresholdBundle = ThresholdBundle {
    energy: &ENERGY_T1,
    saturated_fat: &SAT_FAT_T1,
    sugar: &SUGAR_T1,
    sodium: &SODIUM_T1,
    fvnl: &FVNL_NON_CONCENTRATED,
    protein: &PROTEIN_T6,
    fiber: &FIBER_T6,
    star_thresholds: &STAR_THRESHOLDS_CAT2,
};

// =============================================================================
// Cat 2D (other dairy foods, not cheese) — v9 Table 1 + Table 4 + Table 6
// =============================================================================

static STAR_THRESHOLDS_CAT2D: [f64; 9] =
    [-2.0, 0.0, 2.0, 3.0, 5.0, 7.0, 8.0, 10.0, 12.0];

pub static CATEGORY_2D: ThresholdBundle = ThresholdBundle {
    energy: &ENERGY_T1,
    saturated_fat: &SAT_FAT_T1,
    sugar: &SUGAR_T1,
    sodium: &SODIUM_T1,
    fvnl: &FVNL_NON_CONCENTRATED,
    protein: &PROTEIN_T6,
    fiber: &FIBER_T6,
    star_thresholds: &STAR_THRESHOLDS_CAT2D,
};

// =============================================================================
// Cat 3 (oils, spreads, nuts, seeds) — v9 Table 2 + Table 4 + Table 6
// =============================================================================

static STAR_THRESHOLDS_CAT3: [f64; 9] =
    [13.0, 16.0, 20.0, 23.0, 27.0, 30.0, 34.0, 37.0, 41.0];

pub static CATEGORY_3: ThresholdBundle = ThresholdBundle {
    energy: &ENERGY_T1,         // Table 2 shares Table 1's energy thresholds.
    saturated_fat: &SAT_FAT_T2,  // Different from Table 1: uniform 1-g intervals.
    sugar: &SUGAR_T2,            // Different from Table 1: only 10 pts, uniform 4.5-g intervals after 5.
    sodium: &SODIUM_T1,          // Table 2 shares Table 1's sodium thresholds.
    fvnl: &FVNL_NON_CONCENTRATED,
    protein: &PROTEIN_T6,
    fiber: &FIBER_T6,
    star_thresholds: &STAR_THRESHOLDS_CAT3,
};

// =============================================================================
// Cat 3D (cheese / processed cheese) — v9 Table 2 + Table 4 + Table 6
// =============================================================================

static STAR_THRESHOLDS_CAT3D: [f64; 9] =
    [24.0, 26.0, 28.0, 30.0, 31.0, 33.0, 35.0, 37.0, 39.0];

pub static CATEGORY_3D: ThresholdBundle = ThresholdBundle {
    energy: &ENERGY_T1,
    saturated_fat: &SAT_FAT_T2,
    sugar: &SUGAR_T2,
    sodium: &SODIUM_T1,
    fvnl: &FVNL_NON_CONCENTRATED,
    protein: &PROTEIN_T6,
    fiber: &FIBER_T6,
    star_thresholds: &STAR_THRESHOLDS_CAT3D,
};

// =============================================================================
// Category dispatch
// =============================================================================

/// Maps `Category.value` strings to the appropriate v9 threshold bundle.
/// Aliases: any unknown string falls back to Cat 2 (general food).
pub fn bundle_for_category_value(category: &str) -> &'static ThresholdBundle {
    match category {
        "1" => &CATEGORY_1,
        "1D" => &CATEGORY_1D,
        "2D" => &CATEGORY_2D,
        "3" => &CATEGORY_3,
        "3D" => &CATEGORY_3D,
        // "2" (general food) and any other value → Cat 2.
        _ => &CATEGORY_2,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn category_1_energy_prepends_neg_infinity() {
        // v9 Table 3 Cat 1 row 1 = "≤31 → 1 point": even very low energy must
        // earn at least 1 point. We encode this with NEG_INFINITY as the first
        // threshold so the strict-`>` scoring always counts at least 1.
        assert_eq!(CATEGORY_1.energy[0], f64::NEG_INFINITY);
        assert_eq!(CATEGORY_1.energy[1], 31.0);
    }

    #[test]
    fn category_2_uses_table_1_scales() {
        // v9 Table 1 is shared between Cat 1D, 2, 2D for all four baseline nutrients.
        assert_eq!(CATEGORY_2.energy[0], 335.0);
        assert_eq!(CATEGORY_2.saturated_fat[0], 1.0);
        assert_eq!(CATEGORY_2.sugar[0], 5.0);
        assert_eq!(CATEGORY_2.sodium[0], 90.0);
        assert_eq!(CATEGORY_2.saturated_fat.len(), 30);
        assert_eq!(CATEGORY_2.sodium.len(), 30);
        assert_eq!(CATEGORY_2.sugar.len(), 25);
    }

    #[test]
    fn category_3_has_table_2_sugar_and_sat_fat() {
        // v9 Table 2 Cat 3 sugar caps at 10 points (vs Cat 2's 25); sat fat uses
        // uniform 1-g intervals (vs Cat 2's non-uniform).
        assert_eq!(CATEGORY_3.sugar.len(), 10);
        assert_eq!(CATEGORY_3.saturated_fat[10], 11.0); // uniform 1-g
        assert_eq!(CATEGORY_2.saturated_fat[10], 11.2); // Cat 2 non-uniform
    }

    #[test]
    fn category_3d_distinct_from_2d() {
        // Pre-audit, Cat 3D aliased to Cat 2D. v9 Table 7 distinguishes them.
        assert_eq!(CATEGORY_3D.star_thresholds, &[24.0, 26.0, 28.0, 30.0, 31.0, 33.0, 35.0, 37.0, 39.0]);
        assert_ne!(CATEGORY_3D.star_thresholds, CATEGORY_2D.star_thresholds);
    }

    #[test]
    fn category_2_star_thresholds_reach_v9_top_band() {
        // v9 Table 7 Cat 2: final_score ≤ −11 → 5.0 stars. Our array must
        // include −11 as its first element.
        assert_eq!(CATEGORY_2.star_thresholds[0], -11.0);
        assert_eq!(CATEGORY_2.star_thresholds.len(), 9);
    }

    #[test]
    fn bundle_for_category_value_routes_correctly() {
        assert!(std::ptr::eq(bundle_for_category_value("1"), &CATEGORY_1));
        assert!(std::ptr::eq(bundle_for_category_value("1D"), &CATEGORY_1D));
        assert!(std::ptr::eq(bundle_for_category_value("2"), &CATEGORY_2));
        assert!(std::ptr::eq(bundle_for_category_value("2D"), &CATEGORY_2D));
        assert!(std::ptr::eq(bundle_for_category_value("3"), &CATEGORY_3));
        assert!(std::ptr::eq(bundle_for_category_value("3D"), &CATEGORY_3D));
        // Default → Cat 2.
        assert!(std::ptr::eq(bundle_for_category_value("xx"), &CATEGORY_2));
    }
}
