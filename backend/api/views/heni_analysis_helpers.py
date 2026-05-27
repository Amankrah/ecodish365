"""
Helper functions for HENI API analysis endpoints
Provides detailed insights for researchers, policy makers, and individuals
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

def _identify_primary_health_drivers(heni_result: Dict) -> Dict[str, Any]:
    """Identify the primary factors driving health impact"""
    drivers = {
        "positive_drivers": [],
        "negative_drivers": [],
        "dominant_factor": None,
        "impact_magnitude": "low"
    }
    
    try:
        # Combine food group and nutrient contributions
        all_contributions = {}
        all_contributions.update(heni_result.get('component_breakdown', {}).get('food_group_contributions', {}))
        all_contributions.update(heni_result.get('component_breakdown', {}).get('nutrient_contributions', {}))
        
        # Sort by absolute impact
        sorted_contributions = sorted(all_contributions.items(), key=lambda x: abs(x[1]), reverse=True)
        
        for factor, contribution in sorted_contributions:
            impact_data = {
                "factor": factor.replace('_', ' ').title(),
                "contribution_μdaly": round(contribution, 2),
                "health_minutes": round(contribution * 0.5256, 1)
            }
            
            if contribution > 1:  # Significant positive impact
                drivers["positive_drivers"].append(impact_data)
            elif contribution < -1:  # Significant negative impact
                drivers["negative_drivers"].append(impact_data)
        
        # Identify dominant factor
        if sorted_contributions:
            dominant_factor, dominant_value = sorted_contributions[0]
            drivers["dominant_factor"] = {
                "factor": dominant_factor.replace('_', ' ').title(),
                "contribution": round(dominant_value, 2),
                "direction": "beneficial" if dominant_value > 0 else "detrimental"
            }
            
            # Classify impact magnitude
            abs_impact = abs(dominant_value)
            if abs_impact > 20:
                drivers["impact_magnitude"] = "very high"
            elif abs_impact > 10:
                drivers["impact_magnitude"] = "high"
            elif abs_impact > 3:
                drivers["impact_magnitude"] = "moderate"
            else:
                drivers["impact_magnitude"] = "low"
    
    except Exception as e:
        logger.warning(f"Error identifying health drivers: {e}")
    
    return drivers

def _get_epidemiological_context(heni_result: Dict) -> Dict[str, Any]:
    """Provide epidemiological context for health impacts"""
    context = {
        "evidence_quality": "High",
        "study_populations": "Global population-based cohorts",
        "primary_outcomes": [],
        "risk_certainty": {}
    }
    
    try:
        disease_breakdown = heni_result.get('disease_burden_analysis', {}).get('disease_breakdown', {})
        
        # Identify primary disease outcomes
        for disease, burden in disease_breakdown.items():
            if abs(burden) > 1:  # Significant burden
                outcome_data = {
                    "disease": disease.replace('_', ' ').title(),
                    "burden_contribution": round(burden, 2),
                    "evidence_source": "Global Burden of Disease meta-analyses",
                    "population_relevance": "High"
                }
                context["primary_outcomes"].append(outcome_data)
        
        # Risk certainty classification
        risk_factors = heni_result.get('risk_factor_analysis', {}).get('risk_factors', {})
        for factor, amount in risk_factors.items():
            if amount > 0:
                # Classify evidence strength for each risk factor
                evidence_strength = _get_evidence_strength_for_factor(factor)
                context["risk_certainty"][factor] = evidence_strength
    
    except Exception as e:
        logger.warning(f"Error getting epidemiological context: {e}")
    
    return context

def _estimate_population_impact(heni_result: Dict, serving_size_g: float) -> Dict[str, Any]:
    """Estimate population-level health impact"""
    impact = {
        "per_capita_annual_impact": {},
        "population_scenarios": {},
        "economic_implications": {}
    }
    
    try:
        daily_heni = heni_result.get('heni_scores', {}).get('heni_per_100_grams', 0) * (serving_size_g / 100)
        daily_health_minutes = daily_heni * 0.5256
        
        # Annual impact assuming daily consumption
        annual_heni = daily_heni * 365
        annual_health_minutes = daily_health_minutes * 365
        annual_health_hours = annual_health_minutes / 60
        
        impact["per_capita_annual_impact"] = {
            "annual_heni_μdaly": round(annual_heni, 2),
            "annual_health_minutes": round(annual_health_minutes, 1),
            "annual_health_hours": round(annual_health_hours, 2),
            "life_expectancy_change_days": round(annual_health_hours / 24, 2)
        }
        
        # Population scenarios
        populations = [100000, 1000000, 10000000]  # 100K, 1M, 10M
        for pop_size in populations:
            scenario_key = f"population_{pop_size//1000}k" if pop_size < 1000000 else f"population_{pop_size//1000000}m"
            
            scenario_dalys = (annual_heni * pop_size) / 1000000  # Convert μDALY to DALY
            scenario_economic = scenario_dalys * 50000  # $50K per DALY (rough estimate)
            
            impact["population_scenarios"][scenario_key] = {
                "population_size": pop_size,
                "annual_dalys_avoided": round(scenario_dalys, 2),
                "economic_value_usd": round(scenario_economic, 0),
                "equivalent_life_years": round(scenario_dalys, 2)
            }
    
    except Exception as e:
        logger.warning(f"Error estimating population impact: {e}")
    
    return impact

def _generate_policy_recommendations(heni_result: Dict, food_group: str) -> List[Dict[str, str]]:
    """Generate policy recommendations based on HENI analysis"""
    recommendations = []
    
    try:
        total_heni = heni_result.get('heni_scores', {}).get('total_heni_score', 0)
        health_minutes = heni_result.get('health_impact', {}).get('health_impact_minutes', 0)
        
        if health_minutes > 10:  # Highly beneficial
            recommendations.extend([
                {
                    "category": "Promotion Policy",
                    "recommendation": f"Consider subsidies or tax incentives for {food_group} consumption",
                    "rationale": f"Significant health benefits (+{health_minutes:.1f} minutes per serving) justify public investment",
                    "implementation": "Targeted nutrition programs, school meal integration"
                },
                {
                    "category": "Public Health Campaign", 
                    "recommendation": f"Promote increased {food_group} consumption in dietary guidelines",
                    "rationale": "Strong epidemiological evidence supports population health benefits",
                    "implementation": "Educational campaigns, healthcare provider training"
                }
            ])
        elif health_minutes < -10:  # Highly detrimental
            recommendations.extend([
                {
                    "category": "Regulatory Policy",
                    "recommendation": f"Consider restrictions or taxation on {food_group}",
                    "rationale": f"Significant health risks ({health_minutes:.1f} minutes lost per serving) warrant intervention",
                    "implementation": "Sin taxes, warning labels, marketing restrictions"
                },
                {
                    "category": "Substitution Strategy",
                    "recommendation": f"Promote healthier alternatives to {food_group}",
                    "rationale": "Reducing consumption while providing alternatives maintains consumer choice",
                    "implementation": "Reformulation incentives, substitute promotion campaigns"
                }
            ])
        else:
            recommendations.append({
                "category": "Monitoring Policy",
                "recommendation": f"Continue monitoring {food_group} consumption patterns",
                "rationale": "Moderate health impact requires ongoing surveillance",
                "implementation": "Population surveys, consumption tracking studies"
            })
    
    except Exception as e:
        logger.warning(f"Error generating policy recommendations: {e}")
    
    return recommendations

def _get_comparison_benchmarks(heni_result: Dict) -> Dict[str, Any]:
    """Get comparison benchmarks for HENI scores"""
    benchmarks = {
        "score_percentiles": {},
        "category_comparison": {},
        "reference_foods": {}
    }
    
    try:
        heni_per_100kcal = heni_result.get('heni_scores', {}).get('heni_per_100_kcal', 0)
        
        # Score percentile classification
        if heni_per_100kcal > 30:
            percentile = "Top 5% (Highly Beneficial)"
        elif heni_per_100kcal > 15:
            percentile = "Top 25% (Very Beneficial)"
        elif heni_per_100kcal > 5:
            percentile = "Top 50% (Beneficial)"
        elif heni_per_100kcal > -5:
            percentile = "Average (Neutral)"
        elif heni_per_100kcal > -15:
            percentile = "Bottom 50% (Concerning)"
        else:
            percentile = "Bottom 10% (Highly Concerning)"
        
        benchmarks["score_percentiles"] = {
            "current_score": round(heni_per_100kcal, 2),
            "percentile_category": percentile,
            "population_comparison": "Compared to 5000+ foods in database"
        }
        
        # Reference foods for comparison
        benchmarks["reference_foods"] = {
            "highly_beneficial": [
                {"food": "Salmon (100g)", "heni_score": 45, "key_benefit": "Omega-3 fatty acids"},
                {"food": "Mixed nuts (30g)", "heni_score": 25, "key_benefit": "Healthy fats and protein"},
                {"food": "Leafy greens (100g)", "heni_score": 15, "key_benefit": "Fiber and antioxidants"}
            ],
            "highly_detrimental": [
                {"food": "Processed meat (50g)", "heni_score": -25, "key_concern": "Processed meat risks"},
                {"food": "Soft drink (350ml)", "heni_score": -18, "key_concern": "Added sugars"},
                {"food": "Fried foods (100g)", "heni_score": -12, "key_concern": "Trans fats"}
            ]
        }
    
    except Exception as e:
        logger.warning(f"Error getting comparison benchmarks: {e}")
    
    return benchmarks

def _get_evidence_strength_for_factor(factor: str) -> str:
    """Get evidence strength classification for risk factors"""
    # Based on Global Burden of Disease evidence strength
    high_evidence = ['omega_3', 'fiber', 'processed_meat', 'sodium', 'trans_fat']
    moderate_evidence = ['nuts_seeds', 'whole_grains', 'fruits', 'vegetables']
    
    if factor in high_evidence:
        return "High (RCT and large cohort evidence)"
    elif factor in moderate_evidence:
        return "Moderate (cohort and ecological evidence)"
    else:
        return "Emerging (limited but consistent evidence)"