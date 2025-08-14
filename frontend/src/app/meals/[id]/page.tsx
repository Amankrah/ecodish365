'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { 
  HeartIcon, 
  BookmarkIcon, 
  ShareIcon,
  ClockIcon,
  UserIcon,
  StarIcon,
  GlobeAltIcon,
  ScaleIcon,
  SparklesIcon,
  PencilIcon
} from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon, BookmarkIcon as BookmarkSolidIcon } from '@heroicons/react/24/solid';
import { MealApiService, Meal, CNFApiService, Food, FoodItem } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { isAxiosError } from 'axios';
import Image from 'next/image';

export default function MealDetailPage() {
  const params = useParams();
  const { isAuthenticated, user } = useAuth();
  const [meal, setMeal] = useState<Meal | null>(null);
  const [foodDetails, setFoodDetails] = useState<Record<number, Partial<Food>>>({});
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');

  const mealId = params.id as string;

  const loadMeal = useCallback(async () => {
    setLoading(true);
    try {
      const mealData = await MealApiService.getMeal(mealId);
      setMeal(mealData);

      // Load food details for all food items
      const foodPromises = mealData.food_items.map(async (item: FoodItem) => {
        try {
          const foodDetail = await CNFApiService.getFoodDetails(item.food_id);
          return { [item.food_id]: foodDetail };
        } catch (error) {
          console.error(`Failed to load food ${item.food_id}:`, error);
          return { [item.food_id]: { FoodDescription: `Food ID ${item.food_id}`, FoodID: item.food_id, FoodCode: String(item.food_id), FoodDescriptionF: '', FoodGroupID: 0, FoodSourceID: 0, NutrientValues: [], ConversionFactors: [] } } as Record<number, Partial<Food>>;
        }
      });

      const foodResults: Array<Record<number, Partial<Food>>> = await Promise.all(foodPromises);
      const foodDetailsMap = foodResults.reduce<Record<number, Partial<Food>>>((acc, curr) => ({ ...acc, ...curr }), {} as Record<number, Partial<Food>>);
      setFoodDetails(foodDetailsMap);
    } catch (err: unknown) {
      if (isAxiosError(err) && err.response?.status === 404) {
        setError('Meal not found');
      } else {
        setError('Failed to load meal');
      }
    } finally {
      setLoading(false);
    }
  }, [mealId]);

  useEffect(() => {
    if (mealId) {
      loadMeal();
    }
  }, [loadMeal, mealId]);

  const handleLike = async () => {
    if (!isAuthenticated || !meal || actionLoading) return;
    
    setActionLoading(true);
    try {
      if (meal.is_liked) {
        await MealApiService.unlikeMeal(meal.id);
        setMeal({
          ...meal,
          is_liked: false,
          likes_count: meal.likes_count - 1
        });
      } else {
        await MealApiService.likeMeal(meal.id);
        setMeal({
          ...meal,
          is_liked: true,
          likes_count: meal.likes_count + 1
        });
      }
    } catch (error) {
      console.error('Failed to toggle like:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSave = async () => {
    if (!isAuthenticated || !meal || actionLoading) return;
    
    setActionLoading(true);
    try {
      if (meal.is_saved) {
        await MealApiService.unsaveMeal(meal.id);
        setMeal({
          ...meal,
          is_saved: false,
          saves_count: meal.saves_count - 1
        });
      } else {
        await MealApiService.saveMeal(meal.id);
        setMeal({
          ...meal,
          is_saved: true,
          saves_count: meal.saves_count + 1
        });
      }
    } catch (error) {
      console.error('Failed to toggle save:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const formatTime = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  };

  const getDifficultyColor = (level: string) => {
    switch (level) {
      case 'easy': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'hard': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading meal...</p>
        </div>
      </div>
    );
  }

  if (error || !meal) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">{error || 'Meal not found'}</h1>
          <p className="mt-2 text-gray-600">
            The meal you&apos;re looking for doesn&apos;t exist or has been removed.
          </p>
          <Link
            href="/meals"
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-gradient-primary hover:opacity-90"
          >
            Browse Meals
          </Link>
        </div>
      </div>
    );
  }

  const totalTime = (meal.preparation_time ?? 0) + (meal.cooking_time ?? 0);
  const canEdit = user?.id === meal.creator;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-3">
                {meal.is_featured && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    Featured
                  </span>
                )}
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getDifficultyColor(meal.difficulty_level)}`}>
                  {meal.difficulty_level}
                </span>
              </div>
              <h1 className="mt-2 text-3xl font-bold text-gray-900">{meal.name}</h1>
              <div className="mt-2 flex items-center space-x-6 text-sm text-gray-500">
                <div className="flex items-center space-x-1">
                  <UserIcon className="w-4 h-4" />
                  <span>{meal.creator}</span>
                </div>
                {totalTime > 0 && (
                  <div className="flex items-center space-x-1">
                    <ClockIcon className="w-4 h-4" />
                    <span>{formatTime(totalTime)}</span>
                  </div>
                )}
                <div className="flex items-center space-x-1">
                  <span className="capitalize">{meal.meal_type}</span>
                  <span>•</span>
                  <span>{meal.servings} serving{meal.servings !== 1 ? 's' : ''}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {canEdit && (
                <Link
                  href={`/meals/${meal.id}/edit`}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  <PencilIcon className="w-4 h-4 mr-2" />
                  Edit
                </Link>
              )}
              
              {isAuthenticated && (
                <>
                  <button
                    onClick={handleLike}
                    disabled={actionLoading}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    {meal.is_liked ? (
                      <HeartSolidIcon className="w-4 h-4 mr-2 text-red-600" />
                    ) : (
                      <HeartIcon className="w-4 h-4 mr-2" />
                    )}
                    {meal.likes_count}
                  </button>

                  <button
                    onClick={handleSave}
                    disabled={actionLoading}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    {meal.is_saved ? (
                      <BookmarkSolidIcon className="w-4 h-4 mr-2 text-primary-600" />
                    ) : (
                      <BookmarkIcon className="w-4 h-4 mr-2" />
                    )}
                    Save
                  </button>
                </>
              )}

              <button className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                <ShareIcon className="w-4 h-4 mr-2" />
                Share
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Image */}
            {meal.image && (
              <div className="aspect-w-16 aspect-h-9 overflow-hidden rounded-lg relative">
                <Image
                  src={meal.image}
                  alt={meal.name}
                  fill
                  sizes="(max-width: 1024px) 100vw, 1024px"
                  className="object-cover"
                  unoptimized
                />
              </div>
            )}

            {/* Description */}
            {meal.description && (
              <div className="card">
                <h2 className="text-xl font-semibold text-gray-900 mb-3">Description</h2>
                <p className="text-gray-700 leading-relaxed">{meal.description}</p>
              </div>
            )}

            {/* Ingredients */}
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Ingredients</h2>
              <div className="space-y-3">
                {meal.food_items.map((item: FoodItem, index: number) => (
                  <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
                    <div>
                      <span className="font-medium text-gray-900">
                        {foodDetails[item.food_id]?.FoodDescription || `Food ID ${item.food_id}`}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600">
                      {item.quantity} {item.unit}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Instructions */}
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Instructions</h2>
              <div className="prose prose-sm max-w-none">
                <p className="text-gray-700 leading-relaxed whitespace-pre-line">{meal.instructions}</p>
              </div>
            </div>

            {/* Tips */}
            {meal.tips && (
              <div className="card">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Tips & Notes</h2>
                <p className="text-gray-700 leading-relaxed whitespace-pre-line">{meal.tips}</p>
              </div>
            )}

            {/* Tags */}
            {meal.tags && meal.tags.length > 0 && (
              <div className="card">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Tags</h2>
                <div className="flex flex-wrap gap-2">
                  {meal.tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-700"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Nutrition Summary */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Nutrition Summary</h3>
              <div className="space-y-3">
                {meal.total_calories && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Calories</span>
                    <span className="font-medium text-gray-900">{Math.round(meal.total_calories)}</span>
                  </div>
                )}
                {'total_protein' in (meal as unknown as Record<string, unknown>) && typeof (meal as unknown as Record<string, unknown>)['total_protein'] === 'number' && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Protein</span>
                    <span className="font-medium text-gray-900">{Math.round((meal as unknown as Record<string, number>)['total_protein'])}g</span>
                  </div>
                )}
                {'total_carbs' in (meal as unknown as Record<string, unknown>) && typeof (meal as unknown as Record<string, unknown>)['total_carbs'] === 'number' && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Carbs</span>
                    <span className="font-medium text-gray-900">{Math.round((meal as unknown as Record<string, number>)['total_carbs'])}g</span>
                  </div>
                )}
                {'total_fat' in (meal as unknown as Record<string, unknown>) && typeof (meal as unknown as Record<string, unknown>)['total_fat'] === 'number' && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Fat</span>
                    <span className="font-medium text-gray-900">{Math.round((meal as unknown as Record<string, number>)['total_fat'])}g</span>
                  </div>
                )}
              </div>
            </div>

            {/* Health Scores */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Health Scores</h3>
              <div className="space-y-3">
                {meal.fcs_score && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <SparklesIcon className="w-4 h-4 text-blue-600" />
                      <span className="text-sm text-gray-600">FCS Score</span>
                    </div>
                    <span className="font-medium text-gray-900">{Math.round(meal.fcs_score)}</span>
                  </div>
                )}
                {meal.hefi_score && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <ScaleIcon className="w-4 h-4 text-green-600" />
                      <span className="text-sm text-gray-600">HEFI Score</span>
                    </div>
                    <span className="font-medium text-gray-900">{Math.round(meal.hefi_score)}</span>
                  </div>
                )}
                {meal.hsr_score && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <StarIcon className="w-4 h-4 text-yellow-600" />
                      <span className="text-sm text-gray-600">HSR Score</span>
                    </div>
                    <span className="font-medium text-gray-900">{Math.round(meal.hsr_score)}</span>
                  </div>
                )}
                {meal.sustainability_score && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <GlobeAltIcon className="w-4 h-4 text-green-600" />
                      <span className="text-sm text-gray-600">Sustainability</span>
                    </div>
                    <span className="font-medium text-gray-900">{Math.round(meal.sustainability_score)}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Timing */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Timing</h3>
              <div className="space-y-3">
                {Boolean(meal.preparation_time) && (meal.preparation_time as number) > 0 && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Prep Time</span>
                    <span className="font-medium text-gray-900">{formatTime(meal.preparation_time as number)}</span>
                  </div>
                )}
                {Boolean(meal.cooking_time) && (meal.cooking_time as number) > 0 && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Cook Time</span>
                    <span className="font-medium text-gray-900">{formatTime(meal.cooking_time as number)}</span>
                  </div>
                )}
                {totalTime > 0 && (
                  <div className="flex items-center justify-between font-medium">
                    <span className="text-sm text-gray-900">Total Time</span>
                    <span className="text-gray-900">{formatTime(totalTime)}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Stats */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Community Stats</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Likes</span>
                  <span className="font-medium text-gray-900">{meal.likes_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Saves</span>
                  <span className="font-medium text-gray-900">{meal.saves_count}</span>
                </div>
                {meal.average_rating && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Rating</span>
                    <div className="flex items-center space-x-1">
                      <StarIcon className="w-4 h-4 text-yellow-500 fill-current" />
                      <span className="font-medium text-gray-900">{meal.average_rating.toFixed(1)}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}