'use client';

import React, { useState, useEffect, Suspense, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  PlusIcon,
  XMarkIcon,
  ArrowDownTrayIcon,
  InformationCircleIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
  BeakerIcon,
  LinkIcon,
} from '@heroicons/react/24/outline';
import { CNFApiService, FoodComparison, Food, SearchResult, NutrientValue, Nutrient } from '@/lib/api';
import toast from 'react-hot-toast';
import { SourceFilter, type SourceChoice } from '@/components/shared/SourceFilter';
import { SourceBadge } from '@/components/shared/SourceBadge';
import { AIEnhancedSearch } from '@/components/shared/AIEnhancedSearch';
import { useCnfExplorer } from '@/components/cnf/CnfExplorerContext';
import { FoodDetailDrawer } from '@/components/cnf/FoodProfileContent';
import { appendManyToActiveFoodList, loadActiveFoodList } from '@/lib/activeFoodList';
import { NutrientDiscoverPanel } from '@/components/cnf/NutrientDiscoverPanel';
import { CompareFoodStrip } from '@/components/cnf/compare/CompareFoodStrip';
import { CompareMixedDbBanner } from '@/components/cnf/compare/CompareMixedDbBanner';
import { CompareNutrientTable } from '@/components/cnf/compare/CompareNutrientTable';
import { CompareEmptyState } from '@/components/cnf/compare/CompareEmptyState';
import {
  hasMixedDatabases,
  type CompareBasis,
  cellPercentDV,
} from '@/lib/cnfCompareHelpers';
import { toCsv, downloadCsv } from '@/lib/csv';

type AddFoodMode = 'search' | 'discover';

interface ComparisonData {
  foods: Food[];
  comparison: FoodComparison | null;
}

function CNFComparePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { userType, resolveGroupName, activeFoodCount } = useCnfExplorer();
  const [comparisonData, setComparisonData] = useState<ComparisonData>({ foods: [], comparison: null });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [showAddFood, setShowAddFood] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [detailFood, setDetailFood] = useState<Food | null>(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportFormat, setExportFormat] = useState<'json' | 'csv' | 'compare_csv'>('compare_csv');
  const [selectedFoodIds, setSelectedFoodIds] = useState<Set<number>>(new Set());
  const [modalSource, setModalSource] = useState<SourceChoice>('both');
  const [addFoodMode, setAddFoodMode] = useState<AddFoodMode>('search');
  const [basis, setBasis] = useState<CompareBasis>('per_100g');
  const [showDelta, setShowDelta] = useState(false);
  const [diffOnly, setDiffOnly] = useState(false);
  const [transposed, setTransposed] = useState(false);
  const [customNutrientIds, setCustomNutrientIds] = useState<number[]>([]);
  const [portionMass, setPortionMass] = useState<Record<number, number>>({});
  const [allNutrients, setAllNutrients] = useState<Nutrient[]>([]);

  useEffect(() => {
    CNFApiService.getNutrients().then(setAllNutrients).catch(() => {});
  }, []);

  const syncCompareUrl = useCallback((ids: number[]) => {
    if (ids.length === 0) router.replace('/cnf/compare', { scroll: false });
    else router.replace(`/cnf/compare?foods=${ids.join(',')}`, { scroll: false });
  }, [router]);

  const runComparison = useCallback(async (foods: Food[], extraNutrientIds?: number[]) => {
    const ids = foods.map(f => f.FoodID);
    if (ids.length >= 2) {
      const nutrientIds = extraNutrientIds ?? customNutrientIds;
      const comparison = await CNFApiService.compareFoods(ids, {
        basis,
        nutrientIds: nutrientIds.length ? nutrientIds : undefined,
      });
      setComparisonData({ foods, comparison });
    } else {
      setComparisonData({ foods, comparison: null });
    }
    syncCompareUrl(ids);
  }, [basis, customNutrientIds, syncCompareUrl]);

  useEffect(() => {
    // Load initial foods from URL parameters
    const foodIds = searchParams.get('foods');
    if (foodIds) {
      const ids = foodIds.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
      if (ids.length > 0) {
        loadFoodsForComparison(ids);
      }
    }
  }, [searchParams]);

  // WAFCT-EXTEND (2026-05-24): re-run the search when source scope changes
  // mid-modal so the result list narrows / widens without the user having
  // to retype.
  useEffect(() => {
    if (searchQuery.trim()) {
      searchFoods(searchQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modalSource]);

  const loadFoodsForComparison = async (foodIds: number[]) => {
    try {
      setLoading(true);
      const foods = await Promise.all(foodIds.map(id => CNFApiService.getFoodDetails(id)));
      setPortionMass(prev => {
        const next = { ...prev };
        for (const f of foods) {
          if (next[f.FoodID] == null) next[f.FoodID] = 100;
        }
        return next;
      });
      await runComparison(foods);
    } catch {
      toast.error('Failed to load foods for comparison');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (comparisonData.foods.length >= 2) {
      runComparison(comparisonData.foods).catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [basis]);

  const addCustomNutrient = async (nutrientId: number) => {
    if (customNutrientIds.includes(nutrientId)) return;
    const next = [...customNutrientIds, nutrientId];
    setCustomNutrientIds(next);
    if (comparisonData.foods.length >= 2) {
      await runComparison(comparisonData.foods, next);
    }
  };

  const addFoodToComparison = async (foodId: number) => {
    try {
      if (comparisonData.foods.find(f => f.FoodID === foodId)) {
        toast.error('Food already in comparison');
        return;
      }

      if (comparisonData.foods.length >= 6) {
        toast.error('Maximum 6 foods can be compared at once');
        return;
      }

      const newFood = await CNFApiService.getFoodDetails(foodId);
      const newFoods = [...comparisonData.foods, newFood];
      setPortionMass(prev => ({ ...prev, [foodId]: prev[foodId] ?? 100 }));
      await runComparison(newFoods);

      setShowAddFood(false);
      setSearchQuery('');
      setSearchResults(null);
      setSelectedFoodIds(new Set());
      toast.success('Food added to comparison');
    } catch (error) {
      console.error('Failed to add food to comparison:', error);
      toast.error('Failed to add food to comparison');
    }
  };

  const addFoodsToComparison = async (foodIds: number[]) => {
    try {
      if (foodIds.length === 0) {
        toast.error('No foods selected');
        return;
      }

      const duplicates = foodIds.filter(id =>
        comparisonData.foods.find(f => f.FoodID === id),
      );

      if (duplicates.length > 0) {
        toast.error(`${duplicates.length} food(s) already in comparison`);
        return;
      }

      if (comparisonData.foods.length + foodIds.length > 6) {
        toast.error('Cannot add all selected foods. Maximum 6 foods can be compared at once');
        return;
      }

      const newFoods = await Promise.all(foodIds.map(id => CNFApiService.getFoodDetails(id)));
      const allFoods = [...comparisonData.foods, ...newFoods];
      setPortionMass(prev => {
        const next = { ...prev };
        for (const f of newFoods) next[f.FoodID] = next[f.FoodID] ?? 100;
        return next;
      });
      await runComparison(allFoods);

      setShowAddFood(false);
      setSearchQuery('');
      setSearchResults(null);
      setSelectedFoodIds(new Set());
      toast.success(`${foodIds.length} food(s) added to comparison`);
    } catch (error) {
      console.error('Failed to add selected foods to comparison:', error);
      toast.error('Failed to add selected foods to comparison');
    }
  };

  const addSelectedFoodsToComparison = () => addFoodsToComparison(Array.from(selectedFoodIds));

  const toggleFoodSelection = (foodId: number) => {
    const newSelection = new Set(selectedFoodIds);
    if (newSelection.has(foodId)) {
      newSelection.delete(foodId);
    } else {
      newSelection.add(foodId);
    }
    setSelectedFoodIds(newSelection);
  };

  const selectAllVisibleFoods = () => {
    if (!searchResults) return;
    
    const availableFoods = searchResults.results.filter(food => 
      !comparisonData.foods.find(f => f.FoodID === food.FoodID)
    );
    
    // Check if all available foods are already selected
    const allSelected = availableFoods.every(food => selectedFoodIds.has(food.FoodID));
    
    if (allSelected) {
      // If all are selected, deselect them
      const newSelection = new Set(selectedFoodIds);
      availableFoods.forEach(food => newSelection.delete(food.FoodID));
      setSelectedFoodIds(newSelection);
    } else {
      // If not all are selected, select all available foods
      const newSelection = new Set(selectedFoodIds);
      availableFoods.forEach(food => newSelection.add(food.FoodID));
      setSelectedFoodIds(newSelection);
    }
  };

  const clearSelection = () => {
    setSelectedFoodIds(new Set());
  };

  const removeFoodFromComparison = async (foodId: number) => {
    try {
      const newFoods = comparisonData.foods.filter(f => f.FoodID !== foodId);
      setPortionMass(prev => {
        const next = { ...prev };
        delete next[foodId];
        return next;
      });
      await runComparison(newFoods);

      toast.success('Food removed from comparison');
    } catch (error) {
      console.error('Failed to remove food from comparison:', error);
      toast.error('Failed to remove food from comparison');
    }
  };

  const searchFoods = async (query: string) => {
    if (!query.trim()) {
      setSearchResults(null);
      setSelectedFoodIds(new Set()); // Clear selection when clearing search
      return;
    }

    try {
      setSearchLoading(true);
      // WAFCT-EXTEND (2026-05-24): forward source so the search respects
      // the modal's scope chip.
      const results = await CNFApiService.searchFoods(query, 20, 0, modalSource);
      setSearchResults(results);
      setSelectedFoodIds(new Set()); // Clear selection when new search results come in
    } catch (error) {
      console.error('Search failed:', error);
      toast.error('Search failed');
    } finally {
      setSearchLoading(false);
    }
  };

  const exportComparisonTableCsv = () => {
    const comp = comparisonData.comparison;
    if (!comp) return;
    const foods = comparisonData.foods;
    const nutrientKeys = Object.keys(comp.nutrients);
    const headers = ['Nutrient', 'Unit', 'Basis', ...foods.map(f => f.FoodDescription), ...foods.map(f => `${f.FoodDescription} (%DV)`)];
    const rows = nutrientKeys.map(key => {
      const entry = comp.nutrients[key];
      const row: unknown[] = [key, entry.unit, comp.basis ?? basis];
      for (const food of foods) {
        const cell = entry.by_food_id[String(food.FoodID)];
        row.push(cell?.value ?? '');
      }
      for (const food of foods) {
        const dv = cellPercentDV(comp, food.FoodID, entry.nutrient_id);
        row.push(dv != null ? dv.toFixed(1) : '');
      }
      return row;
    });
    downloadCsv(
      `food-comparison-table-${new Date().toISOString().split('T')[0]}.csv`,
      toCsv(headers, rows),
    );
  };

  const exportComparison = async (format: 'json' | 'csv' | 'compare_csv') => {
    try {
      if (format === 'compare_csv') {
        exportComparisonTableCsv();
        setShowExportModal(false);
        toast.success('Comparison table exported');
        return;
      }
      const foodIds = comparisonData.foods.map(f => f.FoodID);
      const exportData = await CNFApiService.exportFoodsData(foodIds, {
        format: format === 'json' ? 'json' : 'csv',
        include_nutrients: true,
        include_conversions: true,
      });

      if (format === 'json') {
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `food-comparison-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } else {
        const csvData = convertToCSV(exportData);
        const blob = new Blob(['\ufeff' + csvData], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `food-comparison-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }

      setShowExportModal(false);
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch {
      toast.error('Export failed');
    }
  };

  const convertToCSV = (data: { foods: Food[] }): string => {
    const foods = data.foods;
    if (!foods || foods.length === 0) return '';

    // Get all unique nutrients from all foods
    const allNutrients = new Set<string>();
    foods.forEach((food: Food) => {
      if (food.NutrientValues) {
        food.NutrientValues.forEach((nutrient: NutrientValue) => {
          allNutrients.add(nutrient.NutrientName);
        });
      }
    });

    // Create CSV header
    const headers = ['Food Name', 'Food Code', 'Food Group', ...Array.from(allNutrients)];
    let csv = headers.join(',') + '\n';

    // Add data rows
    foods.forEach((food: Food) => {
      const row = [
        `"${food.FoodDescription}"`,
        food.FoodCode,
        `"${food.FoodGroupName || 'Unknown'}"`,
      ];

      // Add nutrient values
      Array.from(allNutrients).forEach((nutrientName: string) => {
        const nutrient = food.NutrientValues?.find((n: NutrientValue) => n.NutrientName === nutrientName);
        row.push(nutrient ? nutrient.NutrientValue.toString() : '');
      });

      csv += row.join(',') + '\n';
    });

    return csv;
  };

  const sendAllToScorecard = () => {
    if (comparisonData.foods.length === 0) return;
    let estKcal = 0;
    for (const food of comparisonData.foods) {
      const mass = portionMass[food.FoodID] ?? 100;
      const energy = food.NutrientValues?.find(n => n.NutrientID === 208)?.NutrientValue;
      if (energy != null) estKcal += energy * mass / 100;
    }
    const result = appendManyToActiveFoodList(
      comparisonData.foods.map(food => ({
        food_id: food.FoodID,
        food_description: food.FoodDescription,
        food_group: food.FoodGroupName ?? resolveGroupName(food.FoodGroupID),
        mass_g: portionMass[food.FoodID] ?? 100,
      })),
      {
        userType,
        source: 'catalogue_compare',
        list_label: `Compare set (${comparisonData.foods.length} foods)`,
        estimated_daily_kcal: estKcal > 0 ? Math.round(estKcal) : undefined,
        replace: true,
      },
    );
    if (!result.ok) {
      toast.error(result.error ?? 'Could not add foods to Scorecard');
      return;
    }
    toast.success(
      userType === 'individual'
        ? `Added ${result.addedCount ?? comparisonData.foods.length} food(s) to all scores`
        : `Added ${result.addedCount ?? comparisonData.foods.length} food(s) to Scorecard`,
    );
    router.push('/scorecard');
  };

  const importFromScorecard = () => {
    const list = loadActiveFoodList();
    if (!list?.ingredients.length) {
      toast.error('No foods in Scorecard');
      return;
    }
    const ids = list.ingredients.map(i => i.food_id).slice(0, 6);
    const masses: Record<number, number> = {};
    for (const ing of list.ingredients.slice(0, 6)) {
      masses[ing.food_id] = ing.mass_g;
    }
    setPortionMass(masses);
    loadFoodsForComparison(ids);
  };

  const copyShareLink = async () => {
    const ids = comparisonData.foods.map(f => f.FoodID);
    if (!ids.length) return;
    const url = `${window.location.origin}/cnf/compare?foods=${ids.join(',')}`;
    try {
      await navigator.clipboard.writeText(url);
      toast.success('Comparison link copied');
    } catch {
      toast.error('Could not copy link');
    }
  };

  const summaryFoods = comparisonData.comparison?.foods ?? [];
  const showMixedBanner = hasMixedDatabases(
    comparisonData.foods.map(f => f.FoodID),
    summaryFoods.map(f => f.source ?? (f.FoodID >= 700_000 ? 'wafct' : 'cnf')),
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
            <div className="inline-flex items-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
              <span className="ml-2 text-gray-600">Loading comparison data...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const searchTabA11y =
    addFoodMode === 'search'
      ? ({ 'aria-selected': 'true' as const })
      : ({ 'aria-selected': 'false' as const });
  const discoverTabA11y =
    addFoodMode === 'discover'
      ? ({ 'aria-selected': 'true' as const })
      : ({ 'aria-selected': 'false' as const });

  return (
    <div className="min-h-screen bg-gray-50 py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Food Comparison
              </h1>
              <p className="text-gray-600">
                Compare up to six foods side by side, then send the set to all scores for every published measure.
              </p>
            </div>
                              <div className="flex items-center flex-wrap gap-3">
                    <button
                      onClick={() => setShowAddFood(true)}
                      className="btn-primary inline-flex items-center"
                      disabled={comparisonData.foods.length >= 6}
                    >
                      <PlusIcon className="w-4 h-4 mr-2" />
                      Add Food
                    </button>
                    {comparisonData.foods.length > 0 && (
                      <>
                        <button
                          type="button"
                          onClick={copyShareLink}
                          className="btn-outline inline-flex items-center text-sm"
                        >
                          <LinkIcon className="w-4 h-4 mr-2" />
                          Copy link
                        </button>
                        <button
                          type="button"
                          onClick={sendAllToScorecard}
                          className="inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg text-emerald-800 bg-emerald-50 border border-emerald-200 hover:bg-emerald-100"
                        >
                          <SparklesIcon className="w-4 h-4 mr-2" />
                          {userType === 'individual' ? 'Send to all scores' : 'Send to Scorecard'}
                        </button>
                        <button
                          type="button"
                          onClick={() => setShowExportModal(true)}
                          className="btn-outline inline-flex items-center"
                        >
                          <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                          Export
                        </button>
                      </>
                    )}
                  </div>
          </div>
        </div>

        {showMixedBanner && <CompareMixedDbBanner />}

        {comparisonData.foods.length > 0 && (
          <CompareFoodStrip
            foods={summaryFoods.length ? summaryFoods.map(s => ({
              ...s,
              FoodGroup: s.FoodGroup,
            })) : comparisonData.foods.map(f => ({
              FoodID: f.FoodID,
              FoodDescription: f.FoodDescription,
              FoodCode: f.FoodCode,
              FoodGroup: f.FoodGroupName ?? resolveGroupName(f.FoodGroupID),
              FoodGroupID: f.FoodGroupID,
              source: f.FoodID >= 700_000 ? 'wafct' : 'cnf',
            }))}
            userType={userType}
            groupLabel={food => resolveGroupName(food.FoodGroupID ?? 0, food.FoodGroup)}
            portionMass={portionMass}
            onPortionChange={(id, mass) => setPortionMass(prev => ({ ...prev, [id]: mass }))}
            onRemove={removeFoodFromComparison}
            onViewProfile={async (id) => {
              const food = comparisonData.foods.find(f => f.FoodID === id)
                ?? await CNFApiService.getFoodDetails(id);
              setDetailFood(food);
            }}
          />
        )}

        {comparisonData.foods.length === 1 && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4 flex flex-wrap items-center gap-3">
            <InformationCircleIcon className="w-5 h-5 text-blue-500 shrink-0" />
            <p className="text-sm text-blue-800 flex-1">Add one more food to start the comparison table.</p>
            <button type="button" onClick={() => setShowAddFood(true)} className="btn-primary text-sm">
              Add food
            </button>
          </div>
        )}

        {comparisonData.comparison && comparisonData.foods.length > 1 && (
          <>
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <select
                value={basis}
                onChange={e => setBasis(e.target.value as CompareBasis)}
                className="text-xs px-2 py-1.5 border border-gray-300 rounded-lg bg-white"
                aria-label="Comparison basis"
              >
                <option value="per_100g">Per 100 g</option>
                <option value="per_100kcal">Per 100 kcal</option>
              </select>
              <label className="inline-flex items-center gap-1.5 text-xs text-gray-700">
                <input type="checkbox" checked={showDelta} onChange={e => setShowDelta(e.target.checked)} className="rounded" />
                Delta vs first
              </label>
              <label className="inline-flex items-center gap-1.5 text-xs text-gray-700">
                <input type="checkbox" checked={diffOnly} onChange={e => setDiffOnly(e.target.checked)} className="rounded" />
                Differences only
              </label>
              <label className="inline-flex items-center gap-1.5 text-xs text-gray-700">
                <input type="checkbox" checked={transposed} onChange={e => setTransposed(e.target.checked)} className="rounded" />
                Transpose
              </label>
            </div>
            <CompareNutrientTable
              foods={comparisonData.foods}
              comparison={comparisonData.comparison}
              userType={userType}
              basis={basis}
              showDelta={showDelta}
              diffOnly={diffOnly}
              transposed={transposed}
              customNutrientIds={customNutrientIds}
              nutrients={allNutrients}
              onAddCustomNutrient={addCustomNutrient}
            />
          </>
        )}

        {comparisonData.foods.length === 0 && (
          <CompareEmptyState
            activeFoodCount={activeFoodCount}
            onAddFood={() => setShowAddFood(true)}
            onImportScorecard={importFromScorecard}
          />
        )}

        {/* Add Food Modal */}
        {showAddFood && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  Add Food to Comparison
                </h3>
                <button
                  type="button"
                  onClick={() => {
                    setShowAddFood(false);
                    setSelectedFoodIds(new Set());
                    setSearchQuery('');
                    setSearchResults(null);
                  }}
                  className="p-2 text-gray-400 hover:text-gray-600"
                  title="Close"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>
              
              <div className="px-6 py-4">
                <div className="flex gap-1 mb-4 p-1 bg-gray-100 rounded-lg" role="tablist" aria-label="Add food method">
                  <button
                    type="button"
                    role="tab"
                    id="add-food-tab-search"
                    {...searchTabA11y}
                    aria-controls="add-food-panel-search"
                    onClick={() => setAddFoodMode('search')}
                    className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition ${
                      addFoodMode === 'search'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Search by name
                  </button>
                  <button
                    type="button"
                    role="tab"
                    id="add-food-tab-discover"
                    {...discoverTabA11y}
                    aria-controls="add-food-panel-discover"
                    onClick={() => setAddFoodMode('discover')}
                    className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition inline-flex items-center justify-center gap-1.5 ${
                      addFoodMode === 'discover'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <BeakerIcon className="w-4 h-4" aria-hidden="true" />
                    Discover by nutrient
                  </button>
                </div>

                {addFoodMode === 'discover' ? (
                  <div id="add-food-panel-discover" role="tabpanel" aria-labelledby="add-food-tab-discover">
                    <NutrientDiscoverPanel
                      compact
                      userType={userType}
                      resolveGroupName={resolveGroupName}
                      onAddFood={addFoodToComparison}
                      onAddFoods={addFoodsToComparison}
                      maxSelections={6 - comparisonData.foods.length}
                      excludeFoodIds={comparisonData.foods.map(f => f.FoodID)}
                    />
                  </div>
                ) : (
                <div id="add-food-panel-search" role="tabpanel" aria-labelledby="add-food-tab-search">
                <>
                {/* WAFCT-EXTEND (2026-05-24): scope picker — applies to BOTH
                    the basic-text search and the AI ranker below. */}
                <div className="mb-3">
                  <SourceFilter source={modalSource} onChange={setModalSource} accent="green" />
                </div>

                {/* Search */}
                <div className="relative mb-3">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    placeholder="Search foods to add (e.g. 'apple', 'salmon', 'fonio', 'baobab')..."
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      searchFoods(e.target.value);
                    }}
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>

                {/* AI-enhanced ranker — same pattern as the main /cnf/search page */}
                <div className="mb-4">
                  <AIEnhancedSearch
                    query={searchQuery}
                    userType={userType}
                    accent="green"
                    source={modalSource}
                    onSelect={(food) => {
                      addFoodToComparison(food.food_id);
                    }}
                  />
                </div>

                {/* Search Results */}
                {searchLoading && (
                  <div className="text-center py-8">
                    <div className="inline-flex items-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
                      <span className="ml-2 text-gray-600">Searching...</span>
                    </div>
                  </div>
                )}

                {searchResults && (
                  <div className="space-y-4">
                    {/* Selection Controls */}
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-4">
                        <button
                          onClick={selectAllVisibleFoods}
                          className="text-sm text-primary-600 hover:text-primary-700"
                        >
                          {(() => {
                            if (!searchResults) return 'Select All';
                            const availableFoods = searchResults.results.filter(food => 
                              !comparisonData.foods.find(f => f.FoodID === food.FoodID)
                            );
                            const allSelected = availableFoods.every(food => selectedFoodIds.has(food.FoodID));
                            return allSelected && availableFoods.length > 0 ? 'Deselect All' : 'Select All';
                          })()}
                        </button>
                        <button
                          onClick={clearSelection}
                          className="text-sm text-gray-600 hover:text-gray-700"
                        >
                          Clear
                        </button>
                        <span className="text-sm text-gray-600">
                          {selectedFoodIds.size} selected
                        </span>
                      </div>
                      {selectedFoodIds.size > 0 && (
                        <button
                          onClick={addSelectedFoodsToComparison}
                          className="btn-primary text-sm py-1 px-3"
                        >
                          Add Selected ({selectedFoodIds.size})
                        </button>
                      )}
                    </div>

                    {/* Search Results List */}
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {searchResults.results.map((food) => {
                        const isAlreadyAdded = comparisonData.foods.find(f => f.FoodID === food.FoodID) !== undefined;
                        const isSelected = selectedFoodIds.has(food.FoodID);
                        
                        return (
                          <div
                            key={food.FoodID}
                            className={`flex items-center p-3 border rounded-lg transition-colors ${
                              isSelected ? 'border-primary-300 bg-primary-50' : 'border-gray-200 hover:bg-gray-50'
                            } ${isAlreadyAdded ? 'opacity-50' : ''}`}
                          >
                            <div className="flex items-center flex-1">
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => toggleFoodSelection(food.FoodID)}
                                disabled={isAlreadyAdded}
                                aria-label={`Select ${food.FoodDescription}`}
                                className="mr-3 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                              />
                              <div className="flex-1">
                                <div className="flex items-center gap-1.5">
                                  <h4 className="text-sm font-medium text-gray-900">
                                    {food.FoodDescription}
                                  </h4>
                                  {/* WAFCT-EXTEND (2026-05-24): per-row provenance */}
                                  <SourceBadge foodId={food.FoodID} userType={userType} />
                                </div>
                                <p className="text-xs text-gray-500">
                                  Code: {food.FoodCode} • Group: {food.FoodGroupID}
                                </p>
                              </div>
                            </div>
                            <div className="flex space-x-2">
                              <button
                                onClick={() => addFoodToComparison(food.FoodID)}
                                className="btn-primary text-sm py-1 px-3"
                                disabled={isAlreadyAdded}
                              >
                                {isAlreadyAdded ? 'Added' : 'Add'}
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {searchQuery && !searchLoading && searchResults && searchResults.results.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No foods found matching &quot;{searchQuery}&quot;
                  </div>
                )}

                {!searchQuery && (
                  <div className="text-center py-8 text-gray-500 space-y-1">
                    <div className="font-medium text-gray-700">Start typing to search for foods</div>
                    <div className="text-xs">
                      Searching <strong>{
                        modalSource === 'both'   ? 'CNF + WAFCT + FDC + CIQUAL' :
                        modalSource === 'cnf'    ? 'CNF only' :
                        modalSource === 'wafct'  ? 'WAFCT only' :
                        modalSource === 'fdc'    ? 'FDC only' :
                                                   'CIQUAL only'
                      }</strong> —
                      try <code className="bg-gray-100 px-1 rounded">apple</code>,{' '}
                      <code className="bg-gray-100 px-1 rounded">salmon</code>,{' '}
                      <code className="bg-gray-100 px-1 rounded">fonio</code>, or{' '}
                      <code className="bg-gray-100 px-1 rounded">baobab</code>.
                      Or use <strong>Discover by nutrient</strong> to find foods by iron, fibre, sodium, and more.
                    </div>
                  </div>
                )}
                </>
                </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Export Modal */}
        {showExportModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl shadow-xl max-w-md w-full">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  Export Comparison Data
                </h3>
                <button
                  type="button"
                  onClick={() => setShowExportModal(false)}
                  className="p-2 text-gray-400 hover:text-gray-600"
                  title="Close"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>
              
              <div className="px-6 py-4">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Export Format
                    </label>
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="exportFormat"
                          value="compare_csv"
                          checked={exportFormat === 'compare_csv'}
                          onChange={() => setExportFormat('compare_csv')}
                          className="mr-2"
                        />
                        <span className="text-sm">Comparison table CSV (current view)</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="exportFormat"
                          value="json"
                          checked={exportFormat === 'json'}
                          onChange={() => setExportFormat('json')}
                          className="mr-2"
                        />
                        <span className="text-sm">JSON (full food profiles)</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="exportFormat"
                          value="csv"
                          checked={exportFormat === 'csv'}
                          onChange={() => setExportFormat('csv')}
                          className="mr-2"
                        />
                        <span className="text-sm">CSV (nutrients as columns)</span>
                      </label>
                    </div>
                  </div>
                  
                  <div className="text-sm text-gray-600">
                    <p>
                      {exportFormat === 'compare_csv'
                        ? 'Exports the side-by-side comparison table with %DV columns for the current basis.'
                        : exportFormat === 'json'
                          ? 'Exports complete food data including all nutrients and conversion factors.'
                          : 'Exports food data in a spreadsheet-friendly format with nutrients as columns.'}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowExportModal(false)}
                  className="btn-outline"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => exportComparison(exportFormat)}
                  className="btn-primary"
                >
                  Export {exportFormat === 'compare_csv' ? 'table CSV' : exportFormat.toUpperCase()}
                </button>
              </div>
            </div>
          </div>
        )}
        {detailFood && (
          <FoodDetailDrawer
            food={detailFood}
            userType={userType}
            groupLabel={resolveGroupName(detailFood.FoodGroupID, detailFood.FoodGroupName)}
            onClose={() => setDetailFood(null)}
          />
        )}
      </div>
    </div>
  );
}

export default function CNFComparePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
            <div className="inline-flex items-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
              <span className="ml-2 text-gray-600">Loading comparison page...</span>
            </div>
          </div>
        </div>
      </div>
    }>
      <CNFComparePageContent />
    </Suspense>
  );
} 