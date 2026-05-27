# api/urls.py

from django.urls import path, include
from .views import (
    cnf_views, environmental_views, food_views, translation_views,
    hsr_views_consolidated, fcs_views, hefi_views, heni_views,
    cnf_ai_search_views,                # AI-MATCH-1 (AI-enhanced CNF search + recipe decomposer)
    packaged_food_views,                # PKG-IMG-1 Phase 1 (image → NF panel → HSR)
    substitution_views,                 # SUBST-1 Phase 1 (ingredient substitution analyzer)
)
from .views.cnf_views import (
    # Food Management
    add_food_to_cnf, add_foods_batch, manage_cnf_food,
    
    # Search and Exploration
    search_cnf_foods, search_foods_by_nutrient, get_foods_by_group, compare_foods,
    
    # Reference Data
    get_food_groups_view, get_food_sources_view, get_nutrient_sources_view,
    get_nutrients_view, get_measures_view,
    
    # Reference Data Management
    add_food_source, add_nutrient_source, add_new_measure,
    
    # Data Quality and Analytics
    check_data_integrity, get_database_statistics,
    
    # Export
    export_foods_data,
    
)

urlpatterns = [
    # =============================================================================
    # Environmental Impact Assessment Endpoints - Comprehensive LCA Analysis
    # =============================================================================
    
    # Core Environmental Impact Analysis
    path('environmental-impact/', environmental_views.environmental_impact, name='environmental_impact'),
    path('environmental-impact/compare-foods/', environmental_views.compare_foods_environmental, name='compare_foods_environmental'),
    path('environmental-impact/food/<int:food_id>/profile/', environmental_views.food_environmental_profile, name='food_environmental_profile'),
    # Methodology metadata: lists available methodologies / perspectives /
    # countries / country-aware pathways for the frontend's Advanced panel.
    path('environmental-impact/methodology/', environmental_views.methodology_info, name='environmental_methodology_info'),

    # Enhanced food search
    path('search-food/', food_views.search_food_api, name='search_food_api'),
    path('food-filters/', food_views.get_food_filters_api, name='get_food_filters_api'),

    # Calculator endpoints
    # path('hsr-calculator/', food_views.calculate_hsr, name='calculate_hsr'),  # Implemented in HSR section
    path('fcs-calculator/', fcs_views.fcs_calculate, name='calculate_fcs'), 
    # path('heni-calculator/', food_views.calculate_heni, name='calculate_heni'),
    # path('net-health-impact/', food_views.calculate_net_health_impact, name='calculate_net_health_impact'),

    # Recipe endpoints (disabled - recipe_views not implemented yet)
    # path('recipes/', recipe_views.get_recipes, name='get_recipes'),
    # path('recipes/create/', recipe_views.create_recipe, name='create_recipe'),
    # path('recipes/<int:recipe_id>/', recipe_views.get_recipe, name='get_recipe'),
    # path('recipes/<int:recipe_id>/update/', recipe_views.update_recipe, name='update_recipe'),
    # path('recipes/<int:recipe_id>/delete/', recipe_views.delete_recipe, name='delete_recipe'),

    # =============================================================================
    # CNF (Canadian Nutrient File) Endpoints
    # =============================================================================
    
    # Food Management
    path('cnf/foods/', add_food_to_cnf, name='add_food_to_cnf'),
    path('cnf/foods/batch/', add_foods_batch, name='add_foods_batch'),
    path('cnf/foods/<int:food_id>/', manage_cnf_food, name='manage_cnf_food'),
    
    # Search and Exploration
    path('cnf/search/', search_cnf_foods, name='search_cnf_foods'),
    # AI-MATCH-1: free-text → CNF FoodID via embedding + LLM ranking (opt-in,
    # additive — the basic fuzzy search above is unchanged).
    path('cnf/search/ai-enhanced/', cnf_ai_search_views.cnf_ai_enhanced_search, name='cnf_ai_enhanced_search'),
    path('cnf/search/by-nutrient/', search_foods_by_nutrient, name='search_foods_by_nutrient'),
    path('cnf/groups/<int:food_group_id>/foods/', get_foods_by_group, name='get_foods_by_group'),
    path('cnf/compare/', compare_foods, name='compare_foods'),
    
    # Reference Data (Read-only)
    path('cnf/food-groups/', get_food_groups_view, name='get_food_groups'),
    path('cnf/food-sources/', get_food_sources_view, name='get_food_sources'),
    path('cnf/nutrient-sources/', get_nutrient_sources_view, name='get_nutrient_sources'),
    path('cnf/nutrients/', get_nutrients_view, name='get_nutrients'),
    path('cnf/measures/', get_measures_view, name='get_measures'),
    
    # Reference Data Management
    path('cnf/food-sources/add/', add_food_source, name='add_food_source'),
    path('cnf/nutrient-sources/add/', add_nutrient_source, name='add_nutrient_source'),
    path('cnf/measures/add/', add_new_measure, name='add_new_measure'),
    
    # Data Quality and Analytics
    path('cnf/integrity-check/', check_data_integrity, name='check_data_integrity'),
    path('cnf/statistics/', get_database_statistics, name='get_database_statistics'),
    
    # Export
    path('cnf/export/', export_foods_data, name='export_foods_data'),
    
    # Translation
    path('cnf/translate/', translation_views.translate_text, name='translate_text'),
    
    # =============================================================================
    # HSR (Health Star Rating) Endpoints - Enhanced with Scientific Improvements
    # =============================================================================
    
    # Core HSR Endpoints (Enhanced with Scientific Algorithm)
    # These maintain backward compatibility while using enhanced calculations
    path('hsr/calculate/', hsr_views_consolidated.calculate_hsr, name='calculate_hsr'),
    path('hsr/compare/', hsr_views_consolidated.compare_foods, name='compare_foods'),
    path('hsr/food/<int:food_id>/', hsr_views_consolidated.get_food_hsr_profile, name='get_food_hsr_profile'),
    path('hsr/meal-insights/', hsr_views_consolidated.get_meal_insights, name='get_meal_insights'),
    
    # Enhanced HSR Endpoints - Scientific Improvements and Advanced Analysis

    # =============================================================================
    # FCS (Food Compass Score 2.0) Endpoints - Comprehensive Nutritional Analysis
    # =============================================================================
    
    # Core FCS Endpoints using validated FCS 2.0 algorithm with 9-domain structure
    path('fcs/calculate/', fcs_views.fcs_calculate, name='fcs_calculate'),
    path('fcs/batch/', fcs_views.fcs_calculate_batch, name='fcs_calculate_batch'),
    path('fcs/food/<int:food_id>/', fcs_views.get_food_fcs_profile, name='get_food_fcs_profile'),
    path('fcs/compare/', fcs_views.compare_foods_fcs, name='compare_foods_fcs'),

    # =============================================================================
    # HEFI (Healthy Eating Food Index 2019) Endpoints - Canada's Food Guide Assessment
    # =============================================================================
    
    # Core HEFI Endpoints using validated HEFI-2019 algorithm with 10-component structure
    path('hefi/calculate/', hefi_views.hefi_calculate, name='hefi_calculate'),
    path('hefi/food/<int:food_id>/', hefi_views.get_food_hefi_profile, name='get_food_hefi_profile'),
    path('hefi/compare/', hefi_views.compare_foods_hefi, name='compare_foods_hefi'),

    # =============================================================================
    # HENI (Health Nutritional Impact) Endpoints - DALY-based Health Impact Analysis
    # =============================================================================
    
    # Core HENI Endpoints using evidence-based DALY methodology with 14 risk factors
    path('heni/calculate/', heni_views.heni_calculate, name='heni_calculate'),
    path('heni/food/<int:food_id>/profile/', heni_views.get_food_heni_profile, name='get_food_heni_profile'),

    # =============================================================================
    # AI-MATCH-1 (2026-05-23) — Recipe decomposer
    # =============================================================================
    # Free-text dish name → CNF ingredient list with masses, ready to feed
    # the HENI / HEFI / HSR / FCS scoring endpoints. Opt-in; rate-limited +
    # monthly-budgeted via the same machinery as /cnf/search/ai-enhanced.
    path('recipes/decompose/', cnf_ai_search_views.decompose_recipe, name='decompose_recipe'),

    # =============================================================================
    # AI-MATCH-2 (2026-05-24) — 24-hour dietary recall orchestrator
    # =============================================================================
    # Free-text occasion-by-occasion daily eating → aggregated CNF ingredient
    # list, ready to feed any of HEFI / HENI / HSR / FCS / Environmental.
    # Composes /recipes/decompose/ per meal; same rate-limit + circuit-breaker
    # machinery, cost = 5¢ per meal capped at 30¢.
    path('recipes/recall-24h/', cnf_ai_search_views.recall_24h, name='recall_24h'),

    # =============================================================================
    # DIET-PATTERN-1 (2026-05-24) — dietary-pattern resemblance classifier
    # =============================================================================
    # Daily ingredient list → cosine resemblance vs 7 (+1 optional) literature-
    # anchored prototype patterns (Mediterranean, DASH, Western, Vegetarian,
    # Vegan, CFG-Healthy, West African Staple, optional EAT-Lancet). Mass-
    # weighted day vectors in the same embedding space as the matcher; reuses
    # cnf_corpus_embeddings.npz. Per DIETARY_PATTERN_JUSTIFICATION.md.
    path('dietary-pattern/classify/',
         cnf_ai_search_views.dietary_pattern_classify,
         name='dietary_pattern_classify'),

    # =============================================================================
    # PKG-IMG-1 (2026-05-26) Phase 1 — packaged-food image → HSR
    # =============================================================================
    # Multimodal LLM extracts the Nutrition Facts panel from a user-uploaded
    # product photo; the user reviews + confirms the extracted values in an
    # editable form; HSR is then computed from the (possibly-edited) panel
    # without touching the existing CNF-FoodID path. Phase 2 will add an
    # ingredient-list path that feeds HEFI/HENI/dietary-pattern/environmental.
    path('packaged-food/extract/',
         packaged_food_views.packaged_food_extract,
         name='packaged_food_extract'),
    path('hsr/calculate-from-panel/',
         packaged_food_views.hsr_calculate_from_panel,
         name='hsr_calculate_from_panel'),
    # PKG-IMG-1 Phase 2 (2026-05-26) — adaptive NF + ingredient extraction
    # and CNF-decomposition for the 5 ingredient-list-dependent scorers.
    path('packaged-food/extract-combined/',
         packaged_food_views.packaged_food_extract_combined,
         name='packaged_food_extract_combined'),
    path('packaged-food/decompose-ingredients/',
         packaged_food_views.packaged_food_decompose_ingredients,
         name='packaged_food_decompose_ingredients'),

    # SUBST-1 Phase 1–3 — ingredient substitution analyzer
    path('substitution/analyze/',
         substitution_views.substitution_analyze,
         name='substitution_analyze'),
    path('substitution/apply/',
         substitution_views.substitution_apply,
         name='substitution_apply'),
    path('substitution/batch/',
         substitution_views.substitution_batch,
         name='substitution_batch'),

    # =============================================================================
    # User Management & Social Features
    # =============================================================================
    path('users/', include('users.urls')),
    
    # =============================================================================
    # Meal Creation & Sharing Platform
    # =============================================================================
    path('meals/', include('meals.urls')),

]