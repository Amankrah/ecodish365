'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  MagnifyingGlassIcon, 
  PlusIcon, 
  XMarkIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { CNFApiService, MealApiService, MealCategory, FoodItem, MealCreateRequest } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { isAxiosError } from 'axios';

interface SearchResult {
  FoodID: number;
  FoodDescription: string;
  relevance: number;
}

export default function MealCreator() {
  const { user } = useAuth();
  const router = useRouter();
  
  // Form state
  const [formData, setFormData] = useState<Omit<MealCreateRequest, 'food_items'>>({
    name: '',
    description: '',
    category: '',
    meal_type: 'lunch',
    is_public: user?.meals_public_by_default || false,
    preparation_time: 0,
    cooking_time: 0,
    servings: 1,
    difficulty_level: 'easy',
    instructions: '',
    tips: '',
    tags: [],
  });
  
  const [foodItems, setFoodItems] = useState<FoodItem[]>([]);
  const [categories, setCategories] = useState<MealCategory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Food search state
  const [foodSearchQuery, setFoodSearchQuery] = useState('');
  const [foodSearchResults, setFoodSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showFoodSearch, setShowFoodSearch] = useState(false);

  // Tag input state
  const [tagInput, setTagInput] = useState('');

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const data = await MealApiService.getCategories();
      setCategories(data);
      if (data.length > 0) {
        setFormData(prev => ({ ...prev, category: data[0].id }));
      }
    } catch (error) {
      console.error('Failed to load categories:', error);
    }
  };

  const searchFoods = async (query: string) => {
    if (query.length < 2) {
      setFoodSearchResults([]);
      return;
    }

    setSearchLoading(true);
    try {
      const results = await CNFApiService.searchFoodsEnhanced({
        query,
        limit: 50
      });
      setFoodSearchResults(results.results);
    } catch (error) {
      console.error('Food search failed:', error);
    } finally {
      setSearchLoading(false);
    }
  };

  const addFoodItem = (food: SearchResult) => {
    const newItem: FoodItem = {
      food_id: food.FoodID,
      quantity: 100,
      unit: 'g'
    };
    setFoodItems([...foodItems, newItem]);
    setFoodSearchQuery('');
    setFoodSearchResults([]);
    setShowFoodSearch(false);
  };

  const removeFoodItem = (index: number) => {
    setFoodItems(foodItems.filter((_, i) => i !== index));
  };

  const updateFoodItem = (index: number, updates: Partial<FoodItem>) => {
    const updatedItems = foodItems.map((item, i) => 
      i === index ? { ...item, ...updates } : item
    );
    setFoodItems(updatedItems);
  };

  const addTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({
        ...formData,
        tags: [...formData.tags, tagInput.trim()]
      });
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter(t => t !== tag)
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (foodItems.length === 0) {
      setError('Please add at least one food item to your meal.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const mealData: MealCreateRequest = {
        ...formData,
        food_items: foodItems
      };
      
      const createdMeal = await MealApiService.createMeal(mealData);
      router.push(`/meals/${createdMeal.id}`);
    } catch (err: unknown) {
      let message = 'Failed to create meal. Please try again.';
      if (isAxiosError(err)) {
        const data = err.response?.data as unknown;
        if (data && typeof data === 'object' && 'message' in data) {
          const maybeMsg = (data as { message?: unknown }).message;
          if (typeof maybeMsg === 'string') message = maybeMsg;
        }
      }
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <style jsx>{``}</style>
      <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Create New Meal</h1>
        <p className="mt-2 text-gray-600">
          Build a healthy meal with nutrition and environmental analysis
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {error && (
          <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        )}

        {/* Basic Information */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Basic Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Meal Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="e.g., Mediterranean Quinoa Bowl"
              />
            </div>

            <div>
              <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
                Category *
              </label>
              <select
                id="category"
                title="Category"
                required
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {formData.category === '' && (
                  <option value="" disabled>
                    Select a category
                  </option>
                )}
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="meal_type" className="block text-sm font-medium text-gray-700 mb-2">
                Meal Type *
              </label>
              <select
                id="meal_type"
                title="Meal Type"
                value={formData.meal_type}
                onChange={(e) => setFormData({...formData, meal_type: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="breakfast">Breakfast</option>
                <option value="lunch">Lunch</option>
                <option value="dinner">Dinner</option>
                <option value="snack">Snack</option>
                <option value="dessert">Dessert</option>
                <option value="beverage">Beverage</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Servings *
              </label>
              <input
                id="servings"
                title="Servings"
                type="number"
                min="1"
                required
                value={formData.servings}
                onChange={(e) => setFormData({...formData, servings: parseInt(e.target.value)})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Describe your meal..."
            />
          </div>
        </div>

        {/* Food Items */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Food Ingredients *</h2>
            <button
              type="button"
              onClick={() => setShowFoodSearch(true)}
              className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Add Food
            </button>
          </div>

          {foodItems.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <InformationCircleIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No food items added yet. Click &quot;Add Food&quot; to start building your meal.</p>
            </div>
          )}

          {/* Food Items List */}
          <div className="space-y-3">
            {foodItems.map((item, index) => (
              <div key={index} className="flex items-center space-x-4 p-3 border border-gray-200 rounded-md">
                <div className="flex-1">
                  <span className="text-sm text-gray-600">Food ID: {item.food_id}</span>
                </div>
                <div className="w-20">
                  <input
                    aria-label="Quantity"
                    title="Quantity"
                    type="number"
                    min="0.1"
                    step="0.1"
                    value={item.quantity}
                    onChange={(e) => updateFoodItem(index, { quantity: parseFloat(e.target.value) })}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                  />
                </div>
                <div className="w-16">
                  <select
                    aria-label="Unit"
                    title="Unit"
                    value={item.unit}
                    onChange={(e) => updateFoodItem(index, { unit: e.target.value })}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                  >
                    <option value="g">g</option>
                    <option value="ml">ml</option>
                    <option value="cup">cup</option>
                    <option value="tbsp">tbsp</option>
                    <option value="tsp">tsp</option>
                  </select>
                </div>
                <button
                  aria-label="Remove food item"
                  title="Remove food item"
                  type="button"
                  onClick={() => removeFoodItem(index)}
                  className="text-red-500 hover:text-red-700"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Food Search Modal */}
        {showFoodSearch && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-96 overflow-hidden">
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Search Foods</h3>
                  <button
                    aria-label="Close food search"
                    title="Close food search"
                    type="button"
                    onClick={() => {
                      setShowFoodSearch(false);
                      setFoodSearchQuery('');
                      setFoodSearchResults([]);
                    }}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="w-5 h-5" />
                  </button>
                </div>
                <div className="mt-3 relative">
                  <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    value={foodSearchQuery}
                    onChange={(e) => {
                      setFoodSearchQuery(e.target.value);
                      searchFoods(e.target.value);
                    }}
                    placeholder="Search for foods..."
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>
              
              <div className="p-4 max-h-64 overflow-y-auto">
                {searchLoading && (
                  <div className="text-center py-4">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mx-auto"></div>
                  </div>
                )}
                
                {foodSearchResults.length === 0 && !searchLoading && foodSearchQuery && (
                  <p className="text-gray-500 text-center py-4">No foods found</p>
                )}
                
                <div className="space-y-2">
                  {foodSearchResults.map((food) => (
                    <button
                      key={food.FoodID}
                      type="button"
                      onClick={() => addFoodItem(food)}
                      className="w-full text-left p-3 border border-gray-200 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                      <div className="text-sm font-medium text-gray-900">
                        {food.FoodDescription}
                      </div>
                      <div className="text-xs text-gray-500">
                        Food ID: {food.FoodID}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Recipe Details */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recipe Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Prep Time (minutes)
              </label>
              <input
                id="preparation_time"
                title="Preparation time"
                type="number"
                min="0"
                value={formData.preparation_time}
                onChange={(e) => setFormData({...formData, preparation_time: parseInt(e.target.value) || 0})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Cook Time (minutes)
              </label>
              <input
                id="cooking_time"
                title="Cooking time"
                type="number"
                min="0"
                value={formData.cooking_time}
                onChange={(e) => setFormData({...formData, cooking_time: parseInt(e.target.value) || 0})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label htmlFor="difficulty_level" className="block text-sm font-medium text-gray-700 mb-2">
                Difficulty
              </label>
              <select
                id="difficulty_level"
                title="Difficulty"
                value={formData.difficulty_level}
                onChange={(e) => setFormData({...formData, difficulty_level: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Instructions *
              </label>
              <textarea
                rows={5}
                required
                value={formData.instructions}
                onChange={(e) => setFormData({...formData, instructions: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="Step-by-step cooking instructions..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tips & Notes
              </label>
              <textarea
                rows={3}
                value={formData.tips}
                onChange={(e) => setFormData({...formData, tips: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="Any helpful tips or substitutions..."
              />
            </div>
          </div>
        </div>

        {/* Tags */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Tags</h2>
          <div className="flex flex-wrap gap-2 mb-4">
            {formData.tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-primary-100 text-primary-800"
              >
                {tag}
                <button
                  aria-label={`Remove tag ${tag}`}
                  title={`Remove tag ${tag}`}
                  type="button"
                  onClick={() => removeTag(tag)}
                  className="ml-2 text-primary-600 hover:text-primary-800"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              </span>
            ))}
          </div>
          <div className="flex space-x-2">
            <input
              type="text"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Add tag (e.g., healthy, quick, vegetarian)"
            />
            <button
              type="button"
              onClick={addTag}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
              Add
            </button>
          </div>
        </div>

        {/* Privacy & Submit */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_public}
                  onChange={(e) => setFormData({...formData, is_public: e.target.checked})}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Make this meal public (others can view and save it)
                </span>
              </label>
            </div>

            <div className="flex space-x-3">
              <button
                type="button"
                onClick={() => router.back()}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-gradient-primary text-white rounded-md hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Creating...' : 'Create Meal'}
              </button>
            </div>
          </div>
        </div>
      </form>
      </div>
    </>
  );
}