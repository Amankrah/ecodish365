'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  HeartIcon, 
  BookmarkIcon, 
  ChatBubbleLeftIcon,
  ClockIcon,
  UserIcon,
  StarIcon,
  GlobeAltIcon,
  FireIcon
} from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon, BookmarkIcon as BookmarkSolidIcon } from '@heroicons/react/24/solid';
import { Meal, MealApiService } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import Image from 'next/image';

interface MealCardProps {
  meal: Meal;
  onUpdate?: (meal: Meal) => void;
}

export default function MealCard({ meal, onUpdate }: MealCardProps) {
  const { isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(false);

  const handleLike = async () => {
    if (!isAuthenticated || loading) return;
    
    setLoading(true);
    try {
      if (meal.is_liked) {
        await MealApiService.unlikeMeal(meal.id);
        const updatedMeal = {
          ...meal,
          is_liked: false,
          likes_count: Math.max(0, (meal.likes_count || 0) - 1)
        };
        onUpdate?.(updatedMeal);
      } else {
        await MealApiService.likeMeal(meal.id);
        const updatedMeal = {
          ...meal,
          is_liked: true,
          likes_count: Math.max(0, (meal.likes_count || 0) + 1)
        };
        onUpdate?.(updatedMeal);
      }
    } catch (error) {
      console.error('Failed to toggle like:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!isAuthenticated || loading) return;
    
    setLoading(true);
    try {
      if (meal.is_saved) {
        await MealApiService.unsaveMeal(meal.id);
        const updatedMeal = {
          ...meal,
          is_saved: false,
          saves_count: Math.max(0, (meal.saves_count || 0) - 1)
        };
        onUpdate?.(updatedMeal);
      } else {
        await MealApiService.saveMeal(meal.id);
        const updatedMeal = {
          ...meal,
          is_saved: true,
          saves_count: Math.max(0, (meal.saves_count || 0) + 1)
        };
        onUpdate?.(updatedMeal);
      }
    } catch (error) {
      console.error('Failed to toggle save:', error);
    } finally {
      setLoading(false);
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

  const getHealthScoreColor = (score?: number) => {
    if (!score) return 'text-gray-500';
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const totalTime = (meal.preparation_time || 0) + (meal.cooking_time || 0);

  return (
    <div className="card group hover:shadow-lg transition-all duration-200 overflow-hidden" role="article" aria-label={`Meal card for ${meal.name}`}>
      {/* Image */}
      <div className="relative overflow-hidden bg-gray-100 h-48">
        {meal.image ? (
          <Image
            src={meal.image}
            alt={meal.name}
            fill
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            className="object-cover group-hover:scale-105 transition-transform duration-200"
            unoptimized
          />
        ) : (
          <div className="flex items-center justify-center h-48 text-gray-400">
            <FireIcon className="w-12 h-12" />
          </div>
        )}
        
        {/* Overlay badges */}
        <div className="absolute top-3 left-3 right-3 flex items-start justify-between">
          <div className="flex flex-col space-y-2">
            {meal.is_featured && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                Featured
              </span>
            )}
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(meal.difficulty_level)}`}>
              {meal.difficulty_level}
            </span>
          </div>
          
          <div className="text-right">
            {typeof meal.sustainability_score === 'number' && (
              <div className="bg-white/90 backdrop-blur-sm rounded-full px-2 py-1 flex items-center space-x-1">
                <GlobeAltIcon className="w-3 h-3 text-green-600" />
                <span className="text-xs font-medium text-green-700">
                  {meal.sustainability_score.toFixed(2)}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-3">
        <div>
          <Link href={`/meals/${meal.id}`}>
            <h3 className="text-lg font-semibold text-gray-900 group-hover:text-primary-600 transition-colors line-clamp-2">
              {meal.name}
            </h3>
          </Link>
          
          <div className="flex flex-wrap items-center gap-2 mt-2 text-sm text-gray-500">
            <div className="flex items-center space-x-1">
              <UserIcon className="w-4 h-4" />
              <span className="truncate max-w-24">@{meal.creator}</span>
            </div>
            
            {totalTime > 0 && (
              <div className="flex items-center space-x-1 bg-blue-50 text-blue-700 px-2 py-1 rounded-full">
                <ClockIcon className="w-3 h-3" />
                <span className="text-xs font-medium">{formatTime(totalTime)}</span>
              </div>
            )}
            
            <div className="flex items-center space-x-1 bg-purple-50 text-purple-700 px-2 py-1 rounded-full">
              <span className="text-xs font-medium capitalize">{meal.meal_type}</span>
            </div>
          </div>
        </div>

        {/* Description */}
        {meal.description && (
          <p className="text-sm text-gray-600 line-clamp-2">
            {meal.description}
          </p>
        )}

        {/* Nutrition & Health Scores */}
        <div className="flex flex-wrap items-center gap-2 text-sm">
          {typeof meal.total_calories === 'number' && (
            <div className="bg-orange-50 text-orange-700 px-2 py-1 rounded-full">
              <span className="text-xs font-medium">{Math.round(meal.total_calories)} cal</span>
            </div>
          )}
          
          {typeof meal.health_score_average === 'number' && (
            <div className={`flex items-center space-x-1 px-2 py-1 rounded-full ${getHealthScoreColor(meal.health_score_average)} bg-opacity-10`}>
              <StarIcon className="w-3 h-3" />
              <span className="text-xs font-medium">{meal.health_score_average.toFixed(2)}</span>
            </div>
          )}
          
          <div className="bg-gray-50 text-gray-600 px-2 py-1 rounded-full">
            <span className="text-xs font-medium">{meal.servings} serving{meal.servings !== 1 ? 's' : ''}</span>
          </div>
        </div>

        {/* Tags */}
        {meal.tags && meal.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {meal.tags.slice(0, 2).map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-600"
              >
                {tag}
              </span>
            ))}
            {meal.tags.length > 2 && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-500">
                +{meal.tags.length - 2}
              </span>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-100">
          <div className="flex items-center space-x-3">
            <button
              onClick={handleLike}
              disabled={!isAuthenticated || loading}
              className="flex items-center space-x-1 text-xs text-gray-500 hover:text-red-600 transition-colors disabled:opacity-50"
              aria-label={meal.is_liked ? 'Unlike meal' : 'Like meal'}
            >
              {meal.is_liked ? (
                <HeartSolidIcon className="w-3 h-3 text-red-600" />
              ) : (
                <HeartIcon className="w-3 h-3" />
              )}
              <span>{meal.likes_count}</span>
            </button>

            <button
              onClick={handleSave}
              disabled={!isAuthenticated || loading}
              className="flex items-center space-x-1 text-xs text-gray-500 hover:text-primary-600 transition-colors disabled:opacity-50"
              aria-label={meal.is_saved ? 'Unsave meal' : 'Save meal'}
            >
              {meal.is_saved ? (
                <BookmarkSolidIcon className="w-3 h-3 text-primary-600" />
              ) : (
                <BookmarkIcon className="w-3 h-3" />
              )}
              <span>{meal.saves_count}</span>
            </button>

            <div className="flex items-center space-x-1 text-xs text-gray-500">
              <ChatBubbleLeftIcon className="w-3 h-3" />
              <span>{meal.comments_count || 0}</span>
            </div>
          </div>

          {typeof meal.average_rating === 'number' && (
            <div className="flex items-center space-x-1 text-xs text-yellow-600">
              <StarIcon className="w-3 h-3 fill-current" />
              <span>{meal.average_rating.toFixed(1)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}