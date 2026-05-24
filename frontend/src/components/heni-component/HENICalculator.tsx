/**
 * HENI Calculator - Main Interface Component
 * Comprehensive health impact calculator for individuals
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  Heart,
  Calculator,
  TrendingUp,
  AlertTriangle,
  Info,
  Plus,
  Trash2,
  Download,
  Share2,
  ChevronDown,
} from 'lucide-react';
import { HENIResultsCard } from './HENIResultsCard';
import { HealthImpactVisualization } from './HealthImpactVisualization';
import { RiskFactorBreakdown } from './RiskFactorBreakdown';
import { DiseaseImpactChart } from './DiseaseImpactChart';
import { HENIApiService, CNFApiService, type HENIResult, type FilterOptions } from '../../lib/api';
import { AudienceToggle, type UserType, type ExplanationsBlock } from '../shared/AudienceToggle';
import { ExplanationsPanel } from '../shared/ExplanationsPanel';
import { AIEnhancedSearch } from '../shared/AIEnhancedSearch';
import { RecipeDecomposerModal } from '../shared/RecipeDecomposerModal';
import { useRecall24hReceiver } from '../shared/useRecall24hReceiver';

interface SelectedFood {
  FoodID: number;
  FoodDescription: string;
  FoodCode?: string;
  amount: number;
  unit: string;
}

interface SearchResult {
  FoodID: number;
  FoodDescription: string;
  FoodCode?: string;
}

const HENICalculator = () => {
  const [selectedFoods, setSelectedFoods] = useState<SelectedFood[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [heniResults, setHeniResults] = useState<HENIResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchIsLoading, setSearchIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [selectedTab, setSelectedTab] = useState('calculator');
  const [filters, setFilters] = useState<FilterOptions | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedMethod, setSelectedMethod] = useState<string>('');
  const [showExportDropdown, setShowExportDropdown] = useState(false);
  const [userType, setUserType] = useState<UserType>('individual');
  // AUDIENCE-CODE-1 follow-up: track the userType that was active when the
  // last calculation succeeded so we can flag stale explanations on toggle.
  const [lastCalcUserType, setLastCalcUserType] = useState<UserType | null>(null);
  // AI-MATCH-1: recipe decomposer modal open state.
  const [recipeModalOpen, setRecipeModalOpen] = useState(false);

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

  // AI-MATCH-2 (2026-05-24): pick up an aggregated 24-h recall payload
  // handed off from /recall-24h.
  useRecall24hReceiver({
    target: 'heni',
    onIngredients: (ingredients, meta) => {
      setUserType(meta.user_type);
      setSelectedFoods(ingredients.map(i => ({
        FoodID: i.food_id,
        FoodDescription: i.food_description,
        amount: i.mass_g,
        unit: 'g',
      })));
    },
  });

  // Close export dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showExportDropdown && !(event.target as Element).closest('.relative')) {
        setShowExportDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showExportDropdown]);

  // Debounced search with filters (enhanced -> fallback)
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    if (searchQuery.trim().length < 2) {
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

  const addFood = (food: SearchResult) => {
    const newFood: SelectedFood = {
      FoodID: food.FoodID,
      FoodDescription: food.FoodDescription,
      FoodCode: food.FoodCode,
      amount: 100,
      unit: 'g'
    };
    
    if (!selectedFoods.some(f => f.FoodID === food.FoodID)) {
      setSelectedFoods([...selectedFoods, newFood]);
    }
    setSearchQuery('');
    setSearchResults([]);
  };

  const removeFood = (foodId: number) => {
    setSelectedFoods(selectedFoods.filter(f => f.FoodID !== foodId));
  };

  const updateFoodAmount = (foodId: number, amount: number) => {
    setSelectedFoods(selectedFoods.map(f => 
      f.FoodID === foodId ? { ...f, amount: Math.max(0.1, amount) } : f
    ));
  };

  // Calculate HENI score
  const calculateHENI = async () => {
    if (selectedFoods.length === 0) {
      setError('Please add at least one food item to calculate HENI score');
      return;
    }

    // Check for valid amounts
    const invalidAmounts = selectedFoods.filter(f => f.amount <= 0);
    if (invalidAmounts.length > 0) {
      setError('All food amounts must be greater than 0.');
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      const meal = selectedFoods.map(f => ({ 
        food_id: f.FoodID, 
        amount: f.amount,
        unit: f.unit 
      }));
      
      const response = await HENIApiService.calculateHENI({ meal, user_type: userType });
      setHeniResults(response);
      setLastCalcUserType(userType);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { message?: string; error?: string } } };
      setError(e?.response?.data?.error || e?.response?.data?.message || 'Failed to calculate HENI score');
      console.warn('HENI calculation error:', e?.response?.data || err);
    } finally {
      setLoading(false);
    }
  };

  // Clear all foods
  const resetCalculation = () => {
    setSelectedFoods([]);
    setHeniResults(null);
    setError('');
    setSearchQuery('');
    setSearchResults([]);
    setLastCalcUserType(null);
  };

  // Export results as JSON
  const exportResultsJSON = () => {
    if (!heniResults) return;
    
    const exportData = {
      timestamp: new Date().toISOString(),
      meal_composition: selectedFoods,
      heni_analysis: heniResults
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `heni-analysis-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Export results as PDF
  const exportResultsPDF = async () => {
    if (!heniResults) return;
    
    // For now, create a text-based PDF until we add jsPDF dependency
    const analysis = heniResults.data;
    const timestamp = new Date().toLocaleString();
    
    const reportContent = `
HENI HEALTH IMPACT ANALYSIS REPORT
Generated on: ${timestamp}

===========================================
MEAL COMPOSITION
===========================================
${selectedFoods.map(food => 
  `• ${food.FoodDescription}: ${food.amount}g`
).join('\n')}

Total Weight: ${analysis?.meal_composition?.total_weight_grams || 0}g
Total Energy: ${analysis?.meal_composition?.total_energy_kcal || 0} kcal

===========================================
HENI SCORES
===========================================
Total HENI Score: ${analysis?.heni_scores?.total_heni_score?.toFixed(2) || '0.00'} μDALY
Per 100 kcal: ${analysis?.heni_scores?.heni_per_100_kcal?.toFixed(2) || '0.00'} μDALY
Per 100g: ${analysis?.heni_scores?.heni_per_100_grams?.toFixed(2) || '0.00'} μDALY

===========================================
HEALTH IMPACT
===========================================
Health Impact: ${analysis?.health_impact?.health_impact_minutes?.toFixed(2) || '0.00'} minutes
Description: ${analysis?.health_impact?.description || 'N/A'}

===========================================
COMPONENT BREAKDOWN
===========================================
Food Group Contributions:
${Object.entries(analysis?.component_breakdown?.food_group_contributions || {})
  .map(([group, value]) => `  ${group.replace('_', ' ')}: ${(value as number).toFixed(2)} μDALY`)
  .join('\n')}

Nutrient Contributions:
${Object.entries(analysis?.component_breakdown?.nutrient_contributions || {})
  .map(([nutrient, value]) => `  ${nutrient.replace('_', ' ')}: ${(value as number).toFixed(2)} μDALY`)
  .join('\n')}

===========================================
RISK FACTORS
===========================================
${Object.entries(analysis?.risk_factor_analysis?.risk_factors || {})
  .map(([factor, amount]) => `${factor.replace('_', ' ')}: ${(amount as number).toFixed(3)}g`)
  .join('\n')}

===========================================
SCIENTIFIC CONTEXT
===========================================
This HENI score is calculated using the Global Burden of Disease methodology,
which quantifies health impacts in micro-DALYs (μDALYs).
One μDALY = 0.5256 minutes of healthy life impact.
Positive scores indicate health benefits, negative scores indicate health risks.

Report generated by EcoDish365 HENI Calculator
    `.trim();
    
    const blob = new Blob([reportContent], {
      type: 'text/plain;charset=utf-8'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `heni-analysis-report-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-purple-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Heart className="h-8 w-8 text-red-500 mr-3" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              HENI Health Impact Calculator
            </h1>
          </div>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Discover how your food choices impact your health using evidence-based
            Disability Adjusted Life Years (DALY) methodology
          </p>
          {/* Audience selector (AUDIENCE-CODE-1 2026-05-23) */}
          <div className="mt-4">
            <AudienceToggle
              userType={userType}
              onChange={setUserType}
              accent="green"
              staleResultHint={heniResults !== null && lastCalcUserType !== null && userType !== lastCalcUserType}
            />
          </div>
        </div>

        {/* Main Content */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab} defaultValue={selectedTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6">
            <TabsTrigger value="calculator" className="flex items-center gap-2">
              <Calculator className="h-4 w-4" />
              Calculator
            </TabsTrigger>
            <TabsTrigger value="analysis" className="flex items-center gap-2" disabled={!heniResults}>
              <TrendingUp className="h-4 w-4" />
              Analysis
            </TabsTrigger>
            <TabsTrigger value="insights" className="flex items-center gap-2" disabled={!heniResults}>
              <Info className="h-4 w-4" />
              Insights
            </TabsTrigger>
          </TabsList>

          {/* Calculator Tab */}
          <TabsContent value="calculator" className="space-y-6">
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Food Input Section */}
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Plus className="h-5 w-5" />
                    Build Your Meal
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-1">Add Foods</h2>
                    <p className="text-sm text-gray-600">Search and select foods to include in the HENI calculation.</p>
                  </div>

                  {/* Search Filters */}
                  {filters && (
                    <div className="space-y-4 border-b pb-4">
                      <h3 className="text-sm font-medium text-gray-700">Search Filters</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Food Category</label>
                          <select
                            value={selectedCategory}
                            onChange={(e) => setSelectedCategory(e.target.value)}
                            aria-label="Food category"
                            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                            aria-label="Cooking method"
                            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          >
                            <option value="">All methods</option>
                            {filters.methods.map((m) => (
                              <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                      {(selectedCategory || selectedMethod) && (
                        <button
                          onClick={() => { setSelectedCategory(''); setSelectedMethod(''); }}
                          className="text-xs text-blue-600 hover:text-blue-800"
                        >
                          Clear filters
                        </button>
                      )}
                    </div>
                  )}

                  {/* Food Search */}
                  <div className="space-y-3">
                    <div className="relative">
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search for foods (e.g., salmon, bread, apple)..."
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    {searchIsLoading && searchQuery && (
                      <div className="text-sm text-gray-500">Searching...</div>
                    )}
                    {/* AI-MATCH-1: opt-in LLM ranker beside the basic search. */}
                    <AIEnhancedSearch
                      query={searchQuery}
                      userType={userType}
                      accent="green"
                      onSelect={(food) => addFood({
                        FoodID: food.food_id,
                        FoodDescription: food.food_description,
                      })}
                    />
                    {/* AI-MATCH-1: homemade-dish workflow */}
                    <button
                      type="button"
                      onClick={() => setRecipeModalOpen(true)}
                      className="inline-flex items-center gap-1.5 text-sm text-green-700 hover:text-green-900 hover:underline"
                    >
                      🍳 Score a homemade dish (decompose into CNF ingredients)
                    </button>
                    {/* AI-MATCH-2 (2026-05-24): 24-h dietary recall — HENI sums healthy-life
                        impact across the day, so the daily aggregate is a more meaningful unit. */}
                    <a
                      href="/recall-24h?then=heni"
                      className="inline-flex items-center gap-1.5 text-sm text-green-700 hover:text-green-900 hover:underline"
                    >
                      🍽️ Build a 24-h recall instead (six-occasion daily eating)
                    </a>

                    {searchResults.length > 0 && (
                      <div className="bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto">
                        {searchResults.map((food) => (
                          <button
                            key={food.FoodID}
                            onClick={() => addFood(food)}
                            className="w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                          >
                            <div className="font-medium text-gray-900">{food.FoodDescription}</div>
                            <div className="text-sm text-gray-500">ID: {food.FoodID}</div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Selected Foods */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-medium text-gray-700">Selected Foods ({selectedFoods.length})</h3>
                      {selectedFoods.length > 0 && (
                        <button
                          onClick={resetCalculation}
                          className="text-xs text-gray-500 hover:text-gray-700"
                        >
                          Clear all
                        </button>
                      )}
                    </div>

                    {selectedFoods.length === 0 ? (
                      <div className="text-center py-6 text-gray-500">
                        <Info className="w-10 h-10 mx-auto mb-2 opacity-50" />
                        <p>No foods selected yet.</p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {selectedFoods.map((food) => (
                          <div key={food.FoodID} className="p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-center justify-between mb-2">
                              <div>
                                <div className="font-medium text-gray-900">{food.FoodDescription}</div>
                                <div className="text-sm text-gray-500">ID: {food.FoodID}</div>
                              </div>
                              <button
                                onClick={() => removeFood(food.FoodID)}
                                className="text-red-500 hover:text-red-700 p-1"
                                aria-label={`Remove ${food.FoodDescription}`}
                                title={`Remove ${food.FoodDescription}`}
                              >
                                <Trash2 className="w-5 h-5" />
                              </button>
                            </div>
                            <div className="flex items-center gap-2">
                              <label className="text-sm font-medium text-gray-600">Amount:</label>
                              <input
                                type="number"
                                min="0.1"
                                step="0.1"
                                value={food.amount}
                                onChange={(e) => updateFoodAmount(food.FoodID, parseFloat(e.target.value) || 0.1)}
                                aria-label="Amount in grams"
                                placeholder="Amount (g)"
                                title="Amount in grams"
                                className="w-24 px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                              />
                              <span className="text-sm text-gray-500">grams</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Calculate Button */}
                  <button
                    onClick={calculateHENI}
                    disabled={loading || selectedFoods.length === 0}
                    className="w-full mt-2 inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
                  >
                    <Calculator className="mr-2 w-5 h-5" />
                    {loading ? 'Calculating...' : 'Calculate HENI Score'}
                  </button>

                  {/* Error */}
                  {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                      <div className="flex items-center">
                        <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
                        <div className="text-sm text-red-700">{error}</div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Quick Results Preview */}
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Heart className="h-5 w-5" />
                    Health Impact Preview
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {error && (
                    <Alert className="mb-4 border-red-200 bg-red-50">
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                      <AlertDescription className="text-red-700">{error}</AlertDescription>
                    </Alert>
                  )}

                  {heniResults ? (
                    <HENIResultsCard results={heniResults} compact userType={userType} />
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <Heart className="h-12 w-12 mx-auto mb-2 opacity-50" />
                      <p>Add ingredients and calculate to see your health impact</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Analysis Tab */}
          <TabsContent value="analysis" className="space-y-6">
            {heniResults && (
              <>
                {/* Audience-aware explanations (AUDIENCE-CODE-1) */}
                <ExplanationsPanel
                  explanations={(heniResults as unknown as { data?: { data?: { explanations?: ExplanationsBlock } } })
                    ?.data?.data?.explanations}
                  userType={userType}
                  accent="text-green-700"
                />
                {/* Math-leaking detailed visualisations: researcher + policy only.
                    The disease-burden chart, μDALY values and risk-factor breakdowns
                    expose per-DRF coefficients that Stylianou 2021 explicitly framed
                    for expert audiences — hidden from individual view. */}
                {userType === 'individual' ? null : (
                <>
                {/* Comprehensive Results */}
                <div className="grid lg:grid-cols-5 gap-6 mb-6">
                  <Card className="lg:col-span-3 shadow-lg">
                    <CardHeader className="flex flex-row items-center justify-between">
                      <CardTitle>Detailed HENI Analysis</CardTitle>
                      <div className="flex gap-2">
                        <div className="relative">
                          <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={() => setShowExportDropdown(!showExportDropdown)}
                            className="flex items-center gap-2"
                          >
                            <Download className="h-4 w-4" />
                            Export
                            <ChevronDown className="h-3 w-3" />
                          </Button>
                          
                          {showExportDropdown && (
                            <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-10 min-w-[140px]">
                              <button
                                onClick={() => {
                                  exportResultsJSON();
                                  setShowExportDropdown(false);
                                }}
                                className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center gap-2"
                              >
                                <Download className="h-4 w-4" />
                                JSON Data
                              </button>
                              <button
                                onClick={() => {
                                  exportResultsPDF();
                                  setShowExportDropdown(false);
                                }}
                                className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center gap-2"
                              >
                                <Download className="h-4 w-4" />
                                PDF Report
                              </button>
                            </div>
                          )}
                        </div>
                        <Button variant="outline" size="sm">
                          <Share2 className="h-4 w-4 mr-2" />
                          Share
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <HENIResultsCard results={heniResults} detailed userType={userType} />
                    </CardContent>
                  </Card>

                  <Card className="lg:col-span-2 shadow-lg">
                    <CardHeader>
                      <CardTitle>Health Impact Visualization</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <HealthImpactVisualization results={heniResults} />
                    </CardContent>
                  </Card>
                </div>

                {/* Risk Factors and Disease Impact */}
                <div className="grid lg:grid-cols-2 gap-6">
                  <Card className="shadow-lg">
                    <CardHeader>
                      <CardTitle>Risk Factor Breakdown</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <RiskFactorBreakdown results={heniResults} />
                    </CardContent>
                  </Card>

                  <Card className="shadow-lg">
                    <CardHeader>
                      <CardTitle>Disease Impact Analysis</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <DiseaseImpactChart results={heniResults} />
                    </CardContent>
                  </Card>
                </div>
                </>
                )}
              </>
            )}
          </TabsContent>

          {/* Insights Tab */}
          <TabsContent value="insights" className="space-y-6">
            {heniResults && (
              <div className="grid gap-6">
                {/* Health Recommendations */}
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5" />
                      Personalized Health Recommendations
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {(() => {
                      const analysis = heniResults?.data;
                      return (
                        <div className="space-y-4">
                          {analysis?.health_impact?.health_impact_minutes > 0 ? (
                        <Alert className="border-green-200 bg-green-50">
                          <TrendingUp className="h-4 w-4 text-green-600" />
                          <AlertDescription className="text-green-800">
                            <strong>Great choice!</strong> This meal adds approximately{' '}
                              <strong>{analysis.health_impact.health_impact_minutes.toFixed(2)}</strong> minutes
                            to your healthy life expectancy.
                          </AlertDescription>
                        </Alert>
                      ) : (
                        <Alert className="border-amber-200 bg-amber-50">
                          <AlertTriangle className="h-4 w-4 text-amber-600" />
                          <AlertDescription className="text-amber-800">
                            This meal may reduce healthy life expectancy by approximately{' '}
                              <strong>{Math.abs(analysis?.health_impact?.health_impact_minutes || 0).toFixed(2)}</strong> minutes.
                            Consider healthier alternatives.
                          </AlertDescription>
                        </Alert>
                      )}

                      {/* Specific Recommendations.
                          FIX (audit bug #3 sign flip + #6 individual-mode math
                          suppression + follow-up): under HENI sign convention
                          v < 0 = benefit (keep), v > 0 = harm (reduce).
                          We merge food_group + nutrient contributions because
                          many CNF foods emit only nutrient contributions (e.g.
                          Beef stew canned 4964) — the food-group-only filter
                          left both lists empty. The μDALY badges are
                          researcher / policy only — individuals see plain
                          factor names, since μDALY is an expert unit per
                          Stylianou 2021. */}
                      {(() => {
                        const merged: Record<string, number> = {
                          ...(analysis?.component_breakdown?.food_group_contributions || {}),
                          ...(analysis?.component_breakdown?.nutrient_contributions || {}),
                        };
                        for (const k of Object.keys(merged)) {
                          if (k.startsWith('__') || merged[k] === 0) delete merged[k];
                        }
                        const allEntries = Object.entries(merged) as Array<[string, number]>;
                        const keepList = allEntries
                          .filter(([, v]) => v < 0)
                          .sort(([, a], [, b]) => a - b)
                          .slice(0, 3);
                        const reduceList = allEntries
                          .filter(([, v]) => v > 0)
                          .sort(([, a], [, b]) => b - a)
                          .slice(0, 3);
                        return (
                          <div className="grid md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <h4 className="font-semibold text-green-700">✓ Keep These Elements</h4>
                              {keepList.length === 0 && (
                                <div className="text-xs text-gray-500 italic">No beneficial μDALY contributors in this meal.</div>
                              )}
                              {keepList.map(([factor, value]) => (
                                <div key={factor} className="flex justify-between text-sm">
                                  <span className="capitalize">{factor.replace('_', ' ')}</span>
                                  {userType !== 'individual' && (
                                    <Badge variant="secondary" className="text-green-700">
                                      {value.toFixed(1)} μDALY
                                    </Badge>
                                  )}
                                </div>
                              ))}
                            </div>

                            <div className="space-y-2">
                              <h4 className="font-semibold text-amber-700">⚠ Consider Reducing</h4>
                              {reduceList.length === 0 && (
                                <div className="text-xs text-gray-500 italic">No harmful μDALY contributors in this meal.</div>
                              )}
                              {reduceList.map(([factor, value]) => (
                                <div key={factor} className="flex justify-between text-sm">
                                  <span className="capitalize">{factor.replace('_', ' ')}</span>
                                  {userType !== 'individual' && (
                                    <Badge variant="destructive" className="text-amber-700">
                                      +{value.toFixed(1)} μDALY
                                    </Badge>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      })()}
                        </div>
                      );
                    })()}
                  </CardContent>
                </Card>

                {/* Scientific Context — researcher / policy only.
                    FIX (audit bug #4 + #6): previous copy hardcoded
                    "Cardiovascular diseases (65 %)", "Various cancers (20 %)",
                    "Metabolic disorders (15 %)" — inconsistent with the
                    DiseaseImpactChart constants (45/25/20) and with no
                    provenance against Stylianou 2021. The 0.5256 conversion
                    constant + per-bucket counts are also expert-only per
                    AUDIENCE-CODE-1. The block is gated behind userType. */}
                {userType !== 'individual' && (
                  <Card className="shadow-lg">
                    <CardHeader>
                      <CardTitle>Scientific Context</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="prose prose-sm max-w-none">
                        <p className="text-gray-600 mb-4">
                          HENI is calculated using the Global Burden of Disease 2016 disease-rate
                          functions per Stylianou et al. 2021 (Nature Food). Health impact is
                          expressed in <strong>micro-DALYs (μDALYs)</strong>; the kernel emits
                          positive μDALY for harmful net contributions and negative μDALY for
                          beneficial ones, converted to minutes of healthy life via
                          MINUTES_PER_UDALY = −0.5256 (Stylianou SI p. 98). Per-disease
                          attribution for this meal is shown in the Analysis tab&apos;s Disease
                          Impact panel and is computed by the kernel — no global percentages
                          are assumed.
                        </p>

                        <div className="grid md:grid-cols-2 gap-4 text-sm">
                          <div>
                            <h5 className="font-semibold mb-2">Risk factors considered (16 total)</h5>
                            <ul className="space-y-1 text-gray-600">
                              <li>• 10 food-group exposures (fruits, vegetables, whole grains, nuts/seeds, milk, red meat, processed meat, SSB, ...)</li>
                              <li>• 6 nutrient exposures (omega-3, fibre, calcium, PUFA, trans-fat, sodium)</li>
                            </ul>
                          </div>

                          <div>
                            <h5 className="font-semibold mb-2">Disease buckets (per Stylianou SI Table 1)</h5>
                            <ul className="space-y-1 text-gray-600">
                              <li>• Cardiovascular diseases</li>
                              <li>• Colorectal cancer / Other cancers</li>
                              <li>• Metabolic disorders</li>
                              <li>• All-cause mortality (residual)</li>
                            </ul>
                          </div>
                        </div>

                        {heniResults.data?.risk_factor_analysis?.warnings?.length > 0 && (
                          <Alert className="mt-4 border-blue-200 bg-blue-50">
                            <Info className="h-4 w-4 text-blue-600" />
                            <AlertDescription className="text-blue-800">
                              <strong>Note:</strong> Some risk factors in your meal exceed typical ranges
                              used in epidemiological studies. Results should be interpreted with caution.
                            </AlertDescription>
                          </Alert>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* AI-MATCH-1: recipe decomposer modal. Apply pushes the chosen
          ingredients into selectedFoods at their decomposed masses. */}
      <RecipeDecomposerModal
        open={recipeModalOpen}
        onClose={() => setRecipeModalOpen(false)}
        userType={userType}
        accent="green"
        onApply={(ingredients) => {
          const additions: SelectedFood[] = ingredients
            .filter(i => !selectedFoods.some(f => f.FoodID === i.food_id))
            .map(i => ({
              FoodID: i.food_id,
              FoodDescription: i.food_description,
              amount: i.mass_g,
              unit: 'g',
            }));
          setSelectedFoods([...selectedFoods, ...additions]);
        }}
      />
    </div>
  );
};

export default HENICalculator;