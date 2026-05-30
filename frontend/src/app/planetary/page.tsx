/**
 * /planetary — EAT-Lancet 2.0 food-system planetary-boundary share view.
 *
 * Interpretive overlay on top of the existing environmental endpoint. Takes
 * whatever foods are in the cross-page active food list, calls
 * `POST /api/environmental-impact/`, then renders the per-meal share of each
 * Table-2 boundary (3 covered in v1, 6 placeholders for v2). Parallel in
 * scope to `/dietary-pattern` (no new endpoint; pure interpretation).
 *
 * Source paper: Rockström, Thilsted, Willett et al. (2025). EAT-Lancet 2.0.
 * Lancet 406:1625-1700, Table 2 p. 1640. doi:10.1016/S0140-6736(25)01201-2.
 */
'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  Loader2, Sparkles, AlertCircle, RefreshCw, Globe, CalendarClock,
  Search, Camera, Bookmark,
} from 'lucide-react';
import {
  AudienceToggle, type UserType,
} from '@/components/shared/AudienceToggle';
import { FoodListPanel } from '@/components/shared/FoodListPanel';
import { useRecall24hReceiver } from '@/components/shared/useRecall24hReceiver';
import {
  loadActiveFoodList, ACTIVE_FOOD_LIST_EVENT,
  type ActiveFoodList,
} from '@/lib/activeFoodList';
import {
  EnvironmentalImpactApiService,
  type EnvironmentalImpactResult,
} from '@/lib/api';
import { PlanetaryBoundaryCard } from '@/components/environmental-component/PlanetaryBoundaryCard';

