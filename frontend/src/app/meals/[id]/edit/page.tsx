'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  MagnifyingGlassIcon, 
  PlusIcon, 
  XMarkIcon,
  InformationCircleIcon,
  PhotoIcon,
  VideoCameraIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import { CNFApiService, MealApiService, MealCategory, FoodItem, MealCreateRequest, Meal } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { isAxiosError } from 'axios';

interface SearchResult {
  FoodID: number;
  FoodDescription: string;
  relevance: number;
}

interface MediaFile {
  id: string;
  file: File;
  type: 'image' | 'video';
  preview: string;
  caption: string;
  isPrimary: boolean;
}

export default function EditMealPage() {
  const { user } = useAuth();
  const router = useRouter();
  const params = useParams();
  const mealId = params.id as string;
  
  // Loading states
  const [initialLoading, setInitialLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Form state
  const [formData, setFormData] = useState<Omit<MealCreateRequest, 'food_items'>>({
    name: '',
    description: '',
    category: '',
    meal_type: 'lunch',
    is_public: false,
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

  // Media upload state
  const [mediaFiles, setMediaFiles] = useState<MediaFile[]>([]);
  const [uploadingMedia, setUploadingMedia] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Food search state
  const [foodSearchQuery, setFoodSearchQuery] = useState('');
  const [foodSearchResults, setFoodSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showFoodSearch, setShowFoodSearch] = useState(false);

  // Tag input state
  const [tagInput, setTagInput] = useState('');

  useEffect(() => {
    loadMealData();
    loadCategories();
  }, [mealId]);

  const loadMealData = async () => {
    try {
      const meal: Meal = await MealApiService.getMeal(mealId);
      
      // Check if user can edit this meal
      if (meal.creator !== user?.username) {
        setError('You can only edit your own meals');
        return;
      }

      // Populate form with existing meal data
      setFormData({
        name: meal.name,
        description: meal.description || '',
        category: meal.category.id,
        meal_type: meal.meal_type,
        is_public: meal.is_public,
        preparation_time: meal.preparation_time || 0,
        cooking_time: meal.cooking_time || 0,
        servings: meal.servings,
        difficulty_level: meal.difficulty_level,
        instructions: meal.instructions || '',
        tips: meal.tips || '',
        tags: meal.tags || [],
      });
      
      setFoodItems(meal.food_items || []);
    } catch (err: unknown) {
      let message = 'Failed to load meal data';
      if (isAxiosError(err)) {
        if (err.response?.status === 404) {
          message = 'Meal not found';
        } else if (err.response?.status === 403) {
          message = 'You do not have permission to edit this meal';
        }
      }
      setError(message);
    } finally {
      setInitialLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await MealApiService.getCategories();
      setCategories(data);
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

  // Media handling functions
  const handleMediaUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    Array.from(files).forEach(file => {
      const isImage = file.type.startsWith('image/');
      const isVideo = file.type.startsWith('video/');
      
      if (!isImage && !isVideo) {
        setError('Please upload only image or video files.');
        return;
      }

      const mediaFile: MediaFile = {
        id: Math.random().toString(36).substr(2, 9),
        file,
        type: isImage ? 'image' : 'video',
        preview: URL.createObjectURL(file),
        caption: '',
        isPrimary: mediaFiles.length === 0 // First file is primary by default
      };

      setMediaFiles(prev => [...prev, mediaFile]);
    });

    // Reset the input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeMediaFile = (id: string) => {
    setMediaFiles(prev => {
      const updated = prev.filter(file => file.id !== id);
      // If we removed the primary file, make the first remaining file primary
      if (updated.length > 0 && !updated.some(file => file.isPrimary)) {
        updated[0].isPrimary = true;
      }
      return updated;
    });
  };

  const setPrimaryMedia = (id: string) => {
    setMediaFiles(prev => 
      prev.map(file => ({
        ...file,
        isPrimary: file.id === id
      }))
    );
  };

  const updateMediaCaption = (id: string, caption: string) => {
    setMediaFiles(prev =>
      prev.map(file =>
        file.id === id ? { ...file, caption } : file
      )
    );
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
      
      // Only include media if we have new files to upload
      if (mediaFiles.length > 0) {
        mealData.media_files = mediaFiles.map(mf => mf.file);
        mealData.media_captions = mediaFiles.map(mf => mf.caption);
      }
      
      await MealApiService.updateMeal(mealId, mealData);
      router.push(`/meals/${mealId}`);
    } catch (err: unknown) {
      let message = 'Failed to update meal. Please try again.';
      if (isAxiosError(err)) {
        console.error('Update meal error:', err.response?.data);
        const data = err.response?.data as unknown;
        if (data && typeof data === 'object') {
          if ('message' in data) {
            const maybeMsg = (data as { message?: unknown }).message;
            if (typeof maybeMsg === 'string') message = maybeMsg;
          } else if ('error' in data) {
            const maybeError = (data as { error?: unknown }).error;
            if (typeof maybeError === 'string') message = maybeError;
          } else if ('detail' in data) {
            const maybeDetail = (data as { detail?: unknown }).detail;
            if (typeof maybeDetail === 'string') message = maybeDetail;
          } else {
            // Try to extract any validation errors
            message = `Update failed: ${JSON.stringify(data)}`;
          }
        }
      }
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading meal...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">{error}</h1>
          <button
            onClick={() => router.back()}
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-gradient-primary hover:opacity-90"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      <style jsx>{``}</style>
      <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Edit Meal</h1>
          <p className="mt-2 text-gray-600">
            Update your meal with nutrition and environmental analysis
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
                <p>No food items added yet. Click "Add Food" to start building your meal.</p>
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

          {/* Media Upload */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Photos & Videos</h2>
                <p className="text-sm text-gray-600 mt-1">📸 Upload images and videos to showcase your meal</p>
              </div>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                <PhotoIcon className="w-4 h-4 mr-2" />
                Add Media
              </button>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*,video/*"
              onChange={handleMediaUpload}
              className="hidden"
            />

            {mediaFiles.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <PhotoIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No media files added yet. Click "Add Media" to upload photos or videos of your meal.</p>
              </div>
            )}

            {/* Media Files Grid */}
            {mediaFiles.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {mediaFiles.map((mediaFile) => (
                  <div key={mediaFile.id} className="relative border border-gray-200 rounded-lg overflow-hidden">
                    {/* Media Preview */}
                    <div className="relative h-48 bg-gray-100">
                      {mediaFile.type === 'image' ? (
                        <img
                          src={mediaFile.preview}
                          alt="Meal preview"
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <video
                          src={mediaFile.preview}
                          className="w-full h-full object-cover"
                          controls
                        />
                      )}
                      
                      {/* Primary Badge */}
                      {mediaFile.isPrimary && (
                        <div className="absolute top-2 left-2 bg-yellow-500 text-white text-xs px-2 py-1 rounded-full">
                          Primary
                        </div>
                      )}
                      
                      {/* Remove Button */}
                      <button
                        type="button"
                        onClick={() => removeMediaFile(mediaFile.id)}
                        className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                      
                      {/* Set Primary Button */}
                      {!mediaFile.isPrimary && (
                        <button
                          type="button"
                          onClick={() => setPrimaryMedia(mediaFile.id)}
                          className="absolute bottom-2 right-2 bg-blue-500 text-white text-xs px-2 py-1 rounded-full hover:bg-blue-600"
                        >
                          Set Primary
                        </button>
                      )}
                    </div>
                    
                    {/* Caption Input */}
                    <div className="p-3">
                      <input
                        type="text"
                        value={mediaFile.caption}
                        onChange={(e) => updateMediaCaption(mediaFile.id, e.target.value)}
                        placeholder="Add a caption..."
                        className="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-primary-500"
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

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
                  {loading ? 'Updating...' : 'Update Meal'}
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </>
  );
}