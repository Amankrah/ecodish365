'use client';

import React, { useState, useEffect } from 'react';
import { 
  CubeIcon,
  ChevronRightIcon,
  EyeIcon,
  MagnifyingGlassIcon,
  ListBulletIcon,
  Squares2X2Icon,
  InformationCircleIcon,
  ScaleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { CNFApiService, FoodGroup, Food } from '@/lib/api';
import Link from 'next/link';
import toast from 'react-hot-toast';

interface FoodGroupWithFoods extends FoodGroup {
  foods?: Partial<Food>[];
  count?: number;
}

export default function CNFGroupsPage() {
  const [foodGroups, setFoodGroups] = useState<FoodGroupWithFoods[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<FoodGroupWithFoods | null>(null);
  const [groupFoods, setGroupFoods] = useState<Partial<Food>[]>([]);
  const [selectedFoods, setSelectedFoods] = useState<number[]>([]);
  const [selectedFood, setSelectedFood] = useState<Food | null>(null);
  const [loading, setLoading] = useState(true);
  const [foodsLoading, setFoodsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  useEffect(() => {
    loadFoodGroups();
  }, []);

  const loadFoodGroups = async () => {
    try {
      setLoading(true);
      const groups = await CNFApiService.getFoodGroups();
      setFoodGroups(groups);
    } catch (error) {
      console.error('Failed to load food groups:', error);
      toast.error('Failed to load food groups');
    } finally {
      setLoading(false);
    }
  };

  const loadFoodsForGroup = async (group: FoodGroupWithFoods) => {
    try {
      setFoodsLoading(true);
      setSelectedGroup(group);
      
      const result = await CNFApiService.getFoodsByGroup(group.FoodGroupID, 200);
      setGroupFoods(result.foods);
    } catch (error) {
      console.error('Failed to load foods for group:', error);
      toast.error('Failed to load foods for group');
    } finally {
      setFoodsLoading(false);
    }
  };

  const toggleFoodSelection = (foodId: number) => {
    setSelectedFoods(prev => 
      prev.includes(foodId) 
        ? prev.filter(id => id !== foodId)
        : [...prev, foodId]
    );
  };

  const clearSelections = () => {
    setSelectedFoods([]);
  };

  const loadFoodDetails = async (foodId: number) => {
    try {
      const food = await CNFApiService.getFoodDetails(foodId);
      setSelectedFood(food);
    } catch (error) {
      console.error('Failed to load food details:', error);
      toast.error('Failed to load food details');
    }
  };

  const getFilteredFoods = () => {
    if (!searchQuery.trim()) return groupFoods;
    
    return groupFoods.filter(food => 
      food.FoodDescription?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      food.FoodCode?.toLowerCase().includes(searchQuery.toLowerCase())
    );
  };

  const getFoodGroupIcon = (groupName: string) => {
    // Simple mapping based on common food group names
    const iconMap: Record<string, string> = {
      'dairy': '🥛',
      'meat': '🥩',
      'poultry': '🐔',
      'fish': '🐟',
      'seafood': '🦐',
      'vegetable': '🥬',
      'fruit': '🍎',
      'grain': '🌾',
      'cereal': '🥣',
      'bread': '🍞',
      'legume': '🫘',
      'bean': '🫘',
      'nut': '🥜',
      'oil': '🫒',
      'fat': '🧈',
      'sugar': '🍯',
      'sweet': '🍰',
      'beverage': '🥤',
      'spice': '🌶️',
      'herb': '🌿',
    };

    for (const [key, icon] of Object.entries(iconMap)) {
      if (groupName.toLowerCase().includes(key)) {
        return icon;
      }
    }
    return '🍽️';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
            <div className="inline-flex items-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
              <span className="ml-2 text-gray-600">Loading food groups...</span>
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
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Browse by Food Groups
              </h1>
              <p className="text-gray-600">
                Explore foods organized by their nutritional categories and food groups
              </p>
            </div>
            {selectedFoods.length > 0 && (
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-600">
                  {selectedFoods.length} selected
                </span>
                <Link
                  href={`/cnf/compare?foods=${selectedFoods.join(',')}`}
                  className="btn-primary inline-flex items-center"
                >
                  <ScaleIcon className="w-4 h-4 mr-2" />
                  Compare Selected
                </Link>
                <button
                  onClick={clearSelections}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Clear
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Food Groups Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Food Groups ({foodGroups.length})
              </h2>
              <div className="space-y-2">
                {foodGroups.map((group) => (
                  <button
                    key={group.FoodGroupID}
                    onClick={() => loadFoodsForGroup(group)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedGroup?.FoodGroupID === group.FoodGroupID
                        ? 'bg-primary-50 text-primary-700 border border-primary-200'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-lg">{getFoodGroupIcon(group.FoodGroupName)}</span>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900 truncate">
                          {group.FoodGroupName}
                        </div>
                        <div className="text-xs text-gray-500">
                          ID: {group.FoodGroupID}
                        </div>
                      </div>
                      <ChevronRightIcon className="w-4 h-4 text-gray-400" />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Foods Content */}
          <div className="lg:col-span-3">
            {!selectedGroup ? (
              // Welcome State
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
                <CubeIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Select a Food Group
                </h3>
                <p className="text-gray-600 mb-6">
                  Choose a food group from the sidebar to explore its foods
                </p>
                <div className="text-sm text-gray-500">
                  {foodGroups.length} food groups available
                </div>
              </div>
            ) : (
              // Foods List
              <div className="bg-white rounded-xl shadow-sm border border-gray-200">
                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-200">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                        <span className="text-xl mr-2">{getFoodGroupIcon(selectedGroup.FoodGroupName)}</span>
                        {selectedGroup.FoodGroupName}
                      </h2>
                      <p className="text-sm text-gray-600">
                        {getFilteredFoods().length} foods in this group
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={() => setViewMode('grid')}
                        className={`p-2 rounded-lg ${
                          viewMode === 'grid' 
                            ? 'bg-primary-100 text-primary-600' 
                            : 'text-gray-400 hover:text-gray-600'
                        }`}
                        title="Grid view"
                      >
                        <Squares2X2Icon className="w-4 h-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setViewMode('list')}
                        className={`p-2 rounded-lg ${
                          viewMode === 'list' 
                            ? 'bg-primary-100 text-primary-600' 
                            : 'text-gray-400 hover:text-gray-600'
                        }`}
                        title="List view"
                      >
                        <ListBulletIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Search */}
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <MagnifyingGlassIcon className="h-4 w-4 text-gray-400" />
                    </div>
                    <input
                      type="text"
                      placeholder="Search foods in this group..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                    />
                  </div>
                </div>

                {/* Loading */}
                {foodsLoading && (
                  <div className="p-8 text-center">
                    <div className="inline-flex items-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
                      <span className="ml-2 text-gray-600">Loading foods...</span>
                    </div>
                  </div>
                )}

                {/* Foods */}
                {!foodsLoading && (
                  <div className="p-6">
                    {getFilteredFoods().length === 0 ? (
                      <div className="text-center py-8">
                        <InformationCircleIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">
                          No Foods Found
                        </h3>
                        <p className="text-gray-600">
                          {searchQuery 
                            ? `No foods match "${searchQuery}" in this group`
                            : 'This food group appears to be empty'
                          }
                        </p>
                      </div>
                    ) : (
                      <div className={
                        viewMode === 'grid' 
                          ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4'
                          : 'space-y-3'
                      }>
                        {getFilteredFoods().map((food) => (
                          <div
                            key={food.FoodID}
                            className={`border border-gray-200 rounded-lg transition-colors ${
                              selectedFoods.includes(food.FoodID!)
                                ? 'bg-primary-50 border-primary-200'
                                : 'bg-white hover:bg-gray-50'
                            } ${
                              viewMode === 'grid' ? 'p-4' : 'p-3'
                            }`}
                          >
                            <div className="flex items-center space-x-3">
                              <input
                                type="checkbox"
                                checked={selectedFoods.includes(food.FoodID!)}
                                onChange={() => toggleFoodSelection(food.FoodID!)}
                                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                                aria-label={`Select ${food.FoodDescription}`}
                              />
                              <div className="flex-1 min-w-0">
                                <h3 className={`font-medium text-gray-900 ${
                                  viewMode === 'grid' ? 'text-sm mb-1' : 'text-sm'
                                }`}>
                                  {food.FoodDescription}
                                </h3>
                                <div className={`text-xs text-gray-500 ${
                                  viewMode === 'grid' ? 'space-y-1' : 'flex items-center space-x-4'
                                }`}>
                                  <span>Code: {food.FoodCode}</span>
                                  {viewMode === 'grid' && (
                                    <span>Group: {food.FoodGroupID}</span>
                                  )}
                                </div>
                              </div>
                              <button
                                onClick={() => loadFoodDetails(food.FoodID!)}
                                className="p-2 text-gray-400 hover:text-primary-600 transition-colors"
                                title="View Details"
                              >
                                <EyeIcon className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Food Details Modal */}
        {selectedFood && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  Food Details
                </h3>
                <button
                  type="button"
                  onClick={() => setSelectedFood(null)}
                  className="p-2 text-gray-400 hover:text-gray-600"
                  title="Close"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>
              
              <div className="px-6 py-4">
                <div className="mb-4">
                  <h4 className="text-xl font-medium text-gray-900 mb-2">
                    {selectedFood.FoodDescription}
                  </h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Food Code:</span>
                      <span className="ml-2 text-gray-600">{selectedFood.FoodCode}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Food Group:</span>
                      <span className="ml-2 text-gray-600">{selectedFood.FoodGroupID}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Country:</span>
                      <span className="ml-2 text-gray-600">{selectedFood.CountryCode}</span>
                    </div>
                    {selectedFood.ScientificName && (
                      <div>
                        <span className="font-medium text-gray-700">Scientific Name:</span>
                        <span className="ml-2 text-gray-600 italic">{selectedFood.ScientificName}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Nutrients */}
                <div className="mb-4">
                  <h5 className="text-lg font-medium text-gray-900 mb-3">
                    Nutritional Information
                  </h5>
                  <div className="grid grid-cols-1 gap-2 max-h-60 overflow-y-auto">
                    {selectedFood.NutrientValues.map((nutrient, index) => (
                      <div key={index} className="flex justify-between items-center py-2 px-3 bg-gray-50 rounded">
                        <span className="text-sm text-gray-700">{nutrient.NutrientName}</span>
                        <span className="text-sm font-medium text-gray-900">
                          {nutrient.NutrientValue} {nutrient.NutrientUnit}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Conversion Factors */}
                {selectedFood.ConversionFactors.length > 0 && (
                  <div>
                    <h5 className="text-lg font-medium text-gray-900 mb-3">
                      Conversion Factors
                    </h5>
                    <div className="grid grid-cols-1 gap-2">
                      {selectedFood.ConversionFactors.map((conversion, index) => (
                        <div key={index} className="flex justify-between items-center py-2 px-3 bg-gray-50 rounded">
                          <span className="text-sm text-gray-700">{conversion.MeasureDescription}</span>
                          <span className="text-sm font-medium text-gray-900">
                            {conversion.ConversionFactorValue}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 