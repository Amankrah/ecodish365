/**
 * MetricEmptyHint — onboarding panel shown when the scorecard has no
 * foods yet. Surfaces every existing acquisition path as a CTA so the
 * user can pick whichever feels natural.
 */
'use client';

import Link from 'next/link';
import {
  Search, ChefHat, CalendarClock, Bookmark, Camera, Sparkles,
} from 'lucide-react';

interface Props {
  /** Called when the user clicks "Add a single food" → opens the inline
   *  search bar focus + maybe scrolls into view. The parent decides. */
  onFocusInlineSearch?: () => void;
  /** Called when the user clicks "Compose a homemade dish" — parent should
   *  open the RecipeDecomposerModal. */
  onOpenDecomposer?: () => void;
}

export function MetricEmptyHint({
  onFocusInlineSearch,
  onOpenDecomposer,
}: Props): JSX.Element {
  return (
    <div className="bg-white border border-dashed border-gray-300 rounded-lg p-6">
      <div className="flex items-start gap-3 mb-4">
        <Sparkles className="h-6 w-6 text-blue-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Score one food, dish, or full day</h2>
          <p className="text-sm text-gray-600 mt-1">
            Add foods to your list, then click <strong>Score all</strong> to see how today&apos;s eating
            ranks under HEFI, HENI, HSR, FCS, Environmental, and Dietary Pattern — all in one view.
          </p>
        </div>
      </div>

      <p className="text-xs font-medium text-gray-700 mb-2">Start from:</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        <button
          type="button"
          onClick={onFocusInlineSearch}
          className="flex items-start gap-2 text-left p-3 rounded-md border border-gray-200 hover:bg-gray-50"
        >
          <Search className="h-4 w-4 text-blue-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <span className="flex-1">
            <span className="block text-sm font-medium text-gray-900">Search a single food</span>
            <span className="block text-xs text-gray-600">Use the search bar below.</span>
          </span>
        </button>

        <button
          type="button"
          onClick={onOpenDecomposer}
          className="flex items-start gap-2 text-left p-3 rounded-md border border-gray-200 hover:bg-gray-50"
        >
          <ChefHat className="h-4 w-4 text-purple-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <span className="flex-1">
            <span className="block text-sm font-medium text-gray-900">Decompose a homemade dish</span>
            <span className="block text-xs text-gray-600">Describe it in plain English; AI maps it to CNF ingredients.</span>
          </span>
        </button>

        <Link
          href="/recall-24h"
          className="flex items-start gap-2 text-left p-3 rounded-md border border-gray-200 hover:bg-gray-50"
        >
          <CalendarClock className="h-4 w-4 text-green-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <span className="flex-1">
            <span className="block text-sm font-medium text-gray-900">Log a 24-h recall</span>
            <span className="block text-xs text-gray-600">Six-occasion daily eating; route back here when done.</span>
          </span>
        </Link>

        <Link
          href="/recall-history"
          className="flex items-start gap-2 text-left p-3 rounded-md border border-gray-200 hover:bg-gray-50"
        >
          <Bookmark className="h-4 w-4 text-violet-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <span className="flex-1">
            <span className="block text-sm font-medium text-gray-900">Load a saved day</span>
            <span className="block text-xs text-gray-600">Re-score a previously logged day.</span>
          </span>
        </Link>

        <Link
          href="/scan-product"
          className="flex items-start gap-2 text-left p-3 rounded-md border border-gray-200 hover:bg-gray-50"
        >
          <Camera className="h-4 w-4 text-amber-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <span className="flex-1">
            <span className="block text-sm font-medium text-gray-900">Scan a packaged product</span>
            <span className="block text-xs text-gray-600">Take a photo of the Nutrition Facts panel.</span>
          </span>
        </Link>
      </div>
    </div>
  );
}
