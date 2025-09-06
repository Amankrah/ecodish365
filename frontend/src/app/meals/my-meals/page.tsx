'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Meal, MealApiService } from '@/lib/api';
import MealCard from '@/components/meals/MealCard';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

export default function MyMealsPage() {
  const [meals, setMeals] = useState<Meal[]>([]);
  const [loading, setLoading] = useState(true);
  const [ordering, setOrdering] = useState<string>('-created_at');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const resp = await MealApiService.getMyMeals({ ordering });
        setMeals(resp.results || []);
      } catch {
        setMeals([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [ordering]);

  const handleMealUpdate = (updated: Meal) => {
    setMeals(prev => prev.map(m => (m.id === updated.id ? updated : m)));
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">My Meals</h1>
                <p className="mt-1 text-sm text-gray-600">Meals you created with photos, videos, and nutrition analysis</p>
              </div>
              <Link href="/meals/create" className="px-4 py-2 bg-gradient-primary text-white rounded-md">
                Create Meal
              </Link>
            </div>
            <div className="mt-4 flex items-center justify-end">
              <label className="mr-2 text-sm text-gray-600" htmlFor="ordering">Sort by</label>
              <select
                id="ordering"
                value={ordering}
                onChange={(e) => setOrdering(e.target.value)}
                className="border border-gray-300 rounded-md text-sm px-2 py-1 bg-white"
                aria-label="Sort my meals"
              >
                <option value="-created_at">Newest</option>
                <option value="created_at">Oldest</option>
                <option value="-likes_count">Most liked</option>
                <option value="-saves_count">Most saved</option>
                <option value="-views_count">Most viewed</option>
              </select>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading your meals...</p>
            </div>
          ) : meals.length === 0 ? (
            <div className="text-center py-12">
              <h3 className="text-lg font-medium text-gray-900">You haven&apos;t created any meals yet</h3>
              <p className="mt-2 text-gray-500">
                Start by creating your first meal with photos, videos, and detailed nutrition analysis.
              </p>
              <Link href="/meals/create" className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-gradient-primary hover:opacity-90">
                Create Your First Meal
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
              {meals.map(meal => (
                <MealCard key={meal.id} meal={meal} onUpdate={handleMealUpdate} />
              ))}
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}


