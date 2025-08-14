import axios from 'axios';

// Use the correct API base URL from environment
// In development, call backend directly; in production, use environment URL
// Resolve base URL and ensure it includes the /api prefix in production
const resolveApiBaseUrl = (): string => {
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:8000/api';
  }
  const raw = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').trim();
  // If the env already includes '/api', keep it; otherwise, append it
  const hasApiSuffix = /\/api\/?$/.test(raw);
  const normalized = raw.replace(/\/$/, '');
  return hasApiSuffix ? normalized : `${normalized}/api`;
};

const API_BASE_URL = resolveApiBaseUrl();

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for authentication
api.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const data = error.response?.data;
    const message = error.message;
    const url = error.config?.url;

    // Downgrade expected client errors (e.g., 400 from short queries) to warnings
    if (status && status < 500) {
      console.warn('API Warning:', { status, url, data, message });
    } else {
      console.error('API Error:', { status, url, data, message });
    }
    return Promise.reject(error);
  }
);

// Types
export interface Food {
  FoodID: number;
  FoodCode: string;
  FoodDescription: string;
  FoodDescriptionF: string;
  FoodGroupID: number;
  FoodGroupName?: string;
  FoodSourceID: number;
  FoodSourceDescription?: string;
  CountryCode: string;
  ScientificName?: string;
  NutrientValues: NutrientValue[];
  ConversionFactors: ConversionFactor[];
}

export interface NutrientValue {
  NutrientID: number;
  NutrientName: string;
  NutrientValue: number;
  NutrientUnit: string;
  NutrientSourceID: number;
  NutrientSourceDescription: string;
}

export interface ConversionFactor {
  MeasureID: number;
  MeasureDescription: string;
  ConversionFactorValue: number;
}

export interface SearchResult {
  results: {
    FoodID: number;
    FoodCode: string;
    FoodDescription: string;
    FoodDescriptionF: string;
    FoodGroupID: number;
    relevance: number;
  }[];
  total: number;
  query: string;
  limit: number;
  offset: number;
  has_more: boolean;
  filters?: {
    available_categories: string[];
    available_methods: string[];
    applied_filters?: {
      category?: string;
      method?: string;
    };
  };
}

export interface FoodGroup {
  FoodGroupID: number;
  FoodGroupName: string;
}

export interface Nutrient {
  NutrientID: number;
  NutrientName: string;
  NutrientUnit?: string;
}

export interface FoodSource {
  FoodSourceID: number;
  FoodSourceDescription: string;
}

export interface NutrientSource {
  NutrientSourceID: number;
  NutrientSourceDescription: string;
}

export interface Measure {
  MeasureID: number;
  MeasureDescription: string;
}

export interface SearchCriteria {
  nutrient_id: number;
  min_value?: number;
  max_value?: number;
  limit: number;
}

export interface FoodComparison {
  foods: {
    FoodID: number;
    FoodDescription: string;
    FoodGroup: string;
  }[];
  nutrients: Record<string, {
    nutrient_id: number;
    unit: string;
    values: Record<string, number>;
  }>;
  comparison_date: string;
}

export interface IntegrityCheck {
  timestamp: string;
  checks: Record<string, {
    count: number;
    status: 'passed' | 'warning' | 'failed';
    details: number[] | { FoodID: number; FoodDescription: string }[];
  }>;
  overall_status: 'passed' | 'warning' | 'failed';
}

export interface DatabaseStats {
  timestamp: string;
  food_count: number;
  nutrient_records: number;
  conversion_records: number;
  food_groups: number;
  food_sources: number;
  nutrient_types: number;
  nutrient_sources: number;
  measures: number;
  foods_by_group: Record<string, number>;
  top_nutrients: Record<string, number>;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  details?: string | string[];
}

// Enhanced Search Interface
export interface EnhancedSearchOptions {
  query: string;
  category?: string;
  method?: string;
  limit?: number;
  offset?: number;
}

// Filter Options
export interface FilterOptions {
  categories: string[];
  methods: string[];
}

// API Service Class
export class CNFApiService {
  // Enhanced Search & Exploration
  static async searchFoods(query: string, limit = 50, offset = 0): Promise<SearchResult> {
    const response = await api.get(`/cnf/search/`, {
      params: { q: query, limit, offset }
    });
    return response.data.data;
  }

  static async searchFoodsEnhanced(options: EnhancedSearchOptions): Promise<SearchResult> {
    const params: Record<string, string | number> = {
      query: options.query,
      limit: options.limit || 50,
      offset: options.offset || 0
    };
    
    if (options.category) {
      params.category = options.category;
    }
    
    if (options.method) {
      params.method = options.method;
    }
    
    const response = await api.get(`/search-food/`, {
      params
    });
    
    // The enhanced search returns data directly, not wrapped in a data property
    return response.data;
  }

  static async getFoodFilters(): Promise<FilterOptions> {
    const response = await api.get(`/food-filters/`);
    return response.data;
  }

  static async searchFoodsByNutrient(
    nutrientId: number,
    minValue?: number,
    maxValue?: number,
    limit = 50
  ): Promise<{ foods: Food[]; search_criteria: SearchCriteria }> {
    const params: Record<string, string | number> = { nutrient_id: nutrientId, limit };
    if (minValue !== undefined) params.min_value = minValue;
    if (maxValue !== undefined) params.max_value = maxValue;

    const response = await api.get(`/cnf/search/by-nutrient/`, { params });
    return response.data.data;
  }

  static async getFoodsByGroup(foodGroupId: number, limit = 100): Promise<{
    foods: Partial<Food>[];
    food_group_id: number;
    count: number;
    limit: number;
  }> {
    const response = await api.get(`/cnf/groups/${foodGroupId}/foods/`, {
      params: { limit }
    });
    return response.data.data;
  }

  static async compareFoods(foodIds: number[], nutrientIds?: number[]): Promise<FoodComparison> {
    const response = await api.post(`/cnf/compare/`, {
      food_ids: foodIds,
      nutrient_ids: nutrientIds
    });
    return response.data.data;
  }

  // Food Management
  static async getFoodDetails(foodId: number): Promise<Food> {
    const response = await api.get(`/cnf/foods/${foodId}/`);
    return response.data.data;
  }

  static async addFood(foodData: Partial<Food>): Promise<{ food_id: number; food_description: string }> {
    const response = await api.post(`/cnf/foods/`, foodData);
    return response.data.data;
  }

  static async updateFood(foodId: number, foodData: Partial<Food>): Promise<Food> {
    const response = await api.put(`/cnf/foods/${foodId}/`, foodData);
    return response.data.data;
  }

  static async deleteFood(foodId: number): Promise<void> {
    await api.delete(`/cnf/foods/${foodId}/`);
  }

  // Reference Data
  static async getFoodGroups(): Promise<FoodGroup[]> {
    const response = await api.get(`/cnf/food-groups/`);
    return response.data.data;
  }

  static async getNutrients(): Promise<Nutrient[]> {
    const response = await api.get(`/cnf/nutrients/`);
    return response.data.data;
  }

  static async getFoodSources(): Promise<FoodSource[]> {
    const response = await api.get(`/cnf/food-sources/`);
    return response.data.data;
  }

  static async getNutrientSources(): Promise<NutrientSource[]> {
    const response = await api.get(`/cnf/nutrient-sources/`);
    return response.data.data;
  }

  static async getMeasures(): Promise<Measure[]> {
    const response = await api.get(`/cnf/measures/`);
    return response.data.data;
  }

  // Analytics & Quality
  static async getDatabaseStatistics(): Promise<DatabaseStats> {
    const response = await api.get(`/cnf/statistics/`);
    return response.data.data;
  }

