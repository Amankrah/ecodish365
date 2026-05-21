import logging
from typing import Any, Dict, List, Optional, Tuple
import openai
from ..database.cnf_integrator import HENICNFIntegrator
from ..config.heni_factors import HENI_RISK_FACTOR_KEYS
from .rule_based_categorizer import RuleBasedCategorizer
import json


_PROVIDER_DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
    "gemini": "gemini-2.5-flash",
}


class LLMFoodCategorizer:
    """Efficient LLM-based food categorizer for HENI risk factors.
    Uses rule-based categorization first, LLM only as fallback or augmentation.

    Supports per-provider routing for Scenario S1 multi-provider robustness
    checks (Ase et al., 2026 — multi-model "dominant" consensus matched or
    slightly beat any single model on every metric). The production default
    remains `openai`/`gpt-4o-mini` at temperature 0; alternative providers
    are lazy-imported so non-default Python clients (`anthropic`, `google-genai`)
    stay out of the default install footprint.
    """

    def __init__(
        self,
        cnf_integrator: HENICNFIntegrator,
        api_key: str,
        provider: str = "openai",
        model: Optional[str] = None,
    ):
        self.cnf_integrator = cnf_integrator
        self.heni_risk_factors = sorted(HENI_RISK_FACTOR_KEYS)
        self.categorization_cache = {}
        self.logger = logging.getLogger(__name__)

        # Provider routing — production default is openai/gpt-4o-mini.
        if provider not in _PROVIDER_DEFAULT_MODELS:
            raise ValueError(
                f"Unknown provider {provider!r}; expected one of "
                f"{sorted(_PROVIDER_DEFAULT_MODELS)}."
            )
        self.provider = provider
        self.model = model or _PROVIDER_DEFAULT_MODELS[provider]

        if provider == "openai":
            self.client = openai.OpenAI(api_key=api_key) if api_key else None
        elif provider == "anthropic":
            try:
                import anthropic  # lazy import; not in default requirements.
            except ImportError as exc:  # pragma: no cover - explicit error path
                raise ImportError(
                    "provider='anthropic' requires the `anthropic` package "
                    "(`pip install anthropic`). It is not in the default "
                    "requirements.txt; see GROUP-D-CODE-1.x-C in code_action_items.md."
                ) from exc
            self.client = anthropic.Anthropic(api_key=api_key) if api_key else None
        elif provider == "gemini":
            try:
                from google import genai  # lazy import; not in default requirements.
            except ImportError as exc:  # pragma: no cover - explicit error path
                raise ImportError(
                    "provider='gemini' requires the `google-genai` package "
                    "(`pip install google-genai`). It is not in the default "
                    "requirements.txt; see GROUP-D-CODE-1.x-C in code_action_items.md."
                ) from exc
            self.client = genai.Client(api_key=api_key) if api_key else None

        # Cost efficiency settings
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
        
        # Migrate legacy `fiber` key to source-split fiber_other/fiber_fvlw.
        # Per Stylianou 2021 SI §S2.9 (pp. 35-36), fibre routes to fiber_fvlw
        # when f/v/l/w is co-present, fiber_other otherwise.
        if "fiber" in categories:
            legacy_fiber = categories.pop("fiber")
            has_fvlw = any(
                k in categories for k in ("fruits", "vegetables", "legumes", "whole_grains")
            )
            target = "fiber_fvlw" if has_fvlw else "fiber_other"
            categories[target] = max(categories.get(target, 0.0), legacy_fiber)
            self.logger.info(
                f"Migrated legacy 'fiber' → '{target}' (food_group={food_group})"
            )

        # Remove all fibre signals from beverages (water, tea, coffee, broth,
        # juices: not a fibre source even if a label claims trace fibre).
        if "Beverages" in food_group:
            for fk in ("fiber_other", "fiber_fvlw"):
                if fk in categories:
                    del categories[fk]
                    self.logger.info(f"Removed '{fk}' from beverage: {food_group}")

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
        """Get concise description of HENI risk factors for the LLM prompt.

        Descriptions follow GBD 2017 Diet Collaborators (Lancet 2019;393:1960)
        exposure definitions and Stylianou 2021 SI §S2.9 fibre source-split.
        """
        descriptions = {
            # Nutrient factors
            'omega_3': 'Omega-3 fatty acids EPA + DHA from seafood (excludes ALA from plants per GBD 2017).',
            'calcium': 'Calcium content (dairy, leafy greens, fortified foods); g/serving.',
            'fiber_other': 'Dietary fibre from sources OTHER than fruits, vegetables, legumes or whole grains (CRC + IHD benefit per Stylianou SI S2.9).',
            'fiber_fvlw': 'Dietary fibre from fruits, vegetables, legumes, or whole grains (CRC benefit only; IHD already counted via f/v/l/w DRFs).',
            'polyunsaturated_fatty_acids': 'PUFA from all sources, mainly omega-6 vegetable oils (per GBD 2017 PUFA = omega-6).',
            'trans_fat': 'Trans fatty acids from PHVOs and ruminant products.',
            'sodium': 'Sodium content (salt, processed foods); g/serving (urinary→dietary factor 0.85).',
            # Food-group factors
            'nuts_seeds': 'Nuts and seeds as a primary ingredient.',
            'whole_grains': 'Whole-grain foods (bran/germ/endosperm in natural proportion per GBD 2017).',
            'fruits': 'Fresh, frozen, cooked, canned or dried fruits; EXCLUDES fruit juices, salted, or pickled.',
            'vegetables': 'Fresh, frozen, cooked, canned or dried vegetables; EXCLUDES legumes, salted/pickled, juices, nuts, seeds, starchy veg (potatoes/corn).',
            'legumes': 'Fresh, frozen, cooked, canned or dried legumes (lentils, chickpeas, beans, soybeans, tofu).',
            'milk': 'Non-fat / low-fat / full-fat dairy milk; EXCLUDES soy milk and plant derivatives per GBD 2017.',
            'sugar_sweetened_beverages': 'Beverages ≥ 50 kcal per 226.8 g serving; EXCLUDES 100% fruit/veg juices, water, tea, coffee.',
            'red_meat': 'Beef, pork, lamb, goat; EXCLUDES poultry, fish, eggs, all processed meats.',
            'processed_meat': 'Meat preserved by smoking, curing, salting, or chemical preservatives.',
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
        """Cost-efficient LLM query with optimized parameters.

        Routes through the active provider. All three providers run at
        `self.temperature` (0) for determinism, deliberately distinct from
        Ase et al. (2026) `temperature=1.0`; their numbers therefore are not
        a like-for-like baseline for this categorizer.
        """
        system_prompt = (
            "You are a precise nutrition expert. Analyze foods for HENI "
            "health risk factors. Respond concisely with JSON only."
        )

        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return response.choices[0].message.content

        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            # Anthropic returns a list of content blocks; concatenate text.
            return "".join(
                block.text for block in response.content if getattr(block, "text", None)
            )

        if self.provider == "gemini":
            # google-genai unified API.
            response = self.client.models.generate_content(
                model=self.model,
                contents=f"{system_prompt}\n\n{prompt}",
                config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                },
            )
            return response.text

        raise RuntimeError(f"Unreachable: unknown provider {self.provider!r}")  # pragma: no cover

    def categorize_food_with_audit(
        self, food_id: int
    ) -> Tuple[Dict[str, float], Dict[str, Any]]:
        """Like categorize_food(), but additionally returns a structured audit dict.

        Audit dict schema (for Scenario S1 per-factor reporting and per-provider
        ablation):
            {
                "food_id": int,
                "rule_confidence_per_factor": Dict[str, float],
                "llm_invoked": bool,
                "llm_provider": str | None,   # None when LLM not invoked
                "llm_model": str | None,
                "llm_factors_queried": List[str],
                "llm_response_raw": str | None,
                "merge_strategy": str,    # "rule_only" | "llm_fills_gaps"
                "final_scores": Dict[str, float],
            }

        The existing categorize_food() signature is unchanged.
        """
        food_description = self.cnf_integrator.get_food_description(food_id)
        nutrient_data = self.cnf_integrator.get_nutrient_data(food_id)
        food_group = self.cnf_integrator.get_food_group(food_id)

        rule_based_categories = RuleBasedCategorizer.categorize_heni_factors(
            food_group, nutrient_data, food_description
        )
        rule_confidence_snapshot = dict(rule_based_categories)

        audit: Dict[str, Any] = {
            "food_id": food_id,
            "rule_confidence_per_factor": rule_confidence_snapshot,
            "llm_invoked": False,
            "llm_provider": None,
            "llm_model": None,
            "llm_factors_queried": [],
            "llm_response_raw": None,
            "merge_strategy": "rule_only",
            "final_scores": {},
        }

        final_categories = rule_based_categories.copy()

        if self.client and self._should_use_llm(rule_based_categories, food_description):
            try:
                prompt = self._create_heni_prompt(
                    food_description, food_group, rule_based_categories
                )
                if prompt:
                    factors_queried: List[str] = []
                    for factor in self.heni_risk_factors:
                        if (
                            factor not in rule_based_categories
                            or rule_based_categories[factor] < 0.3
                        ):
                            factors_queried.append(factor)
                    factors_queried = factors_queried[:5]

                    llm_response_raw = self._query_llm_efficient(prompt)
                    llm_categories = self._parse_llm_json_response(llm_response_raw)
                    final_categories = self._merge_categorizations(
                        rule_based_categories, llm_categories
                    )

                    audit.update(
                        llm_invoked=True,
                        llm_provider=self.provider,
                        llm_model=self.model,
                        llm_factors_queried=factors_queried,
                        llm_response_raw=llm_response_raw,
                        merge_strategy="llm_fills_gaps",
                    )
            except Exception as exc:  # noqa: BLE001 - audit-only fallthrough
                self.logger.warning(
                    f"LLM categorization failed for {food_id}, using rule-based only: {exc}"
                )
                audit["llm_response_raw"] = f"ERROR: {exc!r}"

        final_categories = self._validate_and_adjust_categories(
            final_categories, food_group, nutrient_data
        )
        audit["final_scores"] = dict(final_categories)

        self.categorization_cache[food_id] = final_categories
        return final_categories, audit

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