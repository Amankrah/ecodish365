import time
import logging
import os
import sys
from typing import Dict, Any

# Change to the directory containing this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'api'))

from src.data_loader import DataLoader
from src.food import Food
from src.meal import Meal
from src.life_cycle_assessment import LifeCycleAssessment
from src.monetization import Monetization
from src.reference_meals import ReferenceMeals
from src.cnf_integrator import get_cnf_integrator
from src.utils import format_impact_value, categorize_sustainability_score

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)

def main():
    """
    Enhanced main function with comprehensive meal analysis and comparison.
    """
    logger = setup_logging()
    
    try:
        start_time = time.time()
        
        # Initialize CNF integrator and data loader
        logger.info("Initializing CNF integrator and data loader...")
        cnf_integrator = get_cnf_integrator()
        
        # Get CNF folder path (same pattern as HENI)
        cnf_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'raw_cnf')
        if not cnf_integrator.is_initialized():
            cnf_integrator.initialize(cnf_folder)
        
        data_loader = DataLoader()

        # Create sample meal with diverse foods (using same IDs as HENI for consistency)
        logger.info("Creating food items...")
        try:
            salmon = Food(food_id=2003, quantity=150, data_loader=data_loader)    # Salmon (from HENI)
            brown_rice = Food(food_id=3580, quantity=100, data_loader=data_loader)  # Brown rice (from HENI)
            broccoli = Food(food_id=2892, quantity=120, data_loader=data_loader)   # Broccoli (from HENI)
            # Add one more food for a complete meal analysis
            cheese = Food(food_id=18, quantity=50, data_loader=data_loader)        # Blue cheese (from CNF data we saw)
        except ValueError as e:
            logger.error(f"Failed to create food items: {e}")
            logger.info("Available food IDs from loaded data - using first few as fallback")
            # Use some basic food IDs that we know exist from the CNF data
            salmon = Food(food_id=2, quantity=150, data_loader=data_loader)      # Cheese souffle (fallback)
            brown_rice = Food(food_id=4, quantity=100, data_loader=data_loader)  # Chop suey (fallback) 
            broccoli = Food(food_id=5, quantity=120, data_loader=data_loader)    # Chinese dish (fallback)
            cheese = Food(food_id=6, quantity=50, data_loader=data_loader)       # Corn fritter (fallback)

        # Create meal
        logger.info("Creating meal...")
        meal = Meal([salmon, brown_rice, broccoli, cheese])

        # Comprehensive meal analysis
        logger.info("Performing comprehensive meal analysis...")
        comprehensive_analysis = analyze_meal_comprehensively(meal, data_loader, logger)
        
        # Create reference meals for comparison
        logger.info("Creating reference meals...")
        reference_analysis = create_and_analyze_reference_meals(data_loader, logger)
        
        # Display results
        display_comprehensive_results(comprehensive_analysis, reference_analysis)
            
        end_time = time.time()
        print(f"\n{'='*60}")
        print(f"Total Execution Time: {end_time - start_time:.3f} seconds")
        print(f"{'='*60}")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        raise

def analyze_meal_comprehensively(meal: Meal, data_loader: DataLoader, logger) -> Dict[str, Any]:
    """
    Perform comprehensive analysis of a meal including LCA, monetization, and sustainability scoring.
    """
    analysis = {}
    
    try:
        # Basic meal info
        analysis['meal_info'] = {
            'composition': meal.get_food_breakdown(),
            'total_calories': meal.calculate_total_calories(),
            'total_weight': meal.get_total_weight(),
            'energy_density': meal.get_energy_density()
        }
        
        # Nutritional analysis
        logger.info("Analyzing nutritional profile...")
        analysis['nutrition'] = {
            'nutrient_profile': meal.calculate_nutrient_profile(),
            'nutritional_quality': meal.get_nutritional_quality_score()
        }
        
        # Life Cycle Assessment
        logger.info("Performing Life Cycle Assessment...")
        lca = LifeCycleAssessment(meal)
        lca_results = lca.perform_lcia()
        endpoint_impacts = lca.calculate_endpoint_impacts()
        single_score = lca.calculate_single_score()
        impact_breakdown = lca.get_impact_breakdown()
        sanity_warnings = lca.sanity_check()
        
        analysis['lca'] = {
            'midpoint_impacts': lca_results,
            'endpoint_impacts': endpoint_impacts,
            'single_score': single_score,
            'impact_breakdown': impact_breakdown,
            'warnings': sanity_warnings
        }
        
        # Monetization
        logger.info("Monetizing environmental impacts...")
        monetization = Monetization(lca_results, data_loader)
        total_calories = analysis['meal_info']['total_calories']
        total_protein = analysis['nutrition']['nutrient_profile'].get('PROTEIN', 0)
        
        analysis['monetization'] = {
            'monetized_impacts': monetization.monetize_impacts(),
            'total_cost': monetization.get_total_monetized_impact(),
            'cost_per_calorie': monetization.calculate_cost_per_calorie(total_calories),
            'cost_per_protein': monetization.calculate_cost_per_gram_protein(total_protein),
            'cost_breakdown_by_category': monetization.get_cost_breakdown_by_category(),
            'top_cost_drivers': monetization.get_top_cost_drivers()
        }
        
        # Sustainability scoring
        logger.info("Calculating sustainability scores...")
        analysis['sustainability'] = meal.get_sustainability_score()
        
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        analysis['error'] = str(e)
    
    return analysis

