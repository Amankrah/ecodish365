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
import { CNFApiService, SearchResult, FoodGroup, Food } from '@/lib/api';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { debounce } from 'lodash';

interface SearchFilters {
  foodGroup: string;
  minRelevance: number;
  limit: number;
}

const INITIAL_FILTERS: SearchFilters = {
  foodGroup: '',
  minRelevance: 0,
  limit: 50,
};

export default function CNFSearchPage() {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>(INITIAL_FILTERS);
  const [results, setResults] = useState<SearchResult | null>(null);
  const [selectedFood, setSelectedFood] = useState<Food | null>(null);
  const [foodGroups, setFoodGroups] = useState<FoodGroup[]>([]);
  const [selectedFoods, setSelectedFoods] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [offset, setOffset] = useState(0);

  // Load food groups on mount
  useEffect(() => {
    loadFoodGroups();
  }, []);

  // Debounced search function
  const debouncedSearch = useCallback(
    debounce((searchQuery: string, searchFilters: SearchFilters, searchOffset: number) => {
      if (searchQuery.trim()) {
        performSearch(searchQuery, searchFilters, searchOffset);
      } else {
        setResults(null);
      }
    }, 500),
    []
  );

  // Trigger search when query or filters change
  useEffect(() => {
    setOffset(0);
    debouncedSearch(query, filters, 0);
  }, [query, filters, debouncedSearch]);

  const loadFoodGroups = async () => {
    try {
      const groups = await CNFApiService.getFoodGroups();
      setFoodGroups(groups);
    } catch (error) {
      console.error('Failed to load food groups:', error);
    }
  };

  const performSearch = async (searchQuery: string, searchFilters: SearchFilters, searchOffset: number) => {
    try {
      setLoading(true);
      const searchResults = await CNFApiService.searchFoods(searchQuery, searchFilters.limit, searchOffset);
      
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
    debouncedSearch(query, filters, newOffset);
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

  const toggleFoodSelection = (foodId: number) => {
    setSelectedFoods(prev => 
      prev.includes(foodId) 
        ? prev.filter(id => id !== foodId)
        : [...prev, foodId]
    );
  };

  const clearSelections = () => {
    setSelectedFoods([]);
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
          <p className="text-gray-600">
            Search through the Canadian Nutrient File database with advanced filtering options
          </p>
        </div>

        {/* Search Interface */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          {/* Search Bar */}
          <div className="relative mb-4">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search for foods (e.g., apple, chicken breast, whole wheat bread...)"
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
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                          onChange={() => toggleFoodSelection(food.FoodID)}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                          aria-label={`Select ${food.FoodDescription}`}
                        />
                        <div className="flex-1">
                          <h3 className="text-sm font-medium text-gray-900 mb-1">
                            {food.FoodDescription}
                          </h3>
                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            <span>Code: {food.FoodCode}</span>
                            <span>Group: {food.FoodGroupID}</span>
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

        {/* Food Details Modal */}
        {selectedFood && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  Food Details
                </h3>
                <button
                  type="button"
                  onClick={() => setSelectedFood(null)}
                  className="p-2 text-gray-400 hover:text-gray-600"
                  title="Close"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>
              
              <div className="px-6 py-4">
                <div className="mb-4">
                  <h4 className="text-xl font-medium text-gray-900 mb-2">
                    {selectedFood.FoodDescription}
                  </h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Food Code:</span>
                      <span className="ml-2 text-gray-600">{selectedFood.FoodCode}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Food Group:</span>
                      <span className="ml-2 text-gray-600">{selectedFood.FoodGroupID}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Country:</span>
                      <span className="ml-2 text-gray-600">{selectedFood.CountryCode}</span>
                    </div>
                    {selectedFood.ScientificName && (
                      <div>
                        <span className="font-medium text-gray-700">Scientific Name:</span>
                        <span className="ml-2 text-gray-600 italic">{selectedFood.ScientificName}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Nutrients */}
                <div className="mb-4">
                  <h5 className="text-lg font-medium text-gray-900 mb-3">
                    Nutritional Information
                  </h5>
                  <div className="grid grid-cols-1 gap-2 max-h-60 overflow-y-auto">
                    {selectedFood.NutrientValues.map((nutrient, index) => (
                      <div key={index} className="flex justify-between items-center py-2 px-3 bg-gray-50 rounded">
                        <span className="text-sm text-gray-700">{nutrient.NutrientName}</span>
                        <span className="text-sm font-medium text-gray-900">
                          {nutrient.NutrientValue} {nutrient.NutrientUnit}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Conversion Factors */}
                {selectedFood.ConversionFactors.length > 0 && (
                  <div>
                    <h5 className="text-lg font-medium text-gray-900 mb-3">
                      Conversion Factors
                    </h5>
                    <div className="grid grid-cols-1 gap-2">
                      {selectedFood.ConversionFactors.map((conversion, index) => (
                        <div key={index} className="flex justify-between items-center py-2 px-3 bg-gray-50 rounded">
                          <span className="text-sm text-gray-700">{conversion.MeasureDescription}</span>
                          <span className="text-sm font-medium text-gray-900">
                            {conversion.ConversionFactorValue}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 