'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  MagnifyingGlassIcon,
  AdjustmentsHorizontalIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  EyeIcon,
  ScaleIcon,
  XMarkIcon,
  InformationCircleIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { CNFApiService, SearchResult, FoodGroup, Food, EnhancedSearchOptions, FilterOptions } from '@/lib/api';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { saveActiveFoodList, ACTIVE_FOOD_LIST_SCHEMA_VERSION } from '@/lib/activeFoodList';
import { debounce } from 'lodash';
// AI-MATCH-1 (2026-05-23): opt-in LLM ranking layer alongside the basic
// fuzzy search. CNF Explorer is the first surface; others follow in Phase 6.
import { AIEnhancedSearch } from '@/components/shared/AIEnhancedSearch';
// WAFCT-EXTEND (2026-05-24): explorer surfaces both CNF + WAFCT now.
import { SourceFilter, type SourceChoice } from '@/components/shared/SourceFilter';
import { SourceBadge } from '@/components/shared/SourceBadge';
import { useCnfExplorer } from '@/components/cnf/CnfExplorerContext';
import { FoodDetailDrawer } from '@/components/cnf/FoodProfileContent';

interface SearchFilters {
  foodGroup: string;
  category: string;
  method: string;
  minRelevance: number;
  limit: number;
}

const INITIAL_FILTERS: SearchFilters = {
  foodGroup: '',
  category: '',
  method: '',
  minRelevance: 0,
  limit: 50,
};

