'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { CNFApiService, type Food } from '@/lib/api';
import { useCnfExplorer } from '@/components/cnf/CnfExplorerContext';
import { FoodDetailDrawer } from '@/components/cnf/FoodProfileContent';
import { NutrientDiscoverPanel } from '@/components/cnf/NutrientDiscoverPanel';

export default function CNFNutrientDiscoverPage() {
  const { userType, resolveGroupName } = useCnfExplorer();
  const [selectedFood, setSelectedFood] = useState<Food | null>(null);

  return (
    <div className="min-h-screen bg-gray-50 py-6">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Discover by nutrient</h1>
          <p className="text-gray-600">
            Find foods in the catalogue by nutrient content per 100 g. Results sort highest value first.
            Open any food for lens panels, environmental preview, and Scorecard handoff.
          </p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <NutrientDiscoverPanel
            userType={userType}
            resolveGroupName={resolveGroupName}
            onQuickView={setSelectedFood}
          />
        </div>

        <p className="mt-4 text-sm text-gray-500">
          Adding foods to a comparison? Use{' '}
          <Link href="/cnf/compare" className="text-blue-700 hover:underline">Food Comparison</Link>
          {' '}and switch to Discover by nutrient in the add-food dialog.
        </p>
      </div>

      {selectedFood && (
        <FoodDetailDrawer
          food={selectedFood}
          userType={userType}
          groupLabel={resolveGroupName(selectedFood.FoodGroupID, selectedFood.FoodGroupName)}
          onClose={() => setSelectedFood(null)}
        />
      )}
    </div>
  );
}
