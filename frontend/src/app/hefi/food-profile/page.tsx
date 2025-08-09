'use client';

import React, { useState, useEffect } from 'react';
import { 
  UserIcon,
  MagnifyingGlassIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { HEFIApiService, CNFApiService, type HEFIFoodProfile, type FilterOptions, type SearchResult as CNFSearchResult, type HEFIInterpretation } from '../../../lib/api';

const HEFIProfileDisplay = ({ profile }: { profile: HEFIFoodProfile }) => {
  const { data } = profile;
  const interpretation: HEFIInterpretation | undefined = data.hefi_interpretation as HEFIInterpretation | undefined;
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
      {/* Food Info Header */}
      <div className="card">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {data.food_name}
            </h2>
            <div className="text-gray-600 space-y-1">
              <div>Food IDs: {data.food_ids.join(', ')}</div>
              {data.measure_info && (
                <div>
                  Measure: {data.measure_info.measure_description || 'Standard serving'} 
                  (Factor: {data.measure_info.conversion_factor.toFixed(2)})
                </div>
              )}
            </div>
          </div>
          <div className={`${chipColor} border rounded-lg px-6 py-4 text-center`}>
            <div className="text-3xl font-bold text-gray-900 mb-1">
              {data.total_score.toFixed(1)}
            </div>
            <div className="text-sm text-gray-600 mb-2">
              / {data.max_total_score}
            </div>
            {interpretation && (
              <div className={`text-sm font-semibold`}>
                {interpretation.category}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* HEFI Interpretation */}
      {interpretation && (
        <div className="card">
          <h3 className="text-xl font-bold text-gray-900 mb-4">HEFI Interpretation</h3>
          <div className={`${chipColor} border rounded-lg p-6`}>
            <div className="flex items-center mb-4">
              <CheckCircleIcon className={`w-8 h-8 mr-3`} />
              <div>
                <div className="text-lg font-semibold text-gray-900">
                  Category: {interpretation.category}
                </div>
                <div className="text-gray-600">
                  Score: {(data.total_score / data.max_total_score * 100).toFixed(1)}% of maximum
                </div>
              </div>
            </div>
            <p className="text-gray-700">{interpretation.description}</p>
            {interpretation.population_benchmarks && (
              <div className="text-xs text-gray-500 mt-2">
                Benchmarks: mean {interpretation.population_benchmarks.mean}, p1 {interpretation.population_benchmarks.percentile_1}, p99 {interpretation.population_benchmarks.percentile_99}
              </div>
            )}
            {interpretation.notes && interpretation.notes.length > 0 && (
              <ul className="text-xs text-gray-500 mt-2 list-disc list-inside">
                {interpretation.notes.map((n, i) => (
                  <li key={i}>{n}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {/* Component Scores */}
      <div className="card">
        <h3 className="text-xl font-bold text-gray-900 mb-6">HEFI Component Scores</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(data.components).map(([key, component]) => {
            const percentage = (component.score / component.max_points) * 100;
            const getComponentColor = (pct: number) => {
              if (pct >= 80) return 'bg-green-500';
              if (pct >= 60) return 'bg-blue-500';
              if (pct >= 40) return 'bg-yellow-500';
              if (pct >= 20) return 'bg-orange-500';
              return 'bg-red-500';
            };

            return (
              <div key={key} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="font-medium text-gray-900">
                    {component.name}
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold text-gray-900">
                      {component.score.toFixed(1)}
                    </div>
                    <div className="text-sm text-gray-500">
                      / {component.max_points}
                    </div>
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className={`h-3 rounded-full transition-all duration-300 ${getComponentColor(percentage)}`}
                    style={{ width: `${Math.min(percentage, 100)}%` }}
                  />
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  {percentage.toFixed(1)}% of maximum
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Ratios */}
      <div className="card">
        <h3 className="text-xl font-bold text-gray-900 mb-6">Key Nutritional Ratios</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {Object.entries(data.ratios).map(([key, value]) => (
            <div key={key} className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-xl font-bold text-purple-600">
                {typeof value === 'number' ? value.toFixed(2) : value}
              </div>
              <div className="text-sm text-gray-600 mt-1">
                {key.replace(/_/g, ' ').toLowerCase()}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Nutritional Inputs */}
      <div className="card">
        <h3 className="text-xl font-bold text-gray-900 mb-6">Nutritional Inputs</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(data.inputs).map(([key, value]) => {
            const formatValue = (val: number, key: string) => {
              if (key.includes('_g')) return `${val.toFixed(1)} g`;
              if (key.includes('_mg')) return `${val.toFixed(0)} mg`;
              if (key.includes('_kcal')) return `${val.toFixed(0)} kcal`;
              if (key.includes('_ra')) return val.toFixed(1);
              return val.toFixed(1);
            };

            return (
              <div key={key} className="bg-gray-50 rounded-lg p-4">
                <div className="text-lg font-semibold text-gray-900">
                  {formatValue(value, key)}
                </div>
                <div className="text-sm text-gray-600">
                  {key.replace(/_/g, ' ').toLowerCase()}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

type SelectedFood = { FoodID: number; FoodDescription: string; FoodCode?: string };

export default function HEFIFoodProfilePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<CNFSearchResult['results']>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [profiles, setProfiles] = useState<Record<number, HEFIFoodProfile>>({});
  const [selectedFoods, setSelectedFoods] = useState<SelectedFood[]>([]);
  const [error, setError] = useState<string>('');
  const [filters, setFilters] = useState<FilterOptions | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedMethod, setSelectedMethod] = useState<string>('');
  const [searchIsLoading, setSearchIsLoading] = useState(false);

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
    if (!searchQuery.trim()) {
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
          });
          setSearchResults(enhanced.results || []);
        } catch {
          const basic = await CNFApiService.searchFoods(searchQuery, 50);
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
  }, [searchQuery, selectedCategory, selectedMethod]);

  const addFood = async (food: SelectedFood) => {
    // Add to selected list if not already present
    setSelectedFoods((prev) => {
      if (prev.some((f) => f.FoodID === food.FoodID)) return prev;
      return [...prev, food];
    });

    // Clear search UI
    setSearchQuery('');
    setSearchResults([]);

    // Fetch and store profile
    try {
      setIsLoading(true);
      setError('');
      const response = await HEFIApiService.getFoodHEFIProfile(food.FoodID);
      setProfiles((prev) => ({ ...prev, [food.FoodID]: response }));
    } catch (err: unknown) {
      const e = err as { response?: { data?: { message?: string } } };
      setError(e?.response?.data?.message || 'Failed to load HEFI profile');
      console.error('HEFI profile error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const removeFood = (foodId: number) => {
    setSelectedFoods((prev) => prev.filter((f) => f.FoodID !== foodId));
    setProfiles((prev) => {
      const updated = { ...prev };
      delete updated[foodId];
      return updated;
    });
  };

  const resetProfiles = () => {
    setSelectedFoods([]);
    setProfiles({});
    setError('');
    setSearchQuery('');
    setSearchResults([]);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">HEFI Food Profile</h1>
          <p className="text-lg text-gray-600">Get a detailed HEFI profile for any food with component, ratio, and input breakdowns.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Sidebar Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6 space-y-4">
              <div className="flex items-center mb-4">
                <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 mr-3" />
                <h2 className="text-xl font-semibold text-gray-900">Search and Add Foods</h2>
              </div>

              {filters && (
                <div className="mb-4 space-y-4 border-b pb-4">
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

              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                  }}
                  placeholder="Search for foods (e.g., salmon, bread, apple)..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
                {searchIsLoading && searchQuery && (
                  <div className="p-2 text-sm text-gray-500">Searching...</div>
                )}
                {searchResults.length > 0 && (
                  <div className="absolute z-10 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto mt-1">
                    {searchResults.map((food) => (
                      <button
                        key={food.FoodID}
                        onClick={() => addFood(food)}
                        className="w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0 transition-colors duration-150"
                      >
                        <div className="font-medium text-gray-900">{food.FoodDescription}</div>
                        <div className="text-sm text-gray-500 flex items-center justify-between">
                          <span>ID: {food.FoodID}</span>
                          {food.FoodCode && <span>Code: {food.FoodCode}</span>}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Selected Foods */}
              <div className="pt-2 border-t">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-700">Selected Foods ({selectedFoods.length})</h3>
                  {selectedFoods.length > 0 && (
                    <button onClick={resetProfiles} className="text-xs text-gray-500 hover:text-gray-700">Clear all</button>
                  )}
                </div>
                {selectedFoods.length === 0 ? (
                  <div className="text-center py-4 text-gray-500">
                    <UserIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>No foods added yet.</p>
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
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Error */}
              {error && (
                <div className="mt-2 bg-red-50 border border-red-200 rounded-lg p-3">
                  <div className="flex items-center">
                    <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mr-2" />
                    <div className="text-sm text-red-700">{error}</div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2 space-y-6">
            {isLoading && (
              <div className="bg-white rounded-lg shadow-sm p-4 text-center text-sm text-gray-600">Loading profiles...</div>
            )}

            {selectedFoods.length > 0 ? (
              <div className="space-y-6">
                {selectedFoods.map((food) => (
                  <div key={food.FoodID} className="bg-white rounded-lg shadow-sm p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center">
                        <ChartBarIcon className="w-6 h-6 text-purple-600 mr-2" />
                        <h2 className="text-xl font-bold text-gray-900">HEFI Profile: {food.FoodDescription}</h2>
                      </div>
                    </div>
                    {profiles[food.FoodID] ? (
                      <HEFIProfileDisplay profile={profiles[food.FoodID]} />
                    ) : (
                      <div className="text-center text-gray-500 py-8">Loading profile...</div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <UserIcon className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Profiles Yet</h3>
                <p className="text-gray-600 max-w-xl mx-auto">
                  Search and add foods using the sidebar to view their HEFI profiles here.
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
                <p>• 10 components measuring adequacy and moderation</p>
                <p>• Scores aligned with Canada’s Food Guide recommendations</p>
                <p>• Clear component breakdown and total score out of 80</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
