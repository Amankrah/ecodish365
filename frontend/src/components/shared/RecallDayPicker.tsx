/**
 * RecallDayPicker — choose a browser-local saved food diary day.
 * Used on improve-product and scorecard add flows.
 */
'use client';

import Link from 'next/link';
import { CalendarClock, Bookmark } from 'lucide-react';
import { listSavedDays, recallDayDisplayTitle, type SavedRecallDay } from '@/lib/recallHistory';

interface Props {
  onSelect: (day: SavedRecallDay) => void;
}

export function RecallDayPicker({ onSelect }: Props): JSX.Element {
  const days = listSavedDays();

  if (days.length === 0) {
    return (
      <div className="bg-white border rounded-lg p-6 text-center space-y-4">
        <Bookmark className="h-10 w-10 text-violet-600 mx-auto" aria-hidden="true" />
        <p className="text-sm text-gray-600 max-w-md mx-auto">
          No saved days yet. Log a full day in the food diary, then click{' '}
          <strong>Save to history</strong> on the review step.
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          <Link
            href="/recall-24h"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700"
          >
            <CalendarClock className="h-4 w-4" aria-hidden="true" />
            Log a food diary day
          </Link>
          <Link
            href="/recall-history"
            className="inline-flex items-center gap-1.5 px-4 py-2 border rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Food diary history
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border rounded-lg p-4 space-y-3">
      <p className="text-sm text-gray-600">
        Pick a day you saved from your food diary. We load its food list so you
        can try healthier swaps across the whole day.
      </p>
      <ul className="space-y-1 max-h-72 overflow-y-auto border rounded-md divide-y">
        {days.map(day => (
          <li key={day.id}>
            <button
              type="button"
              onClick={() => onSelect(day)}
              className="w-full text-left px-3 py-2.5 hover:bg-violet-50 flex items-start gap-3"
            >
              <Bookmark className="h-4 w-4 text-violet-600 mt-0.5 flex-shrink-0" aria-hidden="true" />
              <span className="flex-1 min-w-0">
                <span className="block text-sm font-medium text-gray-900 truncate">
                  {recallDayDisplayTitle(day)}
                </span>
                <span className="block text-xs text-gray-500 mt-0.5">
                  {day.date}
                  {day.label ? ` · ${day.label}` : ''}
                  {' · '}
                  {day.aggregated_daily_ingredients.length} foods
                  {' · '}
                  {day.estimated_daily_kcal.toFixed(0)} kcal
                  {' · '}
                  {day.occasions_count} occasions
                </span>
              </span>
            </button>
          </li>
        ))}
      </ul>
      <p className="text-xs text-gray-500">
        Need a new day?{' '}
        <Link href="/recall-24h" className="text-violet-700 underline">Log a food diary day</Link>
        {' '}or manage saved days in{' '}
        <Link href="/recall-history" className="text-violet-700 underline">food diary history</Link>.
      </p>
    </div>
  );
}
