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
  /** Present when food came from nutrient-range search. */
  queried_nutrient_value?: number;
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

/** Enriched row from GET /cnf/groups/{id}/foods/ */
export interface GroupFoodRow {
  FoodID: number;
  FoodCode: string;
  FoodDescription: string;
  FoodDescriptionF?: string;
  source: 'cnf' | 'wafct';
  energy_kcal?: number | null;
  protein_g?: number | null;
  fibre_g?: number | null;
  food_type?: 'single' | 'mixed' | null;
  thermal_state?: string | null;
  preservation_state?: string | null;
}

export interface GroupSummary {
  total_in_group: number;
  cnf_count: number;
  wafct_count: number;
  food_type: { single: number; mixed: number; unknown: number };
  thermal_state: Record<string, number>;
  preservation_state: Record<string, number>;
  prep_both_known_pct: number;
}

export interface GroupFoodsQuery {
  limit?: number;
  offset?: number;
  q?: string;
  sort?: 'name' | 'kcal' | 'food_id';
  sort_dir?: 'asc' | 'desc';
  food_type?: 'single' | 'mixed';
  thermal?: string;
  preservation?: string;
  source?: 'cnf' | 'wafct' | 'both';
  summary?: boolean;
}

export interface GroupFoodsResult {
  foods: GroupFoodRow[];
  food_group_id: number;
  count: number;
  total_count: number;
  total_in_group: number;
  limit: number;
  offset: number;
  has_more: boolean;
  summary?: GroupSummary;
}

export interface Nutrient {
  NutrientID: number;
  NutrientName: string;
  NutrientUnit?: string;
}

// --- Multi-criteria nutrient discovery (research workbench) ---
export type DiscoverBasis = 'per_100g' | 'per_100kcal';
export interface DiscoverCriterion { nutrient_id: number; min?: number; max?: number; }
export interface DiscoverRatio { numerator_id: number; denominator_id: number; }
export interface DiscoverDvThreshold { nutrient_id: number; min_pct?: number; max_pct?: number; }
export interface DiscoverSort { key: number | 'ratio' | 'energy'; direction?: 'asc' | 'desc'; }
export interface DiscoverRequest {
  criteria: DiscoverCriterion[];
  basis?: DiscoverBasis;
  food_group_id?: number | null;
  source?: 'cnf' | 'wafct' | 'both';
  ratio?: DiscoverRatio | null;
  dv_threshold?: DiscoverDvThreshold | null;
  sort?: DiscoverSort | null;
  limit?: number;
}
export interface DiscoverFood {
  FoodID: number;
  FoodCode: string;
  FoodDescription: string;
  FoodGroupID: number | null;
  FoodGroupName: string;
  source: string;
  energy_kcal: number | null;
  /** per-100 g value for each involved NutrientID (keys are stringified ids). */
  nutrient_values: Record<string, number>;
  /** per-100 kcal value per nutrient when basis === 'per_100kcal' (else empty). */
  basis_values: Record<string, number>;
  ratio_value: number | null;
  sort_value: number | null;
}
export interface DiscoverResult {
  foods: DiscoverFood[];
  involved_nutrient_ids: number[];
  basis: DiscoverBasis;
  count: number;
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

export interface FoodComparisonNutrientCell {
  value: number;
  /** Raw per-100 g amount (for %DV when basis is per_100kcal). */
  value_per_100g?: number;
  unit: string;
  nutrient_source_id?: number;
  nutrient_source?: string;
  database?: 'cnf' | 'wafct' | string;
}

export interface CompareFoodSummary {
  FoodID: number;
  FoodDescription: string;
  FoodCode?: string;
  FoodGroup: string;
  FoodGroupID?: number;
  source?: 'cnf' | 'wafct' | string;
  energy_kcal?: number | null;
  protein_g?: number | null;
  fibre_g?: number | null;
  food_type?: 'single' | 'mixed' | null;
  thermal_state?: string | null;
  preservation_state?: string | null;
}

export interface FoodComparison {
  foods: CompareFoodSummary[];
  nutrients: Record<string, {
    nutrient_id: number;
    unit: string;
    values: Record<string, number>;
    by_food_id: Record<string, FoodComparisonNutrientCell>;
  }>;
  comparison_date: string;
  basis?: 'per_100g' | 'per_100kcal';
}

export interface CompareFoodsOptions {
  nutrientIds?: number[];
  basis?: 'per_100g' | 'per_100kcal';
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
  cnf_food_count?: number;
  wafct_food_count?: number;
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
  /** WAFCT-EXTEND (2026-05-24): filter results to one food database. */
  source?: 'cnf' | 'wafct' | 'both';
}

// Filter Options
export interface FilterOptions {
  categories: string[];
  methods: string[];
}

// AI-MATCH-1 (2026-05-23): payload from /api/cnf/search/ai-enhanced/.
// Mirrors backend `CNFMatchResult.to_dict()` in
// backend/api/services/cnf_matcher.py.
export interface CNFAlternativeMatch {
  food_id: number;
  food_description: string;
  food_group: string;
  similarity: number;
}

// AI-MATCH-1: payload from /api/recipes/decompose/.
// Mirrors backend `CNFDecomposedRecipe.to_dict()` in
// backend/api/services/cnf_recipe_decomposer.py.
export interface CNFRecipeIngredient {
  food_id: number;
  food_description: string;
  food_group: string;
  mass_g: number;
  rationale: string;
  resolution_confidence: number | null;       // null in individual mode
}

export interface CNFDecomposedRecipe {
  dish_name: string;
  normalised_dish_name: string;
  total_mass_g: number;
  matched: boolean;                           // true iff all 4 gates passed
  ingredients: CNFRecipeIngredient[];
  resolved_mass_g: number;
  unresolved_mass_g: number;
  decomposition_confidence: number;           // 0-1
  fallback_reason:
    | null
    | 'empty_dish_name'
    | 'non_positive_mass'
    | 'no_llm_client'
    | 'no_candidates'
    | 'missing_ingredients_field'
    | 'low_confidence_or_internal'            // individual-mode redaction
    | string;                                 // detailed reasons (mass_imbalance:..., too_few_ingredients:..., etc.)
  cache_hit: boolean;
  timing_ms: number;
  unresolved_ingredients_audit: Array<{       // empty in individual mode
    name?: string;
    mass_g?: number;
    matcher_food_id?: number | null;
    matcher_confidence?: number;
    reason?: string;
  }>;
  raw_llm_response?: string | null;           // null in individual mode
}

// DIET-PATTERN-1 (2026-05-24): dietary-pattern resemblance result payload
// from /api/dietary-pattern/classify/. Mirrors backend
// `PatternResemblanceResult.to_dict()` in
// backend/api/services/dietary_pattern.py.
export interface PatternResemblance {
  pattern_id: string;
  display_name: string;
  cosine: number;                       // raw cosine [0, 1]
  softmax_share: number;                // softmax-normalised [0, 1]
  distinctive_user_foods: Array<{       // empty for individual mode
    food_id: number;
    mass_g: number;
    cosine_to_prototype: number;
    contribution: number;
  }>;
  literature_anchor: string;            // empty for individual mode
  outcome_evidence_reused: string;      // empty for individual mode
  individual_mode_blurb: string;        // always shown
}

export interface PatternResemblanceResult {
  matched: boolean;
  top_pattern: string | null;
  top_pattern_confidence: 'high' | 'moderate' | 'low';
  co_leading: string[];
  resemblances: PatternResemblance[];
  n_foods: number;
  n_foods_unresolved: number;
  total_mass_g: number;
  fallback_reason: string | null;
  timing_ms: number;
  cache_hit: boolean;
}

export interface PatternFpedDriver {
  component: string;
  label: string;
  delta: number;          // user-day minus prototype-day, in the unit below
  unit: string;
  direction: 'more' | 'less';
}

export interface PatternExplanations {
  plain_summary?: { title: string; message: string };
  mandatory_caveat?: { title: string; message: string };
  methodology?: { title: string; message: string };
  narrative?: { title: string; message: string };
  /** FPED-1: food-group drivers of the resemblance (interpretive overlay). */
  fped_drivers?: {
    title: string;
    pattern: string;
    drivers: PatternFpedDriver[];
    caveat: string;
  };
}

export interface PatternClassifyResponse {
  result: PatternResemblanceResult;
  explanations: PatternExplanations;
}

// AI-MATCH-2 (2026-05-24): aggregated 24-h dietary recall payload from
// /api/recipes/recall-24h/. Mirrors backend `CNFRecall24hResult.to_dict()`
// in backend/api/services/cnf_recall_24h.py.
export type RecallOccasion =
  | 'breakfast' | 'am_snack' | 'lunch' | 'pm_snack'
  | 'dinner' | 'evening_snack';

export interface RecallMealInput {
  occasion: RecallOccasion;
  dish_name: string;
  total_mass_g: number;
  /** Default 'text'. 'packaged' / 'direct' skip LLM dish decompose — use pre_decomposed. */
  entry_type?: 'text' | 'packaged' | 'direct';
  /** Required when entry_type is 'packaged' or 'direct'. */
  pre_decomposed?: RecallPackagedPreDecomposed;
}

/** Pre-decomposed packaged-food payload folded into a 24-h recall meal. */
export interface RecallPackagedPreDecomposed {
  ingredients: Array<{
    food_id: number;
    food_description: string;
    food_group: string;
    mass_g: number;
    confidence?: number;
  }>;
  decomposition_confidence: number;
  decomposition_warnings?: string[];
  product_name?: string | null;
  brand?: string | null;
  image_sha256?: string;
}

export interface CNFRecall24hAggregatedIngredient {
  food_id: number;
  food_description: string;
  food_group: string;
  mass_g: number;
  /** Per-occasion attribution preserved across the FoodID dedup. */
  occasions: Partial<Record<RecallOccasion, number>>;
}

export interface CNFRecall24hMealResult {
  occasion: RecallOccasion;
  decomposition: CNFDecomposedRecipe;
}

export interface CNFRecall24hResult {
  matched: boolean;
  meals: CNFRecall24hMealResult[];
  aggregated_daily_ingredients: CNFRecall24hAggregatedIngredient[];
  total_resolved_mass_g: number;
  total_unresolved_mass_g: number;
  occasions_count: number;
  estimated_daily_kcal: number;
  aggregate_warnings: string[];   // free-text codes like 'no_breakfast_logged'
  fallback_reason: string | null;
  timing_ms: number;
  cache_hit: boolean;
}

export interface CNFRecall24hExplanations {
  // individual mode
  plain_summary?: { title: string; message: string };
  before_you_score?: { title: string; message: string };
  // researcher / policy mode
  mandatory_caveat?: { title: string; message: string };
  methodology?: { title: string; message: string };
  score_routing?: { title: string; message: Record<string, string> };
}

export interface CNFRecall24hResponse {
  result: CNFRecall24hResult;
  explanations: CNFRecall24hExplanations;
}

export interface CNFAIMatchResult {
  query: string;                            // original input
  normalised_query: string;                 // cache key (lowercase, collapsed whitespace)
  matched: boolean;                         // true iff confidence ≥ threshold AND not hallucinated
  food_id: number | null;
  food_description: string | null;
  food_group: string | null;
  confidence: number;                       // 0-1
  justification: string;                    // blank in individual mode
  alternatives: CNFAlternativeMatch[];      // top-3 next-best (excluding the chosen one)
  fallback_reason:                          // null on success
    | null
    | 'low_confidence'
    | 'low_confidence_or_internal'          // individual-mode redaction
    | 'hallucinated_id'
    | 'no_llm_client'
    | 'no_candidates'
    | 'exception';
  used_ai_ranking: boolean;                 // false = degraded retrieval-only top-1
  cache_hit: boolean;
  timing_ms: number;
  corpus_version: string | null;            // build_date_utc from corpus provenance
}

// WAFCT-EXTEND (2026-05-24): food-database provenance. Search-result rows +
// match results can now come from either CNF (Health Canada Canadian
// Nutrient File) or WAFCT (FAO/INFOODS West African Food Composition Table
// 2019). FoodIDs ≥ 700,000 indicate WAFCT-sourced foods; FoodIDs < 700,000
// are CNF. Backend `food_source(food_id)` is the authoritative resolver.
// (Distinct from the existing `FoodSource` interface near line 121 which
// describes a CNF FOOD_SOURCE.csv row — this is provenance, not the row.)
export type FoodSourceTag = 'cnf' | 'wafct';
export type SourceFilter  = 'cnf' | 'wafct' | 'both';

export interface ProfileSampleAdequacy {
  adequate: boolean;
  note: string;
}

export interface ProfileScoreDriver {
  food_id: number;
  food_description: string;
  mass_g: number;
  mass_share_pct: number;
}

export interface ProfileScoreMeta {
  total_mass_g: number;
  estimated_kcal: number;
  food_count: number;
  sample_adequacy: Record<string, ProfileSampleAdequacy>;
  drivers: ProfileScoreDriver[];
}

export interface ProfileScoreResponse {
  metrics: Record<string, { status: 'fulfilled' | 'rejected'; result?: unknown; reason?: string }>;
  meta: ProfileScoreMeta;
}

// API Service Class
export class CNFApiService {
  // Enhanced Search & Exploration. WAFCT-EXTEND (2026-05-24): optional
  // `source` narrows to one food database (cnf / wafct / both). Default both.
  static async searchFoods(
    query: string,
    limit = 50,
    offset = 0,
    source: SourceFilter = 'both',
  ): Promise<SearchResult> {
    const response = await api.get(`/cnf/search/`, {
      params: { q: query, limit, offset, source }
    });
    return response.data.data;
  }

