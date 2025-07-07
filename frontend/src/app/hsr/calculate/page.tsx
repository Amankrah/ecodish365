'use client';

import React, { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  TrashIcon, 
  MagnifyingGlassIcon,
  StarIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  LightBulbIcon,
  ArrowPathIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { HSRApiService, CNFApiService, type HSRResult, type SearchResult } from '@/lib/api';

interface FoodItem {
  id: string;
  food_id: number;
  food_name: string;
  serving_size: number;
  food_group?: string;
}

interface SearchState {
  query: string;
  results: SearchResult['results'];
  isLoading: boolean;
  showResults: boolean;
}

export default function HSRCalculate() {
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
  const [result, setResult] = useState<HSRResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [analysisLevel, setAnalysisLevel] = useState<'simple' | 'detailed'>('detailed');
  const [includeAlternatives, setIncludeAlternatives] = useState(true);
  const [includeMealInsights, setIncludeMealInsights] = useState(true);

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

  const calculateHSR = async () => {
    const validFoods = foods.filter(food => food.food_id > 0 && food.serving_size > 0);
    
    if (validFoods.length === 0) {
      alert('Please select at least one food with a valid serving size.');
      return;
    }

    setIsCalculating(true);
    try {
      const hsrResult = await HSRApiService.calculateHSR({
        food_ids: validFoods.map(food => food.food_id),
        serving_sizes: validFoods.map(food => food.serving_size),
        analysis_level: analysisLevel,
        include_alternatives: includeAlternatives,
        include_meal_insights: includeMealInsights
      });
      
      setResult(hsrResult);
    } catch (error) {
      console.error('HSR calculation error:', error);
      alert('Failed to calculate HSR. Please try again.');
    } finally {
      setIsCalculating(false);
    }
  };

  const getStarRatingColor = (rating: number) => {
    if (rating >= 4.5) return 'text-green-500';
    if (rating >= 3.5) return 'text-green-400';
    if (rating >= 2.5) return 'text-yellow-400';
    if (rating >= 1.5) return 'text-orange-400';
    return 'text-red-400';
  };

  const getPositiveAspectsCount = (result: HSRResult) => {
    let count = 0;
    if (result.hsr_result.score_breakdown.baseline_points === 0) count++;
    if (result.hsr_result.score_breakdown.baseline_points > 0 && result.hsr_result.score_breakdown.baseline_points <= 5) count++;
    if (result.hsr_result.score_breakdown.components.fiber > 0) count++;
    if (result.hsr_result.score_breakdown.components.protein > 0) count++;
    if (result.hsr_result.score_breakdown.components.fvnl > 0) count++;
    if (result.hsr_result.rating.star_rating >= 4.0) count++;
    if (result.hsr_result.rating.star_rating >= 3.0 && result.hsr_result.rating.star_rating < 4.0) count++;
    if (result.hsr_result.score_breakdown.components.energy === 0) count++;
    if (result.hsr_result.score_breakdown.components.sodium === 0) count++;
    if (result.hsr_result.score_breakdown.components.saturated_fat === 0) count++;
    if (result.hsr_result.score_breakdown.components.sugar === 0) count++;
    return count;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">HSR Calculator</h1>
          <p className="text-lg text-gray-600">
            Calculate Health Star Ratings for foods and meals with detailed nutritional analysis.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Add Foods</h2>
              
              {/* Analysis Options */}
              <div className="mb-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Analysis Level
                  </label>
                  <select
                    value={analysisLevel}
                    onChange={(e) => setAnalysisLevel(e.target.value as 'simple' | 'detailed')}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    aria-label="Analysis Level"
                  >
                    <option value="simple">Simple (Star rating only)</option>
                    <option value="detailed">Detailed (Full analysis)</option>
                  </select>
                </div>
                
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={includeAlternatives}
                      onChange={(e) => setIncludeAlternatives(e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Include healthier alternatives</span>
                  </label>
                  
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={includeMealInsights}
                      onChange={(e) => setIncludeMealInsights(e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Include meal insights</span>
                  </label>
                </div>
              </div>

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
                    <div className="mb-3 relative">
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
                    
                    {/* Serving Size */}
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Serving Size (grams)
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="2000"
                        value={food.serving_size}
                        onChange={(e) => updateFood(food.id, { serving_size: Number(e.target.value) })}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        aria-label="Serving size in grams"
                      />
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
                onClick={calculateHSR}
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
                    <ChartBarIcon className="w-4 h-4 mr-2" />
                    Calculate HSR
                  </>
                )}
              </button>

            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {result ? (
              <div className="space-y-6">
                {/* Main HSR Result */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center">
                      <h2 className="text-2xl font-bold text-gray-900 mr-3">
                        {result.food_details.length > 1 ? 'Meal HSR Result' : 'Food HSR Result'}
                      </h2>
                      {result.meal_categorization && result.food_details.length > 1 && (
                        <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                          {result.meal_categorization.final_category}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center">
                      <span className="text-sm text-gray-500 mr-2">Confidence:</span>
                      <span className={`text-sm font-medium ${
                        (result.hsr_result.validation?.confidence_score || 0.8) >= 0.9 ? 'text-green-600' :
                        (result.hsr_result.validation?.confidence_score || 0.8) >= 0.7 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {((result.hsr_result.validation?.confidence_score || 0.8) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  {/* Meal Category Information */}
                  {result.meal_categorization && result.food_details.length > 1 && (
                    <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-6">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-medium text-blue-900">Meal Category Analysis</h3>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          result.meal_categorization.category_confidence >= 0.9 ? 'bg-green-100 text-green-800' :
                          result.meal_categorization.category_confidence >= 0.7 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {(result.meal_categorization.category_confidence * 100).toFixed(0)}% confidence
                        </span>
                      </div>
                      <div className="text-sm text-blue-800">
                        <p>This meal was categorized as <strong>{result.meal_categorization.final_category}</strong> category for HSR calculation.</p>
                        {result.meal_categorization.reasoning && (
                          <p className="mt-1">
                            <strong>Reasoning:</strong> {result.meal_categorization.reasoning}
                          </p>
                        )}
                        {result.meal_categorization.nutritional_rationale && (
                          <p className="mt-1">
                            <strong>Nutritional Rationale:</strong> {result.meal_categorization.nutritional_rationale}
                          </p>
                        )}
                        {result.meal_categorization.scientific_method && (
                          <p className="mt-1 text-xs">
                            <strong>Method:</strong> {result.meal_categorization.scientific_method}
                          </p>
                        )}
                      </div>
                      
                      {/* Category Warnings */}
                      {result.meal_categorization.category_warnings && result.meal_categorization.category_warnings.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-blue-200">
                          <div className="flex items-start">
                            <ExclamationTriangleIcon className="w-4 h-4 text-blue-600 mr-1 flex-shrink-0 mt-0.5" />
                            <div>
                              <p className="text-xs font-medium text-blue-900">Category Warnings:</p>
                              <ul className="text-xs text-blue-800 list-disc list-inside mt-1">
                                {result.meal_categorization.category_warnings.map((warning, index) => (
                                  <li key={index}>{warning}</li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Alternative Categories */}
                      {result.meal_categorization.alternative_categories && result.meal_categorization.alternative_categories.length > 0 && (
                        <div className="mt-3 pt-2 border-t border-blue-200">
                          <p className="text-xs font-medium text-blue-900 mb-1">Alternative Categories Considered:</p>
                          <div className="space-y-1">
                            {result.meal_categorization.alternative_categories.slice(0, 3).map((alt, index) => (
                              <div key={index} className="text-xs text-blue-700 flex items-center justify-between">
                                <span>{alt.category}</span>
                                <span className="text-blue-600">
                                  {(alt.fitness_score * 100).toFixed(0)}% fit
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Star Rating */}
                  <div className="text-center mb-8">
                    <div className="flex justify-center items-center mb-4">
                      <span className={`text-6xl font-bold mr-4 ${getStarRatingColor(result.hsr_result.rating.star_rating)}`}>
                        {result.hsr_result.rating.star_rating}
                      </span>
                      <div className="flex">
                        {[...Array(5)].map((_, i) => (
                          <StarIcon
                            key={i}
                            className={`w-8 h-8 ${
                              i < result.hsr_result.rating.star_rating ? 'text-yellow-400 fill-current' : 'text-gray-300'
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                    <div className="text-xl font-semibold text-gray-900 mb-2">
                      {result.hsr_result.rating.level.charAt(0).toUpperCase() + result.hsr_result.rating.level.slice(1).replace('_', ' ')}
                    </div>
                    <p className="text-gray-600 max-w-2xl mx-auto">
                      {result.hsr_result.rating.description}
                    </p>
                  </div>

                  {/* Warnings */}
                  {result.hsr_result.validation?.warnings && result.hsr_result.validation.warnings.length > 0 && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
                      <div className="flex">
                        <ExclamationTriangleIcon className="w-5 h-5 text-yellow-400 mr-2 flex-shrink-0 mt-0.5" />
                        <div>
                          <h3 className="text-sm font-medium text-yellow-800">Data Quality Warnings</h3>
                          <ul className="mt-1 text-sm text-yellow-700 list-disc list-inside">
                            {result.hsr_result.validation.warnings.map((warning, index) => (
                              <li key={index}>{warning}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Score Breakdown */}
                {analysisLevel === 'detailed' && (
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      {result.food_details.length > 1 ? 'Meal Score Breakdown' : 'Food Score Breakdown'}
                    </h3>
                    
                    {/* Scientific Algorithm Notice */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                      <h4 className="text-sm font-medium text-blue-900 mb-2 flex items-center">
                        <CheckCircleIcon className="w-4 h-4 mr-2" />
                        Scientific HSR Analysis
                      </h4>
                      <div className="text-sm text-blue-800 space-y-1">
                        <p>• <strong>Scientific Thresholds:</strong> Using evidence-based nutrient assessment</p>
                        <p>• <strong>Sugar Source Analysis:</strong> Differentiating natural vs added sugars</p>
                        <p>• <strong>Satiety Factors:</strong> Considering food form and satiety impact</p>
                        <p>• <strong>Processing Assessment:</strong> Evaluating food processing levels</p>
                      </div>
                    </div>
                    
                    {/* Explanation */}
                    <div className="bg-blue-50 rounded-lg p-4 mb-6">
                      <h4 className="text-sm font-medium text-blue-900 mb-2">How HSR Scoring Works</h4>
                      <div className="text-sm text-blue-800 space-y-1">
                        <p>• <strong>Risk nutrients</strong> (energy, saturated fat, sugar, sodium) add baseline points</p>
                        <p>• <strong>Beneficial nutrients</strong> (protein, fiber, FVNL) subtract modifying points</p>
                        <p>• <strong>Final score</strong> = baseline points - modifying points (minimum 0)</p>
                        <p>• <strong>Star rating</strong> is calculated from final score using category-specific thresholds</p>
                        {result.food_details.length > 1 && (
                          <p>• <strong>Meal categorization:</strong> This {result.food_details.length}-food meal was categorized as <strong>{result.hsr_result.rating.category}</strong> for star rating calculation
                            {result.meal_categorization && (
                              <span className="ml-1">
                                (confidence: {(result.meal_categorization.category_confidence * 100).toFixed(0)}%)
                              </span>
                            )}
                          </p>
                        )}
                        <p className="mt-2 pt-2 border-t border-blue-200 font-medium">
                          🧬 <strong>Scientific Algorithm:</strong> This calculation uses scientifically-improved HSR methods for accurate nutritional assessment
                        </p>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Risk Nutrients */}
                      <div>
                        <h4 className="text-md font-medium text-red-600 mb-3">Risk Nutrients (Baseline Points)</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-600">Energy</span>
                            <span className="text-sm font-medium">{result.hsr_result.score_breakdown.components.energy}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-600">Saturated Fat</span>
                            <span className="text-sm font-medium">{result.hsr_result.score_breakdown.components.saturated_fat}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-600">Sugar</span>
                            <span className="text-sm font-medium">{result.hsr_result.score_breakdown.components.sugar}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-600">Sodium</span>
                            <span className="text-sm font-medium">{result.hsr_result.score_breakdown.components.sodium}</span>
                          </div>
                          <div className="flex justify-between border-t pt-2">
                            <span className="text-sm font-semibold text-gray-900">Total</span>
                            <span className="text-sm font-semibold text-red-600">
                              {result.hsr_result.score_breakdown.baseline_points}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Beneficial Nutrients */}
                      <div>
                        <h4 className="text-md font-medium text-green-600 mb-3">Beneficial Nutrients (Modifying Points)</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-600">Protein</span>
                            <span className="text-sm font-medium">{result.hsr_result.score_breakdown.components.protein}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-600">Fiber</span>
                            <span className="text-sm font-medium">{result.hsr_result.score_breakdown.components.fiber}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-600">FVNL</span>
                            <span className="text-sm font-medium">{result.hsr_result.score_breakdown.components.fvnl}</span>
                          </div>
                          <div className="flex justify-between border-t pt-2">
                            <span className="text-sm font-semibold text-gray-900">Total</span>
                            <span className="text-sm font-semibold text-green-600">
                              -{result.hsr_result.score_breakdown.modifying_points}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Advanced Components Display */}
                    {result.hsr_result.score_breakdown.advanced_components && (
                      <div className="mt-6 pt-4 border-t border-gray-200">
                        <h4 className="text-md font-medium text-purple-600 mb-3">Scientific Algorithm Adjustments</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                          {result.hsr_result.score_breakdown.advanced_components.satiety_adjustment !== undefined && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Satiety Adjustment</span>
                              <span className="font-medium text-purple-600">
                                {result.hsr_result.score_breakdown.advanced_components.satiety_adjustment >= 0 ? '+' : ''}
                                {result.hsr_result.score_breakdown.advanced_components.satiety_adjustment.toFixed(1)}
                              </span>
                            </div>
                          )}
                          {result.hsr_result.score_breakdown.advanced_components.processing_penalty !== undefined && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Processing Penalty</span>
                              <span className="font-medium text-red-600">
                                +{result.hsr_result.score_breakdown.advanced_components.processing_penalty.toFixed(1)}
                              </span>
                            </div>
                          )}
                          {result.hsr_result.score_breakdown.advanced_components.naturalness_bonus !== undefined && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Naturalness Bonus</span>
                              <span className="font-medium text-green-600">
                                -{result.hsr_result.score_breakdown.advanced_components.naturalness_bonus.toFixed(1)}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    <div className="mt-6 pt-4 border-t border-gray-200">
                      <div className="flex justify-between items-center mb-2">
                        <div className="flex items-center">
                          <span className="text-lg font-semibold text-gray-900">Final Score</span>
                          <InformationCircleIcon className="w-4 h-4 text-gray-400 ml-1" title="Lower scores are better. Star rating is calculated using category-specific thresholds." />
                        </div>
                        <span className="text-2xl font-bold text-blue-600">
                          {result.hsr_result.score_breakdown.final_score}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 mb-2">
                        Calculation: {result.hsr_result.score_breakdown.baseline_points} baseline points - {result.hsr_result.score_breakdown.modifying_points} modifying points = {result.hsr_result.score_breakdown.final_score}
                      </div>
                      <div className="text-sm text-gray-500">
                        <p>💡 <strong>Understanding your score:</strong></p>
                        {result.hsr_result.score_breakdown.final_score === 0 ? (
                          <p>• Perfect score - all risk nutrients are offset by beneficial ones</p>
                        ) : result.hsr_result.score_breakdown.final_score <= 5 ? (
                          <p>• Low final score - excellent balance of nutrients</p>
                        ) : result.hsr_result.score_breakdown.final_score <= 15 ? (
                          <p>• Moderate final score - some risk nutrients present</p>
                        ) : (
                          <p>• Higher final score - significant risk nutrients present</p>
                        )}
                        <p>• Star rating depends on {result.food_details.length > 1 ? 'meal' : 'food'} category thresholds</p>
                        <p>• Score {result.hsr_result.score_breakdown.final_score} in {result.hsr_result.rating.category} category = {result.hsr_result.rating.star_rating} stars</p>
                        {result.food_details.length > 1 && result.meal_categorization && (
                          <p>• {result.food_details.length} foods combined and categorized as {result.meal_categorization.final_category}</p>
                        )}
                        <p>• ⭐ Using scientific algorithm for improved accuracy</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Result Interpretation */}
                {analysisLevel === 'detailed' && (
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">What Your Results Mean</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-md font-medium text-green-600 mb-3">✅ Positive Aspects</h4>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {/* Dynamic positive aspects based on actual results */}
                          {result.hsr_result.score_breakdown.baseline_points === 0 && (
                            <li>• Excellent risk nutrient profile (all 0 points)</li>
                          )}
                          {result.hsr_result.score_breakdown.baseline_points > 0 && result.hsr_result.score_breakdown.baseline_points <= 5 && (
                            <li>• Low risk nutrient levels ({result.hsr_result.score_breakdown.baseline_points} baseline points)</li>
                          )}
                          {result.hsr_result.score_breakdown.components.fiber > 0 && (
                            <li>• Good fiber content (earning {result.hsr_result.score_breakdown.components.fiber} points)</li>
                          )}
                          {result.hsr_result.score_breakdown.components.protein > 0 && (
                            <li>• Good protein content (earning {result.hsr_result.score_breakdown.components.protein} points)</li>
                          )}
                          {result.hsr_result.score_breakdown.components.fvnl > 0 && (
                            <li>• Good plant food content (earning {result.hsr_result.score_breakdown.components.fvnl} FVNL points)</li>
                          )}
                          {result.hsr_result.rating.star_rating >= 4.0 && (
                            <li>• Excellent nutritional quality ({result.hsr_result.rating.star_rating} stars)</li>
                          )}
                          {result.hsr_result.rating.star_rating >= 3.0 && result.hsr_result.rating.star_rating < 4.0 && (
                            <li>• Above-average nutritional quality ({result.hsr_result.rating.star_rating} stars)</li>
                          )}
                          {result.hsr_result.score_breakdown.components.energy === 0 && (
                            <li>• Low energy density (0 energy points)</li>
                          )}
                          {result.hsr_result.score_breakdown.components.sodium === 0 && (
                            <li>• Low sodium content (0 sodium points)</li>
                          )}
                          {result.hsr_result.score_breakdown.components.saturated_fat === 0 && (
                            <li>• Low saturated fat content (0 points)</li>
                          )}
                          {result.hsr_result.score_breakdown.components.sugar === 0 && (
                            <li>• Low sugar content (0 points)</li>
                          )}
                          {getPositiveAspectsCount(result) === 0 && (
                            <li className="text-orange-600">• No significant positive aspects identified</li>
                          )}
                        </ul>
                      </div>
                      <div>
                        <h4 className="text-md font-medium text-blue-600 mb-3">📊 Score Explanation</h4>
                        <div className="text-sm text-gray-600 space-y-1">
                          <p>Your final score of {result.hsr_result.score_breakdown.final_score} indicates:</p>
                          {result.hsr_result.score_breakdown.final_score === 0 && (
                            <p>• Perfect balance - beneficial nutrients offset all risk</p>
                          )}
                          {result.hsr_result.score_breakdown.final_score > 0 && result.hsr_result.score_breakdown.final_score <= 5 && (
                            <p>• Low risk with some beneficial nutrients</p>
                          )}
                          {result.hsr_result.score_breakdown.final_score > 5 && result.hsr_result.score_breakdown.final_score <= 15 && (
                            <p>• Moderate risk nutrient levels</p>
                          )}
                          {result.hsr_result.score_breakdown.final_score > 15 && (
                            <p>• Higher risk nutrient levels - consume in moderation</p>
                          )}
                          {result.hsr_result.score_breakdown.modifying_points > 0 && (
                            <p>• {result.hsr_result.score_breakdown.modifying_points} points from beneficial nutrients</p>
                          )}
                          <p>• {result.hsr_result.rating.star_rating} stars = {result.hsr_result.rating.level.replace('_', ' ')} quality</p>
                          {result.hsr_result.rating.star_rating >= 4.0 && (
                            <p>• Excellent choice for regular consumption</p>
                          )}
                          {result.hsr_result.rating.star_rating >= 3.0 && result.hsr_result.rating.star_rating < 4.0 && (
                            <p>• Good choice as part of a balanced diet</p>
                          )}
                          {result.hsr_result.rating.star_rating >= 2.0 && result.hsr_result.rating.star_rating < 3.0 && (
                            <p>• Moderate choice - consider healthier alternatives</p>
                          )}
                          {result.hsr_result.rating.star_rating < 2.0 && (
                            <p>• Lower nutritional quality - enjoy in moderation</p>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {/* Areas for Improvement - Only show if there are concerns */}
                    {(result.hsr_result.score_breakdown.baseline_points > 5 || 
                      result.hsr_result.score_breakdown.modifying_points === 0 || 
                      result.hsr_result.rating.star_rating < 3.0) && (
                      <div className="mt-6 pt-6 border-t border-gray-200">
                        <h4 className="text-md font-medium text-orange-600 mb-3">⚠️ Areas for Improvement</h4>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {result.hsr_result.score_breakdown.components.energy > 5 && (
                            <li>• High energy density - consider smaller portions</li>
                          )}
                          {result.hsr_result.score_breakdown.components.saturated_fat > 3 && (
                            <li>• High saturated fat content - choose leaner options</li>
                          )}
                          {result.hsr_result.score_breakdown.components.sugar > 5 && (
                            <li>• High sugar content - limit sweet additions</li>
                          )}
                          {result.hsr_result.score_breakdown.components.sodium > 5 && (
                            <li>• High sodium content - reduce salt or choose low-sodium alternatives</li>
                          )}
                          {result.hsr_result.score_breakdown.components.fiber === 0 && (
                            <li>• Low fiber content - add fruits, vegetables, or whole grains</li>
                          )}
                          {result.hsr_result.score_breakdown.components.protein === 0 && result.hsr_result.score_breakdown.baseline_points > 5 && (
                            <li>• Could benefit from more protein - add lean protein sources</li>
                          )}
                          {result.hsr_result.score_breakdown.components.fvnl === 0 && (
                            <li>• Low plant food content - add more fruits, vegetables, nuts, or legumes</li>
                          )}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* Health Insights */}
                {analysisLevel === 'detailed' && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Strengths */}
                    {result.hsr_result.health_insights.strengths.length > 0 && (
                      <div className="bg-white rounded-lg shadow-sm p-6">
                        <h3 className="text-lg font-semibold text-green-600 mb-4 flex items-center">
                          <CheckCircleIcon className="w-5 h-5 mr-2" />
                          Strengths
                        </h3>
                        <div className="space-y-3">
                          {result.hsr_result.health_insights.strengths.map((insight, index) => (
                            <div key={index} className="border-l-4 border-green-400 pl-3">
                              <h4 className="text-sm font-medium text-gray-900">{insight.title}</h4>
                              <p className="text-xs text-gray-600 mt-1">{insight.description}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Concerns */}
                    {result.hsr_result.health_insights.concerns.length > 0 && (
                      <div className="bg-white rounded-lg shadow-sm p-6">
                        <h3 className="text-lg font-semibold text-red-600 mb-4 flex items-center">
                          <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
                          Concerns
                        </h3>
                        <div className="space-y-3">
                          {result.hsr_result.health_insights.concerns.map((insight, index) => (
                            <div key={index} className="border-l-4 border-red-400 pl-3">
                              <h4 className="text-sm font-medium text-gray-900">{insight.title}</h4>
                              <p className="text-xs text-gray-600 mt-1">{insight.description}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Recommendations */}
                    {result.hsr_result.health_insights.recommendations.length > 0 && (
                      <div className="bg-white rounded-lg shadow-sm p-6">
                        <h3 className="text-lg font-semibold text-blue-600 mb-4 flex items-center">
                          <LightBulbIcon className="w-5 h-5 mr-2" />
                          Recommendations
                        </h3>
                        <div className="space-y-3">
                          {result.hsr_result.health_insights.recommendations.map((insight, index) => (
                            <div key={index} className="border-l-4 border-blue-400 pl-3">
                              <h4 className="text-sm font-medium text-gray-900">{insight.title}</h4>
                              <p className="text-xs text-gray-600 mt-1">{insight.description}</p>
                              {insight.action_text && (
                                <p className="text-xs text-blue-600 mt-1 font-medium">{insight.action_text}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Food Details */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    {result.food_details.length > 1 ? 'Analyzed Foods' : 'Analyzed Food'}
                  </h3>
                  
                  {result.food_details.length > 1 && (
                    <div className="mb-4 p-3 bg-gray-50 rounded-md">
                      <div className="text-sm text-gray-600">
                        <p>This meal contains {result.food_details.length} different foods with a total weight of {result.food_details.reduce((sum, food) => sum + food.serving_size, 0)}g.</p>
                        {result.meal_categorization && (
                          <p className="mt-1">
                            Overall meal category: <strong>{result.meal_categorization.final_category}</strong>
                            {result.meal_categorization.category_confidence && (
                              <span className="ml-2 text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded">
                                {(result.meal_categorization.category_confidence * 100).toFixed(0)}% confidence
                              </span>
                            )}
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {result.food_details.map((food, index) => (
                      <div key={index} className="border border-gray-200 rounded-md p-4">
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-medium text-gray-900 flex-1 pr-2">{food.food_name}</h4>
                          {food.category_confidence !== undefined && (
                            <span className={`text-xs px-2 py-1 rounded-full flex-shrink-0 ${
                              food.category_confidence >= 0.9 ? 'bg-green-100 text-green-800' :
                              food.category_confidence >= 0.7 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {(food.category_confidence * 100).toFixed(0)}%
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-gray-600 space-y-1">
                          <div className="flex justify-between">
                            <span>Serving Size:</span>
                            <span>{food.serving_size}g</span>
                          </div>
                          <div className="flex justify-between">
                            <span>HSR Category:</span>
                            <span className="font-medium">{food.category}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>FVNL Content:</span>
                            <span className={`font-medium ${
                              food.fvnl_percent >= 67 ? 'text-green-600' :
                              food.fvnl_percent >= 40 ? 'text-yellow-600' :
                              'text-gray-600'
                            }`}>
                              {food.fvnl_percent.toFixed(1)}%
                            </span>
                          </div>
                          {food.category_source && (
                            <div className="flex justify-between">
                              <span>Category Source:</span>
                              <span className="text-xs text-gray-500">{food.category_source}</span>
                            </div>
                          )}
                        </div>
                        
                        {/* FVNL Explanation */}
                        {food.fvnl_percent > 0 && (
                          <div className="mt-2 pt-2 border-t border-gray-100">
                            <div className="text-xs text-gray-500">
                              <p>
                                <strong>FVNL:</strong> Fruits, Vegetables, Nuts, Legumes content
                                {food.fvnl_percent >= 67 && ' (High - earns significant health points)'}
                                {food.fvnl_percent >= 40 && food.fvnl_percent < 67 && ' (Moderate - earns some health points)'}
                                {food.fvnl_percent < 40 && ' (Low - limited health points)'}
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                  
                  {/* Category Confidence Summary */}
                  {result.food_details.some(food => food.category_confidence !== undefined) && (
                    <div className="mt-4 p-3 bg-blue-50 rounded-md">
                      <div className="flex items-center mb-2">
                        <InformationCircleIcon className="w-4 h-4 text-blue-600 mr-2" />
                        <span className="text-sm font-medium text-blue-900">Category Confidence Scores</span>
                      </div>
                      <div className="text-xs text-blue-800">
                        <p>• <strong>90%+:</strong> Very confident categorization</p>
                        <p>• <strong>70-89%:</strong> Moderately confident - some ambiguity</p>
                        <p>• <strong>Below 70%:</strong> Lower confidence - consider manual review</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <ChartBarIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Yet</h3>
                <p className="text-gray-600">
                  Add foods and click &quot;Calculate HSR&quot; to see detailed nutritional analysis.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 