def create_and_analyze_reference_meals(data_loader: DataLoader, logger) -> Dict[str, Any]:
    """
    Create and analyze reference meals for comparison.
    """
    reference_analysis = {}
    reference_meals = ReferenceMeals(data_loader)
    
    meal_types = ['sustainable', 'unsustainable', 'ultra_processed', 'balanced']
    
    for meal_type in meal_types:
        try:
            logger.info(f"Creating {meal_type} reference meal...")
            
            if meal_type == 'sustainable':
                ref_meal = reference_meals.create_sustainable_meal('lunch')
            elif meal_type == 'unsustainable':
                ref_meal = reference_meals.create_unsustainable_meal('lunch')
            elif meal_type == 'ultra_processed':
                ref_meal = reference_meals.create_ultra_processed_meal('lunch')
            elif meal_type == 'balanced':
                ref_meal = reference_meals.create_balanced_meal('lunch')
            
            # Quick analysis of reference meal
            ref_lca = LifeCycleAssessment(ref_meal)
            ref_impacts = ref_lca.perform_lcia()
            ref_monetization = Monetization(ref_impacts, data_loader)
            
            reference_analysis[meal_type] = {
                'meal': ref_meal,
                'total_calories': ref_meal.calculate_total_calories(),
                'environmental_cost': ref_monetization.get_total_monetized_impact(),
                'sustainability_score': ref_meal.get_sustainability_score(),
                'carbon_footprint': ref_impacts.get('Global warming', 0)
            }
            
        except Exception as e:
            logger.warning(f"Failed to create {meal_type} reference meal: {e}")
            reference_analysis[meal_type] = {'error': str(e)}
    
    return reference_analysis

