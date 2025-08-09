from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class HEFIInputs:
    # Totals expressed in Reference Amounts (RAs) for foods
    total_foods_ra: float
    vf_ra: float  # Vegetables and fruits RAs
    whole_grains_ra: float
    total_grains_ra: float
    protein_foods_ra: float
    plant_protein_foods_ra: float

    # Beverages (in grams)
    total_beverages_g: float
    recommended_beverages_g: float  # water + plain milk/fortified soy drink; placeholder grouping

    # Nutrients (grams except sodium mg) and energy kcal
    energy_kcal: float
    sfa_g: float
    mufa_g: float
    pufa_g: float
    free_sugars_g: float
    sodium_mg: float


@dataclass
class HEFIComponentScores:
    c1_vf: float
    c2_wholegr: float
    c3_grratio: float
    c4_profoods: float
    c5_plantpro: float
    c6_beverages: float
    c7_fattyacid: float
    c8_sfat: float
    c9_freesugars: float
    c10_sodium: float

    @property
    def total(self) -> float:
        return (
            self.c1_vf + self.c2_wholegr + self.c3_grratio + self.c4_profoods +
            self.c5_plantpro + self.c6_beverages + self.c7_fattyacid + self.c8_sfat +
            self.c9_freesugars + self.c10_sodium
        )


@dataclass
class HEFIResult:
    inputs: HEFIInputs
    ratios: Dict[str, float]
    component_scores: HEFIComponentScores
    total_score: float


