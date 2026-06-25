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
import { MealApiService, Meal } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { isAxiosError } from 'axios';
import Image from 'next/image';

// Interface for food items with additional details from the backend
interface FoodItemWithDetails {
  food_id: number;
  quantity: number;
  unit: string;
  food_description?: string;
}

// Extended meal interface that includes the food_items_with_details property
interface MealWithDetails extends Meal {
  food_items_with_details?: FoodItemWithDetails[];
}

export default function MealDetailPage() {
  const params = useParams();
  const { isAuthenticated, user } = useAuth();
  const [meal, setMeal] = useState<MealWithDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [recalculating, setRecalculating] = useState(false);
  const [error, setError] = useState('');

  const mealId = params.id as string;

  const loadMeal = useCallback(async () => {
    setLoading(true);
    try {
      const mealData = await MealApiService.getMeal(mealId);
      setMeal(mealData);
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

  const handleRecalculate = async () => {
    if (!isAuthenticated || !meal || recalculating) return;
    
    setRecalculating(true);
    try {
      const result = await MealApiService.recalculateMealMetrics(meal.id);
      setMeal(result.meal);
      // You could add a toast notification here
      console.log(result.message);
    } catch (error) {
      console.error('Failed to recalculate metrics:', error);
    } finally {
      setRecalculating(false);
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
  const canEdit = user?.username === meal.creator;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
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
              <h1 className="mt-2 text-4xl font-bold text-gray-900">{meal.name}</h1>
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
                <>
                  <Link
                    href={`/meals/${meal.id}/edit`}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <PencilIcon className="w-4 h-4 mr-2" />
                    Edit
                  </Link>
                  
                  <button
                    onClick={handleRecalculate}
                    disabled={recalculating}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    {recalculating ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
                        Recalculating...
                      </>
                    ) : (
                      <>
                        <SparklesIcon className="w-4 h-4 mr-2" />
                        Recalculate Metrics
                      </>
                    )}
                  </button>
                </>
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="xl:col-span-2 space-y-8">
            {/* Media Gallery */}
            {(meal.primary_media || (meal.media_files && meal.media_files.length > 0)) ? (
              <div className="space-y-4">
                {/* Primary Media */}
                {meal.primary_media && (
                  <div className="relative w-full h-96 overflow-hidden rounded-xl bg-gray-100">
                    {meal.primary_media.media_type === 'image' ? (
                      <Image
                        src={meal.primary_media.file}
                        alt={meal.primary_media.caption || meal.name}
                        fill
                        sizes="(max-width: 1280px) 100vw, 1280px"
                        className="object-cover"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                        }}
                        unoptimized
                      />
                    ) : (
                      <video
                        src={meal.primary_media.file}
                        controls
                        className="w-full h-full object-cover"
                        poster={meal.primary_media.thumbnail}
                        onError={(e) => {
                          // Hide broken video gracefully
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                    )}
                    {meal.primary_media.caption && (
                      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-4">
                        <p className="text-white text-sm">{meal.primary_media.caption}</p>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Additional Media Thumbnails */}
                {meal.media_files && meal.media_files.length > 1 && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {meal.media_files.filter(media => !media.is_primary).map((media) => (
                      <div key={media.id} className="relative w-full h-48 overflow-hidden rounded-lg bg-gray-100 cursor-pointer hover:opacity-90 transition-opacity">
                        {media.media_type === 'image' ? (
                          <Image
                            src={media.file}
                            alt={media.caption || meal.name}
                            fill
                            sizes="(max-width: 768px) 50vw, (max-width: 1200px) 25vw, 200px"
                            className="object-cover"
                            onError={(e) => {
                              e.currentTarget.style.display = 'none';
                            }}
                            unoptimized
                          />
                        ) : (
                          <div className="relative w-full h-full bg-gray-900 flex items-center justify-center">
                            <video
                              src={media.file}
                              className="w-full h-full object-cover"
                              muted
                              preload="metadata"
                              onError={(e) => {
                                e.currentTarget.style.display = 'none';
                              }}
                            />
                            <div className="absolute inset-0 flex items-center justify-center">
                              <div className="bg-black/50 rounded-full p-2">
                                <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                                </svg>
                              </div>
                            </div>
                          </div>
                        )}
                        {media.caption && (
                          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2">
                            <p className="text-white text-xs truncate">{media.caption}</p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : meal.image ? (
              /* Fallback to legacy image field */
              <div className="relative w-full h-96 overflow-hidden rounded-xl bg-gray-100">
                <Image
                  src={meal.image}
                  alt={meal.name}
                  fill
                  sizes="(max-width: 1280px) 100vw, 1280px"
                  className="object-cover"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                  }}
                  unoptimized
                />
              </div>
            ) : (
              /* No media available placeholder */
              <div className="relative w-full h-96 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl flex flex-col items-center justify-center text-gray-400">
                <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <p className="text-lg font-medium">No media available</p>
                <p className="text-sm text-gray-500 mt-1">This meal doesn't have any photos or videos</p>
              </div>
            )}

            {/* Description */}
            {meal.description && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-2xl font-semibold text-gray-900 mb-4">Description</h2>
                <p className="text-gray-700 leading-relaxed text-lg">{meal.description}</p>
              </div>
            )}

            {/* Ingredients */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Ingredients</h2>
              <div className="space-y-4">
                {(meal.food_items_with_details || meal.food_items).map((item: FoodItemWithDetails, index: number) => (
                  <div key={index} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0">
                    <div className="flex-1">
                      <span className="font-medium text-gray-900 text-lg">
                        {item.food_description || `Food ID ${item.food_id}`}
                      </span>
                    </div>
                    <div className="text-lg text-gray-600 ml-6 font-semibold">
                      {item.quantity} {item.unit}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Instructions */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Instructions</h2>
              <div className="prose prose-lg max-w-none">
                <p className="text-gray-700 leading-relaxed whitespace-pre-line text-lg">{meal.instructions}</p>
              </div>
            </div>

            {/* Tips */}
            {meal.tips && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-2xl font-semibold text-gray-900 mb-4">Tips & Notes</h2>
                <p className="text-gray-700 leading-relaxed whitespace-pre-line text-lg">{meal.tips}</p>
              </div>
            )}

            {/* Tags */}
            {meal.tags && meal.tags.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-2xl font-semibold text-gray-900 mb-4">Tags</h2>
                <div className="flex flex-wrap gap-3">
                  {meal.tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center px-4 py-2 rounded-full text-sm bg-gray-100 text-gray-700 font-medium"
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
            {/* Consolidated Environmental Impact */}
            {(meal.sustainability_score || meal.carbon_footprint || meal.environmental_impact) && (
              <div className="bg-gradient-to-br from-green-50 to-emerald-100 rounded-xl p-6 shadow-sm border border-green-200">
                <div className="flex items-center mb-6">
                  <div className="p-3 bg-green-500 rounded-xl mr-4">
                    <GlobeAltIcon className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-green-900">Environmental Impact</h3>
                    <p className="text-sm text-green-700 mt-1">How this meal affects our planet</p>
                  </div>
                </div>
                
                {meal.sustainability_score && (
                  <div className="mb-6 p-4 bg-white/70 rounded-xl">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <span className="text-lg font-semibold text-green-700">Sustainability Score</span>
                        <p className="text-xs text-green-600 mt-1">Overall environmental friendliness (0-100)</p>
                      </div>
                      <span className="text-3xl font-bold text-green-800">{meal.sustainability_score.toFixed(1)}/100</span>
                    </div>
                    <div className="w-full bg-green-200 rounded-full h-3 mb-3">
                      <div 
                        className="bg-gradient-to-r from-green-400 to-green-600 h-3 rounded-full transition-all duration-500" 
                        style={{ width: `${Math.min(meal.sustainability_score, 100)}%` }}
                      ></div>
                    </div>
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-green-600 font-medium">
                        {meal.sustainability_score > 80 ? 'Excellent for the planet' :
                         meal.sustainability_score > 60 ? 'Good environmental choice' :
                         meal.sustainability_score > 40 ? 'Moderate impact' : 'Consider eco-alternatives'}
                      </p>
                      <div className="text-xs text-green-600">
                        {meal.sustainability_score > 80 ? 'Planet-friendly' : 
                         meal.sustainability_score > 60 ? 'Environmentally good' : 
                         meal.sustainability_score > 40 ? 'Room for improvement' : 'High impact'}
                      </div>
                    </div>
                    <div className="mt-3 p-3 bg-green-50 rounded-lg">
                      <p className="text-xs text-green-700">
                        <strong>What this means:</strong> Higher scores mean less harm to the environment. 
                        This considers carbon emissions, water usage, land use, and food processing.
                      </p>
                    </div>
                  </div>
                )}
                
                {(meal.carbon_footprint || meal.carbon_footprint === 0) && (
                  <div className="mb-4 p-4 bg-white/70 rounded-xl">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <span className="text-lg font-semibold text-green-700">Carbon Footprint</span>
                        <p className="text-xs text-green-600 mt-1">Greenhouse gases released to make this meal</p>
                      </div>
                      <span className="text-2xl font-bold text-green-800">{meal.carbon_footprint ? meal.carbon_footprint.toFixed(2) : '0.00'} kg CO₂</span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-green-600">
                      <span>🚗 Equivalent to driving {((meal.carbon_footprint || 0) * 4.1).toFixed(1)} km</span>
                      <span className={`px-2 py-1 rounded ${(meal.carbon_footprint || 0) < 1 ? 'bg-green-200 text-green-800' : (meal.carbon_footprint || 0) < 3 ? 'bg-yellow-200 text-yellow-800' : 'bg-red-200 text-red-800'}`}>
                        {(meal.carbon_footprint || 0) < 1 ? 'Low impact' : (meal.carbon_footprint || 0) < 3 ? 'Moderate' : 'High impact'}
                      </span>
                    </div>
                  </div>
                )}

                {meal.environmental_impact && typeof meal.environmental_impact === 'object' && Object.keys(meal.environmental_impact).length > 0 && (
                  <div className="space-y-3">
                    {(meal.environmental_impact['_monetized_total_cad'] !== undefined && meal.environmental_impact['_monetized_total_cad'] !== null) && (
                      <div className="p-3 bg-white/70 rounded-xl">
                        <div className="flex items-center justify-between mb-1">
                          <div>
                            <span className="text-sm font-semibold text-green-700">Environmental Cost</span>
                            <p className="text-xs text-green-600">True cost of environmental damage</p>
                          </div>
                          <span className="text-lg font-bold text-green-800">${(meal.environmental_impact['_monetized_total_cad'] || 0).toFixed(2)} CAD</span>
                        </div>
                        <p className="text-xs text-green-600">💰 This represents the hidden environmental costs society pays</p>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Environmental action guide */}
                <div className="mt-4 p-4 bg-green-50 rounded-lg">
                  <h4 className="text-sm font-bold text-green-700 mb-2">Making a Difference</h4>
                  <div className="text-xs text-green-600 space-y-1">
                    <p>• <strong>Small changes matter:</strong> Every sustainable meal choice helps</p>
                    <p>• <strong>Share recipes:</strong> Inspire others with your eco-friendly meals</p>
                    <p>• <strong>Buy local:</strong> Choose seasonal, locally-grown ingredients when possible</p>
                    <p>• <strong>Reduce waste:</strong> Plan portions carefully and use leftovers creatively</p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Consolidated Health Impact */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-100 rounded-xl p-6 shadow-sm border border-blue-200">
              <div className="flex items-center mb-6">
                <div className="p-3 bg-blue-500 rounded-xl mr-4">
                  <SparklesIcon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-blue-900">Health Impact</h3>
                  <p className="text-sm text-blue-700 mt-1">How this meal supports your wellbeing</p>
                </div>
              </div>
              
              {(meal.heni_score !== undefined && meal.heni_score !== null) && (
                <div className="mb-6 p-4 bg-white/70 rounded-xl">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <span className="text-lg font-semibold text-blue-700">Healthy Life Impact</span>
                      <p className="text-xs text-blue-600 mt-1">How much healthy time this meal adds to your life</p>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-bold text-blue-800">
                        {meal.heni_score ? (meal.heni_score * 0.5256).toFixed(2) : '0'} min
                      </div>
                      <div className="text-sm text-blue-600">of healthy life</div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-blue-600">
                      {meal.heni_score && meal.heni_score > 0 ? 'This meal supports longevity' :
                       meal.heni_score && meal.heni_score < 0 ? 'Consider healthier alternatives' :
                       'Neutral health impact'}
                    </div>
                    <div className="text-xs text-blue-500">
                      Score: {meal.heni_total_score ? meal.heni_total_score.toFixed(1) : (meal.heni_score ? meal.heni_score.toFixed(1) : '0.0')} µDALY/100kcal
                    </div>
                  </div>
                  <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                    <p className="text-xs text-blue-700">
                      <strong>What this means:</strong> This measures how this meal affects your healthy lifespan. 
                      Positive values mean it may help you live longer and healthier.
                    </p>
                  </div>
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-4 mb-6">
                {meal.fcs_score && (
                  <div className="text-center p-4 bg-white/70 rounded-xl">
                    <div className="text-2xl font-bold text-blue-800">{meal.fcs_score.toFixed(1)}</div>
                    <div className="text-sm text-blue-600 font-medium mb-1">Food Compass Score</div>
                    <div className="text-xs text-blue-500">Overall food healthiness (1-100)</div>
                    <div className={`mt-2 px-2 py-1 rounded text-xs ${
                      meal.fcs_score >= 70 ? 'bg-green-200 text-green-800' :
                      meal.fcs_score >= 31 ? 'bg-yellow-200 text-yellow-800' :
                      'bg-red-200 text-red-800'
                    }`}>
                      {meal.fcs_score >= 70 ? 'Encourage' :
                       meal.fcs_score >= 31 ? 'Moderate' :
                       'Minimize'}
                    </div>
                  </div>
                )}
                {meal.hefi_score && (
                  <div className="text-center p-4 bg-white/70 rounded-xl">
                    <div className="text-2xl font-bold text-blue-800">{meal.hefi_score.toFixed(1)}</div>
                    <div className="text-sm text-blue-600 font-medium mb-1">HEFI Score</div>
                    <div className="text-xs text-blue-500">Canadian healthy eating index (0-80)</div>
                    <div className={`mt-2 px-2 py-1 rounded text-xs ${
                      meal.hefi_score >= 60 ? 'bg-green-200 text-green-800' :
                      meal.hefi_score >= 40 ? 'bg-yellow-200 text-yellow-800' :
                      'bg-red-200 text-red-800'
                    }`}>
                      {meal.hefi_score >= 60 ? 'Excellent diet' :
                       meal.hefi_score >= 40 ? 'Good diet' :
                       'Needs improvement'}
                    </div>
                  </div>
                )}
              </div>
              
              {meal.hsr_score && (
                <div className="p-4 bg-white/70 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <span className="text-lg font-semibold text-blue-700">Health Star Rating</span>
                      <p className="text-xs text-blue-600 mt-1">Australian government nutrition rating (0.5-5 stars)</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      {Array.from({ length: 5 }, (_, i) => {
                        const starValue = i + 1;
                        const rating = meal.hsr_score || 0;
                        if (rating >= starValue) {
                          return <StarIcon key={i} className="w-5 h-5 text-yellow-500 fill-current" />;
                        } else if (rating >= starValue - 0.5) {
                          return (
                            <div key={i} className="relative w-5 h-5">
                              <StarIcon className="w-5 h-5 text-gray-300 fill-current absolute" />
                              <div className="absolute inset-0 overflow-hidden w-1/2">
                                <StarIcon className="w-5 h-5 text-yellow-500 fill-current" />
                              </div>
                            </div>
                          );
                        } else {
                          return <StarIcon key={i} className="w-5 h-5 text-gray-300 fill-current" />;
                        }
                      })}
                      <span className="text-lg font-bold text-blue-800 ml-2">{meal.hsr_score.toFixed(1)}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-blue-600">
                      {meal.hsr_score >= 4 ? 'Excellent nutritional choice' :
                       meal.hsr_score >= 3 ? 'Good nutritional value' :
                       meal.hsr_score >= 2 ? 'Moderate nutrition' :
                       'Limited nutritional benefits'}
                    </div>
                    <div className="text-xs text-blue-500">
                      Higher stars = healthier choice
                    </div>
                  </div>
                </div>
              )}
              
              {/* Health action guide */}
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <h4 className="text-sm font-bold text-blue-700 mb-2">Health Tips</h4>
                <div className="text-xs text-blue-600 space-y-1">
                  <p>• <strong>Balance is key:</strong> Combine different food groups for optimal nutrition</p>
                  <p>• <strong>Mindful eating:</strong> Eat slowly and pay attention to your body's signals</p>
                  <p>• <strong>Regular meals:</strong> Consistent eating patterns support your health</p>
                  <p>• <strong>Stay active:</strong> Good nutrition works best with regular movement</p>
                </div>
              </div>
            </div>
            
            {/* Nutrition Summary - Enhanced */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center mb-6">
                <div className="p-3 bg-orange-500 rounded-xl mr-4">
                  <ScaleIcon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">Nutrition Facts</h3>
                  <p className="text-sm text-gray-600 mt-1">Key nutrients in this meal</p>
                </div>
              </div>
              <div className="space-y-4">
                {meal.total_calories && meal.total_calories > 0 ? (
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <span className="text-lg font-semibold text-gray-700">Calories</span>
                      <p className="text-xs text-gray-500 mt-1">Energy this meal provides</p>
                    </div>
                    <div className="text-right">
                      <span className="text-2xl font-bold text-gray-900">{Math.round(meal.total_calories)}</span>
                      <div className="text-xs text-gray-500">
                        {meal.total_calories < 300 ? 'Light meal' :
                         meal.total_calories < 600 ? 'Moderate meal' :
                         meal.total_calories < 800 ? 'Substantial meal' : 'Large meal'}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <span className="text-lg font-semibold text-gray-700">Calories</span>
                      <p className="text-xs text-gray-500 mt-1">Energy this meal provides</p>
                    </div>
                    <span className="text-lg text-gray-400">Not calculated</span>
                  </div>
                )}
                
                {meal.total_weight_grams && meal.total_weight_grams > 0 && (
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-lg font-semibold text-gray-700">Total Weight</span>
                    <span className="text-2xl font-bold text-gray-900">{Math.round(meal.total_weight_grams)}g</span>
                  </div>
                )}
                
                {meal.nutrient_profile && typeof meal.nutrient_profile === 'object' && Object.keys(meal.nutrient_profile).length > 0 ? (
                  <>
                    {/* Try multiple possible protein column names */}
                    {(meal.nutrient_profile['PROTEIN'] || meal.nutrient_profile['Protein'] || meal.nutrient_profile['protein']) ? (
                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <span className="text-lg font-semibold text-gray-700">Protein</span>
                          <p className="text-xs text-gray-500 mt-1">Builds and repairs muscles</p>
                        </div>
                        <div className="text-right">
                          <span className="text-2xl font-bold text-gray-900">
                            {Math.round(meal.nutrient_profile['PROTEIN'] || meal.nutrient_profile['Protein'] || meal.nutrient_profile['protein'])}g
                          </span>
                          <div className="text-xs text-gray-500">
                            {Math.round((meal.nutrient_profile['PROTEIN'] || meal.nutrient_profile['Protein'] || meal.nutrient_profile['protein']) * 4)} cal from protein
                          </div>
                        </div>
                      </div>
                    ) : null}
                    
                    {/* Try multiple possible carbohydrate column names */}
                    {(meal.nutrient_profile['CARBOHYDRATE, TOTAL (BY DIFFERENCE)'] || 
                      meal.nutrient_profile['CARBOHYDRATE'] || 
                      meal.nutrient_profile['Carbohydrate'] || 
                      meal.nutrient_profile['carbohydrate']) ? (
                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <span className="text-lg font-semibold text-gray-700">Carbs</span>
                          <p className="text-xs text-gray-500 mt-1">Main energy source for your body</p>
                        </div>
                        <div className="text-right">
                          <span className="text-2xl font-bold text-gray-900">
                            {Math.round(
                              meal.nutrient_profile['CARBOHYDRATE, TOTAL (BY DIFFERENCE)'] || 
                              meal.nutrient_profile['CARBOHYDRATE'] || 
                              meal.nutrient_profile['Carbohydrate'] || 
                              meal.nutrient_profile['carbohydrate']
                            )}g
                          </span>
                          <div className="text-xs text-gray-500">
                            {Math.round((meal.nutrient_profile['CARBOHYDRATE, TOTAL (BY DIFFERENCE)'] || meal.nutrient_profile['CARBOHYDRATE'] || meal.nutrient_profile['Carbohydrate'] || meal.nutrient_profile['carbohydrate']) * 4)} cal from carbs
                          </div>
                        </div>
                      </div>
                    ) : null}
                    
                    {/* Try multiple possible fat column names */}
                    {(meal.nutrient_profile['FAT (TOTAL LIPIDS)'] || 
                      meal.nutrient_profile['FAT'] || 
                      meal.nutrient_profile['Fat'] || 
                      meal.nutrient_profile['fat']) ? (
                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <span className="text-lg font-semibold text-gray-700">Fat</span>
                          <p className="text-xs text-gray-500 mt-1">🧄 Essential for vitamins and brain health</p>
                        </div>
                        <div className="text-right">
                          <span className="text-2xl font-bold text-gray-900">
                            {Math.round(
                              meal.nutrient_profile['FAT (TOTAL LIPIDS)'] || 
                              meal.nutrient_profile['FAT'] || 
                              meal.nutrient_profile['Fat'] || 
                              meal.nutrient_profile['fat']
                            )}g
                          </span>
                          <div className="text-xs text-gray-500">
                            {Math.round((meal.nutrient_profile['FAT (TOTAL LIPIDS)'] || meal.nutrient_profile['FAT'] || meal.nutrient_profile['Fat'] || meal.nutrient_profile['fat']) * 9)} cal from fat
                          </div>
                        </div>
                      </div>
                    ) : null}
                    
                    {/* Try multiple possible fiber column names */}
                    {(meal.nutrient_profile['FIBRE, TOTAL DIETARY'] || 
                      meal.nutrient_profile['FIBER'] || 
                      meal.nutrient_profile['Fiber'] || 
                      meal.nutrient_profile['fiber']) ? (
                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <span className="text-lg font-semibold text-gray-700">Fiber</span>
                          <p className="text-xs text-gray-500 mt-1">Supports digestion and heart health</p>
                        </div>
                        <div className="text-right">
                          <span className="text-2xl font-bold text-gray-900">
                            {Math.round(
                              meal.nutrient_profile['FIBRE, TOTAL DIETARY'] || 
                              meal.nutrient_profile['FIBER'] || 
                              meal.nutrient_profile['Fiber'] || 
                              meal.nutrient_profile['fiber']
                            )}g
                          </span>
                          <div className="text-xs text-gray-500">
                            {Math.round((meal.nutrient_profile['FIBRE, TOTAL DIETARY'] || meal.nutrient_profile['FIBER'] || meal.nutrient_profile['Fiber'] || meal.nutrient_profile['fiber']) / 25 * 100)}% of daily needs
                          </div>
                        </div>
                      </div>
                    ) : null}
                    
                    {/* Try multiple possible sodium column names */}
                    {(meal.nutrient_profile['SODIUM'] || 
                      meal.nutrient_profile['Sodium'] || 
                      meal.nutrient_profile['sodium']) ? (
                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <span className="text-lg font-semibold text-gray-700">Sodium</span>
                          <p className="text-xs text-gray-500 mt-1">🧂 Essential mineral, but limit intake</p>
                        </div>
                        <div className="text-right">
                          <span className="text-2xl font-bold text-gray-900">
                            {Math.round(
                              meal.nutrient_profile['SODIUM'] || 
                              meal.nutrient_profile['Sodium'] || 
                              meal.nutrient_profile['sodium']
                            )}mg
                          </span>
                          <div className={`text-xs ${
                            (meal.nutrient_profile['SODIUM'] || meal.nutrient_profile['Sodium'] || meal.nutrient_profile['sodium']) > 800 ?
                            'text-red-500' : (meal.nutrient_profile['SODIUM'] || meal.nutrient_profile['Sodium'] || meal.nutrient_profile['sodium']) > 400 ?
                            'text-yellow-600' : 'text-green-600'
                          }`}>
                            {(meal.nutrient_profile['SODIUM'] || meal.nutrient_profile['Sodium'] || meal.nutrient_profile['sodium']) > 800 ?
                             'High sodium' : (meal.nutrient_profile['SODIUM'] || meal.nutrient_profile['Sodium'] || meal.nutrient_profile['sodium']) > 400 ?
                             'Moderate sodium' : 'Low sodium'}
                          </div>
                        </div>
                      </div>
                    ) : null}
                    
                    {/* Show debug info for available nutrients if no standard ones found */}
                    {!meal.nutrient_profile['PROTEIN'] && 
                     !meal.nutrient_profile['Protein'] && 
                     !meal.nutrient_profile['protein'] && 
                     Object.keys(meal.nutrient_profile).length > 0 && (
                      <div className="mt-4 p-4 bg-gray-50 rounded-lg text-sm">
                        <details>
                          <summary className="cursor-pointer text-gray-600 font-semibold">Available nutrients (debug)</summary>
                          <div className="mt-3 space-y-2 max-h-32 overflow-y-auto">
                            {Object.entries(meal.nutrient_profile).slice(0, 10).map(([key, value]) => (
                              <div key={key} className="flex justify-between">
                                <span className="truncate mr-2">{key}:</span>
                                <span>{typeof value === 'number' ? value.toFixed(2) : value}</span>
                              </div>
                            ))}
                            {Object.keys(meal.nutrient_profile).length > 10 && (
                              <div className="text-gray-500">... and {Object.keys(meal.nutrient_profile).length - 10} more</div>
                            )}
                          </div>
                        </details>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-lg text-gray-400 italic text-center py-4">
                    Nutrition data not available. Try recalculating metrics.
                  </div>
                )}
                
                {/* Nutritional guidance */}
                <div className="mt-6 p-4 bg-orange-50 rounded-lg">
                  <h4 className="text-sm font-bold text-orange-700 mb-2">Nutrition Tips</h4>
                  <div className="text-xs text-orange-600 space-y-1">
                    <p>• <strong>Balanced meals</strong> include protein, carbs, healthy fats, and fiber</p>
                    <p>• <strong>Portion control:</strong> Listen to your body's hunger cues</p>
                    <p>• <strong>Variety matters:</strong> Different foods provide different nutrients</p>
                    <p>• <strong>Stay hydrated:</strong> Drink water with your meals</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Timing */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-6">Timing</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-lg font-semibold text-gray-700">Prep Time</span>
                  <span className="text-xl font-bold text-gray-900">
                    {Boolean(meal.preparation_time) && (meal.preparation_time as number) > 0 
                      ? formatTime(meal.preparation_time as number)
                      : "Not specified"
                    }
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-lg font-semibold text-gray-700">Cook Time</span>
                  <span className="text-xl font-bold text-gray-900">
                    {Boolean(meal.cooking_time) && (meal.cooking_time as number) > 0 
                      ? formatTime(meal.cooking_time as number)
                      : "Not specified"
                    }
                  </span>
                </div>
                {totalTime > 0 ? (
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg font-bold">
                    <span className="text-lg text-blue-900">Total Time</span>
                    <span className="text-2xl text-blue-900">{formatTime(totalTime)}</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-lg font-semibold text-gray-700">Total Time</span>
                    <span className="text-lg text-gray-400">Not specified</span>
                  </div>
                )}
              </div>
            </div>

            {/* Stats */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-6">Community Stats</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-lg font-semibold text-gray-700">Likes</span>
                  <span className="text-2xl font-bold text-gray-900">{meal.likes_count}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-lg font-semibold text-gray-700">Saves</span>
                  <span className="text-2xl font-bold text-gray-900">{meal.saves_count}</span>
                </div>
                {meal.average_rating && (
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-lg font-semibold text-gray-700">Rating</span>
                    <div className="flex items-center space-x-2">
                      <StarIcon className="w-5 h-5 text-yellow-500 fill-current" />
                      <span className="text-2xl font-bold text-gray-900">{meal.average_rating.toFixed(1)}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            {/* Sustainability Call-to-Action */}
            <div className="bg-gradient-to-br from-emerald-50 to-green-100 rounded-xl p-6 shadow-sm border border-emerald-200">
              <div className="flex items-center mb-6">
                <div className="p-3 bg-emerald-500 rounded-xl mr-4">
                  <GlobeAltIcon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold text-emerald-900">Your Impact Matters</h3>
              </div>
              
              <div className="space-y-4">
                <div className="bg-white/70 rounded-xl p-4">
                  <h4 className="text-lg font-bold text-emerald-700 mb-3">Growing Your Impact</h4>
                  <p className="text-sm text-emerald-600 mb-3 leading-relaxed">
                    Every sustainable meal choice creates a ripple effect for our planet&apos;s health.
                  </p>
                  <div className="text-sm text-emerald-600 space-y-2">
                    <div>• Share this recipe to inspire others</div>
                    <div>• Choose seasonal, local ingredients</div>
                    <div>• Minimize food waste with proper portions</div>
                    <div>• Support regenerative farming practices</div>
                  </div>
                </div>
                
                {meal.sustainability_score && meal.sustainability_score > 70 && (
                  <div className="bg-emerald-100 rounded-xl p-4 text-center">
                    <div className="text-sm font-bold text-emerald-700">Eco-Champion Choice</div>
                    <div className="text-sm text-emerald-600">This meal supports planetary health</div>
                  </div>
                )}
                
                {meal.sustainability_score && meal.sustainability_score <= 70 && (
                  <div className="bg-amber-100 rounded-xl p-4 text-center">
                    <div className="text-sm font-bold text-amber-700">Room to Grow</div>
                    <div className="text-sm text-amber-600">Small swaps can make a big difference</div>
                  </div>
                )}
                
                {/* Micro-actions */}
                <div className="bg-white/70 rounded-xl p-4">
                  <h4 className="text-lg font-bold text-emerald-700 mb-3">Next Steps</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <button className="bg-emerald-200 hover:bg-emerald-300 text-emerald-700 px-3 py-2 rounded-lg transition-colors font-medium">
                      💚 Save Recipe
                    </button>
                    <button className="bg-blue-200 hover:bg-blue-300 text-blue-700 px-3 py-2 rounded-lg transition-colors font-medium">
                      📱 Share Impact
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}