  static async checkDataIntegrity(): Promise<IntegrityCheck> {
    const response = await api.get(`/cnf/integrity-check/`);
    return response.data.data;
  }

  // Export
  static async exportFoodsData(
    foodIds: number[],
    options: {
      format?: string;
      include_nutrients?: boolean;
      include_conversions?: boolean;
    } = {}
  ): Promise<{
    foods: Food[];
    export_info: {
      total_requested: number;
      total_exported: number;
      format: string;
      include_nutrients: boolean;
      include_conversions: boolean;
      export_date: string;
    };
  }> {
    const response = await api.post(`/cnf/export/`, {
      food_ids: foodIds,
      ...options
    });
    return response.data.data;
  }
}

// HSR Types
export interface HSRCalculationRequest {
  food_ids: number[];
  serving_sizes: number[];
  analysis_level?: 'simple' | 'detailed';
  include_alternatives?: boolean;
  include_meal_insights?: boolean;
}

export interface HSRComparisonRequest {
  food_ids: number[];
  serving_size: number;
  sort_by?: 'hsr_rating' | 'energy' | 'protein' | 'sodium' | 'fiber';
}

export interface HSRMealInsightsRequest {
  food_ids: number[];
  serving_sizes: number[];
  meal_type?: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  dietary_goals?: ('weight_loss' | 'heart_health' | 'diabetes_management')[];
}

export interface HSRRating {
  star_rating: number;
  level: 'poor' | 'below_average' | 'average' | 'good' | 'excellent';
  description: string;
  category: string;
}

export interface HSRScoreBreakdown {
  final_score: number;
  baseline_points: number;
  modifying_points: number;
  components: {
    energy: number;
    saturated_fat: number;
    sugar: number;
    sodium: number;
    protein: number;
    fiber: number;
    fvnl: number;
  };
  // Additional components from the scientific algorithm
  advanced_components?: {
    sugar_natural?: number;
    sugar_added?: number;
    satiety_adjustment?: number;
    processing_penalty?: number;
    naturalness_bonus?: number;
  };
}

export interface NutrientAnalysis {
  nutrient: string;
  value: number;
  unit: string;
  points: number;
  impact: string;
  recommendation?: string;
}

export interface HealthInsight {
  title: string;
  description: string;
  category: 'strength' | 'concern' | 'recommendation';
  priority: 'high' | 'medium' | 'low';
  actionable: boolean;
  action_text?: string;
}

// Simplified meal categorization interface
export interface MealCategorization {
  final_category: string;
  category_confidence: number;
  reasoning: string;
  nutritional_rationale?: string;
  scientific_method?: string;
  category_warnings?: string[];
  category_breakdown?: Record<string, number | string>;
  alternative_categories?: Array<{
    category: string;
    fitness_score: number;
    explanation: string;
  }>;
}

export interface HSRResult {
  success: boolean;
  hsr_result: {
    rating: HSRRating;
    score_breakdown: HSRScoreBreakdown;
    nutritional_analysis: NutrientAnalysis[];
    health_insights: {
      strengths: HealthInsight[];
      concerns: HealthInsight[];
      recommendations: HealthInsight[];
    };
    validation: {
      confidence_score: number;
      warnings: string[];
    };
    healthier_alternatives?: Array<{
      category: string;
      suggestions: string[];
    }>;
    meal_insights?: {
      meal_composition: {
        total_foods: number;
        total_weight: number;
        dominant_category: string;
        energy_density: number;
      };
      nutritional_balance: {
        protein_adequate: boolean;
        fiber_adequate: boolean;
        sodium_concern: boolean;
        sugar_concern: boolean;
      };
      meal_suitability: string;
    };
    // Sugar source analysis
    sugar_source_analysis?: {
      natural_sugars: number;
      added_sugars: number;
      natural_percentage: number;
      sources?: string[];
    };
    // Satiety analysis
    satiety_analysis?: {
      satiety_index: number;
      processing_level: string;
      liquid_percentage?: number;
    };
  };
  food_details: Array<{
    food_id: number;
    food_name: string;
    serving_size: number;
    category: string;
    fvnl_percent: number;
    food_group_id?: number;
    category_confidence?: number;
    category_source?: string;
  }>;
  meal_categorization?: MealCategorization;
}

export interface HSRComparison {
  success: boolean;
  comparison: {
    serving_size: number;
    sort_by: string;
    total_foods: number;
    successfully_analyzed: number;
    foods: Array<{
      food_id: number;
      food_name: string;
      serving_size: number;
      food_group: string;
      hsr_rating: number;
      hsr_level: string;
      category: string;
      energy_kj: number;
      key_nutrients: {
        protein: number;
        saturated_fat: number;
        sugar: number;
        sodium: number;
        fiber: number;
        fvnl_percent: number;
      };
      top_strength?: string;
      top_concern?: string;
    }>;
    summary: {
      highest_rated: {
        food_id: number;
        food_name: string;
        hsr_rating: number;
        hsr_level: string;
      } | null;
      lowest_rated: {
        food_id: number;
        food_name: string;
        hsr_rating: number;
        hsr_level: string;
      } | null;
      average_rating: number;
      rating_distribution: {
        excellent: number;
        good: number;
        average: number;
        below_average: number;
        poor: number;
      };
    };
    recommendations: string[];
  };
}

export interface HSRFoodProfile {
  success: boolean;
  food_profile: {
    basic_info: {
      food_id: number;
      food_name: string;
      serving_size: number;
      food_group: string;
      hsr_category: string;
      fvnl_percent: number;
    };
    hsr_analysis: {
      rating: HSRRating;
      score_breakdown: HSRScoreBreakdown;
      nutritional_analysis: NutrientAnalysis[];
      health_insights: {
        strengths: HealthInsight[];
        concerns: HealthInsight[];
        recommendations: HealthInsight[];
      };
      validation: {
        confidence_score: number;
        warnings: string[];
      };
    };
    nutritional_highlights: {
      high_in: string[];
      low_in: string[];
      good_source_of: string[];
    };
    usage_recommendations: string[];
    healthier_alternatives?: Array<{
      category: string;
      suggestions: string[];
    }>;
  };
}

export interface HSRMealInsights {
  success: boolean;
  meal_insights: {
    meal_composition: {
      total_foods: number;
      total_weight: number;
      food_group_distribution: Record<string, number>;
      dominant_groups: Array<[string, number]>;
    };
    nutritional_balance: {
      macronutrient_distribution: {
        protein_percent: number;
        carbohydrate_percent: number;
        fat_percent: number;
      };
      nutrient_density: {
        protein_per_100g: number;
        fiber_per_100g: number;
        sodium_per_100g: number;
        fvnl_percent: number;
      };
      nutritional_quality: {
        high_protein: boolean;
        high_fiber: boolean;
        high_fvnl: boolean;
        low_sodium: boolean;
        low_sugar: boolean;
      };
    };
    hsr_breakdown: {
      final_rating: number;
      rating_level: string;
      score_components: {
        risk_nutrients: {
          energy: number;
          saturated_fat: number;
          sugar: number;
          sodium: number;
          total: number;
        };
        beneficial_nutrients: {
          protein: number;
          fiber: number;
          fvnl: number;
          total: number;
        };
        final_score: number;
      };
    };
    improvement_opportunities: Array<{
      area: string;
      current: number;
      target: number;
      suggestion: string;
    }>;
    meal_type_suitability?: {
      meal_type: string;
      suitability_score: number;
      criteria_met: Record<string, boolean>;
      recommendation: string;
    } | null;
    dietary_goal_alignment?: Record<string, {
      score: number;
      [key: string]: boolean | number | string;
    }> | null;
  };
  food_details: Array<{
    food_id: number;
    food_name: string;
    serving_size: number;
    category: string;
    fvnl_percent: number;
    food_group_id?: number;
    category_confidence?: number;
    category_source?: string;
  }>;
  meal_categorization: MealCategorization;
}

