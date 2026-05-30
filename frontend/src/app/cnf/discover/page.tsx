'use client';

import React, { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { NutrientWorkbench } from '@/components/cnf/NutrientWorkbench';

function DiscoverPageContent() {
  const searchParams = useSearchParams();
  const groupParam = searchParams.get('group');
  const parsed = groupParam ? parseInt(groupParam, 10) : NaN;
  const initialFoodGroupId = Number.isFinite(parsed) ? parsed : undefined;

  return (
    <div className="min-h-screen bg-gray-50 py-6">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Discover by nutrient</h1>
          <p className="text-gray-600">
            A research workbench over the CNF + WAFCT catalogue. Combine nutrient bounds, rank by
            density per 100 kcal or by clinical ratios, threshold on % Daily Value, scope to a food
            group, and export the result set. Open any food for its scoring panels and all-scores handoff.
          </p>
          {initialFoodGroupId != null && (
            <p className="text-sm text-teal-800 mt-2">
              Scoped to food group ID {initialFoodGroupId}.{' '}
              <Link href="/cnf/groups" className="underline hover:text-teal-950">Browse groups</Link>
            </p>
          )}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <NutrientWorkbench initialFoodGroupId={initialFoodGroupId} />
        </div>

        <p className="mt-4 text-sm text-gray-500">
          Adding foods to a comparison? Use{' '}
          <Link href="/cnf/compare" className="text-blue-700 hover:underline">Food Comparison</Link>
          {' '}and switch to Discover by nutrient in the add-food dialog.
        </p>
      </div>
    </div>
  );
}

export default function CNFNutrientDiscoverPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 py-8 flex items-center justify-center text-gray-600">
        Loading discover workbench…
      </div>
    }>
      <DiscoverPageContent />
    </Suspense>
  );
}
