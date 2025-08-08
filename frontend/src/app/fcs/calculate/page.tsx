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
import { FCSApiService, CNFApiService, type FCSResult, type SearchResult } from '@/lib/api';

interface FoodItem {
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

export default function FCSCalculate() {
  const [foods, setFoods] = useState<FoodItem[]>([
    { id: '1', food_id: 0, food_name: '' }
  ]);
  const [search, setSearch] = useState<SearchState>({
    query: '',
    results: [],
    isLoading: false,
    showResults: false
  });
  const [activeSearch, setActiveSearch] = useState<string>('');
  const [result, setResult] = useState<FCSResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);

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
            limit: 10
          });
        } catch {
          searchResult = await CNFApiService.searchFoods(search.query, 10);
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
  }, [search.query]);

  const addFood = () => {
    const newId = (foods.length + 1).toString();
    setFoods([...foods, { id: newId, food_id: 0, food_name: '' }]);
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
        food_names: validFoods.map(food => food.food_name)
      });
      
      console.log('FCS API Response:', fcsResult);
      console.log('FCS Result Data:', fcsResult.data);
      console.log('Setting result to:', fcsResult.data);
      // Extract the actual FCS result data
      const actualResult = (fcsResult.data as { data?: FCSResult }).data || fcsResult.data;
      console.log('Actual FCS result:', actualResult);
      setResult(actualResult);
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

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">FCS Calculator</h1>
          <p className="text-lg text-gray-600">
            Calculate Food Compass Scores using the scientifically validated FCS 2.0 algorithm.
          </p>
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center">
              <SparklesIcon className="w-5 h-5 text-blue-600 mr-2" />
              <span className="text-sm font-medium text-blue-900">Advanced Algorithm</span>
            </div>
            <p className="text-sm text-blue-800 mt-1">
              Evaluates 54 attributes across 9 domains: nutrient ratios, vitamins, minerals, 
              food ingredients, additives, processing, specific lipids, fiber & protein, and phytochemicals.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Add Foods</h2>
              
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
              <button
                onClick={addFood}
                className="w-full mt-4 flex items-center justify-center px-4 py-2 border border-dashed border-gray-300 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 hover:border-gray-400"
              >
                <PlusIcon className="w-4 h-4 mr-2" />
                Add Another Food
              </button>

              {/* Calculate Button */}
              <button
                onClick={calculateFCS}
                disabled={isCalculating || foods.every(food => food.food_id === 0)}
                className="w-full mt-6 bg-blue-600 text-white px-4 py-3 rounded-md font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center"
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
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {result ? (
              <div className="space-y-6">
                {(() => { console.log('Rendering with result:', result); return null; })()}

                {/* Main FCS Result */}
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

                  {/* Score Details */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="text-sm font-medium text-gray-700 mb-2">Original Algorithm Score</h3>
                      <div className="text-2xl font-bold text-gray-900">{result.original_score !== undefined ? result.original_score.toFixed(2) : 'N/A'}</div>
                      <p className="text-xs text-gray-500 mt-1">
                        Raw score from 9-domain calculation before transformation to 1-100 scale
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="text-sm font-medium text-gray-700 mb-2">NOVA Category</h3>
                      <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getNOVAColor(result.nova_category)}`}>
                        {formatNOVAName(result.nova_category)}
                      </span>
                      <p className="text-xs text-gray-500 mt-1">
                        {result.nova_category === 'MIXED_PROCESSING_LEVELS' 
                          ? 'Energy-weighted processing level for combined foods' 
                          : 'Food processing classification level'}
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
                                NOVA {food.nova_level}
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
                              <span>NOVA {food.nova_level} × {(food.energy_weight * 100).toFixed(1)}%</span>
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

                {/* Algorithm Information */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    FCS 2.0 Algorithm Details
                  </h3>
                  
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                    <h4 className="text-sm font-medium text-blue-900 mb-2 flex items-center">
                      <CheckCircleIcon className="w-4 h-4 mr-2" />
                      Scientific Validation
                    </h4>
                    <div className="text-sm text-blue-800 space-y-1">
                      <p>• <strong>9-Domain Structure:</strong> Comprehensive evaluation across all nutritional aspects</p>
                      <p>• <strong>54 Attributes:</strong> Most detailed nutrient profiling system available</p>
                      <p>• <strong>Population Validated:</strong> Tested on 47,999 U.S. adults (NHANES 1999-2018)</p>
                      <p>• <strong>Health Outcomes:</strong> 7% lower mortality risk per standard deviation increase</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="bg-green-100 rounded-lg p-4 mb-2">
                        <BeakerIcon className="w-8 h-8 text-green-600 mx-auto" />
                      </div>
                      <h4 className="text-sm font-medium text-gray-900">Advanced Analysis</h4>
                      <p className="text-xs text-gray-600 mt-1">
                        Per 100 kcal normalization for consistent comparison
                      </p>
                    </div>
                    <div className="text-center">
                      <div className="bg-blue-100 rounded-lg p-4 mb-2">
                        <ChartBarIcon className="w-8 h-8 text-blue-600 mx-auto" />
                      </div>
                      <h4 className="text-sm font-medium text-gray-900">Domain Weighting</h4>
                      <p className="text-xs text-gray-600 mt-1">
                        Evidence-based weighting with half-weight for emerging domains
                      </p>
                    </div>
                    <div className="text-center">
                      <div className="bg-purple-100 rounded-lg p-4 mb-2">
                        <SparklesIcon className="w-8 h-8 text-purple-600 mx-auto" />
                      </div>
                      <h4 className="text-sm font-medium text-gray-900">Unique Features</h4>
                      <p className="text-xs text-gray-600 mt-1">
                        Only system that evaluates all food types uniformly
                      </p>
                    </div>
                  </div>
                </div>

                {/* Food Details */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Analyzed Food</h3>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900">{result.name}</h4>
                    <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">FCS Score:</span>
                        <span className={`ml-2 font-medium ${getFCSColor(result.fcs)}`}>
                          {result.fcs}/100
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Processing Level:</span>
                        <span className="ml-2 font-medium">
                          {formatNOVAName(result.nova_category)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
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
    </div>
  );
}