// HSR API Service Class
export class HSRApiService {
  static async calculateHSR(request: HSRCalculationRequest): Promise<HSRResult> {
    const response = await api.post('/hsr/calculate/', request);
    return response.data;
  }

  static async compareFoods(request: HSRComparisonRequest): Promise<HSRComparison> {
    const response = await api.post('/hsr/compare/', request);
    return response.data;
  }

  static async getFoodHSRProfile(
    foodId: number,
    servingSize = 100,
    includeAlternatives = false
  ): Promise<HSRFoodProfile> {
    const response = await api.get(`/hsr/food/${foodId}/`, {
      params: {
        serving_size: servingSize,
        include_alternatives: includeAlternatives
      }
    });
    return response.data;
  }

  static async getMealInsights(request: HSRMealInsightsRequest): Promise<HSRMealInsights> {
    const response = await api.post('/hsr/meal-insights/', request);
    return response.data;
  }
}

// FCS Types
export interface FCSCalculationRequest {
  food_ids: number[];
  food_names?: string[];
}

export interface FCSBatchRequest {
  foods: Array<{
    food_ids: number[];
    food_name: string;
  }>;
}

export interface FCSComparisonRequest {
  foods: Array<{
    food_ids: number[];
    food_name: string;
  }>;
}

export interface FoodProcessingDetail {
  food_id: number;
  food_name: string;
  nova_level: number;
  nova_category: string;
  energy_kcal: number;
  energy_weight: number;
}

export interface ProcessingDetails {
  is_mixed_dish: boolean;
  individual_foods: FoodProcessingDetail[];
  energy_weights: number[];
  final_processing_level?: number;
}

export interface FCSResult {
  name: string;
  original_score: number;
  fcs: number;
  nova_category: string;
  processing_details?: ProcessingDetails;
}

export interface FCSBatchResult {
  results: FCSResult[];
  total_processed: number;
  successful: number;
}

export interface FCSFoodProfile {
  food_id: number;
  food_name: string;
  fcs_summary: FCSResult;
  domain_breakdown: Record<string, Record<string, {
    value: number;
    score: number;
    type: string;
  }>>;
  attributes_count: number;
}

export interface FCSComparison {
  foods: Array<FCSResult & {
    domain_scores: Record<string, number>;
  }>;
  comparison_insights: {
    highest_fcs: {
      food: string;
      fcs: number;
      nova_category: string;
    };
    lowest_fcs: {
      food: string;
      fcs: number;
      nova_category: string;
    };
    fcs_range: number;
    average_fcs: number;
  };
  foods_count: number;
}

// HEFI Types
export interface HEFICalculationRequest {
  foods: Array<{
    food_id: number;
    amount_g: number;
  }>;
}

export interface HEFIComparisonRequest {
  foods: Array<{
    food_ids?: number[];
    food_name?: string;
    amount_g?: number;
    food_items?: Array<{ food_id: number; amount_g: number }>
  }>;
}

export interface HEFIComponentScore {
  c1_vf: number;
  c2_wholegr: number;
  c3_grratio: number;
  c4_profoods: number;
  c5_plantpro: number;
  c6_beverages: number;
  c7_fattyacid: number;
  c8_sfat: number;
  c9_freesugars: number;
  c10_sodium: number;
}

export interface HEFIRatios {
  RATIO_VF: number;
  RATIO_WGTOT: number;
  RATIO_WGGR: number;
  RATIO_PRO: number;
  RATIO_PLANT: number;
  RATIO_BEV: number;
  RATIO_UNSFAT: number;
  SFA_PERC: number;
  SUG_PERC: number;
  SODDEN: number;
}

export interface HEFIInterpretation {
  category: 'Below Average' | 'Below Average to Average' | 'Above Average' | 'Excellent';
  description: string;
  score: number;
  population_benchmarks?: {
    mean: number;
    percentile_1: number;
    percentile_99: number;
  };
  notes?: string[];
  ui_color?: 'red' | 'yellow' | 'green' | 'emerald';
}

export interface HEFIInputs {
  total_foods_ra: number;
  energy_kcal: number;
  vf_ra: number;
  whole_grains_ra: number;
  total_grains_ra: number;
  protein_foods_ra: number;
  plant_protein_foods_ra: number;
  total_beverages_g: number;
  recommended_beverages_g: number;
  sfa_g: number;
  mufa_g: number;
  pufa_g: number;
  free_sugars_g: number;
  sodium_mg: number;
}

export interface HEFIResult {
  success: boolean;
  data: {
    food_ids: number[];
    food_name?: string;
    total_score: number;
    max_total_score: number;
    percentage: number;
    ratios: HEFIRatios;
    components: {
      [key: string]: {
        score: number;
        max_points: number;
        name: string;
      };
    };
    inputs: HEFIInputs;
    hefi_interpretation?: HEFIInterpretation;
  };
}

export interface HEFIFoodProfile {
  success: boolean;
  data: {
    food_ids: number[];
    food_name: string;
    total_score: number;
    max_total_score: number;
    percentage: number;
    ratios: HEFIRatios;
    components: {
      [key: string]: {
        score: number;
        max_points: number;
        name: string;
      };
    };
    inputs: HEFIInputs;
    measure_info: {
      conversion_factor: number;
      measure_description?: string;
      measure_id?: number;
    };
    hefi_interpretation: HEFIInterpretation;
  };
}

export interface HEFIComparison {
  success: boolean;
  data: {
    foods: Array<{
      food_ids: number[];
      food_name: string;
      total_score: number;
      max_total_score: number;
      percentage: number;
      ratios?: HEFIRatios;
      components: {
        [key: string]: {
          score: number;
          max_points: number;
          name: string;
        };
      };
      inputs?: HEFIInputs;
      hefi_interpretation?: HEFIInterpretation;
      error?: string;
    }>;
    comparison_insights: {
      highest_score?: number;
      lowest_score?: number;
      average_score?: number;
      score_range?: number;
      best_performing?: string;
      component_analysis?: {
        [key: string]: {
          variation: number;
          max_score: number;
          min_score: number;
          component_name: string;
        };
      };
      message?: string;
    };
    total_compared: number;
  };
}

// HEFI API Service Class
export class HEFIApiService {
  static async calculateHEFI(request: HEFICalculationRequest): Promise<HEFIResult> {
    const response = await api.post('/hefi/calculate/', request);
    return response.data;
  }

  static async getFoodHEFIProfile(foodId: number, amount_g = 100): Promise<HEFIFoodProfile> {
    const response = await api.get(`/hefi/food/${foodId}/`, {
      params: { amount_g }
    });
    return response.data;
  }

  static async compareFoodsHEFI(request: HEFIComparisonRequest): Promise<HEFIComparison> {
    const response = await api.post('/hefi/compare/', request);
    return response.data;
  }
}

// FCS API Service Class
export class FCSApiService {
  static async calculateFCS(request: FCSCalculationRequest): Promise<{ data: FCSResult }> {
    const response = await api.post('/fcs/calculate/', request);
    // Backend returns { success: true, data: FCSResult, message: string }
    console.log('Raw backend response:', response.data);
    const result = { data: response.data.data };
    console.log('API service returning:', result);
    return result;
  }

