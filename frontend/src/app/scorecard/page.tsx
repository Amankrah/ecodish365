/**
 * /scorecard — multi-metric food profile view.
 *
 * Reads the cross-page active food list, lets the user add/edit/remove
 * foods inline, then on an explicit "Score all" click fires the six
 * existing scorer endpoints in parallel and renders a compact summary
 * card per metric.
 *
 * All editing flows through `FoodListPanel` (the shared cross-page
 * widget) + `ScorecardAddBar`. The handoff from /recall-24h, /scan-product,
 * and /recall-history all already write to the same active food list, so
 * arriving here just shows whatever was last loaded.
 */
'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Loader2, RefreshCw, Sparkles, AlertCircle, Info } from 'lucide-react';
import {
  AudienceToggle, type UserType,
} from '@/components/shared/AudienceToggle';
import { FoodListPanel } from '@/components/shared/FoodListPanel';
import { FpedPanel } from '@/components/shared/FpedPanel';
import { useRecall24hReceiver } from '@/components/shared/useRecall24hReceiver';
import {
  loadActiveFoodList, ACTIVE_FOOD_LIST_EVENT,
  type ActiveFoodList,
} from '@/lib/activeFoodList';
import {
  runAllScorers, retryOneMetric, clearScorecardCache,
  type ProfileResults, type RunOptions, type MetricKey,
} from '@/lib/foodProfileOrchestrator';
import { MetricCard } from '@/components/scorecard/MetricCard';
import { MetricSkeleton } from '@/components/scorecard/MetricSkeleton';
import { MetricEmptyHint } from '@/components/scorecard/MetricEmptyHint';
import { ScorecardAddBar } from '@/components/scorecard/ScorecardAddBar';
import {
  toHefiCard, toHeniCard, toHsrCard, toFcsCard,
  toEnvironmentalCard, toDietaryPatternCard,
} from '@/components/scorecard/metricAdapters';

const METRIC_ORDER: MetricKey[] = [
  'hefi', 'heni', 'hsr', 'fcs', 'environmental', 'dietary_pattern',
];

const METRIC_LABELS: Record<MetricKey, { emoji: string; title: string }> = {
  hefi:            { emoji: '🥗', title: 'HEFI-2019' },
  heni:            { emoji: '🧬', title: 'HENI' },
  hsr:             { emoji: '⭐', title: 'HSR' },
  fcs:             { emoji: '🧭', title: 'FCS' },
  environmental:   { emoji: '🌍', title: 'Environmental' },
  dietary_pattern: { emoji: '🎯', title: 'Dietary pattern' },
};

