'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { 
  ScaleIcon,
  PlusIcon,
  XMarkIcon,
  ArrowDownTrayIcon,
  InformationCircleIcon,
  MagnifyingGlassIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { CNFApiService, FoodComparison, Food, SearchResult, NutrientValue } from '@/lib/api';
import toast from 'react-hot-toast';

interface ComparisonData {
  foods: Food[];
  comparison: FoodComparison | null;
}

const NUTRIENT_CATEGORIES = {
  'Energy': ['ENERGY (KILOCALORIES)', 'ENERGY (KILOJOULES)'],
  'Macronutrients': ['PROTEIN', 'FAT (TOTAL LIPIDS)', 'CARBOHYDRATE, TOTAL (BY DIFFERENCE)', 'FIBRE, TOTAL DIETARY'],
  'Minerals': ['CALCIUM', 'IRON', 'SODIUM', 'POTASSIUM', 'MAGNESIUM', 'PHOSPHORUS', 'ZINC'],
  'Vitamins': ['RETINOL', 'RETINOL ACTIVITY EQUIVALENTS', 'BETA CAROTENE', 'ALPHA-TOCOPHEROL', 'VITAMIN D (INTERNATIONAL UNITS)', 'VITAMIN C', 'THIAMIN', 'RIBOFLAVIN', 'NIACIN', 'TOTAL FOLACIN', 'VITAMIN B-12', 'VITAMIN K'],
  'Fatty Acids': ['FATTY ACIDS, SATURATED, TOTAL', 'FATTY ACIDS, MONOUNSATURATED, TOTAL', 'FATTY ACIDS, POLYUNSATURATED, TOTAL', 'FATTY ACIDS, TRANS, TOTAL', 'CHOLESTEROL'],
};

