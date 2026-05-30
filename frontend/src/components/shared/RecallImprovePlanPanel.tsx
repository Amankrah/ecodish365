'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import {
  AlertTriangle, ArrowRight, Loader2, Sparkles, Target, X,
} from 'lucide-react';
import {
  ImprovePlanApiService,
  type ImprovePlanResponse,
  type SubstitutionCompositionItem,
  type SubstitutionPurpose,
} from '@/lib/api';
import {
  buildImprovePlanRecallExport,
  recallDaySubstitutionDishName,
  type SavedRecallDay,
} from '@/lib/recallHistory';
import { fromRecallAggregated, saveActiveFoodList } from '@/lib/activeFoodList';
import { stashScorecardSwapHandoff } from '@/lib/scorecardSwapHandoff';
import type { UserType } from './AudienceToggle';

const PURPOSE_OPTIONS: Array<{ id: SubstitutionPurpose; label: string }> = [
  { id: 'general_health', label: 'Overall health' },
  { id: 'lower_sodium', label: 'Less sodium' },
  { id: 'higher_fibre', label: 'More fibre' },
  { id: 'sustainability', label: 'Lower environmental impact' },
];

const FLAG_LABELS: Record<string, string> = {
  sugary_drink: 'Sugary drink',
  refined_grain: 'Refined grain',
  red_meat: 'Red meat',
  poultry: 'Poultry',
  wafct: 'West African food',
};

function metricVal(
  sc: Record<string, { value?: number | null; unit?: string }> | undefined,
  key: string,
): string {
  const v = sc?.[key]?.value;
  if (v == null || Number.isNaN(v)) return '—';
  if (key === 'heni') return `${v >= 0 ? '+' : ''}${v.toFixed(1)} min`;
  if (key === 'hefi') return `${v.toFixed(1)}/80`;
  if (key === 'hsr') return `${v.toFixed(1)}★`;
  if (key === 'fcs') return `${v.toFixed(1)}`;
  return v.toFixed(4);
}

function routeCompositionToScorecard(
  modified: SubstitutionCompositionItem[],
  userType: UserType,
  planLabel: string,
  purpose: SubstitutionPurpose,
): void {
  const totalMass = modified.reduce((s, i) => s + i.mass_g, 0);
  const payload = {
    source: 'recall_24h' as const,
    user_type: userType,
    captured_at: new Date().toISOString(),
    target: 'scorecard' as const,
    meals_meta: [{
      occasion: 'improved_plan',
      dish_name: planLabel,
      total_mass_g: totalMass,
    }],
    aggregated_daily_ingredients: modified.map(i => ({
      food_id: i.food_id,
      food_description: i.food_description ?? '',
      food_group: i.food_group ?? '',
      mass_g: i.mass_g,
    })),
    estimated_daily_kcal: undefined as number | undefined,
  };
  try {
    sessionStorage.setItem('recall_24h_payload', JSON.stringify(payload));
  } catch { /* private mode */ }
  try {
    saveActiveFoodList(fromRecallAggregated(payload.aggregated_daily_ingredients, {
      user_type: userType,
      meals_meta: payload.meals_meta,
    }));
  } catch { /* localStorage unavailable */ }
  stashScorecardSwapHandoff(purpose);
  window.location.href = '/scorecard?from=recall24h';
}

interface Props {
  days: SavedRecallDay[];
  onClose?: () => void;
  backHref?: string;
}

