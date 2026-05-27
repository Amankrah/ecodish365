'use client';
/**
 * Environmental Food Comparison - Compare Environmental Impacts of Multiple Foods
 * Comprehensive side-by-side comparison with detailed analysis
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { Progress } from '../ui/progress';
import {
  Leaf,
  Plus,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Globe,
  Droplets,
  TreePine,
  DollarSign,
  BarChart3,
  Users,
  Info,
  Download,
  RefreshCw,
} from 'lucide-react';
import { 
  EnvironmentalImpactApiService, 
  type FoodComparisonResult,
} from '../../lib/api';
import {
  ScorerFoodInput,
  type ScorerFoodPoolItem,
} from '../shared/ScorerFoodInput';

interface SelectedFood {
  FoodID: number;
  FoodDescription: string;
  FoodCode?: string;
  amount: number;
  unit: string;
}

function envToPool(foods: SelectedFood[]): ScorerFoodPoolItem[] {
  return foods.map(f => ({
    food_id: f.FoodID,
    food_name: f.FoodDescription,
    amount_g: f.amount,
  }));
}

function poolToEnv(pool: ScorerFoodPoolItem[]): SelectedFood[] {
  return pool.map(p => ({
    FoodID: p.food_id,
    FoodDescription: p.food_name,
    amount: p.amount_g,
    unit: 'g',
  }));
}

type UserType = 'individual' | 'researcher' | 'policy';

const EnvironmentalFoodComparison = () => {
  const [selectedFoods, setSelectedFoods] = useState<SelectedFood[]>([]);
  const [comparisonResults, setComparisonResults] = useState<FoodComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [userType, setUserType] = useState<UserType>('individual');

  const compareFoods = async () => {
    if (selectedFoods.length < 2) {
      setError('Please add at least 2 food items to compare');
      return;
    }

    const invalidAmounts = selectedFoods.filter(f => f.amount <= 0);
    if (invalidAmounts.length > 0) {
      setError('All food amounts must be greater than 0');
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      const foods = selectedFoods.map(f => ({ 
        food_id: f.FoodID, 
        amount: f.amount,
        unit: f.unit 
      }));
      
      const response = await EnvironmentalImpactApiService.compareFoodsEnvironmentalImpact({ 
        foods,
        user_type: userType 
      });
      setComparisonResults(response);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { message?: string; error?: string } } };
      setError(e?.response?.data?.error || e?.response?.data?.message || 'Failed to compare foods');
      console.warn('Food comparison error:', e?.response?.data || err);
    } finally {
      setLoading(false);
    }
  };

  const resetComparison = () => {
    setSelectedFoods([]);
    setComparisonResults(null);
    setError('');
  };

  const exportResults = () => {
    if (!comparisonResults) return;
    
    const exportData = {
      timestamp: new Date().toISOString(),
      user_type: userType,
      comparison_results: comparisonResults
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `food-environmental-comparison-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getUserTypeIcon = (type: UserType) => {
    switch (type) {
      case 'individual': return <Users className="h-4 w-4" />;
      case 'researcher': return <Info className="h-4 w-4" />;
      case 'policy': return <Globe className="h-4 w-4" />;
    }
  };

  const formatImpactValue = (value: number, unit: string): string => {
    if (!Number.isFinite(value) || value === 0) return `0 ${unit}`;
    const absVal = Math.abs(value);
    if (absVal >= 1) return `${value.toFixed(3)} ${unit}`;
    if (absVal >= 1e-3) return `${value.toFixed(6)} ${unit}`;
    return `${value.toExponential(2)} ${unit}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-emerald-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <BarChart3 className="h-8 w-8 text-green-500 mr-3" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              Environmental Food Comparison
            </h1>
          </div>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Compare the environmental impacts of different foods using comprehensive LCA methodology 
            with Canadian-specific factors. For one food across all metrics see{' '}
            <a href="/food-profile" className="text-green-700 underline">Food profile</a>.
          </p>
          
          {/* User Type Selector */}
          <div className="mt-4 flex justify-center">
            <div className="bg-white rounded-lg border p-1 shadow-sm">
              {(['individual', 'researcher', 'policy'] as UserType[]).map((type) => (
                <button
                  key={type}
                  onClick={() => setUserType(type)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                    userType === type
                      ? 'bg-green-100 text-green-700 shadow-sm'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  {getUserTypeIcon(type)}
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Food Selection Panel */}
          <Card className="lg:col-span-1 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5" />
                Select Foods to Compare
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <ScorerFoodInput
                mode="pool"
                target="environmental"
                accent="green"
                userType={userType}
                onUserTypeChange={setUserType}
                pool={envToPool(selectedFoods)}
                onPoolChange={pool => setSelectedFoods(poolToEnv(pool))}
                poolSearchLabel="Search foods to compare (grams)"
              >
                <button
                  type="button"
                  onClick={compareFoods}
                  disabled={loading || selectedFoods.length < 2}
                  className="w-full mt-2 inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  <BarChart3 className="mr-2 w-5 h-5" />
                  {loading ? 'Comparing…' : 'Compare foods'}
                </button>
                {selectedFoods.length > 0 && (
                  <button
                    type="button"
                    onClick={resetComparison}
                    className="w-full text-xs text-gray-500 hover:text-gray-700 mt-1"
                  >
                    Clear all foods
                  </button>
                )}
              </ScorerFoodInput>

              {error && (
                <Alert className="border-red-200 bg-red-50">
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                  <AlertDescription className="text-red-700">{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Comparison Results */}
          <div className="lg:col-span-2 space-y-6">
            {comparisonResults ? (
              <>
                {/* Header with Export */}
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="h-5 w-5" />
                      Food Comparison Results
                    </CardTitle>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={exportResults}>
                        <Download className="h-4 w-4 mr-2" />
                        Export
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => setComparisonResults(null)}>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        New Comparison
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {/* Best and Worst Performers */}
                    <div className="grid md:grid-cols-2 gap-4 mb-6">
                      <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                        <div className="flex items-center gap-2 mb-2">
                          <TrendingUp className="h-5 w-5 text-green-600" />
                          <span className="font-semibold text-green-900">Best Performer</span>
                        </div>
                        <div className="font-bold text-green-900">
                          {comparisonResults?.data?.comparison_analysis?.best_performing?.food_name || 'N/A'}
                        </div>
                        <div className="text-sm text-green-700 mt-1">
                          {comparisonResults?.data?.comparison_analysis?.best_performing?.reason || ''}
                        </div>
                      </div>

                      <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                        <div className="flex items-center gap-2 mb-2">
                          <TrendingDown className="h-5 w-5 text-red-600" />
                          <span className="font-semibold text-red-900">Needs Improvement</span>
                        </div>
                        <div className="font-bold text-red-900">
                          {comparisonResults?.data?.comparison_analysis?.worst_performing?.food_name || 'N/A'}
                        </div>
                        <div className="text-sm text-red-700 mt-1">
                          {comparisonResults?.data?.comparison_analysis?.worst_performing?.reason || ''}
                        </div>
                      </div>
                    </div>

                    {/* User Explanation */}
                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 mb-6">
                      <h4 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                        {getUserTypeIcon(userType)}
                        {userType.charAt(0).toUpperCase() + userType.slice(1)} Analysis
                      </h4>
                      <p className="text-blue-800 mb-3">{comparisonResults.data.user_explanation.summary}</p>
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <h5 className="font-medium text-blue-900 mb-2">Key Findings:</h5>
                          <ul className="space-y-1 text-sm text-blue-800">
                      {comparisonResults?.data?.user_explanation?.key_findings?.slice(0, 3).map((finding, index) => (
                              <li key={index} className="flex items-start gap-2">
                                <Badge variant="outline" className="text-xs mt-0.5">{index + 1}</Badge>
                                {finding}
                              </li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <h5 className="font-medium text-blue-900 mb-2">Recommendations:</h5>
                          <ul className="space-y-1 text-sm text-blue-800">
                      {comparisonResults?.data?.user_explanation?.recommendations?.slice(0, 3).map((rec, index) => (
                              <li key={index} className="flex items-start gap-2">
                                <Leaf className="h-3 w-3 text-green-600 mt-0.5" />
                                {rec}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Detailed Food Comparison */}
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Detailed Impact Comparison</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      {comparisonResults?.data?.comparison_analysis?.foods?.map((food, index) => {
                        const sustainabilityLevel = food.sustainability_score >= 80 ? 'Excellent' :
                                                  food.sustainability_score >= 60 ? 'Good' :
                                                  food.sustainability_score >= 40 ? 'Fair' :
                                                  food.sustainability_score >= 20 ? 'Poor' : 'Very Poor';
                        
                        const sustainabilityColor = food.sustainability_score >= 80 ? 'text-green-600' :
                                                   food.sustainability_score >= 60 ? 'text-blue-600' :
                                                   food.sustainability_score >= 40 ? 'text-yellow-600' :
                                                   food.sustainability_score >= 20 ? 'text-orange-600' : 'text-red-600';

                        return (
                          <div key={food.food_id} className="border border-gray-200 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-4">
                              <div className="flex items-center gap-3">
                                <Badge variant="outline" className="text-sm">
                                  #{index + 1}
                                </Badge>
                                <div>
                                  <h4 className="font-semibold text-gray-900">{food.food_name}</h4>
                                  <div className="text-sm text-gray-600">Functional unit: per 100 kcal</div>
                                </div>
                              </div>
                              <div className="text-right">
                                <div className={`font-bold ${sustainabilityColor}`}>
                                  {sustainabilityLevel}
                                </div>
                                <div className="text-sm text-gray-600">
                                  {food.sustainability_score.toFixed(0)}/100
                                </div>
                              </div>
                            </div>

                            {/* Key Metrics */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                              <div className="bg-red-50 p-3 rounded-lg">
                                <div className="flex items-center gap-1 mb-1">
                                  <Globe className="h-4 w-4 text-red-600" />
                                  <span className="text-xs font-medium text-red-900">Carbon</span>
                                </div>
                                <div className="text-sm font-bold text-red-900">
                                  {formatImpactValue(food.lca_results['Global warming'] || 0, 'kg CO₂-eq')}
                                </div>
                              </div>

                              <div className="bg-blue-50 p-3 rounded-lg">
                                <div className="flex items-center gap-1 mb-1">
                                  <Droplets className="h-4 w-4 text-blue-600" />
                                  <span className="text-xs font-medium text-blue-900">Water</span>
                                </div>
                                <div className="text-sm font-bold text-blue-900">
                                  {formatImpactValue(food.lca_results['Water consumption'] || 0, 'm³')}
                                </div>
                              </div>

                              <div className="bg-green-50 p-3 rounded-lg">
                                <div className="flex items-center gap-1 mb-1">
                                  <TreePine className="h-4 w-4 text-green-600" />
                                  <span className="text-xs font-medium text-green-900">Land</span>
                                </div>
                                <div className="text-sm font-bold text-green-900">
                                  {formatImpactValue(food.lca_results['Land use'] || 0, 'm²a')}
                                </div>
                              </div>

                              <div className="bg-yellow-50 p-3 rounded-lg">
                                <div className="flex items-center gap-1 mb-1">
                                  <DollarSign className="h-4 w-4 text-yellow-600" />
                                  <span className="text-xs font-medium text-yellow-900">Cost</span>
                                </div>
                                <div className="text-sm font-bold text-yellow-900">
                                  CAD ${food.environmental_cost.toFixed(3)}
                                </div>
                              </div>
                            </div>

                            {/* Sustainability Progress */}
                            <div className="mb-3">
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-sm font-medium text-gray-700">Sustainability Score</span>
                                <span className={`text-sm font-bold ${sustainabilityColor}`}>
                                  {food.sustainability_score.toFixed(0)}/100
                                </span>
                              </div>
                              <Progress value={food.sustainability_score} className="h-2" />
                            </div>

                            {/* Key Impacts */}
                            {food.key_impacts.length > 0 && (
                              <div>
                                <span className="text-xs font-medium text-gray-600">Key Environmental Concerns:</span>
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {food.key_impacts.slice(0, 3).map((impact, impactIndex) => (
                                    <Badge key={impactIndex} variant="outline" className="text-xs">
                                      {impact}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>

                {/* Comparison Insights */}
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Comparison Insights</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {comparisonResults?.data?.comparison_analysis?.comparison_insights?.map((insight, index) => (
                        <div key={index} className="flex items-start gap-3 p-3 bg-indigo-50 rounded-lg">
                          <Info className="h-5 w-5 text-indigo-600 mt-0.5" />
                          <p className="text-sm text-indigo-800">{insight}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card className="shadow-lg">
                <CardContent className="text-center py-12">
                  <BarChart3 className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                  <h3 className="text-lg font-semibold text-gray-700 mb-2">Ready to Compare Foods</h3>
                  <p className="text-gray-600">
                    Select at least 2 foods from the search panel and click &quot;Compare Foods&quot; to see detailed 
                    environmental impact comparisons with personalized insights.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnvironmentalFoodComparison;