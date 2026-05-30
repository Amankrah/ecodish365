'use client';
/**
 * Environmental Impact Calculator - Main Interface Component
 * Comprehensive environmental LCA calculator for sustainable food choices
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
  Leaf,
  Calculator,
  TrendingUp,
  AlertTriangle,
  Info,
  Plus,
  Trash2,
  Download,
  Share2,
  ChevronDown,
  Globe,
  Users,
} from 'lucide-react';
import { AIEnhancedSearch } from '../shared/AIEnhancedSearch';
import { RecipeDecomposerModal } from '../shared/RecipeDecomposerModal';
import { SourceFilter, type SourceChoice } from '../shared/SourceFilter';
import { useRecall24hReceiver } from '../shared/useRecall24hReceiver';
import { FoodListPanel } from '../shared/FoodListPanel';
import { CollapsibleSection } from '../shared/CollapsibleSection';
import { EnvironmentalResultsCard } from './EnvironmentalResultsCard';
import { PlanetaryBoundaryCard } from './PlanetaryBoundaryCard';
import { EnvironmentalVisualization } from './EnvironmentalVisualization';
import { LCABreakdown } from './LCABreakdown';
import { SustainabilityChart } from './SustainabilityChart';
import { MonetizationBreakdown } from './MonetizationBreakdown';
import {
  EnvironmentalImpactApiService,
  CNFApiService,
  type EnvironmentalImpactResult,
  type FilterOptions,
  type LcaPerspective,
  type LcaConsumerPerspective,
  type LcaBasis,
  type MethodologyInfo,
} from '../../lib/api';

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

type UserType = 'individual' | 'researcher' | 'policy';

const EnvironmentalCalculator = () => {
  const [selectedFoods, setSelectedFoods] = useState<SelectedFood[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [environmentalResults, setEnvironmentalResults] = useState<EnvironmentalImpactResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchIsLoading, setSearchIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [selectedTab, setSelectedTab] = useState('calculator');
  const [filters, setFilters] = useState<FilterOptions | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedMethod, setSelectedMethod] = useState<string>('');
  const [showExportDropdown, setShowExportDropdown] = useState(false);
  const [recipeModalOpen, setRecipeModalOpen] = useState(false);
  const [userType, setUserType] = useState<UserType>('individual');
  // WAFCT-EXTEND (2026-05-24): food-database scope.
  const [sourceFilter, setSourceFilter] = useState<SourceChoice>('both');

  // Advanced methodology selection. Defaults reproduce prior behaviour
  // (Hierarchist perspective, global supply chain, world-average CFs,
  // per-100-kcal functional unit).
  const [perspective, setPerspective] = useState<LcaPerspective>('H');
  const [country, setCountry] = useState<string | null>(null);
  const [consumerPerspective, setConsumerPerspective] = useState<LcaConsumerPerspective>('global');
  const [basis, setBasis] = useState<LcaBasis>('per_100_kcal');
  // Tier γ composite-food recipe decomposition. Default ON for transparency:
  // only fires on the ~12 % of foods that are composite-group AND get a
  // borderline matcher match (conf < 0.85). For Canadian-specific composites
  // the LLM commonly rejects its own decomposition with low self-confidence
  // (audit trail enriched, headline number unchanged); for generic composites
  // expressible in v32 ingredients it resolves and replaces the matcher's
  // near-miss. Worst-case +5-7 s per affected food; +$0.0003 per attempt.
  const [enableDecomposer, setEnableDecomposer] = useState(true);
  const [methodologyInfo, setMethodologyInfo] = useState<MethodologyInfo | null>(null);
  const [advancedOpen, setAdvancedOpen] = useState(false);

  // AI-MATCH-2 (2026-05-24): pick up an aggregated 24-h recall payload
  // handed off from /recall-24h.
  useRecall24hReceiver({
    target: 'environmental',
    onIngredients: (ingredients, meta) => {
      setUserType(meta.user_type as UserType);
      setSelectedFoods(ingredients.map(i => ({
        FoodID: i.food_id,
        FoodDescription: i.food_description,
        amount: i.mass_g,
        unit: 'g',
      })));
    },
  });

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
    // Load methodology info once on mount so the Advanced panel can populate
    // its dropdowns with the live workbook-derived list (perspectives,
    // countries, country-aware pathways).
    EnvironmentalImpactApiService.getMethodologyInfo()
      .then(setMethodologyInfo)
      .catch((e) => console.warn('Failed to load methodology info', e));
  }, []);

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

  // Debounced search with filters
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
            source: sourceFilter,
          });
          setSearchResults(enhanced.results || []);
        } catch {
          const basic = await CNFApiService.searchFoods(searchQuery, 50, 0, sourceFilter);
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
  }, [searchQuery, selectedCategory, selectedMethod, sourceFilter]);

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

  // Calculate Environmental Impact
  const calculateEnvironmentalImpact = async () => {
    if (selectedFoods.length === 0) {
      setError('Please add at least one food item to calculate environmental impact');
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
      
      const foods = selectedFoods.map(f => ({ 
        food_id: f.FoodID, 
        quantity: f.amount
      }));
      
      const response = await EnvironmentalImpactApiService.analyzeMealEnvironmentalImpact({
        foods,
        user_type: userType,
        // AGRIBALYSE-INGEST §3.5: always on — every CNF food gets matched to
        // its Agribalyse 3.2 LCI entry (v32 catalog, ~$0.0002/food). The
        // matcher audit panel in the Analysis tab documents each decision.
        enable_lca_matcher: true,
        // Tier γ composite-food recipe decomposition (default off; opt-in
        // via Advanced panel). Adds ~$0.0003 per composite when triggered.
        enable_recipe_decomposer: enableDecomposer,
        // Methodology pack (defaults preserved unless user opens Advanced).
        perspective,
        country: consumerPerspective === 'national' ? country : null,
        consumer_perspective: consumerPerspective,
        basis,
      });
      setEnvironmentalResults(response);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { message?: string; error?: string } } };
      setError(e?.response?.data?.error || e?.response?.data?.message || 'Failed to calculate environmental impact');
      console.warn('Environmental calculation error:', e?.response?.data || err);
    } finally {
      setLoading(false);
    }
  };

  // Clear all foods
  const resetCalculation = () => {
    setSelectedFoods([]);
    setEnvironmentalResults(null);
    setError('');
    setSearchQuery('');
    setSearchResults([]);
  };

  // Export results as JSON
  const exportResultsJSON = () => {
    if (!environmentalResults) return;
    
    const exportData = {
      timestamp: new Date().toISOString(),
      meal_composition: selectedFoods,
      environmental_analysis: environmentalResults,
      user_type: userType
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `environmental-impact-analysis-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Export results as PDF report
  const exportResultsPDF = async () => {
    if (!environmentalResults) return;
    
    const analysis = environmentalResults.data;
    const timestamp = new Date().toLocaleString();
    
    const reportContent = `
ENVIRONMENTAL IMPACT ANALYSIS REPORT
Generated on: ${timestamp}
User Type: ${userType.charAt(0).toUpperCase() + userType.slice(1)}

===========================================
MEAL COMPOSITION
===========================================
${selectedFoods.map(food => 
  `• ${food.FoodDescription}: ${food.amount}g`
).join('\n')}

Total Weight: ${analysis?.meal_analysis?.meal_composition?.total_weight_grams || 0}g
Total Energy: ${analysis?.meal_analysis?.meal_composition?.total_energy_kcal || 0} kcal

===========================================
ENVIRONMENTAL IMPACTS (LCA RESULTS)
===========================================
Carbon Footprint: ${analysis?.meal_analysis?.lca_results['Global warming']?.toFixed(3) || '0.000'} kg CO2-eq
Water Consumption: ${analysis?.meal_analysis?.lca_results['Water consumption']?.toFixed(3) || '0.000'} m³
Land Use: ${analysis?.meal_analysis?.lca_results['Land use']?.toFixed(3) || '0.000'} m²a crop-eq
Acidification: ${analysis?.meal_analysis?.lca_results['Terrestrial acidification']?.toFixed(3) || '0.000'} kg SO2-eq
Eutrophication: ${analysis?.meal_analysis?.lca_results['Freshwater eutrophication']?.toFixed(3) || '0.000'} kg P-eq

Single Score: ${analysis?.meal_analysis?.single_score?.toFixed(3) || '0.000'} points

===========================================
ECONOMIC IMPACT (MONETIZATION)
===========================================
Total Environmental Cost: CAD $${analysis?.meal_analysis?.monetization?.total_cost?.toFixed(3) || '0.000'}
Cost per Calorie: CAD $${analysis?.meal_analysis?.monetization?.cost_per_calorie?.toFixed(5) || '0.00000'}
Cost per Protein: CAD $${analysis?.meal_analysis?.monetization?.cost_per_protein?.toFixed(5) || '0.00000'}

Top Cost Drivers:
${analysis?.meal_analysis?.monetization?.top_cost_drivers?.slice(0, 3).map(driver => 
  `${driver.rank}. ${driver.impact_category}: CAD $${driver.cost.toFixed(3)} (${driver.percentage_of_total.toFixed(1)}%)`
).join('\n') || 'N/A'}

===========================================
SUSTAINABILITY ASSESSMENT
===========================================
Overall Sustainability Score: ${analysis?.meal_analysis?.sustainability_score?.overall_sustainability_score?.toFixed(1) || '0.0'}/100
Rating: ${analysis?.meal_analysis?.sustainability_score?.sustainability_rating || 'Unknown'}
Environmental Score: ${analysis?.meal_analysis?.sustainability_score?.environmental_score?.toFixed(1) || '0.0'}/100
Nutritional Score: ${analysis?.meal_analysis?.sustainability_score?.nutritional_score?.toFixed(1) || '0.0'}/100

===========================================
USER EXPLANATION
===========================================
${analysis?.user_explanation?.summary || 'No summary available'}

Key Findings:
${analysis?.user_explanation?.key_findings?.map((finding, i) => `${i + 1}. ${finding}`).join('\n') || 'N/A'}

Recommendations:
${analysis?.user_explanation?.recommendations?.map((rec, i) => `${i + 1}. ${rec}`).join('\n') || 'N/A'}

===========================================
SCIENTIFIC METHODOLOGY
===========================================
This environmental impact analysis uses ReCiPe 2016 LCA methodology with 18 midpoint 
impact categories and Canadian regional correction factors. Monetization uses current 
Canadian economic factors including $185 CAD per tonne CO2-eq (Environment Canada SCC 2024).

Analysis considers:
• 18 Midpoint Impact Categories (Climate, Resource Depletion, Ecosystem Quality, Human Health)
• 3 Endpoint Categories (Human Health, Ecosystem Quality, Resource Scarcity)
• Canadian Regional Adjustment Factors
• Current Environmental Economic Valuations (2024)
• Comprehensive Sustainability Scoring

Report generated by EcoDish365 Environmental Impact Calculator
    `.trim();
    
    const blob = new Blob([reportContent], {
      type: 'text/plain;charset=utf-8'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `environmental-impact-report-${new Date().toISOString().split('T')[0]}.txt`;
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

  const getUserTypeDescription = (type: UserType) => {
    switch (type) {
      case 'individual': return 'Consumer-friendly explanations with practical tips for everyday choices';
      case 'researcher': return 'Scientific methodology details and data suitable for academic research';
      case 'policy': return 'Policy-relevant analysis for decision-makers and regulatory frameworks';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-emerald-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Leaf className="h-8 w-8 text-green-500 mr-3" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              Environmental Impact Calculator
            </h1>
          </div>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Analyze your food&apos;s environmental impact using ReCiPe 2016 v1.1
            Life Cycle Assessment with workbook-grounded characterisation factors,
            configurable cultural perspective, and per-country endpoint adaptation.
          </p>

          {/* User Type Selector */}
          <div className="mt-4 flex justify-center">
            <div className="bg-white rounded-lg border p-1 shadow-sm">
              {(['individual', 'researcher', 'policy'] as UserType[]).map((type) => (
                <button
                  key={type}
                  onClick={() => setUserType(type)}
                  title={getUserTypeDescription(type)}
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

          {/* FOOD-LIST-PANEL (2026-05-26): cross-metric transferable food list. */}
          <div className="mt-6 text-left">
            <FoodListPanel
              currentTarget="environmental"
              onChange={list => {
                if (!list) {
                  setSelectedFoods([]);
                  return;
                }
                setSelectedFoods(list.ingredients.map(i => ({
                  FoodID: i.food_id,
                  FoodDescription: i.food_description,
                  amount: i.mass_g,
                  unit: 'g',
                })));
              }}
            />
          </div>

          {/* Advanced methodology panel (collapsed by default) */}
          <div className="mt-4 max-w-3xl mx-auto">
            <button
              type="button"
              onClick={() => setAdvancedOpen(!advancedOpen)}
              className="text-xs text-gray-500 hover:text-gray-700 underline"
            >
              {advancedOpen ? 'Hide' : 'Show'} advanced methodology options
              {(perspective !== 'H' || country || consumerPerspective !== 'global' || basis !== 'per_100_kcal' || !enableDecomposer) && (
                <span className="ml-2 inline-flex items-center gap-1 text-green-700 font-medium">
                  • {perspective}
                  {country ? ` · ${country}` : ''}
                  {consumerPerspective === 'national' ? ' · national' : ''}
                  {basis !== 'per_100_kcal' ? ` · ${basis.replace('per_', '/')}` : ''}
                  {!enableDecomposer ? ' · decomposer off' : ''}
                </span>
              )}
            </button>
            {advancedOpen && (
              <div className="mt-2 bg-white rounded-lg border p-4 shadow-sm text-left space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">
                    Cultural perspective
                  </label>
                  <div className="flex gap-2 flex-wrap">
                    {(['H', 'I', 'E'] as LcaPerspective[]).map((p) => (
                      <button
                        key={p}
                        type="button"
                        onClick={() => setPerspective(p)}
                        title={methodologyInfo?.perspective_descriptions?.[p] || ''}
                        className={`px-3 py-1 rounded text-xs border transition-colors ${
                          perspective === p
                            ? 'bg-green-100 text-green-800 border-green-400 font-medium'
                            : 'bg-white text-gray-600 border-gray-300 hover:border-gray-400'
                        }`}
                      >
                        {p === 'H' ? 'Hierarchist (default)' : p === 'I' ? 'Individualist' : 'Egalitarian'}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">
                    Consumer perspective
                  </label>
                  <div className="flex gap-2 flex-wrap">
                    {(['global', 'national'] as LcaConsumerPerspective[]).map((cp) => (
                      <button
                        key={cp}
                        type="button"
                        onClick={() => setConsumerPerspective(cp)}
                        title={methodologyInfo?.consumer_perspective_descriptions?.[cp] || ''}
                        className={`px-3 py-1 rounded text-xs border transition-colors ${
                          consumerPerspective === cp
                            ? 'bg-green-100 text-green-800 border-green-400 font-medium'
                            : 'bg-white text-gray-600 border-gray-300 hover:border-gray-400'
                        }`}
                      >
                        {cp === 'global' ? 'Global supply chain (default)' : 'National (uses country-specific CFs)'}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">
                    Country (ISO-3) {consumerPerspective !== 'national' && <span className="text-gray-400 font-normal">— enabled only when consumer perspective is &apos;national&apos;</span>}
                  </label>
                  <select
                    title="Select an ISO-3 country code for country-specific endpoint CFs"
                    aria-label="Country (ISO-3)"
                    value={country ?? ''}
                    onChange={(e) => setCountry(e.target.value || null)}
                    disabled={consumerPerspective !== 'national'}
                    className="w-full text-xs px-2 py-1 border border-gray-300 rounded disabled:bg-gray-100 disabled:text-gray-400"
                  >
                    <option value="">(world-average)</option>
                    {(methodologyInfo?.available_countries || []).map((iso) => (
                      <option key={iso} value={iso}>{iso}</option>
                    ))}
                  </select>
                  {consumerPerspective === 'national' && country && methodologyInfo?.country_aware_pathways && (
                    <p className="mt-1 text-xs text-gray-500">
                      Country-specific endpoint CFs apply to {methodologyInfo.country_aware_pathways.length} pathways
                      (currently the water-consumption family). All other pathways remain world-average.
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">
                    Functional unit
                  </label>
                  <div className="flex gap-2 flex-wrap">
                    {([
                      { v: 'per_100_kcal',     l: 'per 100 kcal (default)',  t: 'Caloric-density-fair basis. Poore & Nemecek Panel C uses this; appropriate when comparing meals of different mass with comparable caloric content.' },
                      { v: 'per_serving',      l: 'per serving (raw)',        t: 'Absolute meal impact for the meal as input. Most consumer-relevant; what a person actually consumes.' },
                      { v: 'per_100g_product', l: 'per 100 g product',        t: 'Mass-normalised basis. Biased by water content (raw cucumber ~96% water). Useful for label-comparable per-100g values.' },
                      { v: 'per_100g_protein', l: 'per 100 g protein',        t: 'Protein-source-fair basis. Poore & Nemecek Panel A uses this; appropriate when comparing protein sources (meat vs legumes vs pulses).' },
                    ] as { v: LcaBasis; l: string; t: string }[]).map(({ v, l, t }) => (
                      <button
                        key={v}
                        type="button"
                        onClick={() => setBasis(v)}
                        title={t}
                        className={`px-3 py-1 rounded text-xs border transition-colors ${
                          basis === v
                            ? 'bg-green-100 text-green-800 border-green-400 font-medium'
                            : 'bg-white text-gray-600 border-gray-300 hover:border-gray-400'
                        }`}
                      >
                        {l}
                      </button>
                    ))}
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    Changes the headline numbers only; all four bases are always computed and returned in the response under <code>impacts_by_basis</code>.
                  </p>
                </div>

                <div className="border-t pt-3">
                  <label className="flex items-start gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={enableDecomposer}
                      onChange={(e) => setEnableDecomposer(e.target.checked)}
                      className="mt-0.5"
                    />
                    <div className="text-xs">
                      <div className="font-semibold text-gray-700">
                        Composite recipe decomposition (Tier γ) — on by default
                      </div>
                      <div className="text-gray-500 mt-0.5">
                        For composite CNF foods (poutine, bannock, tourtière, soups, mixed
                        dishes, babyfoods) where the direct matcher&apos;s confidence is below
                        0.85, asks the LLM to express the dish as an ingredient list
                        constrained to Agribalyse v32 entries. On generic composites with
                        v32-expressible ingredients the decomposition replaces the matcher&apos;s
                        near-miss; on Canadian-specific dishes the LLM commonly rejects its
                        own decomposition with low self-confidence (audit trail enriched,
                        headline number unchanged). Adds ~5-7 s and ~$0.0003 per affected
                        composite; requires OpenAI key on the backend. Uncheck to skip and
                        always show the matcher&apos;s direct (possibly stretched) result.
                      </div>
                    </div>
                  </label>
                </div>

                {methodologyInfo?.active_methodology_version && (
                  <div className="text-xs text-gray-400 border-t pt-2">
                    Active pack: <code className="font-mono">{methodologyInfo.active_methodology_version}</code>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Main Content */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab} defaultValue={selectedTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6">
            <TabsTrigger value="calculator" className="flex items-center gap-2">
              <Calculator className="h-4 w-4" />
              Calculator
            </TabsTrigger>
            <TabsTrigger value="analysis" className="flex items-center gap-2" disabled={!environmentalResults}>
              <TrendingUp className="h-4 w-4" />
              Analysis
            </TabsTrigger>
            <TabsTrigger value="insights" className="flex items-center gap-2" disabled={!environmentalResults}>
              <Info className="h-4 w-4" />
              Insights
            </TabsTrigger>
          </TabsList>

          {/* Calculator Tab */}
          <TabsContent value="calculator" className="space-y-6">
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Food Input Section — collapsible so the cross-page FoodListPanel
                  above can be the primary surface once a list is loaded. */}
              <CollapsibleSection
                title="Build Your Meal"
                icon={<Plus className="h-5 w-5 text-gray-700" />}
                badge={selectedFoods.length > 0 ? `${selectedFoods.length} food${selectedFoods.length === 1 ? '' : 's'}` : undefined}
                persistKey="environmental-build-meal"
                defaultCollapsed
                className="bg-white border rounded-lg shadow-lg"
                headerClassName="p-6"
                whenCollapsedHint={
                  <p className="px-6 pb-4 text-xs text-gray-600">
                    Click above to search the CNF database and add or change foods.
                  </p>
                }
              >
                <div className="p-6 pt-0 space-y-6">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-1">Add Foods</h2>
                    <p className="text-sm text-gray-600">
                      Search and select foods to analyze their environmental impact using LCA methodology.
                    </p>
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
                            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
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
                            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
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
                    {/* WAFCT-EXTEND (2026-05-24): food-database scope */}
                    <SourceFilter source={sourceFilter} onChange={setSourceFilter} accent="green" />
                    <div className="relative">
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search for foods (e.g., beef, lentils, rice, fonio, baobab)..."
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
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
                      source={sourceFilter}
                      onSelect={(food) =>
                        addFood({
                          FoodID: food.food_id,
                          FoodDescription: food.food_description,
                        })
                      }
                    />
                    <button
                      type="button"
                      onClick={() => setRecipeModalOpen(true)}
                      className="inline-flex items-center gap-1.5 text-sm text-green-700 hover:text-green-900 hover:underline"
                    >
                      🍳 Score a homemade dish (decompose into CNF ingredients)
                    </button>
                    {/* AI-MATCH-2 (2026-05-24): 24-h dietary recall — daily
                        environmental footprint aggregates LCA factors across
                        the whole day's eating. */}
                    <a
                      href="/recall-24h?then=environmental"
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
                        <Leaf className="w-10 h-10 mx-auto mb-2 opacity-50" />
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
                                className="w-24 px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
                              />
                              <span className="text-sm text-gray-500">grams</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Error */}
                  {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                      <div className="flex items-center">
                        <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
                        <div className="text-sm text-red-700">{error}</div>
                      </div>
                    </div>
                  )}
                </div>
              </CollapsibleSection>

              {/* Calculate button — outside the collapsible so the user can score
                  without re-expanding the Build Your Meal panel after editing
                  the list via the FoodListPanel above. */}
              <button
                type="button"
                onClick={calculateEnvironmentalImpact}
                disabled={loading || selectedFoods.length === 0}
                className="w-full mt-4 inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                <Leaf className="mr-2 w-5 h-5" />
                {loading ? 'Analyzing...' : 'Analyze Environmental Impact'}
              </button>

              {/* Quick Results Preview */}
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Globe className="h-5 w-5" />
                    Environmental Impact Preview
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {error && (
                    <Alert className="mb-4 border-red-200 bg-red-50">
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                      <AlertDescription className="text-red-700">{error}</AlertDescription>
                    </Alert>
                  )}

                  {environmentalResults ? (
                    <EnvironmentalResultsCard results={environmentalResults} compact />
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <Leaf className="h-12 w-12 mx-auto mb-2 opacity-50" />
                      <p>Add ingredients and calculate to see environmental impact</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Analysis Tab */}
          <TabsContent value="analysis" className="space-y-6">
            {environmentalResults && (
              <>
                {/* PLANETARY-1 (2026-05-27): EAT-Lancet 2.0 Table 2 food-system
                    boundary share. Renders only when the backend emits the
                    block (older deploys are backward-compatible — undefined
                    here gracefully hides the card). */}
                {environmentalResults.data?.meal_analysis?.planetary_boundary_shares && (
                  <PlanetaryBoundaryCard
                    shares={environmentalResults.data.meal_analysis.planetary_boundary_shares}
                    explanations={environmentalResults.data.meal_analysis.planetary_explanations}
                  />
                )}
                {/* AGRIBALYSE-INGEST §3.5 matcher audit (only when matcher fired) */}
                {environmentalResults.data?.meal_analysis?.lca_matcher?.enabled && (
                  <Card className="shadow-lg border-2 border-emerald-200 bg-emerald-50/30">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-emerald-900">
                        <Leaf className="h-5 w-5" />
                        Agribalyse 3.2 Matcher Audit (experimental)
                      </CardTitle>
                      <p className="text-xs text-gray-600 mt-1">
                        Catalog:{' '}
                        <code className="text-[11px] bg-white px-1 py-0.5 rounded">
                          {environmentalResults.data.meal_analysis.lca_matcher.catalog_version || 'unknown'}
                        </code>
                      </p>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-left border-b border-emerald-200 text-xs uppercase tracking-wide text-emerald-800">
                              <th className="py-2 pr-4">CNF food</th>
                              <th className="py-2 pr-4">Matched Ciqual</th>
                              <th className="py-2 pr-4">Confidence</th>
                              <th className="py-2 pr-4">DQR</th>
                              <th className="py-2 pr-4">Cats m/g</th>
                              <th className="py-2">Justification</th>
                            </tr>
                          </thead>
                          <tbody>
                            {environmentalResults.data.meal_analysis.lca_matcher.decisions.map((d) => (
                              <tr key={d.food_id} className="border-b border-emerald-100 last:border-0">
                                <td className="py-2 pr-4 font-mono text-xs">
                                  {selectedFoods.find((f) => f.FoodID === d.food_id)?.FoodDescription || `food_id=${d.food_id}`}
                                </td>
                                <td className="py-2 pr-4">
                                  {d.matched ? (
                                    <div>
                                      <code className="text-xs bg-emerald-100 px-1.5 py-0.5 rounded">{d.ciqual_code}</code>
                                      <div className="text-xs text-gray-600 mt-0.5">{d.lci_name}</div>
                                    </div>
                                  ) : (
                                    <span className="text-xs text-red-600">fallback ({d.fallback_reason})</span>
                                  )}
                                </td>
                                <td className="py-2 pr-4 font-mono text-xs">{d.confidence.toFixed(2)}</td>
                                <td className="py-2 pr-4 font-mono text-xs">{d.dqr?.toFixed(1) ?? '—'}</td>
                                <td className="py-2 pr-4 font-mono text-xs" title="categories from match / from group default">
                                  {d.categories_from_match ?? '—'}/{d.categories_from_group_default ?? '—'}
                                </td>
                                <td className="py-2 text-xs text-gray-700 max-w-md">{d.justification}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      {environmentalResults.data.meal_analysis.lca_matcher.sensitivity && (
                        <div className="mt-4 pt-4 border-t border-emerald-200">
                          <div className="text-xs font-semibold text-emerald-900 mb-2">
                            EF 3.1 sensitivity ({environmentalResults.data.meal_analysis.lca_matcher.sensitivity.matched_count} matched foods, native units, NOT interchangeable with ReCiPe)
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                            {Object.entries(environmentalResults.data.meal_analysis.lca_matcher.sensitivity.ef31_aggregated_per_meal)
                              .slice(0, 9)
                              .map(([k, v]) => (
                                <div key={k} className="bg-white rounded px-2 py-1.5 border border-emerald-100">
                                  <div className="text-[10px] text-gray-500 truncate" title={k}>{k}</div>
                                  <div className="font-mono">{typeof v === 'number' ? v.toExponential(3) : v} <span className="text-[10px] text-gray-500">{environmentalResults.data.meal_analysis.lca_matcher.sensitivity?.unit_metadata?.[k]?.replace('/kg de produit', '/meal') ?? ''}</span></div>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Comprehensive Results */}
                <div className="grid lg:grid-cols-5 gap-6 mb-6">
                  <Card className="lg:col-span-3 shadow-lg">
                    <CardHeader className="flex flex-row items-center justify-between">
                      <CardTitle>Detailed Environmental Analysis</CardTitle>
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
                                Report
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
                      <EnvironmentalResultsCard results={environmentalResults} detailed />
                    </CardContent>
                  </Card>

                  <Card className="lg:col-span-2 shadow-lg">
                    <CardHeader>
                      <CardTitle>Environmental Visualization</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <EnvironmentalVisualization results={environmentalResults} />
                    </CardContent>
                  </Card>
                </div>

                {/* Impact Breakdown and Sustainability */}
                <div className="grid lg:grid-cols-2 gap-6 mb-6">
                  <Card className="shadow-lg">
                    <CardHeader>
                      <CardTitle>LCA Impact Breakdown</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <LCABreakdown results={environmentalResults} userType={userType} />
                    </CardContent>
                  </Card>

                  <Card className="shadow-lg">
                    <CardHeader>
                      <CardTitle>Sustainability Assessment</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <SustainabilityChart results={environmentalResults} />
                    </CardContent>
                  </Card>
                </div>

                {/* Economic Analysis */}
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Economic Impact Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <MonetizationBreakdown results={environmentalResults} userType={userType} />
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>

          {/* Insights Tab */}
          <TabsContent value="insights" className="space-y-6">
            {environmentalResults && (
              <div className="grid gap-6">
                {/* User-Tailored Explanation */}
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      {getUserTypeIcon(userType)}
                      {userType.charAt(0).toUpperCase() + userType.slice(1)} Insights
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {/* Summary */}
                      <div className="bg-blue-50 p-4 rounded-lg">
                        <h4 className="font-semibold text-blue-900 mb-2">Summary</h4>
                        <p className="text-blue-800">{environmentalResults.data?.user_explanation?.summary || 'No summary available'}</p>
                      </div>

                      {/* Key Findings */}
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-3">Key Findings</h4>
                        <div className="grid gap-2">
                          {(environmentalResults.data?.user_explanation?.key_findings || []).map((finding, index) => (
                            <div key={index} className="flex items-start gap-2">
                              <Badge variant="outline" className="text-xs mt-0.5">
                                {index + 1}
                              </Badge>
                              <p className="text-sm text-gray-700">{finding}</p>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Recommendations */}
                      <div>
                        <h4 className="font-semibold text-green-700 mb-3">Recommendations</h4>
                        <div className="space-y-2">
                          {(environmentalResults.data?.user_explanation?.recommendations || []).map((rec, index) => (
                            <div key={index} className="flex items-start gap-2 p-3 bg-green-50 rounded-lg">
                              <Leaf className="h-4 w-4 text-green-600 mt-0.5" />
                              <p className="text-sm text-green-800">{rec}</p>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Context */}
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-semibold text-gray-900 mb-2">Context</h4>
                        <p className="text-gray-700 text-sm">{environmentalResults.data?.user_explanation?.context || 'No context available'}</p>
                      </div>

                      {/* Technical Notes for Researchers/Policy */}
                      {(userType === 'researcher' || userType === 'policy') && environmentalResults.data?.user_explanation?.technical_notes && (
                        <div className="bg-indigo-50 p-4 rounded-lg">
                          <h4 className="font-semibold text-indigo-900 mb-2">Technical Notes</h4>
                          <div className="space-y-1">
                            {(environmentalResults.data?.user_explanation?.technical_notes || []).map((note, index) => (
                              <p key={index} className="text-sm text-indigo-800">• {note}</p>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Reference Comparisons */}
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Reference Meal Comparisons</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-3">
                        <h4 className="font-semibold text-green-700">vs Sustainable Meal</h4>
                        <div className="bg-green-50 p-4 rounded-lg space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm">Cost Ratio:</span>
                            <Badge variant={environmentalResults.data?.comparison_to_references?.sustainable_meal?.cost_ratio <= 1 ? 'default' : 'destructive'}>
                              {environmentalResults.data?.comparison_to_references?.sustainable_meal?.cost_ratio?.toFixed(2) || '0.00'}x
                            </Badge>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm">Carbon Ratio:</span>
                            <Badge variant={environmentalResults.data?.comparison_to_references?.sustainable_meal?.carbon_ratio <= 1 ? 'default' : 'destructive'}>
                              {environmentalResults.data?.comparison_to_references?.sustainable_meal?.carbon_ratio?.toFixed(2) || '0.00'}x
                            </Badge>
                          </div>
                          <p className="text-xs text-green-700">
                            {environmentalResults.data?.comparison_to_references?.sustainable_meal?.sustainability_comparison || 'No comparison available'}
                          </p>
                        </div>
                      </div>

                      <div className="space-y-3">
                        <h4 className="font-semibold text-orange-700">vs Average Meal</h4>
                        <div className="bg-orange-50 p-4 rounded-lg space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm">Cost Ratio:</span>
                            <Badge variant={environmentalResults.data?.comparison_to_references?.average_meal?.cost_ratio <= 1 ? 'default' : 'destructive'}>
                              {environmentalResults.data?.comparison_to_references?.average_meal?.cost_ratio?.toFixed(2) || '0.00'}x
                            </Badge>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm">Carbon Ratio:</span>
                            <Badge variant={environmentalResults.data?.comparison_to_references?.average_meal?.carbon_ratio <= 1 ? 'default' : 'destructive'}>
                              {environmentalResults.data?.comparison_to_references?.average_meal?.carbon_ratio?.toFixed(2) || '0.00'}x
                            </Badge>
                          </div>
                          <p className="text-xs text-orange-700">
                            {environmentalResults.data?.comparison_to_references?.average_meal?.sustainability_comparison || 'No comparison available'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Scientific Context */}
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Scientific Methodology</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-sm max-w-none">
                      <p className="text-gray-600 mb-4">
                        This environmental impact analysis uses the <strong>ReCiPe 2016 LCA methodology</strong> with 
                        18 midpoint impact categories and Canadian regional correction factors. Economic valuation 
                        includes current Canadian factors with <strong>$185 CAD per tonne CO2-eq</strong> social cost of carbon.
                      </p>

                      <div className="grid md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <h5 className="font-semibold mb-2">18 Impact Categories:</h5>
                          <ul className="space-y-1 text-gray-600">
                            <li>• Climate Change (Global Warming)</li>
                            <li>• Ozone Depletion</li>
                            <li>• Fine Particulate Matter Formation</li>
                            <li>• Terrestrial/Freshwater/Marine Acidification</li>
                            <li>• Terrestrial/Freshwater/Marine Ecotoxicity</li>
                            <li>• Human Carcinogenic/Non-carcinogenic Toxicity</li>
                            <li>• Land Use, Water Consumption</li>
                            <li>• Fossil/Mineral Resource Scarcity</li>
                          </ul>
                        </div>

                        <div>
                          <h5 className="font-semibold mb-2">3 Endpoint Categories:</h5>
                          <ul className="space-y-1 text-gray-600">
                            <li>• <strong>Human Health</strong> (DALY)</li>
                            <li>• <strong>Ecosystem Quality</strong> (species.year)</li>
                            <li>• <strong>Resource Scarcity</strong> (USD)</li>
                          </ul>
                          
                          <h5 className="font-semibold mb-2 mt-4">Regional Adjustments:</h5>
                          <ul className="space-y-1 text-gray-600">
                            <li>• Canadian Climate Factors (+15%)</li>
                            <li>• Water Abundance Adjustment (-30%)</li>
                            <li>• Land Use Factors (-20%)</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* AI-MATCH-1: homemade dish workflow — pushes decomposed rows into Selected Foods */}
      <RecipeDecomposerModal
        open={recipeModalOpen}
        onClose={() => setRecipeModalOpen(false)}
        userType={userType}
        accent="green"
        initialSource={sourceFilter}
        onApply={(ingredients) => {
          const additions: SelectedFood[] = ingredients
            .filter((i) => !selectedFoods.some((f) => f.FoodID === i.food_id))
            .map((i) => ({
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

export default EnvironmentalCalculator;