  static async calculateFCSBatch(request: FCSBatchRequest): Promise<{ data: FCSBatchResult }> {
    const response = await api.post('/fcs/batch/', request);
    return { data: response.data.data };
  }

  static async getFoodFCSProfile(foodId: number): Promise<{ data: FCSFoodProfile }> {
    const response = await api.get(`/fcs/food/${foodId}/`);
    return { data: response.data.data };
  }

  static async compareFoodsFCS(request: FCSComparisonRequest): Promise<{ data: FCSComparison }> {
    const response = await api.post('/fcs/compare/', request);
    return { data: response.data.data };
  }
}

// HENI Types
export interface HENICalculationRequest {
  meal: Array<{
    food_id: number;
    amount: number;
    unit?: string;
  }>;
}

export interface HENIFoodProfileRequest {
  food_id: number;
  amount_g?: number;
}

export interface HENIDietaryPatternRequest {
  dietary_pattern: {
    meals: Array<{
      meal_name: string;
      foods: Array<{
        food_id: number;
        amount: number;
        unit?: string;
      }>;
    }>;
    parameters?: {
      population_size?: number;
      time_horizon_years?: number;
    };
  };
}

export interface HENIScores {
  total_heni_score: number;
  heni_per_100_kcal: number;
  heni_per_100_grams: number;
  confidence_level?: number;
}

export interface HealthImpact {
  health_impact_minutes: number;
  health_impact_dalys: number;
  description: string;
}

export interface ComponentBreakdown {
  food_group_contributions: Record<string, number>;
  nutrient_contributions: Record<string, number>;
  total_positive_contributions: number;
  total_negative_contributions: number;
}

export interface RiskFactorAnalysis {
  risk_factors: Record<string, number>;
  warnings: string[];
  confidence_scores: Record<string, number>;
}

export interface DiseaseImpactAnalysis {
  cardiovascular: number;
  cancer: number;
  metabolic: number;
  neurological: number;
  musculoskeletal: number;
  other: number;
}

export interface MealComposition {
  total_energy_kcal: number;
  total_weight_grams: number;
  food_count: number;
  macronutrient_distribution: {
    protein_percent: number;
    carbohydrate_percent: number;
    fat_percent: number;
  };
}

export interface HENIResult {
  success: boolean;
  data: {
    heni_scores: HENIScores;
    health_impact: HealthImpact;
    component_breakdown: ComponentBreakdown;
    risk_factor_analysis: RiskFactorAnalysis;
    disease_burden_analysis?: DiseaseImpactAnalysis;
    meal_composition: MealComposition;
  };
  metadata?: {
    calculation_method: string;
    reference: string;
    last_updated: string;
    units: string;
  };
}

export interface HENIFoodProfile {
  success: boolean;
  data: {
    food_details: {
      food_id: number;
      food_name: string;
      food_group: string;
      amount_analyzed_g: number;
    };
    heni_analysis: {
      heni_scores: HENIScores;
      health_impact: HealthImpact;
      component_breakdown: ComponentBreakdown;
      risk_factor_analysis: RiskFactorAnalysis;
      disease_burden_analysis: DiseaseImpactAnalysis;
      meal_composition: MealComposition;
    };
    research_insights: {
      primary_health_drivers: Array<{
        factor: string;
        impact: number;
        direction: 'protective' | 'risk';
        mechanism: string;
      }>;
      epidemiological_evidence: {
        quality: 'High' | 'Moderate' | 'Low';
        confidence: number;
        studies?: Array<{
          title: string;
          finding: string;
        }>;
      };
      population_impact_estimate: {
        dalys_per_100k: number;
        economic_value_usd: number;
        years_affected: number;
        confidence_interval?: string;
      };
    };
    policy_recommendations: {
      recommendations: Array<{
        priority: 'High' | 'Medium' | 'Low';
        title: string;
        description: string;
        implementation: string;
      }>;
      regulatory_status?: string;
      implementation_priority?: 'High' | 'Medium' | 'Low';
    };
    comparison_benchmarks: {
      similar_foods: Array<{
        name: string;
        heni_score: number;
        health_impact: number;
      }>;
    };
  };
}

export interface HENIDietaryPatternResult {
  success: boolean;
  data: {
    dietary_pattern_summary: {
      total_meals_analyzed: number;
      daily_heni_score: number;
      daily_energy_kcal: number;
      daily_health_impact_minutes: number;
      pattern_classification: 'Healthy' | 'Moderate' | 'Poor';
    };
    meal_breakdowns: Array<{
      meal_name: string;
      heni_scores: HENIScores;
      health_impact: HealthImpact;
      component_breakdown: ComponentBreakdown;
      risk_factor_analysis: RiskFactorAnalysis;
      meal_composition: MealComposition;
    }>;
    population_health_impact: {
      total_dalys_avoided: number;
      economic_value_usd: number;
      projected_dalys_avoided: number;
      health_economic_value: number;
      time_horizon_years: number;
    };
    policy_insights: {
      intervention_priority: Array<{
        priority: 'High' | 'Medium' | 'Low';
        title: string;
        description: string;
        impact: string;
      }>;
      target_food_groups: Array<{
        name: string;
        impact: number;
        action: 'increase' | 'decrease';
      }>;
      expected_impact_per_serving_change: Array<{
        food_group: string;
        impact: number;
        recommendation: string;
      }>;
    };
    epidemiological_context: {
      primary_disease_burdens: Array<{
        disease: string;
        percentage: number;
      }>;
      risk_factor_contributions: Record<string, number>;
      evidence_strength: string;
    };
  };
  metadata?: {
    analysis_type: string;
    population_scope: string;
    methodology: string;
  };
}

// HENI API Service Class
export class HENIApiService {
  static async calculateHENI(request: HENICalculationRequest): Promise<HENIResult> {
    const response = await api.post('/heni/calculate/', request);
    // Backend returns nested structure: { data: { success: true, data: {...} } }
    return {
      success: response.data.data.success,
      data: response.data.data.data,
      metadata: response.data.data.metadata
    };
  }

  static async getFoodHENIProfile(foodId: number, amount_g = 100): Promise<HENIFoodProfile> {
    const response = await api.get(`/heni/food/${foodId}/profile/`, {
      params: { amount_g }
    });
    // Backend returns nested structure: { data: { success: true, data: {...} } }
    return {
      success: response.data.data.success,
      data: response.data.data.data
    };
  }

  static async analyzeDietaryPattern(request: HENIDietaryPatternRequest): Promise<HENIDietaryPatternResult> {
    const response = await api.post('/heni/analyze-pattern/', request);
    // Backend returns nested structure: { data: { success: true, data: {...} } }
    return {
      success: response.data.data.success,
      data: response.data.data.data,
      metadata: response.data.data.metadata
    };
  }
}

// Environmental Impact Types
export interface EnvironmentalImpactRequest {
  foods: Array<{
    food_id: number;
    quantity: number;
  }>;
  user_type?: 'individual' | 'researcher' | 'policy';
}

export interface FoodComparisonRequest {
  foods: Array<{
    food_id: number;
    amount: number;
    unit?: string;
  }>;
  user_type?: 'individual' | 'researcher' | 'policy';
}

export interface EnvironmentalProfileRequest {
  food_id: number;
  amount_g?: number;
  user_type?: 'individual' | 'researcher' | 'policy';
}

