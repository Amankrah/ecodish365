'use client';

import Link from 'next/link';
import { ScaleIcon, PlusIcon, SparklesIcon, CubeIcon, BeakerIcon } from '@heroicons/react/24/outline';

interface CompareEmptyStateProps {
  activeFoodCount: number;
  onAddFood: () => void;
  onImportScorecard: () => void;
}

export function CompareEmptyState({
  activeFoodCount,
  onAddFood,
  onImportScorecard,
}: CompareEmptyStateProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-10 text-center">
      <ScaleIcon className="w-14 h-14 text-gray-300 mx-auto mb-3" />
      <h3 className="text-lg font-medium text-gray-900 mb-1">No foods selected</h3>
      <p className="text-gray-600 text-sm mb-6 max-w-lg mx-auto">
        Compare up to six foods from the CNF + WAFCT + FDC + CIQUAL catalogue side by side, with optional
        per-100 kcal density, %DV, and clinical ratios.
      </p>
      <div className="flex flex-col sm:flex-row gap-3 justify-center mb-6">
        <button type="button" onClick={onAddFood} className="btn-primary inline-flex items-center justify-center">
          <PlusIcon className="w-4 h-4 mr-2" />
          Add food
        </button>
        {activeFoodCount >= 2 && (
          <button
            type="button"
            onClick={onImportScorecard}
            className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-lg text-emerald-800 bg-emerald-50 border border-emerald-200 hover:bg-emerald-100"
          >
            <SparklesIcon className="w-4 h-4 mr-2" />
            Import from Scorecard ({activeFoodCount})
          </button>
        )}
      </div>
      <div className="flex flex-wrap justify-center gap-4 text-sm">
        <Link href="/cnf/search" className="inline-flex items-center gap-1.5 text-primary-700 hover:text-primary-900">
          Advanced search
        </Link>
        <Link href="/cnf/groups" className="inline-flex items-center gap-1.5 text-primary-700 hover:text-primary-900">
          <CubeIcon className="w-4 h-4" /> Food groups
        </Link>
        <Link href="/cnf/discover" className="inline-flex items-center gap-1.5 text-primary-700 hover:text-primary-900">
          <BeakerIcon className="w-4 h-4" /> Discover
        </Link>
      </div>
    </div>
  );
}
