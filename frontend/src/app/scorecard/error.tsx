'use client';

// Per-route error boundary for /scorecard. The multi-lens orchestrator
// already handles per-lens errors gracefully (each card has its own
// retry); this boundary catches the broader cases where the page itself
// fails to render (e.g. a bad active food list, a missing localStorage
// blob, a hydration mismatch).

import { useEffect } from 'react';
import Link from 'next/link';
import {
  ExclamationTriangleIcon,
  ArrowPathIcon,
  CalendarDaysIcon,
  HomeIcon,
} from '@heroicons/react/24/outline';

export default function ScorecardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Scorecard route error:', error);
  }, [error]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <div className="bg-white rounded-2xl border border-amber-200 shadow-sm p-6 sm:p-8">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
            <ExclamationTriangleIcon className="w-5 h-5 text-amber-700" aria-hidden="true" />
          </div>
          <div className="flex-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">All scores</p>
            <h1 className="mt-1 text-lg font-semibold text-gray-900">
              The scorecard failed to render.
            </h1>
            <p className="mt-2 text-sm text-gray-700 leading-relaxed">
              The multi-lens view ran into an error before any scoring started. Your active food
              list and saved sessions are kept in your browser and are not lost. Retrying usually
              fixes a transient hydration issue.
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
                href="/recall-24h"
                className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
              >
                <CalendarDaysIcon className="w-4 h-4" aria-hidden="true" />
                Build a food diary
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
