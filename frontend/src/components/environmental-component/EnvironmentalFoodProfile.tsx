'use client';
/**
 * Environmental Food Profile - Detailed Individual Food Environmental Analysis
 * Comprehensive profile with LCA, monetization, sustainability, and comparative context
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription } from '../ui/alert';
import {
  Leaf,
  Search,
  Globe,
  Droplets,
  TreePine,
  DollarSign,
  BarChart3,
  Users,
  Info,
  Download,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  AlertTriangle,
  Factory,
  Zap,
  Apple,
  RefreshCw,
} from 'lucide-react';
import { 
  EnvironmentalImpactApiService, 
  CNFApiService, 
  type FoodEnvironmentalProfile,
  type FilterOptions 
} from '../../lib/api';

interface SearchResult {
  FoodID: number;
  FoodDescription: string;
  FoodCode?: string;
}

type UserType = 'individual' | 'researcher' | 'policy';

const EnvironmentalFoodProfile = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [selectedFood, setSelectedFood] = useState<SearchResult | null>(null);
  const [amount, setAmount] = useState(100);
  const [profileResults, setProfileResults] = useState<FoodEnvironmentalProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchIsLoading, setSearchIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [filters, setFilters] = useState<FilterOptions | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedMethod, setSelectedMethod] = useState<string>('');
  const [userType, setUserType] = useState<UserType>('individual');

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

  // Debounced search
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.trim().length < 2) {
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

  const selectFood = (food: SearchResult) => {
    setSelectedFood(food);
    setSearchQuery('');
    setSearchResults([]);
    setError('');
  };

  const analyzeFoodProfile = async () => {
    if (!selectedFood) {
      setError('Please select a food to analyze');
      return;
    }

    if (amount <= 0) {
      setError('Amount must be greater than 0');
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      const response = await EnvironmentalImpactApiService.getFoodEnvironmentalProfile(
        selectedFood.FoodID, 
        amount, 
        userType
      );
      setProfileResults(response);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { message?: string; error?: string } } };
      setError(e?.response?.data?.error || e?.response?.data?.message || 'Failed to analyze food profile');
      console.warn('Food profile error:', e?.response?.data || err);
    } finally {
      setLoading(false);
    }
  };

  const resetProfile = () => {
    setSelectedFood(null);
    setProfileResults(null);
    setAmount(100);
    setError('');
    setSearchQuery('');
    setSearchResults([]);
  };

  const exportProfile = () => {
    if (!profileResults) return;
    
    const exportData = {
      timestamp: new Date().toISOString(),
      user_type: userType,
      amount_analyzed: amount,
      profile_results: profileResults
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `food-environmental-profile-${selectedFood?.FoodID}-${new Date().toISOString().split('T')[0]}.json`;
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

  const getSustainabilityInfo = (score: number) => {
    if (score >= 80) return { color: 'text-green-600', bgColor: 'bg-green-100', icon: CheckCircle, label: 'Excellent' };
    if (score >= 60) return { color: 'text-blue-600', bgColor: 'bg-blue-100', icon: TrendingUp, label: 'Good' };
    if (score >= 40) return { color: 'text-yellow-600', bgColor: 'bg-yellow-100', icon: TrendingUp, label: 'Fair' };
    if (score >= 20) return { color: 'text-orange-600', bgColor: 'bg-orange-100', icon: TrendingDown, label: 'Poor' };
    return { color: 'text-red-600', bgColor: 'bg-red-100', icon: AlertTriangle, label: 'Very Poor' };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-emerald-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Search className="h-8 w-8 text-green-500 mr-3" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              Food Environmental Profile
            </h1>
          </div>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Get detailed environmental impact analysis for individual foods using comprehensive LCA methodology 
            with Canadian-specific factors and economic valuation
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
                <Search className="h-5 w-5" />
                Select Food to Analyze
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Search Filters */}
              {filters && (
                <div className="space-y-4 border-b pb-4">
                  <h3 className="text-sm font-medium text-gray-700">Search Filters</h3>
                  <div className="space-y-3">
                    <div>
                      <label htmlFor="food-category-select" className="block text-xs font-medium text-gray-600 mb-1">Food Category</label>
                      <select
                        id="food-category-select"
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                      >
                        <option value="">All categories</option>
                        {filters.categories.map((c) => (
                          <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label htmlFor="cooking-method-select" className="block text-xs font-medium text-gray-600 mb-1">Cooking Method</label>
                      <select
                        id="cooking-method-select"
                        value={selectedMethod}
                        onChange={(e) => setSelectedMethod(e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
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
                      className="text-xs text-green-600 hover:text-green-800"
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
                    placeholder="Search for a food to profile..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  />
                </div>
                {searchIsLoading && searchQuery && (
                  <div className="text-sm text-gray-500">Searching...</div>
                )}

                {searchResults.length > 0 && (
                  <div className="bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto">
                    {searchResults.map((food) => (
                      <button
                        key={food.FoodID}
                        onClick={() => selectFood(food)}
                        className="w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                      >
                        <div className="font-medium text-gray-900">{food.FoodDescription}</div>
                        <div className="text-sm text-gray-500">ID: {food.FoodID}</div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Selected Food */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">Selected Food</h3>
                {selectedFood ? (
                  <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="font-medium text-green-900">{selectedFood.FoodDescription}</div>
                        <div className="text-sm text-green-700">ID: {selectedFood.FoodID}</div>
                      </div>
                      <button
                        onClick={resetProfile}
                        className="text-green-600 hover:text-green-800 p-1"
                        aria-label="Reset selection"
                        title="Reset selection"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="flex items-center gap-2">
                      <label htmlFor="amount-input" className="text-sm font-medium text-green-700">Amount:</label>
                      <input
                        id="amount-input"
                        type="number"
                        min="0.1"
                        step="0.1"
                        value={amount}
                        onChange={(e) => setAmount(parseFloat(e.target.value) || 0.1)}
                        className="w-24 px-2 py-1 border border-green-300 rounded text-sm focus:ring-2 focus:ring-green-500"
                        placeholder="Amount in grams"
                      />
                      <span className="text-sm text-green-700">grams</span>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-6 text-gray-500">
                    <Search className="w-10 h-10 mx-auto mb-2 opacity-50" />
                    <p>No food selected yet.</p>
                    <p className="text-xs mt-1">Search and select a food to analyze.</p>
                  </div>
                )}
              </div>

              {/* Analyze Button */}
              <button
                onClick={analyzeFoodProfile}
                disabled={loading || !selectedFood}
                className="w-full mt-2 inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                <Leaf className="mr-2 w-5 h-5" />
                {loading ? 'Analyzing...' : 'Analyze Environmental Profile'}
              </button>

              {/* Error Display */}
              {error && (
                <Alert className="border-red-200 bg-red-50">
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                  <AlertDescription className="text-red-700">{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Profile Results */}
          <div className="lg:col-span-2 space-y-6">
            {profileResults ? (
              <>
                {/* Header with Export */}
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <Leaf className="h-5 w-5" />
                      Environmental Profile: {profileResults.data.food_details.food_name}
                    </CardTitle>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={exportProfile}>
                        <Download className="h-4 w-4 mr-2" />
                        Export
                      </Button>
                      <Button variant="outline" size="sm" onClick={resetProfile}>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        New Analysis
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {/* Food Basic Info */}
                    <div className="bg-gray-50 p-4 rounded-lg mb-6">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Food Group:</span>
                          <div className="font-semibold">{profileResults.data.food_details.food_group}</div>
                        </div>
                        <div>
                          <span className="text-gray-600">Amount Analyzed:</span>
                          <div className="font-semibold">{profileResults.data.food_details.amount_analyzed_g}g</div>
                        </div>
                        <div>
                          <span className="text-gray-600">Food ID:</span>
                          <div className="font-semibold">{profileResults.data.food_details.food_id}</div>
                        </div>
                        <div>
                          <span className="text-gray-600">Analysis Type:</span>
                          <div className="font-semibold capitalize">{userType}</div>
                        </div>
                      </div>
                    </div>

                    {/* User-Tailored Explanation */}
                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 mb-6">
                      <h4 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                        {getUserTypeIcon(userType)}
                        {userType.charAt(0).toUpperCase() + userType.slice(1)} Analysis
                      </h4>
                      <p className="text-blue-800 mb-3">{profileResults.data.user_explanation.summary}</p>
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <h5 className="font-medium text-blue-900 mb-2">Key Findings:</h5>
                          <ul className="space-y-1 text-sm text-blue-800">
                            {profileResults.data.user_explanation.key_findings.slice(0, 3).map((finding, index) => (
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
                            {profileResults.data.user_explanation.recommendations.slice(0, 3).map((rec, index) => (
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

                {/* Environmental Impacts */}
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Globe className="h-5 w-5" />
                      Environmental Impact Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {/* Key Environmental Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                      <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                        <div className="flex items-center gap-2 mb-2">
                          <Globe className="h-5 w-5 text-red-600" />
                          <span className="font-medium text-red-900">Climate Impact</span>
                        </div>
                        <div className="text-2xl font-bold text-red-900">
                          {formatImpactValue(profileResults.data.environmental_analysis.lca_results['Global warming'], 'kg CO₂-eq')}
                        </div>
                      </div>

                      <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                        <div className="flex items-center gap-2 mb-2">
                          <Droplets className="h-5 w-5 text-blue-600" />
                          <span className="font-medium text-blue-900">Water Impact</span>
                        </div>
                        <div className="text-2xl font-bold text-blue-900">
                          {formatImpactValue(profileResults.data.environmental_analysis.lca_results['Water consumption'], 'm³')}
                        </div>
                      </div>

                      <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                        <div className="flex items-center gap-2 mb-2">
                          <TreePine className="h-5 w-5 text-green-600" />
                          <span className="font-medium text-green-900">Land Impact</span>
                        </div>
                        <div className="text-2xl font-bold text-green-900">
                          {formatImpactValue(profileResults.data.environmental_analysis.lca_results['Land use'], 'm²a crop-eq')}
                        </div>
                      </div>

                      <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                        <div className="flex items-center gap-2 mb-2">
                          <DollarSign className="h-5 w-5 text-yellow-600" />
                          <span className="font-medium text-yellow-900">Economic Cost</span>
                        </div>
                        <div className="text-2xl font-bold text-yellow-900">
                          CAD ${profileResults.data.environmental_analysis.monetization.total_cost.toFixed(3)}
                        </div>
                      </div>
                    </div>

                    {/* Sustainability Assessment */}
                    <div className="mb-6">
                      <h4 className="font-semibold text-gray-900 mb-4">Sustainability Assessment</h4>
                      <div className="space-y-4">
                        {['overall_sustainability_score', 'environmental_score', 'nutritional_score', 'processing_score'].map((scoreType) => {
                          const score = profileResults.data.environmental_analysis.sustainability_score[scoreType as keyof typeof profileResults.data.environmental_analysis.sustainability_score] as number;
                          const sustainabilityInfo = getSustainabilityInfo(score);
                          const SustainabilityIcon = sustainabilityInfo.icon;
                          
                          const labels = {
                            overall_sustainability_score: 'Overall Sustainability',
                            environmental_score: 'Environmental Performance',
                            nutritional_score: 'Nutritional Quality',
                            processing_score: 'Processing Level'
                          };

                          const icons = {
                            overall_sustainability_score: Leaf,
                            environmental_score: Globe,
                            nutritional_score: Apple,
                            processing_score: Factory
                          };

                          const ScoreIcon = icons[scoreType as keyof typeof icons];

                          return (
                            <div key={scoreType} className={`p-3 rounded-lg ${sustainabilityInfo.bgColor} border border-gray-200`}>
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                  <ScoreIcon className={`h-4 w-4 ${sustainabilityInfo.color}`} />
                                  <span className="font-medium">{labels[scoreType as keyof typeof labels]}</span>
                                  <SustainabilityIcon className={`h-4 w-4 ${sustainabilityInfo.color}`} />
                                </div>
                                <Badge className={sustainabilityInfo.color}>
                                  {sustainabilityInfo.label}
                                </Badge>
                              </div>
                              <div className="flex items-center gap-3">
                                <Progress value={score} className="flex-1" />
                                <span className={`font-bold ${sustainabilityInfo.color}`}>
                                  {score.toFixed(0)}/100
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Endpoint Impacts */}
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-4">Endpoint Impact Categories</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                          <div className="flex items-center gap-2 mb-2">
                            <Zap className="h-5 w-5 text-red-600" />
                            <span className="font-medium text-red-900">Human Health</span>
                          </div>
                          <div className="text-lg font-bold text-red-900">
                            {profileResults.data.environmental_analysis.endpoint_impacts['Human Health'].toFixed(6)} DALY
                          </div>
                          <div className="text-sm text-red-700 mt-1">
                            Disability Adjusted Life Years
                          </div>
                        </div>

                        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                          <div className="flex items-center gap-2 mb-2">
                            <TreePine className="h-5 w-5 text-green-600" />
                            <span className="font-medium text-green-900">Ecosystem Quality</span>
                          </div>
                          <div className="text-lg font-bold text-green-900">
                            {profileResults.data.environmental_analysis.endpoint_impacts['Ecosystems'].toFixed(6)} sp.year
                          </div>
                          <div className="text-sm text-green-700 mt-1">
                            Species Extinction Years
                          </div>
                        </div>

                        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                          <div className="flex items-center gap-2 mb-2">
                            <DollarSign className="h-5 w-5 text-blue-600" />
                            <span className="font-medium text-blue-900">Resource Scarcity</span>
                          </div>
                          <div className="text-lg font-bold text-blue-900">
                            ${profileResults.data.environmental_analysis.endpoint_impacts['Resources'].toFixed(3)}
                          </div>
                          <div className="text-sm text-blue-700 mt-1">
                            Resource Depletion Cost
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Comparative Context */}
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="h-5 w-5" />
                      Comparative Context
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {/* Food Group Percentile */}
                    <div className="mb-6">
                      <h4 className="font-semibold text-gray-900 mb-3">Food Group Performance</h4>
                      <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-indigo-900 font-medium">
                            Percentile within {profileResults.data.food_details.food_group}
                          </span>
                          <Badge variant="outline" className="text-indigo-700">
                            {profileResults.data.comparative_context.food_group_percentile.toFixed(0)}th percentile
                          </Badge>
                        </div>
                        <Progress value={profileResults.data.comparative_context.food_group_percentile} className="mb-2" />
                        <div className="text-sm text-indigo-800">
                          {profileResults.data.comparative_context.food_group_percentile >= 75 
                            ? 'Performs better than most foods in this group'
                            : profileResults.data.comparative_context.food_group_percentile >= 50
                            ? 'Average performance within this food group'
                            : 'Below average performance within this food group'}
                        </div>
                      </div>
                    </div>

                    {/* Similar Foods */}
                    <div className="mb-6">
                      <h4 className="font-semibold text-gray-900 mb-3">Similar Foods Comparison</h4>
                      <div className="space-y-3">
                        {profileResults.data.comparative_context.similar_foods.slice(0, 3).map((similarFood, index) => (
                          <div key={index} className="bg-gray-50 p-3 rounded-lg border border-gray-200">
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-gray-900">{similarFood.name}</span>
                              <div className="flex items-center gap-3 text-sm">
                                <div className="text-center">
                                  <div className="text-gray-600">Env Cost</div>
                                  <div className="font-bold">CAD ${similarFood.environmental_cost.toFixed(3)}</div>
                                </div>
                                <div className="text-center">
                                  <div className="text-gray-600">Carbon</div>
                                  <div className="font-bold">{formatImpactValue(similarFood.carbon_footprint, 'kg CO₂-eq')}</div>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Reference Comparisons */}
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">Reference Comparisons</h4>
                      <div className="space-y-3">
                        {Object.entries(profileResults.data.comparative_context.reference_comparisons).map(([refType, comparison]) => (
                          <div key={refType} className="bg-white p-3 rounded-lg border border-gray-200">
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-gray-900 capitalize">
                                vs {refType.replace('_', ' ')} Meal
                              </span>
                              <div className="flex items-center gap-2">
                                <Badge variant={comparison.ratio <= 1 ? 'default' : 'destructive'}>
                                  {comparison.ratio.toFixed(2)}x
                                </Badge>
                              </div>
                            </div>
                            <div className="text-sm text-gray-600 mt-1">
                              {comparison.interpretation}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card className="shadow-lg">
                <CardContent className="text-center py-12">
                  <Search className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                  <h3 className="text-lg font-semibold text-gray-700 mb-2">Ready to Analyze Food Profile</h3>
                  <p className="text-gray-600">
                    Search and select a food from the panel, then click &quot;Analyze Environmental Profile&quot; to get 
                    comprehensive environmental impact analysis with personalized insights and comparative context.
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

export default EnvironmentalFoodProfile;