export default function PlanetaryBoundaryPage(): JSX.Element {
  const [userType, setUserType] = useState<UserType>('individual');
  const [list, setList] = useState<ActiveFoodList | null>(null);
  const [scoring, setScoring] = useState(false);
  const [result, setResult] = useState<EnvironmentalImpactResult | null>(null);
  const [scoreError, setScoreError] = useState<string | null>(null);
  const [scoredAtHash, setScoredAtHash] = useState<string | null>(null);

  // Hydrate from localStorage on mount + subscribe to changes.
  useEffect(() => {
    setList(loadActiveFoodList());
    function handler(e: Event) {
      const ce = e as CustomEvent<ActiveFoodList | null>;
      setList(ce.detail ?? loadActiveFoodList());
    }
    window.addEventListener(ACTIVE_FOOD_LIST_EVENT, handler);
    return () => window.removeEventListener(ACTIVE_FOOD_LIST_EVENT, handler);
  }, []);

  // Recall-24h handoff: target='planetary'. We pick the audience but never
  // auto-score (matches the Scorecard convention — user clicks "Score").
  useRecall24hReceiver({
    target: 'planetary',
    onIngredients: (_ingredients, meta) => {
      if (meta.user_type) setUserType(meta.user_type);
      setList(loadActiveFoodList());
    },
  });

  const ingredients = useMemo(
    () => (list?.ingredients ?? []).map(i => ({
      food_id: i.food_id, quantity: i.mass_g,
    })),
    [list],
  );
  const nFoods = ingredients.length;

  const currentHash = useMemo(
    () => ingredients
      .map(i => `${i.food_id}:${Math.round(i.quantity)}`)
      .sort()
      .join('|') + `|${userType}`,
    [ingredients, userType],
  );
  const isStale = result !== null && currentHash !== scoredAtHash;

  const handleScore = useCallback(async () => {
    if (ingredients.length === 0) return;
    setScoreError(null);
    setScoring(true);
    try {
      const rsp = await EnvironmentalImpactApiService.analyzeMealEnvironmentalImpact({
        foods: ingredients,
        user_type: userType,
        // 'per_serving' is the raw aggregated mass-weighted impact — the
        // correct basis for a planetary-boundary share. Per-100kcal would
        // normalize away the very signal we're trying to surface.
        basis: 'per_serving',
        enable_lca_matcher: true,
      });
      setResult(rsp);
      setScoredAtHash(currentHash);
    } catch (e) {
      setScoreError(e instanceof Error ? e.message : 'Failed to compute planetary shares.');
    } finally {
      setScoring(false);
    }
  }, [ingredients, userType, currentHash]);

  const shares = result?.data?.meal_analysis?.planetary_boundary_shares;
  const explanations = result?.data?.meal_analysis?.planetary_explanations;

  return (
    <main className="min-h-screen bg-gradient-to-br from-emerald-50 via-blue-50 to-cyan-50 py-8 px-4">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <header className="bg-white rounded-2xl border p-6 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="bg-emerald-100 p-3 rounded-lg flex-shrink-0">
              <Globe className="h-7 w-7 text-emerald-700" aria-hidden="true" />
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">
                Your share of the daily planet budget
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                What share of <strong>one person&apos;s daily share</strong> of the world&apos;s
                food-system budget does this meal or day use? We compare your food against
                limits scientists have set for climate, land, and water — divided evenly
                across the world to give a per-person reference point.
              </p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t flex items-center justify-between gap-3 flex-wrap">
            <AudienceToggle userType={userType} onChange={setUserType} accent="green" staleResultHint={isStale} />
            <button
              type="button"
              onClick={handleScore}
              disabled={nFoods === 0 || scoring}
              className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-md hover:bg-emerald-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed"
            >
              {scoring
                ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                : isStale
                  ? <RefreshCw className="h-4 w-4" aria-hidden="true" />
                  : <Sparkles className="h-4 w-4" aria-hidden="true" />}
              {scoring
                ? 'Computing planetary shares…'
                : isStale
                  ? 'Re-score'
                  : nFoods === 0
                    ? 'Add foods to score'
                    : `Score (${nFoods} food${nFoods > 1 ? 's' : ''})`}
            </button>
          </div>
        </header>

        {/* Active food list */}
        <FoodListPanel
          currentTarget="planetary"
          onChange={() => setList(loadActiveFoodList())}
        />

        {/* Empty state — entry points to populate the list */}
        {nFoods === 0 && !scoring && !result && (
          <div className="bg-white border border-dashed border-emerald-300 rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Get started</h2>
            <p className="text-sm text-gray-600 mb-4">
              The planetary overlay scores any food list. Pick the entry point that fits.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <Link href="/recall-24h?then=planetary" className="flex items-start gap-2 p-3 rounded-md border border-gray-200 hover:bg-gray-50">
                <CalendarClock className="h-4 w-4 text-green-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <span className="flex-1">
                  <span className="block text-sm font-medium text-gray-900">Log a food diary day</span>
                  <span className="block text-xs text-gray-600">Build a full day, then return here.</span>
                </span>
              </Link>
              <Link href="/scan-product" className="flex items-start gap-2 p-3 rounded-md border border-gray-200 hover:bg-gray-50">
                <Camera className="h-4 w-4 text-amber-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <span className="flex-1">
                  <span className="block text-sm font-medium text-gray-900">Scan a packaged product</span>
                  <span className="block text-xs text-gray-600">Photo of the NF panel + ingredients.</span>
                </span>
              </Link>
              <Link href="/cnf/search" className="flex items-start gap-2 p-3 rounded-md border border-gray-200 hover:bg-gray-50">
                <Search className="h-4 w-4 text-blue-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <span className="flex-1">
                  <span className="block text-sm font-medium text-gray-900">Search foods</span>
                  <span className="block text-xs text-gray-600">Canadian and West African food catalogue.</span>
                </span>
              </Link>
              <Link href="/recall-history" className="flex items-start gap-2 p-3 rounded-md border border-gray-200 hover:bg-gray-50">
                <Bookmark className="h-4 w-4 text-violet-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <span className="flex-1">
                  <span className="block text-sm font-medium text-gray-900">Load a saved day</span>
                  <span className="block text-xs text-gray-600">Re-score a previously logged day.</span>
                </span>
              </Link>
            </div>
          </div>
        )}

        {/* Top-level scoring error */}
        {scoreError && (
          <div role="alert" className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-900">
            <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <span>{scoreError}</span>
          </div>
        )}

        {/* Stale banner */}
        {isStale && (
          <div role="alert" className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-md p-3 text-sm text-amber-900">
            <RefreshCw className="h-4 w-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <span>
              Your food list or audience has changed since the last score. Click <strong>Re-score</strong> to refresh.
            </span>
          </div>
        )}

        {/* Loading skeleton */}
        {scoring && (
          <div className="bg-white rounded-2xl border p-6 animate-pulse" aria-busy="true">
            <div className="h-6 w-3/4 bg-gray-200 rounded mb-3" />
            <div className="h-4 w-1/2 bg-gray-100 rounded mb-4" />
            <div className="space-y-3">
              <div className="h-20 bg-gray-100 rounded" />
              <div className="h-20 bg-gray-100 rounded" />
              <div className="h-20 bg-gray-100 rounded" />
            </div>
          </div>
        )}

        {/* Result card */}
        {!scoring && shares && (
          <PlanetaryBoundaryCard
            shares={shares}
            explanations={explanations}
          />
        )}

        {/* Cross-link reminder */}
        {!scoring && shares && (
          <div className="bg-white rounded-lg border border-gray-200 p-4 text-sm text-gray-700">
            <p>
              The planetary share is one measure. Pair it with{' '}
              <Link href="/scorecard" className="text-emerald-700 underline">all scores</Link>{' '}
              to see healthy eating, health impact, star ratings, Food Compass, environment, and eating style
              on the same list of foods. Different questions about the same eating.
            </p>
          </div>
        )}
      </div>
    </main>
  );
}