export function RecallImprovePlanPanel({ days, onClose, backHref }: Props): JSX.Element {
  const [purpose, setPurpose] = useState<SubstitutionPurpose>('general_health');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [plan, setPlan] = useState<ImprovePlanResponse | null>(null);
  const [opening, setOpening] = useState(false);

  const userType = days[0]?.user_type ?? 'individual';
  const dayLabel = days.length === 1
    ? (days[0].label?.trim() || days[0].date)
    : `${days.length}-day combined plan`;

  const fetchPlan = useCallback(async (): Promise<void> => {
    if (days.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      const dishName = days.length === 1
        ? recallDaySubstitutionDishName(days[0])
        : undefined;
      const rsp = await ImprovePlanApiService.improvePlan({
        recall_export: buildImprovePlanRecallExport(days),
        purpose,
        max_suggestions: 0,
        include_population_benchmark: true,
        dish_name: dishName,
      });
      if (!rsp.success) {
        setError('Improvement plan request failed.');
        setPlan(null);
        return;
      }
      setPlan(rsp);
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { message?: string } } };
      setError(ax.response?.data?.message ?? 'Could not build improvement plan.');
      setPlan(null);
    } finally {
      setLoading(false);
    }
  }, [days, purpose]);

  useEffect(() => {
    void fetchPlan();
  }, [fetchPlan]);

  function handleOpenOnScorecard(): void {
    const baseline = plan?.baseline.composition;
    if (!baseline?.length) return;
    setOpening(true);
    routeCompositionToScorecard(baseline, userType, dayLabel, purpose);
  }

  const baselineSc = plan?.baseline.scorecard;
  const pop = plan?.baseline.population_context?.hefi;

  return (
    <section className="bg-white rounded-lg border border-violet-200 shadow-sm overflow-hidden">
      <div className="flex items-start justify-between gap-3 px-4 py-3 bg-gradient-to-r from-violet-50 to-indigo-50 border-b border-violet-100">
        <div>
          <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-violet-600" aria-hidden="true" />
            Improvement plan
          </h2>
          <p className="text-xs text-gray-600 mt-0.5">
            {days.length === 1
              ? `Based on ${days[0].date}${days[0].label ? ` (${days[0].label})` : ''}`
              : `Combined across ${days.length} saved recall days`}
            {' · '}
            {plan?.baseline.ingredient_count ?? '…'} foods
          </p>
        </div>
        {backHref ? (
          <Link
            href={backHref}
            className="text-xs text-violet-700 hover:text-violet-900 underline whitespace-nowrap"
          >
            Change days
          </Link>
        ) : onClose ? (
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-md text-gray-500 hover:bg-white/80 hover:text-gray-800"
            aria-label="Close improvement plan"
          >
            <X className="h-5 w-5" />
          </button>
        ) : null}
      </div>

      <div className="p-4 space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <label htmlFor="improve-purpose" className="text-xs font-medium text-gray-700">
            Swap goal (used on scorecard)
          </label>
          <select
            id="improve-purpose"
            value={purpose}
            onChange={e => setPurpose(e.target.value as SubstitutionPurpose)}
            disabled={loading}
            className="text-sm border border-gray-300 rounded-md px-2 py-1 bg-white"
          >
            {PURPOSE_OPTIONS.map(o => (
              <option key={o.id} value={o.id}>{o.label}</option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => void fetchPlan()}
            disabled={loading}
            className="text-xs px-2.5 py-1 rounded-md border border-gray-300 hover:bg-gray-50 disabled:opacity-50"
          >
            Refresh scores
          </button>
        </div>

        {loading && (
          <div className="flex items-center gap-2 text-sm text-gray-600 py-6 justify-center">
            <Loader2 className="h-5 w-5 animate-spin text-violet-600" aria-hidden="true" />
            Scoring your day across all six metrics…
          </div>
        )}

        {error && !loading && (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
            {error}
          </div>
        )}

        {plan && !loading && (
          <>
            {plan.summary && (
              <p className="text-sm text-gray-800 leading-relaxed">{plan.summary}</p>
            )}

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
              {(['hefi', 'heni', 'fcs', 'hsr', 'environmental', 'dietary_pattern'] as const).map(k => (
                <div key={k} className="rounded-md border border-gray-100 bg-gray-50 px-2 py-2 text-center">
                  <div className="text-[10px] uppercase tracking-wide text-gray-500">{k.replace('_', ' ')}</div>
                  <div className="text-sm font-semibold text-gray-900">{metricVal(baselineSc, k)}</div>
                </div>
              ))}
            </div>

            {pop && (
              <div className="rounded-md border border-blue-100 bg-blue-50 px-3 py-2 text-xs text-blue-900">
                <strong>Canadian context:</strong> HEFI {pop.value.toFixed(1)}/80 — {pop.band_phrase}.
                {' '}{pop.caveat}
              </div>
            )}

            {plan.priority_targets.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-gray-800 mb-2 flex items-center gap-1">
                  <Target className="h-3.5 w-3.5" aria-hidden="true" />
                  Priority swap targets
                </h3>
                <ul className="space-y-1.5">
                  {plan.priority_targets.slice(0, 5).map(t => (
                    <li
                      key={`${t.food_id}-${t.ingredient_index}`}
                      className="text-xs text-gray-700 flex flex-wrap items-center gap-x-2 gap-y-0.5"
                    >
                      <span className="font-medium truncate max-w-[16rem]">{t.food_description}</span>
                      <span className="text-gray-500">{t.mass_g}g ({t.mass_pct}%)</span>
                      {t.swap_rule_id && (
                        <span className="text-violet-700 bg-violet-100 px-1.5 py-0.5 rounded">rule match</span>
                      )}
                      {t.flags.map(f => (
                        <span key={f} className="text-amber-800 bg-amber-100 px-1.5 py-0.5 rounded">
                          {FLAG_LABELS[f] ?? f}
                        </span>
                      ))}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900 flex gap-2">
              <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
              <p>
                Swaps run on the scorecard only — this page scores your day and highlights what to
                change first. Continue below to find and apply swaps in one place.
              </p>
            </div>

            {plan.baseline.composition?.length ? (
              <button
                type="button"
                onClick={handleOpenOnScorecard}
                disabled={opening}
                className="w-full inline-flex items-center justify-center gap-2 px-4 py-3 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white text-sm font-medium rounded-md"
              >
                {opening ? (
                  <>Opening scorecard…</>
                ) : (
                  <>
                    Try swaps on scorecard
                    <ArrowRight className="h-4 w-4" aria-hidden="true" />
                  </>
                )}
              </button>
            ) : null}

            {plan.metadata.elapsed_ms != null && (
              <p className="text-[10px] text-gray-400 text-right">
                Scored in {(plan.metadata.elapsed_ms / 1000).toFixed(1)}s
              </p>
            )}
          </>
        )}
      </div>
    </section>
  );
}