export interface LCAResults {
  'Global warming': number;
  'Fine particulate matter formation': number;
  'Terrestrial acidification': number;
  'Freshwater eutrophication': number;
  'Marine eutrophication': number;
  'Stratospheric ozone depletion': number;
  'Fossil resource scarcity': number;
  'Mineral resource scarcity': number;
  'Water consumption': number;
  'Land use': number;
  'Terrestrial ecotoxicity': number;
  'Freshwater ecotoxicity': number;
  'Marine ecotoxicity': number;
  'Human carcinogenic toxicity': number;
  'Human non-carcinogenic toxicity': number;
  'Ionizing radiation': number;
  'Ozone formation, Human health': number;
  'Ozone formation, Terrestrial ecosystems': number;
}

export interface EndpointImpacts {
  'Human Health': number;
  'Ecosystems': number;
  'Resources': number;
}

export interface EnvironmentalMonetization {
  monetized_impacts: Record<string, number>;
  total_cost: number;
  cost_per_calorie: number;
  cost_per_protein: number;
  cost_breakdown_by_category: Record<string, {
    total_cost: number;
    individual_impacts: Record<string, number>;
    percentage_of_total: number;
  }>;
  top_cost_drivers: Array<{
    rank: number;
    impact_category: string;
    cost: number;
    percentage_of_total: number;
  }>;
}

export interface SustainabilityScore {
  overall_sustainability_score: number;
  sustainability_rating: string;
  environmental_score: number;
  nutritional_score: number;
  processing_score: number;
  category_scores: Record<string, number>;
  recommendations: string[];
}

export interface MealComposition {
  total_energy_kcal: number;
  total_weight_grams: number;
  food_count: number;
  macronutrient_distribution: {
    protein_percent: number;
    carbohydrate_percent: number;
    fat_percent: number;
  };
  food_breakdown: Array<{
    name: string;
    quantity: number;
    group: string;
    calories: number;
    weight_percentage: number;
  }>;
}

export interface UserExplanation {
  summary: string;
  key_findings: string[];
  interpretation: string;
  recommendations: string[];
  context: string;
  technical_notes?: string[];
}

export interface EnvironmentalImpactResult {
  success: boolean;
  data: {
    meal_analysis: {
      lca_results: LCAResults;
      endpoint_impacts: EndpointImpacts;
      single_score: number;
      monetization: EnvironmentalMonetization;
      sustainability_score: SustainabilityScore;
      meal_composition: MealComposition;
    };
    user_explanation: UserExplanation;
    comparison_to_references: {
      sustainable_meal: {
        cost_ratio: number;
        carbon_ratio: number;
        sustainability_comparison: string;
      };
      average_meal: {
        cost_ratio: number;
        carbon_ratio: number;
        sustainability_comparison: string;
      };
    };
  };
  metadata?: {
    analysis_timestamp: string;
    methodology: string;
    reference_version: string;
  };
}

export interface FoodComparisonResult {
  success: boolean;
  data: {
    comparison_analysis: {
      foods: Array<{
        food_id: number;
        food_name: string;
        amount_g: number;
        lca_results: Partial<LCAResults>;
        environmental_cost: number;
        sustainability_score: number;
        key_impacts: string[];
      }>;
      best_performing: {
        food_id: number;
        food_name: string;
        reason: string;
      };
      worst_performing: {
        food_id: number;
        food_name: string;
        reason: string;
      };
      comparison_insights: string[];
    };
    user_explanation: UserExplanation;
  };
}

export interface FoodEnvironmentalProfile {
  success: boolean;
  data: {
    food_details: {
      food_id: number;
      food_name: string;
      food_group: string;
      amount_analyzed_g: number;
    };
    environmental_analysis: {
      lca_results: LCAResults;
      endpoint_impacts: EndpointImpacts;
      single_score: number;
      monetization: EnvironmentalMonetization;
      sustainability_score: SustainabilityScore;
    };
    comparative_context: {
      food_group_percentile: number;
      similar_foods: Array<{
        name: string;
        environmental_cost: number;
        carbon_footprint: number;
      }>;
      reference_comparisons: Record<string, {
        ratio: number;
        interpretation: string;
      }>;
    };
    user_explanation: UserExplanation;
  };
}

// Environmental Impact API Service Class
export class EnvironmentalImpactApiService {
  static async analyzeMealEnvironmentalImpact(request: EnvironmentalImpactRequest): Promise<EnvironmentalImpactResult> {
    const response = await api.post('/environmental-impact/', request);
    
    console.log('DEBUG - Full response:', response.data);
    console.log('DEBUG - response.data.data keys:', Object.keys(response.data?.data || {}));
    
    // Extract the actual backend data structure with safe fallbacks
    const outerData = response.data?.data || {};
    const backendData = outerData.data || {};  // The actual environmental data is nested one level deeper
    const envImpacts = backendData.environmental_impacts || {};
    const monetData = backendData.monetization || {};
    const overallAssessment = backendData.overall_assessment || {};
    const sustainability = backendData.sustainability || {};
    const refComparisons = backendData.reference_comparisons || {};
    const mealInfo = outerData.meal_info || {};
    
    console.log('DEBUG - envImpacts:', envImpacts);
    console.log('DEBUG - envImpacts.all_impacts:', envImpacts.all_impacts);
    console.log('DEBUG - monetData:', monetData);
    console.log('DEBUG - monetData.results:', monetData.results);
    
    // Simple transformation to match component expectations using actual calculated values
    return {
      success: true,
      data: {
        meal_analysis: {
          lca_results: envImpacts.all_impacts || {},
          endpoint_impacts: envImpacts.endpoint_impacts || {},
          single_score: typeof envImpacts.summary_score?.value === 'number' ? envImpacts.summary_score.value : (outerData?.data?.environmental_impacts?.summary_score?.value ?? 0),
          monetization: {
            monetized_impacts: monetData.results?.monetized_impacts || {},
            total_cost: monetData.results?.total_environmental_cost?.value || 0,
            cost_per_calorie: monetData.results?.cost_per_calorie?.value || 0,
            cost_per_protein: monetData.results?.cost_per_protein?.value || 0,
            cost_breakdown_by_category: monetData.results?.cost_breakdown || {},
            top_cost_drivers: monetData.results?.top_cost_drivers || []
          },
          sustainability_score: {
            // Prefer backend-provided sustainability block; fall back conservatively if missing
            overall_sustainability_score: sustainability.overall_sustainability_score ?? 50,
            sustainability_rating: sustainability.sustainability_rating ?? (overallAssessment.rating || 'Unknown'),
            environmental_score: sustainability.environmental_score ?? 0,
            nutritional_score: sustainability.nutritional_score ?? 0,
            processing_score: sustainability.processing_score ?? 0,
            category_scores: sustainability.category_scores || {},
            recommendations: Array.isArray(sustainability.recommendations) && sustainability.recommendations.length > 0
              ? sustainability.recommendations
              : (overallAssessment.recommendation ? [overallAssessment.recommendation] : [])
          },
          meal_composition: {
            total_energy_kcal: mealInfo.total_calories || 0,
            total_weight_grams: mealInfo.total_weight || 0,
            food_count: Array.isArray(mealInfo.composition) ? mealInfo.composition.length : 0,
            macronutrient_distribution: mealInfo.macronutrient_distribution || { protein_percent: 0, carbohydrate_percent: 0, fat_percent: 0 },
            food_breakdown: mealInfo.composition || []
          }
        },
        user_explanation: {
          summary: envImpacts.explanation?.simple_explanation || '',
          key_findings: [monetData.interpretation?.message || 'Environmental impact analysis completed'],
          interpretation: envImpacts.explanation?.detailed_explanation || '',
          recommendations: overallAssessment.recommendation ? [overallAssessment.recommendation] : [],
          context: envImpacts.explanation?.what_it_means || '',
          technical_notes: []
        },
        comparison_to_references: {
          sustainable_meal: {
            cost_ratio: refComparisons.results?.sustainable?.environmental_cost_ratio?.value || 1.0,
            carbon_ratio: refComparisons.results?.sustainable?.carbon_footprint_ratio?.value || 1.0,
            sustainability_comparison: refComparisons.interpretation?.sustainable || 'No comparison available'
          },
          average_meal: {
            cost_ratio: refComparisons.results?.unsustainable?.environmental_cost_ratio?.value || 1.0,
            carbon_ratio: refComparisons.results?.unsustainable?.carbon_footprint_ratio?.value || 1.0,
            sustainability_comparison: refComparisons.interpretation?.unsustainable || 'No comparison available'
          }
        }
      },
      metadata: outerData.metadata || {}
    };
  }

