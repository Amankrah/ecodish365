/**
 * HENI Food Profile Analysis Component
 * Advanced analysis interface designed for researchers and nutrition professionals
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
import {
  Search,
  Download,
  BarChart3,
  Users,
  TrendingUp,
  Heart,
  Shield,
  AlertTriangle,
  Info,
  Database,
  Microscope,
  Target,
  Activity,
  Share2,
  ChevronDown
} from 'lucide-react';
import { HENIResultsCard } from './HENIResultsCard';
import { RiskFactorBreakdown } from './RiskFactorBreakdown';
import { DiseaseImpactChart } from './DiseaseImpactChart';
import { HealthImpactVisualization } from './HealthImpactVisualization';
import { HENIApiService, CNFApiService, type FilterOptions, type HENIFoodProfile } from '../../lib/api';

const HENIFoodProfileAnalysis = () => {
  const [foodId, setFoodId] = useState<string>('');
  const [amount, setAmount] = useState<number>(100);
  const [profileData, setProfileData] = useState<HENIFoodProfile['data'] | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState('overview');
  const [showExportDropdown, setShowExportDropdown] = useState(false);

  // CNF search and filters (align with calculator)
  const [filters, setFilters] = useState<FilterOptions | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedMethod, setSelectedMethod] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<Array<{ FoodID: number; FoodDescription: string; FoodCode?: string }>>([]);
  const [searchIsLoading, setSearchIsLoading] = useState<boolean>(false);

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

  // Close export dropdown on outside click
  useEffect(() => {
    const handle = (e: MouseEvent) => {
      if (showExportDropdown && !(e.target as Element).closest('.export-menu-anchor')) {
        setShowExportDropdown(false);
      }
    };
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, [showExportDropdown]);

  // Analyze food profile
  const analyzeFoodProfile = async () => {
    if (!foodId.trim()) {
      setError('Please enter a food ID');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const resp = await HENIApiService.getFoodHENIProfile(parseInt(foodId, 10), amount);
      if (resp?.success && resp.data) {
        setProfileData(resp.data);
      } else {
        setError('Failed to analyze food profile');
      }
    } catch {
      setError('Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  // Export profile as JSON
  const exportProfileJSON = () => {
    if (!profileData) return;
    const exportPayload = {
      timestamp: new Date().toISOString(),
      input: { food_id: foodId, amount_g: amount },
      profile: profileData,
    };
    const blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `heni-food-profile-${foodId}-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Export simple text report (placeholder for PDF)
  const exportProfileReport = () => {
    if (!profileData) return;
    const a = profileData.heni_analysis;
    const lines = [
      `HENI FOOD PROFILE REPORT`,
      `Food: ${profileData.food_details?.food_name || 'N/A'} (ID ${foodId})`,
      `Amount analyzed: ${amount} g`,
      ``,
      `HENI Scores:`,
      `  Total: ${a.heni_scores?.total_heni_score?.toFixed(2) || '0.00'} μDALY`,
      `  Per 100 kcal: ${a.heni_scores?.heni_per_100_kcal?.toFixed(2) || '0.00'} μDALY`,
      `  Per 100 g: ${a.heni_scores?.heni_per_100_grams?.toFixed(2) || '0.00'} μDALY`,
      ``,
      `Health Impact:`,
      `  Minutes: ${a.health_impact?.health_impact_minutes?.toFixed(2) || '0.00'}`,
      `  Description: ${a.health_impact?.description || 'N/A'}`,
      ``,
      `Top Risk Factors:`,
      ...Object.entries(a.risk_factor_analysis?.risk_factors || {})
        .sort(([,x],[,y]) => Math.abs(Number(y)) - Math.abs(Number(x)))
        .slice(0,5)
        .map(([k,v]) => `  - ${k.replace('_',' ')}: ${Number(v).toFixed(2)} μDALY`),
    ].join('\n');
    const blob = new Blob([lines], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `heni-food-profile-${foodId}-${new Date().toISOString().split('T')[0]}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // CNF search handler (debounced with enhanced -> fallback)
  useEffect(() => {
    const query = searchQuery.trim();
    if (!query) {
      setSearchResults([]);
      return;
    }

    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setSearchIsLoading(true);
      try {
        try {
          const enhanced = await CNFApiService.searchFoodsEnhanced({
            query,
            limit: 50,
            category: selectedCategory || undefined,
            method: selectedMethod || undefined,
          });
          setSearchResults(
            (enhanced.results || []).map((r) => ({
              FoodID: r.FoodID,
              FoodDescription: r.FoodDescription,
              FoodCode: r.FoodCode,
            }))
          );
        } catch {
          const basic = await CNFApiService.searchFoods(query, 50);
          setSearchResults(
            (basic.results || []).map((r) => ({
              FoodID: r.FoodID,
              FoodDescription: r.FoodDescription,
              FoodCode: r.FoodCode,
            }))
          );
        }
      } catch (err) {
        console.error('Search error:', err);
        setSearchResults([]);
      } finally {
        setSearchIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery, selectedCategory, selectedMethod]);

  // Export detailed report
  const exportDetailedReport = () => {
    if (!profileData) return;
    
    const reportData = {
      ...profileData,
      analysis_timestamp: new Date().toISOString(),
      report_type: 'Comprehensive HENI Food Profile Analysis'
    };
    
    const blob = new Blob([JSON.stringify(reportData, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `heni-food-profile-${foodId}-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Microscope className="h-8 w-8 text-blue-500 mr-3" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              HENI Food Profile Analysis
            </h1>
          </div>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Comprehensive health impact analysis for individual foods using evidence-based 
            DALY methodology. Designed for researchers, nutrition professionals, and policy makers.
          </p>
        </div>

        {/* Sidebar + Content Grid */}
        <div className="grid lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1 lg:sticky lg:top-24 self-start">
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Search className="h-5 w-5" />
                  Food Analysis Parameters
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Food (CNF)</label>
                    {filters && (
                      <div className="grid grid-cols-2 gap-2 mb-2">
                        <select
                          value={selectedCategory}
                          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedCategory(e.target.value)}
                          aria-label="Food category"
                          className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm"
                        >
                          <option value="">All categories</option>
                          {filters.categories.map((c) => (
                            <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                          ))}
                        </select>
                        <select
                          value={selectedMethod}
                          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedMethod(e.target.value)}
                          aria-label="Cooking method"
                          className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm"
                        >
                          <option value="">All methods</option>
                          {filters.methods.map((m) => (
                            <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>
                          ))}
                        </select>
                      </div>
                    )}
                    <div className="space-y-2">
                      <Input
                        type="text"
                        placeholder="Search foods (e.g., salmon, bread, apple) or enter ID"
                        value={searchQuery}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
                      />
                      {searchIsLoading && searchQuery && (
                        <div className="text-xs text-gray-500">Searching...</div>
                      )}
                      {searchResults.length > 0 && (
                        <div className="bg-white border border-gray-200 rounded-md shadow-sm max-h-48 overflow-y-auto">
                          {searchResults.map((f) => (
                            <button
                              key={f.FoodID}
                              onClick={() => {
                                setFoodId(String(f.FoodID));
                                setSearchQuery('');
                                setSearchResults([]);
                              }}
                              className="w-full text-left px-3 py-2 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                            >
                              <div className="font-medium text-gray-900">{f.FoodDescription}</div>
                              <div className="text-xs text-gray-500">ID: {f.FoodID}</div>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Amount (grams)</label>
                    <Input
                      type="number"
                      value={amount}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAmount(parseInt(e.target.value) || 100)}
                      min="1"
                      max="10000"
                    />
                  </div>

                  <Button onClick={analyzeFoodProfile} disabled={loading} className="w-full bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600">
                    {loading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <BarChart3 className="h-4 w-4 mr-2" />
                        Analyze Food Profile
                      </>
                    )}
                  </Button>

                  {error && (
                    <Alert className="border-red-200 bg-red-50">
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                      <AlertDescription className="text-red-700">{error}</AlertDescription>
                    </Alert>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Content */}
          <div className="lg:col-span-3">
            {!profileData && (
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle>Food Profile Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-10 text-gray-500">
                    <Microscope className="h-12 w-12 mx-auto mb-3 opacity-60" />
                    <p>Select or search a food from the sidebar and click &quot;Analyze Food Profile&quot; to view results.</p>
                  </div>
                </CardContent>
              </Card>
            )}
            {profileData && (
              <Tabs value={selectedTab} onValueChange={setSelectedTab} defaultValue={selectedTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <Heart className="h-4 w-4" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="analysis" className="flex items-center gap-2" disabled={!profileData}>
                <TrendingUp className="h-4 w-4" />
                Analysis
              </TabsTrigger>
              <TabsTrigger value="insights" className="flex items-center gap-2" disabled={!profileData}>
                <Info className="h-4 w-4" />
                Insights
              </TabsTrigger>
              <TabsTrigger value="research" className="flex items-center gap-2">
                <Database className="h-4 w-4" />
                Research Data
              </TabsTrigger>
              <TabsTrigger value="population" className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                Population Impact
              </TabsTrigger>
              <TabsTrigger value="policy" className="flex items-center gap-2">
                <Target className="h-4 w-4" />
                Policy Insights
              </TabsTrigger>
              <TabsTrigger value="comparison" className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Benchmarks
              </TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              <div className="grid lg:grid-cols-3 gap-6">
                {/* Food Details */}
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Food Information</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <span className="text-sm text-gray-600">Name:</span>
                      <p className="font-medium">{profileData.food_details?.food_name || 'Unknown'}</p>
                    </div>
                    <div>
                      <span className="text-sm text-gray-600">Food Group:</span>
                      <Badge variant="secondary" className="ml-2">
                        {profileData.food_details?.food_group || 'Unclassified'}
                      </Badge>
                    </div>
                    <div>
                      <span className="text-sm text-gray-600">Amount Analyzed:</span>
                      <p className="font-medium">{amount}g</p>
                    </div>
                    <div>
                      <span className="text-sm text-gray-600">Food ID:</span>
                      <p className="font-medium">{foodId}</p>
                    </div>
                  </CardContent>
                </Card>

                {/* Quick Results */}
                <div className="lg:col-span-2">
                  <div className="flex items-center justify-between mb-3">
                    <div className="font-medium text-gray-700">Results</div>
                    <div className="relative export-menu-anchor">
                      <Button variant="outline" size="sm" onClick={() => setShowExportDropdown(!showExportDropdown)} className="flex items-center gap-2">
                        <Download className="h-4 w-4" />
                        Export
                        <ChevronDown className="h-3 w-3" />
                      </Button>
                      {showExportDropdown && (
                        <div className="absolute top-full right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-10 min-w-[140px]">
                          <button onClick={() => { exportProfileJSON(); setShowExportDropdown(false); }} className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center gap-2">
                            <Download className="h-4 w-4" /> JSON Data
                          </button>
                          <button onClick={() => { exportProfileReport(); setShowExportDropdown(false); }} className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center gap-2">
                            <Download className="h-4 w-4" /> Text Report
                          </button>
                          <button onClick={() => setShowExportDropdown(false)} className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center gap-2">
                            <Share2 className="h-4 w-4" /> Share
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                  <HENIResultsCard results={profileData.heni_analysis} />
                </div>
              </div>

              {/* Detailed Analysis */}
              <div className="grid lg:grid-cols-2 gap-6">
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Risk Factor Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <RiskFactorBreakdown results={profileData.heni_analysis} />
                  </CardContent>
                </Card>

                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Disease Impact Profile</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <DiseaseImpactChart results={profileData.heni_analysis} />
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Analysis Tab - mirrors calculator */}
            <TabsContent value="analysis" className="space-y-6">
              {profileData && (
                <>
                  <div className="grid lg:grid-cols-5 gap-6 mb-6">
                    <Card className="lg:col-span-3 shadow-lg">
                      <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>Detailed HENI Analysis</CardTitle>
                        <div className="relative export-menu-anchor">
                          <Button variant="outline" size="sm" onClick={() => setShowExportDropdown(!showExportDropdown)} className="flex items-center gap-2">
                            <Download className="h-4 w-4" /> Export <ChevronDown className="h-3 w-3" />
                          </Button>
                          {showExportDropdown && (
                            <div className="absolute top-full right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-10 min-w-[140px]">
                              <button onClick={() => { exportProfileJSON(); setShowExportDropdown(false); }} className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center gap-2">
                                <Download className="h-4 w-4" /> JSON Data
                              </button>
                              <button onClick={() => { exportProfileReport(); setShowExportDropdown(false); }} className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center gap-2">
                                <Download className="h-4 w-4" /> Text Report
                              </button>
                            </div>
                          )}
                        </div>
                      </CardHeader>
                      <CardContent>
                        <HENIResultsCard results={profileData.heni_analysis} detailed />
                      </CardContent>
                    </Card>

                    <Card className="lg:col-span-2 shadow-lg">
                      <CardHeader>
                        <CardTitle>Health Impact Visualization</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <HealthImpactVisualization results={profileData.heni_analysis} />
                      </CardContent>
                    </Card>
                  </div>

                  <div className="grid lg:grid-cols-2 gap-6">
                    <Card className="shadow-lg">
                      <CardHeader>
                        <CardTitle>Risk Factor Breakdown</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <RiskFactorBreakdown results={profileData.heni_analysis} />
                      </CardContent>
                    </Card>

                    <Card className="shadow-lg">
                      <CardHeader>
                        <CardTitle>Disease Impact Analysis</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <DiseaseImpactChart results={profileData.heni_analysis} />
                      </CardContent>
                    </Card>
                  </div>
                </>
              )}
            </TabsContent>

            {/* Insights Tab - mirrors calculator */}
            <TabsContent value="insights" className="space-y-6">
              {profileData && (
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5" />
                      Personalized Health Recommendations
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {(() => {
                      const analysis = profileData.heni_analysis;
                      return (
                        <div className="space-y-4">
                          {analysis?.health_impact?.health_impact_minutes > 0 ? (
                            <Alert className="border-green-200 bg-green-50">
                              <TrendingUp className="h-4 w-4 text-green-600" />
                              <AlertDescription className="text-green-800">
                                <strong>Great choice!</strong> This food adds approximately{' '}
                                <strong>{analysis.health_impact.health_impact_minutes.toFixed(2)}</strong> minutes to healthy life expectancy.
                              </AlertDescription>
                            </Alert>
                          ) : (
                            <Alert className="border-amber-200 bg-amber-50">
                              <AlertTriangle className="h-4 w-4 text-amber-600" />
                              <AlertDescription className="text-amber-800">
                                This food may reduce healthy life expectancy by approximately{' '}
                                <strong>{Math.abs(analysis?.health_impact?.health_impact_minutes || 0).toFixed(2)}</strong> minutes.
                              </AlertDescription>
                            </Alert>
                          )}

                          <div className="grid md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <h4 className="font-semibold text-green-700">✓ Keep These Elements</h4>
                              {(Object.entries(analysis?.component_breakdown?.food_group_contributions || {}) as Array<[string, number]>)
                                .filter(([, v]) => v > 0)
                                .slice(0, 3)
                                .map(([factor, value]) => (
                                  <div key={factor} className="flex justify-between text-sm">
                                    <span className="capitalize">{factor.replace('_', ' ')}</span>
                                    <Badge variant="secondary" className="text-green-700">+{value.toFixed(1)} μDALY</Badge>
                                  </div>
                                ))}
                            </div>
                            <div className="space-y-2">
                              <h4 className="font-semibold text-amber-700">Consider Reducing</h4>
                              {(Object.entries(analysis?.component_breakdown?.food_group_contributions || {}) as Array<[string, number]>)
                                .filter(([, v]) => v < 0)
                                .slice(0, 3)
                                .map(([factor, value]) => (
                                  <div key={factor} className="flex justify-between text-sm">
                                    <span className="capitalize">{factor.replace('_', ' ')}</span>
                                    <Badge variant="destructive" className="text-amber-700">{value.toFixed(1)} μDALY</Badge>
                                  </div>
                                ))}
                            </div>
                          </div>
                        </div>
                      );
                    })()}
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Research Data Tab */}
            <TabsContent value="research" className="space-y-6">
              <div className="grid lg:grid-cols-2 gap-6">
                {/* Primary Health Drivers */}
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-green-500" />
                      Primary Health Drivers
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {(() => {
                        const drivers = profileData.research_insights?.primary_health_drivers as unknown as {
                          positive_drivers?: Array<{ factor: string; contribution_μdaly?: number; health_minutes?: number }>;
                          negative_drivers?: Array<{ factor: string; contribution_μdaly?: number; health_minutes?: number }>;
                        } | undefined;
                        const positive = drivers?.positive_drivers || [];
                        const negative = drivers?.negative_drivers || [];
                        const combined = [...positive.map(d => ({ ...d, impact: d.contribution_μdaly || 0 })), ...negative.map(d => ({ ...d, impact: d.contribution_μdaly || 0 }))];
                        if (combined.length === 0) {
                          return <p className="text-gray-500">No specific health drivers identified</p>;
                        }
                        return combined.map((driver, index) => (
                          <div key={index} className="p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium capitalize">
                                {driver.factor?.replace('_', ' ') || 'Unknown Factor'}
                              </span>
                              <Badge variant={(driver.impact || 0) > 0 ? 'default' : 'destructive'}>
                                {(driver.impact || 0) > 0 ? '+' : ''}{(driver.impact || 0).toFixed(1)} μDALY
                              </Badge>
                            </div>
                            {driver.health_minutes !== undefined && (
                              <div className="text-xs text-gray-500 mb-1">{driver.health_minutes.toFixed(1)} minutes</div>
                            )}
                          </div>
                        ));
                      })()}
                    </div>
                  </CardContent>
                </Card>

                {/* Epidemiological Evidence */}
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Shield className="h-5 w-5 text-blue-500" />
                      Epidemiological Evidence
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-semibold text-gray-700 mb-2">Evidence Quality</h4>
                        <Badge variant="default">
                          {profileData.research_insights?.epidemiological_evidence?.quality || 'Moderate'}
                        </Badge>
                      </div>
                      
                      <div>
                        <h4 className="font-semibold text-gray-700 mb-2">Key Studies</h4>
                        <div className="space-y-2">
                          {profileData.research_insights?.epidemiological_evidence?.studies?.slice(0, 3).map((study, index) => (
                            <div key={index} className="text-sm p-2 bg-blue-50 rounded">
                              <p className="font-medium">{study.title || `Study ${index + 1}`}</p>
                              <p className="text-gray-600">{study.finding || 'Key epidemiological finding'}</p>
                            </div>
                          )) || (
                            <p className="text-sm text-gray-500">Based on Global Burden of Disease meta-analyses</p>
                          )}
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold text-gray-700 mb-2">Confidence Level</h4>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full" 
                              style={{ width: `${profileData.research_insights?.epidemiological_evidence?.confidence || 75}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium">
                            {profileData.research_insights?.epidemiological_evidence?.confidence || 75}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Population Impact Tab */}
            <TabsContent value="population" className="space-y-6">
              <Card className="shadow-lg">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5" />
                    Population Health Impact Modeling
                  </CardTitle>
                  <Button variant="outline" size="sm" onClick={exportDetailedReport}>
                    <Download className="h-4 w-4 mr-2" />
                    Export Report
                  </Button>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {profileData.research_insights?.population_impact_estimate?.dalys_per_100k || '0'}
                      </div>
                      <div className="text-sm text-gray-600">DALYs per 100,000</div>
                    </div>
                    
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        ${(profileData.research_insights?.population_impact_estimate?.economic_value_usd || 0).toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-600">Economic Value</div>
                    </div>
                    
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {profileData.research_insights?.population_impact_estimate?.years_affected || '0'}
                      </div>
                      <div className="text-sm text-gray-600">Years of Life Affected</div>
                    </div>
                    
                    <div className="text-center p-4 bg-amber-50 rounded-lg">
                      <div className="text-2xl font-bold text-amber-600">
                        {profileData.research_insights?.population_impact_estimate?.confidence_interval || 'N/A'}
                      </div>
                      <div className="text-sm text-gray-600">95% CI</div>
                    </div>
                  </div>

                  <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-semibold text-gray-700 mb-2">Modeling Assumptions</h4>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>• Population-attributable fraction based on exposure distributions</li>
                      <li>• Linear dose-response relationships within normal consumption ranges</li>
                      <li>• Economic valuation: $100,000 per DALY (WHO recommendation)</li>
                      <li>• 10-year time horizon for chronic disease development</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Policy Insights Tab */}
            <TabsContent value="policy" className="space-y-6">
              <div className="grid lg:grid-cols-2 gap-6">
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5" />
                      Policy Recommendations
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {profileData.policy_recommendations?.recommendations?.map((rec, index) => (
                        <div key={index} className="p-3 border-l-4 border-blue-500 bg-blue-50 rounded-r">
                          <div className="flex items-start gap-2">
                            <Badge variant="secondary" className="mt-0.5">
                              {rec.priority || 'Medium'}
                            </Badge>
                            <div>
                              <h4 className="font-medium text-blue-900">{rec.title || `Recommendation ${index + 1}`}</h4>
                              <p className="text-sm text-blue-800 mt-1">{rec.description || 'Policy recommendation details'}</p>
                            </div>
                          </div>
                        </div>
                      )) || (
                        <div className="text-center py-8 text-gray-500">
                          <Target className="h-12 w-12 mx-auto mb-2 opacity-50" />
                          <p>No specific policy recommendations available for this food item</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Regulatory Context</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-semibold text-gray-700 mb-2">Current Regulations</h4>
                        <p className="text-sm text-gray-600">
                          {profileData.policy_recommendations?.regulatory_status || 
                           'Food item subject to standard food safety and labeling regulations'}
                        </p>
                      </div>
                      
                      <div>
                        <h4 className="font-semibold text-gray-700 mb-2">International Guidelines</h4>
                        <ul className="text-sm text-gray-600 space-y-1">
                          <li>• WHO Global Strategy on Diet, Physical Activity and Health</li>
                          <li>• FAO/WHO Joint Expert Committee recommendations</li>
                          <li>• National dietary guidelines alignment</li>
                        </ul>
                      </div>

                      <div>
                        <h4 className="font-semibold text-gray-700 mb-2">Implementation Priority</h4>
                        <Badge variant={
                          profileData.policy_recommendations?.implementation_priority === 'High' ? 'destructive' :
                          profileData.policy_recommendations?.implementation_priority === 'Medium' ? 'default' : 'secondary'
                        }>
                          {profileData.policy_recommendations?.implementation_priority || 'Medium'}
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Benchmarks Tab */}
            <TabsContent value="comparison" className="space-y-6">
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle>Comparative Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid lg:grid-cols-3 gap-6">
                    {profileData.comparison_benchmarks?.similar_foods?.map((food, index) => (
                      <div key={index} className="p-4 border rounded-lg">
                        <h4 className="font-medium mb-2">{food.name || `Food ${index + 1}`}</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-600">HENI Score:</span>
                            <span className={`text-sm font-medium ${
                              food.heni_score > 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {food.heni_score > 0 ? '+' : ''}{food.heni_score?.toFixed(1) || '0.0'}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-600">Health Impact:</span>
                            <span className="text-sm font-medium">
                              {food.health_impact?.toFixed(1) || '0.0'} min
                            </span>
                          </div>
                        </div>
                      </div>
                    )) || (
                      <div className="col-span-3 text-center py-8 text-gray-500">
                        <BarChart3 className="h-12 w-12 mx-auto mb-2 opacity-50" />
                        <p>No comparison data available</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
            )}
          </div>
        </div>

        {/* Footer Info */}
        <Card className="mt-8 border-blue-200 bg-blue-50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-medium text-blue-800 mb-2">Research-Grade Analysis</h4>
                <p className="text-sm text-blue-700">
                  This tool provides research-quality HENI analysis using Global Burden of Disease methodology. 
                  Results are based on peer-reviewed epidemiological evidence and are suitable for academic research, 
                  policy development, and nutrition intervention planning.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default HENIFoodProfileAnalysis;