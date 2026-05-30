'use client';

import React from 'react';
import Link from 'next/link';
import { NutrientWorkbench } from '@/components/cnf/NutrientWorkbench';

export default function CNFNutrientDiscoverPage() {
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
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <NutrientWorkbench />
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