  static async compareFoodsEnvironmentalImpact(request: FoodComparisonRequest): Promise<FoodComparisonResult> {
    // Backend expects 'quantity' (g) not 'amount'; normalize payload
    const payload = {
      foods: (request.foods || []).map((f) => ({
        food_id: f.food_id,
        quantity: f.amount,
      })),
      user_type: request.user_type || 'individual',
    };

    const response = await api.post('/environmental-impact/compare-foods/', payload);

    // Normalize backend shape to the component's expected structure (typed, no 'any')
    type BackendFoodInfo = {
      name?: string;
      food_name?: string;
      FoodDescription?: string;
      FoodDescriptionF?: string;
      food_id?: number;
      foodId?: number;
      FoodID?: number;
      quantity?: number;
    };
    type BackendComparisonItem = {
      food_info?: BackendFoodInfo;
      all_impacts?: Record<string, unknown>;
      sustainability_score?: number;
      amount?: number;
      error?: unknown;
    };

    const isRecord = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null;

    const raw: unknown = response.data;
    const bodyObj = (isRecord(raw) && (raw.data ?? raw)) as Record<string, unknown>;

    const fcRaw = bodyObj['food_comparisons'];
    const items: BackendComparisonItem[] = Array.isArray(fcRaw)
      ? (fcRaw as unknown[]).filter((x): x is BackendComparisonItem => isRecord(x))
      : [];

    const ciRaw = bodyObj['comparison_insights'];
    let insights: string[] = [];
    if (Array.isArray(ciRaw)) {
      insights = (ciRaw as unknown[]).map((v) => String(v));
    } else if (isRecord(ciRaw) && Array.isArray((ciRaw as Record<string, unknown>)['key_takeaways'])) {
      insights = ((ciRaw as Record<string, unknown>)['key_takeaways'] as unknown[]).map((v) => String(v));
    }

    const explanations = (isRecord(bodyObj['explanations']) ? (bodyObj['explanations'] as Record<string, unknown>) : {}) as Record<string, unknown>;

    // Map foods
    const foods = items
      .filter((it) => !it.error)
      .map((it) => {
        const info: BackendFoodInfo = it.food_info || {};
        const allImpRaw = isRecord(it.all_impacts) ? (it.all_impacts as Record<string, unknown>) : {};
        const allImp: Record<string, number> = Object.fromEntries(
          Object.entries(allImpRaw).map(([k, v]) => [k, typeof v === 'number' ? v : 0])
        ) as Record<string, number>;
        const amountG = typeof info.quantity === 'number' ? info.quantity : (typeof it.amount === 'number' ? it.amount : 0);
        // Prefer new structured per-100g LCA metrics when provided
        const lcaPer100g = isRecord((it as Record<string, unknown>)['lca_per_100g'])
          ? ((it as Record<string, unknown>)['lca_per_100g'] as Record<string, unknown>)
          : undefined;
        const midpointsPer100g = isRecord(lcaPer100g?.['midpoint_impacts'])
          ? (lcaPer100g?.['midpoint_impacts'] as Record<string, unknown>)
          : undefined;
        const allImpFinal: Record<string, number> = midpointsPer100g
          ? Object.fromEntries(Object.entries(midpointsPer100g).map(([k, v]) => [k, typeof v === 'number' ? v : 0]))
          : allImp;

        // Derive simple key impacts (top 3 by value)
        const key_impacts = Object.entries(allImpFinal)
          .sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0))
          .slice(0, 3)
          .map(([k]) => k);
        const name = info.name || info.food_name || info.FoodDescription || info.FoodDescriptionF || String(info.food_id || info.foodId || 'Food');

        // Prefer new monetization field when available
        const monetRaw = (it as Record<string, unknown>)['monetization'];
        const costPer100gNew = isRecord(monetRaw) && typeof (monetRaw as Record<string, unknown>)['cost_per_100g'] === 'number'
          ? ((monetRaw as Record<string, unknown>)['cost_per_100g'] as number)
          : undefined;
        const legacyCostPer100g = typeof (it as Record<string, unknown>)['environmental_cost_per_100g'] === 'number'
          ? ((it as Record<string, unknown>)['environmental_cost_per_100g'] as number)
          : 0;
        const costPer100g = typeof costPer100gNew === 'number' ? costPer100gNew : legacyCostPer100g;

        return {
          food_id: info.food_id ?? info.foodId ?? info.FoodID ?? 0,
          food_name: name,
          amount_g: amountG,
          lca_results: allImpFinal,
          environmental_cost: costPer100g,
          sustainability_score: typeof it.sustainability_score === 'number' ? it.sustainability_score : 0,
          key_impacts,
        };
      });

    // Compute best/worst performers by sustainability score
    const bestFood = foods.length > 0 ? foods.reduce((a, b) => (b.sustainability_score > a.sustainability_score ? b : a)) : undefined;
    const worstFood = foods.length > 0 ? foods.reduce((a, b) => (b.sustainability_score < a.sustainability_score ? b : a)) : undefined;

    // Build user explanation from backend description and generate actionable recommendations
    const recs: string[] = [];
    if (bestFood && worstFood) {
      recs.push(`Swap ${worstFood.food_name} with ${bestFood.food_name} to reduce overall impact.`);
      if (Array.isArray(worstFood.key_impacts) && worstFood.key_impacts.length > 0) {
        recs.push(`Focus on lowering '${worstFood.key_impacts[0]}' for ${worstFood.food_name}.`);
      }
    }
    if (recs.length === 0 && insights.length > 0) {
      recs.push(...insights.slice(0, 2));
    }

    const user_explanation: UserExplanation = {
      summary: String((explanations['description'] as string) || 'Comparison completed'),
      key_findings: insights.slice(0, 3),
      interpretation: String((explanations['comparison_explanation'] as string) || ''),
      recommendations: recs,
      context: String((explanations['title'] as string) || 'Food Environmental Impact Comparison'),
    };

    const normalized: FoodComparisonResult = {
      success: true,
      data: {
        comparison_analysis: {
          foods,
          best_performing: bestFood
            ? { food_id: bestFood.food_id, food_name: bestFood.food_name, reason: 'Highest sustainability score' }
            : { food_id: 0, food_name: foods[0]?.food_name || 'N/A', reason: 'Insufficient data' },
          worst_performing: worstFood
            ? { food_id: worstFood.food_id, food_name: worstFood.food_name, reason: 'Lowest sustainability score' }
            : { food_id: 0, food_name: foods[foods.length - 1]?.food_name || 'N/A', reason: 'Insufficient data' },
          comparison_insights: insights,
        },
        user_explanation,
      },
    };

    return normalized;
  }

  static async getFoodEnvironmentalProfile(): Promise<FoodEnvironmentalProfile> {
    // Endpoint removed per request; keep method but throw to signal deprecation
    throw new Error('Food environmental profile endpoint is disabled.');
  }

  // Normalize and coerce API response to exactly what the components expect
  private static normalizeEnvironmentalImpactResponse(raw: unknown): EnvironmentalImpactResult {
    const safeNumber = (v: unknown, fallback = 0): number => {
      const n = typeof v === 'string' ? Number(v) : v;
      return typeof n === 'number' && Number.isFinite(n) ? n : fallback;
    };

    const coerceRecordNumbers = (obj: Record<string, unknown> | undefined): Record<string, number> => {
      const source = obj || {};
      return Object.fromEntries(
        Object.entries(source).map(([k, v]) => [k, safeNumber(v, 0)])
      );
    };

    const root = (raw as Record<string, unknown>) || {};
    const dataObj: Record<string, unknown> = (root?.data as Record<string, unknown>) ?? root;
    const maObj: Record<string, unknown> = (dataObj?.meal_analysis as Record<string, unknown>) ?? {};

    const lca_results = coerceRecordNumbers((maObj as Record<string, unknown>)["lca_results"] as Record<string, unknown> | undefined) as unknown as LCAResults;
    const endpoint_impacts = coerceRecordNumbers((maObj as Record<string, unknown>)["endpoint_impacts"] as Record<string, unknown> | undefined) as unknown as EndpointImpacts;

    const monetizationRaw = (maObj?.monetization as Record<string, unknown>) ?? {};
    const monetization: EnvironmentalMonetization = {
      monetized_impacts: coerceRecordNumbers(monetizationRaw?.monetized_impacts as Record<string, unknown> | undefined),
      total_cost: safeNumber(monetizationRaw?.total_cost, 0),
      cost_per_calorie: safeNumber(monetizationRaw?.cost_per_calorie, 0),
      cost_per_protein: safeNumber(monetizationRaw?.cost_per_protein, 0),
      cost_breakdown_by_category: Object.fromEntries(
        Object.entries((monetizationRaw?.cost_breakdown_by_category || {}) as Record<string, unknown>).map(([cat, info]) => [
          cat,
          {
            total_cost: safeNumber((info as Record<string, unknown>)?.total_cost, 0),
            individual_impacts: coerceRecordNumbers(((info as Record<string, unknown>)?.individual_impacts as Record<string, unknown> | undefined)),
            percentage_of_total: safeNumber((info as Record<string, unknown>)?.percentage_of_total, 0),
          },
        ])
      ),
      top_cost_drivers: Array.isArray(monetizationRaw?.top_cost_drivers)
        ? (monetizationRaw.top_cost_drivers as unknown[]).map((d: unknown) => ({
        rank: safeNumber((d as Record<string, unknown>)?.rank, 0),
        impact_category: String((d as Record<string, unknown>)?.impact_category ?? ''),
        cost: safeNumber((d as Record<string, unknown>)?.cost, 0),
        percentage_of_total: safeNumber((d as Record<string, unknown>)?.percentage_of_total, 0),
        }))
        : [],
    };

    const sustainabilityRaw = (((maObj as Record<string, unknown>)["sustainability_score"] as Record<string, unknown>) || {}) as Record<string, unknown>;
    const sustainability_score: SustainabilityScore = {
      overall_sustainability_score: safeNumber(sustainabilityRaw?.overall_sustainability_score, 0),
      sustainability_rating: String(sustainabilityRaw?.sustainability_rating ?? 'Unknown'),
      environmental_score: safeNumber(sustainabilityRaw?.environmental_score, 0),
      nutritional_score: safeNumber(sustainabilityRaw?.nutritional_score, 0),
      processing_score: safeNumber(sustainabilityRaw?.processing_score, 0),
      category_scores: coerceRecordNumbers(sustainabilityRaw?.category_scores as Record<string, unknown> | undefined) as Record<string, number>,
      recommendations: Array.isArray(sustainabilityRaw?.recommendations)
        ? (sustainabilityRaw.recommendations as unknown[]).map((r) => String(r))
        : [],
    };

    const compRaw = (((maObj as Record<string, unknown>)["meal_composition"] as Record<string, unknown>) || {}) as Record<string, unknown>;
    const meal_composition: MealComposition = {
      total_energy_kcal: safeNumber(compRaw?.total_energy_kcal, 0),
      total_weight_grams: safeNumber(compRaw?.total_weight_grams, 0),
      food_count: safeNumber(compRaw?.food_count, 0),
      macronutrient_distribution: {
        protein_percent: safeNumber((compRaw?.macronutrient_distribution as Record<string, unknown>)?.protein_percent, 0),
        carbohydrate_percent: safeNumber((compRaw?.macronutrient_distribution as Record<string, unknown>)?.carbohydrate_percent, 0),
        fat_percent: safeNumber((compRaw?.macronutrient_distribution as Record<string, unknown>)?.fat_percent, 0),
      },
    } as MealComposition;
    // Include optional food_breakdown if present
    if (Array.isArray(compRaw?.food_breakdown)) {
      (meal_composition as unknown as { food_breakdown: MealComposition['food_breakdown'] }).food_breakdown = compRaw.food_breakdown as MealComposition['food_breakdown'];
    }

    const userExpRaw = (dataObj?.user_explanation as Record<string, unknown>) ?? {};
    const user_explanation: UserExplanation = {
      summary: String(userExpRaw?.summary ?? ''),
      key_findings: Array.isArray(userExpRaw?.key_findings)
        ? (userExpRaw.key_findings as unknown[]).map((k) => String(k))
        : [],
      interpretation: String(userExpRaw?.interpretation ?? ''),
      recommendations: Array.isArray(userExpRaw?.recommendations)
        ? (userExpRaw.recommendations as unknown[]).map((r) => String(r))
        : [],
      context: String(userExpRaw?.context ?? ''),
      technical_notes: Array.isArray(userExpRaw?.technical_notes)
        ? (userExpRaw.technical_notes as unknown[]).map((t) => String(t))
        : undefined,
    };

    const compRefsRaw = (dataObj?.comparison_to_references as {
      sustainable_meal?: { cost_ratio?: unknown; carbon_ratio?: unknown; sustainability_comparison?: unknown };
      average_meal?: { cost_ratio?: unknown; carbon_ratio?: unknown; sustainability_comparison?: unknown };
    }) ?? {};
    const comparison_to_references = {
      sustainable_meal: {
        cost_ratio: safeNumber(compRefsRaw?.sustainable_meal?.cost_ratio, 0),
        carbon_ratio: safeNumber(compRefsRaw?.sustainable_meal?.carbon_ratio, 0),
        sustainability_comparison: String(compRefsRaw?.sustainable_meal?.sustainability_comparison ?? ''),
      },
      average_meal: {
        cost_ratio: safeNumber(compRefsRaw?.average_meal?.cost_ratio, 0),
        carbon_ratio: safeNumber(compRefsRaw?.average_meal?.carbon_ratio, 0),
        sustainability_comparison: String(compRefsRaw?.average_meal?.sustainability_comparison ?? ''),
      },
    } as EnvironmentalImpactResult['data']['comparison_to_references'];

    const normalized: EnvironmentalImpactResult = {
      success: Boolean((root?.success as boolean | undefined) ?? true),
      data: {
        meal_analysis: {
          lca_results,
          endpoint_impacts,
          single_score: safeNumber(maObj?.single_score, 0),
          monetization,
          sustainability_score,
          meal_composition,
        },
        user_explanation,
        comparison_to_references,
      },
      metadata: root?.metadata as EnvironmentalImpactResult['metadata'],
    };
    return normalized;
  }
}

