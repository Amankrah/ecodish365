import time
import logging
from src.data_loader import DataLoader
from src.food import Food
from src.meal import Meal
from src.life_cycle_assessment import LifeCycleAssessment
from src.monetization import Monetization
from src.reference_meals import ReferenceMeals

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)

def main():
    logger = setup_logging()
    
    try:
        start_time = time.time()
        
        # Initialize data loader
        logger.info("Initializing data loader...")
        data_loader = DataLoader()

        # Create foods
        logger.info("Creating food items...")
        chicken = Food(food_id=2003, quantity=150, data_loader=data_loader)
        beans = Food(food_id=3580, quantity=100, data_loader=data_loader)
        plantain = Food(food_id=2892, quantity=10, data_loader=data_loader)

        # Create meal
        logger.info("Creating meal...")
        meal = Meal([chicken, beans, plantain])

        # Perform LCA
        logger.info("Performing Life Cycle Assessment...")
        lca = LifeCycleAssessment(meal)
        lca_results = lca.perform_lcia()
        endpoint_impacts = lca.calculate_endpoint_impacts()
       
        # Monetize impacts
        logger.info("Monetizing environmental impacts...")
        monetization = Monetization(lca_results, data_loader)
        try:
            monetized_impacts = monetization.monetize_impacts()
            total_monetized_impact = monetization.get_total_monetized_impact()
        except Exception as e:
            logger.error(f"Error in monetization: {str(e)}")
            monetized_impacts = {}
            total_monetized_impact = 0
        
        # Create reference meals
        logger.info("Creating reference meals...")
        reference_meals = ReferenceMeals(data_loader)
        try:
            sustainable_lunch = reference_meals.create_sustainable_meal('lunch')
            unsustainable_lunch = reference_meals.create_unsustainable_meal('lunch')
            ultra_processed_lunch = reference_meals.create_ultra_processed_meal('lunch')
        except ValueError as e:
            logger.error(f"Failed to create reference meals: {str(e)}")
            sustainable_lunch = unsustainable_lunch = ultra_processed_lunch = None

        # Print results
        print("\n--- Environmental Impact Assessment Results ---")
        print(f"Meal composition: {meal}")
        print(f"\nMidpoint Impacts:")
        for impact, value in lca_results.items():
            print(f"  {impact}: {value:.2f}")
        
        print(f"\nEndpoint Impacts:")
        for impact, value in endpoint_impacts.items():
            print(f"  {impact}: {value:.2f}")

        print(f"\nMonetized Environmental Impacts:")
        if monetized_impacts:
            for impact, value in monetized_impacts.items():
                print(f"  {impact}: ${value:.2f}")
            print(f"\nTotal monetized environmental impact: ${total_monetized_impact:.2f}")
        else:
            print("  Monetization failed. Please check the logs for details.")

        print("\n--- Meal Comparisons ---")
        if sustainable_lunch and unsustainable_lunch and ultra_processed_lunch:
            compare_meals(meal, sustainable_lunch, unsustainable_lunch, ultra_processed_lunch)
        else:
            print("Could not create reference meals for comparison.")
            
        end_time = time.time()
        print(f"Execution Time: {end_time - start_time:.6f} seconds")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

def compare_meals(meal, sustainable, unsustainable, ultra_processed):
    meal_impact = sum(meal.calculate_environmental_impact().values())
    sustainable_impact = sum(sustainable.calculate_environmental_impact().values())
    unsustainable_impact = sum(unsustainable.calculate_environmental_impact().values())
    ultra_processed_impact = sum(ultra_processed.calculate_environmental_impact().values())

    print(f"Comparison to sustainable lunch: {meal_impact / sustainable_impact:.2f}")
    print(f"Comparison to unsustainable lunch: {meal_impact / unsustainable_impact:.2f}")
    print(f"Comparison to ultra-processed lunch: {meal_impact / ultra_processed_impact:.2f}")

if __name__ == "__main__":
    main()