  // AI-MATCH-1 (2026-05-23): free-text → CNF FoodID via embedding + LLM
  // ranking. Opt-in, additive to the fuzzy `searchFoods` above. Server may
  // return 429 (per-IP rate limit) or 503 (monthly circuit breaker) — surface
  // both with a clean error.
  // WAFCT-EXTEND (2026-05-24): optional `source` filters candidates to one
  // food database before LLM ranking.
  static async searchFoodsAI(
    query: string,
    options: {
      topK?: number;
      userType?: 'individual' | 'researcher' | 'policy';
      source?: SourceFilter;
    } = {},
  ): Promise<CNFAIMatchResult> {
    const response = await api.post('/cnf/search/ai-enhanced/', {
      query,
      top_k: options.topK,
      user_type: options.userType || 'individual',
      source: options.source || 'both',
    });
    return response.data.result as CNFAIMatchResult;
  }

  // AI-MATCH-1 (Phase 8): free-text dish name → CNF ingredient list with
  // masses. Two-stage server-side (LLM decompose → CNFMatcher resolve). May
  // take 5-15 s; long-running modal UX recommended. Same 429/503 surface as
  // searchFoodsAI.
  static async decomposeRecipe(
    dishName: string,
    totalMassG: number,
    options: {
      userType?: 'individual' | 'researcher' | 'policy';
      /** WAFCT-EXTEND (2026-05-24): restrict Stage-2 ingredient resolution
       *  to one food database. Default 'both'. */
      source?: SourceFilter;
    } = {},
  ): Promise<CNFDecomposedRecipe> {
    const response = await api.post('/recipes/decompose/', {
      dish_name: dishName,
      total_mass_g: totalMassG,
      user_type: options.userType || 'individual',
      source: options.source || 'both',
    });
    return response.data.result as CNFDecomposedRecipe;
  }

  // DIET-PATTERN-1 (2026-05-24): score a daily ingredient list against
  // the prototype-pattern library (Mediterranean / DASH / Western /
  // Vegetarian / Vegan / CFG-Healthy / West African Staple + optional
  // EAT-Lancet). Returns top-3 resemblances + confidence band + audience-
  // aware caveat. Optional LLM narrative when include_narrative=true.
  // Cost: 1¢ baseline, 2¢ with narrative.
  static async classifyDietaryPattern(
    foods: Array<{ food_id: number; mass_g: number }>,
    options: {
      userType?: 'individual' | 'researcher' | 'policy';
      includeNarrative?: boolean;
      /** RECALL-HISTORY-1 (2026-05-24): set to e.g. "5-day average,
       *  2026-05-17 to 2026-05-21" to swap the single-day mandatory caveat
       *  for the softened multi-day variant. The /recall-history page
       *  passes this when routing the N-day-average view. */
      metaLabel?: string;
      /** PKG-IMG-1 Phase 2 (2026-05-26): when set to 'packaged_food_inferred',
       *  swaps the caveat language to flag that the food list came from an
       *  LLM-decomposed packaged-food label (not a measured recall). The
       *  /scan-product page passes this when routing a decomposed product. */
      decompositionProvenance?: 'packaged_food_inferred';
    } = {},
  ): Promise<PatternClassifyResponse> {
    const response = await api.post('/dietary-pattern/classify/', {
      foods,
      user_type: options.userType || 'individual',
      include_narrative: options.includeNarrative ?? false,
      ...(options.metaLabel ? { meta_label: options.metaLabel } : {}),
      ...(options.decompositionProvenance
          ? { decomposition_provenance: options.decompositionProvenance } : {}),
    });
    return {
      result: response.data.result as PatternResemblanceResult,
      explanations: response.data.explanations as PatternExplanations,
    };
  }

  /** Unified six-metric profile score (server-side parallel fan-out). */
  static async scoreProfile(
    foods: Array<{ food_id: number; mass_g: number; food_description?: string }>,
    options: {
      userType?: 'individual' | 'researcher' | 'policy';
      metrics?: string[];
      decompositionProvenance?: 'packaged_food_inferred';
      multiDayLabel?: string;
      enableLcaMatcher?: boolean;
    } = {},
  ): Promise<ProfileScoreResponse> {
    const response = await api.post('/profile/score/', {
      foods,
      user_type: options.userType || 'individual',
      ...(options.metrics?.length ? { metrics: options.metrics } : {}),
      ...(options.decompositionProvenance
        ? { decomposition_provenance: options.decompositionProvenance } : {}),
      ...(options.multiDayLabel ? { multi_day_label: options.multiDayLabel } : {}),
      ...(options.enableLcaMatcher != null ? { enable_lca_matcher: options.enableLcaMatcher } : {}),
    });
    return response.data.data as ProfileScoreResponse;
  }

  // AI-MATCH-2 (2026-05-24): occasion-by-occasion 24-h dietary recall →
  // aggregated daily CNF ingredient list. Composes the per-meal decomposer
  // in parallel server-side. Same 429 (per-IP) / 503 (circuit breaker)
  // surface as searchFoodsAI + decomposeRecipe. Cost = 5¢/meal capped at 30¢.
  static async recall24h(
    meals: RecallMealInput[],
    options: {
      userType?: 'individual' | 'researcher' | 'policy';
      /** WAFCT-EXTEND (2026-05-24): restrict every meal's Stage-2 ingredient
       *  resolution to one food database. Default 'both'. */
      source?: SourceFilter;
    } = {},
  ): Promise<CNFRecall24hResponse> {
    const response = await api.post('/recipes/recall-24h/', {
      meals,
      user_type: options.userType || 'individual',
      source: options.source || 'both',
    });
    return {
      result: response.data.result as CNFRecall24hResult,
      explanations: response.data.explanations as CNFRecall24hExplanations,
    };
  }

  // AI-MATCH-2 (2026-05-24): per-scoring-endpoint adapters that take an
  // aggregated 24-h recall ingredient list and shape it to each endpoint's
  // request schema. Five 1-line adapters keep wizard call-sites identical:
  //   const req = CNFApiService.recallTo<X>(aggregatedList, userType)
  //   await CNFApiService.calculate<X>(req)
  // Centralising the shape adapters here means the wizard never needs to
  // know the per-endpoint quirks (food_ids vs foods, amount_g vs amount
  // vs quantity, separate serving_sizes array, etc.).
  static recallToHEFI(
    ingredients: CNFRecall24hAggregatedIngredient[],
    userType: 'individual' | 'researcher' | 'policy' = 'individual',
  ): HEFICalculationRequest {
    return {
      foods: ingredients.map(i => ({ food_id: i.food_id, amount_g: i.mass_g })),
      user_type: userType,
    };
  }

  static recallToHENI(
    ingredients: CNFRecall24hAggregatedIngredient[],
    userType: 'individual' | 'researcher' | 'policy' = 'individual',
  ): HENICalculationRequest {
    return {
      meal: ingredients.map(i => ({ food_id: i.food_id, amount: i.mass_g, unit: 'g' })),
      user_type: userType,
    };
  }

