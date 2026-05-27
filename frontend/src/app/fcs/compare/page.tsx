'use client';

import React, { useState } from 'react';
import {
  ScaleIcon,
  ChartBarIcon,
  ArrowPathIcon,
  TrophyIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import { FCSApiService, type FCSComparison } from '@/lib/api';
import {
  ScorerFoodInput,
  ensureMinSlots,
  type ScorerFoodSlot,
} from '@/components/shared/ScorerFoodInput';

export default function FCSCompare() {
  const [foods, setFoods] = useState<ScorerFoodSlot[]>(() =>
    ensureMinSlots([], 2, 100),
  );
  const [comparison, setComparison] = useState<FCSComparison | null>(null);
  const [isComparing, setIsComparing] = useState(false);

  // Helper to get the actual comparison data from the response
  const getComparisonData = (comparisonResponse: FCSComparison | { success: boolean; data: FCSComparison; message: string } | null): FCSComparison | null => {
    if (!comparisonResponse) return null;
    if ('data' in comparisonResponse && 'success' in comparisonResponse) {
      return comparisonResponse.data;
    }
    return comparisonResponse as FCSComparison;
  };

  const compareFoods = async () => {
    const validFoods = foods.filter(food => food.food_id > 0);
    
    if (validFoods.length < 2) {
      alert('Please select at least 2 foods for comparison.');
      return;
    }

    setIsComparing(true);
    try {
      const comparisonResult = await FCSApiService.compareFoodsFCS({
        foods: validFoods.map(food => ({
          food_ids: [food.food_id],
          food_name: food.food_name
        }))
      });
      
      setComparison(comparisonResult.data);
    } catch (error) {
      console.error('Comparison error:', error);
      alert('Failed to compare foods. Please try again.');
    } finally {
      setIsComparing(false);
    }
  };

  const getFCSColor = (fcs: number) => {
    if (fcs >= 70) return 'text-green-600';
    if (fcs >= 31) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getFCSBgColor = (fcs: number) => {
    if (fcs >= 70) return 'bg-green-50 border-green-200';
    if (fcs >= 31) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  const getFCSLevel = (fcs: number) => {
    if (fcs >= 70) return 'Encourage';
    if (fcs >= 31) return 'Moderation';
    return 'Minimize';
  };

  const formatNOVAName = (nova: string) => {
    return nova.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getDomainColor = (score: number) => {
    if (score > 0) return 'text-green-600';
    if (score < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const comparisonData = getComparisonData(comparison);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Compare Foods</h1>
          <p className="text-lg text-gray-600">
            Rank products by Food Compass Score — works across all food types.
            For one food across all metrics see{' '}
            <a href="/food-profile" className="text-violet-700 underline">Food profile</a>.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Foods to compare</h2>
              <ScorerFoodInput
                mode="slots"
                target="fcs"
                accent="blue"
                userType="individual"
                slots={foods}
                onSlotsChange={setFoods}
                minSlots={2}
                maxSlots={10}
              >
                <button
                  type="button"
                  onClick={compareFoods}
                  disabled={isComparing || foods.filter(f => f.food_id > 0).length < 2}
                  className="w-full mt-2 bg-purple-600 text-white px-4 py-3 rounded-md font-medium hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {isComparing ? (
                    <>
                      <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
                      Comparing…
                    </>
                  ) : (
                    <>
                      <ScaleIcon className="w-4 h-4 mr-2" />
                      Compare foods
                    </>
                  )}
                </button>
              </ScorerFoodInput>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {comparison && comparisonData ? (
              <div className="space-y-6">
                {/* Comparison Summary */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">
                    Comparison Results ({comparisonData.foods_count || 0} foods)
                  </h2>

                  {/* Key Insights */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                      <TrophyIcon className="w-6 h-6 text-green-600 mx-auto mb-2" />
                      <div className="text-sm font-medium text-green-900">Best Choice</div>
                      <div className="text-lg font-bold text-green-600">{comparisonData.comparison_insights?.highest_fcs?.food || 'N/A'}</div>
                      <div className="text-sm text-green-700">FCS: {comparisonData.comparison_insights?.highest_fcs?.fcs || 'N/A'}</div>
                    </div>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                      <ChartBarIcon className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                      <div className="text-sm font-medium text-blue-900">Average Score</div>
                      <div className="text-lg font-bold text-blue-600">{comparisonData.comparison_insights?.average_fcs?.toFixed(1) || 'N/A'}</div>
                      <div className="text-sm text-blue-700">Range: {comparisonData.comparison_insights?.fcs_range?.toFixed(1) || 'N/A'}</div>
                    </div>
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                      <ExclamationTriangleIcon className="w-6 h-6 text-red-600 mx-auto mb-2" />
                      <div className="text-sm font-medium text-red-900">Lowest Score</div>
                      <div className="text-lg font-bold text-red-600">{comparisonData.comparison_insights?.lowest_fcs?.food || 'N/A'}</div>
                      <div className="text-sm text-red-700">FCS: {comparisonData.comparison_insights?.lowest_fcs?.fcs || 'N/A'}</div>
                    </div>
                  </div>
                </div>

                {/* Individual Food Results */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Individual Food Scores</h3>
                  
                  <div className="space-y-4">
                    {(comparisonData.foods || [])
                      .sort((a, b) => b.fcs - a.fcs)
                      .map((food, index) => (
                      <div key={food.name} className={`border rounded-lg p-4 ${getFCSBgColor(food.fcs)}`}>
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center">
                            {index === 0 && <TrophyIcon className="w-5 h-5 text-yellow-500 mr-2" />}
                            <h4 className="font-medium text-gray-900">{food.name}</h4>
                          </div>
                          <div className="flex items-center">
                            <span className={`text-2xl font-bold mr-2 ${getFCSColor(food.fcs)}`}>
                              {food.fcs}
                            </span>
                            <span className={`text-sm font-medium px-2 py-1 rounded ${
                              food.fcs >= 70 ? 'bg-green-100 text-green-800' :
                              food.fcs >= 31 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {getFCSLevel(food.fcs)}
                            </span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-600">Original Score:</span>
                            <span className="ml-2 font-medium">{food.original_score?.toFixed(2) || 'N/A'}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">NOVA Category:</span>
                            <span className="ml-2 font-medium">{formatNOVAName(food.nova_category)}</span>
                          </div>
                        </div>

                        {/* Domain Scores */}
                        {food.domain_scores && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <div className="text-xs font-medium text-gray-700 mb-2">Domain Scores:</div>
                            <div className="grid grid-cols-3 gap-2 text-xs">
                              {Object.entries(food.domain_scores).map(([domain, score]) => (
                                <div key={domain} className="flex justify-between">
                                  <span className="text-gray-600 truncate">
                                    {domain.replace(/_/g, ' ')}:
                                  </span>
                                  <span className={`font-medium ${getDomainColor(score as number)}`}>
                                    {(score as number) > 0 ? '+' : ''}{(score as number).toFixed(1)}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Analysis & Recommendations */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Analysis & Recommendations</h3>
                  
                  <div className="space-y-4">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-green-900 mb-2 flex items-center">
                        <TrophyIcon className="w-4 h-4 mr-2" />
                        Best Choice
                      </h4>
                      <p className="text-sm text-green-800">
                        <strong>{comparisonData.comparison_insights?.highest_fcs?.food || 'N/A'}</strong> has the highest 
                        FCS score of {comparisonData.comparison_insights?.highest_fcs?.fcs || 'N/A'}, placing it in the 
                        &quot;{comparisonData.comparison_insights?.highest_fcs?.fcs ? getFCSLevel(comparisonData.comparison_insights.highest_fcs.fcs) : 'Unknown'}&quot; category. 
                        This food has excellent nutritional quality and is recommended for regular consumption.
                      </p>
                    </div>

                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-blue-900 mb-2 flex items-center">
                        <InformationCircleIcon className="w-4 h-4 mr-2" />
                        Overall Analysis
                      </h4>
                      <div className="text-sm text-blue-800 space-y-1">
                        <p>
                          The {comparisonData.foods_count || 0} foods compared show a score range of {comparisonData.comparison_insights?.fcs_range?.toFixed(1) || 'N/A'} points, 
                          with an average FCS of {comparisonData.comparison_insights?.average_fcs?.toFixed(1) || 'N/A'}.
                        </p>
                        <p>
                          {(comparisonData.foods || []).filter(f => f.fcs >= 70).length > 0 && 
                            `${(comparisonData.foods || []).filter(f => f.fcs >= 70).length} food${(comparisonData.foods || []).filter(f => f.fcs >= 70).length > 1 ? 's' : ''} in the "Encourage" category (≥70), `
                          }
                          {(comparisonData.foods || []).filter(f => f.fcs >= 31 && f.fcs < 70).length > 0 && 
                            `${(comparisonData.foods || []).filter(f => f.fcs >= 31 && f.fcs < 70).length} in "Moderation" (31-69), `
                          }
                          {(comparisonData.foods || []).filter(f => f.fcs < 31).length > 0 && 
                            `${(comparisonData.foods || []).filter(f => f.fcs < 31).length} in "Minimize" (<31).`
                          }
                        </p>
                      </div>
                    </div>

                    {(comparisonData.comparison_insights?.fcs_range || 0) > 30 && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-yellow-900 mb-2">Significant Differences</h4>
                        <p className="text-sm text-yellow-800">
                          There&apos;s a large difference ({comparisonData.comparison_insights?.fcs_range?.toFixed(1) || 'N/A'} points) 
                          between the highest and lowest scoring foods. Consider choosing foods with higher FCS scores 
                          for better nutritional quality.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <ScaleIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Comparison Yet</h3>
                <p className="text-gray-600">
                  Add at least 2 foods and click &quot;Compare Foods&quot; to see detailed nutritional comparison.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}