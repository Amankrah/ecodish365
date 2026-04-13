import logging
import time

from fcs.service import extract_and_score, get_cnf_integrator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    try:
        print("=== FCS CALCULATION PERFORMANCE TEST ===")
        total_start = time.time()

        food_ids = [3049, 3725]

        integrator_start = time.time()
        get_cnf_integrator()
        integrator_time = time.time() - integrator_start
        print(f"CNF integrator initialization: {integrator_time:.3f} seconds")

        extraction_start = time.time()
        _, result = extract_and_score(food_ids, "Example Food")
        extraction_time = time.time() - extraction_start
        print(f"Nutrient extraction + FCS (Rust): {extraction_time:.3f} seconds")

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("FCS result: %s", result)

        total_time = time.time() - total_start
        print("\n=== FCS RESULTS ===")
        print(f"Analysis for {result['name']}:")
        print(f"Original Score: {result['original_score']}")
        print(f"Food Compass Score (FCS): {result['fcs']}")
        print(f"NOVA Category: {result['nova_category']}")

        print("\n=== PERFORMANCE SUMMARY ===")
        print(f"CNF integrator initialization: {integrator_time:.3f}s")
        print(f"Extract + score: {extraction_time:.3f}s")
        print(f"TOTAL TIME: {total_time:.3f} seconds")

    except Exception as e:
        logger.error("An error occurred: %s", e)


def test_subsequent_calculations():
    print("\n=== TESTING SUBSEQUENT CALCULATIONS ===")
    test_cases = [
        ([3049], "Single food: Salmon"),
        ([3725], "Single food: Rice bran bread"),
        ([3049, 3725], "Two foods: Salmon + Bread"),
        ([3049, 3725, 3580], "Three foods: Salmon + Bread + Venison"),
    ]

    for food_ids, description in test_cases:
        start_time = time.time()
        _, result = extract_and_score(food_ids, f"Test: {description}")
        calc_time = time.time() - start_time
        print(
            f"{description}: {calc_time:.3f}s "
            f"(FCS: {result['fcs']:.1f}, NOVA: {result['nova_category']})"
        )


if __name__ == "__main__":
    main()
    test_subsequent_calculations()
