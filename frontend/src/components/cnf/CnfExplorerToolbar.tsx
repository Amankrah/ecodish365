'use client';

import Link from 'next/link';
import { SparklesIcon } from '@heroicons/react/24/outline';
import { AudienceToggle } from '@/components/shared/AudienceToggle';
import { useCnfExplorer } from './CnfExplorerContext';

export function CnfExplorerToolbar() {
  const { userType, setUserType, activeFoodCount } = useCnfExplorer();

  return (
    <div className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="text-sm text-gray-600 max-w-xl">
          {userType === 'individual' && (
            <span>Plain-language food profiles. Open any food to see what matters without methodology jargon.</span>
          )}
          {userType === 'researcher' && (
            <span>Lens-relevant nutrients, provenance, and scorecard handoff. Values are per 100 g unless noted.</span>
          )}
          {userType === 'policy' && (
            <span>Population-level catalogue browsing. Export comparisons or send foods to the Scorecard for multi-lens review.</span>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {activeFoodCount > 0 && (
            <Link
              href="/scorecard"
              className="inline-flex items-center text-sm font-medium text-emerald-700 hover:text-emerald-900 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-1.5"
            >
              <SparklesIcon className="w-4 h-4 mr-1.5" aria-hidden="true" />
              Scorecard ({activeFoodCount} food{activeFoodCount === 1 ? '' : 's'})
            </Link>
          )}
          <AudienceToggle userType={userType} onChange={setUserType} accent="blue" />
        </div>
      </div>
    </div>
  );
}
