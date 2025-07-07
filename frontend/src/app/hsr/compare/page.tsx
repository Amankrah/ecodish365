'use client';

import React, { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  TrashIcon, 
  MagnifyingGlassIcon,
  StarIcon,
  ArrowsUpDownIcon,
  TrophyIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { HSRApiService, CNFApiService, type HSRComparison, type SearchResult } from '@/lib/api';

interface ComparisonFood {
  id: string;
  food_id: number;
  food_name: string;
}

interface SearchState {
  query: string;
  results: SearchResult['results'];
  isLoading: boolean;
  showResults: boolean;
}

export default function HSRCompare() {
  const [foods, setFoods] = useState<ComparisonFood[]>([
    { id: '1', food_id: 0, food_name: '' },
    { id: '2', food_id: 0, food_name: '' }
  ]);
  const [servingSize, setServingSize] = useState(100);
  const [sortBy, setSortBy] = useState<'hsr_rating' | 'energy' | 'protein' | 'sodium' | 'fiber'>('hsr_rating');
  const [search, setSearch] = useState<SearchState>({
    query: '',
    results: [],
    isLoading: false,
    showResults: false
  });
  const [activeSearch, setActiveSearch] = useState<string>('');
  const [result, setResult] = useState<HSRComparison | null>(null);
  const [isComparing, setIsComparing] = useState(false);

  // Debounced search
  useEffect(() => {
    if (search.query.length < 2) {
      setSearch(prev => ({ ...prev, results: [], showResults: false }));
      return;
    }

    const timeoutId = setTimeout(async () => {
      setSearch(prev => ({ ...prev, isLoading: true }));
      try {
        const searchResult = await CNFApiService.searchFoods(search.query, 10);
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
  }, [search.query]);

  const addFood = () => {
    const newId = (foods.length + 1).toString();
    setFoods([...foods, { id: newId, food_id: 0, food_name: '' }]);
  };

  const removeFood = (id: string) => {
    if (foods.length > 2) {
      setFoods(foods.filter(food => food.id !== id));
    }
  };

  const updateFood = (id: string, updates: Partial<ComparisonFood>) => {
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

  const compareFoods = async () => {
    const validFoods = foods.filter(food => food.food_id > 0);
    
    if (validFoods.length < 2) {
      alert('Please select at least 2 foods to compare.');
      return;
    }

    setIsComparing(true);
    try {
      const comparisonResult = await HSRApiService.compareFoods({
        food_ids: validFoods.map(food => food.food_id),
        serving_size: servingSize,
        sort_by: sortBy
      });
      
      setResult(comparisonResult);
    } catch (error) {
      console.error('Food comparison error:', error);
      alert('Failed to compare foods. Please try again.');
    } finally {
      setIsComparing(false);
    }
  };

  const getStarRatingColor = (rating: number) => {
    if (rating >= 4.5) return 'text-green-500';
    if (rating >= 3.5) return 'text-green-400';
    if (rating >= 2.5) return 'text-yellow-400';
    if (rating >= 1.5) return 'text-orange-400';
    return 'text-red-400';
  };

  const getRatingBadgeColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'excellent': return 'bg-green-100 text-green-800';
      case 'good': return 'bg-green-50 text-green-700';
      case 'average': return 'bg-yellow-100 text-yellow-800';
      case 'below_average': return 'bg-orange-100 text-orange-800';
      case 'poor': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };



  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Food Comparison</h1>
          <p className="text-lg text-gray-600">
            Compare Health Star Ratings across multiple foods to make better choices.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Select Foods to Compare</h2>
              
              {/* Comparison Settings */}
              <div className="mb-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Serving Size (grams)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="2000"
                    value={servingSize}
                    onChange={(e) => setServingSize(Number(e.target.value))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    aria-label="Serving size in grams"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sort By
                  </label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as 'hsr_rating' | 'energy' | 'protein' | 'sodium' | 'fiber')}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    aria-label="Sort by"
                  >
                    <option value="hsr_rating">HSR Rating</option>
                    <option value="energy">Energy (kJ)</option>
                    <option value="protein">Protein</option>
                    <option value="sodium">Sodium</option>
                    <option value="fiber">Fiber</option>
                  </select>
                </div>
              </div>

              {/* Food Inputs */}
              <div className="space-y-4">
                {foods.map((food, index) => (
                  <div key={food.id} className="border border-gray-200 rounded-md p-4">
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="text-sm font-medium text-gray-700">Food {index + 1}</h3>
                      {foods.length > 2 && (
                        <button
                          onClick={() => removeFood(food.id)}
                          className="text-red-500 hover:text-red-700"
                          aria-label={`Remove food ${index + 1}`}
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                    
                    {/* Food Search */}
                    <div className="relative">
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
                  </div>
                ))}
              </div>

              {/* Add Food Button */}
              {foods.length < 10 && (
                <button
                  onClick={addFood}
                  className="w-full mt-4 flex items-center justify-center px-4 py-2 border border-dashed border-gray-300 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 hover:border-gray-400"
                >
                  <PlusIcon className="w-4 h-4 mr-2" />
                  Add Another Food
                </button>
              )}

              {/* Compare Button */}
              <button
                onClick={compareFoods}
                disabled={isComparing || foods.filter(food => food.food_id > 0).length < 2}
                className="w-full mt-6 bg-blue-600 text-white px-4 py-3 rounded-md font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isComparing ? (
                  <>
                    <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
                    Comparing...
                  </>
                ) : (
                  <>
                    <ArrowsUpDownIcon className="w-4 h-4 mr-2" />
                    Compare Foods
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {result ? (
              <div className="space-y-6">
                {/* Summary */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gray-900">Comparison Results</h2>
                    <div className="text-sm text-gray-500">
                      {result.comparison.successfully_analyzed} of {result.comparison.total_foods} foods analyzed
                    </div>
                  </div>

                  {/* Quick Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div className="bg-green-50 rounded-lg p-4">
                      <div className="flex items-center">
                        <TrophyIcon className="w-8 h-8 text-green-600 mr-3" />
                        <div>
                          <div className="text-sm text-green-600 font-medium">Best Choice</div>
                          <div className="text-lg font-bold text-green-900">
                            {result.comparison.summary.highest_rated?.hsr_rating.toFixed(1)} ★
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-purple-50 rounded-lg p-4">
                      <div className="flex items-center">
                        <StarIcon className="w-8 h-8 text-purple-600 mr-3" />
                        <div>
                          <div className="text-sm text-purple-600 font-medium">Serving Size</div>
                          <div className="text-lg font-bold text-purple-900">
                            {result.comparison.serving_size}g
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Enhanced Algorithm Notice */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                    <div className="flex items-center">
                      <CheckCircleIcon className="w-5 h-5 text-blue-600 mr-2" />
                      <div>
                        <h4 className="text-sm font-medium text-blue-900">Scientific HSR Analysis</h4>
                        <p className="text-sm text-blue-800 mt-1">
                          All foods analyzed using scientifically-improved HSR methods with scientific thresholds, 
                          sugar source differentiation, and satiety considerations for more accurate comparisons.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Rating Distribution */}
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Rating Distribution</h3>
                    <div className="grid grid-cols-5 gap-2">
                      {Object.entries(result.comparison.summary.rating_distribution).map(([level, count]) => (
                        <div key={level} className="text-center">
                          <div className={`h-8 rounded ${
                            level === 'excellent' ? 'bg-green-500' :
                            level === 'good' ? 'bg-green-400' :
                            level === 'average' ? 'bg-yellow-400' :
                            level === 'below_average' ? 'bg-orange-400' :
                            'bg-red-400'
                          } flex items-center justify-center text-white font-bold`}>
                            {count}
                          </div>
                          <div className="text-xs text-gray-600 mt-1 capitalize">
                            {level.replace('_', ' ')}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Recommendations */}
                  {result.comparison.recommendations.length > 0 && (
                    <div className="bg-blue-50 rounded-lg p-4">
                      <h3 className="text-md font-semibold text-blue-900 mb-2">Recommendations</h3>
                      <ul className="text-sm text-blue-800 space-y-1">
                        {result.comparison.recommendations.map((rec, index) => (
                          <li key={index} className="flex items-start">
                            <CheckCircleIcon className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Detailed Comparison Table */}
                <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">Detailed Comparison</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      Comparing {result.comparison.successfully_analyzed} foods at {result.comparison.serving_size}g serving size
                    </p>
                  </div>
                  
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Food
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            HSR Rating
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Level
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Category
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Energy (kJ)
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Protein
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Sat Fat
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Sodium
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Fiber
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            FVNL
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {result.comparison.foods.map((food, index) => (
                          <tr key={food.food_id} className={index === 0 ? 'bg-green-50' : ''}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                {index === 0 && (
                                  <TrophyIcon className="w-5 h-5 text-yellow-500 mr-2" />
                                )}
                                <div>
                                  <div className="text-sm font-medium text-gray-900 max-w-xs truncate">
                                    {food.food_name}
                                  </div>
                                  {food.food_group && food.food_group !== 'Unknown' && (
                                    <div className="text-xs text-gray-500">
                                      {food.food_group}
                                    </div>
                                  )}
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <span className={`text-lg font-bold mr-2 ${getStarRatingColor(food.hsr_rating)}`}>
                                  {food.hsr_rating.toFixed(1)}
                                </span>
                                <div className="flex">
                                  {[...Array(5)].map((_, i) => (
                                    <StarIcon
                                      key={i}
                                      className={`w-4 h-4 ${
                                        i < food.hsr_rating ? 'text-yellow-400 fill-current' : 'text-gray-300'
                                      }`}
                                    />
                                  ))}
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRatingBadgeColor(food.hsr_level)}`}>
                                {food.hsr_level.replace('_', ' ')}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-900">
                                {food.category}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {food.energy_kj.toFixed(0)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {food.key_nutrients.protein.toFixed(1)}g
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {food.key_nutrients.saturated_fat.toFixed(1)}g
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {food.key_nutrients.sodium.toFixed(0)}mg
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {food.key_nutrients.fiber.toFixed(1)}g
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              <span className={`${
                                food.key_nutrients.fvnl_percent >= 67 ? 'text-green-600 font-medium' :
                                food.key_nutrients.fvnl_percent >= 40 ? 'text-yellow-600 font-medium' :
                                'text-gray-600'
                              }`}>
                                {food.key_nutrients.fvnl_percent.toFixed(1)}%
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Individual Food Insights */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Individual Food Analysis</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {result.comparison.foods.map((food, index) => (
                      <div key={food.food_id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center">
                            {index === 0 && (
                              <TrophyIcon className="w-5 h-5 text-yellow-500 mr-2" />
                            )}
                            <h4 className="text-md font-semibold text-gray-900">
                              {food.food_name}
                            </h4>
                          </div>
                          <div className="flex items-center">
                            <span className={`text-lg font-bold mr-2 ${getStarRatingColor(food.hsr_rating)}`}>
                              {food.hsr_rating.toFixed(1)}
                            </span>
                            <div className="flex">
                              {[...Array(5)].map((_, i) => (
                                <StarIcon
                                  key={i}
                                  className={`w-4 h-4 ${
                                    i < food.hsr_rating ? 'text-yellow-400 fill-current' : 'text-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                        </div>
                        
                        {/* Food Details */}
                        <div className="mb-4 p-3 bg-gray-50 rounded-md">
                          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-600">Category:</span>
                              <span className="font-medium">{food.category}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Food Group:</span>
                              <span className="font-medium text-xs">
                                {food.food_group && food.food_group !== 'Unknown' ? food.food_group : 'Not specified'}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">FVNL:</span>
                              <span className={`font-medium ${
                                food.key_nutrients.fvnl_percent >= 67 ? 'text-green-600' :
                                food.key_nutrients.fvnl_percent >= 40 ? 'text-yellow-600' :
                                'text-gray-600'
                              }`}>
                                {food.key_nutrients.fvnl_percent.toFixed(1)}%
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Rating:</span>
                              <span className={`text-xs px-2 py-1 rounded-full ${getRatingBadgeColor(food.hsr_level)}`}>
                                {food.hsr_level.replace('_', ' ')}
                              </span>
                            </div>
                          </div>
                        </div>
                        
                        {/* Key Nutrients */}
                        <div className="mb-4">
                          <h5 className="text-sm font-medium text-gray-700 mb-2">Key Nutrients (per {result.comparison.serving_size}g)</h5>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div className="flex justify-between">
                              <span>Protein:</span>
                              <span className="font-medium">{food.key_nutrients.protein.toFixed(1)}g</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Fiber:</span>
                              <span className="font-medium">{food.key_nutrients.fiber.toFixed(1)}g</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Sat Fat:</span>
                              <span className="font-medium">{food.key_nutrients.saturated_fat.toFixed(1)}g</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Sodium:</span>
                              <span className="font-medium">{food.key_nutrients.sodium.toFixed(0)}mg</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Sugar:</span>
                              <span className="font-medium">{food.key_nutrients.sugar.toFixed(1)}g</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Energy:</span>
                              <span className="font-medium">{food.energy_kj.toFixed(0)}kJ</span>
                            </div>
                          </div>
                        </div>
                        
                        {/* Insights */}
                        <div className="space-y-3">
                          {food.top_strength && (
                            <div className="flex items-start">
                              <CheckCircleIcon className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                              <div>
                                <div className="text-sm font-medium text-green-700">Strength</div>
                                <div className="text-sm text-green-600">{food.top_strength}</div>
                              </div>
                            </div>
                          )}
                          
                          {food.top_concern && (
                            <div className="flex items-start">
                              <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
                              <div>
                                <div className="text-sm font-medium text-red-700">Concern</div>
                                <div className="text-sm text-red-600">{food.top_concern}</div>
                              </div>
                            </div>
                          )}
                          
                          {/* FVNL Explanation */}
                          {food.key_nutrients.fvnl_percent > 0 && (
                            <div className="text-xs text-gray-500 pt-2 border-t border-gray-100">
                              <p>
                                <strong>FVNL:</strong> Fruits, Vegetables, Nuts, Legumes content
                                {food.key_nutrients.fvnl_percent >= 67 && ' (High - earns significant health points)'}
                                {food.key_nutrients.fvnl_percent >= 40 && food.key_nutrients.fvnl_percent < 67 && ' (Moderate - earns some health points)'}
                                {food.key_nutrients.fvnl_percent < 40 && ' (Low - limited health points)'}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <ArrowsUpDownIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Comparison Yet</h3>
                <p className="text-gray-600">
                  Select foods and click &quot;Compare Foods&quot; to see detailed side-by-side analysis.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 