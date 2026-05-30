/**
 * /recall-history/analyze — focused analysis workspace for selected saved days.
 *
 * Separated from /recall-history so users manage days on one page and run
 * pattern scoring, improvement plans, and cohort food-group reads here.
 */
'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  ArrowLeft, BookOpen, ChevronRight, Loader2, Sparkles, Target,
} from 'lucide-react';
import {
  listSavedDays, combineDays, subscribe, resolveAnalyzeDays,
  type SavedRecallDay,
} from '@/lib/recallHistory';
import { RecallImprovePlanPanel } from '@/components/shared/RecallImprovePlanPanel';
import { FpedCohortPanel } from '@/components/shared/FpedCohortPanel';

interface RouteMultiDayPayload {
  source: 'recall_24h';
  user_type: SavedRecallDay['user_type'];
  captured_at: string;
  target: 'dietary_pattern';
  meals_meta: Array<{ occasion: string; dish_name: string; total_mass_g: number }>;
  aggregated_daily_ingredients: SavedRecallDay['aggregated_daily_ingredients'];
  estimated_daily_kcal: number;
  multi_day?: {
    n_days: number;
    first_date: string;
    last_date: string;
    label: string;
    day_ids: string[];
  };
}

export default function RecallHistoryAnalyzePage() {
  const [hydrated, setHydrated] = useState(false);
  const [allDays, setAllDays] = useState<SavedRecallDay[]>([]);

  const refresh = useCallback(() => {
    setAllDays(listSavedDays());
  }, []);

  useEffect(() => {
    refresh();
    setHydrated(true);
    return subscribe(refresh);
  }, [refresh]);

  const days = useMemo(
    () => resolveAnalyzeDays(allDays),
    [allDays],
  );

  const cohortRecalls = useMemo(
    () => days.map(d =>
      d.aggregated_daily_ingredients.map(i => ({ food_id: i.food_id, mass_g: i.mass_g }))),
    [days],
  );
  const cohortUserType = days[0]?.user_type ?? 'individual';

  function handleScorePattern() {
    if (days.length === 0) return;
    if (days.length === 1) {
      const day = days[0];
      const payload: RouteMultiDayPayload = {
        source: 'recall_24h',
        user_type: day.user_type,
        captured_at: new Date().toISOString(),
        target: 'dietary_pattern',
        meals_meta: day.meals.map(m => ({
          occasion: m.occasion,
          dish_name: m.decomposition.dish_name,
          total_mass_g: m.decomposition.total_mass_g,
        })),
        aggregated_daily_ingredients: day.aggregated_daily_ingredients,
        estimated_daily_kcal: day.estimated_daily_kcal,
      };
      try { sessionStorage.setItem('recall_24h_payload', JSON.stringify(payload)); } catch {}
      window.location.href = '/dietary-pattern?from=recall24h';
      return;
    }
    const sorted = [...days].sort((a, b) => a.date.localeCompare(b.date));
    const first = sorted[0].date;
    const last = sorted[sorted.length - 1].date;
    const combined = combineDays(days);
    const kcal = days.reduce((s, d) => s + d.estimated_daily_kcal, 0);
    const meals_meta = days.flatMap(d => d.meals.map(m => ({
      occasion: m.occasion,
      dish_name: m.decomposition.dish_name,
      total_mass_g: m.decomposition.total_mass_g,
    })));
    const payload: RouteMultiDayPayload = {
      source: 'recall_24h',
      user_type: days[0].user_type,
      captured_at: new Date().toISOString(),
      target: 'dietary_pattern',
      meals_meta,
      aggregated_daily_ingredients: combined,
      estimated_daily_kcal: kcal / days.length,
      multi_day: {
        n_days: days.length,
        first_date: first,
        last_date: last,
        label: `${days.length}-day average, ${first} to ${last}`,
        day_ids: days.map(d => d.id),
      },
    };
    try { sessionStorage.setItem('recall_24h_payload', JSON.stringify(payload)); } catch {}
    window.location.href = '/dietary-pattern?from=recall24h';
  }

  if (!hydrated) {
    return (
      <main className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg border p-6 shadow-sm flex items-center gap-3 text-sm text-gray-700">
            <Loader2 className="h-5 w-5 animate-spin text-blue-700" aria-hidden="true" />
            Loading analysis workspace&hellip;
          </div>
        </div>
      </main>
    );
  }

  if (allDays.length === 0) {
    return (
      <main className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-4xl mx-auto space-y-4">
          <Link
            href="/recall-history"
            className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Back to saved days
          </Link>
          <div className="bg-white rounded-lg border p-6 shadow-sm text-sm text-gray-700 space-y-3">
            <p className="font-medium text-gray-900">No saved days to analyze.</p>
            <p>Log a day first, then return here to score patterns or get swap suggestions.</p>
            <Link
              href="/recall-24h"
              className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md"
            >
              Log a day <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto space-y-6">

        <div className="flex items-center justify-between gap-3">
          <Link
            href="/recall-history"
            className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Saved days
          </Link>
          <Link
            href="/recall-24h"
            className="text-sm text-blue-700 hover:text-blue-900 underline"
          >
            Log another day
          </Link>
        </div>

        <header className="bg-white rounded-lg border p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="bg-violet-100 p-3 rounded-lg">
              <Target className="h-8 w-8 text-violet-800" aria-hidden="true" />
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">Analyze saved days</h1>
              <p className="text-sm text-gray-600 mt-1">
                Score dietary patterns, get ranked swap suggestions, and review food-group
                exposure across the days you selected on the history page.
              </p>
            </div>
          </div>
        </header>

        <section className="bg-white rounded-lg border p-4 shadow-sm space-y-2">
          <h2 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-gray-500" aria-hidden="true" />
            Analyzing {days.length} day{days.length === 1 ? '' : 's'}
          </h2>
          <div className="flex flex-wrap gap-1.5">
            {days.map(d => (
              <span
                key={d.id}
                className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-800 border border-gray-200"
              >
                {d.date}{d.label ? ` · ${d.label}` : ''}
              </span>
            ))}
          </div>
          {days.length !== allDays.length && (
            <p className="text-xs text-gray-500">
              Showing your selection from saved days.
              {' '}<Link href="/recall-history" className="text-blue-700 underline">Change selection</Link>
            </p>
          )}
        </section>

        <section className="bg-white rounded-lg border p-4 shadow-sm space-y-3">
          <div>
            <h2 className="text-sm font-semibold text-gray-900">Dietary pattern</h2>
            <p className="text-xs text-gray-600 mt-1">
              {days.length === 1
                ? 'Classify this day against Canadian dietary pattern prototypes.'
                : `Combine ${days.length} days (mass-weighted) and classify the average pattern.`}
            </p>
          </div>
          <button
            type="button"
            onClick={handleScorePattern}
            className="inline-flex items-center gap-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-md"
          >
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            {days.length === 1 ? 'Score this day\'s pattern' : `Score ${days.length}-day average`}
          </button>
        </section>

        <RecallImprovePlanPanel days={days} backHref="/recall-history" />

        <details className="bg-white rounded-lg border shadow-sm group">
          <summary className="cursor-pointer px-4 py-3 text-sm font-semibold text-gray-900 list-none flex items-center justify-between">
            Food groups across days
            <span className="text-xs font-normal text-gray-500 group-open:hidden">Show advanced</span>
          </summary>
          <div className="border-t px-4 pb-4">
            <FpedCohortPanel recalls={cohortRecalls} userType={cohortUserType} />
          </div>
        </details>
      </div>
    </main>
  );
}
