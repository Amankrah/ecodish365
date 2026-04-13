//! FCS 2.0 attribute classification (mirrors Python `FoodAnalyzer.get_attribute_type`).

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum AttrKind {
    Beneficial,
    Harmful,
    Ratio,
}

pub fn attribute_kind(name: &str) -> Option<AttrKind> {
    match name {
        // Beneficial
        "vitamin_a" | "vitamin_b1" | "vitamin_b2" | "vitamin_b3" | "vitamin_b6" | "vitamin_b9"
        | "vitamin_b12" | "vitamin_c" | "vitamin_d" | "vitamin_e" | "vitamin_k" | "calcium"
        | "phosphorus" | "magnesium" | "iron" | "zinc" | "copper" | "selenium" | "potassium"
        | "manganese" | "chromium" | "molybdenum" | "fruit" | "vegetable" | "beans"
        | "whole_grains" | "nuts" | "seafood" | "yogurt" | "plant_oils" | "alpha_linolenic_acid"
        | "epa_dha" | "mcfas" | "oleic_acid" | "linoleic_acid" | "monounsaturated_fat"
        | "polyunsaturated_fat" | "fiber" | "protein" | "amino_acid_score" | "total_flavonoids"
        | "total_carotenoids" | "anthocyanins" | "isoflavones" | "proanthocyanidins" | "lignans"
        | "choline" | "betaine" | "fermentation" | "minimal_processing" => Some(AttrKind::Beneficial),

        // Harmful
        "added_sugar" | "refined_grains" | "red_or_processed_meat" | "nitrites"
        | "artificial_sweeteners" | "partially_hydrated_oils" | "hydrogenated_oils"
        | "high_fructose_corn_syrup" | "monosodium_glutamate" | "artificial_colors"
        | "preservatives" | "nova_processing" | "frying" | "smoking" | "canning" | "cholesterol"
        | "transfat" | "sodium" | "saturated_fat" | "total_sugars" => Some(AttrKind::Harmful),

        // Ratio
        "unsaturated_to_saturated_fat" | "fiber_to_carbohydrate" | "potassium_to_sodium" => {
            Some(AttrKind::Ratio)
        }

        _ => None,
    }
}
