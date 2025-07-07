import logging

logger = logging.getLogger(__name__)

class NetHealthImpactCalculator:
    def __init__(self, heni_calculator, lca_class, monetization_class):
        self.heni_calculator = heni_calculator
        self.lca_class = lca_class
        self.monetization_class = monetization_class
        self.minutes_per_daly = 0.53  # Conversion factor from DALYs to minutes

    def calculate_net_impact(self, heni_ingredients, env_meal):
        # Calculate HENI
        heni_score, total_kcal, total_heni, ingredient_categories = self.heni_calculator.calculate_heni(heni_ingredients)
        logger.info(f"HENI Score: {heni_score} μDALYs per 100 kcal")
        logger.info(f"Total kcal: {total_kcal}")
        logger.info(f"Total HENI: {total_heni} μDALYs")

        # Calculate environmental impact
        lca = self.lca_class(env_meal)
        lca_results = lca.perform_lcia()
        endpoint_impacts = lca.calculate_endpoint_impacts()
        
        # Monetize environmental impacts
        monetization = self.monetization_class(lca_results, env_meal.data_loader)
        total_monetized_impact = monetization.get_total_monetized_impact()

        # Convert HENI to DALYs (it's currently in μDALYs)
        heni_dalys = total_heni / 1_000_000

        # Combine HENI and environmental impact
        # Assuming endpoint_impacts['Human Health'] is in DALYs
        net_dalys = heni_dalys - endpoint_impacts['Human Health']

        # Convert to minutes of healthy life
        net_minutes = net_dalys * self.minutes_per_daly

        logger.info(f"HENI impact: {heni_dalys:.6f} DALYs")
        logger.info(f"Environmental impact: {endpoint_impacts['Human Health']:.6f} DALYs")
        logger.info(f"Net impact: {net_minutes:.2f} minutes of healthy life")
        logger.info(f"Total monetized environmental impact: ${total_monetized_impact:.2f}")

        return {
            "net_health_impact": net_minutes,
            "heni_score": heni_score,
            "total_kcal": total_kcal,
            "total_heni": total_heni,
            "environmental_impact_dalys": endpoint_impacts['Human Health'],
            "total_monetized_impact": total_monetized_impact
        }