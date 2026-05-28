'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowRight, Check, Loader2, Sparkles, TrendingDown, TrendingUp } from 'lucide-react';
import {
  SubstitutionApiService,
  type SubstitutionAllergen,
  type SubstitutionCompositionItem,
  type SubstitutionConstraints,
  type SubstitutionCulturalContext,
  type SubstitutionPurpose,
  type SubstitutionReformulationMode,
  type SubstitutionSourceFilter,
  type SubstitutionSuggestion,
} from '@/lib/api';
import {
  applySuggestionToComposition,
  isSuggestionApplied,
  suggestionKey,
} from '@/lib/substitutionApply';
import type { UserType } from './AudienceToggle';
import { SubstitutionScorecardDelta } from './SubstitutionScorecardDelta';

const PURPOSE_OPTIONS: Array<{ id: SubstitutionPurpose; label: string; hint: string }> = [
  { id: 'general_health', label: 'Overall health', hint: 'Balance fibre, sodium, and saturated fat' },
  { id: 'lower_sodium', label: 'Less sodium', hint: 'Helpful for blood pressure' },
  { id: 'higher_fibre', label: 'More fibre', hint: 'Digestive health and fullness' },
  { id: 'higher_protein', label: 'More protein', hint: 'Muscle and satiety' },
  { id: 'lower_sat_fat', label: 'Less saturated fat', hint: 'Heart health' },
  { id: 'diabetes_friendly', label: 'Less sugar', hint: 'Lower total sugars' },
  { id: 'sustainability', label: 'Lower environmental impact', hint: 'Rough group-level estimate' },
];

const SOURCE_LABELS: Record<SubstitutionSourceFilter, string> = {
  both: 'Canada + West Africa',
  cnf: 'Canada (CNF)',
  wafct: 'West Africa (WAFCT)',
};

const CULTURE_LABELS: Record<SubstitutionCulturalContext, string> = {
  auto: 'Detect from dish',
  west_africa: 'West African cooking',
  north_america: 'North American products',
  any: 'Any tradition',
};

const ALLERGEN_OPTIONS: Array<{ id: SubstitutionAllergen; label: string }> = [
  { id: 'milk', label: 'Milk' },
  { id: 'egg', label: 'Egg' },
  { id: 'peanut', label: 'Peanut' },
  { id: 'tree_nut', label: 'Tree nuts' },
  { id: 'wheat', label: 'Wheat' },
  { id: 'soy', label: 'Soy' },
  { id: 'fish', label: 'Fish' },
  { id: 'shellfish', label: 'Shellfish' },
  { id: 'sesame', label: 'Sesame' },
];

interface Props {
  composition: SubstitutionCompositionItem[];
  onApply: (modified: SubstitutionCompositionItem[], suggestion: SubstitutionSuggestion) => void;
  userType?: UserType;
  dishName?: string;
  autoRun?: boolean;
}

function DeltaBadge({ value, unit, invert }: { value: number; unit: string; invert?: boolean }): JSX.Element {
  const improved = invert ? value < 0 : value > 0;
  const neutral = Math.abs(value) < 0.05;
  const Icon = improved ? TrendingUp : TrendingDown;
  const color = neutral
    ? 'text-gray-600 bg-gray-100'
    : improved
      ? 'text-emerald-800 bg-emerald-100'
      : 'text-red-800 bg-red-100';
  return (
    <span className={`inline-flex items-center gap-0.5 text-xs px-1.5 py-0.5 rounded ${color}`}>
      {!neutral && <Icon className="h-3 w-3" aria-hidden="true" />}
      {value >= 0 ? '+' : ''}{value.toFixed(1)}{unit}
    </span>
  );
}

function sourceLabel(source?: string, userType?: UserType): string | null {
  if (userType === 'individual') return null;
  switch (source) {
    case 'curated_rule': return 'Research rule';
    case 'nutrient_discovery': return 'Nutrient match';
    case 'matcher_alternative': return 'Similar food';
    case 'wafct_recipe': return 'Regional recipe';
    case 'reformulation': return 'Multi-step plan';
    case 'combined': return 'Combined';
    default: return null;
  }
}

