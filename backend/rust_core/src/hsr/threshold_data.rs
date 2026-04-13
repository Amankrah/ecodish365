//! Static HSR threshold tables — must match
//! `backend/hsr_calculator/hsr/providers/threshold_provider.py`.

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

// Category 1 — non-dairy beverages
pub static CATEGORY_1: ThresholdBundle = ThresholdBundle {
    energy: &[
        0.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0, 240.0, 270.0, 300.0,
    ],
    saturated_fat: &INF11,
    sugar: &[
        0.0, 1.5, 3.0, 4.5, 6.0, 7.5, 9.0, 10.5, 12.0, 13.5, 15.0,
    ],
    sodium: &[
        0.0, 90.0, 180.0, 270.0, 360.0, 450.0, 540.0, 630.0, 720.0, 810.0, 900.0,
    ],
    fvnl: &[40.0, 60.0, 67.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0],
    protein: &[
        0.0, 0.8, 1.6, 2.4, 3.2, 4.0, 4.8, 5.6, 6.4, 7.2, 8.0,
    ],
    fiber: &INF11,
    star_thresholds: &[4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0],
};

// Category 1D — dairy beverages
pub static CATEGORY_1D: ThresholdBundle = ThresholdBundle {
    energy: &[
        0.0, 80.0, 160.0, 240.0, 320.0, 400.0, 480.0, 560.0, 640.0, 720.0, 800.0,
    ],
    saturated_fat: &[
        0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0,
    ],
    sugar: &[
        0.0, 4.5, 9.0, 13.5, 18.0, 22.5, 27.0, 31.5, 36.0, 40.5, 45.0,
    ],
    sodium: &[
        0.0, 90.0, 180.0, 270.0, 360.0, 450.0, 540.0, 630.0, 720.0, 810.0, 900.0,
    ],
    fvnl: &[40.0, 60.0, 67.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0],
    protein: &[
        0.0, 1.6, 3.2, 4.8, 6.4, 8.0, 9.6, 11.2, 12.8, 14.4, 16.0,
    ],
    fiber: &INF11,
    star_thresholds: &[2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
};

// Category 2 — general foods
pub static CATEGORY_2: ThresholdBundle = ThresholdBundle {
    energy: &[
        0.0, 335.0, 670.0, 1005.0, 1340.0, 1675.0, 2010.0, 2345.0, 2680.0, 3015.0,
        3350.0,
    ],
    saturated_fat: &[
        0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0,
    ],
    sugar: &[
        0.0, 4.5, 9.0, 13.5, 18.0, 22.5, 27.0, 31.5, 36.0, 40.5, 45.0,
    ],
    sodium: &[
        0.0, 90.0, 180.0, 270.0, 360.0, 450.0, 540.0, 630.0, 720.0, 810.0, 900.0,
    ],
    fvnl: &[40.0, 60.0, 67.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0],
    protein: &[
        0.0, 1.6, 3.2, 4.8, 6.4, 8.0, 9.6, 11.2, 12.8, 14.4, 16.0,
    ],
    fiber: &[
        0.0, 0.9, 1.9, 2.8, 3.7, 4.7, 5.6, 6.5, 7.4, 8.4, 9.3,
    ],
    star_thresholds: &[-1.0, 2.0, 5.0, 8.0, 11.0, 14.0, 17.0, 20.0],
};

// Category 2D — dairy foods in category 2 (also used for `Category.CHEESE` in Python)
pub static CATEGORY_2D: ThresholdBundle = ThresholdBundle {
    energy: &[
        0.0, 335.0, 670.0, 1005.0, 1340.0, 1675.0, 2010.0, 2345.0, 2680.0, 3015.0,
        3350.0,
    ],
    saturated_fat: &[
        0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0,
    ],
    sugar: &[
        0.0, 4.5, 9.0, 13.5, 18.0, 22.5, 27.0, 31.5, 36.0, 40.5, 45.0,
    ],
    sodium: &[
        0.0, 90.0, 180.0, 270.0, 360.0, 450.0, 540.0, 630.0, 720.0, 810.0, 900.0,
    ],
    fvnl: &[40.0, 60.0, 67.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0],
    protein: &[
        0.0, 1.6, 3.2, 4.8, 6.4, 8.0, 9.6, 11.2, 12.8, 14.4, 16.0,
    ],
    fiber: &[
        0.0, 0.9, 1.9, 2.8, 3.7, 4.7, 5.6, 6.5, 7.4, 8.4, 9.3,
    ],
    star_thresholds: &[-1.0, 2.0, 5.0, 8.0, 11.0, 14.0, 17.0, 20.0],
};

// Category 3 — oils, spreads, nuts, seeds
pub static CATEGORY_3: ThresholdBundle = ThresholdBundle {
    energy: &[
        0.0, 2100.0, 2200.0, 2300.0, 2400.0, 2500.0, 2600.0, 2700.0, 2800.0, 2900.0,
        3000.0,
    ],
    saturated_fat: &[
        0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0,
    ],
    sugar: &[
        0.0, 4.5, 9.0, 13.5, 18.0, 22.5, 27.0, 31.5, 36.0, 40.5, 45.0,
    ],
    sodium: &[
        0.0, 90.0, 180.0, 270.0, 360.0, 450.0, 540.0, 630.0, 720.0, 810.0, 900.0,
    ],
    fvnl: &[40.0, 60.0, 67.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0],
    protein: &[
        0.0, 1.6, 3.2, 4.8, 6.4, 8.0, 9.6, 11.2, 12.8, 14.4, 16.0,
    ],
    fiber: &[
        0.0, 0.9, 1.9, 2.8, 3.7, 4.7, 5.6, 6.5, 7.4, 8.4, 9.3,
    ],
    star_thresholds: &[0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0],
};

/// Maps `Category.value` strings to the same bundle as `ThresholdProvider.get_thresholds`.
pub fn bundle_for_category_value(category: &str) -> &'static ThresholdBundle {
    match category {
        "1" => &CATEGORY_1,
        "1D" => &CATEGORY_1D,
        // Python uses CHEESE = '3D' but assigns CATEGORY_2D_THRESHOLDS
        "3D" => &CATEGORY_2D,
        "3" => &CATEGORY_3,
        // FOOD ('2'), DAIRY_FOOD ('2D'), and anything else → category 2
        _ => &CATEGORY_2,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn category_1_energy_first_bucket() {
        assert_eq!(CATEGORY_1.energy[1], 30.0);
    }

    #[test]
    fn cheese_gets_2d_sat_fat_scale() {
        let b = bundle_for_category_value("3D");
        assert_eq!(b.saturated_fat[1], 2.0);
        let food = bundle_for_category_value("2");
        assert_eq!(food.saturated_fat[1], 1.0);
    }
}
