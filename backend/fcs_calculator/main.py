import time
import logging
from fcs.models.food_item import FoodItem
from fcs.analyzers.cnf_integrator import CNFIntegrator
from fcs.analyzers.food_analyzer import FoodAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        start_time = time.time()

        # Create an example FoodItem
        food_item = FoodItem("Example Food")
        
        # Example food IDs (wild salmon, brown rice, broccoli)
        food_ids = [2003, 3580, 2892]  
        
        # Extract nutrients from CNF based on food IDs and populate the FoodItem
        CNFIntegrator.extract_nutrients_from_cnf(food_ids, food_item)
        
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