'use client';

import React, { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  TrashIcon, 
  MagnifyingGlassIcon,
  StarIcon,
  ChartPieIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  LightBulbIcon,
  TrophyIcon,
  ArrowPathIcon,
  ClockIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { HSRApiService, CNFApiService, type HSRMealInsights, type SearchResult } from '@/lib/api';

interface MealFood {
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

export default function HSRMealInsights() {
  const [foods, setFoods] = useState<MealFood[]>([
    { id: '1', food_id: 0, food_name: '', serving_size: 100 }
  ]);
  const [mealType, setMealType] = useState<'breakfast' | 'lunch' | 'dinner' | 'snack' | ''>('');
  const [dietaryGoals, setDietaryGoals] = useState<('weight_loss' | 'heart_health' | 'diabetes_management')[]>([]);
  const [search, setSearch] = useState<SearchState>({
    query: '',
    results: [],
    isLoading: false,
    showResults: false
  });
  const [activeSearch, setActiveSearch] = useState<string>('');
  const [result, setResult] = useState<HSRMealInsights | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

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

  const updateFood = (id: string, updates: Partial<MealFood>) => {
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

  const toggleDietaryGoal = (goal: 'weight_loss' | 'heart_health' | 'diabetes_management') => {
    setDietaryGoals(prev => 
      prev.includes(goal) 
        ? prev.filter(g => g !== goal)
        : [...prev, goal]
    );
  };

  const analyzeMeal = async () => {
    const validFoods = foods.filter(food => food.food_id > 0 && food.serving_size > 0);
    
    if (validFoods.length === 0) {
      alert('Please select at least one food with a valid serving size.');
      return;
    }

    setIsAnalyzing(true);
    try {
      const insights = await HSRApiService.getMealInsights({
        food_ids: validFoods.map(food => food.food_id),
        serving_sizes: validFoods.map(food => food.serving_size),
        meal_type: mealType || undefined,
        dietary_goals: dietaryGoals.length > 0 ? dietaryGoals : undefined
      });
      
      setResult(insights);
    } catch (error) {
      console.error('Meal analysis error:', error);
      alert('Failed to analyze meal. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getSuitabilityColor = (recommendation: string | undefined) => {
    if (!recommendation) return 'text-gray-600';
    if (recommendation.includes('Excellent')) return 'text-green-600';
    if (recommendation.includes('Good')) return 'text-green-500';
    if (recommendation.includes('Moderate')) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getGoalScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Meal Insights</h1>
          <p className="text-lg text-gray-600">
            Get comprehensive meal-level analysis and personalized recommendations for better nutrition.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Build Your Meal</h2>
              
              {/* Meal Settings */}
              <div className="mb-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Meal Type (Required for Suitability Analysis)
                  </label>
                  <select
                    value={mealType}
                    onChange={(e) => setMealType(e.target.value as 'breakfast' | 'lunch' | 'dinner' | 'snack' | '')}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    aria-label="Meal type"
                  >
                    <option value="">Select meal type</option>
                    <option value="breakfast">Breakfast</option>
                    <option value="lunch">Lunch</option>
                    <option value="dinner">Dinner</option>
                    <option value="snack">Snack</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Dietary Goals (Optional)
                  </label>
                  <div className="space-y-2">
                    {[
                      { key: 'weight_loss', label: 'Weight Loss' },
                      { key: 'heart_health', label: 'Heart Health' },
                      { key: 'diabetes_management', label: 'Diabetes Management' }
                    ].map(goal => (
                      <label key={goal.key} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={dietaryGoals.includes(goal.key as 'weight_loss' | 'heart_health' | 'diabetes_management')}
                          onChange={() => toggleDietaryGoal(goal.key as 'weight_loss' | 'heart_health' | 'diabetes_management')}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">{goal.label}</span>
                      </label>
                    ))}
                  </div>
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

              {/* Analyze Button */}
              <button
                onClick={analyzeMeal}
                disabled={isAnalyzing || foods.every(food => food.food_id === 0)}
                className="w-full mt-6 bg-blue-600 text-white px-4 py-3 rounded-md font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isAnalyzing ? (
                  <>
                    <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <ChartPieIcon className="w-4 h-4 mr-2" />
                    Analyze Meal
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {result ? (
              <div className="space-y-6">
                {/* Meal Overview */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center">
                      <h2 className="text-2xl font-bold text-gray-900 mr-3">
                        {result.food_details.length > 1 ? 'Meal Analysis' : 'Food Analysis'}
                      </h2>
                      {result.meal_categorization && (
                        <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                          {result.meal_categorization.final_category}
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-500">
                      {result.food_details.length} food{result.food_details.length > 1 ? 's' : ''} analyzed
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                    {/* HSR Score */}
                    <div className="text-center">
                      <div className="flex justify-center items-center mb-2">
                        <span className="text-4xl font-bold text-blue-600 mr-2">
                          {result.meal_insights.hsr_breakdown.final_rating.toFixed(1)}
                        </span>
                        <div className="flex">
                          {[...Array(5)].map((_, i) => (
                            <StarIcon
                              key={i}
                              className={`w-6 h-6 ${
                                i < result.meal_insights.hsr_breakdown.final_rating ? 'text-yellow-400 fill-current' : 'text-gray-300'
                              }`}
                            />
                          ))}
                        </div>
                      </div>
                      <div className="text-sm font-medium text-gray-600">HSR Rating</div>
                      <div className="text-xs text-gray-500 capitalize">
                        {result.meal_insights.hsr_breakdown.rating_level.replace('_', ' ')}
                      </div>
                    </div>

                    {/* Total Weight */}
                    <div className="text-center">
                      <div className="text-4xl font-bold text-green-600 mb-2">
                        {result.meal_insights.meal_composition.total_weight.toFixed(0)}
                      </div>
                      <div className="text-sm font-medium text-gray-600">Total Weight (g)</div>
                      <div className="text-xs text-gray-500">
                        {result.meal_insights.meal_composition.total_foods} foods
                      </div>
                    </div>

                    {/* Energy Density */}
                    <div className="text-center">
                      <div className="text-4xl font-bold text-purple-600 mb-2">
                        {(result.meal_insights.nutritional_balance.nutrient_density.protein_per_100g * 4 + 
                          result.meal_insights.nutritional_balance.nutrient_density.fiber_per_100g * 4).toFixed(0)}
                      </div>
                      <div className="text-sm font-medium text-gray-600">Energy Density</div>
                      <div className="text-xs text-gray-500">kJ per 100g</div>
                    </div>
                  </div>

                  {/* Meal Type Suitability */}
                  <div className="bg-gray-50 rounded-lg p-4 mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                      <ClockIcon className="w-5 h-5 mr-2" />
                      Meal Type Suitability
                    </h3>
                    {result.meal_insights.meal_type_suitability ? (
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm text-gray-600">
                            {result.meal_insights.meal_type_suitability.meal_type 
                              ? result.meal_insights.meal_type_suitability.meal_type.charAt(0).toUpperCase() + 
                                result.meal_insights.meal_type_suitability.meal_type.slice(1)
                              : 'Meal'} Suitability
                          </div>
                          <div className={`text-lg font-semibold ${getSuitabilityColor(result.meal_insights.meal_type_suitability.recommendation)}`}>
                            {result.meal_insights.meal_type_suitability.recommendation || 'Analysis pending'}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-blue-600">
                            {typeof result.meal_insights.meal_type_suitability.suitability_score === 'number'
                              ? (result.meal_insights.meal_type_suitability.suitability_score * 100).toFixed(0)
                              : '0'}%
                          </div>
                          <div className="text-xs text-gray-500">Match Score</div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-4">
                        <div className="text-yellow-600 mb-2">
                          <ExclamationTriangleIcon className="w-8 h-8 mx-auto mb-2" />
                        </div>
                        <div className="text-sm font-medium text-gray-900 mb-1">
                          No Meal Type Selected
                        </div>
                        <div className="text-xs text-gray-600 mb-3">
                          Select a meal type above (breakfast, lunch, dinner, or snack) to get meal-specific suitability analysis.
                        </div>
                        <button
                          onClick={() => {
                            // Scroll to meal type selector
                            const mealTypeSelect = document.querySelector('select[aria-label="Meal type"]') as HTMLSelectElement;
                            if (mealTypeSelect) {
                              mealTypeSelect.focus();
                              mealTypeSelect.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            }
                          }}
                          className="text-xs bg-blue-100 text-blue-700 px-3 py-1 rounded-full hover:bg-blue-200 transition-colors"
                        >
                          Select Meal Type
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Meal Categorization Information */}
                {result.meal_categorization && (
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <InformationCircleIcon className="w-5 h-5 mr-2" />
                      Meal Category Analysis
                    </h3>
                    
                    <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="text-md font-medium text-blue-900">HSR Category Assignment</h4>
                          <p className="text-sm text-blue-800 mt-1">
                            This meal was categorized as <strong>{result.meal_categorization.final_category}</strong> for Health Star Rating calculation.
                          </p>
                        </div>
                        <div className="text-right">
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            result.meal_categorization.category_confidence >= 0.9 ? 'bg-green-100 text-green-800' :
                            result.meal_categorization.category_confidence >= 0.7 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {(result.meal_categorization.category_confidence * 100).toFixed(0)}% confidence
                          </span>
                        </div>
                      </div>
                      
                      {/* Categorization Reasoning */}
                      {result.meal_categorization.reasoning && (
                        <div className="text-sm text-blue-700 mb-3">
                          <strong>Categorization Reasoning:</strong> {result.meal_categorization.reasoning}
                        </div>
                      )}

                      {result.meal_categorization.nutritional_rationale && (
                        <div className="text-sm text-blue-700 mb-3">
                          <strong>Nutritional Rationale:</strong> {result.meal_categorization.nutritional_rationale}
                        </div>
                      )}

                      {result.meal_categorization.scientific_method && (
                        <div className="text-sm text-blue-600 mb-3">
                          <strong>Analysis Method:</strong> {result.meal_categorization.scientific_method}
                        </div>
                      )}

                      {/* Scientific Features Information */}
                      <div className="mb-3 p-2 bg-blue-100 rounded-md">
                        <div className="flex items-center">
                          <span className="text-xs bg-blue-200 text-blue-800 px-2 py-1 rounded-full mr-2">
                            Scientific Analysis
                          </span>
                          <span className="text-xs text-blue-700">
                            Scientific nutritional profiling with advanced categorization
                          </span>
                        </div>
                      </div>
                      
                      {/* Category Warnings */}
                      {result.meal_categorization.category_warnings && result.meal_categorization.category_warnings.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-blue-200">
                          <div className="flex items-start">
                            <ExclamationTriangleIcon className="w-4 h-4 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                            <div>
                              <p className="text-xs font-medium text-blue-900 mb-1">Category Warnings:</p>
                              <ul className="text-xs text-blue-800 list-disc list-inside">
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
                        <div className="mt-3 pt-3 border-t border-blue-200">
                          <p className="text-xs font-medium text-blue-900 mb-2">Alternative Categories Considered:</p>
                          <div className="space-y-1">
                            {result.meal_categorization.alternative_categories.slice(0, 3).map((alt, index) => (
                              <div key={index} className="text-xs text-blue-700 flex items-center justify-between bg-blue-100 rounded p-2">
                                <span className="font-medium">{alt.category}</span>
                                <div className="flex items-center">
                                  <span className="text-blue-600 mr-2">
                                    {(alt.fitness_score * 100).toFixed(0)}% fit
                                  </span>
                                  <span className="text-blue-500 text-xs">
                                    {alt.explanation}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Nutritional Quality */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Nutritional Quality</h3>
                  
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                    {Object.entries(result.meal_insights.nutritional_balance.nutritional_quality).map(([key, value]) => (
                      <div key={key} className="text-center">
                        <div className={`w-12 h-12 rounded-full mx-auto mb-2 flex items-center justify-center ${
                          value ? 'bg-green-100' : 'bg-red-100'
                        }`}>
                          {value ? (
                            <CheckCircleIcon className="w-6 h-6 text-green-600" />
                          ) : (
                            <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
                          )}
                        </div>
                        <div className="text-xs font-medium text-gray-900 capitalize">
                          {key.replace('_', ' ')}
                        </div>
                        <div className={`text-xs ${value ? 'text-green-600' : 'text-red-600'}`}>
                          {value ? 'Good' : 'Needs Improvement'}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Macronutrient Distribution */}
                  <div className="mb-4">
                    <h4 className="text-md font-medium text-gray-900 mb-3">Macronutrient Distribution</h4>
                    <div className="space-y-2">
                      {Object.entries(result.meal_insights.nutritional_balance.macronutrient_distribution).map(([nutrient, percentage]) => (
                        <div key={nutrient} className="flex items-center">
                          <div className="w-16 text-sm text-gray-600 capitalize">
                            {nutrient.replace('_percent', '')}
                          </div>
                          <div className="flex-1 bg-gray-200 rounded-full h-2 mx-3">
                            <div 
                              className={`h-2 rounded-full ${
                                nutrient.includes('protein') ? 'bg-blue-500' :
                                nutrient.includes('carbohydrate') ? 'bg-green-500' :
                                'bg-yellow-500'
                              }`}
                              style={{ width: `${Math.min(percentage, 100)}%` }}
                            ></div>
                          </div>
                          <div className="w-12 text-sm text-gray-900 text-right">
                            {percentage.toFixed(1)}%
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Improvement Opportunities */}
                {result.meal_insights.improvement_opportunities.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <LightBulbIcon className="w-5 h-5 mr-2" />
                      Improvement Opportunities
                    </h3>
                    
                    <div className="space-y-4">
                      {result.meal_insights.improvement_opportunities.map((opportunity, index) => (
                        <div key={index} className="border-l-4 border-yellow-400 pl-4 py-2">
                          <h4 className="text-sm font-medium text-gray-900 capitalize mb-1">
                            {opportunity.area}
                          </h4>
                          <p className="text-sm text-gray-600 mb-2">{opportunity.suggestion}</p>
                          <div className="flex items-center text-xs text-gray-500">
                            <span>Current: {opportunity.current.toFixed(1)}</span>
                            <span className="mx-2">→</span>
                            <span>Target: {opportunity.target.toFixed(1)}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Dietary Goal Alignment */}
                {result.meal_insights.dietary_goal_alignment && Object.keys(result.meal_insights.dietary_goal_alignment).length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <TrophyIcon className="w-5 h-5 mr-2" />
                      Dietary Goal Alignment
                    </h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {Object.entries(result.meal_insights.dietary_goal_alignment).map(([goal, data]) => (
                        <div key={goal} className="border border-gray-200 rounded-lg p-4">
                          <h4 className="text-md font-medium text-gray-900 mb-2 capitalize">
                            {goal.replace('_', ' ')}
                          </h4>
                          <div className="flex items-center mb-3">
                            <div className={`text-2xl font-bold mr-2 ${getGoalScoreColor(data?.score || 0)}`}>
                              {typeof data?.score === 'number' ? (data.score * 100).toFixed(0) : '0'}%
                            </div>
                            <div className="text-sm text-gray-600">Alignment</div>
                          </div>
                          <div className="text-xs text-gray-500">
                            {(data?.score || 0) >= 0.8 ? 'Excellent alignment with your goal' :
                             (data?.score || 0) >= 0.6 ? 'Good alignment with some improvements possible' :
                             'Consider adjustments to better meet your goal'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Food Group Distribution */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Food Group Distribution</h3>
                  
                  <div className="mb-4 text-sm text-gray-600">
                    <p>This shows how your meal is composed by food groups. A balanced meal typically includes multiple food groups.</p>
                  </div>
                  
                  <div className="space-y-3">
                    {result.meal_insights.meal_composition.dominant_groups
                      .filter(([group]) => group && group !== 'Unknown')
                      .map(([group, weight], index) => {
                        const percentage = (weight / result.meal_insights.meal_composition.total_weight) * 100;
                        return (
                          <div key={group} className="flex items-center">
                            <div className={`w-6 h-6 rounded-full text-white text-xs flex items-center justify-center mr-3 ${
                              index === 0 ? 'bg-blue-600' :
                              index === 1 ? 'bg-blue-500' :
                              'bg-blue-400'
                            }`}>
                              {index + 1}
                            </div>
                            <div className="flex-1">
                              <div className="flex justify-between mb-1">
                                <span className="text-sm font-medium text-gray-900">{group}</span>
                                <div className="flex items-center">
                                  <span className="text-sm text-gray-600 mr-2">{weight.toFixed(0)}g</span>
                                  <span className="text-sm text-gray-600">({percentage.toFixed(1)}%)</span>
                                </div>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div 
                                  className={`h-2 rounded-full ${
                                    index === 0 ? 'bg-blue-600' :
                                    index === 1 ? 'bg-blue-500' :
                                    'bg-blue-400'
                                  }`}
                                  style={{ width: `${percentage}%` }}
                                ></div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                  
                  {result.meal_insights.meal_composition.dominant_groups.length === 0 && (
                    <div className="text-center py-4 text-gray-500">
                      <p>No food group information available for analysis.</p>
                    </div>
                  )}
                </div>

                {/* Individual Food Details */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Individual Food Analysis
                  </h3>
                  
                  <div className="mb-4 p-3 bg-gray-50 rounded-md">
                    <div className="text-sm text-gray-600">
                      <p>This meal contains {result.food_details.length} different foods with a total weight of {result.food_details.reduce((sum, food) => sum + food.serving_size, 0)}g.</p>
                      <p className="mt-1">
                        Overall meal category: <strong>{result.meal_categorization.final_category}</strong>
                        <span className="ml-2 text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded">
                          {(result.meal_categorization.category_confidence * 100).toFixed(0)}% confidence
                        </span>
                      </p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {result.food_details.map((food, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-3">
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
                        
                        <div className="text-sm text-gray-600 space-y-2">
                          <div className="flex justify-between">
                            <span>Serving Size:</span>
                            <span className="font-medium">{food.serving_size}g</span>
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
                          <div className="mt-3 pt-3 border-t border-gray-100">
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
                <ChartPieIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Analysis Yet</h3>
                <p className="text-gray-600">
                  Build your meal and click &quot;Analyze Meal&quot; to get comprehensive nutritional insights.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 