'use client';

// Per-route error boundary for /research/nutrient-analysis. Recovers
// from a render-time crash inside the page without losing access to the
// rest of the platform. The food list is preserved in localStorage; the
// life-stage selection is local component state and will reset on retry.

import { useEffect } from 'react';
import Link from 'next/link';
import {
  ExclamationTriangleIcon,
  ArrowPathIcon,
  BeakerIcon,
  HomeIcon,
} from '@heroicons/react/24/outline';

export default function NutrientAnalysisError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Nutrient analysis route error:', error);
  }, [error]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <div className="bg-white rounded-2xl border border-amber-200 shadow-sm p-6 sm:p-8">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
            <ExclamationTriangleIcon className="w-5 h-5 text-amber-700" aria-hidden="true" />
          </div>
          <div className="flex-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Nutrient analysis</p>
            <h1 className="mt-1 text-lg font-semibold text-gray-900">
              The analyzer ran into an error.
            </h1>
            <p className="mt-2 text-base text-gray-700 leading-relaxed">
              The composition computation or the catalogue handoff failed. Your active food list
              and recall history are stored in your browser and are not lost. Try the analysis
              again; if the same error keeps happening, the backend may be temporarily
              unavailable.
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
                href="/scorecard"
                className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
              >
                <BeakerIcon className="w-4 h-4" aria-hidden="true" />
                Open all scores
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
