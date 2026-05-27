'use client';

import React, { useEffect, useState } from 'react';
import { 
  CalculatorIcon,
  XMarkIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { HEFIApiService, CNFApiService, type HEFIResult, type FilterOptions, type HEFIInterpretation } from '../../../lib/api';
import { AudienceToggle, type UserType, type ExplanationsBlock } from '../../../components/shared/AudienceToggle';
import { ExplanationsPanel } from '../../../components/shared/ExplanationsPanel';
import { AIEnhancedSearch } from '../../../components/shared/AIEnhancedSearch';
import { RecipeDecomposerModal } from '../../../components/shared/RecipeDecomposerModal';
import { SourceFilter, type SourceChoice } from '../../../components/shared/SourceFilter';
import { useRecall24hReceiver } from '../../../components/shared/useRecall24hReceiver';
import { FoodListPanel } from '../../../components/shared/FoodListPanel';
import { CollapsibleSection } from '../../../components/shared/CollapsibleSection';
import { Plus } from 'lucide-react';

interface SelectedFood {
  FoodID: number;
  FoodDescription: string;
  FoodCode?: string;
  amount_g: number;
}

// Minimal shape returned by CNF search used in this UI
interface SearchResult {
  FoodID: number;
  FoodDescription: string;
  FoodCode?: string;
}

  // FIX (HEFI audit fix #2): kernel-internal key → human-readable label. Without
  // this map, the Key Ratios panel rendered "ratio vf", "sodden", "sfa perc"
  // (lowercase-snake-case) which is researcher-jargon, not researcher-readable.
  const RATIO_LABELS: Record<string, string> = {
    RATIO_VF:      'Vegetables & fruits / total foods',
    RATIO_WGTOT:   'Whole grains / total foods',
    RATIO_WGGR:    'Whole grains / grain foods',
    RATIO_PRO:     'Protein foods / total foods',
    RATIO_PLANT:   'Plant protein / protein foods',
    RATIO_BEV:     'Recommended beverages / total beverages',
    RATIO_UNSFAT:  '(MUFA + PUFA) / SFA',
    SFA_PERC:      'Saturated fat (% energy)',
    SUG_PERC:      'Free sugars (% energy)',
    SODDEN:        'Sodium density (mg / kcal)',
  };

  // Same treatment for Nutritional Inputs. The "_ra" suffix is Brassard's
  // "reference amount" — jargon without context.
  const INPUT_LABELS: Record<string, string> = {
    total_foods_ra:          'Total foods (reference-amount equivalents)',
    energy_kcal:             'Energy (kcal)',
    vf_ra:                   'Vegetables & fruits (ref. amts)',
    whole_grains_ra:         'Whole grains (ref. amts)',
    total_grains_ra:         'Total grains (ref. amts)',
    protein_foods_ra:        'Protein foods (ref. amts)',
    plant_protein_foods_ra:  'Plant protein foods (ref. amts)',
    total_beverages_g:       'Total beverages (g)',
    recommended_beverages_g: 'Recommended beverages (g)',
    sfa_g:                   'Saturated fat (g)',
    mufa_g:                  'Monounsaturated fat (g)',
    pufa_g:                  'Polyunsaturated fat (g)',
    free_sugars_g:           'Free sugars (g)',
    sodium_mg:               'Sodium (mg)',
  };

  // FIX (HEFI audit fix #4): per-component scoring-rule microcopy, sourced from
  // Brassard et al. 2022a Table 2 p. 600. Surfaced as a small caption under
  // each component bar so a researcher can audit the score in context.
  const COMPONENT_RULES: Record<string, string> = {
    C1_VF:         'Adequacy: full 20 pts if ≥ 0.50 ref. amts of V&F per total ref. amts; 0 at 0.',
    C2_WHOLEGR:    'Adequacy: full 5 pts if whole-grain ref. amts ≥ 0.25 of total foods; 0 at 0.',
    C3_GRRATIO:    'Adequacy: full 5 pts if whole grains / total grains ≥ 1.0; 0 at 0.',
    C4_PROFOODS:   'Adequacy: full 5 pts if protein foods / total foods ≥ 0.25; 0 at 0.',
    C5_PLANTPRO:   'Adequacy: full 5 pts if plant protein / protein foods ≥ 0.50; 0 at 0.',
    C6_BEVERAGES:  'Adequacy: full 10 pts if recommended beverages / total beverages = 1.0; 0 at 0.',
    C7_FATTYACID:  'Moderation: full 5 pts if (MUFA+PUFA) / SFA ≥ 2.6; 0 if ≤ 1.1.',
    C8_SFAT:       'Moderation: full 5 pts if SFA ≤ 10 % of energy; 0 if ≥ 15 %.',
    C9_FREESUGARS: 'Moderation: full 10 pts if free sugars ≤ 20 % of energy; 0 if ≥ 30 %.',
    C10_SODIUM:    'Moderation: full 10 pts if sodium density ≤ 0.9 mg/kcal; 0 if ≥ 2.0 mg/kcal.',
  };

  const HEFIScoreDisplay = ({ result }: { result: HEFIResult }) => {
  const { data } = result;
    const interpretation: HEFIInterpretation | undefined = data.hefi_interpretation as HEFIInterpretation | undefined;
    const numFoods = Array.isArray(data.food_ids) ? data.food_ids.length : 0;

    const chipColor = interpretation?.ui_color === 'emerald'
      ? 'text-emerald-700 bg-emerald-50 border-emerald-200'
      : interpretation?.ui_color === 'green'
      ? 'text-green-700 bg-green-50 border-green-200'
      : interpretation?.ui_color === 'yellow'
      ? 'text-yellow-700 bg-yellow-50 border-yellow-200'
      : interpretation?.ui_color === 'red'
      ? 'text-red-700 bg-red-50 border-red-200'
      : 'text-gray-700 bg-gray-50 border-gray-200';

  return (
    <div className="space-y-8">
      {/* Overall Score */}
      <div className={`border rounded-2xl p-8 text-center ${chipColor.split(' ').slice(1, 2).join(' ')}`}>
        <div className="flex items-center justify-center mb-4">
          <CheckCircleIcon className={`w-12 h-12 ${chipColor.split(' ')[0]}`} />
        </div>
        <div className="space-y-3">
          <div className="text-4xl font-bold text-gray-900">
            {data.total_score.toFixed(1)} / {data.max_total_score}
          </div>
          {interpretation && (
            <div className={`inline-flex items-center px-3 py-1 border rounded-full text-sm font-semibold ${chipColor}`}>
              {interpretation.category}
            </div>
          )}
          <div className="text-gray-600">HEFI Score</div>
          {interpretation?.description && (
            <p className="text-sm text-gray-700 max-w-2xl mx-auto">{interpretation.description}</p>
          )}
          {interpretation?.notes && interpretation.notes.length > 0 && (
            <div className="text-xs text-gray-500 max-w-2xl mx-auto">
              <ul className="list-disc list-inside space-y-1">
                {interpretation.notes.map((n, idx) => (
                  <li key={idx}>{n}</li>
                ))}
              </ul>
            </div>
          )}
          {interpretation?.population_benchmarks && (
            <div className="text-xs text-gray-500">
              Population benchmarks: mean {interpretation.population_benchmarks.mean}, p1 {interpretation.population_benchmarks.percentile_1}, p99 {interpretation.population_benchmarks.percentile_99}
            </div>
          )}
        </div>
      </div>

      {/* Components Breakdown — with empty-component annotation (#3) and
          per-component scoring-rule microcopy (#4). */}
      <div className="card">
        <h3 className="text-xl font-bold text-gray-900 mb-6">Component Scores</h3>
        {numFoods <= 1 && (
          <div className="mb-4 text-xs text-gray-600 bg-yellow-50 border border-yellow-200 rounded-md p-3">
            <strong>Single-food caveat:</strong> HEFI-2019 is a 24-h dietary-pattern index.
            Components that depend on contributions from other food groups (V&amp;F, grains,
            beverages, etc.) naturally score 0 when only one food is scored.
          </div>
        )}
        <div className="space-y-4">
          {Object.entries(data.components).map(([key, component]) => {
            const percentage = (component.score / component.max_points) * 100;
            const isEmpty = component.score === 0;
            const rule = COMPONENT_RULES[key];
            return (
              <div key={key} className="flex items-start justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">{component.name}</span>
                    {isEmpty && (
                      <span className="text-[10px] uppercase tracking-wide bg-gray-200 text-gray-600 rounded px-1.5 py-0.5">
                        N/A for this food
                      </span>
                    )}
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div
                      className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(percentage, 100)}%` }}
                    />
                  </div>
                  {rule && (
                    <div className="text-xs text-gray-500 mt-2">{rule}</div>
                  )}
                </div>
                <div className="ml-4 text-right">
                  <div className="text-lg font-semibold text-gray-900">
                    {component.score.toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-500">
                    / {component.max_points}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Ratios — labels from RATIO_LABELS map (fix #2) */}
      <div className="card">
        <h3 className="text-xl font-bold text-gray-900 mb-6">Key Ratios</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {Object.entries(data.ratios).map(([key, value]) => (
            <div key={key} className="bg-gray-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-purple-600">
                {typeof value === 'number' ? value.toFixed(2) : value}
              </div>
              <div className="text-sm text-gray-600 mt-1">
                {RATIO_LABELS[key] || key.replace(/_/g, ' ').toLowerCase()}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Nutritional Inputs — labels from INPUT_LABELS map (fix #2) */}
      <div className="card">
        <h3 className="text-xl font-bold text-gray-900 mb-6">Nutritional Inputs</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(data.inputs).map(([key, value]) => (
            <div key={key} className="bg-gray-50 rounded-lg p-4">
              <div className="text-lg font-semibold text-gray-900">
                {typeof value === 'number' ? value.toFixed(1) : value}
              </div>
              <div className="text-sm text-gray-600">
                {INPUT_LABELS[key] || key.replace(/_/g, ' ').toLowerCase()}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default function HEFICalculatePage() {
  const [selectedFoods, setSelectedFoods] = useState<SelectedFood[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchIsLoading, setSearchIsLoading] = useState(false);
  const [result, setResult] = useState<HEFIResult | null>(null);
  const [userType, setUserType] = useState<UserType>('individual');
  // AUDIENCE-CODE-1 follow-up: track which userType the current `result` was
  // computed under so we can flag stale explanations when the user toggles.
  const [lastCalcUserType, setLastCalcUserType] = useState<UserType | null>(null);
  const [recipeModalOpen, setRecipeModalOpen] = useState(false);
  // AI-MATCH-2 (2026-05-24): true when the food list was injected from the
  // /recall-24h wizard. Recasts the pattern-level caveat: HEFI was DESIGNED
  // for 24-h recall data (Brassard 2022b), so framing the recall as a
  // "single-food estimate" would actively mislead. The Brassard single-day
  // caveat (multiple recalls for usual-intake) still applies and surfaces
  // via the explanations block.
  const [cameFromRecall, setCameFromRecall] = useState(false);
  // WAFCT-EXTEND (2026-05-24): per-search food-database scope.
  const [sourceFilter, setSourceFilter] = useState<SourceChoice>('both');
  const [error, setError] = useState<string>('');
  const [filters, setFilters] = useState<FilterOptions | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedMethod, setSelectedMethod] = useState<string>('');

  useEffect(() => {
    const loadFilters = async () => {
      try {
        const data = await CNFApiService.getFoodFilters();
        setFilters(data);
      } catch (e) {
        // Non-fatal
        console.warn('Failed to load CNF filters', e);
      }
    };
    loadFilters();
  }, []);

  // AI-MATCH-2 (2026-05-24): pick up an aggregated 24-h recall payload
  // handed off from /recall-24h. Pre-populates the food picker so the user
  // sees their day's CNF foods ready to score. Fires once per mount.
  useRecall24hReceiver({
    target: 'hefi',
    onIngredients: (ingredients, meta) => {
      setUserType(meta.user_type);
      setCameFromRecall(true);
      setSelectedFoods(ingredients.map(i => ({
        FoodID: i.food_id,
        FoodDescription: i.food_description,
        amount_g: i.mass_g,
      })));
    },
  });

  // Debounced search with filters (enhanced -> fallback)
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    // Avoid hitting backend with too-short queries (backend enforces min length 2)
    if (searchQuery.trim().length < 2) {
      setSearchResults([]);
      return;
    }

    const timeoutId = setTimeout(async () => {
      setSearchIsLoading(true);
      try {
        try {
          const enhanced = await CNFApiService.searchFoodsEnhanced({
            query: searchQuery,
            limit: 50,
            category: selectedCategory || undefined,
            method: selectedMethod || undefined,
            source: sourceFilter,
          });
          setSearchResults(enhanced.results || []);
        } catch {
          const basic = await CNFApiService.searchFoods(searchQuery, 50, 0, sourceFilter);
          setSearchResults(basic.results || []);
        }
      } catch (err) {
        console.error('Search error:', err);
        setSearchResults([]);
      } finally {
        setSearchIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, selectedCategory, selectedMethod, sourceFilter]);

  const addFood = (food: SearchResult) => {
    const newFood: SelectedFood = {
      FoodID: food.FoodID,
      FoodDescription: food.FoodDescription,
      FoodCode: food.FoodCode,
      amount_g: 100 // Default amount
    };
    
    if (!selectedFoods.some(f => f.FoodID === food.FoodID)) {
      setSelectedFoods([...selectedFoods, newFood]);
    }
    setSearchQuery('');
    setSearchResults([]);
  };

  const removeFood = (foodId: number) => {
    setSelectedFoods(selectedFoods.filter(f => f.FoodID !== foodId));
  };

  const updateFoodAmount = (foodId: number, amount: number) => {
    setSelectedFoods(selectedFoods.map(f => 
      f.FoodID === foodId ? { ...f, amount_g: Math.max(0.1, amount) } : f
    ));
  };

  const calculateHEFI = async () => {
    if (selectedFoods.length === 0) {
      setError('Please select at least one food item.');
      return;
    }

    // Check for valid amounts
    const invalidAmounts = selectedFoods.filter(f => f.amount_g <= 0);
    if (invalidAmounts.length > 0) {
      setError('All food amounts must be greater than 0.');
      return;
    }

    try {
      setIsLoading(true);
      setError('');
      
      const foods = selectedFoods.map(f => ({ food_id: f.FoodID, amount_g: f.amount_g }));
      const response = await HEFIApiService.calculateHEFI({ foods, user_type: userType });

      setResult(response);
      setLastCalcUserType(userType);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { message?: string; error?: string } } };
      setError(e?.response?.data?.error || e?.response?.data?.message || 'Failed to calculate HEFI score');
      console.warn('HEFI calculation error:', e?.response?.data || err);
    } finally {
      setIsLoading(false);
    }
  };

  const resetCalculation = () => {
    setSelectedFoods([]);
    setResult(null);
    setError('');
    setSearchQuery('');
    setSearchResults([]);
    setLastCalcUserType(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">HEFI Calculator</h1>
          <p className="text-lg text-gray-600">
            Build a meal or day from foods to estimate HEFI-2019 alignment. For scientifically valid use, HEFI-2019 is intended for complete
            daily dietary patterns (24-hour recalls), not single foods.
          </p>
          {/* Audience selector (AUDIENCE-CODE-1 2026-05-23) */}
          <div className="mt-4">
            <AudienceToggle
              userType={userType}
              onChange={setUserType}
              accent="green"
              staleResultHint={result !== null && lastCalcUserType !== null && userType !== lastCalcUserType}
            />
          </div>
          {cameFromRecall ? (
            <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex">
                <CheckCircleIcon className="w-5 h-5 text-green-700 mr-2 flex-shrink-0" />
                <div className="text-sm text-green-900">
                  <p className="font-semibold">Scoring a 24-h dietary recall — natural fit for HEFI-2019.</p>
                  <p className="mt-1">
                    HEFI-2019 was designed against 24-h recall data (Brassard et&nbsp;al. 2022b).
                    This score reflects one day&rsquo;s eating; for usual-intake claims,
                    score multiple recall days.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex">
                <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0" />
                <div className="text-sm text-yellow-800">
                  <p className="font-semibold">Important: HEFI-2019 is a pattern-level index</p>
                  <ul className="list-disc list-inside mt-1 space-y-1">
                    <li>Use HEFI with complete meals or 24-hour recalls.</li>
                    <li>Single-food scores are educational estimates and should be interpreted cautiously.</li>
                  </ul>
                  <p className="mt-2 text-xs">
                    Building your full day instead?{' '}
                    <a href="/recall-24h?then=hefi" className="underline font-medium hover:text-yellow-900">
                      Use the 24-h recall wizard
                    </a>.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* FOOD-LIST-PANEL (2026-05-26): cross-metric transferable food list. */}
        <div className="mb-6">
          <FoodListPanel
            currentTarget="hefi"
            onChange={list => {
              if (!list) {
                setSelectedFoods([]);
                return;
              }
              setSelectedFoods(list.ingredients.map(i => ({
                FoodID: i.food_id,
                FoodDescription: i.food_description,
                amount_g: i.mass_g,
              })));
            }}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input Panel — collapsible so the cross-page FoodListPanel above
              can be the primary surface once a list is loaded. */}
          <div className="lg:col-span-1">
            <CollapsibleSection
              title="Add Foods"
              icon={<Plus className="h-5 w-5 text-gray-700" />}
              badge={selectedFoods.length > 0 ? `${selectedFoods.length} selected` : undefined}
              persistKey="hefi-add-foods"
              defaultCollapsed
              className="bg-white rounded-lg shadow-sm"
              headerClassName="p-6"
              whenCollapsedHint={
                <p className="px-6 pb-4 text-xs text-gray-600">
                  Click above to search the CNF database and add or change foods.
                </p>
              }
            >
              <div className="p-6 pt-0 space-y-6">
              <div>
                <p className="text-sm text-gray-600">Search and select foods to include in the HEFI calculation.</p>
              </div>

              {/* Search Filters */}
              {filters && (
                <div className="space-y-4 border-b pb-4">
                  <h3 className="text-sm font-medium text-gray-700">Search Filters</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Food Category</label>
                      <select
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        aria-label="Food category filter"
                      >
                        <option value="">All categories</option>
                        {filters.categories.map((c) => (
                          <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Cooking Method</label>
                      <select
                        value={selectedMethod}
                        onChange={(e) => setSelectedMethod(e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        aria-label="Cooking method filter"
                      >
                        <option value="">All methods</option>
                        {filters.methods.map((m) => (
                          <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  {(selectedCategory || selectedMethod) && (
                    <button
                      onClick={() => { setSelectedCategory(''); setSelectedMethod(''); }}
                      className="text-xs text-purple-600 hover:text-purple-800"
                    >
                      Clear filters
                    </button>
                  )}
                </div>
              )}

              {/* Food Search */}
              <div className="space-y-3">
                {/* WAFCT-EXTEND (2026-05-24): scope the food database */}
                <SourceFilter source={sourceFilter} onChange={setSourceFilter} accent="purple" />
                <div className="relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                    }}
                    placeholder="Search for foods (e.g., salmon, bread, apple, fonio, baobab)..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  />
                </div>
                {searchIsLoading && searchQuery && (
                  <div className="text-sm text-gray-500">Searching...</div>
                )}
                {/* AI-MATCH-1: opt-in LLM ranker */}
                <AIEnhancedSearch
                  query={searchQuery}
                  userType={userType}
                  accent="purple"
                  source={sourceFilter}
                  onSelect={(food) => addFood({
                    FoodID: food.food_id,
                    FoodDescription: food.food_description,
                  })}
                />
                {/* AI-MATCH-1: homemade-dish workflow */}
                <button
                  type="button"
                  onClick={() => setRecipeModalOpen(true)}
                  className="inline-flex items-center gap-1.5 text-sm text-purple-700 hover:text-purple-900 hover:underline"
                >
                  🍳 Score a homemade dish (decompose into CNF ingredients)
                </button>
                {/* AI-MATCH-2 (2026-05-24): 24-h dietary recall — natural anchor for HEFI
                    since Brassard 2022b designed HEFI-2019 explicitly for 24-h recall data. */}
                <a
                  href="/recall-24h?then=hefi"
                  className="inline-flex items-center gap-1.5 text-sm text-purple-700 hover:text-purple-900 hover:underline"
                >
                  🍽️ Build a 24-h recall instead (six-occasion daily eating)
                </a>

                {searchResults.length > 0 && (
                  <div className="bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto">
                    {searchResults.map((food) => (
                      <button
                        key={food.FoodID}
                        onClick={() => addFood(food)}
                        className="w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                      >
                        <div className="font-medium text-gray-900">{food.FoodDescription}</div>
                        <div className="text-sm text-gray-500">ID: {food.FoodID}</div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Selected Foods */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-gray-700">Selected Foods ({selectedFoods.length})</h3>
                  {selectedFoods.length > 0 && (
                    <button
                      onClick={resetCalculation}
                      className="text-xs text-gray-500 hover:text-gray-700"
                    >
                      Clear all
                    </button>
                  )}
                </div>

                {selectedFoods.length === 0 ? (
                  <div className="text-center py-6 text-gray-500">
                    <InformationCircleIcon className="w-10 h-10 mx-auto mb-2 opacity-50" />
                    <p>No foods selected yet.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {selectedFoods.map((food) => (
                      <div key={food.FoodID} className="p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <div>
                            <div className="font-medium text-gray-900">{food.FoodDescription}</div>
                            <div className="text-sm text-gray-500">ID: {food.FoodID}</div>
                          </div>
                          <button
                            onClick={() => removeFood(food.FoodID)}
                            className="text-red-500 hover:text-red-700 p-1"
                            title={`Remove ${food.FoodDescription}`}
                            aria-label={`Remove ${food.FoodDescription}`}
                          >
                            <XMarkIcon className="w-5 h-5" />
                            <span className="sr-only">Remove {food.FoodDescription}</span>
                          </button>
                        </div>
                        <div className="flex items-center gap-2">
                          <label htmlFor={`amount-g-${food.FoodID}`} className="text-sm font-medium text-gray-600">Amount:</label>
                          <input
                            id={`amount-g-${food.FoodID}`}
                            type="number"
                            min="0.1"
                            step="0.1"
                            value={food.amount_g}
                            onChange={(e) => updateFoodAmount(food.FoodID, parseFloat(e.target.value) || 0.1)}
                            className="w-24 px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                            aria-label={`Amount in grams for ${food.FoodDescription}`}
                          />
                          <span className="text-sm text-gray-500">grams</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Error */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <div className="flex items-center">
                    <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mr-2" />
                    <div className="text-sm text-red-700">{error}</div>
                  </div>
                </div>
              )}
              </div>
            </CollapsibleSection>

            {/* Calculate button — outside the collapsible so the user can score
                without re-expanding the Add Foods panel after editing the list
                via the FoodListPanel above. */}
            <button
              type="button"
              onClick={calculateHEFI}
              disabled={isLoading || selectedFoods.length === 0}
              className="w-full mt-4 inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              <CalculatorIcon className="mr-2 w-5 h-5" />
              {isLoading ? 'Calculating...' : 'Calculate HEFI Score'}
            </button>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2 space-y-6">
            {result ? (
              <div className="space-y-6">
                {/* Audience-aware explanations (AUDIENCE-CODE-1) */}
                <ExplanationsPanel
                  explanations={(result.data as unknown as { explanations?: ExplanationsBlock })?.explanations}
                  userType={userType}
                  accent="text-purple-700"
                />
                {/* Math-leaking detailed breakdown: researcher + policy only.
                    Component scores, ratios, raw inputs (sodium mg, energy
                    kcal, etc.) expose internal calculation state. */}
                {userType !== 'individual' && (
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">HEFI Component Breakdown</h2>
                    <HEFIScoreDisplay result={result} />
                  </div>
                )}
                {/* FIX (#6): Calculate Another button moved out of the result-card
                    header to the bottom of the result panel, consistent across
                    audience modes — previously it sat inside the title row of
                    the researcher card which interrupted reading flow. */}
                <div className="text-center pt-2">
                  <button
                    type="button"
                    onClick={resetCalculation}
                    className="inline-flex items-center px-4 py-2 border border-purple-200 rounded-md text-purple-700 hover:bg-purple-50 hover:text-purple-800 font-medium text-sm transition-colors"
                  >
                    Calculate Another
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <InformationCircleIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Yet</h3>
                <p className="text-gray-600">
                  Add foods on the left and click &quot;Calculate HEFI Score&quot; to see your results here.
                </p>
              </div>
            )}

            {/* Algorithm Info */}
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-purple-900 mb-2 flex items-center">
                <CheckCircleIcon className="w-5 h-5 mr-2" />
                HEFI-2019 Algorithm Highlights
              </h3>
              <div className="text-sm text-purple-800 space-y-1">
                <p>• 10 components covering adequacy and moderation</p>
                <p>• Scoring based on dietary patterns aligned with Canada’s Food Guide</p>
                <p>• Total score out of 80 with component-level breakdown</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* AI-MATCH-1: recipe decomposer modal */}
      <RecipeDecomposerModal
        open={recipeModalOpen}
        onClose={() => setRecipeModalOpen(false)}
        userType={userType}
        accent="purple"
        initialSource={sourceFilter}
        onApply={(ingredients) => {
          const additions: SelectedFood[] = ingredients
            .filter(i => !selectedFoods.some(f => f.FoodID === i.food_id))
            .map(i => ({
              FoodID: i.food_id,
              FoodDescription: i.food_description,
              amount_g: i.mass_g,
            }));
          setSelectedFoods([...selectedFoods, ...additions]);
        }}
      />
    </div>
  );
}