'use client';

// Root error boundary. Catches any uncaught error thrown during render in
// a child route segment. Does NOT catch errors in the root layout itself
// (those land in global-error.tsx).

import { useEffect } from 'react';
import Link from 'next/link';
import { ExclamationTriangleIcon, ArrowPathIcon, HomeIcon } from '@heroicons/react/24/outline';

export default function RootError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Surface to console so it shows up in DevTools and the Next.js
    // overlay during dev. Plug a real telemetry hook in here later.
    console.error('Unhandled route error:', error);
  }, [error]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full bg-white rounded-2xl border border-amber-200 shadow-sm p-6 sm:p-8">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
            <ExclamationTriangleIcon className="w-5 h-5 text-amber-700" aria-hidden="true" />
          </div>
          <div className="flex-1">
            <h1 className="text-lg font-semibold text-gray-900">Something went wrong on this page.</h1>
            <p className="mt-2 text-sm text-gray-700 leading-relaxed">
              The page hit an unexpected error. Your food list and any saved days in your browser are
              safe. Try the action again, or head back to the home page.
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
