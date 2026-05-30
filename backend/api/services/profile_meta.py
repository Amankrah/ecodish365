"""Profile score metadata — sample adequacy, kcal estimate, mass drivers."""
from __future__ import annotations

from typing import Any, Dict, List


ENERGY_NUTRIENT_ID = 208


def _estimate_kcal(composition: List[Dict[str, Any]]) -> float:
    try:
        from dish_cnf_db_pipeline.cnf_pipeline import CNFPipeline
        from django.conf import settings

        pipeline = CNFPipeline(settings.CNF_FOLDER)
        na = pipeline.data_loader.nutrient_amount_df
        total = 0.0
        for row in composition:
            fid = int(row['food_id'])
            mass = float(row['mass_g'])
            hit = na[(na['FoodID'] == fid) & (na['NutrientID'] == ENERGY_NUTRIENT_ID)]
            if hit.empty:
                continue
            kcal_per_100 = float(hit.iloc[0]['NutrientValue'])
            total += kcal_per_100 * mass / 100.0
        return round(total, 1)
    except Exception:
        return 0.0


def compute_profile_meta(composition: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Sample adequacy flags + drivers for scorecard UI."""
    n = len(composition)
    total_mass = sum(float(r.get('mass_g') or 0) for r in composition)
    kcal = _estimate_kcal(composition)

    drivers: List[Dict[str, Any]] = []
    if total_mass > 0:
        ranked = sorted(composition, key=lambda r: float(r.get('mass_g') or 0), reverse=True)
        for row in ranked[:3]:
            mass = float(row.get('mass_g') or 0)
            drivers.append({
                'food_id': int(row['food_id']),
                'food_description': row.get('food_description') or f"Food {row['food_id']}",
                'mass_g': mass,
                'mass_share_pct': round(100.0 * mass / total_mass, 1),
            })

    return {
        'total_mass_g': round(total_mass, 1),
        'estimated_kcal': kcal,
        'food_count': n,
        'sample_adequacy': {
            'hefi': {'adequate': kcal >= 1500 or total_mass >= 400, 'note': 'Best with a full day (~1500+ kcal).'},
            'heni': {'adequate': n >= 1 and total_mass >= 50, 'note': 'Population-average estimate.'},
            'hsr': {'adequate': n == 1, 'note': 'Rates one product at a time; multi-food uses energy-weighted average.'},
            'fcs': {'adequate': n >= 1, 'note': 'Treats the list as one combined meal.'},
            'environmental': {'adequate': kcal >= 200 or total_mass >= 100, 'note': 'LCA normalised per 100 kcal when possible.'},
            'dietary_pattern': {'adequate': kcal >= 800 or total_mass >= 250, 'note': 'Pattern matching works best with fuller intake.'},
        },
        'drivers': drivers,
    }