// User Management Types
export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  date_of_birth?: string;
  bio: string;
  profile_picture?: string;
  activity_level: 'sedentary' | 'light' | 'moderate' | 'very_active' | 'extra_active';
  dietary_preferences: string[];
  allergies: string[];
  health_goals: string[];
  daily_calorie_target?: number;
  profile_public: boolean;
  meals_public_by_default: boolean;
  created_at: string;
  last_active: string;
  followers_count: number;
  following_count: number;
  meals_count: number;
}

export interface UserRegistration {
  email: string;
  username: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  date_of_birth?: string;
  bio?: string;
  activity_level?: string;
  dietary_preferences?: string[];
  allergies?: string[];
  health_goals?: string[];
  daily_calorie_target?: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

// Meal Types
export interface MealCategory {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
}

export interface FoodItem {
  food_id: number;
  quantity: number;
  unit: string;
}

export interface Meal {
  id: string;
  name: string;
  description: string;
  creator: string;
  category: MealCategory;
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'dessert' | 'beverage';
  is_public: boolean;
  is_featured: boolean;
  food_items: FoodItem[];
  total_calories?: number;
  total_weight_grams?: number;
  nutrient_profile: Record<string, number>;
  fcs_score?: number;
  hefi_score?: number;
  hsr_score?: number;
  heni_score?: number;
  environmental_impact: Partial<LCAResults>;
  sustainability_score?: number;
  carbon_footprint?: number;
  preparation_time?: number;
  cooking_time?: number;
  servings: number;
  difficulty_level: 'easy' | 'medium' | 'hard';
  instructions: string;
  tips: string;
  image?: string;
  likes_count: number;
  saves_count: number;
  views_count: number;
  comments_count: number;
  average_rating?: number;
  tags: string[];
  created_at: string;
  updated_at: string;
  is_liked: boolean;
  is_saved: boolean;
  health_score_average?: number;
  overall_rating?: number;
}

export interface MealCreateRequest {
  name: string;
  description: string;
  category: string;
  meal_type: string;
  is_public?: boolean;
  food_items: FoodItem[];
  preparation_time?: number;
  cooking_time?: number;
  servings: number;
  difficulty_level: string;
  instructions: string;
  tips?: string;
  image?: File;
  tags: string[];
}

export interface MealComment {
  id: string;
  user: string;
  content: string;
  parent_comment?: string;
  replies: MealComment[];
  created_at: string;
  updated_at: string;
}

export interface MealRating {
  id: string;
  user: string;
  taste_rating?: number;
  health_rating?: number;
  ease_rating?: number;
  sustainability_rating?: number;
  overall_rating: number;
  review: string;
  created_at: string;
  updated_at: string;
}

// API Service Classes

export class AuthApiService {
  static async register(userData: UserRegistration): Promise<AuthResponse> {
    const response = await api.post('/users/register/', userData);
    if (response.data.token) {
      localStorage.setItem('authToken', response.data.token);
    }
    return response.data;
  }

  static async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await api.post('/users/login/', credentials);
    if (response.data.token) {
      localStorage.setItem('authToken', response.data.token);
    }
    return response.data;
  }

  static async logout(): Promise<void> {
    localStorage.removeItem('authToken');
  }

  static async getCurrentUser(): Promise<User> {
    const response = await api.get('/users/profiles/me/');
    return response.data;
  }

  static async updateProfile(userData: Partial<User>): Promise<User> {
    const response = await api.patch('/users/profiles/me/', userData);
    return response.data;
  }

  static async followUser(username: string): Promise<{ message: string }> {
    const response = await api.post(`/users/profiles/${username}/follow/`);
    return response.data;
  }

  static async unfollowUser(username: string): Promise<{ message: string }> {
    const response = await api.delete(`/users/profiles/${username}/unfollow/`);
    return response.data;
  }

  static async searchUsers(query: string): Promise<User[]> {
    const response = await api.get('/users/search/', { params: { q: query } });
    return response.data;
  }
}

export class MealApiService {
  static async getCategories(): Promise<MealCategory[]> {
    const response = await api.get('/meals/categories/');
    const body = response.data;
    if (Array.isArray(body)) return body as MealCategory[];
    if (body && Array.isArray(body.results)) return body.results as MealCategory[];
    if (body && body.data) {
      if (Array.isArray(body.data)) return body.data as MealCategory[];
      if (Array.isArray(body.data?.results)) return body.data.results as MealCategory[];
    }
    return [];
  }

  static async getMeals(params: {
    page?: number;
    meal_type?: string;
    difficulty_level?: string;
    tags?: string;
    min_calories?: number;
    max_calories?: number;
    creator?: string;
    search?: string;
    ordering?: string;
  } = {}): Promise<{ results: Meal[]; count: number; next?: string; previous?: string }> {
    const response = await api.get('/meals/meals/', { params });
    return response.data;
  }

  static async getMeal(id: string): Promise<Meal> {
    const response = await api.get(`/meals/meals/${id}/`);
    return response.data;
  }

  static async createMeal(mealData: MealCreateRequest): Promise<Meal> {
    const formData = new FormData();
    
    // Add all non-file fields
    Object.entries(mealData).forEach(([key, value]) => {
      if (key === 'image' && value instanceof File) {
        formData.append(key, value);
      } else if (key === 'food_items' || key === 'tags') {
        formData.append(key, JSON.stringify(value));
      } else if (value !== undefined && value !== null) {
        formData.append(key, String(value));
      }
    });

    const response = await api.post('/meals/meals/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }

  static async updateMeal(id: string, mealData: Partial<MealCreateRequest>): Promise<Meal> {
    const response = await api.patch(`/meals/meals/${id}/`, mealData);
    return response.data;
  }

  static async deleteMeal(id: string): Promise<void> {
    await api.delete(`/meals/meals/${id}/`);
  }

  static async likeMeal(id: string): Promise<{ message: string }> {
    const response = await api.post(`/meals/meals/${id}/like/`);
    return response.data;
  }

  static async unlikeMeal(id: string): Promise<{ message: string }> {
    const response = await api.delete(`/meals/meals/${id}/unlike/`);
    return response.data;
  }

  static async saveMeal(id: string): Promise<{ message: string }> {
    const response = await api.post(`/meals/meals/${id}/save/`);
    return response.data;
  }

  static async unsaveMeal(id: string): Promise<{ message: string }> {
    const response = await api.delete(`/meals/meals/${id}/unsave/`);
    return response.data;
  }

  static async getMyMeals(): Promise<{ results: Meal[] }> {
    const response = await api.get('/meals/meals/my_meals/');
    return response.data;
  }

  static async getSavedMeals(): Promise<{ results: Meal[] }> {
    const response = await api.get('/meals/meals/saved_meals/');
    return response.data;
  }

  static async getRecommendations(params: {
    meal_type?: string;
    limit?: number;
  } = {}): Promise<Meal[]> {
    const response = await api.get('/meals/recommendations/', { params });
    return response.data;
  }

  static async addComment(mealId: string, content: string, parentId?: string): Promise<MealComment> {
    const response = await api.post(`/meals/comments/`, {
      meal: mealId,
      content,
      parent_comment: parentId
    });
    return response.data;
  }

  static async rateMeal(mealId: string, rating: Omit<MealRating, 'id' | 'user' | 'created_at' | 'updated_at'>): Promise<MealRating> {
    const response = await api.post(`/meals/ratings/`, {
      meal: mealId,
      ...rating
    });
    return response.data;
  }
}

export default CNFApiService; 