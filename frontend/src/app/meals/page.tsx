'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { MagnifyingGlassIcon, PlusCircleIcon, FunnelIcon } from '@heroicons/react/24/outline';
import { MealApiService, Meal } from '@/lib/api';
import MealCard from '@/components/meals/MealCard';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

export default function MealsPage() {
  const [meals, setMeals] = useState<Meal[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    meal_type: '',
    difficulty: '',
    max_prep_time: '',
    min_health_score: '',
    is_featured: false,
    tags: [] as string[]
  });
  const [showFilters, setShowFilters] = useState(false);

  const loadMeals = useCallback(async () => {
    setLoading(true);
    try {
      type MealsQueryParams = {
        search?: string;
        ordering?: string;
        limit?: number;
        meal_type?: string;
        difficulty_level?: string;
        max_prep_time?: string;
        min_health_score?: string;
        is_featured?: boolean;
        tags?: string;
      };

      const params: MealsQueryParams = {
        search: searchQuery,
        ordering: '-created_at',
        limit: 20
      };

      // Add filters
      if (filters.meal_type) params.meal_type = filters.meal_type;
      if (filters.difficulty) params.difficulty_level = filters.difficulty;
      if (filters.max_prep_time) params.max_prep_time = filters.max_prep_time;
      if (filters.min_health_score) params.min_health_score = filters.min_health_score;
      if (filters.is_featured) params.is_featured = true;
      if (filters.tags.length > 0) params.tags = filters.tags.join(',');

      const data = await MealApiService.getMeals(params);
      const mealsWithMedia = Array.isArray(data.results) ? data.results : (Array.isArray(data) ? data : []);
      setMeals(mealsWithMedia);
    } catch (error) {
      console.error('Failed to load meals:', error);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, filters]);

  useEffect(() => {
    loadMeals();
  }, [loadMeals]);

  const handleMealUpdate = (updatedMeal: Meal) => {
    setMeals(meals.map(meal => 
      meal.id === updatedMeal.id ? updatedMeal : meal
    ));
  };

  const clearFilters = () => {
    setFilters({
      meal_type: '',
      difficulty: '',
      max_prep_time: '',
      min_health_score: '',
      is_featured: false,
      tags: []
    });
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="md:flex md:items-center md:justify-between">
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl">
                Discover Meals
              </h1>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Explore healthy, sustainable meals with photos, videos, and comprehensive nutrition analysis
              </p>
            </div>
            <div className="mt-4 flex md:mt-0 md:ml-4">
              <Link
                href="/meals/create"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-gradient-primary hover:opacity-90"
              >
                <PlusCircleIcon className="w-4 h-4 mr-2" />
                Create Meal
              </Link>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="mt-6">
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search */}
              <div className="flex-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Search meals..."
                />
              </div>

              {/* Filter Toggle */}
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md bg-white text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                <FunnelIcon className="w-4 h-4 mr-2" />
                Filters
              </button>
            </div>

            {/* Filter Panel */}
            {showFilters && (
              <div className="mt-4 p-4 bg-white rounded-lg border border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label htmlFor="filter-meal-type" className="block text-sm font-medium text-gray-700 mb-1">
                      Meal Type
                    </label>
                    <select
                      id="filter-meal-type"
                      value={filters.meal_type}
                      onChange={(e) => setFilters({...filters, meal_type: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    >
                      <option value="">All Types</option>
                      <option value="breakfast">Breakfast</option>
                      <option value="lunch">Lunch</option>
                      <option value="dinner">Dinner</option>
                      <option value="snack">Snack</option>
                      <option value="dessert">Dessert</option>
                      <option value="beverage">Beverage</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="filter-difficulty" className="block text-sm font-medium text-gray-700 mb-1">
                      Difficulty
                    </label>
                    <select
                      id="filter-difficulty"
                      value={filters.difficulty}
                      onChange={(e) => setFilters({...filters, difficulty: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    >
                      <option value="">All Levels</option>
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="filter-max-prep-time" className="block text-sm font-medium text-gray-700 mb-1">
                      Max Prep Time (min)
                    </label>
                    <select
                      id="filter-max-prep-time"
                      value={filters.max_prep_time}
                      onChange={(e) => setFilters({...filters, max_prep_time: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    >
                      <option value="">Any Time</option>
                      <option value="15">15 minutes</option>
                      <option value="30">30 minutes</option>
                      <option value="60">1 hour</option>
                      <option value="120">2 hours</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="filter-min-health-score" className="block text-sm font-medium text-gray-700 mb-1">
                      Min Health Score
                    </label>
                    <select
                      id="filter-min-health-score"
                      value={filters.min_health_score}
                      onChange={(e) => setFilters({...filters, min_health_score: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    >
                      <option value="">Any Score</option>
                      <option value="60">60+</option>
                      <option value="70">70+</option>
                      <option value="80">80+</option>
                      <option value="90">90+</option>
                    </select>
                  </div>
                </div>

                <div className="mt-4 flex items-center space-x-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.is_featured}
                      onChange={(e) => setFilters({...filters, is_featured: e.target.checked})}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Featured meals only</span>
                  </label>
                  
                  <div className="text-sm text-gray-500">
                    📸 Meals with photos and videos are highlighted with media indicators
                  </div>

                  <button
                    onClick={clearFilters}
                    className="text-sm text-primary-600 hover:text-primary-800"
                  >
                    Clear all filters
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Meals Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading meals...</p>
          </div>
        ) : meals.length === 0 ? (
          <div className="text-center py-12">
            <h3 className="text-lg font-medium text-gray-900">No meals found</h3>
            <p className="mt-2 text-gray-500">
              Try adjusting your search criteria or{' '}
              <Link href="/meals/create" className="text-primary-600 hover:text-primary-800">
                create a new meal
              </Link>
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {meals.map((meal) => (
              <MealCard
                key={meal.id}
                meal={meal}
                onUpdate={handleMealUpdate}
              />
            ))}
          </div>
        )}
      </div>

      </div>
    </ProtectedRoute>
  );
}