export default function CNFSearchPage() {
  const { userType, resolveGroupName } = useCnfExplorer();
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>(INITIAL_FILTERS);
  const [results, setResults] = useState<SearchResult | null>(null);
  const [selectedFood, setSelectedFood] = useState<Food | null>(null);
  const [foodGroups, setFoodGroups] = useState<FoodGroup[]>([]);
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [selectedFoods, setSelectedFoods] = useState<number[]>([]);
  // Persistent metadata for selected foods so the "Send to deep-dive"
  // handoff still works after the user paginates past the page on which
  // they made the selection. Mirrors the FoodID -> {description, group}
  // shape consumers downstream need.
  const [selectedFoodMeta, setSelectedFoodMeta] = useState<
    Record<number, { food_description: string; food_group?: string }>
  >({});
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [offset, setOffset] = useState(0);
  const router = useRouter();
  // WAFCT-EXTEND (2026-05-24): food-database scope. Default 'both' so users
  // see CNF + WAFCT together unless they actively narrow.
  const [source, setSource] = useState<SourceChoice>('both');

  // Load food groups and filter options on mount
  useEffect(() => {
    loadFoodGroups();
    loadFilterOptions();
  }, []);

  // Debounced search function.
  // FDC-INGEST (2026-06-25): pass `source` as an explicit argument so the
  // debounced closure picks up the latest selection. Previously the
  // closure captured `source` once via `performSearch` and source-toggle
  // re-triggers used the stale initial value ('both'), so picking WAFCT
  // or FDC silently still searched everything.
  const debouncedSearch = useCallback(
    debounce((searchQuery: string, searchFilters: SearchFilters, searchOffset: number, searchSource: SourceChoice) => {
      if (searchQuery.trim()) {
        performSearch(searchQuery, searchFilters, searchOffset, searchSource);
      } else {
        setResults(null);
      }
    }, 500),
    []
  );

  // Trigger search when query, filters, or source scope change
  useEffect(() => {
    setOffset(0);
    debouncedSearch(query, filters, 0, source);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, filters, source, debouncedSearch]);

  const loadFoodGroups = async () => {
    try {
      const groups = await CNFApiService.getFoodGroups();
      setFoodGroups(groups);
    } catch (error) {
      console.error('Failed to load food groups:', error);
    }
  };

  const loadFilterOptions = async () => {
    try {
      const options = await CNFApiService.getFoodFilters();
      setFilterOptions(options);
    } catch (error) {
      console.error('Failed to load filter options:', error);
    }
  };

  const performSearch = async (
    searchQuery: string,
    searchFilters: SearchFilters,
    searchOffset: number,
    searchSource: SourceChoice = source,
  ) => {
    try {
      setLoading(true);

      // Use enhanced search if category/method filters are specified
      let searchResults: SearchResult;

      if (searchFilters.category || searchFilters.method) {
        const options: EnhancedSearchOptions = {
          query: searchQuery,
          limit: searchFilters.limit,
          offset: searchOffset,
          source: searchSource,  // WAFCT-EXTEND (2026-05-24); FDC-INGEST (2026-06-25)
        };

        if (searchFilters.category) {
          options.category = searchFilters.category;
        }

        if (searchFilters.method) {
          options.method = searchFilters.method;
        }

        searchResults = await CNFApiService.searchFoodsEnhanced(options);
      } else {
        searchResults = await CNFApiService.searchFoods(searchQuery, searchFilters.limit, searchOffset, searchSource);
      }
      
      // Apply client-side filtering for food groups and relevance
      let filteredResults = searchResults.results;
      
      if (searchFilters.foodGroup) {
        filteredResults = filteredResults.filter(food => 
          food.FoodGroupID === parseInt(searchFilters.foodGroup)
        );
      }
      
      if (searchFilters.minRelevance > 0) {
        filteredResults = filteredResults.filter(food => 
          food.relevance >= searchFilters.minRelevance
        );
      }

      setResults({
        ...searchResults,
        results: filteredResults,
        total: filteredResults.length
      });
    } catch (error) {
      console.error('Search failed:', error);
      toast.error('Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadMoreResults = () => {
    const newOffset = offset + filters.limit;
    setOffset(newOffset);
    debouncedSearch(query, filters, newOffset, source);
  };

  const loadFoodDetails = async (foodId: number) => {
    try {
      const food = await CNFApiService.getFoodDetails(foodId);
      setSelectedFood(food);
    } catch (error) {
      console.error('Failed to load food details:', error);
      toast.error('Failed to load food details');
    }
  };

  const toggleFoodSelection = (
    foodId: number,
    meta?: { food_description: string; food_group?: string },
  ) => {
    setSelectedFoods(prev =>
      prev.includes(foodId)
        ? prev.filter(id => id !== foodId)
        : [...prev, foodId]
    );
    if (meta) {
      setSelectedFoodMeta(prev => ({ ...prev, [foodId]: meta }));
    }
  };

  const clearSelections = () => {
    setSelectedFoods([]);
    setSelectedFoodMeta({});
  };

  // Pipe selected foods into the research deep-dive via the shared
  // activeFoodList handoff. Foods that the user selected but for which we
  // do not yet have a description (selected on a previous page that has
  // since been navigated away from) fall back to a synthetic placeholder;
  // the deep-dive page will still resolve the nutrient panel correctly
  // because aggregation is keyed by FoodID.
  const sendToDeepDive = () => {
    if (selectedFoods.length === 0) return;
    const ingredients = selectedFoods.map(food_id => {
      const meta = selectedFoodMeta[food_id];
      return {
        food_id,
        food_description: meta?.food_description || `CNF FoodID ${food_id}`,
        food_group: meta?.food_group,
        mass_g: 100,
      };
    });
    saveActiveFoodList({
      schema_version: ACTIVE_FOOD_LIST_SCHEMA_VERSION,
      captured_at: new Date().toISOString(),
      source: 'catalogue',
      ingredients,
    });
    router.push('/research/nutrient-analysis?from=cnf_search');
  };

  const getRelevanceColor = (relevance: number) => {
    if (relevance >= 0.8) return 'bg-green-100 text-green-800';
    if (relevance >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getRelevanceLabel = (relevance: number) => {
    if (relevance >= 0.8) return 'High';
    if (relevance >= 0.6) return 'Medium';
    return 'Low';
  };

  return (
    <div className="min-h-screen bg-gray-50 py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Advanced Food Search
          </h1>
          <p className="text-gray-600 mb-2">
            Search across <strong>two food-composition databases</strong>: Canada&rsquo;s CNF
            (5,691 foods, Health Canada) and FAO&rsquo;s WAFCT 2019 (1,028 West African foods).
            Use the source filter below to scope a search to one database, or leave on
            &ldquo;Both&rdquo; to see the combined catalog.
          </p>
          <div className="text-sm text-gray-500">
            <strong>Search Tips:</strong> Use filters like <code className="bg-gray-100 px-1 rounded">category:cheese</code>,{' '}
            <code className="bg-gray-100 px-1 rounded">method:cooked</code>, or{' '}
            <code className="bg-gray-100 px-1 rounded">type:chicken</code> in your search.
            Try West African staples: <code className="bg-gray-100 px-1 rounded">fonio</code>,{' '}
            <code className="bg-gray-100 px-1 rounded">baobab leaves</code>,{' '}
            <code className="bg-gray-100 px-1 rounded">dawadawa</code>.
          </div>
        </div>

        {/* Search Interface */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          {/* WAFCT-EXTEND (2026-05-24): scope picker — applies to BOTH the
              basic text search and the AI-enhanced ranker below. */}
          <div className="mb-3">
            <SourceFilter source={source} onChange={setSource} accent="blue" />
          </div>

          {/* Search Bar */}
          <div className="relative mb-4">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search for foods (e.g. 'chicken breast', 'fonio', 'baobab', 'category:cheese', 'method:raw')..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery('')}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                title="Clear search"
              >
                <XMarkIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              </button>
            )}
          </div>

          {/* AI-MATCH-1 (2026-05-23): opt-in AI ranker. Stays out of the way
              until the user clicks "Find with AI". Selecting a result loads
              the food details via the existing flow so downstream UX is
              unchanged. WAFCT-EXTEND wires `source` through so the LLM only
              ranks in-scope candidates. */}
          <div className="mb-4">
            <AIEnhancedSearch
              query={query}
              userType={userType}
              accent="blue"
              source={source}
              onSelect={(food) => {
                setQuery(food.food_description);
                loadFoodDetails(food.food_id);
              }}
            />
          </div>

          {/* Filter Toggle */}
          <div className="flex items-center justify-between">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center text-sm text-gray-600 hover:text-gray-900"
            >
              <AdjustmentsHorizontalIcon className="w-4 h-4 mr-2" />
              Advanced Filters
              {showFilters ? (
                <ChevronUpIcon className="w-4 h-4 ml-1" />
              ) : (
                <ChevronDownIcon className="w-4 h-4 ml-1" />
              )}
            </button>
            
            {selectedFoods.length > 0 && (
              <div className="flex items-center space-x-3">
                <span className="text-sm text-gray-600">
                  {selectedFoods.length} selected
                </span>
                <Link
                  href={`/cnf/compare?foods=${selectedFoods.join(',')}`}
                  className="btn-primary text-sm py-2 px-4"
                >
                  <ScaleIcon className="w-4 h-4 mr-2" />
                  Compare Selected
                </Link>
                <button
                  type="button"
                  onClick={sendToDeepDive}
                  className="inline-flex items-center text-sm py-2 px-4 rounded border border-emerald-300 text-emerald-800 bg-emerald-50 hover:bg-emerald-100"
                  title="Open the research deep-dive (nutrient panel, DRIs, FPED, NOVA, food-source attribution) on the selected foods"
                >
                  <SparklesIcon className="w-4 h-4 mr-2" />
                  Send to deep-dive
                </button>
                <button
                  type="button"
                  onClick={clearSelections}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Clear
                </button>
              </div>
            )}
          </div>

          {/* Advanced Filters */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Food Category
                  </label>
                  <select
                    value={filters.category}
                    onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
                    className="block w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    aria-label="Food Category"
                  >
                    <option value="">All Categories</option>
                    {filterOptions?.categories.map((category) => (
                      <option key={category} value={category}>
                        {category.charAt(0).toUpperCase() + category.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Preparation Method
                  </label>
                  <select
                    value={filters.method}
                    onChange={(e) => setFilters(prev => ({ ...prev, method: e.target.value }))}
                    className="block w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    aria-label="Preparation Method"
                  >
                    <option value="">All Methods</option>
                    {filterOptions?.methods.map((method) => (
                      <option key={method} value={method}>
                        {method.charAt(0).toUpperCase() + method.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Food Group
                  </label>
                  <select
                    value={filters.foodGroup}
                    onChange={(e) => setFilters(prev => ({ ...prev, foodGroup: e.target.value }))}
                    className="block w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    aria-label="Food Group"
                  >
                    <option value="">All Food Groups</option>
                    {foodGroups.map((group) => (
                      <option key={group.FoodGroupID} value={group.FoodGroupID}>
                        {group.FoodGroupName}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Minimum Relevance
                  </label>
                  <select
                    value={filters.minRelevance}
                    onChange={(e) => setFilters(prev => ({ ...prev, minRelevance: parseFloat(e.target.value) }))}
                    className="block w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    aria-label="Minimum Relevance"
                  >
                    <option value="0">Any Relevance</option>
                    <option value="0.6">Medium+ Relevance</option>
                    <option value="0.8">High Relevance</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Results Per Page
                  </label>
                  <select
                    value={filters.limit}
                    onChange={(e) => setFilters(prev => ({ ...prev, limit: parseInt(e.target.value) }))}
                    className="block w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    aria-label="Results Per Page"
                  >
                    <option value="25">25 results</option>
                    <option value="50">50 results</option>
                    <option value="100">100 results</option>
                  </select>
                </div>
              </div>
              
              {/* Active Filters Display */}
              {(filters.category || filters.method || filters.foodGroup) && (
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="text-sm text-gray-500">Active filters:</span>
                  {filters.category && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Category: {filters.category}
                      <button
                        type="button"
                        onClick={() => setFilters(prev => ({ ...prev, category: '' }))}
                        className="ml-1 text-blue-600 hover:text-blue-800"
                      >
                        ×
                      </button>
                    </span>
                  )}
                  {filters.method && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Method: {filters.method}
                      <button
                        type="button"
                        onClick={() => setFilters(prev => ({ ...prev, method: '' }))}
                        className="ml-1 text-green-600 hover:text-green-800"
                      >
                        ×
                      </button>
                    </span>
                  )}
                  {filters.foodGroup && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                      Group: {foodGroups.find(g => g.FoodGroupID.toString() === filters.foodGroup)?.FoodGroupName}
                      <button
                        type="button"
                        onClick={() => setFilters(prev => ({ ...prev, foodGroup: '' }))}
                        className="ml-1 text-purple-600 hover:text-purple-800"
                      >
                        ×
                      </button>
                    </span>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Search Results */}
        {loading && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
            <div className="inline-flex items-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
              <span className="ml-2 text-gray-600">Searching...</span>
            </div>
          </div>
        )}

        {results && !loading && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            {/* Results Header */}
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    Search Results
                  </h2>
                  <p className="text-sm text-gray-600">
                    Found {results.total} foods for &quot;{results.query}&quot;
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <InformationCircleIcon className="w-4 h-4 text-gray-400" />
                  <span className="text-xs text-gray-500">
                    Click foods to view details • Select multiple to compare
                  </span>
                </div>
              </div>
            </div>

            {/* Results List */}
            <div className="divide-y divide-gray-200">
              {results.results.map((food) => (
                <div
                  key={food.FoodID}
                  className={`px-6 py-4 hover:bg-gray-50 transition-colors ${
                    selectedFoods.includes(food.FoodID) ? 'bg-primary-50 border-l-4 border-primary-500' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={selectedFoods.includes(food.FoodID)}
                          onChange={() => toggleFoodSelection(food.FoodID, {
                            food_description: food.FoodDescription,
                            food_group: resolveGroupName(food.FoodGroupID),
                          })}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                          aria-label={`Select ${food.FoodDescription}`}
                        />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <Link
                              href={`/cnf/foods/${food.FoodID}`}
                              className="text-sm font-medium text-gray-900 hover:text-primary-700"
                            >
                              {food.FoodDescription}
                            </Link>
                            {/* WAFCT-EXTEND (2026-05-24): provenance badge.
                                Derives source from FoodID (≥700,000 = WAFCT)
                                so it works for the basic search response
                                which doesn't carry a `source` field per row. */}
                            <SourceBadge foodId={food.FoodID} userType={userType} />
                          </div>
                          <div className="flex items-center flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                            <span>Code: {food.FoodCode}</span>
                            <span>{resolveGroupName(food.FoodGroupID)}</span>
                            {userType === 'researcher' && (
                              <Link
                                href={`/cnf/groups?group=${food.FoodGroupID}`}
                                className="text-blue-600 hover:text-blue-800"
                              >
                                Browse group →
                              </Link>
                            )}
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRelevanceColor(food.relevance)}`}>
                              <SparklesIcon className="w-3 h-3 inline mr-1" />
                              {getRelevanceLabel(food.relevance)} ({(food.relevance * 100).toFixed(0)}%)
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => loadFoodDetails(food.FoodID)}
                        className="p-2 text-gray-400 hover:text-primary-600 transition-colors"
                        title="View Details"
                      >
                        <EyeIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Load More */}
            {results.has_more && (
              <div className="px-6 py-4 border-t border-gray-200 text-center">
                <button
                  onClick={loadMoreResults}
                  className="btn-outline"
                  disabled={loading}
                >
                  Load More Results
                </button>
              </div>
            )}

            {results.results.length === 0 && (
              <div className="px-6 py-12 text-center">
                <MagnifyingGlassIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No results found
                </h3>
                <p className="text-gray-600 mb-4">
                  Try adjusting your search query or filters
                </p>
              </div>
            )}
          </div>
        )}

        {selectedFood && (
          <FoodDetailDrawer
            food={selectedFood}
            userType={userType}
            groupLabel={resolveGroupName(selectedFood.FoodGroupID, selectedFood.FoodGroupName)}
            onClose={() => setSelectedFood(null)}
            onAddToCompare={() => {
              if (!selectedFoods.includes(selectedFood.FoodID)) {
                setSelectedFoods(prev => [...prev, selectedFood.FoodID]);
              }
              setSelectedFoodMeta(prev => ({
                ...prev,
                [selectedFood.FoodID]: {
                  food_description: selectedFood.FoodDescription,
                  food_group: resolveGroupName(selectedFood.FoodGroupID, selectedFood.FoodGroupName),
                },
              }));
              toast.success('Added to selection');
            }}
          />
        )}
      </div>
    </div>
  );
} 