function CNFComparePageContent() {
  const searchParams = useSearchParams();
  const [comparisonData, setComparisonData] = useState<ComparisonData>({ foods: [], comparison: null });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [showAddFood, setShowAddFood] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('Energy');
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportFormat, setExportFormat] = useState<'json' | 'csv'>('json');
  const [selectedFoodIds, setSelectedFoodIds] = useState<Set<number>>(new Set());

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

  const loadFoodsForComparison = async (foodIds: number[]) => {
    try {
      setLoading(true);
      
      // Load individual food details
      const foodPromises = foodIds.map(id => CNFApiService.getFoodDetails(id));
      const foods = await Promise.all(foodPromises);
      
      // Load comparison data
      const comparison = await CNFApiService.compareFoods(foodIds);
      
      setComparisonData({ foods, comparison });
    } catch (error) {
      console.error('Failed to load foods for comparison:', error);
      toast.error('Failed to load foods for comparison');
    } finally {
      setLoading(false);
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

      // Only call comparison API if we have at least 2 foods
      if (newFoods.length >= 2) {
        const newFoodIds = newFoods.map(f => f.FoodID);
        const newComparison = await CNFApiService.compareFoods(newFoodIds);

        setComparisonData({
          foods: newFoods,
          comparison: newComparison
        });
      } else {
        // Just add the food without comparison data
        setComparisonData({
          foods: newFoods,
          comparison: null
        });
      }

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

  const addSelectedFoodsToComparison = async () => {
    try {
      if (selectedFoodIds.size === 0) {
        toast.error('No foods selected');
        return;
      }

      const selectedIds = Array.from(selectedFoodIds);
      const duplicates = selectedIds.filter(id => 
        comparisonData.foods.find(f => f.FoodID === id)
      );

      if (duplicates.length > 0) {
        toast.error(`${duplicates.length} food(s) already in comparison`);
        return;
      }

      if (comparisonData.foods.length + selectedIds.length > 6) {
        toast.error('Cannot add all selected foods. Maximum 6 foods can be compared at once');
        return;
      }

      // Load all selected foods
      const newFoodPromises = selectedIds.map(id => CNFApiService.getFoodDetails(id));
      const newFoods = await Promise.all(newFoodPromises);
      const allFoods = [...comparisonData.foods, ...newFoods];

      // Only call comparison API if we have at least 2 foods
      if (allFoods.length >= 2) {
        const allFoodIds = allFoods.map(f => f.FoodID);
        const newComparison = await CNFApiService.compareFoods(allFoodIds);

        setComparisonData({
          foods: allFoods,
          comparison: newComparison
        });
      } else {
        // Just add the foods without comparison data
        setComparisonData({
          foods: allFoods,
          comparison: null
        });
      }

      setShowAddFood(false);
      setSearchQuery('');
      setSearchResults(null);
      setSelectedFoodIds(new Set());
      toast.success(`${selectedIds.length} food(s) added to comparison`);
    } catch (error) {
      console.error('Failed to add selected foods to comparison:', error);
      toast.error('Failed to add selected foods to comparison');
    }
  };

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
      
      if (newFoods.length === 0) {
        setComparisonData({ foods: [], comparison: null });
        toast.success('Food removed from comparison');
        return;
      }

      // Only call comparison API if we have at least 2 foods
      if (newFoods.length >= 2) {
        const newFoodIds = newFoods.map(f => f.FoodID);
        const newComparison = await CNFApiService.compareFoods(newFoodIds);

        setComparisonData({
          foods: newFoods,
          comparison: newComparison
        });
      } else {
        // Just update foods without comparison data
        setComparisonData({
          foods: newFoods,
          comparison: null
        });
      }

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
      const results = await CNFApiService.searchFoods(query, 20);
      setSearchResults(results);
      setSelectedFoodIds(new Set()); // Clear selection when new search results come in
    } catch (error) {
      console.error('Search failed:', error);
      toast.error('Search failed');
    } finally {
      setSearchLoading(false);
    }
  };

  const exportComparison = async (format: 'json' | 'csv') => {
    try {
      const foodIds = comparisonData.foods.map(f => f.FoodID);
      const exportData = await CNFApiService.exportFoodsData(foodIds, {
        format: format,
        include_nutrients: true,
        include_conversions: true
      });

      if (format === 'json') {
        // Create and trigger JSON download
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
        // Create CSV data
        const csvData = convertToCSV(exportData);
        const blob = new Blob([csvData], { type: 'text/csv' });
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
      toast.success(`Comparison data exported as ${format.toUpperCase()} successfully`);
    } catch (error) {
      console.error('Export failed:', error);
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

  const getNutrientValue = (foodId: number, nutrientName: string): number | null => {
    if (!comparisonData.comparison) return null;
    
    // Get the food name for this food ID
    const food = comparisonData.foods.find(f => f.FoodID === foodId);
    if (!food) return null;
    
    // Find the nutrient data by matching nutrient names
    const nutrientData = Object.entries(comparisonData.comparison.nutrients).find(
      ([key]) => {
        const keyLower = key.toLowerCase();
        const nutrientLower = nutrientName.toLowerCase();
        
        // Direct match or partial match for common nutrient names
        if (keyLower === nutrientLower || 
            keyLower.includes(nutrientLower) || 
            nutrientLower.includes(keyLower)) {
          return true;
        }
        
        // Special mapping for common nutrients
        const mappings: Record<string, string[]> = {
          'energy': ['energy', 'kilocalories', 'kcal', 'calories'],
          'protein': ['protein', 'prot'],
          'fat': ['fat', 'lipids', 'total lipids'],
          'carbohydrate': ['carbohydrate', 'carb', 'total'],
          'fibre': ['fibre', 'fiber', 'dietary'],
          'calcium': ['calcium', 'ca'],
          'iron': ['iron', 'fe'],
          'magnesium': ['magnesium', 'mg'],
          'phosphorus': ['phosphorus', 'p'],
          'potassium': ['potassium', 'k'],
          'sodium': ['sodium', 'na'],
          'zinc': ['zinc', 'zn'],
          'vitamin a': ['vitamin a', 'retinol', 'retinol activity'],
          'vitamin c': ['vitamin c', 'vitc'],
          'vitamin d': ['vitamin d', 'vitd'],
          'vitamin e': ['vitamin e', 'tocopherol', 'alpha-tocopherol'],
          'vitamin k': ['vitamin k', 'vitk'],
          'thiamine': ['thiamine', 'thiamin', 'thia'],
          'riboflavin': ['riboflavin', 'ribo'],
          'niacin': ['niacin', 'nicotinic acid'],
          'folate': ['folate', 'folic acid', 'folacin'],
          'vitamin b12': ['vitamin b12', 'vitamin b-12', 'b12'],
          'saturated fat': ['saturated', 'fatty acids, saturated'],
          'monounsaturated fat': ['monounsaturated', 'fatty acids, monounsaturated'],
          'polyunsaturated fat': ['polyunsaturated', 'fatty acids, polyunsaturated'],
          'trans fat': ['trans', 'fatty acids, trans'],
          'cholesterol': ['cholesterol', 'chol'],
        };
        
        const searchTerms = mappings[nutrientLower] || [nutrientLower];
        return searchTerms.some(term => keyLower.includes(term));
      }
    );
    
    if (!nutrientData) return null;
    
    // Access by food name (FoodDescription), not food ID
    return nutrientData[1].values[food.FoodDescription] || null;
  };

  const getHighestValue = (nutrientName: string): number => {
    if (!comparisonData.comparison) return 0;
    
    const values = comparisonData.foods.map(food => getNutrientValue(food.FoodID, nutrientName) || 0);
    return Math.max(...values);
  };

  const getValuePercentage = (value: number | null, maxValue: number): number => {
    if (!value || maxValue === 0) return 0;
    return (value / maxValue) * 100;
  };

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
                Compare nutritional profiles of multiple foods side-by-side
              </p>
            </div>
                              <div className="flex items-center space-x-4">
                    <button
                      onClick={() => setShowAddFood(true)}
                      className="btn-primary inline-flex items-center"
                      disabled={comparisonData.foods.length >= 6}
                    >
                      <PlusIcon className="w-4 h-4 mr-2" />
                      Add Food
                    </button>
                    {comparisonData.foods.length > 0 && (
                      <button
                        onClick={() => setShowExportModal(true)}
                        className="btn-outline inline-flex items-center"
                      >
                        <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                        Export Data
                      </button>
                    )}
                  </div>
          </div>
        </div>

        {/* Foods Overview */}
        {comparisonData.foods.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Comparing {comparisonData.foods.length} Foods
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {comparisonData.foods.map((food) => (
                <div key={food.FoodID} className="relative bg-gray-50 rounded-lg p-4">
                  <button
                    type="button"
                    onClick={() => removeFoodFromComparison(food.FoodID)}
                    className="absolute top-2 right-2 p-1 text-gray-400 hover:text-red-500 transition-colors"
                    title="Remove food"
                  >
                    <XMarkIcon className="w-4 h-4" />
                  </button>
                  <div className="pr-6">
                    <h3 className="font-medium text-gray-900 text-sm mb-1">
                      {food.FoodDescription}
                    </h3>
                    <p className="text-xs text-gray-500">
                      Code: {food.FoodCode}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Single Food Message */}
        {comparisonData.foods.length === 1 && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-6">
            <div className="flex items-center">
              <InformationCircleIcon className="w-6 h-6 text-blue-500 mr-3" />
              <div>
                <h3 className="text-sm font-medium text-blue-900">
                  Add Another Food to Start Comparison
                </h3>
                <p className="text-sm text-blue-700 mt-1">
                  Add at least one more food to see nutritional comparisons side-by-side.
                </p>
              </div>
              <button
                onClick={() => setShowAddFood(true)}
                className="btn-primary ml-auto text-sm"
              >
                Add Food
              </button>
            </div>
          </div>
        )}

        {/* Comparison Results */}
        {comparisonData.comparison && comparisonData.foods.length > 1 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
            {/* Category Selector */}
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">
                  Nutritional Comparison
                </h2>
                <div className="flex items-center space-x-2">
                  <InformationCircleIcon className="w-4 h-4 text-gray-400" />
                  <span className="text-xs text-gray-500">
                    Values per 100g • Green bars indicate highest values
                  </span>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {Object.keys(NUTRIENT_CATEGORIES).map((category) => (
                  <button
                    key={category}
                    onClick={() => setSelectedCategory(category)}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                      selectedCategory === category
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {category}
                  </button>
                ))}
              </div>
            </div>

            {/* Comparison Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left px-6 py-3 text-sm font-medium text-gray-900">
                      Food
                    </th>
                    {comparisonData.foods.map((food) => (
                      <th key={food.FoodID} className="text-left px-4 py-3 text-sm font-medium text-gray-900 min-w-[120px]">
                        {food.FoodDescription.length > 30 
                          ? `${food.FoodDescription.substring(0, 30)}...`
                          : food.FoodDescription
                        }
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {(() => {
                    const categoryNutrients = NUTRIENT_CATEGORIES[selectedCategory as keyof typeof NUTRIENT_CATEGORIES];
                    const availableNutrients = categoryNutrients.filter((nutrientName) => {
                      const hasData = comparisonData.foods.some(food => 
                        getNutrientValue(food.FoodID, nutrientName) !== null
                      );
                      if (!hasData) {
                        console.log(`No data found for nutrient: ${nutrientName}`);
                      }
                      return hasData;
                    });

                    if (availableNutrients.length === 0) {
                      return (
                        <tr>
                          <td colSpan={comparisonData.foods.length + 1} className="px-6 py-8 text-center text-gray-500">
                            <div className="flex flex-col items-center">
                              <ExclamationTriangleIcon className="w-8 h-8 text-gray-400 mb-2" />
                              <p className="text-sm">No {selectedCategory.toLowerCase()} data available for the selected foods.</p>
                              <p className="text-xs text-gray-400 mt-1">
                                This food category may not contain detailed {selectedCategory.toLowerCase()} information.
                              </p>
                            </div>
                          </td>
                        </tr>
                      );
                    }

                    return availableNutrients.map((nutrientName) => {
                      const maxValue = getHighestValue(nutrientName);

                      return (
                        <tr key={nutrientName} className="hover:bg-gray-50">
                          <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                            {nutrientName}
                          </td>
                          {comparisonData.foods.map((food) => {
                            const value = getNutrientValue(food.FoodID, nutrientName);
                            const percentage = getValuePercentage(value, maxValue);
                            const isHighest = value === maxValue && value !== null && value > 0;

                            return (
                              <td key={food.FoodID} className="px-4 py-4">
                                {value !== null ? (
                                  <div className="space-y-1">
                                    <div className="flex items-center justify-between">
                                      <span className={`text-sm font-medium ${isHighest ? 'text-green-700' : 'text-gray-900'}`}>
                                        {value.toFixed(2)}
                                      </span>
                                      {isHighest && (
                                        <CheckCircleIcon className="w-4 h-4 text-green-500" />
                                      )}
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                      <div 
                                        className={`h-2 rounded-full transition-all duration-300 ${
                                          isHighest ? 'bg-green-500' : 'bg-primary-500'
                                        }`}
                                        style={{ width: `${percentage}%` }}
                                      />
                                    </div>
                                  </div>
                                ) : (
                                  <div className="flex items-center text-gray-400">
                                    <ExclamationTriangleIcon className="w-4 h-4 mr-1" />
                                    <span className="text-sm">N/A</span>
                                  </div>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    });
                  })()}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Empty State */}
        {comparisonData.foods.length === 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
            <ScaleIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No Foods Selected for Comparison
            </h3>
            <p className="text-gray-600 mb-6">
              Add foods to compare their nutritional profiles side-by-side
            </p>
            <button
              onClick={() => setShowAddFood(true)}
              className="btn-primary inline-flex items-center"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Add Your First Food
            </button>
          </div>
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
                {/* Search */}
                <div className="relative mb-4">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    placeholder="Search for foods to add..."
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      searchFoods(e.target.value);
                    }}
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
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
                                <h4 className="text-sm font-medium text-gray-900">
                                  {food.FoodDescription}
                                </h4>
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
                  <div className="text-center py-8 text-gray-500">
                    Start typing to search for foods
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
                          value="json"
                          checked={exportFormat === 'json'}
                          onChange={(e) => setExportFormat(e.target.value as 'json' | 'csv')}
                          className="mr-2"
                        />
                        <span className="text-sm">JSON (structured data)</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="exportFormat"
                          value="csv"
                          checked={exportFormat === 'csv'}
                          onChange={(e) => setExportFormat(e.target.value as 'json' | 'csv')}
                          className="mr-2"
                        />
                        <span className="text-sm">CSV (spreadsheet format)</span>
                      </label>
                    </div>
                  </div>
                  
                  <div className="text-sm text-gray-600">
                    <p>
                      {exportFormat === 'json' 
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
                  Export {exportFormat.toUpperCase()}
                </button>
              </div>
            </div>
          </div>
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