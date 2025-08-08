import time
import logging
from fcs.models.food_item import FoodItem
from fcs.utils.cnf_data_integrator import create_cnf_integrator
from fcs.analyzers.food_analyzer import FoodAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        start_time = time.time()

        # Create an example FoodItem
        food_item = FoodItem("Example Food")
        
        # Example food IDs ([Fish, salmon, atlantic, wild, raw], [Rice, spanish rice mix, unprepared])
        food_ids = [3049, 3725]  
        
        # Extract nutrients from CNF using enhanced integrator
        cnf_integrator = create_cnf_integrator()
        cnf_integrator.extract_nutrients_enhanced(food_ids, food_item)
        
        # Debug: Show what nutrients were extracted
        print(f"\nDEBUG: Food item '{food_item.name}' after nutrient extraction:")
        for domain, attributes in food_item.attributes.items():
            non_zero_attrs = {k: v for k, v in attributes.items() if v != 0}
            if non_zero_attrs:
                print(f"  {domain}: {non_zero_attrs}")
        
        # Analyze the food item to get the FCS and NOVA category
        analyzer = FoodAnalyzer()
        result = analyzer.analyze_food_item(food_item)

        # Display the analysis results
        end_time = time.time()
        
        print(f"Analysis for {result['name']}:")
        print(f"Original Score: {result['original_score']}")
        print(f"Food Compass Score (FCS): {result['fcs']}")
        print(f"NOVA Category: {result['nova_category']}")
        print(f"Execution Time: {end_time - start_time:.6f} seconds")

    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()