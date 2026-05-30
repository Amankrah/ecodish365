'use client';

import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

export function CompareMixedDbBanner() {
  return (
    <div className="mb-4 flex gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
      <ExclamationTriangleIcon className="w-5 h-5 shrink-0 text-amber-600" aria-hidden="true" />
      <div>
        <p className="font-medium">Mixed CNF + WAFCT comparison</p>
        <p className="text-xs text-amber-900/90 mt-0.5">
          West African (WAFCT) and Canadian (CNF) foods use different analytical methods for some
          nutrients. Direct numeric comparison is exploratory — check provenance on each cell in
          Researcher mode and review WAFCT caveats when scoring.
        </p>
      </div>
    </div>
  );
}
