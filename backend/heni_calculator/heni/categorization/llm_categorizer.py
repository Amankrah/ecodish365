import logging
from typing import Dict, Optional
import openai
from ..database.cnf_integrator import HENICNFIntegrator
from ..config.heni_factors import HENI_RISK_FACTOR_KEYS
from .rule_based_categorizer import RuleBasedCategorizer
import json

class LLMFoodCategorizer:
    """Efficient LLM-based food categorizer for HENI risk factors.
    Uses rule-based categorization first, LLM only as fallback or augmentation.
    """
    
    def __init__(self, cnf_integrator: HENICNFIntegrator, api_key: str):
        self.cnf_integrator = cnf_integrator
        self.client = openai.OpenAI(api_key=api_key) if api_key else None
        self.heni_risk_factors = sorted(HENI_RISK_FACTOR_KEYS)
        self.categorization_cache = {}
        self.logger = logging.getLogger(__name__)
        
        # Cost efficiency settings
        self.model = "gpt-4o-mini"  # Most cost-effective model
        self.max_tokens = 150  # Keep responses concise
        self.temperature = 0  # Deterministic responses
    
    def _create_heni_prompt(self, food_description: str, food_group: str, rule_based_result: Dict[str, float]) -> str:
        """Create precise, concise prompt for HENI risk factor categorization."""
        
        # Only ask LLM to fill gaps or validate uncertain categorizations
        missing_factors = []
        uncertain_factors = []
        
        for factor in self.heni_risk_factors:
            if factor not in rule_based_result:
                missing_factors.append(factor)
            elif rule_based_result[factor] < 0.3:  # Low confidence from rules
                uncertain_factors.append(factor)
        
        if not missing_factors and not uncertain_factors:
            return None  # No need for LLM
        
        prompt = f"""HENI Risk Factor Analysis for: {food_description}
Food Group: {food_group}

Task: Determine presence of these HENI risk factors (0-1 scale):
"""
        
        # Focus LLM only on missing or uncertain factors
        factors_to_analyze = missing_factors + uncertain_factors
        
        for factor in factors_to_analyze[:5]:  # Limit to 5 factors for efficiency
            factor_description = self._get_factor_description(factor)
            prompt += f"\n{factor}: {factor_description}"
        
        if rule_based_result:
            prompt += f"\n\nRule-based results (for context): {rule_based_result}"
        
        prompt += f"\n\nRespond with JSON only: {{\"factor_name\": score, ...}}\nScore 0 = not present, 1 = strongly present. Be precise and conservative."
        
        return prompt

    def categorize_food(self, food_id: int) -> Dict[str, float]:
        """Efficient food categorization: rule-based first, LLM as fallback/augmentation."""
        if food_id in self.categorization_cache:
            return self.categorization_cache[food_id]

        food_description = self.cnf_integrator.get_food_description(food_id)
        nutrient_data = self.cnf_integrator.get_nutrient_data(food_id)
        food_group = self.cnf_integrator.get_food_group(food_id)
        
        # Step 1: Always start with rule-based categorization (free and fast)
        rule_based_categories = RuleBasedCategorizer.categorize_heni_factors(
            food_group, nutrient_data, food_description
        )
        
        # Step 2: Use LLM only if needed and available
        final_categories = rule_based_categories.copy()
        
        if self.client and self._should_use_llm(rule_based_categories, food_description):
            try:
                self.logger.info(f"Using LLM augmentation for {food_description[:50]}...")
                prompt = self._create_heni_prompt(food_description, food_group, rule_based_categories)
                
                if prompt:  # Only query if there's something to ask
                    llm_response = self._query_llm_efficient(prompt)
                    llm_categories = self._parse_llm_json_response(llm_response)
                    
                    # Merge LLM results with rule-based (LLM fills gaps/validates)
                    final_categories = self._merge_categorizations(rule_based_categories, llm_categories)
            
            except Exception as e:
                self.logger.warning(f"LLM categorization failed for {food_id}, using rule-based only: {e}")
        
        # Step 3: Final validation and cleanup
        final_categories = self._validate_and_adjust_categories(
            final_categories, food_group, nutrient_data
        )
        
        self.categorization_cache[food_id] = final_categories
        return final_categories

    def _validate_and_adjust_categories(self, categories: Dict[str, float], food_group: str, nutrient_data: Dict) -> Dict[str, float]:
        if any(meat in food_group for meat in ["Beef Products", "Pork Products", "Lamb, Veal and Game"]) and "red_meat" not in categories and "processed_meat" not in categories:
            categories["red_meat"] = 1.0
            self.logger.warning(f"Forced 'red_meat' categorization for {food_group}")
        
        if "Finfish and Shellfish Products" in food_group:
            categories["seafood"] = max(categories.get("seafood", 0), 0.8)
        
        if "Beverages" in food_group and nutrient_data.get("SUGARS, TOTAL", 0) > 5:
            categories["sugar_sweetened_beverages"] = max(categories.get("sugar_sweetened_beverages", 0), 0.8)
        
        if nutrient_data.get("CALCIUM", 0) > 200:
            categories["calcium"] = max(categories.get("calcium", 0), 0.8)
        
        # Remove fiber from beverages
        if "Beverages" in food_group and "fiber" in categories:
            del categories["fiber"]
            self.logger.info(f"Removed 'fiber' category from beverage: {food_group}")
        
        # Ensure initially categorized items are not lost
        for category, score in initial_categories.items():
            if category not in categories:
                categories[category] = score
                self.logger.warning(f"Restored initial category {category} with score {score}")
        
        return {k: v for k, v in categories.items() if v >= 0.1}
    
    def _should_use_llm(self, rule_based_result: Dict[str, float], food_description: str) -> bool:
        """Determine if LLM should be used based on rule-based results quality."""
        # Use LLM only in specific cases to minimize cost
        
        # Case 1: No rule-based results (complete failure)
        if not rule_based_result:
            return True
        
        # Case 2: Very few factors identified (< 2 factors)
        if len(rule_based_result) < 2:
            return True
        
        # Case 3: All scores are very low (uncertain categorization)
        if all(score < 0.3 for score in rule_based_result.values()):
            return True
        
        # Case 4: Complex processed foods that need detailed analysis
        complex_indicators = ['processed', 'prepared', 'mixed', 'combo', 'dish', 'meal', 'recipe']
        if any(indicator in food_description.lower() for indicator in complex_indicators):
            return True
        
        # Case 5: Foods with ambiguous names
        ambiguous_indicators = ['other', 'misc', 'various', 'mixed', 'combination']
        if any(indicator in food_description.lower() for indicator in ambiguous_indicators):
            return True
        
        return False  # Use rule-based only for clear, simple cases
    
    def _get_factor_description(self, factor: str) -> str:
        """Get concise description of HENI risk factors for LLM."""
        descriptions = {
            'omega_3': 'Omega-3 fatty acids (EPA/DHA from fish, ALA from plants)',
            'calcium': 'Calcium content (dairy, leafy greens, fortified foods)',
            'fiber': 'Dietary fiber content (whole grains, fruits, vegetables)',
            'polyunsaturated_fatty_acids': 'PUFA content (vegetable oils, nuts, seeds)',
            'trans_fat': 'Trans fatty acids (processed foods, hydrogenated oils)',
            'sodium': 'Sodium content (salt, processed foods)',
            'nuts_seeds': 'Nuts and seeds as primary ingredient',
            'whole_grains': 'Whole grain content (brown rice, whole wheat, oats)',
            'fruits': 'Fresh, dried, or minimally processed fruits',
            'vegetables': 'Fresh, frozen, or minimally processed vegetables',
            'milk': 'Dairy products (milk, yogurt, cheese)',
            'sugar_sweetened_beverages': 'Added sugar drinks (sodas, juices with added sugar)',
            'red_meat': 'Red meat content (beef, pork, lamb)',
            'processed_meat': 'Processed meats (bacon, sausage, deli meats, ham)'
        }
        return descriptions.get(factor, f'{factor.replace("_", " ").title()} content')
    
    def _merge_categorizations(self, rule_based: Dict[str, float], llm_based: Dict[str, float]) -> Dict[str, float]:
        """Intelligently merge rule-based and LLM categorizations."""
        merged = rule_based.copy()
        
        for factor, llm_score in llm_based.items():
            if factor in merged:
                # If rule-based had low confidence, use LLM
                if merged[factor] < 0.3:
                    merged[factor] = llm_score
                # Otherwise, take weighted average favoring rule-based
                else:
                    merged[factor] = (merged[factor] * 0.7) + (llm_score * 0.3)
            else:
                # LLM identified new factor not caught by rules
                merged[factor] = llm_score
        
        return merged
    
    def _parse_llm_text_fallback(self, response: str) -> Dict[str, float]:
        """Fallback text parsing if JSON parsing fails."""
        categories = {}
        for line in response.split('\n'):
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    factor = parts[0].strip().lower().replace(' ', '_')
                    try:
                        score_text = parts[1].strip()
                        # Extract first number from the score text
                        import re
                        numbers = re.findall(r'0?\\.?\\d+', score_text)
                        if numbers:
                            score = float(numbers[0])
                            if factor in self.heni_risk_factors:
                                categories[factor] = max(0.0, min(1.0, score))
                    except (ValueError, IndexError):
                        continue
        return categories

    def _query_llm_efficient(self, prompt: str) -> str:
        """Cost-efficient LLM query with optimized parameters."""
        response = self.client.chat.completions.create(
            model=self.model,  # gpt-4o-mini for cost efficiency
            messages=[
                {
                    "role": "system", 
                    "content": "You are a precise nutrition expert. Analyze foods for HENI health risk factors. Respond concisely with JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content

    def _parse_llm_json_response(self, response: str) -> Dict[str, float]:
        """Parse JSON response from LLM with error handling."""
        categories = {}
        try:
            # Extract JSON from response (in case there's extra text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = response[json_start:json_end]
                parsed = json.loads(json_str)
                
                # Validate and convert to float
                for factor, score in parsed.items():
                    if factor in self.heni_risk_factors:
                        categories[factor] = max(0.0, min(1.0, float(score)))
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            self.logger.warning(f"Failed to parse LLM JSON response: {e}")
            # Fallback to text parsing
            categories = self._parse_llm_text_fallback(response)
        
        return categories