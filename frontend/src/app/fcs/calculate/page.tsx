'use client';

import React, { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  TrashIcon, 
  MagnifyingGlassIcon,
  BeakerIcon,
  ChartBarIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { FCSApiService, CNFApiService, type FCSResult, type SearchResult, type FilterOptions } from '@/lib/api';
import { AudienceToggle, type UserType, type ExplanationsBlock } from '@/components/shared/AudienceToggle';
import { ExplanationsPanel } from '@/components/shared/ExplanationsPanel';
import { AIEnhancedSearch } from '@/components/shared/AIEnhancedSearch';
import { RecipeDecomposerModal } from '@/components/shared/RecipeDecomposerModal';
import { SourceFilter, type SourceChoice } from '@/components/shared/SourceFilter';
import { useRecall24hReceiver } from '@/components/shared/useRecall24hReceiver';
import { FoodListPanel } from '@/components/shared/FoodListPanel';
import { CollapsibleSection } from '@/components/shared/CollapsibleSection';

interface FoodItem {
  id: string;
  food_id: number;
  food_name: string;
  serving_size: number;
}

interface SearchState {
  query: string;
  results: SearchResult['results'];
  isLoading: boolean;
  showResults: boolean;
}

export default function FCSCalculate() {
  const [foods, setFoods] = useState<FoodItem[]>([
    { id: '1', food_id: 0, food_name: '', serving_size: 100 }
  ]);
  const [search, setSearch] = useState<SearchState>({
    query: '',
    results: [],
    isLoading: false,
    showResults: false
  });
  const [activeSearch, setActiveSearch] = useState<string>('');
  const [result, setResult] = useState<FCSResult | null>(null);
  const [userType, setUserType] = useState<UserType>('individual');
  // AUDIENCE-CODE-1 follow-up: track which userType the current `result` was
  // computed under so we can flag stale explanations when the user toggles.
  const [lastCalcUserType, setLastCalcUserType] = useState<UserType | null>(null);
  const [recipeModalOpen, setRecipeModalOpen] = useState(false);
  const [isCalculating, setIsCalculating] = useState(false);
  const [filters, setFilters] = useState<FilterOptions | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedMethod, setSelectedMethod] = useState<string>('');
  // WAFCT-EXTEND (2026-05-24): food-database scope.
  const [sourceFilter, setSourceFilter] = useState<SourceChoice>('both');

  // Load filters on component mount
  useEffect(() => {
    const loadFilters = async () => {
      try {
        const filterOptions = await CNFApiService.getFoodFilters();
        setFilters(filterOptions);
      } catch (error) {
        console.error('Failed to load filters:', error);
      }
    };
    loadFilters();
  }, []);

  // AI-MATCH-2 (2026-05-24): pick up an aggregated 24-h recall payload
  // handed off from /recall-24h. FCS scores at the food level (no per-food
  // mass in the request shape); diet-level scoring uses the energy-weighted
  // mean across daily intake — the food list is the right input.
  useRecall24hReceiver({
    target: 'fcs',
    onIngredients: (ingredients, meta) => {
      setUserType(meta.user_type);
      setFoods(ingredients.map((i, idx) => ({
        id: String(idx + 1),
        food_id: i.food_id,
        food_name: i.food_description,
        serving_size: i.mass_g ?? 100,
      })));
    },
  });

  // Debounced search
  useEffect(() => {
    if (search.query.length < 2) {
      setSearch(prev => ({ ...prev, results: [], showResults: false }));
      return;
    }

    const timeoutId = setTimeout(async () => {
      setSearch(prev => ({ ...prev, isLoading: true }));
      try {
        // Try enhanced search first, fallback to regular search
        let searchResult;
        try {
          searchResult = await CNFApiService.searchFoodsEnhanced({
            query: search.query,
            limit: 50,
            category: selectedCategory || undefined,
            method: selectedMethod || undefined,
            source: sourceFilter,
          });
        } catch (enhancedError) {
          console.log('Enhanced search failed, falling back to regular search:', enhancedError);
          try {
            searchResult = await CNFApiService.searchFoods(search.query, 50, 0, sourceFilter);
          } catch (regularError) {
            console.error('Both search methods failed:', { enhancedError, regularError });
            throw regularError;
          }
        }
        setSearch(prev => ({ 
          ...prev, 
          results: searchResult.results, 
          isLoading: false, 
          showResults: true 
        }));
      } catch (error) {
        console.error('Search error:', error);
        setSearch(prev => ({ ...prev, isLoading: false, showResults: false }));
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [search.query, selectedCategory, selectedMethod, sourceFilter]);

  const addFood = () => {
    const newId = (foods.length + 1).toString();
    setFoods([...foods, { id: newId, food_id: 0, food_name: '', serving_size: 100 }]);
  };

  const removeFood = (id: string) => {
    if (foods.length > 1) {
      setFoods(foods.filter(food => food.id !== id));
    }
  };

  const updateFood = (id: string, updates: Partial<FoodItem>) => {
    setFoods(foods.map(food => 
      food.id === id ? { ...food, ...updates } : food
    ));
  };

  const selectFood = (foodId: string, selectedFood: SearchResult['results'][0]) => {
    updateFood(foodId, {
      food_id: selectedFood.FoodID,
      food_name: selectedFood.FoodDescription
    });
    setSearch(prev => ({ ...prev, query: '', showResults: false }));
    setActiveSearch('');
  };

  const handleSearch = (foodId: string, query: string) => {
    setActiveSearch(foodId);
    setSearch(prev => ({ ...prev, query }));
  };

  const calculateFCS = async () => {
    const validFoods = foods.filter(food => food.food_id > 0);
    
    if (validFoods.length === 0) {
      alert('Please select at least one food.');
      return;
    }

    setIsCalculating(true);
    try {
      const fcsResult = await FCSApiService.calculateFCS({
        food_ids: validFoods.map(food => food.food_id),
        food_names: validFoods.map(food => food.food_name),
        serving_sizes: validFoods.map(food => food.serving_size),
        user_type: userType
      });
      
      console.log('FCS API Response:', fcsResult);
      console.log('FCS Result Data:', fcsResult.data);
      console.log('Setting result to:', fcsResult.data);
      // Extract the actual FCS result data
      const actualResult = (fcsResult.data as { data?: FCSResult }).data || fcsResult.data;
      console.log('Actual FCS result:', actualResult);
      setResult(actualResult);
      setLastCalcUserType(userType);
    } catch (error) {
      console.error('FCS calculation error:', error);
      alert('Failed to calculate FCS. Please try again.');
    } finally {
      setIsCalculating(false);
    }
  };

  const getFCSColor = (fcs: number) => {
    if (fcs >= 70) return 'text-green-600';
    if (fcs >= 31) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getFCSLevel = (fcs: number) => {
    if (fcs >= 70) return 'Encourage';
    if (fcs >= 31) return 'Moderation';
    return 'Minimize';
  };

  const getFCSDescription = (fcs: number) => {
    if (fcs >= 70) return 'Excellent nutritional quality - encourage regular consumption';
    if (fcs >= 31) return 'Moderate nutritional quality - consume in moderation';
    return 'Lower nutritional quality - minimize consumption';
  };

  const getNOVAColor = (nova: string) => {
    if (!nova) return 'bg-gray-100 text-gray-800';
    switch (nova.toLowerCase()) {
      case 'minimally_processed': return 'bg-green-100 text-green-800';
      case 'processed_culinary_ingredients': return 'bg-yellow-100 text-yellow-800';
      case 'processed_foods': return 'bg-orange-100 text-orange-800';
      case 'ultra_processed_foods': return 'bg-red-100 text-red-800';
      case 'mixed_processing_levels': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatNOVAName = (nova: string) => {
    if (!nova) return 'Unknown';
    if (nova.toLowerCase() === 'mixed_processing_levels') return 'Mixed Processing Levels';
    return nova.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatProcessingLevel = (nova: string, lvl: number | null) => {
    const name = formatNOVAName(nova);
    if (userType === 'individual') {
      if (lvl !== null) return `Level ${lvl} · ${name}`;
      return name;
    }
    if (lvl !== null) return `NOVA ${lvl} — ${name}`;
    return name;
  };

  // FIX (FCS audit #4): the single-food NOVA badge previously rendered just
  // the category name (e.g. "Ultra Processed Foods") with no NOVA level
  // number, whereas the mixed-dish badge correctly shows "NOVA 4". Map the
  // category string back to its Monteiro level for consistent labelling.
  // Returns null for unknown / mixed-processing categories where a single
  // level number is not meaningful.
  const novaLevelOf = (nova: string): number | null => {
    switch ((nova || '').toUpperCase()) {
      case 'MINIMALLY_PROCESSED': return 1;
      case 'PROCESSED_CULINARY_INGREDIENTS': return 2;
      case 'PROCESSED_FOODS': return 3;
      case 'ULTRA_PROCESSED_FOODS': return 4;
      default: return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Food Compass Calculator</h1>
          <p className="text-lg text-gray-600">
            Score how closely a food, a meal, or a whole day of eating resembles the
            patterns linked to longer, healthier lives. Every food sits on the same 1 to 100 scale.
          </p>
          {/* Audience selector (AUDIENCE-CODE-1 2026-05-23) */}
          <div className="mt-4">
            <AudienceToggle
              userType={userType}
              onChange={setUserType}
              accent="blue"
              staleResultHint={result !== null && lastCalcUserType !== null && userType !== lastCalcUserType}
            />
          </div>
          {/* Researcher / policy banner — kept brief and free of internal codes. */}
          {userType !== 'individual' && (
            <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center">
                <SparklesIcon className="w-5 h-5 text-blue-600 mr-2" />
                <span className="text-sm font-medium text-blue-900">Algorithm</span>
              </div>
              <p className="text-sm text-blue-800 mt-1">
                Implements the Food Compass nutrient profiling system (Mozaffarian 2021,
                <em> Nature Food</em> 2:809-818). Nine domains: nutrient ratios, vitamins, minerals,
                food ingredients, additives, processing, specific lipids, fiber &amp; protein,
                and phytochemicals. Raw domain scores are rescaled to a single 1 to 100 output
                per the published mapping (SI Table S3).
              </p>
            </div>
          )}
        </div>

        {/* FOOD-LIST-PANEL (2026-05-26): cross-metric transferable food list. */}
        <div className="mb-6">
          <FoodListPanel
            currentTarget="fcs"
            onChange={list => {
              if (!list) {
                setFoods([]);
                return;
              }
              setFoods(list.ingredients.map((i, idx) => ({
                id: String(idx + 1),
                food_id: i.food_id,
                food_name: i.food_description,
                serving_size: i.mass_g ?? 100,
              })));
            }}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input Panel — collapsible so the FoodListPanel above can dominate
              once a list is loaded. */}
          <div className="lg:col-span-1">
            <CollapsibleSection
              title="Add Foods"
              icon={<PlusIcon className="h-5 w-5 text-gray-700" />}
              badge={foods.length > 0 ? `${foods.length} selected` : undefined}
              persistKey="fcs-add-foods"
              defaultCollapsed
              className="bg-white rounded-lg shadow-sm"
              headerClassName="p-6"
              whenCollapsedHint={
                <p className="px-6 pb-4 text-xs text-gray-600">
                  Click above to search and add foods to your list.
                </p>
              }
            >
              <div className="p-6 pt-0">
              
              {/* Search Filters */}
              {filters && (
                <div className="mb-6 space-y-4 border-b pb-4">
                  <h3 className="text-sm font-medium text-gray-700">Search Filters</h3>
                  
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Food Category
                    </label>
                    <select
                      value={selectedCategory}
                      onChange={(e) => setSelectedCategory(e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      aria-label="Food category filter"
                    >
                      <option value="">All categories</option>
                      {filters.categories.map((category) => (
                        <option key={category} value={category}>
                          {category.charAt(0).toUpperCase() + category.slice(1)}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Cooking Method
                    </label>
                    <select
                      value={selectedMethod}
                      onChange={(e) => setSelectedMethod(e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      aria-label="Cooking method filter"
                    >
                      <option value="">All methods</option>
                      {filters.methods.map((method) => (
                        <option key={method} value={method}>
                          {method.charAt(0).toUpperCase() + method.slice(1)}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  {(selectedCategory || selectedMethod) && (
                    <button
                      onClick={() => {
                        setSelectedCategory('');
                        setSelectedMethod('');
                      }}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      Clear filters
                    </button>
                  )}
                </div>
              )}

              {/* Food Inputs */}
              <div className="space-y-4">
                {foods.map((food) => (
                  <div key={food.id} className="border border-gray-200 rounded-md p-4">
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="text-sm font-medium text-gray-700">Food {food.id}</h3>
                      {foods.length > 1 && (
                        <button
                          onClick={() => removeFood(food.id)}
                          className="text-red-500 hover:text-red-700"
                          aria-label={`Remove food ${food.id}`}
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                    
                    {/* Food Search */}
                    <div className="relative">
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Search Food
                      </label>
                      <div className="relative">
                        <input
                          type="text"
                          value={activeSearch === food.id ? search.query : food.food_name}
                          onChange={(e) => handleSearch(food.id, e.target.value)}
                          placeholder="Search for a food..."
                          className="w-full border border-gray-300 rounded-md pl-10 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                        <MagnifyingGlassIcon className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                      </div>

                      {/* AI-MATCH-1: opt-in LLM ranker for THIS slot */}
                      {activeSearch === food.id && search.query.trim() && (
                        <div className="mt-2 space-y-2">
                          {/* WAFCT-EXTEND (2026-05-24): food-database scope */}
                          <SourceFilter source={sourceFilter} onChange={setSourceFilter} accent="blue" />
                          <AIEnhancedSearch
                            query={search.query}
                            userType={userType}
                            accent="blue"
                            source={sourceFilter}
                            onSelect={(picked) => selectFood(food.id, {
                              FoodID: picked.food_id,
                              FoodDescription: picked.food_description,
                              FoodCode: undefined as unknown as string,
                            } as SearchResult['results'][0])}
                          />
                        </div>
                      )}

                      {/* Search Results */}
                      {activeSearch === food.id && search.showResults && (
                        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-48 overflow-y-auto">
                          {search.isLoading ? (
                            <div className="p-3 text-center text-sm text-gray-500">
                              Searching...
                            </div>
                          ) : search.results.length > 0 ? (
                            search.results.map((item) => (
                              <button
                                key={item.FoodID}
                                onClick={() => selectFood(food.id, item)}
                                className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                              >
                                <div className="font-medium text-gray-900 truncate">
                                  {item.FoodDescription}
                                </div>
                                <div className="text-xs text-gray-500">
                                  Code: {item.FoodCode}
                                </div>
                              </button>
                            ))
                          ) : (
                            <div className="p-3 text-center text-sm text-gray-500">
                              No foods found
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {food.food_id > 0 && (
                      <div className="mt-3">
                        <label
                          htmlFor={`fcs-serving-${food.id}`}
                          className="block text-xs font-medium text-gray-700 mb-1"
                        >
                          Amount (grams)
                        </label>
                        <input
                          id={`fcs-serving-${food.id}`}
                          type="number"
                          min={0.1}
                          step={1}
                          value={food.serving_size}
                          onChange={e =>
                            updateFood(food.id, {
                              serving_size: Math.max(0.1, Number(e.target.value) || 100),
                            })
                          }
                          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Add Food Button */}
              <button
                onClick={addFood}
                className="w-full mt-4 flex items-center justify-center px-4 py-2 border border-dashed border-gray-300 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 hover:border-gray-400"
              >
                <PlusIcon className="w-4 h-4 mr-2" />
                Add Another Food
              </button>

              {/* AI-MATCH-1: homemade-dish workflow */}
              <button
                type="button"
                onClick={() => setRecipeModalOpen(true)}
                className="w-full mt-2 flex items-center justify-center gap-1.5 text-sm text-blue-700 hover:text-blue-900 hover:underline"
              >
                🍳 Break down a homemade dish
              </button>
              {/* AI-MATCH-2 (2026-05-24): 24-h dietary recall — the diet-level
                  Food Compass score (O'Hearn 2022, Nat Comm 13:7066) is the
                  energy-weighted mean FCS across daily intake, so a full day
                  is the right unit for diet-level scoring. */}
              <a
                href="/recall-24h?then=fcs"
                className="w-full mt-1 flex items-center justify-center gap-1.5 text-sm text-blue-700 hover:text-blue-900 hover:underline"
              >
                🍽️ Log a full food diary day instead
              </a>

              </div>
            </CollapsibleSection>

            {/* Calculate button — outside the collapsible so the user can score
                without re-expanding the Add Foods panel after editing the list
                via the FoodListPanel above. */}
            <button
              type="button"
              onClick={calculateFCS}
              disabled={isCalculating || foods.every(food => food.food_id === 0)}
              className="w-full mt-4 bg-blue-600 text-white px-4 py-3 rounded-md font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {isCalculating ? (
                <>
                  <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
                  Calculating...
                </>
              ) : (
                <>
                  <BeakerIcon className="w-4 h-4 mr-2" />
                  Calculate FCS
                </>
              )}
            </button>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {result ? (
              <div className="space-y-6">
                {/* Audience-aware explanations (AUDIENCE-CODE-1) */}
                <ExplanationsPanel
                  explanations={(result as unknown as { explanations?: ExplanationsBlock })?.explanations}
                  userType={userType}
                  accent="text-blue-700"
                />

                {/* Main FCS Result — headline always visible */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">
                    Food Compass Score Results
                  </h2>

                  {/* FCS Score Display */}
                  <div className="text-center mb-8">
                    <div className="mb-4">
                      <span className={`text-6xl font-bold ${getFCSColor(result.fcs)}`}>
                        {result.fcs || 'N/A'}
                      </span>
                      <span className="text-2xl text-gray-500 ml-2">/100</span>
                    </div>
                    <div className={`text-xl font-semibold mb-2 ${getFCSColor(result.fcs)}`}>
                      {getFCSLevel(result.fcs)}
                    </div>
                    <p className="text-gray-600 max-w-2xl mx-auto">
                      {getFCSDescription(result.fcs)}
                    </p>
                  </div>

                  {/* Score Details — Original Algorithm Score is researcher/policy only
                      (pre-rescaling raw value confuses individuals). */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {userType !== 'individual' && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="text-sm font-medium text-gray-700 mb-2">Original Algorithm Score</h3>
                      <div className="text-2xl font-bold text-gray-900">{result.original_score !== undefined ? result.original_score.toFixed(2) : 'N/A'}</div>
                      <p className="text-xs text-gray-500 mt-1">
                        Raw score from 9-domain calculation before transformation to 1-100 scale
                      </p>
                    </div>
                    )}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="text-sm font-medium text-gray-700 mb-2">
                        {userType === 'individual' ? 'Processing level' : 'NOVA Category'}
                      </h3>
                      <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getNOVAColor(result.nova_category)}`}>
                        {formatProcessingLevel(result.nova_category, novaLevelOf(result.nova_category))}
                      </span>
                      <p className="text-xs text-gray-500 mt-1">
                        {result.nova_category === 'MIXED_PROCESSING_LEVELS'
                          ? 'Energy-weighted processing level for combined foods'
                          : userType === 'individual'
                            ? 'How much the food was processed before you eat it'
                            : 'Food processing classification level (Monteiro 2019)'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Processing Details for Mixed Dishes */}
                {result.processing_details && result.processing_details.is_mixed_dish && (
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Mixed Dish Processing Analysis
                    </h3>
                    
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                      <h4 className="text-sm font-medium text-blue-900 mb-2">Energy-Weighted Processing</h4>
                      <p className="text-sm text-blue-800">
                        This mixed dish contains foods with different processing levels. The final processing score 
                        is calculated using energy-weighted averaging based on each food&apos;s caloric contribution.
                      </p>
                    </div>

                    <div className="space-y-4">
                      <h4 className="text-md font-medium text-gray-900">Individual Food Components</h4>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {result.processing_details.individual_foods.map((food) => (
                          <div key={food.food_id} className="border border-gray-200 rounded-lg p-4">
                            <div className="flex justify-between items-start mb-2">
                              <h5 className="font-medium text-gray-900 text-sm leading-tight">
                                {food.food_name}
                              </h5>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${getNOVAColor(food.nova_category)}`}>
                                {userType === 'individual' ? `Level ${food.nova_level}` : `NOVA ${food.nova_level}`}
                              </span>
                            </div>
                            
                            <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                              <div>
                                <span className="font-medium">Energy:</span> {food.energy_kcal} kcal
                              </div>
                              <div>
                                <span className="font-medium">Weight:</span> {(food.energy_weight * 100).toFixed(1)}%
                              </div>
                            </div>
                            
                            <div className="mt-2">
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div 
                                  className="bg-blue-600 h-2 rounded-full" 
                                  style={{ width: `${food.energy_weight * 100}%` } as React.CSSProperties}
                                ></div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="bg-gray-50 rounded-lg p-4">
                        <h5 className="text-sm font-medium text-gray-700 mb-2">Processing Score Calculation</h5>
                        <div className="text-sm text-gray-600 space-y-1">
                          {result.processing_details.individual_foods.map((food) => (
                            <div key={food.food_id} className="flex justify-between">
                              <span>
                                {userType === 'individual'
                                  ? `Level ${food.nova_level} × ${(food.energy_weight * 100).toFixed(1)}%`
                                  : `NOVA ${food.nova_level} × ${(food.energy_weight * 100).toFixed(1)}%`}
                              </span>
                              <span className="font-mono">
                                {food.nova_level} × {food.energy_weight.toFixed(3)}
                              </span>
                            </div>
                          ))}
                          <hr className="my-2" />
                          <div className="flex justify-between font-medium">
                            <span>Final Processing Penalty:</span>
                            <span className="font-mono">
                              Mixed Processing Score
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Researcher / policy algorithm card. The diet-level mortality
                    finding is gated to non-individual modes because it does not
                    apply to a single food. */}
                {userType !== 'individual' && (
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Food Compass &mdash; algorithm details
                    </h3>

                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                      <h4 className="text-sm font-medium text-blue-900 mb-2 flex items-center">
                        <CheckCircleIcon className="w-4 h-4 mr-2" />
                        Scientific validation
                      </h4>
                      <div className="text-sm text-blue-800 space-y-1">
                        <p>• <strong>Nine-domain structure:</strong> Mozaffarian 2021, <em>Nature Food</em> 2:809-818.</p>
                        <p>• <strong>Single 1 to 100 scale:</strong> raw domain sum rescaled per Mozaffarian 2021 SI Table S3 footnote * (truncate raw at [-10.7, 26.1]; FCS = 100 - ((26.1 - raw) / 36.8) &times; 99).</p>
                        <p>• <strong>Population validation:</strong> 47,999 U.S. adults (NHANES 1999-2018).</p>
                        <p>• <strong>Diet-level outcome link:</strong> energy-weighted mean across daily intake, per 1 SD (10.9 pts) &rarr; HR 0.92 (0.88-0.95) all-cause mortality (O&apos;Hearn 2022, <em>Nature Communications</em> 13:7066). NOT applicable to single-food rankings.</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center">
                        <div className="bg-green-100 rounded-lg p-4 mb-2">
                          <BeakerIcon className="w-8 h-8 text-green-600 mx-auto" />
                        </div>
                        <h4 className="text-sm font-medium text-gray-900">Per-100-kcal Density</h4>
                        <p className="text-xs text-gray-600 mt-1">
                          Energy-normalized so foods are compared on nutrient density, not portion size
                        </p>
                      </div>
                      <div className="text-center">
                        <div className="bg-blue-100 rounded-lg p-4 mb-2">
                          <ChartBarIcon className="w-8 h-8 text-blue-600 mx-auto" />
                        </div>
                        <h4 className="text-sm font-medium text-gray-900">Domain Weighting</h4>
                        <p className="text-xs text-gray-600 mt-1">
                          5 domains full weight; Specific Lipids, Fiber &amp; Protein, Phytochemicals at half weight
                        </p>
                      </div>
                      <div className="text-center">
                        <div className="bg-purple-100 rounded-lg p-4 mb-2">
                          <SparklesIcon className="w-8 h-8 text-purple-600 mx-auto" />
                        </div>
                        <h4 className="text-sm font-medium text-gray-900">Cross-Group Coverage</h4>
                        <p className="text-xs text-gray-600 mt-1">
                          Evaluates all food types uniformly (≠ category-specific schemes like HSR)
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <BeakerIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Yet</h3>
                <p className="text-gray-600">
                  Add foods and click &quot;Calculate FCS&quot; to see comprehensive nutritional analysis.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* AI-MATCH-1: recipe decomposer modal */}
      <RecipeDecomposerModal
        open={recipeModalOpen}
        onClose={() => setRecipeModalOpen(false)}
        userType={userType}
        accent="blue"
        initialSource={sourceFilter}
        onApply={(ingredients) => {
          // FCS uses the same slot pattern as HSR. Replace the empty
          // starter slot if present, else append.
          const nextId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
          const seed = (foods.length === 1 && foods[0].food_id === 0)
            ? []
            : [...foods];
          const additions = ingredients
            .filter(i => !seed.some(f => f.food_id === i.food_id))
            .map(i => ({
              id: nextId(),
              food_id: i.food_id,
              food_name: i.food_description,
              serving_size: i.mass_g ?? 100,
            }));
          setFoods(seed.length === 0 ? additions : [...seed, ...additions]);
        }}
      />
    </div>
  );
}