export default function ScorecardPage(): JSX.Element {
  const [userType, setUserType] = useState<UserType>('individual');
  const [list, setList] = useState<ActiveFoodList | null>(null);
  const [scoring, setScoring] = useState(false);
  const [results, setResults] = useState<ProfileResults | null>(null);
  const [scoreError, setScoreError] = useState<string | null>(null);
  const [scoredAtIngHash, setScoredAtIngHash] = useState<string | null>(null);
  const [scoredAtUserType, setScoredAtUserType] = useState<UserType | null>(null);
  const [retryingMetric, setRetryingMetric] = useState<MetricKey | null>(null);
  const [selectedFoodIds, setSelectedFoodIds] = useState<Set<number>>(() => new Set());
  const prevFoodIdsRef = useRef<Set<number>>(new Set());

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

  // Sync selection when the active list changes: keep user choices, auto-select new foods.
  useEffect(() => {
    const ids = list?.ingredients.map(i => i.food_id) ?? [];
    const currentIdSet = new Set(ids);
    if (ids.length === 0) {
      setSelectedFoodIds(new Set());
      prevFoodIdsRef.current = new Set();
      return;
    }
    setSelectedFoodIds(prev => {
      const next = new Set<number>();
      for (const id of ids) {
        if (!prevFoodIdsRef.current.has(id) || prev.has(id)) {
          next.add(id);
        }
      }
      return next;
    });
    prevFoodIdsRef.current = currentIdSet;
  }, [list]);

  // Pick up a recall handoff (target='scorecard'). Per spec, we do NOT
  // auto-score — receiving the list is enough; the user clicks "Score all".
  useRecall24hReceiver({
    target: 'scorecard',
    onIngredients: (ingredients, meta) => {
      if (meta.user_type) setUserType(meta.user_type);
      // The receiver already saves to active list (see useRecall24hReceiver
      // line ~107); no extra write needed. Setting list refreshes our view
      // immediately too.
      setList(loadActiveFoodList());
    },
  });

  // Derived: foods selected for the next scoring run.
  const allIngredients = useMemo(
    () => (list?.ingredients ?? []).map(i => ({
      food_id: i.food_id,
      mass_g: i.mass_g,
      food_description: i.food_description,
    })),
    [list],
  );
  const ingredients = useMemo(
    () => allIngredients.filter(i => selectedFoodIds.has(i.food_id)),
    [allIngredients, selectedFoodIds],
  );
  const nFoods = ingredients.length;
  const nTotalFoods = allIngredients.length;
  const hasPartialSelection = nTotalFoods > 0 && nFoods < nTotalFoods;

  // Cheap stale detector: if the active list (or audience) changes after a
  // scoring run, the displayed cards are stale until the user re-scores.
  const currentIngHash = useMemo(
    () => ingredients
      .map(i => `${i.food_id}:${Math.round(i.mass_g)}`)
      .sort()
      .join('|'),
    [ingredients],
  );
  const isStale =
    results !== null &&
    (currentIngHash !== scoredAtIngHash || userType !== scoredAtUserType);

  // Total mass / kcal for "small sample" advisory. The active list carries
  // estimated_daily_kcal when populated from a recall or packaged-food
  // decomposition; manual additions don't, so fall back to mass-only.
  const totalMassG = useMemo(
    () => ingredients.reduce((s, i) => s + i.mass_g, 0),
    [ingredients],
  );
  const dailyKcal = list?.estimated_daily_kcal;
  // Partial-day recall: < 1500 kcal is unlikely to be a full 24-h intake.
  // Tiny samples: < 100 g total mass.
  const isSmallSample =
    nFoods > 0 &&
    ((typeof dailyKcal === 'number' && dailyKcal > 0 && dailyKcal < 1500)
      || (totalMassG > 0 && totalMassG < 100));

  const runOptions: RunOptions = useMemo(() => ({
    userType,
    decompositionProvenance: list?.packaged_food ? 'packaged_food_inferred' : undefined,
    multiDayLabel: list?.multi_day?.label,
  }), [userType, list]);

  const handleScoreAll = useCallback(async () => {
    if (ingredients.length === 0) return;
    setScoreError(null);
    setScoring(true);
    try {
      const r = await runAllScorers(ingredients, runOptions);
      setResults(r);
      setScoredAtIngHash(currentIngHash);
      setScoredAtUserType(userType);
    } catch (e) {
      setScoreError(e instanceof Error ? e.message : 'Failed to run scorers.');
    } finally {
      setScoring(false);
    }
  }, [ingredients, runOptions, currentIngHash, userType]);

  const handleRescore = useCallback(async () => {
    // Force a fresh run by clearing the cache for this hash.
    clearScorecardCache();
    await handleScoreAll();
  }, [handleScoreAll]);

  const handleRetry = useCallback(async (metric: MetricKey) => {
    if (!results) return;
    setRetryingMetric(metric);
    try {
      const fresh = await retryOneMetric(metric, ingredients, runOptions);
      setResults(prev => prev ? { ...prev, [metric]: fresh } : prev);
    } finally {
      setRetryingMetric(null);
    }
  }, [results, ingredients, runOptions]);

  // Renderable card models, derived from outcomes + audience.
  const cardModels = useMemo(() => {
    if (!results) return null;
    return {
      hefi:            toHefiCard(results.hefi, userType),
      heni:            toHeniCard(results.heni, userType),
      hsr:             toHsrCard(results.hsr, userType, nFoods),
      fcs:             toFcsCard(results.fcs, userType),
      environmental:   toEnvironmentalCard(results.environmental, userType),
      dietary_pattern: toDietaryPatternCard(results.dietary_pattern, userType, nFoods),
    };
  }, [results, userType, nFoods]);

  return (
    <main className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <header className="bg-white rounded-lg border p-6 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="bg-blue-100 p-3 rounded-lg">
              <Sparkles className="h-7 w-7 text-blue-700" aria-hidden="true" />
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">Scorecard</h1>
              <p className="text-sm text-gray-600 mt-1">
                See how the same food, dish, or full day ranks under six different scoring lenses
                — at a glance, in plain English.
              </p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t flex items-center justify-between gap-3 flex-wrap">
            <AudienceToggle userType={userType} onChange={setUserType} accent="blue" staleResultHint={isStale} />
            <button
              type="button"
              onClick={isStale ? handleRescore : handleScoreAll}
              disabled={nFoods === 0 || scoring}
              className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-md hover:bg-emerald-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed"
            >
              {scoring
                ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                : isStale
                  ? <RefreshCw className="h-4 w-4" aria-hidden="true" />
                  : <Sparkles className="h-4 w-4" aria-hidden="true" />}
              {scoring
                ? 'Scoring all metrics…'
                : isStale
                  ? 'Re-score'
                  : nFoods === 0
                    ? nTotalFoods > 0
                      ? 'Select foods to score'
                      : 'Add foods to score'
                    : hasPartialSelection
                      ? `Score selected (${nFoods} of ${nTotalFoods})`
                      : `Score all (${nFoods} food${nFoods > 1 ? 's' : ''})`}
            </button>
          </div>
        </header>

        {/* Active food list */}
        <FoodListPanel
          currentTarget="scorecard"
          selectable
          selectedFoodIds={selectedFoodIds}
          onSelectionChange={setSelectedFoodIds}
          onChange={() => setList(loadActiveFoodList())}
        />

        {/* Add foods inline */}
        <ScorecardAddBar userType={userType} />

        {/* Empty state */}
        {nFoods === 0 && !scoring && !results && (
          <MetricEmptyHint
            onFocusInlineSearch={() => {
              const el = document.getElementById('scorecard-food-search');
              el?.focus();
              el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }}
          />
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
              Your food list, selection, or audience has changed since the last score. Click <strong>Re-score</strong> to refresh.
            </span>
          </div>
        )}

        {hasPartialSelection && !scoring && !isStale && (
          <div role="status" className="flex items-start gap-2 bg-gray-50 border border-gray-200 rounded-md p-3 text-sm text-gray-700">
            <Info className="h-4 w-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <span>
              Scoring <strong>{nFoods} of {nTotalFoods}</strong> foods. Deselected items stay in your saved list but are excluded from this run.
            </span>
          </div>
        )}

        {/* Small-sample advisory — shown when the input is clearly less
            than a full meal. Most metrics are designed for full days. */}
        {isSmallSample && !scoring && (
          <div role="status" className="flex items-start gap-2 bg-blue-50 border border-blue-200 rounded-md p-3 text-sm text-blue-900">
            <Info className="h-4 w-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <span>
              <strong>Small sample</strong> ({totalMassG.toFixed(0)} g
              {typeof dailyKcal === 'number' && dailyKcal > 0 ? `, ${dailyKcal.toFixed(0)} kcal` : ''}).
              HEFI, HENI, Environmental, and Dietary Pattern need a fuller day to be meaningful —
              treat their absolute numbers below as illustrative, not as a personal diet diagnosis.
              HSR here summarises individual products only (not a daily HSR score); FCS aggregates
              this list as one combined meal.
            </span>
          </div>
        )}

        {/* Packaged-food inferred-composition advisory */}
        {list?.packaged_food && !scoring && (
          <div role="status" className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-md p-3 text-sm text-amber-900">
            <Info className="h-4 w-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <span>
              <strong>Packaged product — inferred composition.</strong>{' '}
              One or more foods came from a label scan; per-ingredient masses were inferred from
              descending-mass-order + Nutrition Facts macros, not weighed. Metric caveats below
              reflect this uncertainty.
            </span>
          </div>
        )}

        {/* Skeletons while scoring */}
        {scoring && (
          <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {METRIC_ORDER.map(m => (
              <MetricSkeleton key={m} emoji={METRIC_LABELS[m].emoji} title={METRIC_LABELS[m].title} />
            ))}
          </section>
        )}

        {/* Scored cards */}
        {!scoring && cardModels && (
          <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {METRIC_ORDER.map(m => (
              <MetricCard
                key={m}
                card={cardModels[m]}
                stale={isStale}
                onRetry={cardModels[m].status === 'error' ? () => handleRetry(m) : undefined}
                retrying={retryingMetric === m}
              />
            ))}
          </section>
        )}

        {/* FPED-1: food-group exposure (cup/oz equivalents + reference-plate gaps).
            Deterministic + cheap, so it fetches on its own once a score has run. */}
        {!scoring && cardModels && nFoods > 0 && (
          <FpedPanel foods={ingredients} userType={userType} />
        )}
      </div>
    </main>
  );
}
