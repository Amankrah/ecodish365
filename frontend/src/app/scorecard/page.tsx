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

import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Loader2, RefreshCw, Sparkles, AlertCircle, Info, Download } from 'lucide-react';
import {
  AudienceToggle, type UserType,
} from '@/components/shared/AudienceToggle';
import { FoodListPanel } from '@/components/shared/FoodListPanel';
import { FpedPanel } from '@/components/shared/FpedPanel';
import { FpidDrilldownSection } from '@/components/shared/FpidDrilldownSection';
import { CollapsibleSection } from '@/components/shared/CollapsibleSection';
import { SubstitutionSuggestionsPanel } from '@/components/shared/SubstitutionSuggestionsPanel';
import { useRecall24hReceiver } from '@/components/shared/useRecall24hReceiver';
import {
  loadActiveFoodList, saveActiveFoodList, ACTIVE_FOOD_LIST_EVENT,
  type ActiveFoodList,
} from '@/lib/activeFoodList';
import type { ProfileScoreMeta } from '@/lib/api';
import type { SubstitutionCompositionItem, SubstitutionSuggestion } from '@/lib/api';
import { readScorecardSwapHandoff } from '@/lib/scorecardSwapHandoff';
import {
  runAllScorersProgressive, retryOneMetric, clearScorecardCache,
  type ProfileResults, type RunOptions, type MetricKey,
} from '@/lib/foodProfileOrchestrator';
import { MetricCard } from '@/components/scorecard/MetricCard';
import { MetricSkeleton } from '@/components/scorecard/MetricSkeleton';
import { MetricEmptyHint } from '@/components/scorecard/MetricEmptyHint';
import { ScorecardAddBar } from '@/components/scorecard/ScorecardAddBar';
import { ScorecardReadyStrip, ScorecardStickyBar } from '@/components/scorecard/ScorecardReadyStrip';
import { ScorecardSummaryDashboard } from '@/components/scorecard/ScorecardSummaryDashboard';
import { deriveScorecardMode, provenanceLabel } from '@/lib/scorecardProvenance';
import { saveScorecardSession, exportSessionJson, loadScorecardSession } from '@/lib/scorecardSession';
import {
  toHefiCard, toHeniCard, toHsrCard, toFcsCard,
  toEnvironmentalCard, toDietaryPatternCard,
} from '@/components/scorecard/metricAdapters';

const METRIC_ORDER: MetricKey[] = [
  'hefi', 'heni', 'hsr', 'fcs', 'environmental', 'dietary_pattern',
];

const METRIC_LABELS: Record<MetricKey, { emoji: string; title: string }> = {
  hefi:            { emoji: '🥗', title: 'Healthy eating' },
  heni:            { emoji: '🧬', title: 'Health impact' },
  hsr:             { emoji: '⭐', title: 'Product rating' },
  fcs:             { emoji: '🧭', title: 'Food Compass' },
  environmental:   { emoji: '🌍', title: 'Environment' },
  dietary_pattern: { emoji: '🎯', title: 'Eating style' },
};

