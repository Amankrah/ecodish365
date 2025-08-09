'use client';

import React, { useEffect, useState } from 'react';
import { 
  ChartBarIcon,
  XMarkIcon,
  InformationCircleIcon,
  TrophyIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { HEFIApiService, CNFApiService, type HEFIComparison, type FilterOptions, type SearchResult as CNFSearchResult, type HEFIInterpretation } from '../../../lib/api';

type SelectedFood = { FoodID: number; FoodDescription: string; FoodCode?: string };

const HEFIComparisonDisplay = ({ result }: { result: HEFIComparison }) => {
  const { data } = result;
  const { foods, comparison_insights } = data;

  return (
    <div className="space-y-8">
      {/* Comparison Summary */}
      <div className="card">
        <h3 className="text-xl font-bold text-gray-900 mb-6">Comparison Summary</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {comparison_insights.highest_score?.toFixed(1) || 'N/A'}
            </div>
            <div className="text-sm text-gray-600">Highest Score</div>
          </div>
          
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {comparison_insights.average_score?.toFixed(1) || 'N/A'}
            </div>
            <div className="text-sm text-gray-600">Average Score</div>
          </div>
          
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {comparison_insights.score_range?.toFixed(1) || 'N/A'}
            </div>
            <div className="text-sm text-gray-600">Score Range</div>
          </div>
        </div>

        {comparison_insights.best_performing && (
          <div className="flex items-center justify-center bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <TrophyIcon className="w-6 h-6 text-yellow-600 mr-3" />
            <div>
              <div className="font-semibold text-yellow-900">Best Performing Food</div>
              <div className="text-yellow-700">{comparison_insights.best_performing}</div>
            </div>
          </div>
        )}
      </div>

      {/* Detailed Comparison */}
      <div className="card">
        <h3 className="text-xl font-bold text-gray-900 mb-6">Detailed Results</h3>
        
        <div className="space-y-6">
          {foods.map((food, index) => {
            const interpretation: HEFIInterpretation | undefined = food.hefi_interpretation;
            const getScoreColor = () => {
              const color = interpretation?.ui_color;
              if (color === 'emerald') return 'text-emerald-700 bg-emerald-50 border-emerald-200';
              if (color === 'green') return 'text-green-700 bg-green-50 border-green-200';
              if (color === 'yellow') return 'text-yellow-700 bg-yellow-50 border-yellow-200';
              if (color === 'red') return 'text-red-700 bg-red-50 border-red-200';
              return 'text-gray-700 bg-gray-50 border-gray-200';
            };

            return (
              <div key={index} className="border border-gray-200 rounded-lg p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h4 className="text-lg font-semibold text-gray-900 mb-1">
                      {food.food_name}
                    </h4>
                    <div className="text-sm text-gray-500">
                      Food IDs: {food.food_ids.join(', ')}
                    </div>
                  </div>
                  
                  <div className={`px-4 py-2 rounded-lg border text-right ${getScoreColor()}`}>
                    <div className="text-2xl font-bold">
                      {food.total_score.toFixed(1)}
                    </div>
                    <div className="text-sm">
                      {food.percentage.toFixed(1)}%
                    </div>
                    {interpretation && (
                      <div className="text-xs font-semibold mt-1">{interpretation.category}</div>
                    )}
                  </div>
                </div>

                {food.error ? (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center text-red-700">
                      <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
                      Error: {food.error}
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    {Object.entries(food.components).slice(0, 10).map(([key, component]) => {
                      const percentage = (component.score / component.max_points) * 100;
                      return (
                        <div key={key} className="text-center">
                          <div className="text-sm font-medium text-gray-900 mb-1">
                            {component.name.replace('C', 'C')}
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2 mb-1">
                            <div 
                              className="bg-purple-600 h-2 rounded-full"
                              style={{ width: `${Math.min(percentage, 100)}%` }}
                            />
                          </div>
                          <div className="text-xs text-gray-600">
                            {component.score.toFixed(1)}/{component.max_points}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Component Analysis */}
      {comparison_insights.component_analysis && (
        <div className="card">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Component Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(comparison_insights.component_analysis).map(([key, analysis]) => (
              <div key={key} className="bg-gray-50 rounded-lg p-4">
                <div className="font-medium text-gray-900 mb-2">
                  {analysis.component_name}
                </div>
                <div className="space-y-1 text-sm text-gray-600">
                  <div>Max: {analysis.max_score.toFixed(1)}</div>
                  <div>Min: {analysis.min_score.toFixed(1)}</div>
                  <div>Variation: {analysis.variation.toFixed(1)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default function HEFIComparePage() {
  const [selectedFoods, setSelectedFoods] = useState<SelectedFood[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<CNFSearchResult['results']>([]);
  const [searchIsLoading, setSearchIsLoading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<HEFIComparison | null>(null);
  const [error, setError] = useState<string>('');
  const [filters, setFilters] = useState<FilterOptions | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedMethod, setSelectedMethod] = useState<string>('');
  const [showResults, setShowResults] = useState<boolean>(false);

  // Load filters on mount
  useEffect(() => {
    const loadFilters = async () => {
      try {
        const filterOptions = await CNFApiService.getFoodFilters();
        setFilters(filterOptions);
      } catch (e) {
        console.warn('Failed to load CNF filters', e);
      }
    };
    loadFilters();
  }, []);

  // Debounced search with filters (enhanced -> fallback)
  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setSearchResults([]);
      setShowResults(false);
      return;
    }

    const timeoutId = setTimeout(async () => {
      setSearchIsLoading(true);
      try {
        let searchResult;
        try {
          searchResult = await CNFApiService.searchFoodsEnhanced({
            query: searchQuery,
            limit: 50,
            category: selectedCategory || undefined,
            method: selectedMethod || undefined,
          });
        } catch {
          // Fallback to basic search
          searchResult = await CNFApiService.searchFoods(searchQuery, 50);
        }
        setSearchResults(searchResult.results || []);
        setShowResults(true);
      } catch (err) {
        console.error('Search error:', err);
        setSearchResults([]);
        setShowResults(false);
      } finally {
        setSearchIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, selectedCategory, selectedMethod]);

  const addFood = (food: SelectedFood) => {
    setSelectedFoods((prev) => {
      if (prev.some((f) => f.FoodID === food.FoodID)) return prev;
      return [...prev, food];
    });
    setSearchQuery('');
    setSearchResults([]);
    setShowResults(false);
  };

  const removeFood = (foodId: number) => {
    setSelectedFoods((prev) => prev.filter((f) => f.FoodID !== foodId));
  };

  const compareHEFI = async () => {
    const validFoods = selectedFoods;
    if (validFoods.length < 2) {
      setError('Please select at least 2 foods to compare.');
      return;
    }

    try {
      setIsLoading(true);
      setError('');
      
      const compareRequest = {
        foods: validFoods.map(f => ({ food_ids: [f.FoodID], food_name: f.FoodDescription }))
      };
      
      const response = await HEFIApiService.compareFoodsHEFI(compareRequest);
      setResult(response);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { message?: string } } };
      setError(e?.response?.data?.message || 'Failed to compare HEFI scores');
      console.error('HEFI comparison error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const resetComparison = () => {
    setSelectedFoods([]);
    setResult(null);
    setError('');
    setSearchQuery('');
    setSearchResults([]);
    setShowResults(false);
    setSelectedCategory('');
    setSelectedMethod('');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">HEFI Comparison</h1>
          <p className="text-lg text-gray-600">Create groups of foods and compare their HEFI scores side-by-side.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Sidebar Configuration */}
          <aside className="lg:col-span-1 space-y-6">
            {/* Search Filters */}
            {filters && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-sm font-medium text-gray-700 mb-4">Search Filters</h3>
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
                    className="mt-3 text-xs text-purple-600 hover:text-purple-800"
                  >
                    Clear filters
                  </button>
                )}
              </div>
            )}

            {/* Add Foods */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Search Foods</label>
                <div className="relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search foods to compare..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  />
                  {showResults && (
                    <div className="absolute z-10 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto mt-1">
                      {searchIsLoading ? (
                        <div className="p-3 text-center text-sm text-gray-500">Searching...</div>
                      ) : searchResults.length > 0 ? (
                        searchResults.map((food) => (
                          <button
                            key={food.FoodID}
                            onClick={() => addFood(food)}
                            className="w-full text-left px-4 py-2 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                          >
                            <div className="font-medium text-gray-900">{food.FoodDescription}</div>
                            <div className="text-sm text-gray-500">ID: {food.FoodID}</div>
                          </button>
                        ))
                      ) : (
                        <div className="p-3 text-center text-sm text-gray-500">No foods found</div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Selected Foods */}
              <div className="mt-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-700">Selected Foods ({selectedFoods.length})</h3>
                  {selectedFoods.length > 0 && (
                    <button
                      onClick={() => setSelectedFoods([])}
                      className="text-xs text-gray-500 hover:text-gray-700"
                    >
                      Clear all
                    </button>
                  )}
                </div>
                {selectedFoods.length === 0 ? (
                  <div className="text-center py-4 text-gray-500">
                    <InformationCircleIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>No foods selected yet.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {selectedFoods.map((food) => (
                      <div key={food.FoodID} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                        <div>
                          <div className="text-sm font-medium text-gray-900 truncate max-w-[200px]">{food.FoodDescription}</div>
                          <div className="text-xs text-gray-500">ID: {food.FoodID}</div>
                        </div>
                        <button
                          onClick={() => removeFood(food.FoodID)}
                          className="text-red-500 hover:text-red-700 p-1"
                          aria-label={`Remove ${food.FoodDescription}`}
                        >
                          <XMarkIcon className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Compare Button */}
            {selectedFoods.length >= 2 && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <button
                  onClick={compareHEFI}
                  disabled={isLoading}
                  className="w-full inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  <ChartBarIcon className="mr-2 w-5 h-5" />
                  {isLoading ? 'Comparing...' : 'Compare HEFI Scores'}
                </button>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center">
                  <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mr-3" />
                  <div className="text-red-700">{error}</div>
                </div>
              </div>
            )}
          </aside>

          {/* Main Content */}
          <section className="lg:col-span-2 space-y-8">
            {result ? (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-gray-900">Comparison Results</h2>
                  <button
                    onClick={resetComparison}
                    className="inline-flex items-center text-purple-600 hover:text-purple-700 font-medium"
                  >
                    Start New Comparison
                  </button>
                </div>
                <HEFIComparisonDisplay result={result} />
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <InformationCircleIcon className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Yet</h3>
                <p className="text-gray-600 max-w-xl mx-auto">
                  Use the sidebar to add at least two foods, then click &quot;Compare HEFI Scores&quot; to see the results here.
                </p>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}