export function SubstitutionSuggestionsPanel({
  composition, onApply, userType = 'individual', dishName, autoRun = false,
}: Props): JSX.Element {
  const [purpose, setPurpose] = useState<SubstitutionPurpose>('general_health');
  const [sourceFilter, setSourceFilter] = useState<SubstitutionSourceFilter>('both');
  const [maxSwaps, setMaxSwaps] = useState<1 | 2 | 3 | 4>(3);
  const [reformulationMode, setReformulationMode] = useState<SubstitutionReformulationMode>('greedy');
  const [culturalContext, setCulturalContext] = useState<SubstitutionCulturalContext>('auto');
  const [vegetarian, setVegetarian] = useState(false);
  const [sameRole, setSameRole] = useState(false);
  const [excludeAllergens, setExcludeAllergens] = useState<SubstitutionAllergen[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<SubstitutionSuggestion[]>([]);
  const [frontierIds, setFrontierIds] = useState<Set<string>>(new Set());
  const [baselineHefi, setBaselineHefi] = useState<number | null>(null);
  const [baselineFcs, setBaselineFcs] = useState<number | null>(null);
  const [hasRun, setHasRun] = useState(false);
  const [stale, setStale] = useState(false);
  const [appliedMessage, setAppliedMessage] = useState<string | null>(null);
  const [justAppliedKeys, setJustAppliedKeys] = useState<Set<string>>(new Set());
  const refetchAfterApplyRef = useRef(false);
  const isRefreshing = loading && hasRun;
  const compositionKey = JSON.stringify(composition.map(c => [c.food_id, c.mass_g]));

  const purposeHint = PURPOSE_OPTIONS.find(o => o.id === purpose)?.hint ?? '';

  const toggleAllergen = (id: SubstitutionAllergen): void => {
    setExcludeAllergens(prev =>
      prev.includes(id) ? prev.filter(a => a !== id) : [...prev, id],
    );
  };

  const fetchSuggestions = useCallback(async (): Promise<void> => {
    if (composition.length === 0) return;
    setLoading(true);
    setError(null);
    const constraints: SubstitutionConstraints = {
      source_filter: sourceFilter,
      max_swaps: maxSwaps,
      vegetarian,
      same_functional_role: sameRole,
      exclude_allergens: excludeAllergens.length > 0 ? excludeAllergens : undefined,
      cultural_context: culturalContext === 'auto' ? undefined : culturalContext,
    };
    try {
      const rsp = await SubstitutionApiService.analyze({
        composition,
        purpose,
        max_suggestions: 6,
        include_scorecard: true,
        dish_name: dishName,
        reformulation_mode: reformulationMode,
        constraints,
      });
      setBaselineHefi(rsp.baseline.hefi.total_score);
      setBaselineFcs(rsp.baseline.fcs?.total_score ?? null);
      setSuggestions(rsp.suggestions);
      setFrontierIds(new Set((rsp.pareto_frontier ?? []).map(s => s.id ?? s.rule_id)));
      setHasRun(true);
      setStale(false);
      setAppliedMessage(null);
      setJustAppliedKeys(new Set());
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { message?: string } } };
      setError(ax.response?.data?.message || 'We could not find swaps for this meal. Try adjusting your settings.');
      setSuggestions([]);
      setFrontierIds(new Set());
    } finally {
      setLoading(false);
    }
  }, [
    composition, purpose, sourceFilter, maxSwaps, reformulationMode, culturalContext,
    vegetarian, sameRole, excludeAllergens, dishName,
  ]);

  const handleApply = useCallback((suggestion: SubstitutionSuggestion, index: number): void => {
    const key = suggestionKey(suggestion, index);
    if (isSuggestionApplied(composition, suggestion)) return;

    const merged = applySuggestionToComposition(composition, suggestion);
    const swapCount = suggestion.swaps?.length ?? 1;
    refetchAfterApplyRef.current = true;
    setJustAppliedKeys(prev => new Set(prev).add(key));
    setAppliedMessage(
      swapCount > 1
        ? `Applied ${swapCount} swaps. Refreshing suggestions for your updated meal…`
        : 'Swap applied. Refreshing suggestions for your updated meal…',
    );
    onApply(merged, suggestion);
  }, [composition, onApply]);

  useEffect(() => {
    if (refetchAfterApplyRef.current) {
      refetchAfterApplyRef.current = false;
      if (composition.length > 0) void fetchSuggestions();
      return;
    }
    if (hasRun) setStale(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [compositionKey]);

  useEffect(() => {
    if (autoRun && composition.length > 0) void fetchSuggestions();
  }, [autoRun, fetchSuggestions, composition.length]);

  if (composition.length === 0) {
    return (
      <div className="text-sm text-gray-500 text-center py-4">
        Add ingredients above to explore swaps.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-violet-600" aria-hidden="true" />
          <h3 className="text-sm font-semibold text-gray-900">Try healthier swaps</h3>
        </div>

        <p className="text-sm text-gray-600">
          Check the ingredient list first. When the amounts look right, choose what you want to
          improve and click <strong>Find swaps</strong>. You can apply swaps one at a time or pick
          a <strong>multi-step plan</strong> to change several ingredients at once.
        </p>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => void fetchSuggestions()}
            disabled={loading || composition.length === 0}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md bg-violet-600 text-white hover:bg-violet-700 disabled:opacity-50"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
            Find swaps
          </button>
          {appliedMessage && !loading && (
            <span className="text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 rounded px-2 py-1">
              {appliedMessage}
            </span>
          )}
          {stale && hasRun && !loading && !appliedMessage && !isRefreshing && (
            <span className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-2 py-1">
              You edited the ingredients. Run again to refresh suggestions.
            </span>
          )}
        </div>

        <div className="flex flex-wrap gap-3 text-sm">
          <label className="flex flex-col gap-0.5">
            <span className="text-gray-600">What do you want to improve?</span>
            <select
              value={purpose}
              onChange={e => setPurpose(e.target.value as SubstitutionPurpose)}
              className="border border-gray-300 rounded-md px-2 py-1"
              aria-label="Improvement goal"
            >
              {PURPOSE_OPTIONS.map(o => (
                <option key={o.id} value={o.id}>{o.label}</option>
              ))}
            </select>
            {purposeHint && <span className="text-xs text-gray-500">{purposeHint}</span>}
          </label>
          <label className="flex flex-col gap-0.5">
            <span className="text-gray-600">Food database</span>
            <select
              value={sourceFilter}
              onChange={e => setSourceFilter(e.target.value as SubstitutionSourceFilter)}
              className="border border-gray-300 rounded-md px-2 py-1"
              aria-label="Food database"
            >
              {(Object.keys(SOURCE_LABELS) as SubstitutionSourceFilter[]).map(k => (
                <option key={k} value={k}>{SOURCE_LABELS[k]}</option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-0.5">
            <span className="text-gray-600">Cooking tradition</span>
            <select
              value={culturalContext}
              onChange={e => setCulturalContext(e.target.value as SubstitutionCulturalContext)}
              className="border border-gray-300 rounded-md px-2 py-1"
              aria-label="Cooking tradition"
            >
              {(Object.keys(CULTURE_LABELS) as SubstitutionCulturalContext[]).map(k => (
                <option key={k} value={k}>{CULTURE_LABELS[k]}</option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-0.5">
            <span className="text-gray-600">Swaps per suggestion</span>
            <select
              value={maxSwaps}
              onChange={e => setMaxSwaps(Number(e.target.value) as 1 | 2 | 3 | 4)}
              className="border border-gray-300 rounded-md px-2 py-1"
              aria-label="Maximum swaps"
            >
              <option value={1}>One ingredient</option>
              <option value={2}>Up to two</option>
              <option value={3}>Up to three</option>
              <option value={4}>Up to four</option>
            </select>
          </label>
          <label className="flex flex-col gap-0.5">
            <span className="text-gray-600">Plan type</span>
            <select
              value={reformulationMode}
              onChange={e => setReformulationMode(e.target.value as SubstitutionReformulationMode)}
              className="border border-gray-300 rounded-md px-2 py-1"
              aria-label="Plan type"
            >
              <option value="singles">Single swaps</option>
              <option value="greedy">Multi-step plan</option>
            </select>
          </label>
        </div>

        <div className="flex flex-wrap gap-4 text-sm">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={vegetarian} onChange={e => setVegetarian(e.target.checked)} className="rounded border-gray-300" />
            <span className="text-gray-700">Vegetarian swaps only</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={sameRole} onChange={e => setSameRole(e.target.checked)} className="rounded border-gray-300" />
            <span className="text-gray-700">Keep the same role (e.g. oil stays oil)</span>
          </label>
        </div>

        <fieldset className="text-sm">
          <legend className="text-gray-600 text-xs mb-1">Avoid these allergens in replacements</legend>
          <div className="flex flex-wrap gap-2">
            {ALLERGEN_OPTIONS.map(a => (
              <label key={a.id} className="inline-flex items-center gap-1 cursor-pointer">
                <input
                  type="checkbox"
                  checked={excludeAllergens.includes(a.id)}
                  onChange={() => toggleAllergen(a.id)}
                  className="rounded border-gray-300"
                />
                <span className="text-xs text-gray-700">{a.label}</span>
              </label>
            ))}
          </div>
        </fieldset>
      </div>

      {(baselineHefi !== null || baselineFcs !== null) && (
        <p className="text-xs text-gray-500">
          Current scores:{' '}
          {baselineHefi !== null && <>HEFI {baselineHefi.toFixed(1)} out of 80</>}
          {baselineFcs !== null && <> · FCS {baselineFcs.toFixed(0)} out of 100</>}
        </p>
      )}

      {loading && (
        <div className="flex items-center justify-center py-6 text-gray-600 text-sm">
          <Loader2 className="h-5 w-5 animate-spin mr-2" aria-hidden="true" />
          Searching for swaps…
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-800">
          {error}
        </div>
      )}

      {!loading && !error && !hasRun && (
        <div className="bg-gray-50 border border-gray-200 rounded-md p-4 text-sm text-gray-600">
          Set your preferences above, then click <strong>Find swaps</strong>.
        </div>
      )}

      {!loading && !error && hasRun && suggestions.length === 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-md p-4 text-sm text-gray-600">
          Nothing matched this time. Try a different goal, relax the filters, or use the Swap button
          on a specific row to pick your own replacement.
        </div>
      )}

      {(!loading || hasRun) && suggestions.length > 0 && (
        <div className="space-y-3">
          {suggestions.map((s, i) => {
            const sid = s.id ?? s.rule_id;
            const key = suggestionKey(s, i);
            const applied = justAppliedKeys.has(key) || isSuggestionApplied(composition, s);
            const onFrontier = !applied && (s.pareto?.on_frontier ?? frontierIds.has(sid));
            const tag = sourceLabel(s.candidate_source, userType);
            return (
              <div
                key={key}
                className={`border rounded-lg p-4 ${
                  applied
                    ? 'border-emerald-300 bg-emerald-50/70'
                    : onFrontier
                      ? 'border-amber-300 bg-amber-50/50'
                      : 'border-violet-200 bg-violet-50/40'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-sm font-semibold text-gray-900">{s.label}</p>
                      {onFrontier && (
                        <span className="text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded bg-amber-200 text-amber-900">
                          Strong balance
                        </span>
                      )}
                      {tag && (
                        <span className="text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded bg-violet-200 text-violet-900">
                          {tag}
                        </span>
                      )}
                      {s.suggestion_type === 'reformulation_plan' && (
                        <span className="text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded bg-indigo-200 text-indigo-900">
                          {s.reformulation_steps ?? 2} steps
                        </span>
                      )}
                      {s.suggestion_type === 'multi_swap' && (
                        <span className="text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded bg-indigo-200 text-indigo-900">
                          {s.swaps?.length ?? 2} ingredients
                        </span>
                      )}
                      {applied && (
                        <span className="inline-flex items-center gap-0.5 text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded bg-emerald-200 text-emerald-900">
                          <Check className="h-3 w-3" aria-hidden="true" />
                          Applied
                        </span>
                      )}
                    </div>

                    {(s.swaps && s.swaps.length > 1 ? s.swaps : [s]).map((sw, j) => (
                      <p key={j} className="text-xs text-gray-600 mt-1 flex flex-wrap items-center gap-1">
                        <span className="truncate">{sw.original?.food_description ?? s.original.food_description}</span>
                        <ArrowRight className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
                        <span className="truncate font-medium text-violet-900">
                          {sw.replacement?.food_description ?? s.replacement.food_description}
                        </span>
                      </p>
                    ))}

                    <p className="text-xs text-gray-500 mt-2">{s.rationale}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleApply(s, i)}
                    disabled={applied || isRefreshing}
                    {...(applied ? { 'aria-pressed': 'true' as const } : { 'aria-pressed': 'false' as const })}
                    className={`flex-shrink-0 inline-flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-md ${
                      applied
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-300 cursor-default'
                        : 'bg-violet-600 text-white hover:bg-violet-700 disabled:opacity-50'
                    }`}
                  >
                    {applied && <Check className="h-3.5 w-3.5" aria-hidden="true" />}
                    {applied
                      ? 'Applied'
                      : s.suggestion_type === 'reformulation_plan' || s.suggestion_type === 'multi_swap'
                        ? 'Apply all'
                        : 'Apply'}
                  </button>
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  <DeltaBadge value={s.hefi.delta} unit=" HEFI" />
                  {s.fcs && <DeltaBadge value={s.fcs.delta} unit=" FCS" />}
                  {s.nutrients.sodium_mg && (
                    <DeltaBadge value={s.nutrients.sodium_mg.diff} unit=" mg Na" invert />
                  )}
                  {s.nutrients.fibre_g && (
                    <DeltaBadge value={s.nutrients.fibre_g.diff} unit=" g fibre" />
                  )}
                  {s.nutrients.sat_fat_g && (
                    <DeltaBadge value={s.nutrients.sat_fat_g.diff} unit=" g sat fat" invert />
                  )}
                </div>

                {/* FPED-1: the swap in food-group language (DASH/Mediterranean/CFG). */}
                {s.fped_deltas && s.fped_deltas.changed.length > 0 && (
                  <div className="mt-2 flex flex-wrap items-center gap-1.5">
                    <span className="text-[11px] text-gray-400">food groups:</span>
                    {s.fped_deltas.changed.map((c) => (
                      <span
                        key={c.component}
                        className="text-[11px] px-1.5 py-0.5 rounded-full bg-teal-50 text-teal-800 border border-teal-200"
                      >
                        {c.direction === 'more' ? '▲' : '▼'} {Math.abs(c.delta)} {c.unit} {c.label}
                      </span>
                    ))}
                    {s.fped_deltas.partial && (
                      <span
                        className="text-[11px] text-amber-700"
                        title="Based only on the foods we could map to a food-group profile"
                      >
                        ⚠ partial
                      </span>
                    )}
                  </div>
                )}

                {s.scorecard?.deltas && (
                  <SubstitutionScorecardDelta deltas={s.scorecard.deltas} compact />
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