function ScorecardPageInner(): JSX.Element {
  const searchParams = useSearchParams();
  const [userType, setUserType] = useState<UserType>('individual');
  const [list, setList] = useState<ActiveFoodList | null>(null);
  const [scoring, setScoring] = useState(false);
  const [results, setResults] = useState<ProfileResults | null>(null);
  const [profileMeta, setProfileMeta] = useState<ProfileScoreMeta | null>(null);
  const [partialResults, setPartialResults] = useState<Partial<ProfileResults>>({});
  const [scoreError, setScoreError] = useState<string | null>(null);
  const [scoredAtIngHash, setScoredAtIngHash] = useState<string | null>(null);
  const [scoredAtUserType, setScoredAtUserType] = useState<UserType | null>(null);
  const [retryingMetric, setRetryingMetric] = useState<MetricKey | null>(null);
  const [selectedFoodIds, setSelectedFoodIds] = useState<Set<number>>(() => new Set());
  const [swapHandoff] = useState(() => readScorecardSwapHandoff());
  const [swapsExpanded, setSwapsExpanded] = useState(false);
  const [decomposerOpen, setDecomposerOpen] = useState(false);
  const prevFoodIdsRef = useRef<Set<number>>(new Set());
  const listAnchorRef = useRef<HTMLDivElement>(null);
  const autorunDone = useRef(false);

  // Hydrate from localStorage on mount + subscribe to changes.
  useEffect(() => {
    const refresh = () => setList(loadActiveFoodList());
    refresh();
    function handler(e: Event) {
      const ce = e as CustomEvent<ActiveFoodList | null>;
      setList(ce.detail ?? loadActiveFoodList());
    }
    window.addEventListener(ACTIVE_FOOD_LIST_EVENT, handler);
    window.addEventListener('focus', refresh);
    window.addEventListener('pageshow', refresh);
    return () => {
      window.removeEventListener(ACTIVE_FOOD_LIST_EVENT, handler);
      window.removeEventListener('focus', refresh);
      window.removeEventListener('pageshow', refresh);
    };
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
      // First load with foods but nothing selected yet — select all.
      if (prev.size === 0 && prevFoodIdsRef.current.size === 0) {
        return new Set(ids);
      }
      const next = new Set<number>();
      for (const id of ids) {
        if (!prevFoodIdsRef.current.has(id) || prev.has(id)) {
          next.add(id);
        }
      }
      return next.size > 0 ? next : new Set(ids);
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
      food_group: i.food_group,
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
    setPartialResults({});
    try {
      const bundle = await runAllScorersProgressive(
        ingredients,
        runOptions,
        (partial, meta) => {
          setPartialResults(prev => ({ ...prev, ...partial }));
          if (meta) setProfileMeta(meta);
        },
        { useCache: !isStale, preferBackend: true },
      );
      setResults(bundle.results);
      setProfileMeta(bundle.meta);
      setScoredAtIngHash(currentIngHash);
      setScoredAtUserType(userType);
      if (list) {
        saveScorecardSession({
          list,
          user_type: userType,
          ingredient_hash: currentIngHash,
          results: bundle.results,
          meta: bundle.meta,
          selected_food_ids: Array.from(selectedFoodIds),
        });
      }
      if (bundle.meta?.estimated_kcal && list && !list.estimated_daily_kcal) {
        saveActiveFoodList({ ...list, estimated_daily_kcal: bundle.meta.estimated_kcal });
        setList(loadActiveFoodList());
      }
    } catch (e) {
      setScoreError(e instanceof Error ? e.message : 'Failed to run scorers.');
    } finally {
      setScoring(false);
      setPartialResults({});
    }
  }, [ingredients, runOptions, currentIngHash, userType, isStale, list, selectedFoodIds]);

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

  const compositionForSubstitution = useMemo(
    () => allIngredients.map(i => ({
      food_id: i.food_id,
      mass_g: i.mass_g,
      food_description: i.food_description,
      food_group: i.food_group,
    })),
    [allIngredients],
  );

  const dishNameForSubstitution = useMemo(() => {
    const names = list?.meals_meta?.map(m => m.dish_name).filter(Boolean);
    if (names?.length) return names.join(' / ');
    return list?.packaged_food?.product_name ?? undefined;
  }, [list]);

  const handleSubstitutionApply = useCallback((
    modified: SubstitutionCompositionItem[],
    _suggestion: SubstitutionSuggestion,
  ) => {
    const current = loadActiveFoodList();
    if (!current) return;
    saveActiveFoodList({
      ...current,
      ingredients: modified.map(m => ({
        food_id: m.food_id,
        food_description: m.food_description ?? `Food ${m.food_id}`,
        food_group: m.food_group,
        mass_g: m.mass_g,
      })),
    });
    setList(loadActiveFoodList());
    setSelectedFoodIds(new Set(modified.map(m => m.food_id)));
  }, []);

  const hasResults = results !== null && !isStale;
  const scorecardMode = deriveScorecardMode(nFoods, hasResults, swapsExpanded);
  const effectiveKcal = list?.estimated_daily_kcal ?? profileMeta?.estimated_kcal;

  const displayResults = useMemo((): ProfileResults | null => {
    if (scoring && Object.keys(partialResults).length > 0) {
      return { ...(results ?? {}), ...partialResults } as ProfileResults;
    }
    return results;
  }, [scoring, partialResults, results]);

  const cardModels = useMemo(() => {
    if (!displayResults) return null;
    const r = displayResults;
    const models: Partial<Record<MetricKey, ReturnType<typeof toHefiCard>>> = {};
    if (r.hefi) models.hefi = toHefiCard(r.hefi, userType);
    if (r.heni) models.heni = toHeniCard(r.heni, userType);
    if (r.hsr) models.hsr = toHsrCard(r.hsr, userType, nFoods);
    if (r.fcs) models.fcs = toFcsCard(r.fcs, userType);
    if (r.environmental) models.environmental = toEnvironmentalCard(r.environmental, userType);
    if (r.dietary_pattern) {
      models.dietary_pattern = toDietaryPatternCard(r.dietary_pattern, userType, nFoods);
    }
    return models as Record<MetricKey, ReturnType<typeof toHefiCard>> | null;
  }, [displayResults, userType, nFoods]);

  const handleScaleToDay = useCallback(() => {
    const kcal = effectiveKcal;
    if (!kcal || kcal <= 0 || !list) return;
    const factor = 2000 / kcal;
    saveActiveFoodList({
      ...list,
      ingredients: list.ingredients.map(i => ({
        ...i,
        mass_g: Math.round(i.mass_g * factor * 10) / 10,
      })),
      estimated_daily_kcal: 2000,
    });
    setList(loadActiveFoodList());
  }, [effectiveKcal, list]);

  const handleExportSession = useCallback(() => {
    const session = loadScorecardSession();
    if (!session) return;
    const blob = new Blob([exportSessionJson(session)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scorecard-session-${session.saved_at.slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  const scoreAction = isStale ? handleRescore : handleScoreAll;
  const scoreButtonLabel = scoring
    ? 'Scoring all metrics…'
    : isStale
      ? 'Re-score'
      : nFoods === 0
        ? nTotalFoods > 0
          ? 'Select foods to score'
          : 'Add foods to score'
        : hasPartialSelection
          ? `Score selected (${nFoods} of ${nTotalFoods})`
          : `Score all (${nFoods} food${nFoods > 1 ? 's' : ''})`;

  const stickyVisible = nFoods > 0 && (!hasResults || isStale);

  useEffect(() => {
    if (autorunDone.current) return;
    if (searchParams?.get('autorun') !== '1') return;
    if (nFoods === 0 || scoring) return;
    autorunDone.current = true;
    void handleScoreAll();
  }, [searchParams, nFoods, scoring, handleScoreAll]);

  const savedSession = useMemo(() => loadScorecardSession(), [results, list]);

  const MODE_LABELS: Record<ReturnType<typeof deriveScorecardMode>, string> = {
    build: 'Build your list',
    review: 'Review your scores',
    improve: 'Improve with swaps',
  };

  useEffect(() => {
    if (swapsExpanded) {
      try {
        window.localStorage.setItem('collapsible:scorecard_substitution', '0');
      } catch { /* private mode */ }
    }
  }, [swapsExpanded]);

  return (
    <main className={`min-h-screen bg-gray-50 py-8 px-4 ${stickyVisible ? 'pb-24' : ''}`}>
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <header className="bg-white rounded-lg border p-6 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="bg-blue-100 p-3 rounded-lg">
              <Sparkles className="h-7 w-7 text-blue-700" aria-hidden="true" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl font-bold text-gray-900">Your nutrition scores</h1>
                <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
                  {MODE_LABELS[scorecardMode]}
                </span>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                {scorecardMode === 'build' && 'Add foods, then score them on nutrition, health, and environment in one view.'}
                {scorecardMode === 'review' && 'Your profile is scored. Explore each metric below or try swaps to improve.'}
                {scorecardMode === 'improve' && 'Apply ingredient swaps, then re-score to see updated numbers.'}
              </p>
              {list && list.ingredients.length > 0 && (
                <p className="text-xs text-gray-500 mt-1">
                  List: <strong>{provenanceLabel(list)}</strong>
                  {typeof effectiveKcal === 'number' && effectiveKcal > 0 && ` · ~${effectiveKcal.toFixed(0)} kcal`}
                </p>
              )}
            </div>
          </div>
          <div className="mt-4 pt-4 border-t flex items-center justify-between gap-3 flex-wrap">
            <AudienceToggle userType={userType} onChange={setUserType} accent="blue" staleResultHint={isStale} />
            <div className="flex items-center gap-2">
              {savedSession && (
                <button
                  type="button"
                  onClick={handleExportSession}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  <Download className="h-4 w-4" aria-hidden="true" />
                  Export last session
                </button>
              )}
              <button
                type="button"
                onClick={scoreAction}
                disabled={nFoods === 0 || scoring}
                className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-md hover:bg-emerald-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed"
              >
                {scoring
                  ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  : isStale
                    ? <RefreshCw className="h-4 w-4" aria-hidden="true" />
                    : <Sparkles className="h-4 w-4" aria-hidden="true" />}
                {scoreButtonLabel}
              </button>
            </div>
          </div>
        </header>

        {/* Add foods first (build mode) */}
        <ScorecardAddBar
          userType={userType}
          decomposerOpen={decomposerOpen}
          onDecomposerOpenChange={setDecomposerOpen}
        />

        <div ref={listAnchorRef}>
          <FoodListPanel
            currentTarget="scorecard"
            variant="scorecard"
            userType={userType}
            transferMode="compact"
            selectable
            selectedFoodIds={selectedFoodIds}
            onSelectionChange={setSelectedFoodIds}
            onChange={() => setList(loadActiveFoodList())}
          />
        </div>

        <ScorecardReadyStrip
          nFoods={nFoods}
          nTotalFoods={nTotalFoods}
          totalMassG={totalMassG}
          dailyKcal={effectiveKcal}
          isSmallSample={isSmallSample}
          hasPartialSelection={hasPartialSelection}
          onScore={scoreAction}
          scoring={scoring}
        />

        {/* Empty state */}
        {nTotalFoods === 0 && !scoring && !results && (
          <MetricEmptyHint
            onFocusInlineSearch={() => {
              const el = document.getElementById('scorecard-food-search');
              el?.focus();
              el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }}
            onOpenDecomposer={() => setDecomposerOpen(true)}
          />
        )}

        {scoreError && (
          <div role="alert" className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-900">
            <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <span>{scoreError}</span>
          </div>
        )}

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

        {isSmallSample && !scoring && nFoods > 0 && (
          <div role="status" className="flex items-start gap-2 bg-blue-50 border border-blue-200 rounded-md p-3 text-sm text-blue-900">
            <Info className="h-4 w-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <span>
              <strong>Small sample</strong> ({totalMassG.toFixed(0)} g
              {typeof effectiveKcal === 'number' && effectiveKcal > 0 ? `, ${effectiveKcal.toFixed(0)} kcal` : ''}).
              Some scores work best with a full day of eating. Treat the numbers below as a preview,
              not a diagnosis. HSR rates individual products. FCS treats your list as one combined meal.
            </span>
          </div>
        )}

        {list?.packaged_food && !scoring && (
          <div role="status" className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-md p-3 text-sm text-amber-900">
            <Info className="h-4 w-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <span>
              <strong>Scanned product.</strong> Ingredient amounts were estimated from the nutrition label,
              not weighed. Scores may be less precise because of that.
            </span>
          </div>
        )}

        {hasResults && cardModels && (
          <ScorecardSummaryDashboard
            cards={cardModels}
            meta={profileMeta}
            nFoods={nFoods}
            totalMassG={totalMassG}
            dailyKcal={effectiveKcal}
            onScaleToDay={handleScaleToDay}
          />
        )}

        {(scoring || cardModels) && (
          <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {METRIC_ORDER.map(m => {
              if (scoring && !cardModels?.[m]) {
                return (
                  <MetricSkeleton
                    key={m}
                    emoji={METRIC_LABELS[m].emoji}
                    title={METRIC_LABELS[m].title}
                  />
                );
              }
              if (!cardModels?.[m]) return null;
              return (
                <MetricCard
                  key={m}
                  card={cardModels[m]}
                  stale={isStale}
                  onRetry={cardModels[m].status === 'error' ? () => handleRetry(m) : undefined}
                  retrying={retryingMetric === m}
                />
              );
            })}
          </section>
        )}

        {nTotalFoods > 0 && hasResults && (
          <CollapsibleSection
            key={swapsExpanded ? 'swaps-open' : 'swaps-closed'}
            title="Ingredient swaps"
            icon={<Sparkles className="h-4 w-4 text-violet-600" aria-hidden="true" />}
            badge={`${nTotalFoods} food${nTotalFoods > 1 ? 's' : ''}`}
            persistKey="scorecard_substitution"
            defaultCollapsed={!swapsExpanded}
          >
            <p className="text-xs text-gray-500 mb-3">
              Try healthier ingredient swaps. When you apply a swap, your food list updates above.
              Click <strong>Re-score</strong> to refresh the numbers.
            </p>
            <SubstitutionSuggestionsPanel
              composition={compositionForSubstitution}
              onApply={handleSubstitutionApply}
              userType={userType}
              dishName={dishNameForSubstitution}
              autoRun={swapHandoff.autoRun}
              initialPurpose={swapHandoff.purpose}
            />
          </CollapsibleSection>
        )}

        {hasResults && !swapsExpanded && (
          <div className="text-center">
            <button
              type="button"
              onClick={() => setSwapsExpanded(true)}
              className="text-sm text-violet-700 hover:text-violet-900 font-medium"
            >
              Try ingredient swaps to improve →
            </button>
          </div>
        )}

        {!scoring && cardModels && nFoods > 0 && (
          <FpedPanel foods={ingredients} userType={userType} estimatedKcal={effectiveKcal} />
        )}

        {!scoring && cardModels && nFoods > 0 && (
          <FpidDrilldownSection foods={ingredients} userType={userType} />
        )}
      </div>

      <ScorecardStickyBar
        visible={stickyVisible}
        label={scoreButtonLabel}
        onScore={scoreAction}
        scoring={scoring}
        isStale={isStale}
        disabled={nFoods === 0}
      />
    </main>
  );
}

export default function ScorecardPage(): JSX.Element {
  // useSearchParams requires Suspense in the Next.js App Router.
  return (
    <Suspense fallback={<div className="min-h-screen bg-gray-50" />}>
      <ScorecardPageInner />
    </Suspense>
  );
}
