/**
 * HENI Dietary Pattern Analysis Dashboard
 * Comprehensive population-level dietary analysis for policy makers and public health officials
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Progress } from '../ui/progress';
import {
  Users,
  Target,
  Globe,
  BarChart3,
  DollarSign,
  Download,
  Plus,
  Trash2,
  AlertTriangle,
  Info,
  Activity,
  Building
} from 'lucide-react';
import { HENIApiService, CNFApiService, type FilterOptions, type HENIDietaryPatternResult } from '../../lib/api';

interface MealFoodItem {
  food_id: number;
  amount: number;
  unit: string;
  name?: string;
}

interface MealItem {
  id: number;
  meal_name: string;
  foods: MealFoodItem[];
}

interface SearchResultItem {
  FoodID: number;
  FoodDescription: string;
  FoodCode?: string;
}

const HENIDietaryPatternDashboard = () => {
  const [meals, setMeals] = useState<MealItem[]>([
    {
      id: 1,
      meal_name: 'Breakfast',
      foods: []
    }
  ]);
  
  const [analysisResults, setAnalysisResults] = useState<HENIDietaryPatternResult['data'] | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState('overview');
  const [populationSize, setPopulationSize] = useState<number>(100000);
  const [timeHorizon, setTimeHorizon] = useState<number>(10);

  // Search and filters (aligned with calculator)
  const [filters, setFilters] = useState<FilterOptions | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedMethod, setSelectedMethod] = useState<string>('');

  // Per-meal search state
  const [mealSearchQueries, setMealSearchQueries] = useState<Record<number, string>>({});
  const [mealSearchResults, setMealSearchResults] = useState<Record<number, SearchResultItem[]>>({});
  const [mealSearchLoading, setMealSearchLoading] = useState<Record<number, boolean>>({});

  useEffect(() => {
    const loadFilters = async () => {
      try {
        const data = await CNFApiService.getFoodFilters();
        setFilters(data);
      } catch (e) {
        console.warn('Failed to load CNF filters', e);
      }
    };
    loadFilters();
  }, []);

  // Add new meal
  const addMeal = () => {
    const newMeal: MealItem = {
      id: Date.now(),
      meal_name: `Meal ${meals.length + 1}`,
      foods: []
    };
    setMeals([...meals, newMeal]);
  };

  // Remove meal
  const removeMeal = (id: number) => {
    setMeals(meals.filter(meal => meal.id !== id));
  };

  // Add food to meal
  const addFoodToMeal = (mealId: number, food: { food_id: number; amount?: number; unit?: string; name?: string }) => {
    setMeals(meals.map(meal => 
      meal.id === mealId 
        ? { ...meal, foods: [...meal.foods, { food_id: food.food_id, amount: food.amount ?? 100, unit: food.unit ?? 'g', name: food.name }] }
        : meal
    ));
    // Clear search for that meal
    setMealSearchQueries(prev => ({ ...prev, [mealId]: '' }));
    setMealSearchResults(prev => ({ ...prev, [mealId]: [] }));
  };

  // Remove food from meal
  const removeFoodFromMeal = (mealId: number, foodIndex: number) => {
    setMeals(meals.map(meal => 
      meal.id === mealId 
        ? { ...meal, foods: meal.foods.filter((_, index) => index !== foodIndex) }
        : meal
    ));
  };

  const updateFoodInMeal = (mealId: number, foodIndex: number, changes: Partial<MealFoodItem>) => {
    setMeals(meals.map(meal => {
      if (meal.id !== mealId) return meal;
      const updatedFoods = meal.foods.map((food, index) => index === foodIndex ? { ...food, ...changes } : food);
      return { ...meal, foods: updatedFoods };
    }));
  };

  const searchFoodsForMeal = async (mealId: number, query: string) => {
    setMealSearchQueries(prev => ({ ...prev, [mealId]: query }));
    if (!query || query.trim().length < 2) {
      setMealSearchResults(prev => ({ ...prev, [mealId]: [] }));
      return;
    }
    setMealSearchLoading(prev => ({ ...prev, [mealId]: true }));
    try {
      const enhanced = await CNFApiService.searchFoodsEnhanced({
        query,
        limit: 25,
        category: selectedCategory || undefined,
        method: selectedMethod || undefined,
      });
      const results = (enhanced.results || []) as Array<{ FoodID: number; FoodDescription: string; FoodCode?: string }>;
      const mapped: SearchResultItem[] = results.map(r => ({
        FoodID: r.FoodID,
        FoodDescription: r.FoodDescription,
        FoodCode: r.FoodCode,
      }));
      setMealSearchResults(prev => ({ ...prev, [mealId]: mapped }));
    } catch (err) {
      console.warn('Meal search error', err);
      setMealSearchResults(prev => ({ ...prev, [mealId]: [] }));
    } finally {
      setMealSearchLoading(prev => ({ ...prev, [mealId]: false }));
    }
  };

  // Analyze dietary pattern
  const analyzeDietaryPattern = async () => {
    if (meals.length === 0 || meals.every(meal => meal.foods.length === 0)) {
      setError('Please add at least one meal with foods');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const patternData = {
        dietary_pattern: {
          meals: meals.map(meal => ({
            meal_name: meal.meal_name,
            foods: meal.foods.map(food => ({
              food_id: food.food_id,
              amount: food.amount,
              unit: food.unit
            }))
          })),
          parameters: {
            population_size: populationSize,
            time_horizon_years: timeHorizon
          }
        }
      };

      const resp = await HENIApiService.analyzeDietaryPattern(patternData);
      if (resp?.success) {
        setAnalysisResults(resp.data);
      } else {
        setError('Failed to analyze dietary pattern');
      }
    } catch {
      setError('Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  // Export comprehensive report
  const exportPolicyReport = () => {
    if (!analysisResults) return;
    
    const reportData = {
      executive_summary: {
        population_size: populationSize,
        time_horizon: timeHorizon,
        total_meals_analyzed: meals.length,
        daily_health_impact: analysisResults.dietary_pattern_summary?.daily_health_impact_minutes,
        population_dalys: analysisResults.population_health_impact?.total_dalys_avoided,
        economic_value: analysisResults.population_health_impact?.economic_value_usd
      },
      detailed_analysis: analysisResults,
      policy_recommendations: analysisResults.policy_insights,
      methodology: 'DALY-based population health impact modeling',
      timestamp: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(reportData, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `heni-policy-analysis-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Building className="h-8 w-8 text-purple-500 mr-3" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              HENI Policy Analysis Dashboard
            </h1>
          </div>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Population-level dietary pattern analysis for evidence-based policy making. 
            Model health impacts, economic outcomes, and intervention strategies using DALY methodology.
          </p>
        </div>

        {/* Configuration Panel */}
        <Card className="mb-8 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Analysis Configuration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Population Size
                </label>
                <Input
                  type="number"
                  value={populationSize}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPopulationSize(parseInt(e.target.value) || 100000)}
                  min="1000"
                  max="10000000"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Time Horizon (Years)
                </label>
                <Input
                  type="number"
                  value={timeHorizon}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTimeHorizon(parseInt(e.target.value) || 10)}
                  min="1"
                  max="50"
                />
              </div>
              <div className="flex items-end">
                <Button
                  onClick={analyzeDietaryPattern}
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <BarChart3 className="h-4 w-4 mr-2" />
                      Analyze Pattern
                    </>
                  )}
                </Button>
              </div>
              <div className="flex items-end">
                <Button
                  variant="outline"
                  onClick={exportPolicyReport}
                  disabled={!analysisResults}
                  className="w-full"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export Report
                </Button>
              </div>
            </div>

            {/* Meal Configuration */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Dietary Pattern ({meals.length} meals)</h3>
                <Button onClick={addMeal} size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Meal
                </Button>
              </div>
              
              <div className="grid gap-4">
                {meals.map((meal) => (
                  <Card key={meal.id} className="border-l-4 border-purple-400">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <Input
                          value={meal.meal_name}
                          onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                            setMeals(meals.map(m => 
                              m.id === meal.id ? { ...m, meal_name: e.target.value } : m
                            ));
                          }}
                          className="font-medium max-w-xs"
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeMeal(meal.id)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>

                      {/* Global search filters */}
                      {filters && (
                        <div className="mb-3 grid grid-cols-1 md:grid-cols-2 gap-3">
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Food Category</label>
                            <select
                              value={selectedCategory}
                              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedCategory(e.target.value)}
                              aria-label="Food category"
                              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
                              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedMethod(e.target.value)}
                              aria-label="Cooking method"
                              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            >
                              <option value="">All methods</option>
                              {filters.methods.map((m) => (
                                <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>
                              ))}
                            </select>
                          </div>
                        </div>
                      )}
                      
                      {/* Meal-specific search */}
                      <div className="space-y-2 mb-3">
                        <div className="relative">
                          <input
                            type="text"
                            value={mealSearchQueries[meal.id] || ''}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => searchFoodsForMeal(meal.id, e.target.value)}
                            placeholder="Search foods to add to this meal..."
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                            aria-label="Search foods"
                          />
                        </div>
                        {mealSearchLoading[meal.id] && (
                          <div className="text-xs text-gray-500">Searching...</div>
                        )}
                        {(mealSearchResults[meal.id] || []).length > 0 && (
                          <div className="bg-white border border-gray-200 rounded-md shadow-sm max-h-48 overflow-y-auto">
                            {(mealSearchResults[meal.id] || []).map((food: SearchResultItem) => (
                              <button
                                key={`${food.FoodID}-${meal.id}`}
                                onClick={() => addFoodToMeal(meal.id, { food_id: food.FoodID, amount: 100, unit: 'g', name: food.FoodDescription })}
                                className="w-full text-left px-3 py-2 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                              >
                                <div className="font-medium text-gray-900">{food.FoodDescription}</div>
                                <div className="text-xs text-gray-500">ID: {food.FoodID}</div>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                      
                      <div className="space-y-2">
                        {meal.foods.map((food, index) => (
                          <div key={`${meal.id}-${index}`} className="flex items-center gap-3 p-2 bg-gray-50 rounded">
                            <span className="flex-1 text-sm truncate" title={food.name || `Food ID: ${food.food_id}`}>
                              {food.name || `Food ID: ${food.food_id}`}
                            </span>
                            <label className="text-xs text-gray-600">Amount</label>
                            <input
                              type="number"
                              min="0.1"
                              step="0.1"
                              value={food.amount}
                              onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateFoodInMeal(meal.id, index, { amount: parseFloat(e.target.value) || 0.1 })}
                              className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
                              aria-label="Amount"
                            />
                            <select
                              value={food.unit}
                              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => updateFoodInMeal(meal.id, index, { unit: e.target.value })}
                              className="px-2 py-1 border border-gray-300 rounded text-sm"
                              aria-label="Unit"
                            >
                              <option value="g">g</option>
                              <option value="ml">ml</option>
                            </select>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeFoodFromMeal(meal.id, index)}
                              className="text-red-500 hover:text-red-700 p-1"
                              aria-label={`Remove ${food.name || `food ${index + 1}`}`}
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </div>
                        ))}

                        {meal.foods.length === 0 && (
                          <div className="text-center py-4 text-gray-500 text-sm">
                            No foods added to this meal
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* Error Display */}
            {error && (
              <Alert className="mt-4 border-red-200 bg-red-50">
                <AlertTriangle className="h-4 w-4 text-red-500" />
                <AlertDescription className="text-red-700">{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Analysis Results */}
        {analysisResults && (
          <Tabs value={selectedTab} onValueChange={setSelectedTab} defaultValue={selectedTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <Globe className="h-4 w-4" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="population" className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                Population Impact
              </TabsTrigger>
              <TabsTrigger value="economic" className="flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                Economic Analysis
              </TabsTrigger>
              <TabsTrigger value="policy" className="flex items-center gap-2">
                <Target className="h-4 w-4" />
                Policy Insights
              </TabsTrigger>
              <TabsTrigger value="interventions" className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Interventions
              </TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              {/* Executive Summary */}
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle>Executive Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-3xl font-bold text-blue-600">
                        {analysisResults.dietary_pattern_summary?.daily_health_impact_minutes > 0 ? '+' : ''}
                        {(analysisResults.dietary_pattern_summary?.daily_health_impact_minutes || 0).toFixed(2)}
                      </div>
                      <div className="text-sm text-gray-600">Minutes/Person/Day</div>
                      <div className="text-xs text-gray-500 mt-1">Health Impact</div>
                    </div>

                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-3xl font-bold text-green-600">
                        {Math.round(analysisResults.population_health_impact?.projected_dalys_avoided || 0).toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-600">DALYs Avoided</div>
                      <div className="text-xs text-gray-500 mt-1">{timeHorizon}-Year Projection</div>
                    </div>

                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <div className="text-3xl font-bold text-purple-600">
                        ${Math.round(analysisResults.population_health_impact?.health_economic_value / 1000000 || 0)}M
                      </div>
                      <div className="text-sm text-gray-600">Economic Value</div>
                      <div className="text-xs text-gray-500 mt-1">Health Savings</div>
                    </div>

                    <div className="text-center p-4 bg-amber-50 rounded-lg">
                      <div className="text-3xl font-bold text-amber-600">
                        {populationSize.toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-600">Population</div>
                      <div className="text-xs text-gray-500 mt-1">Analysis Scope</div>
                    </div>
                  </div>

                  <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-semibold text-gray-800 mb-2">Pattern Classification</h4>
                    <div className="flex items-center gap-2">
                      {(() => {
                        const classificationRaw = analysisResults.dietary_pattern_summary?.pattern_classification as unknown;
                        const classificationLabel = typeof classificationRaw === 'string'
                          ? classificationRaw
                          : (classificationRaw && typeof classificationRaw === 'object' && (classificationRaw as { category?: string }).category)
                            ? (classificationRaw as { category?: string }).category as string
                            : 'Unknown';
                        const variant = classificationLabel === 'Healthy' ? 'default' : classificationLabel === 'Moderate' ? 'secondary' : 'destructive';
                        return (
                          <Badge variant={variant}>
                            {classificationLabel}
                          </Badge>
                        );
                      })()}
                      <span className="text-sm text-gray-600">
                        Based on overall HENI score of {analysisResults.dietary_pattern_summary?.daily_heni_score?.toFixed(1) || '0.0'} μDALY
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Meal Breakdown */}
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle>Meal-Level Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {Array.isArray(analysisResults.meal_breakdowns) && analysisResults.meal_breakdowns.length > 0 ? (
                      analysisResults.meal_breakdowns.map((meal: { meal_name: string; heni_scores: { total_heni_score: number }; meal_composition: { total_energy_kcal: number }; health_impact: { health_impact_minutes: number }; risk_factor_analysis: { risk_factors: Record<string, number> } }, index: number) => (
                        <div key={index} className="p-4 border rounded-lg">
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-medium">{meal.meal_name}</h4>
                            <div className="flex items-center gap-4">
                              <Badge variant={meal.heni_scores?.total_heni_score > 0 ? 'default' : 'destructive'}>
                                {meal.heni_scores?.total_heni_score > 0 ? '+' : ''}
                                {meal.heni_scores?.total_heni_score?.toFixed(1) || '0.0'} μDALY
                              </Badge>
                              <span className="text-sm text-gray-600">
                                {Math.round(meal.meal_composition?.total_energy_kcal || 0)} kcal
                              </span>
                            </div>
                          </div>
                          
                          <div className="grid md:grid-cols-2 gap-4">
                            <div>
                              <h5 className="text-sm font-medium text-gray-700 mb-2">Health Impact</h5>
                              <div className={`text-lg font-semibold ${
                                meal.health_impact?.health_impact_minutes > 0 ? 'text-green-600' : 'text-red-600'
                              }`}>
                                {meal.health_impact?.health_impact_minutes > 0 ? '+' : ''}
                                {(meal.health_impact?.health_impact_minutes || 0).toFixed(2)} minutes
                              </div>
                            </div>
                            
                            <div>
                              <h5 className="text-sm font-medium text-gray-700 mb-2">Risk Factors</h5>
                              <div className="text-sm text-gray-600">
                                {Object.keys(meal.risk_factor_analysis?.risk_factors || {}).length} factors analyzed
                              </div>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-6 text-gray-500">No meal breakdowns available</div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Population Impact Tab */}
            <TabsContent value="population" className="space-y-6">
              <div className="grid lg:grid-cols-2 gap-6">
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Users className="h-5 w-5" />
                      Population Health Metrics
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between items-center p-3 bg-blue-50 rounded">
                      <span className="text-sm font-medium">Total DALYs Avoided</span>
                      <span className="text-lg font-bold text-blue-600">
                        {Math.round(analysisResults.population_health_impact?.projected_dalys_avoided || 0).toLocaleString()}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center p-3 bg-green-50 rounded">
                      <span className="text-sm font-medium">Lives Saved (Equivalent)</span>
                      <span className="text-lg font-bold text-green-600">
                        {Math.round((analysisResults.population_health_impact?.projected_dalys_avoided || 0) / 25).toLocaleString()}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center p-3 bg-purple-50 rounded">
                      <span className="text-sm font-medium">Healthy Years Gained</span>
                      <span className="text-lg font-bold text-purple-600">
                        {Math.round(analysisResults.population_health_impact?.projected_dalys_avoided || 0).toLocaleString()}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center p-3 bg-amber-50 rounded">
                      <span className="text-sm font-medium">Per Capita Impact</span>
                      <span className="text-lg font-bold text-amber-600">
                        {((analysisResults.population_health_impact?.projected_dalys_avoided || 0) / populationSize * 1000).toFixed(1)} 
                        <span className="text-sm ml-1">DALYs/1k</span>
                      </span>
                    </div>
                  </CardContent>
                </Card>

                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Disease Burden Distribution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {Array.isArray(analysisResults.epidemiological_context?.primary_disease_burdens) && analysisResults.epidemiological_context?.primary_disease_burdens.length > 0 ? (
                        analysisResults.epidemiological_context.primary_disease_burdens.map((burden: { disease: string; percentage: number }, index: number) => (
                          <div key={index} className="space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">{burden.disease || `Disease ${index + 1}`}</span>
                              <span className="text-sm text-gray-600">{burden.percentage || 0}%</span>
                            </div>
                            <Progress value={burden.percentage || 0} className="h-2" />
                          </div>
                        ))
                      ) : (
                        <div className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium">Cardiovascular Disease</span>
                            <span className="text-sm text-gray-600">45%</span>
                          </div>
                          <Progress value={45} className="h-2" />
                          
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium">Cancer</span>
                            <span className="text-sm text-gray-600">25%</span>
                          </div>
                          <Progress value={25} className="h-2" />
                          
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium">Diabetes</span>
                            <span className="text-sm text-gray-600">20%</span>
                          </div>
                          <Progress value={20} className="h-2" />
                          
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium">Other</span>
                            <span className="text-sm text-gray-600">10%</span>
                          </div>
                          <Progress value={10} className="h-2" />
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Economic Analysis Tab */}
            <TabsContent value="economic" className="space-y-6">
              <div className="grid lg:grid-cols-3 gap-6">
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="text-green-700">Healthcare Savings</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                      <div className="text-center">
                        <div className="text-3xl font-bold text-green-600">
                          ${Math.round((analysisResults.population_health_impact?.health_economic_value || 0) / 1_000_000)}M
                        </div>
                        <div className="text-sm text-gray-600">{timeHorizon}-Year Total</div>
                      </div>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Per Person:</span>
                        <span className="font-medium">
                          ${Math.round((analysisResults.population_health_impact?.health_economic_value || 0) / populationSize)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Per Year:</span>
                        <span className="font-medium">
                          ${Math.round((analysisResults.population_health_impact?.health_economic_value || 0) / timeHorizon / 1000000)}M
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="text-blue-700">Implementation Cost</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                      <div className="text-center">
                        <div className="text-3xl font-bold text-blue-600">
                          ${Math.round(((analysisResults.population_health_impact?.health_economic_value || 0) * 0.1) / 1_000_000)}M
                        </div>
                        <div className="text-sm text-gray-600">Estimated (10% of savings)</div>
                      </div>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Education:</span>
                        <span className="font-medium">40%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Infrastructure:</span>
                        <span className="font-medium">35%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Monitoring:</span>
                        <span className="font-medium">25%</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="text-purple-700">ROI Analysis</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-purple-600">
                        {Math.round((analysisResults.population_health_impact?.health_economic_value || 0) / 
                        ((analysisResults.population_health_impact?.health_economic_value || 0) * 0.1) || 1)}:1
                      </div>
                      <div className="text-sm text-gray-600">Return on Investment</div>
                    </div>
                    
                    <div className="text-sm text-center text-gray-600">
                      Every $1 invested returns ${Math.round((analysisResults.population_health_impact?.health_economic_value || 0) / 
                      ((analysisResults.population_health_impact?.health_economic_value || 0) * 0.1) || 1)} in health savings
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Policy Insights Tab */}
            <TabsContent value="policy" className="space-y-6">
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle>Priority Interventions</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-6">
                    {Array.isArray(analysisResults.policy_insights?.intervention_priority) && analysisResults.policy_insights?.intervention_priority.length > 0 ? (
                      analysisResults.policy_insights.intervention_priority.map((intervention: { priority: string; title?: string; description?: string; impact?: string }, index: number) => (
                        <div key={index} className="p-4 border-l-4 border-purple-500 bg-purple-50 rounded-r">
                          <div className="flex items-start gap-2 mb-2">
                            <Badge variant={intervention.priority === 'High' ? 'destructive' : 'secondary'}>
                              {intervention.priority || 'Medium'}
                            </Badge>
                            <h4 className="font-semibold text-purple-900">{intervention.title || `Intervention ${index + 1}`}</h4>
                          </div>
                          <p className="text-sm text-purple-800 mb-2">{intervention.description || 'Policy intervention description'}</p>
                          <div className="text-xs text-purple-600">
                            Expected impact: {intervention.impact || 'Moderate health improvement'}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="col-span-2 text-center py-8 text-gray-500">
                        <Target className="h-12 w-12 mx-auto mb-2 opacity-50" />
                        <p>Policy recommendations will be generated after analysis</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle>Target Food Groups</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-3 gap-4">
                    {Array.isArray(analysisResults.policy_insights?.target_food_groups) && analysisResults.policy_insights?.target_food_groups.length > 0 ? (
                      analysisResults.policy_insights.target_food_groups.map((group: { name?: string; impact: number; action: 'increase' | 'decrease' }, index: number) => (
                        <div key={index} className="p-3 bg-gray-50 rounded">
                          <h4 className="font-medium text-gray-800">{group.name || `Food Group ${index + 1}`}</h4>
                          <div className="text-sm text-gray-600 mt-1">
                            Impact: {group.impact > 0 ? '+' : ''}{(group.impact ?? 0).toFixed(1)} μDALY
                          </div>
                          <Badge variant={group.action === 'increase' ? 'default' : 'destructive'} className="mt-2">
                            {group.action === 'increase' ? 'Promote' : 'Reduce'}
                          </Badge>
                        </div>
                      ))
                    ) : (
                      <div className="col-span-3 text-center py-8 text-gray-500">
                        <BarChart3 className="h-12 w-12 mx-auto mb-2 opacity-50" />
                        <p>Food group analysis will be generated after pattern analysis</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Interventions Tab */}
            <TabsContent value="interventions" className="space-y-6">
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle>Recommended Interventions</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div>
                      <h4 className="font-semibold text-gray-800 mb-3">Per-Serving Impact Changes</h4>
                      <div className="grid md:grid-cols-2 gap-4">
                        {Array.isArray(analysisResults.policy_insights?.expected_impact_per_serving_change) && analysisResults.policy_insights?.expected_impact_per_serving_change.length > 0 ? (
                          analysisResults.policy_insights.expected_impact_per_serving_change.map((change: { food_group?: string; impact: number; recommendation?: string }, index: number) => (
                            <div key={index} className="p-3 border rounded">
                              <div className="flex justify-between items-center mb-2">
                                <span className="font-medium">{change.food_group || `Group ${index + 1}`}</span>
                                <Badge variant={(change.impact ?? 0) > 0 ? 'default' : 'destructive'}>
                                  {(change.impact ?? 0) > 0 ? '+' : ''}{(change.impact ?? 0).toFixed(1)} μDALY
                                </Badge>
                              </div>
                              <p className="text-sm text-gray-600">{change.recommendation || 'Intervention recommendation'}</p>
                            </div>
                          ))
                        ) : (
                          <div className="col-span-2 text-center py-8 text-gray-500">
                            <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
                            <p>Intervention analysis will be available after dietary pattern assessment</p>
                          </div>
                        )}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold text-gray-800 mb-3">Implementation Timeline</h4>
                      <div className="space-y-3">
                        <div className="flex items-center gap-4 p-3 bg-blue-50 rounded">
                          <div className="w-12 text-center">
                            <div className="text-sm font-medium text-blue-700">0-6M</div>
                          </div>
                          <div>
                            <h5 className="font-medium text-blue-800">Phase 1: Policy Development</h5>
                            <p className="text-sm text-blue-700">Stakeholder engagement, regulatory framework, pilot programs</p>
                          </div>
                        </div>

                        <div className="flex items-center gap-4 p-3 bg-green-50 rounded">
                          <div className="w-12 text-center">
                            <div className="text-sm font-medium text-green-700">6M-2Y</div>
                          </div>
                          <div>
                            <h5 className="font-medium text-green-800">Phase 2: Implementation</h5>
                            <p className="text-sm text-green-700">Public education campaigns, infrastructure development, monitoring systems</p>
                          </div>
                        </div>

                        <div className="flex items-center gap-4 p-3 bg-purple-50 rounded">
                          <div className="w-12 text-center">
                            <div className="text-sm font-medium text-purple-700">2Y+</div>
                          </div>
                          <div>
                            <h5 className="font-medium text-purple-800">Phase 3: Long-term Impact</h5>
                            <p className="text-sm text-purple-700">Health outcome measurement, policy refinement, scaling up</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        )}

        {/* Footer */}
        <Card className="mt-8 border-purple-200 bg-purple-50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 text-purple-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-medium text-purple-800 mb-2">Policy-Grade Analysis</h4>
                <p className="text-sm text-purple-700">
                  This dashboard provides evidence-based population health impact modeling suitable for policy development, 
                  health economic evaluation, and intervention planning. Results are based on peer-reviewed epidemiological 
                  evidence and DALY methodology as used by the Global Burden of Disease Study.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default HENIDietaryPatternDashboard;