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

export default CNFApiService; 