def display_comprehensive_results(analysis: Dict[str, Any], reference_analysis: Dict[str, Any]):
    """
    Display comprehensive analysis results in a formatted way.
    """
    print("\n" + "="*80)
    print("COMPREHENSIVE MEAL ENVIRONMENTAL IMPACT ANALYSIS")
    print("="*80)
    
    # Meal composition
    if 'meal_info' in analysis:
        print("\n📋 MEAL COMPOSITION")
        print("-" * 40)
        meal_info = analysis['meal_info']
        print(f"Total Calories: {meal_info['total_calories']:.0f} kcal")
        print(f"Total Weight: {meal_info['total_weight']:.1f} g")
        print(f"Energy Density: {meal_info['energy_density']:.2f} kcal/g")
        
        print("\nFood Items:")
        for food in meal_info['composition']:
            print(f"  • {food['name']} ({food['quantity']}g) - {food['group']}")
    
    # Nutritional Quality
    if 'nutrition' in analysis:
        print("\n🥗 NUTRITIONAL ANALYSIS") 
        print("-" * 40)
        nutrition_quality = analysis['nutrition']['nutritional_quality']
        rating = nutrition_quality.get('rating', 'Unknown')
        score = nutrition_quality.get('nutritional_quality_score', 0)
        print(f"Nutritional Quality Score: {score:.1f}/100 ({rating})")
    
    # Environmental Impact Summary
    if 'lca' in analysis:
        print("\n🌍 ENVIRONMENTAL IMPACT SUMMARY")
        print("-" * 40)
        lca = analysis['lca']
        
        # Key impacts
        midpoint = lca['midpoint_impacts']
        carbon = midpoint.get('Global warming', 0)
        water = midpoint.get('Water consumption', 0)
        land = midpoint.get('Land use', 0)
        
        print(f"Carbon Footprint: {format_impact_value(carbon, 'kg CO2-eq')}")
        print(f"Water Consumption: {format_impact_value(water, 'm³')}")
        print(f"Land Use: {format_impact_value(land, 'm²a crop-eq')}")
        print(f"Single Score: {lca['single_score']:.3e} points")
        
        # Endpoint impacts
        if 'endpoint_impacts' in lca:
            print(f"\nEndpoint Impacts:")
            for endpoint, value in lca['endpoint_impacts'].items():
                print(f"  {endpoint}: {value:.2e}")
    
    # Economic Impact
    if 'monetization' in analysis:
        print("\n💰 ECONOMIC IMPACT")
        print("-" * 40)
        monetization = analysis['monetization']
        total_cost = monetization['total_cost']
        cost_per_cal = monetization['cost_per_calorie']
        
        print(f"Total Environmental Cost: CAD ${total_cost:.3f}")
        print(f"Cost per Calorie: CAD ${cost_per_cal:.5f}")
        
        # Top cost drivers
        top_drivers = monetization.get('top_cost_drivers', [])[:3]
        if top_drivers:
            print(f"\nTop Cost Drivers:")
            for driver in top_drivers:
                impact = driver['impact_category']
                cost = driver['cost']
                percent = driver['percentage_of_total']
                print(f"  {impact}: CAD ${cost:.3f} ({percent:.1f}%)")
    
    # Sustainability Score
    if 'sustainability' in analysis:
        print("\n🌱 SUSTAINABILITY ASSESSMENT")
        print("-" * 40)
        sustainability = analysis['sustainability']
        score = sustainability.get('overall_sustainability_score', 0)
        rating = sustainability.get('sustainability_rating', 'Unknown')
        print(f"Overall Sustainability Score: {score:.1f}/100 ({rating})")
    
    # Reference Meal Comparisons
    print("\n📊 REFERENCE MEAL COMPARISONS")
    print("-" * 40)
    
    main_cost = analysis.get('monetization', {}).get('total_cost', 0)
    main_carbon = analysis.get('lca', {}).get('midpoint_impacts', {}).get('Global warming', 0)
    main_sustainability = analysis.get('sustainability', {}).get('overall_sustainability_score', 0)
    
    for meal_type, ref_data in reference_analysis.items():
        if 'error' not in ref_data:
            ref_cost = ref_data.get('environmental_cost', 0)
            ref_carbon = ref_data.get('carbon_footprint', 0)
            ref_sustain = ref_data.get('sustainability_score', {}).get('overall_sustainability_score', 0)
            
            cost_ratio = (main_cost / ref_cost) if ref_cost > 0 else float('inf')
            carbon_ratio = (main_carbon / ref_carbon) if ref_carbon > 0 else float('inf')
            
            print(f"\nvs {meal_type.title()} Meal:")
            print(f"  Environmental Cost Ratio: {cost_ratio:.2f}x")
            print(f"  Carbon Footprint Ratio: {carbon_ratio:.2f}x")
            print(f"  Sustainability: {main_sustainability:.1f} vs {ref_sustain:.1f}")
        else:
            print(f"\n{meal_type.title()} Meal: Analysis failed")

def compare_meals(meal, sustainable, unsustainable, ultra_processed):
    """Legacy comparison function for backward compatibility."""
    meal_impact = sum(meal.calculate_environmental_impact().values())
    sustainable_impact = sum(sustainable.calculate_environmental_impact().values())
    unsustainable_impact = sum(unsustainable.calculate_environmental_impact().values())
    ultra_processed_impact = sum(ultra_processed.calculate_environmental_impact().values())

    print(f"Comparison to sustainable lunch: {meal_impact / sustainable_impact:.2f}")
    print(f"Comparison to unsustainable lunch: {meal_impact / unsustainable_impact:.2f}")
    print(f"Comparison to ultra-processed lunch: {meal_impact / ultra_processed_impact:.2f}")

if __name__ == "__main__":
    main()