  static recallToHSR(
    ingredients: CNFRecall24hAggregatedIngredient[],
    userType: 'individual' | 'researcher' | 'policy' = 'individual',
  ): HSRCalculationRequest {
    return {
      food_ids: ingredients.map(i => i.food_id),
      serving_sizes: ingredients.map(i => i.mass_g),
      analysis_level: 'detailed',
      include_meal_insights: true,
      user_type: userType,
    };
  }

  static recallToFCS(
    ingredients: CNFRecall24hAggregatedIngredient[],
    userType: 'individual' | 'researcher' | 'policy' = 'individual',
  ): FCSCalculationRequest {
    return {
      food_ids: ingredients.map(i => i.food_id),
      food_names: ingredients.map(i => i.food_description),
      serving_sizes: ingredients.map(i => i.mass_g),
      user_type: userType,
    };
  }

  static recallToEnvironmental(
    ingredients: CNFRecall24hAggregatedIngredient[],
    userType: 'individual' | 'researcher' | 'policy' = 'individual',
  ): EnvironmentalImpactRequest {
    return {
      foods: ingredients.map(i => ({ food_id: i.food_id, quantity: i.mass_g })),
      user_type: userType,
    };
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
    if (options.source && options.source !== 'both') {
      params.source = options.source;
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

  /** Multi-criteria nutrient discovery (research workbench). */
  static async discoverFoods(req: DiscoverRequest): Promise<DiscoverResult> {
    const body: Record<string, unknown> = {
      criteria: req.criteria ?? [],
      basis: req.basis ?? 'per_100g',
      limit: req.limit ?? 100,
    };
    if (req.food_group_id != null) body.food_group_id = req.food_group_id;
    if (req.source && req.source !== 'both') body.source = req.source;
    if (req.ratio) body.ratio = req.ratio;
    if (req.dv_threshold) body.dv_threshold = req.dv_threshold;
    if (req.sort) body.sort = req.sort;
    const response = await api.post(`/cnf/discover/`, body);
    return response.data.data;
  }

  static async getFoodsByGroup(
    foodGroupId: number,
    query: GroupFoodsQuery = {},
  ): Promise<GroupFoodsResult> {
    const params: Record<string, string | number | boolean> = {
      limit: query.limit ?? 100,
    };
    if (query.offset != null) params.offset = query.offset;
    if (query.q) params.q = query.q;
    if (query.sort) params.sort = query.sort;
    if (query.sort_dir) params.sort_dir = query.sort_dir;
    if (query.food_type) params.food_type = query.food_type;
    if (query.thermal) params.thermal = query.thermal;
    if (query.preservation) params.preservation = query.preservation;
    if (query.source && query.source !== 'both') params.source = query.source;
    if (query.summary) params.summary = 'true';
    const response = await api.get(`/cnf/groups/${foodGroupId}/foods/`, { params });
    return response.data.data;
  }

  static async compareFoods(
    foodIds: number[],
    options: CompareFoodsOptions = {},
  ): Promise<FoodComparison> {
    const body: Record<string, unknown> = { food_ids: foodIds };
    if (options.nutrientIds?.length) body.nutrient_ids = options.nutrientIds;
    if (options.basis) body.basis = options.basis;
    const response = await api.post(`/cnf/compare/`, body);
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

  // ====================================================================
  // PKG-IMG-1 Phase 1 (2026-05-26) — packaged-food image → NF panel → HSR
  // ====================================================================

  /** Multipart image upload → server-extracted NF panel JSON.
   *  Cost: 1¢ per fresh extraction; cache hits (same image SHA-256 within
   *  7 days) are free. Throws on 4xx/5xx; caller renders error state. */
  static async extractPackagedFood(
    images: File | Blob | Array<File | Blob>,
    opts: { target?: 'hsr' } = {},
  ): Promise<PackagedFoodExtractResponse> {
    const list = Array.isArray(images) ? images : [images];
    if (list.length === 0) {
      throw new Error('extractPackagedFood: at least one image is required');
    }
    if (list.length > 3) {
      throw new Error('extractPackagedFood: at most 3 images per scan');
    }
    const form = new FormData();
    for (const img of list) {
      form.append('images', img);
    }
    if (opts.target) form.append('target', opts.target);
    const response = await api.post('/packaged-food/extract/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data as PackagedFoodExtractResponse;
  }

  /** User-confirmed NF panel + HSR category → HSR star rating with
   *  audience-aware explanation + provenance. No LLM call (0¢). */
  static async calculateHsrFromPanel(
    panel: NFPanelExtraction,
    category: HSRCategoryCode,
    opts: {
      userType?: 'individual' | 'researcher' | 'policy';
      consumedPortionGrams?: number | null;
      fvnlPercent?: number | null;
    } = {},
  ): Promise<HsrFromPanelResponse> {
    const response = await api.post('/hsr/calculate-from-panel/', {
      panel,
      category,
      consumed_portion_grams: opts.consumedPortionGrams ?? null,
      fvnl_percent: opts.fvnlPercent ?? null,
      user_type: opts.userType ?? 'individual',
    });
    return response.data as HsrFromPanelResponse;
  }

  // PKG-IMG-1 Phase 2 (2026-05-26) — adaptive extraction + decomposition

  /** Multipart image upload → adaptive NF panel + ingredient list extraction.
   *  Single multimodal LLM call (1¢). Frontend uses has_nf_panel /
   *  has_ingredient_list to decide what to do next. */
  static async extractPackagedFoodCombined(
    images: File | Blob | Array<File | Blob>,
  ): Promise<PackagedFoodExtractCombinedResponse> {
    const list = Array.isArray(images) ? images : [images];
    if (list.length === 0) {
      throw new Error('extractPackagedFoodCombined: at least one image is required');
    }
    if (list.length > 3) {
      throw new Error('extractPackagedFoodCombined: at most 3 images per scan');
    }
    const form = new FormData();
    for (const img of list) {
      form.append('images', img);
    }
    const response = await api.post('/packaged-food/extract-combined/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data as PackagedFoodExtractCombinedResponse;
  }

  /** Confirmed NF panel + ingredient list → CNF-mapped composition.
   *  Text-only LLM call (2¢) constrained by descending-mass-order,
   *  optional explicit percentages, and macro-reconciliation against
   *  the NF panel. Composition is INFERRED, not measured. */
  static async decomposePackagedFood(
    panel: NFPanelExtraction,
    ingredient_list: IngredientListExtraction,
  ): Promise<PackagedFoodDecomposeResponse> {
    const response = await api.post('/packaged-food/decompose-ingredients/', {
      nf_panel: panel, ingredient_list,
    });
    return response.data as PackagedFoodDecomposeResponse;
  }
}

// ===========================================================================
// FPED-1 (2026-05-28) — USDA Food Pattern food-group exposure.
// POST /api/fped/analyze/ aggregates a food list into cup/oz/tsp equivalents +
// gaps vs MyPlate/DGA and Canada's Food Guide. Deterministic; bridged CNF + WAFCT.
// ===========================================================================

export type FpedDirection = 'aim_at_least' | 'keep_at_most';
export type FpedStatus = 'short' | 'met' | 'over';

export interface FpedGap {
  component: string;
  label: string;
  unit: string;
  intake: number;
  direction: FpedDirection;
  myplate_target: number;
  cfg_target: number;
  myplate_pct_of_target: number | null;
  cfg_pct_of_target: number | null;
  myplate_status: FpedStatus;
  cfg_status: FpedStatus;
}

export interface FpedCoverage {
  n_foods: number;
  n_covered: number;
  n_no_profile: number;
  covered_mass_g: number;
  total_mass_g: number;
  coverage_pct_by_mass: number;
}

/** Audience-aware block from `explanations.fped_component_analysis`. */
export interface FpedComponentAnalysis {
  title: string;
  caveat?: string;
  coverage_note?: string;
  // individual / clinician
  headline?: string;
  main_contributions?: string[];
  eat_more?: string[];   // everyday groups the day was light on
  eat_less?: string[];   // groups to go easier on
  targets_energy_scaled?: boolean;
  reference_kcal?: number;
  single_food_mode?: boolean;
  // researcher / policy
  component_totals?: Record<string, number>;
  component_units?: Record<string, string>;
  gaps?: FpedGap[];
  coverage?: FpedCoverage;
  methodology?: string;
  caveats?: string[];
}

export interface FpedAnalyzeResponse {
  result: {
    component_totals: Record<string, number>;
    component_units: Record<string, string>;
    gaps: FpedGap[];
    coverage: FpedCoverage;
  };
  analysis: FpedComponentAnalysis;
}

// --- Cohort (food-group exposure across N recalls) ---------------------------

export interface FpedCohortComponent {
  component: string;
  label: string;
  unit: string;
  direction: FpedDirection;
  myplate_target: number;
  cfg_target: number;
  median: number;
  q1: number;
  q3: number;
  min: number;
  max: number;
  mean: number;
  pct_meeting_myplate: number;
  pct_meeting_cfg: number;
}

export interface FpedCohortCoverage {
  mean_coverage_pct_by_mass: number;
  n_recalls_with_unmatched: number;
}

export interface FpedCohortResult {
  n_recalls: number;
  components: FpedCohortComponent[];
  coverage: FpedCohortCoverage;
}

/** Audience-aware block from `explanations.fped_cohort_analysis`. */
export interface FpedCohortAnalysis {
  title: string;
  n_recalls: number;
  caveat?: string;
  coverage_note?: string;
  // individual / clinician
  headline?: string;
  adherence?: Array<{ label: string; pct_meeting: number; goal: 'more' | 'less' }>;
  // researcher / policy
  components?: FpedCohortComponent[];
  coverage?: FpedCohortCoverage;
  methodology?: string;
  caveats?: string[];
}

export interface FpedCohortResponse {
  result: FpedCohortResult;
  analysis: FpedCohortAnalysis;
}

export class FpedApiService {
  static async analyze(
    foods: Array<{ food_id: number; mass_g: number }>,
    userType: 'individual' | 'researcher' | 'policy' = 'individual',
    options: { estimatedKcal?: number } = {},
  ): Promise<FpedAnalyzeResponse> {
    const response = await api.post('/fped/analyze/', {
      foods,
      user_type: userType,
      ...(options.estimatedKcal != null && options.estimatedKcal > 0
        ? { estimated_kcal: options.estimatedKcal }
        : {}),
    });
    return {
      result: response.data.result,
      analysis: response.data.explanations.fped_component_analysis as FpedComponentAnalysis,
    };
  }

  static async cohort(
    recalls: Array<Array<{ food_id: number; mass_g: number }>>,
    userType: 'individual' | 'researcher' | 'policy' = 'individual',
  ): Promise<FpedCohortResponse> {
    const response = await api.post('/fped/cohort/', { recalls, user_type: userType });
    return {
      result: response.data.result,
      analysis: response.data.explanations.fped_cohort_analysis as FpedCohortAnalysis,
    };
  }
}

// ===========================================================================
// FPID-1 (2026-05-28) — ingredient-level food-group attribution + reconstruction QC.
// POST /api/fpid/breakdown/ : for one composite food, which ingredients contribute
// which food groups (from its US FNDDS recipe analog, USDA FPID 2017-18).
// ===========================================================================

export interface FpidGroupSource {
  sr_description: string;
  amount: number;
  pct: number;
}

export interface FpidGroupAttribution {
  component: string;
  label: string;
  unit: string;
  amount: number;
  sources: FpidGroupSource[];
}

export interface FpidIngredientRow {
  sr_description: string;
  gram_weight: number;
  share_of_recipe: number;
  has_fpid: boolean;
}

export interface FpidCoverage {
  n_ingredients: number;
  n_with_fpid: number;
  unmapped_pct: number;
}

export interface FpidBreakdown {
  available: boolean;
  food_id: number;
  fdc_id: number;
  food_code: number;
  bridge_confidence: number;
  mass_g: number;
  by_group: FpidGroupAttribution[];
  ingredients: FpidIngredientRow[];
  coverage: FpidCoverage;
  note: string;
}

export interface FpidReconstruction {
  available: boolean;
  food_id: number;
  cosine: number | null;
  plausible: boolean;
  cosine_floor: number;
  coverage: FpidCoverage;
  top_divergences: Array<{
    component: string;
    unit: string;
    twin_per_100g: number;
    reconstructed_per_100g: number;
    delta: number;
  }>;
  note: string;
}

export interface FpidBreakdownResponse {
  food_id: number;
  mass_g: number;
  breakdown: FpidBreakdown | null;
  reconstruction: FpidReconstruction | null;
  note: string | null;
}

export class FpidApiService {
  static async breakdown(foodId: number, massG = 100): Promise<FpidBreakdownResponse> {
    const response = await api.post('/fpid/breakdown/', { food_id: foodId, mass_g: massG });
    return response.data as FpidBreakdownResponse;
  }
}

/** SUBST-1 Phase 1–3 — ingredient substitution analyzer. */
export class SubstitutionApiService {
  static async analyze(request: {
    composition: SubstitutionCompositionItem[];
    purpose?: SubstitutionPurpose;
    max_suggestions?: number;
    include_scorecard?: boolean;
    dish_name?: string;
    reformulation_mode?: SubstitutionReformulationMode;
    constraints?: SubstitutionConstraints;
  }): Promise<SubstitutionAnalyzeResponse> {
    const response = await api.post('/substitution/analyze/', request);
    return response.data as SubstitutionAnalyzeResponse;
  }

  static async apply(request: {
    modified_composition: SubstitutionCompositionItem[];
  }): Promise<SubstitutionApplyResponse> {
    const response = await api.post('/substitution/apply/', request);
    return response.data as SubstitutionApplyResponse;
  }

  static async batch(request: {
    items: SubstitutionBatchItem[];
    purpose?: SubstitutionPurpose;
    max_suggestions?: number;
    include_scorecard?: boolean;
    constraints?: SubstitutionConstraints;
  }): Promise<SubstitutionBatchResponse> {
    const response = await api.post('/substitution/batch/', request);
    return response.data as SubstitutionBatchResponse;
  }
}

/** Improve-plan orchestration — recall → baseline scorecard → ranked swaps. */
export interface ImprovePlanPriorityTarget {
  ingredient_index: number;
  food_id: number;
  food_description: string;
  food_group: string;
  mass_g: number;
  mass_pct: number;
  swap_rule_id: string | null;
  flags: string[];
  priority_score: number;
}

export interface ImprovePlanPopulationContext {
  hefi?: {
    value: number;
    max: number;
    band: string;
    band_phrase: string;
    canadian_population: Record<string, number>;
    caveat: string;
  };
}

export interface ImprovePlanSuggestion extends SubstitutionSuggestion {
  scorecard_full?: SubstitutionScorecard;
}

export interface ImprovePlanResponse {
  success: boolean;
  purpose: SubstitutionPurpose;
  input: {
    source: string;
    days_used: string[];
    day_count?: number;
    export_version?: number;
  };
  baseline: {
    composition: SubstitutionCompositionItem[];
    total_mass_g: number;
    ingredient_count: number;
    scorecard: Record<string, SubstitutionScorecardMetric>;
    population_context: ImprovePlanPopulationContext | null;
  };
  priority_targets: ImprovePlanPriorityTarget[];
  suggestions: ImprovePlanSuggestion[];
  pareto_frontier?: ImprovePlanSuggestion[];
  summary: string;
  metadata: {
    endpoint: string;
    scorecard_metrics: string[];
    pareto_axes: string[];
    reformulation_mode: string;
    constraints: { max_swaps: number };
    substitution_metadata?: SubstitutionAnalyzeResponse['metadata'];
    elapsed_ms: number;
  };
}

export class ImprovePlanApiService {
  static async improvePlan(request: {
    composition?: SubstitutionCompositionItem[];
    recall_export?: {
      version: number;
      exported_from?: string;
      exported_at?: string;
      days: Array<{
        id: string;
        aggregated_daily_ingredients: SubstitutionCompositionItem[];
      }>;
    };
    day_ids?: string[];
    purpose?: SubstitutionPurpose;
    max_suggestions?: number;
    max_swaps?: number;
    reformulation_mode?: SubstitutionReformulationMode;
    include_population_benchmark?: boolean;
    dish_name?: string;
  }): Promise<ImprovePlanResponse> {
    const response = await api.post('/substitution/improve-plan/', request);
    return response.data as ImprovePlanResponse;
  }
}

// --- PKG-IMG-1 Phase 1 types (mirror backend Pydantic schema) ----------

export type HSRCategoryCode = '1' | '1D' | '2' | '2D' | '3' | '3D';

export interface ExtractedNumeric {
  value: number | null;
  unit: string | null;
  confidence: number;
  raw_text: string | null;
  from_dv_percent: boolean;
  from_kcal_conversion: boolean;
}

export interface ExtractedString {
  value: string | null;
  confidence: number;
}

export interface NutrientBlock {
  energy_kj: ExtractedNumeric;
  energy_kcal: ExtractedNumeric;
  fat_total_g: ExtractedNumeric;
  fat_sat_g: ExtractedNumeric;
  fat_trans_g: ExtractedNumeric;
  carbohydrate_total_g: ExtractedNumeric;
  fibre_g: ExtractedNumeric;
  sugars_total_g: ExtractedNumeric;
  sugars_added_g: ExtractedNumeric;
  protein_g: ExtractedNumeric;
  sodium_mg: ExtractedNumeric;
  potassium_mg: ExtractedNumeric;
  calcium_mg: ExtractedNumeric;
  iron_mg: ExtractedNumeric;
  cholesterol_mg: ExtractedNumeric;
}

export interface HSRCategoryHint {
  guess: HSRCategoryCode;
  confidence: number;
  rationale: string;
  alternatives: Array<{ category: HSRCategoryCode; reason: string }>;
}

export interface FoplOnPack {
  hsr_stars_visible: number | null;
  nutri_score_visible: string | null;
}

export interface ExtractionMetadata {
  model: string;
  provider: string;
  prompt_version: number;
  schema_version: number;
  image_sha256: string;
  image_bytes: number;
  image_dimensions: number[];
  extracted_at: string;
  extraction_warnings: string[];
  sanity_guard_rejections: string[];
  cache_hit: boolean;
  latency_ms: number | null;
}

export interface NFPanelExtraction {
  schema_version: number;
  language_detected: 'en' | 'fr' | 'en-fr' | 'es' | 'other' | 'unknown';
  panel_format_detected: 'canadian_2016' | 'us_fda_2016' | 'eu_1169_2011' | 'canadian_infant_formula' | 'unknown';
  product_name_visible: ExtractedString;
  brand_visible: ExtractedString;
  serving_size: ExtractedNumeric;
  servings_per_container: ExtractedNumeric;
  net_weight: ExtractedNumeric;
  per_serving: NutrientBlock;
  per_100g: NutrientBlock | null;
  hsr_category_hint: HSRCategoryHint;
  fopl_on_pack: FoplOnPack;
  extraction_metadata: ExtractionMetadata;
  extraction_succeeded: boolean;
  failure_reason: string | null;
}

// --- PKG-IMG-1 Phase 2 (2026-05-26) types ------------------------------

export interface IngredientEntry {
  name: string;
  position: number;
  parenthetical: string[];
  explicit_percentage: number | null;
  allergen_flag: string | null;
}

export interface IngredientListExtraction {
  ingredients_text: string;
  ingredients_parsed: IngredientEntry[];
  explicit_percentages_found: boolean;
  contains_statement: string | null;
  language_detected: NFPanelExtraction['language_detected'];
  confidence: number;
}

export interface PackagedFoodExtraction {
  schema_version: number;
  nf_panel: NFPanelExtraction | null;
  ingredient_list: IngredientListExtraction | null;
  has_nf_panel: boolean;
  has_ingredient_list: boolean;
  extraction_metadata: ExtractionMetadata;
  extraction_succeeded: boolean;
  failure_reason: string | null;
}

export interface DecomposedIngredient {
  label_name: string;
  position: number;
  food_id: number;
  food_description: string;
  food_group: string | null;
  mass_g: number;
  confidence: number;
  mass_source: 'explicit_percentage' | 'macro_constrained' | 'position_inferred';
}

export interface DecompositionResult {
  schema_version: number;
  ingredients: DecomposedIngredient[];
  net_weight_g_assumed: number;
  mass_conservation_residual_g: number;
  macro_reconciliation: Record<string, {
    panel_per_100g: number;
    inferred_per_100g: number;
    diff: number;
    rel_diff_pct: number;
    within_tolerance: boolean;
  }>;
  decomposition_confidence: number;
  decomposition_warnings: string[];
  extraction_metadata: ExtractionMetadata;
  decomposition_succeeded: boolean;
  failure_reason: string | null;
}

// --- SUBST-1 Phase 1–3: ingredient substitution -----------------------

export type SubstitutionPurpose =
  | 'general_health'
  | 'lower_sodium'
  | 'higher_fibre'
  | 'higher_protein'
  | 'lower_sat_fat'
  | 'diabetes_friendly'
  | 'sustainability';

export type SubstitutionSourceFilter = 'both' | 'cnf' | 'wafct';

export type SubstitutionCulturalContext = 'auto' | 'west_africa' | 'north_america' | 'any';

export type SubstitutionReformulationMode = 'singles' | 'greedy';

export type SubstitutionAllergen =
  | 'milk'
  | 'egg'
  | 'peanut'
  | 'tree_nut'
  | 'wheat'
  | 'soy'
  | 'fish'
  | 'shellfish'
  | 'sesame';

export interface SubstitutionConstraints {
  exclude_food_ids?: number[];
  source_filter?: SubstitutionSourceFilter;
  max_swaps?: 1 | 2 | 3 | 4;
  vegetarian?: boolean;
  same_functional_role?: boolean;
  exclude_allergens?: SubstitutionAllergen[];
  cultural_context?: SubstitutionCulturalContext;
}

export interface SubstitutionCompositionItem {
  food_id: number;
  mass_g: number;
  food_description?: string;
  food_group?: string;
  label_name?: string;
  position?: number;
}

export interface SubstitutionNutrientDelta {
  before: number;
  after: number;
  diff: number;
  pct: number;
}

export interface SubstitutionScorecardMetric {
  value: number | null;
  unit?: string;
  max?: number;
  invert?: boolean;
  available?: boolean;
  proxy?: boolean;
  error?: string;
  top_pattern_id?: string | null;
  top_pattern_label?: string | null;
}

export interface SubstitutionScorecardDeltaEntry {
  before: number | null;
  after: number | null;
  delta: number | null;
  improved: boolean | null;
}

export type SubstitutionScorecardDeltaMap = Record<string, SubstitutionScorecardDeltaEntry>;

export interface SubstitutionScorecard {
  baseline: Record<string, SubstitutionScorecardMetric>;
  modified: Record<string, SubstitutionScorecardMetric>;
  deltas: SubstitutionScorecardDeltaMap;
}

export interface SubstitutionParetoInfo {
  on_frontier: boolean;
  wins_on: string[];
}

export interface SubstitutionSuggestion {
  id?: string;
  rule_id: string;
  suggestion_type?: 'single_swap' | 'multi_swap' | 'reformulation_plan';
  candidate_source?: 'curated_rule' | 'nutrient_discovery' | 'matcher_alternative' | 'combined' | 'wafct_recipe' | 'reformulation';
  label: string;
  rationale: string;
  ingredient_index: number;
  ingredient_indices?: number[];
  reformulation_steps?: number;
  swaps?: Array<{
    original: SubstitutionSuggestion['original'];
    replacement: SubstitutionSuggestion['replacement'];
  }>;
  original: {
    food_id: number;
    food_description: string;
    food_group: string;
    mass_g: number;
    label_name?: string;
  };
  replacement: {
    food_id: number;
    food_description: string;
    mass_g: number;
  };
  modified_composition: SubstitutionCompositionItem[];
  /** FCS-only ranking: substitution analyzer no longer emits HEFI per suggestion. */
  hefi?: { before: number; after: number; delta: number };
  fcs?: { before: number; after: number; delta: number };
  sustainability_proxy?: { before: number; after: number; delta: number; note?: string };
  nutrients: Record<string, SubstitutionNutrientDelta>;
  rank_score: number;
  scorecard?: SubstitutionScorecard;
  pareto?: SubstitutionParetoInfo;
  /** FPED-1: the swap expressed in food-group terms (−red meat, +legumes, …). */
  fped_deltas?: {
    changed: Array<{
      component: string;
      label: string;
      unit: string;
      before: number;
      after: number;
      delta: number;
      direction: 'more' | 'less';
    }>;
    n_changed: number;
    partial: boolean;
  } | null;
}

export interface SubstitutionAnalyzeResponse {
  success: boolean;
  purpose: SubstitutionPurpose;
  purpose_label: string;
  dish_name?: string | null;
  baseline: {
    composition: SubstitutionCompositionItem[];
    total_mass_g: number;
    /** FCS-only ranking: baseline no longer carries HEFI. */
    hefi?: { total_score: number; max_score: number; components: Record<string, number> };
    fcs?: { total_score: number; max_score: number; nova_category?: string };
    nutrients: Record<string, number>;
    sustainability_proxy?: number;
    scorecard?: Record<string, SubstitutionScorecardMetric> | null;
  };
  suggestions: SubstitutionSuggestion[];
  pareto_frontier?: SubstitutionSuggestion[];
  metadata: {
    phase: number;
    rules_evaluated: number;
    candidates_found: number;
    single_suggestions?: number;
    multi_suggestions?: number;
    reformulation_plans?: number;
    reformulation_mode?: string;
    include_scorecard?: boolean;
    constraints?: {
      exclude_food_ids: number[];
      source_filter: string;
      max_swaps: number;
      vegetarian?: boolean;
      same_functional_role?: boolean;
      exclude_allergens?: string[];
      cultural_context?: string;
    };
    elapsed_ms: number;
  };
}

export interface SubstitutionApplyResponse {
  success: boolean;
  composition: SubstitutionCompositionItem[];
  total_mass_g: number;
  /** FCS-only ranking: apply endpoint no longer returns HEFI. */
  hefi?: { total_score: number; max_score: number; components: Record<string, number> };
  fcs: { total_score: number; max_score: number; nova_category?: string };
  nutrients: Record<string, number>;
  sustainability_proxy: number;
  scorecard: Record<string, SubstitutionScorecardMetric>;
}

export interface SubstitutionBatchItem {
  label?: string;
  composition: SubstitutionCompositionItem[];
  purpose?: SubstitutionPurpose;
  max_suggestions?: number;
  constraints?: SubstitutionConstraints;
}

export interface SubstitutionBatchResponse {
  success: boolean;
  results: Array<{ index: number; label?: string } & SubstitutionAnalyzeResponse>;
  errors: Array<{ index: number; message: string }>;
  metadata: {
    phase: number;
    count: number;
    succeeded: number;
    failed: number;
  };
}

export interface PackagedFoodExtractCombinedResponse {
  success: boolean;
  extraction: PackagedFoodExtraction;
  cache_hit: boolean;
  cache_ttl_seconds: number;
  image_count?: number;
}

export interface PackagedFoodDecomposeResponse {
  success: boolean;
  decomposition: DecompositionResult;
}

export interface PackagedFoodExtractResponse {
  success: boolean;
  extraction: NFPanelExtraction;
  cache_hit: boolean;
  cache_ttl_seconds: number;
}

export interface HSRScoreDriver {
  kind: 'baseline_high' | 'baseline_low' | 'modifying_good';
  nutrient: string;
  value: number;
  unit: string;
  value_per_100: number;
  unit_per_100: string;
  threshold_phrase: string;
  severity: 'high' | 'moderate' | 'good' | string;
}

export interface HSRInterpretiveNote {
  kind: 'condensed_product' | 'fvnl_hint' | 'ml_to_g' | string;
  severity: 'info' | 'warn' | string;
  title: string;
  message: string;
  suggestion?: string;
}

export interface HSRResultNotes {
  drivers: HSRScoreDriver[];
  notes: HSRInterpretiveNote[];
}

export interface HsrFromPanelResponse {
  success: boolean;
  hsr_result: {
    star_rating: number;
    category: HSRCategoryCode;
    baseline_points: number;
    modifying_points: number;
    final_score: number;
    level: string | null;
  };
  explanations: Record<string, Record<string, string> | unknown>;
  result_notes: HSRResultNotes;
  provenance: {
    extraction_source: 'llm_vision' | 'manual';
    model: string;
    provider: string;
    prompt_version: number;
    schema_version: number;
    image_sha256: string;
    extracted_at: string;
    confirmed_at: string;
    user_type: string;
    category_source: string;
    ml_to_g_assumption: boolean;
    serving_size_grams: number;
    consumed_portion_grams: number;
    fvnl_percent_supplied_by_user: boolean;
    extraction_warnings: string[];
    sanity_guard_rejections: string[];
  };
  user_type: string;
}

// HSR Types
export interface HSRCalculationRequest {
  food_ids: number[];
  serving_sizes: number[];
  analysis_level?: 'simple' | 'detailed';
  include_alternatives?: boolean;
  include_meal_insights?: boolean;
  /** When true, server disables alternatives and adds recall caveat (PKG-RECALL-1). */
  from_recall24h?: boolean;
  /** Audience selector for the explanations block (AUDIENCE-CODE-1 2026-05-23). */
  user_type?: 'individual' | 'researcher' | 'policy';
  /** PKG-IMG-1 Phase 2.x: swap caveat when list came from packaged-food decomposition. */
  decomposition_provenance?: 'packaged_food_inferred';
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
  // SCORECARD-1 (2026-05-26): present only when from_recall24h=true AND
  // the request had ≥2 foods. Each food is scored individually in its own
  // HSRAC v9 category at its actual serving size — the right framing for
  // the Scorecard's multi-food "within-category compare" headline.
  per_food_ratings?: Array<{
    food_id: number;
    food_name: string;
    serving_size: number;
    food_group: string;
    hsr_rating: number;
    hsr_level: string;
    category: string;
    energy_kj: number;
    key_nutrients?: Record<string, number>;
    top_strength?: string | null;
    top_concern?: string | null;
    error?: string;
  }>;
  per_food_summary?: {
    available: boolean;
    n_foods: number;
    n_failed: number;
    energy_weighted_avg: number;
    simple_avg: number;
    min: number;
    max: number;
    highest: { food_id: number; food_name: string; star_rating: number };
    lowest: { food_id: number; food_name: string; star_rating: number };
    distribution: {
      excellent: number;
      good: number;
      average: number;
      below_average: number;
      poor: number;
    };
  };
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
  /** Grams per food_id (parallel array). Defaults to 100 g each when omitted. */
  serving_sizes?: number[];
  /** Alias for serving_sizes (HEFI-style callers). */
  amounts_g?: number[];
  /** Audience selector for the explanations block (AUDIENCE-CODE-1 2026-05-23). */
  user_type?: 'individual' | 'researcher' | 'policy';
  /** PKG-IMG-1 Phase 2.x: swap caveat when list came from packaged-food decomposition. */
  decomposition_provenance?: 'packaged_food_inferred';
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
  /** Audience selector for the explanations block (AUDIENCE-CODE-1 2026-05-23). */
  user_type?: 'individual' | 'researcher' | 'policy';
  /** PKG-IMG-1 Phase 2.x: swap caveat when list came from packaged-food decomposition. */
  decomposition_provenance?: 'packaged_food_inferred';
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
    /** HEFI-CODE-1C disclosure (additive): C9 free sugars currently use CNF
     *  SUGARS, TOTAL as a proxy until the Rana et al. 2021 free-sugars
     *  supplement is integrated. Present whenever the backend returns it. */
    c9_imputation_note?: string;
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
    /** HEFI-CODE-1C disclosure (additive); see HEFIResult.data. */
    c9_imputation_note?: string;
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
      /** HEFI-CODE-1C disclosure (additive); see HEFIResult.data. */
      c9_imputation_note?: string;
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
  /** Audience selector for the explanations block (AUDIENCE-CODE-1 2026-05-23). */
  user_type?: 'individual' | 'researcher' | 'policy';
  /** PKG-IMG-1 Phase 2.x: swap caveat when list came from packaged-food decomposition. */
  decomposition_provenance?: 'packaged_food_inferred';
}

export interface HENIFoodProfileRequest {
  food_id: number;
  amount_g?: number;
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

// Actual backend payload shape — see heni_calculator_methods.py:315-324.
// Keys in `disease_breakdown` are kernel-emitted (cardiovascular_diseases,
// colorectal_cancer, other_cancers, metabolic_disorders, all_cause_mortality,
// etc.); values are per-disease μDALY contributions for this meal.
export interface DiseaseImpactAnalysis {
  disease_breakdown: Record<string, number>;
  methodology?: string;
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
}

// Environmental Impact Types
export type LcaPerspective = 'I' | 'H' | 'E';
export type LcaConsumerPerspective = 'global' | 'national';
export type LcaBasis = 'per_serving' | 'per_100g_product' | 'per_100_kcal' | 'per_100g_protein';

export interface EnvironmentalImpactRequest {
  foods: Array<{
    food_id: number;
    quantity: number;
  }>;
  user_type?: 'individual' | 'researcher' | 'policy';
  /**
   * AGRIBALYSE-INGEST §3.5 LCA matcher. When true, the backend runs the
   * LLM-assisted retrieve-then-rank pipeline against the Agribalyse 3.2
   * v32 catalog (2,425 entries) and overlays its per-food factors over
   * the cnf_integrator group defaults for the 5 directly-equivalent
   * EF→ReCiPe categories. Default false → unchanged behaviour.
   */
  enable_lca_matcher?: boolean;
  /**
   * Tier γ composite-food recipe decomposition. When true AND the food's
   * CNF group is composite (Mixed Dishes, Soups, Fast Foods, Babyfoods,
   * Sausages, Sweets, Snacks, Baked Products) AND the matcher returns
   * matched=False OR confidence < 0.85, the backend asks an LLM to express
   * the dish as a mass-weighted ingredient list constrained to retrieved
   * v32 entries; each ingredient routes through the matcher and impacts
   * are mass-weighted summed. Adds ~$0.0003 per composite; requires
   * OpenAI key on the backend. Default false.
   */
  enable_recipe_decomposer?: boolean;
  /**
   * LCA methodology pack. Default `recipe2016`. Reserved for future EF 3.1 /
   * IMPACT World+ packs once their workbooks are ingested.
   */
  methodology?: string;
  /**
   * ReCiPe 2016 cultural perspective:
   *  - 'H' (default, Hierarchist) — 100-yr GW horizon, RIVM convention
   *  - 'I' (Individualist) — 20-yr horizon, optimistic
   *  - 'E' (Egalitarian) — 1000-yr horizon, pessimistic (≈13× H on GW)
   */
  perspective?: LcaPerspective;
  /**
   * ISO-3 country code (e.g. 'CAN', 'USA'). Default `null` = world-average.
   * When set + `consumer_perspective='national'`, the backend substitutes
   * country-specific endpoint CFs for the water-consumption pathways.
   */
  country?: string | null;
  /**
   * 'global' (default) uses world-average endpoint CFs for every pathway.
   * 'national' substitutes country-specific CFs where the workbook supports
   * it (currently the three water-consumption pathways).
   */
  consumer_perspective?: LcaConsumerPerspective;
  /**
   * Functional-unit basis. Default `per_100_kcal` preserves prior behaviour.
   * All four bases are computed and returned regardless; this field only
   * controls which one is the "headline" output (`all_impacts` and
   * `endpoint_impacts`). Full multi-basis dicts are always available under
   * `impacts_by_basis` and `endpoint_impacts_by_basis`.
   */
  basis?: LcaBasis;
  /** PKG-IMG-1 Phase 2.x: swap caveat when list came from packaged-food decomposition. */
  decomposition_provenance?: 'packaged_food_inferred';
}

/**
 * Methodology info response — shape returned by GET /environmental-impact/methodology/
 * Used by the frontend's Advanced methodology panel to populate dropdowns.
 */
export interface MethodologyInfo {
  available_methodologies: string[];
  active_methodology: string;
  active_methodology_version: string;
  available_perspectives: LcaPerspective[];
  available_consumer_perspectives: LcaConsumerPerspective[];
  available_countries: string[];          // ISO-3 codes
  country_aware_pathways: string[];
  country_aware_categories: string[];
  perspective_descriptions: Record<LcaPerspective, string>;
  consumer_perspective_descriptions: Record<LcaConsumerPerspective, string>;
  methodology_provenance: {
    methodology: string;
    methodology_version: string;
    schema_version: string;
    etl_git_rev: string;
    extracted_at_utc: string;
    endpoint_pack_sha256: string;
    normalization_pack_sha256: string;
    country_pack_sha256: string;
    checksum_status: Record<string, string>;
    source_workbooks: string[];
  };
}

/**
 * Per-food matcher decision returned by the backend when
 * `enable_lca_matcher: true`. Surfaced under
 * `environmental_impacts.lca_matcher_decisions[]`.
 */
export interface LCAMatcherDecision {
  food_id: number;
  matched: boolean;
  ciqual_code: string | null;
  lci_name: string | null;
  confidence: number;
  justification: string;
  fallback_reason: string | null;
  n_candidates_considered: number;
  dqr: number | null;
  warnings: string[];
  catalog_version: string | null;
  /** Number of ReCiPe categories whose value came from the Agribalyse match. */
  categories_from_match?: number;
  /** Number of ReCiPe categories that fell back to the cnf_integrator group default. */
  categories_from_group_default?: number;
  /** True when the Canadian regional multiplier was applied (i.e. food fell back to group default). */
  regional_scaling_applied?: boolean;
  /** Full 16 EF 3.1 indicators in native units, present when matched=true. */
  ef31_indicators?: Record<string, number>;
  unit_metadata?: Record<string, string>;
}

/**
 * Single Tier γ recipe-decomposition audit row. Populated when
 * `enable_recipe_decomposer: true` AND the decomposer was triggered for the
 * food (CNF group composite + matcher failed/borderline). `matched=true`
 * here means the decomposition passed all four validation gates and its
 * mass-weighted aggregate replaced the direct matcher value.
 */
export interface RecipeDecompositionDecision {
  food_id: number;
  matched: boolean;
  ingredient_count: number;
  ingredients: Array<{
    ciqual_code: string;
    lci_name: string;
    mass_g: number;
    rationale: string;
  }>;
  total_recipe_mass_g: number;
  decomposition_confidence: number;
  unresolved_mass_g: number;
  /**
   * Audit tag. When matched=false: the validation gate that rejected
   * this decomposition (e.g. 'mass_imbalance', 'unresolved_mass_too_large',
   * 'too_few_ingredients', 'low_confidence', 'hallucinated_ciqual_code').
   * When matched=true: usually null. The exception is the value
   * 'decomposer_confirmed_direct_match', which signals that the decomposer
   * returned exactly 1 ingredient equal to the matcher's borderline-confidence
   * direct match (a "confirmation" rather than a real ingredient-level
   * decomposition; the LCA value equals exactly the matcher-direct path).
   */
  fallback_reason: string | null;
  /** Why the decomposer fired: 'matcher_failed' or 'low_matcher_confidence:<conf>'. */
  triggered_by?: string;
}

/**
 * Per-meal EF 3.1 sensitivity block. Aggregates matched-food EF indicators
 * (all 16, in native units) for side-by-side comparison with the ReCiPe
 * midpoints in the same response. EF and ReCiPe are NOT interchangeable —
 * see manuscript §3.2 dual-namespace policy.
 */
export interface RecipeEF31SensitivityBlock {
  matched_count: number;
  ef31_aggregated_per_meal: Record<string, number>;
  unit_metadata: Record<string, string>;
  note: string;
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

// v1 LCA scope trim: backend consumes only the 3 literature-anchored midpoint
// categories (Global warming, Land use, Water consumption). The other 15 are
// not part of the consumed vector — see backend §7.5 manuscript and
// `_smoke_validate_cnf_integrator.py`. Trimmed-category fields are typed
// optional so legacy consumers don't crash, but they will be `undefined` in
// v1 responses.
export interface LCAResults {
  'Global warming'?: number;
  'Land use'?: number;
  'Water consumption'?: number;
  // The following 15 are NOT returned in v1 (kept optional for legacy code paths).
  'Fine particulate matter formation'?: number;
  'Terrestrial acidification'?: number;
  'Freshwater eutrophication'?: number;
  'Marine eutrophication'?: number;
  'Stratospheric ozone depletion'?: number;
  'Fossil resource scarcity'?: number;
  'Mineral resource scarcity'?: number;
  'Terrestrial ecotoxicity'?: number;
  'Freshwater ecotoxicity'?: number;
  'Marine ecotoxicity'?: number;
  'Human carcinogenic toxicity'?: number;
  'Human non-carcinogenic toxicity'?: number;
  'Ionizing radiation'?: number;
  'Ozone formation, Human health'?: number;
  'Ozone formation, Terrestrial ecosystems'?: number;
}

// v1 'demote, don't perfect' uncertainty bands. Each consumed category maps
// to a {low, central, high} envelope derived from P&N 10th-percentile/mean
// ratios + M&H spatial spread. Not a 90% CI — a worst/best-case bound.
export interface UncertaintyBand {
  low: number;
  central: number;
  high: number;
}

export interface LCABands {
  'Global warming'?: UncertaintyBand;
  'Land use'?: UncertaintyBand;
  'Water consumption'?: UncertaintyBand;
}

export interface EndpointImpacts {
  'Human Health'?: number;
  'Ecosystems'?: number;
  // Resources is null in v1 because both Fossil + Mineral scarcity midpoints
  // are not consumed; surfaced as `null` rather than `0` to signal not-estimable.
  'Resources'?: number | null;
}

export interface EndpointBands {
  'Human Health'?: UncertaintyBand;
  'Ecosystems'?: UncertaintyBand;
  // Resources intentionally omitted in v1 (None at the scalar level).
}

/** CODE-4 per-category source attribution. Pinned at
 *  `backend/environmental_impact_model/src/monetization.py:159-211`.
 *  Status `'verified'` means the value was reconciled against the cited
 *  page; `'pending_page_citation'` means the source family is known
 *  (CE Delft, True Price) but the exact figure has not yet been pinned. */
export interface EnvironmentalValueSource {
  source: string;
  currency_year: string;
  status: 'verified' | 'pending_page_citation' | string;
  last_verified: string;
  page_anchor?: string;
  sensitivity_range_2026?: string;
  methodological_note?: string;
  override_env?: string;
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
  /** CODE-4 per-category source attribution (additive). Visible whenever
   *  the backend includes it (every analyze + batch + profile path does). */
  value_sources?: Record<string, EnvironmentalValueSource>;
}

/** CODE-5 per-category factor confidence. Keys mirror the consumed
 *  midpoint categories (Global warming / Land use / Water consumption).
 *  Backend shape: `{level, rationale}` (see
 *  `backend/environmental_impact_model/src/life_cycle_assessment.py:69` —
 *  `LCA_FACTOR_CONFIDENCE`). */
export interface EnvironmentalFactorConfidence {
  level: 'high' | 'medium' | 'low' | string;
  rationale: string;
}

/** CODE-5 data-quality report. Emitted at
 *  `backend/environmental_impact_model/src/life_cycle_assessment.py:767-799`. */
export interface EnvironmentalDataQuality {
  methodology_version: string;
  perspective?: string;
  country?: string | null;
  consumer_perspective?: string;
  methodology_provenance?: Record<string, unknown>;
  sources: string[];
  confidence_summary?: {
    high_confidence: number;
    medium_confidence: number;
    low_confidence: number;
  };
  confidence_by_category?: Record<string, EnvironmentalFactorConfidence>;
  endpoint_factor_sources?: Record<string, string>;
  known_issues: string[];
  recommendations: string[];
}

export interface SustainabilityScore {
  overall_sustainability_score: number;
  sustainability_rating: string;
  environmental_score: number;
  environmental_rating?: string;
  nutritional_score: number;
  processing_score: number;
  category_scores: Record<string, number>;
  // v1 literature-anchored zone scoring: per-category Low/Moderate/High
  // dominant zone (Stylianou 2021 SI Table 11B + P&N 2018 land panel).
  category_zones?: Record<string, 'Low' | 'Moderate' | 'High' | 'Unknown'>;
  methodology_note?: string;
  overall_weights?: { environmental: number; nutritional: number; processing: number };
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

/** PLANETARY-1: EAT-Lancet 2.0 Table 2 per-capita-per-day boundary share.
 *  Mirrors `backend/environmental_impact_model/src/planetary_boundaries.py`
 *  `compute_planetary_boundary_shares()` output. */
export interface PlanetaryBoundaryShareRow {
  key:
    | 'climate_change' | 'land_use' | 'water_consumption'
    | 'biosphere_integrity_hanpp' | 'stratospheric_ozone_n2o'
    | 'ocean_acidification' | 'nitrogen_surplus' | 'phosphorus_loss'
    | 'novel_entities_pesticides';
  label: string;
  control_variable: string;
  unit: string;
  available: boolean;
  global_boundary_per_year: number;
  global_boundary_source: string;
  current_food_system_contribution: string;
  /** Present on available rows: ReCiPe midpoint we read from the meal. */
  recipe_midpoint_key?: string;
  /** Present on available rows: the meal's value in `unit`. */
  meal_value?: number | null;
  /** Present on available rows: per-capita-per-day allocation in `unit`. */
  per_capita_daily_budget?: number;
  /** Present on available rows: 100 × meal_value / per_capita_daily_budget. */
  share_of_daily_budget_pct?: number | null;
  method_note?: string;
  /** Present on unavailable rows (and on available rows when the meal value
   *  is missing). Explains why no share is shown. */
  reason?: string;
}

export interface PlanetaryBoundaryShares {
  shares: PlanetaryBoundaryShareRow[];
  n_covered: number;
  n_total: number;
  population_assumption: number;
  days_per_year: number;
  citation: {
    citation: string;
    doi: string;
    table: string;
    manuscript_anchor: string;
  };
  method_note: string;
}

export interface PlanetaryBoundaryExplanations {
  title: string;
  headline: string;
  message: string;
  mandatory_caveat: string;
}

export interface EnvironmentalImpactResult {
  success: boolean;
  data: {
    meal_analysis: {
      lca_results: LCAResults;
      endpoint_impacts: EndpointImpacts;
      // v1 'demote, don't perfect' uncertainty bands. Parallel to
      // lca_results / endpoint_impacts; each consumed category maps to
      // {low, central, high}. Present only for the 3 grounded midpoints.
      lca_results_bands?: LCABands;
      endpoint_impacts_bands?: EndpointBands;
      single_score: number;
      monetization: EnvironmentalMonetization;
      sustainability_score: SustainabilityScore;
      meal_composition: MealComposition;
      /**
       * AGRIBALYSE-INGEST §3.5 LCA matcher audit + EF 3.1 sensitivity.
       * `enabled=false` and empty arrays when `enable_lca_matcher` was off
       * in the request (default behaviour).
       */
      lca_matcher: {
        enabled: boolean;
        catalog_version: string | null;
        decisions: LCAMatcherDecision[];
        sensitivity: RecipeEF31SensitivityBlock | null;
      };
      /**
       * Tier γ recipe-decomposition audit. `enabled=false` and empty
       * decisions array when `enable_recipe_decomposer` was off in the
       * request (default behaviour). Decisions are populated even on
       * decomposition failure — `matched=false` rows carry the
       * `fallback_reason` from one of the four validation gates.
       */
      recipe_decomposer?: {
        enabled: boolean;
        decisions: RecipeDecompositionDecision[];
      };
      /**
       * Server-computed midpoint dicts keyed by functional unit (`per_serving`,
       * `per_100g_product`, …). `per_serving` is the raw aggregated impact for
       * the actual grams entered — use for “this portion” previews when
       * `reporting_basis` is a normalized column.
       */
      impacts_by_basis?: Record<string, Partial<LCAResults>>;
      /** Advanced-panel basis matching `lca_results` normalization. */
      reporting_basis?: string;
      /** PLANETARY-1 (2026-05-27): per-meal share of per-capita-per-day
       *  food-system planetary boundary (EAT-Lancet 2.0 Table 2). v1 covers
       *  3 of 9 boundaries (climate, land, water); the other 6 surface as
       *  `available=false` placeholders. */
      planetary_boundary_shares?: PlanetaryBoundaryShares;
      /** PLANETARY-1: audience-aware explanation pack for the planetary
       *  overlay (Individual / Researcher / Policy). */
      planetary_explanations?: PlanetaryBoundaryExplanations;
      /** CODE-5 per-category confidence rating (additive). */
      factor_confidence_by_category?: Record<string, EnvironmentalFactorConfidence>;
      /** CODE-5 data-quality report (additive). May appear here or under
       *  `lca_quality` depending on endpoint; both shapes share the same
       *  inner type. */
      data_quality?: EnvironmentalDataQuality;
      /** CODE-5 sibling slot used by the env profile / batch paths. */
      lca_quality?: {
        factor_confidence_by_category?: Record<string, EnvironmentalFactorConfidence>;
        data_quality?: EnvironmentalDataQuality;
      };
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
  /**
   * Cached singleton fetch of methodology metadata. The data rarely changes
   * (only when the methodology pack is rebuilt) so we hit the backend once
   * per page load and reuse.
   */
  private static _methodologyInfoCache: MethodologyInfo | null = null;
  static async getMethodologyInfo(force: boolean = false): Promise<MethodologyInfo> {
    if (!force && this._methodologyInfoCache) {
      return this._methodologyInfoCache;
    }
    const response = await api.get('/environmental-impact/methodology/');
    const info = (response.data?.data || response.data) as MethodologyInfo;
    this._methodologyInfoCache = info;
    return info;
  }

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

    const impactsByBasisRaw = envImpacts.impacts_by_basis;
    const impacts_by_basis =
      impactsByBasisRaw && typeof impactsByBasisRaw === 'object'
        ? (Object.fromEntries(
            Object.entries(impactsByBasisRaw as Record<string, Record<string, unknown>>).map(
              ([basis, mids]) => [
                basis,
                Object.fromEntries(
                  Object.entries(mids || {}).map(([cat, val]) => {
                    const n = typeof val === 'string' ? Number(val) : val;
                    return [cat, typeof n === 'number' && Number.isFinite(n) ? n : 0];
                  }),
                ),
              ],
            ),
          ) as EnvironmentalImpactResult['data']['meal_analysis']['impacts_by_basis'])
        : undefined;
    
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
          // v1 bands — wired through from backend `all_impacts_bands` /
          // `endpoint_impacts_bands` parallel fields.
          lca_results_bands: envImpacts.all_impacts_bands || {},
          endpoint_impacts_bands: envImpacts.endpoint_impacts_bands || {},
          single_score: typeof envImpacts.summary_score?.value === 'number' ? envImpacts.summary_score.value : (outerData?.data?.environmental_impacts?.summary_score?.value ?? 0),
          monetization: {
            monetized_impacts: monetData.results?.monetized_impacts || {},
            total_cost: monetData.results?.total_environmental_cost?.value || 0,
            cost_per_calorie: monetData.results?.cost_per_calorie?.value || 0,
            cost_per_protein: monetData.results?.cost_per_protein?.value || 0,
            cost_breakdown_by_category: monetData.results?.cost_breakdown || {},
            top_cost_drivers: monetData.results?.top_cost_drivers || [],
            // CODE-4 per-category source attribution (additive). Backend
            // emits at `monetization.results.value_sources` — pass through
            // verbatim; `undefined` when the backend doesn't ship it.
            value_sources: (monetData.results?.value_sources as
              EnvironmentalImpactResult['data']['meal_analysis']['monetization']['value_sources']) || undefined,
          },
          sustainability_score: {
            // Prefer backend-provided sustainability block; fall back conservatively if missing
            overall_sustainability_score: sustainability.overall_sustainability_score ?? 50,
            sustainability_rating: sustainability.sustainability_rating ?? (overallAssessment.rating || 'Unknown'),
            environmental_score: sustainability.environmental_score ?? 0,
            environmental_rating: sustainability.environmental_rating,
            nutritional_score: sustainability.nutritional_score ?? 0,
            processing_score: sustainability.processing_score ?? 0,
            category_scores: sustainability.category_scores || {},
            // v1 literature-anchored zone scoring (Stylianou 2021 + P&N 2018).
            category_zones: sustainability.category_zones || {},
            methodology_note: sustainability.methodology_note,
            overall_weights: sustainability.overall_weights,
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
          },
          // AGRIBALYSE-INGEST §3.5 matcher: surface the audit trail + EF 3.1
          // sensitivity block when `enable_lca_matcher: true` was sent.
          // Both arrays/objects are empty/null when the flag is off.
          lca_matcher: {
            enabled: envImpacts.lca_matcher_enabled === true,
            catalog_version: envImpacts.catalog_version ?? null,
            decisions: (envImpacts.lca_matcher_decisions as LCAMatcherDecision[] | undefined) || [],
            sensitivity: (envImpacts.recipe2016_h_ef31_sensitivity as RecipeEF31SensitivityBlock | undefined) || null,
          },
          // Tier γ recipe decomposer: surface audit trail when
          // `enable_recipe_decomposer: true` was sent (default off).
          recipe_decomposer: {
            enabled: envImpacts.recipe_decomposer_enabled === true,
            decisions: (envImpacts.recipe_decomposition_decisions as RecipeDecompositionDecision[] | undefined) || [],
          },
          impacts_by_basis,
          reporting_basis:
            typeof envImpacts.reporting_basis === 'string'
              ? envImpacts.reporting_basis
              : 'per_100_kcal',
          // CODE-5 per-category factor confidence + data-quality report
          // (additive). Backend emits both inside `environmental_impacts`;
          // pass through verbatim. `undefined` when backend doesn't ship them.
          factor_confidence_by_category: (envImpacts.factor_confidence_by_category as
            EnvironmentalImpactResult['data']['meal_analysis']['factor_confidence_by_category']) || undefined,
          data_quality: (envImpacts.data_quality as
            EnvironmentalImpactResult['data']['meal_analysis']['data_quality']) || undefined,
          // PLANETARY-1: pass through E28 Table 2 boundary shares + audience-
          // aware explanations. Backward-compatible: undefined when an older
          // backend deploy doesn't emit them, in which case the UI hides the card.
          planetary_boundary_shares:
            (envImpacts.planetary_boundary_shares as PlanetaryBoundaryShares | undefined) || undefined,
          planetary_explanations:
            (envImpacts.planetary_explanations as PlanetaryBoundaryExplanations | undefined) || undefined,
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

    // AGRIBALYSE-INGEST §3.5 matcher: surface audit + sensitivity when
    // the raw response carries them (additive — empty/disabled by default).
    const matcherRaw = (maObj?.lca_matcher as Record<string, unknown> | undefined) ?? {};
    const lca_matcher: EnvironmentalImpactResult['data']['meal_analysis']['lca_matcher'] = {
      enabled: Boolean(matcherRaw?.enabled),
      catalog_version: (matcherRaw?.catalog_version as string | null) ?? null,
      decisions: Array.isArray(matcherRaw?.decisions)
        ? (matcherRaw.decisions as LCAMatcherDecision[])
        : [],
      sensitivity: (matcherRaw?.sensitivity as RecipeEF31SensitivityBlock | null) ?? null,
    };

    // v1 uncertainty-band parsing (parallel to lca_results / endpoint_impacts).
    const lca_results_bands_raw = (maObj as Record<string, unknown>)['lca_results_bands']
      || (maObj as Record<string, unknown>)['all_impacts_bands'];
    const endpoint_impacts_bands_raw = (maObj as Record<string, unknown>)['endpoint_impacts_bands'];
    const coerceBands = (raw: unknown): Record<string, UncertaintyBand> | undefined => {
      if (!raw || typeof raw !== 'object') return undefined;
      const out: Record<string, UncertaintyBand> = {};
      for (const [k, v] of Object.entries(raw as Record<string, unknown>)) {
        if (v && typeof v === 'object') {
          const o = v as Record<string, unknown>;
          out[k] = {
            low:     safeNumber(o.low, 0),
            central: safeNumber(o.central, 0),
            high:    safeNumber(o.high, 0),
          };
        }
      }
      return out;
    };

    const normalized: EnvironmentalImpactResult = {
      success: Boolean((root?.success as boolean | undefined) ?? true),
      data: {
        meal_analysis: {
          lca_results,
          endpoint_impacts,
          lca_results_bands: coerceBands(lca_results_bands_raw) as LCABands | undefined,
          endpoint_impacts_bands: coerceBands(endpoint_impacts_bands_raw) as EndpointBands | undefined,
          single_score: safeNumber(maObj?.single_score, 0),
          monetization,
          sustainability_score,
          meal_composition,
          lca_matcher,
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
  username_or_email: string;
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

export interface MealMedia {
  id: string;
  media_type: 'image' | 'video';
  file: string;
  thumbnail?: string;
  caption: string;
  order: number;
  is_primary: boolean;
  file_size?: number;
  file_size_mb?: number;
  duration?: number;
  width?: number;
  height?: number;
  created_at: string;
  updated_at: string;
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
  heni_total_score?: number;
  environmental_impact: Record<string, number>;
  sustainability_score?: number;
  carbon_footprint?: number;
  preparation_time?: number;
  cooking_time?: number;
  servings: number;
  difficulty_level: 'easy' | 'medium' | 'hard';
  instructions: string;
  tips: string;
  image?: string; // Legacy field for backward compatibility
  media_files?: MealMedia[]; // New media files
  primary_media?: MealMedia; // Primary media file
  media_count?: number; // Total number of media files
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
  image?: File; // Legacy field for backward compatibility
  media_files?: File[]; // New media files
  media_captions?: string[]; // Captions for media files
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
      } else if (key === 'media_files' && Array.isArray(value)) {
        // Add media files
        (value as File[]).forEach(file => {
          formData.append('media_files', file);
        });
      } else if (key === 'media_captions' && Array.isArray(value)) {
        // Add media captions as JSON string
        formData.append('media_captions', JSON.stringify(value));
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
    // If media files are included, use FormData
    if (mealData.media_files && mealData.media_files.length > 0) {
      const formData = new FormData();
      
      // Add all non-file fields
      Object.entries(mealData).forEach(([key, value]) => {
        if (key === 'media_files' && Array.isArray(value)) {
          // Add media files
          (value as File[]).forEach(file => {
            formData.append('media_files', file);
          });
        } else if (key === 'media_captions' && Array.isArray(value)) {
          // Add media captions
          formData.append('media_captions', JSON.stringify(value));
        } else if (key === 'food_items' || key === 'tags') {
          formData.append(key, JSON.stringify(value));
        } else if (value !== undefined && value !== null) {
          formData.append(key, String(value));
        }
      });

      const response = await api.patch(`/meals/meals/${id}/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response.data;
    } else {
      // Regular JSON update for non-media updates
      const response = await api.patch(`/meals/meals/${id}/`, mealData);
      return response.data;
    }
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

  static async getMyMeals(params: { ordering?: string } = {}): Promise<{ results: Meal[] }> {
    const response = await api.get('/meals/meals/my_meals/', { params });
    // Normalize to always return { results }
    const body = response.data;
    if (Array.isArray(body)) return { results: body as Meal[] };
    if (body && Array.isArray(body.results)) return { results: body.results as Meal[] };
    if (body && body.data) {
      if (Array.isArray(body.data)) return { results: body.data as Meal[] };
      if (Array.isArray(body.data?.results)) return { results: body.data.results as Meal[] };
    }
    return { results: [] };
  }

  static async getSavedMeals(params: { ordering?: string } = {}): Promise<{ results: Meal[] }> {
    const response = await api.get('/meals/meals/saved_meals/', { params });
    // Normalize to always return { results }
    const body = response.data;
    if (Array.isArray(body)) return { results: body as Meal[] };
    if (body && Array.isArray(body.results)) return { results: body.results as Meal[] };
    if (body && body.data) {
      if (Array.isArray(body.data)) return { results: body.data as Meal[] };
      if (Array.isArray(body.data?.results)) return { results: body.data.results as Meal[] };
    }
    return { results: [] };
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

  static async recalculateMealMetrics(mealId: string): Promise<{ message: string; meal: Meal }> {
    const response = await api.post(`/meals/meals/${mealId}/recalculate/`);
    return response.data;
  }

  // Media management
  static async getMealMedia(mealId: string): Promise<MealMedia[]> {
    const response = await api.get(`/meals/media/`, { params: { meal_id: mealId } });
    return response.data;
  }

  static async uploadMealMedia(mealId: string, mediaData: {
    file: File;
    caption?: string;
    order?: number;
  }): Promise<MealMedia> {
    const formData = new FormData();
    formData.append('file', mediaData.file);
    if (mediaData.caption) formData.append('caption', mediaData.caption);
    if (mediaData.order !== undefined) formData.append('order', mediaData.order.toString());
    formData.append('meal', mealId);

    const response = await api.post(`/meals/media/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }

  static async updateMealMedia(mediaId: string, updates: Partial<MealMedia>): Promise<MealMedia> {
    const response = await api.patch(`/meals/media/${mediaId}/`, updates);
    return response.data;
  }

  static async deleteMealMedia(mediaId: string): Promise<void> {
    await api.delete(`/meals/media/${mediaId}/`);
  }

  static async setPrimaryMedia(mediaId: string): Promise<{ message: string }> {
    const response = await api.post(`/meals/media/${mediaId}/set_primary/`);
    return response.data;
  }
}

export default CNFApiService; 