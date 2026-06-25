'use client';

// Segment-wide error boundary for /cnf/*. Catches uncaught render errors
// from every catalogue route (/cnf, /cnf/search, /cnf/compare,
// /cnf/discover, /cnf/groups, /cnf/analytics, /cnf/foods/[id]) without
// bubbling up to the root error.tsx. Contextual recovery target is the
// catalogue hub instead of /.

import { useEffect } from 'react';
import Link from 'next/link';
import {
  ExclamationTriangleIcon,
  ArrowPathIcon,
  Squares2X2Icon,
  HomeIcon,
} from '@heroicons/react/24/outline';

export default function CnfError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Catalogue route error:', error);
  }, [error]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <div className="bg-white rounded-2xl border border-amber-200 shadow-sm p-6 sm:p-8">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
            <ExclamationTriangleIcon className="w-5 h-5 text-amber-700" aria-hidden="true" />
          </div>
          <div className="flex-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Food catalogue</p>
            <h1 className="mt-1 text-lg font-semibold text-gray-900">
              A catalogue page ran into an error.
            </h1>
            <p className="mt-2 text-sm text-gray-700 leading-relaxed">
              The page failed to render. The catalogue data itself is not affected — most often
              this is a transient hydration or filter-state issue that clears on retry. Your
              active food list in the browser is safe.
            </p>
            {error.digest && (
              <p className="mt-2 text-xs text-gray-500 font-mono break-all">
                Reference: {error.digest}
              </p>
            )}
            <div className="mt-5 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={reset}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-semibold rounded-lg text-white bg-accent-500 hover:bg-accent-600 shadow-sm"
              >
                <ArrowPathIcon className="w-4 h-4" aria-hidden="true" />
                Try again
              </button>
              <Link
                href="/cnf"
                className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
              >
                <Squares2X2Icon className="w-4 h-4" aria-hidden="true" />
                Open the catalogue hub
              </Link>
              <Link
                href="/"
                className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
              >
                <HomeIcon className="w-4 h-4" aria-hidden="true" />
                Home
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
