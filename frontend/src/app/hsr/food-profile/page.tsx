'use client';

import React, { useState, useEffect } from 'react';
import { 
  MagnifyingGlassIcon,
  StarIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  LightBulbIcon,
  ArrowPathIcon,
  HeartIcon,
  CubeIcon
} from '@heroicons/react/24/outline';
import { HSRApiService, CNFApiService, type HSRFoodProfile, type SearchResult } from '@/lib/api';

interface SearchState {
  query: string;
  results: SearchResult['results'];
  isLoading: boolean;
  showResults: boolean;
}

export default function HSRFoodProfile() {
  const [selectedFood, setSelectedFood] = useState<{ id: number; name: string } | null>(null);
  const [servingSize, setServingSize] = useState(100);
  const [includeAlternatives, setIncludeAlternatives] = useState(true);
  const [search, setSearch] = useState<SearchState>({
    query: '',
    results: [],
    isLoading: false,
    showResults: false
  });
  const [result, setResult] = useState<HSRFoodProfile | null>(null);
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
        const searchResult = await CNFApiService.searchFoods(search.query, 15);
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

  const selectFood = (selectedItem: SearchResult['results'][0]) => {
    setSelectedFood({
      id: selectedItem.FoodID,
      name: selectedItem.FoodDescription
    });
    setSearch(prev => ({ ...prev, query: '', showResults: false }));
  };

  const analyzeFoodProfile = async () => {
    if (!selectedFood) {
      alert('Please select a food to analyze.');
      return;
    }

    setIsAnalyzing(true);
    try {
      const profile = await HSRApiService.getFoodHSRProfile(
        selectedFood.id,
        servingSize,
        includeAlternatives
      );
      
      setResult(profile);
    } catch (error) {
      console.error('Food profile analysis error:', error);
      alert('Failed to analyze food profile. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getStarRatingColor = (rating: number) => {
    if (rating >= 4.5) return 'text-green-500';
    if (rating >= 3.5) return 'text-green-400';
    if (rating >= 2.5) return 'text-yellow-400';
    if (rating >= 1.5) return 'text-orange-400';
    return 'text-red-400';
  };



  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Food HSR Profile</h1>
          <p className="text-lg text-gray-600">
            Get comprehensive HSR analysis for individual foods with detailed nutritional insights.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Search Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Search Food</h2>
              
              {/* Food Search */}
              <div className="mb-6 relative">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search for a food
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={selectedFood ? selectedFood.name : search.query}
                    onChange={(e) => {
                      if (selectedFood) {
                        setSelectedFood(null);
                        setResult(null);
                      }
                      setSearch(prev => ({ ...prev, query: e.target.value }));
                    }}
                    placeholder="Search for a food..."
                    className="w-full border border-gray-300 rounded-md pl-10 pr-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <MagnifyingGlassIcon className="absolute left-3 top-3.5 w-4 h-4 text-gray-400" />
                </div>
                
                {/* Search Results */}
                {!selectedFood && search.showResults && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-64 overflow-y-auto">
                    {search.isLoading ? (
                      <div className="p-4 text-center text-sm text-gray-500">
                        <ArrowPathIcon className="w-4 h-4 animate-spin mx-auto mb-2" />
                        Searching...
                      </div>
                    ) : search.results.length > 0 ? (
                      search.results.map((item) => (
                        <button
                          key={item.FoodID}
                          onClick={() => selectFood(item)}
                          className="w-full text-left px-4 py-3 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                        >
                          <div className="font-medium text-gray-900 mb-1">
                            {item.FoodDescription}
                          </div>
                          <div className="text-xs text-gray-500">
                            Code: {item.FoodCode} • Relevance: {(item.relevance * 100).toFixed(0)}%
                          </div>
                        </button>
                      ))
                    ) : (
                      <div className="p-4 text-center text-sm text-gray-500">
                        No foods found
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Analysis Options */}
              {selectedFood && (
                <div className="space-y-4 mb-6">
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
                  
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={includeAlternatives}
                      onChange={(e) => setIncludeAlternatives(e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Include healthier alternatives</span>
                  </label>
                </div>
              )}

              {/* Selected Food Display */}
              {selectedFood && (
                <div className="bg-blue-50 rounded-lg p-4 mb-6">
                  <h3 className="text-sm font-medium text-blue-900 mb-2">Selected Food</h3>
                  <p className="text-sm text-blue-800">{selectedFood.name}</p>
                  <p className="text-xs text-blue-600 mt-1">ID: {selectedFood.id}</p>
                </div>
              )}

              {/* Analyze Button */}
              <button
                onClick={analyzeFoodProfile}
                disabled={isAnalyzing || !selectedFood}
                className="w-full bg-blue-600 text-white px-4 py-3 rounded-md font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isAnalyzing ? (
                  <>
                    <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <ChartBarIcon className="w-4 h-4 mr-2" />
                    Analyze Food Profile
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {result ? (
              <div className="space-y-6">
                {/* Basic Info & HSR Rating */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex items-start justify-between mb-6">
                    <div className="flex-1">
                      <h2 className="text-2xl font-bold text-gray-900 mb-2">
                        {result.food_profile.basic_info.food_name}
                      </h2>
                      <div className="flex items-center text-sm text-gray-600 space-x-4">
                        <span>Food Group: {result.food_profile.basic_info.food_group}</span>
                        <span>Category: {result.food_profile.basic_info.hsr_category}</span>
                        <span>Serving: {result.food_profile.basic_info.serving_size}g</span>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <span className="text-sm text-gray-500 mr-2">Confidence:</span>
                      <span className={`text-sm font-medium ${
                        (result.food_profile.hsr_analysis.validation?.confidence_score || 0.8) >= 0.9 ? 'text-green-600' :
                        (result.food_profile.hsr_analysis.validation?.confidence_score || 0.8) >= 0.7 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {((result.food_profile.hsr_analysis.validation?.confidence_score || 0.8) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  {/* Star Rating */}
                  <div className="text-center mb-8">
                    <div className="flex justify-center items-center mb-4">
                      <span className={`text-6xl font-bold mr-4 ${getStarRatingColor(result.food_profile.hsr_analysis.rating.star_rating)}`}>
                        {result.food_profile.hsr_analysis.rating.star_rating}
                      </span>
                      <div className="flex">
                        {[...Array(5)].map((_, i) => (
                          <StarIcon
                            key={i}
                            className={`w-8 h-8 ${
                              i < result.food_profile.hsr_analysis.rating.star_rating ? 'text-yellow-400 fill-current' : 'text-gray-300'
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                    <div className="text-xl font-semibold text-gray-900 mb-2">
                      {result.food_profile.hsr_analysis.rating.level.charAt(0).toUpperCase() + 
                       result.food_profile.hsr_analysis.rating.level.slice(1).replace('_', ' ')}
                    </div>
                    <p className="text-gray-600 max-w-2xl mx-auto">
                      {result.food_profile.hsr_analysis.rating.description}
                    </p>
                  </div>

                  {/* Warnings */}
                  {result.food_profile.hsr_analysis.validation?.warnings && result.food_profile.hsr_analysis.validation.warnings.length > 0 && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                      <div className="flex">
                        <ExclamationTriangleIcon className="w-5 h-5 text-yellow-400 mr-2 flex-shrink-0 mt-0.5" />
                        <div>
                          <h3 className="text-sm font-medium text-yellow-800">Data Quality Warnings</h3>
                          <ul className="mt-1 text-sm text-yellow-700 list-disc list-inside">
                            {result.food_profile.hsr_analysis.validation.warnings.map((warning, index) => (
                              <li key={index}>{warning}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Nutritional Highlights */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <CubeIcon className="w-5 h-5 mr-2" />
                    Nutritional Highlights
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {result.food_profile.nutritional_highlights.high_in.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">High In</h4>
                        <div className="space-y-1">
                          {result.food_profile.nutritional_highlights.high_in.map((item, index) => (
                            <span key={index} className="inline-block bg-red-100 text-red-800 text-xs px-2 py-1 rounded mr-1 mb-1">
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {result.food_profile.nutritional_highlights.good_source_of.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Good Source Of</h4>
                        <div className="space-y-1">
                          {result.food_profile.nutritional_highlights.good_source_of.map((item, index) => (
                            <span key={index} className="inline-block bg-green-100 text-green-800 text-xs px-2 py-1 rounded mr-1 mb-1">
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">FVNL Content</h4>
                      <div className="flex items-center">
                        <div className="w-16 h-16 bg-gradient-to-br from-green-100 to-green-200 rounded-full flex items-center justify-center">
                          <span className="text-sm font-bold text-green-700">
                            {result.food_profile.basic_info.fvnl_percent.toFixed(0)}%
                          </span>
                        </div>
                        <div className="ml-3">
                          <div className="text-xs text-gray-600">Fruits, Vegetables,</div>
                          <div className="text-xs text-gray-600">Nuts & Legumes</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Score Breakdown */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Score Breakdown</h3>
                  
                  {/* Scientific Algorithm Notice */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                    <h4 className="text-sm font-medium text-blue-900 mb-2 flex items-center">
                      <CheckCircleIcon className="w-4 h-4 mr-2" />
                      Scientific HSR Algorithm
                    </h4>
                    <div className="text-sm text-blue-800 space-y-1">
                      <p>• <strong>Scientific Thresholds:</strong> Evidence-based nutrient assessment</p>
                      <p>• <strong>Sugar Analysis:</strong> Natural vs added sugar differentiation</p>
                      <p>• <strong>Satiety Factors:</strong> Food form and satiety impact</p>
                      <p>• <strong>Processing Assessment:</strong> Food processing evaluation</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Risk Nutrients */}
                    <div>
                      <h4 className="text-md font-medium text-red-600 mb-3">Risk Nutrients (Baseline Points)</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Energy</span>
                          <span className="text-sm font-medium">{result.food_profile.hsr_analysis.score_breakdown.components.energy}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Saturated Fat</span>
                          <span className="text-sm font-medium">{result.food_profile.hsr_analysis.score_breakdown.components.saturated_fat}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Sugar</span>
                          <span className="text-sm font-medium">{result.food_profile.hsr_analysis.score_breakdown.components.sugar}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Sodium</span>
                          <span className="text-sm font-medium">{result.food_profile.hsr_analysis.score_breakdown.components.sodium}</span>
                        </div>
                        <div className="flex justify-between border-t pt-2">
                          <span className="text-sm font-semibold text-gray-900">Total</span>
                          <span className="text-sm font-semibold text-red-600">
                            {result.food_profile.hsr_analysis.score_breakdown.baseline_points}
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
                          <span className="text-sm font-medium">{result.food_profile.hsr_analysis.score_breakdown.components.protein}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Fiber</span>
                          <span className="text-sm font-medium">{result.food_profile.hsr_analysis.score_breakdown.components.fiber}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">FVNL</span>
                          <span className="text-sm font-medium">{result.food_profile.hsr_analysis.score_breakdown.components.fvnl}</span>
                        </div>
                        <div className="flex justify-between border-t pt-2">
                          <span className="text-sm font-semibold text-gray-900">Total</span>
                          <span className="text-sm font-semibold text-green-600">
                            -{result.food_profile.hsr_analysis.score_breakdown.modifying_points}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Advanced Components Display */}
                  {result.food_profile.hsr_analysis.score_breakdown.advanced_components && (
                    <div className="mt-6 pt-4 border-t border-gray-200">
                      <h4 className="text-md font-medium text-purple-600 mb-3">Scientific Algorithm Adjustments</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        {result.food_profile.hsr_analysis.score_breakdown.advanced_components.satiety_adjustment !== undefined && (
                          <div className="flex justify-between">
                            <span className="text-gray-600">Satiety Adjustment</span>
                            <span className="font-medium text-purple-600">
                              {result.food_profile.hsr_analysis.score_breakdown.advanced_components.satiety_adjustment >= 0 ? '+' : ''}
                              {result.food_profile.hsr_analysis.score_breakdown.advanced_components.satiety_adjustment.toFixed(1)}
                            </span>
                          </div>
                        )}
                        {result.food_profile.hsr_analysis.score_breakdown.advanced_components.processing_penalty !== undefined && (
                          <div className="flex justify-between">
                            <span className="text-gray-600">Processing Penalty</span>
                            <span className="font-medium text-red-600">
                              +{result.food_profile.hsr_analysis.score_breakdown.advanced_components.processing_penalty.toFixed(1)}
                            </span>
                          </div>
                        )}
                        {result.food_profile.hsr_analysis.score_breakdown.advanced_components.naturalness_bonus !== undefined && (
                          <div className="flex justify-between">
                            <span className="text-gray-600">Naturalness Bonus</span>
                            <span className="font-medium text-green-600">
                              -{result.food_profile.hsr_analysis.score_breakdown.advanced_components.naturalness_bonus.toFixed(1)}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="mt-6 pt-4 border-t border-gray-200">
                    <div className="flex justify-between items-center">
                      <span className="text-lg font-semibold text-gray-900">Final Score</span>
                      <span className="text-2xl font-bold text-blue-600">
                        {result.food_profile.hsr_analysis.score_breakdown.final_score}
                      </span>
                    </div>
                    <div className="mt-2 text-sm text-gray-600">
                      ⭐ <strong>Scientific Analysis:</strong> Using scientifically-improved HSR methods for more accurate assessment
                    </div>
                  </div>
                </div>

                {/* Health Insights */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Strengths */}
                  {result.food_profile.hsr_analysis.health_insights.strengths.length > 0 && (
                    <div className="bg-white rounded-lg shadow-sm p-6">
                      <h3 className="text-lg font-semibold text-green-600 mb-4 flex items-center">
                        <CheckCircleIcon className="w-5 h-5 mr-2" />
                        Strengths
                      </h3>
                      <div className="space-y-3">
                        {result.food_profile.hsr_analysis.health_insights.strengths.map((insight, index) => (
                          <div key={index} className="border-l-4 border-green-400 pl-3">
                            <h4 className="text-sm font-medium text-gray-900">{insight.title}</h4>
                            <p className="text-xs text-gray-600 mt-1">{insight.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Concerns */}
                  {result.food_profile.hsr_analysis.health_insights.concerns.length > 0 && (
                    <div className="bg-white rounded-lg shadow-sm p-6">
                      <h3 className="text-lg font-semibold text-red-600 mb-4 flex items-center">
                        <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
                        Concerns
                      </h3>
                      <div className="space-y-3">
                        {result.food_profile.hsr_analysis.health_insights.concerns.map((insight, index) => (
                          <div key={index} className="border-l-4 border-red-400 pl-3">
                            <h4 className="text-sm font-medium text-gray-900">{insight.title}</h4>
                            <p className="text-xs text-gray-600 mt-1">{insight.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recommendations */}
                  {result.food_profile.hsr_analysis.health_insights.recommendations.length > 0 && (
                    <div className="bg-white rounded-lg shadow-sm p-6">
                      <h3 className="text-lg font-semibold text-blue-600 mb-4 flex items-center">
                        <LightBulbIcon className="w-5 h-5 mr-2" />
                        Recommendations
                      </h3>
                      <div className="space-y-3">
                        {result.food_profile.hsr_analysis.health_insights.recommendations.map((insight, index) => (
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

                {/* Usage Recommendations */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <HeartIcon className="w-5 h-5 mr-2" />
                    Usage Recommendations
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {result.food_profile.usage_recommendations.map((recommendation, index) => (
                      <div key={index} className="flex items-center p-3 bg-gray-50 rounded-lg">
                        <CheckCircleIcon className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
                        <span className="text-sm text-gray-700">{recommendation}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Healthier Alternatives */}
                {result.food_profile.healthier_alternatives && result.food_profile.healthier_alternatives.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <LightBulbIcon className="w-5 h-5 mr-2" />
                      Healthier Alternatives
                    </h3>
                    <div className="space-y-4">
                      {result.food_profile.healthier_alternatives.map((alternative, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4">
                          <h4 className="text-md font-medium text-gray-900 mb-2">{alternative.category}</h4>
                          <ul className="text-sm text-gray-600 space-y-1">
                            {alternative.suggestions.map((suggestion, idx) => (
                              <li key={idx} className="flex items-start">
                                <span className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                                {suggestion}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <ChartBarIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Profile Analysis Yet</h3>
                <p className="text-gray-600">
                  Search for and select a food, then click &quot;Analyze Food Profile&quot; to see detailed HSR analysis.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 