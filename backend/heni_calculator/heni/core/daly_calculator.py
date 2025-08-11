"""
DALY Calculator for HENI Score Implementation
Implements the proper Disability Adjusted Life Years methodology as described in the technical report
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from ..config.heni_factors import (
    HENI_FACTORS, 
    DISEASE_BURDEN_ATTRIBUTION,
    RISK_FACTOR_DISEASE_MAPPING,
    EFFECTIVE_INTAKE_RANGES,
    AGE_GENDER_ADJUSTMENTS
)

logger = logging.getLogger(__name__)

@dataclass 
class DALYComponents:
    """Components of DALY calculation: Years of Life Lost (YLL) + Years Lived with Disability (YLD)"""
    yll: float  # Years of Life Lost
    yld: float  # Years Lived with Disability
    total_daly: float  # Total DALY burden
    
    def __post_init__(self):
        self.total_daly = self.yll + self.yld

@dataclass
class HENIResult:
    """Comprehensive HENI calculation result"""
    total_heni_score: float  # Total avoided μDALY
    heni_per_100_kcal: float  # Energy-normalized score
    heni_per_100_grams: float  # Weight-normalized score  
    heni_per_serving: float  # Portion-based score
    
    # Component breakdowns
    food_group_contributions: Dict[str, float]
    nutrient_contributions: Dict[str, float]
    disease_burden_breakdown: Dict[str, float]
    
    # Risk factor analysis
    risk_factor_amounts: Dict[str, float]
    effective_range_warnings: List[str]
    
    # Health interpretation
    health_impact_minutes: float  # Impact in minutes of healthy life
    health_impact_description: str

class DALYCalculator:
    """
    Core DALY calculator implementing the HENI methodology
    Based on: HENI_score = Σ(Risk_Factor_Amount × HENI_Factor)
    """
    
    def __init__(self, age_group: str = "adult_male", gender_adjustment: bool = True):
        self.age_group = age_group
        self.gender_adjustment = gender_adjustment
        self.adjustment_factor = AGE_GENDER_ADJUSTMENTS.get(age_group, 1.0)
    
    def calculate_heni_score(
        self, 
        risk_factor_amounts: Dict[str, float],
        total_energy_kcal: float,
        total_weight_grams: float,
        serving_size_grams: float = 100.0
    ) -> HENIResult:
        """
        Calculate comprehensive HENI score with all components
        
        Args:
            risk_factor_amounts: Dictionary of risk factor amounts in grams
            total_energy_kcal: Total energy content in kilocalories
            total_weight_grams: Total weight in grams
            serving_size_grams: Standard serving size for portion-based calculation
        """
        # Calculate base HENI score
        total_heni = 0.0
        food_group_contributions = {}
        nutrient_contributions = {}
        effective_range_warnings = []
        
        for risk_factor, amount in risk_factor_amounts.items():
            if risk_factor in HENI_FACTORS:
                heni_factor = HENI_FACTORS[risk_factor]
                
                # Check if amount is within effective range
                if risk_factor in EFFECTIVE_INTAKE_RANGES:
                    min_range, max_range = EFFECTIVE_INTAKE_RANGES[risk_factor]
                    if amount > max_range:
                        effective_range_warnings.append(
                            f"{risk_factor}: {amount:.2f}g exceeds effective range (max: {max_range}g)"
                        )
                        # Apply diminishing returns above effective range
                        effective_amount = max_range + (amount - max_range) * 0.5
                    else:
                        effective_amount = amount
                else:
                    effective_amount = amount
                
                # Calculate contribution
                contribution = effective_amount * heni_factor
                total_heni += contribution
                
                # Categorize contribution
                if risk_factor in ["omega_3", "calcium", "fiber", "polyunsaturated_fatty_acids"]:
                    nutrient_contributions[risk_factor] = contribution
                else:
                    food_group_contributions[risk_factor] = contribution
        
        # Apply age/gender adjustment
        if self.gender_adjustment:
            total_heni *= self.adjustment_factor
        
        # Calculate normalized scores
        heni_per_100_kcal = (total_heni / total_energy_kcal) * 100 if total_energy_kcal > 0 else 0
        heni_per_100_grams = (total_heni / total_weight_grams) * 100 if total_weight_grams > 0 else 0
        heni_per_serving = (total_heni / total_weight_grams) * serving_size_grams if total_weight_grams > 0 else 0
        
        # Calculate disease burden breakdown
        disease_breakdown = self._calculate_disease_burden_breakdown(
            risk_factor_amounts, total_heni
        )
        
        # Convert to health impact minutes (1 μDALY ≈ 0.5256 minutes per technical report)
        health_impact_minutes = total_heni * 0.5256
        
        # Generate health interpretation
        health_impact_description = self._generate_health_interpretation(
            health_impact_minutes, risk_factor_amounts
        )
        
        return HENIResult(
            total_heni_score=total_heni,
            heni_per_100_kcal=heni_per_100_kcal,
            heni_per_100_grams=heni_per_100_grams,
            heni_per_serving=heni_per_serving,
            food_group_contributions=food_group_contributions,
            nutrient_contributions=nutrient_contributions,
            disease_burden_breakdown=disease_breakdown,
            risk_factor_amounts=risk_factor_amounts,
            effective_range_warnings=effective_range_warnings,
            health_impact_minutes=health_impact_minutes,
            health_impact_description=health_impact_description
        )
    
    def _calculate_disease_burden_breakdown(
        self, 
        risk_factor_amounts: Dict[str, float], 
        total_heni: float
    ) -> Dict[str, float]:
        """Calculate the contribution of each disease category to the total HENI score"""
        disease_breakdown = {disease: 0.0 for disease in DISEASE_BURDEN_ATTRIBUTION.keys()}
        
        for risk_factor, amount in risk_factor_amounts.items():
            if risk_factor in RISK_FACTOR_DISEASE_MAPPING and risk_factor in HENI_FACTORS:
                risk_contribution = amount * HENI_FACTORS[risk_factor]
                associated_diseases = RISK_FACTOR_DISEASE_MAPPING[risk_factor]
                
                # Distribute contribution among associated diseases
                for disease in associated_diseases:
                    if disease in disease_breakdown:
                        # Weight by disease's overall attribution factor
                        disease_weight = DISEASE_BURDEN_ATTRIBUTION[disease]
                        disease_breakdown[disease] += risk_contribution * disease_weight / len(associated_diseases)
        
        return disease_breakdown
    
    def _generate_health_interpretation(
        self, 
        health_impact_minutes: float, 
        risk_factor_amounts: Dict[str, float]
    ) -> str:
        """Generate human-readable interpretation of health impact"""
        
        if health_impact_minutes > 20:
            category = "Highly Beneficial"
            description = f"This food provides significant health benefits, adding approximately {abs(health_impact_minutes):.1f} minutes to healthy life expectancy."
        elif health_impact_minutes > 5:
            category = "Moderately Beneficial"  
            description = f"This food provides moderate health benefits, adding approximately {abs(health_impact_minutes):.1f} minutes to healthy life expectancy."
        elif health_impact_minutes > 0:
            category = "Mildly Beneficial"
            description = f"This food provides mild health benefits, adding approximately {abs(health_impact_minutes):.1f} minutes to healthy life expectancy."
        elif health_impact_minutes > -5:
            category = "Neutral"
            description = "This food has minimal impact on health outcomes."
        elif health_impact_minutes > -20:
            category = "Mildly Detrimental" 
            description = f"This food may reduce healthy life expectancy by approximately {abs(health_impact_minutes):.1f} minutes."
        else:
            category = "Highly Detrimental"
            description = f"This food may significantly reduce healthy life expectancy by approximately {abs(health_impact_minutes):.1f} minutes."
        
        # Add specific risk factor insights
        dominant_factors = []
        for factor, amount in risk_factor_amounts.items():
            if factor in HENI_FACTORS and amount > 0:
                contribution = amount * HENI_FACTORS[factor] * 0.5256  # Convert to minutes
                if abs(contribution) > 2:  # Significant contributors (>2 minutes)
                    dominant_factors.append((factor, contribution))
        
        if dominant_factors:
            dominant_factors.sort(key=lambda x: abs(x[1]), reverse=True)
            top_factor, top_contribution = dominant_factors[0]
            
            if top_contribution > 0:
                description += f" Primary benefit comes from {top_factor.replace('_', ' ')}."
            else:
                description += f" Primary concern is {top_factor.replace('_', ' ')}."
        
        return f"{category}: {description}"
    
    def calculate_population_impact(
        self, 
        individual_results: List[HENIResult], 
        population_size: int = 100000
    ) -> Dict[str, float]:
        """Calculate population-level health impact for policy analysis"""
        if not individual_results:
            return {}
        
        avg_heni = sum(result.total_heni_score for result in individual_results) / len(individual_results)
        total_minutes_saved = sum(result.health_impact_minutes for result in individual_results)
        
        # Convert to population-level metrics
        population_dalys_avoided = avg_heni * population_size / 1_000_000  # Convert μDALY to DALY
        population_life_years_saved = population_dalys_avoided  # 1 DALY = 1 life year
        
        return {
            "population_size": population_size,
            "average_heni_score": avg_heni,
            "total_dalys_avoided": population_dalys_avoided,
            "total_life_years_saved": population_life_years_saved,
            "total_minutes_saved": total_minutes_saved,
            "economic_value_usd": population_dalys_avoided * 50000,  # Rough economic value of DALY
        }