/**
 * Recall24hWizard — occasion-by-occasion 24-h dietary recall (AI-MATCH-2).
 *
 * Stepped form (not a chat UI — the codebase has no chat scaffolding and a
 * stepped form is cleaner for the deterministic occasion → ingredients →
 * aggregate → route flow):
 *
 *   Step 1: occasion picker (6 checkboxes; 3 mains on by default)
 *   Step 2: per-occasion entry — dish name + total mass; user clicks
 *           "Decompose all" which calls the new server-side /recipes/recall-24h/
 *           endpoint once with all enabled occasions. The endpoint runs the
 *           per-meal decomposer in parallel via ThreadPoolExecutor so this
 *           single call returns in ~max(per-meal latency) ≈ 8-12 s.
 *   Step 3: review aggregated daily summary (deduped CNF list, kcal,
 *           per-occasion breakdown, sanity warnings)
 *   Step 4: score routing — 5 buttons that POST the aggregated list to
 *           HEFI / HENI / HSR / FCS / Environmental.
 *
 * Audience-aware: in researcher / policy mode the per-meal audit trail +
 * per-ingredient resolution_confidence are visible; in individual mode
 * they're hidden. HEFI's Brassard 2022b single-day caveat surfaces
 * automatically on the HEFI result page regardless of mode.
 */
'use client';

import { useState, useMemo } from 'react';
import {
  CalendarClock, Coffee, Sandwich, Soup, Apple, Cookie, Pizza,
  Loader2, AlertCircle, Check, Info, Sparkles, ChevronRight, ChevronLeft,
  type LucideIcon,
} from 'lucide-react';
import {
  CNFApiService,
  type CNFRecall24hResult,
  type CNFRecall24hExplanations,
  type RecallOccasion,
  type RecallMealInput,
} from '@/lib/api';
import { SourceFilter, type SourceChoice } from './SourceFilter';
import { SourceBadge } from './SourceBadge';
import type { UserType } from './AudienceToggle';

interface Recall24hWizardProps {
  userType: UserType;
  /** When set, pre-highlights one score-routing button on step 4. */
  preselectScore?: 'hefi' | 'heni' | 'hsr' | 'fcs' | 'environmental';
}

interface OccasionMeta {
  id: RecallOccasion;
  label: string;
  icon: LucideIcon;
  defaultMass: number;
  defaultEnabled: boolean;
  placeholder: string;
}

const OCCASIONS: OccasionMeta[] = [
  { id: 'breakfast',     label: 'Breakfast',     icon: Coffee,    defaultMass: 250, defaultEnabled: true,  placeholder: 'e.g. scrambled eggs with toast' },
  { id: 'am_snack',      label: 'Morning snack', icon: Apple,     defaultMass:  80, defaultEnabled: false, placeholder: 'e.g. apple, almonds, yogurt' },
  { id: 'lunch',         label: 'Lunch',         icon: Sandwich,  defaultMass: 300, defaultEnabled: true,  placeholder: 'e.g. chicken caesar salad' },
  { id: 'pm_snack',      label: 'Afternoon snack', icon: Cookie,  defaultMass:  50, defaultEnabled: false, placeholder: 'e.g. cookie, granola bar' },
  { id: 'dinner',        label: 'Dinner',        icon: Soup,      defaultMass: 350, defaultEnabled: true,  placeholder: 'e.g. spaghetti bolognese' },
  { id: 'evening_snack', label: 'Evening snack', icon: Pizza,     defaultMass: 100, defaultEnabled: false, placeholder: 'e.g. ice cream, fruit' },
];

const SCORE_BUTTONS: Array<{
  id: 'hefi' | 'heni' | 'hsr' | 'fcs' | 'environmental';
  emoji: string;
  label: string;
  path: string;
  note?: string;
}> = [
  { id: 'hefi',          emoji: '🥗', label: 'Score HEFI-2019',     path: '/hefi/calculate',          note: 'Natural fit (Brassard 2022b)' },
  { id: 'heni',          emoji: '🧬', label: 'Score HENI',          path: '/heni/calculate',          note: 'Sums healthy-life-minutes across the day' },
  { id: 'hsr',           emoji: '⭐', label: 'Score HSR',            path: '/hsr/calculate',           note: 'Informational only — HSR is per-product' },
  { id: 'fcs',           emoji: '🧭', label: 'Score FCS',            path: '/fcs/calculate',           note: 'i.FCS energy-weighted diet score' },
  { id: 'environmental', emoji: '🌍', label: 'Score Environmental',  path: '/environmental/calculate', note: 'Per-day environmental footprint' },
];

interface MealRow {
  enabled: boolean;
  dishName: string;
  totalMass: number;
}

interface ApiError { status: number; message: string }

function humanWarning(code: string): string {
  // Translate backend warning codes into plain English.
  if (code.startsWith('no_breakfast')) return 'No breakfast logged.';
  if (code.startsWith('no_lunch'))     return 'No lunch logged.';
  if (code.startsWith('no_dinner'))    return 'No dinner logged.';
  if (code.startsWith('daily_kcal_below_')) return 'Daily calories look low — did you forget a meal?';
  if (code.startsWith('daily_kcal_above_')) return 'Daily calories look high — possible double-counting.';
  if (code === 'single_occasion_day_aggregation_unreliable') return 'Only one meal logged — daily aggregation is unreliable.';
  if (code.includes('_resolved_only_partially')) return code.split('_')[0] + ' meal(s) resolved only partially.';
  if (code.includes('_failed_to_decompose'))     return code.split('_')[0] + ' meal(s) failed to decompose.';
  return code;
}

export function Recall24hWizard({ userType, preselectScore }: Recall24hWizardProps) {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [rows, setRows] = useState<Record<RecallOccasion, MealRow>>(() => {
    const out = {} as Record<RecallOccasion, MealRow>;
    for (const o of OCCASIONS) {
      out[o.id] = {
        enabled: o.defaultEnabled,
        dishName: '',
        totalMass: o.defaultMass,
      };
    }
    return out;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<ApiError | null>(null);
  const [result, setResult]   = useState<CNFRecall24hResult | null>(null);
  const [explanations, setExplanations] = useState<CNFRecall24hExplanations | null>(null);
  // WAFCT-EXTEND (2026-05-24): food-database scope. Forwarded into every
  // meal's Stage-2 ingredient resolution so a 'wafct' recall stays
  // entirely within WAFCT FoodIDs.
  const [source, setSource]   = useState<SourceChoice>('both');

  const enabledOccasions = useMemo(
    () => OCCASIONS.filter(o => rows[o.id].enabled),
    [rows],
  );
  const canRunRecall = useMemo(
    () => enabledOccasions.length > 0
       && enabledOccasions.every(o => rows[o.id].dishName.trim() && rows[o.id].totalMass > 0),
    [enabledOccasions, rows],
  );

  function toggle(id: RecallOccasion) {
    setRows(prev => ({ ...prev, [id]: { ...prev[id], enabled: !prev[id].enabled } }));
  }
  function updateRow(id: RecallOccasion, patch: Partial<MealRow>) {
    setRows(prev => ({ ...prev, [id]: { ...prev[id], ...patch } }));
  }

  async function handleDecomposeAll() {
    setLoading(true);
    setError(null);
    setResult(null);
    setExplanations(null);
    const meals: RecallMealInput[] = enabledOccasions.map(o => ({
      occasion:    o.id,
      dish_name:   rows[o.id].dishName.trim(),
      total_mass_g: rows[o.id].totalMass,
    }));
    try {
      const r = await CNFApiService.recall24h(meals, { userType, source });
      setResult(r.result);
      setExplanations(r.explanations);
      setStep(3);
    } catch (e: unknown) {
      const ax = e as { response?: { status?: number; data?: { message?: string; error?: string } } };
      setError({
        status: ax?.response?.status ?? 500,
        message: ax?.response?.data?.message
          || ax?.response?.data?.error
          || 'Recall decomposition failed. Try fewer meals or use single-dish scoring.',
      });
    } finally {
      setLoading(false);
    }
  }

  function handleRoute(target: typeof SCORE_BUTTONS[number]) {
    if (!result) return;
    // Stash the aggregated list in sessionStorage and navigate. The target
    // page reads `recall_24h_payload` on mount and pre-populates its picker.
    try {
      const payload = {
        source: 'recall_24h',
        user_type: userType,
        captured_at: new Date().toISOString(),
        target: target.id,
        meals_meta: enabledOccasions.map(o => ({
          occasion: o.id,
          dish_name: rows[o.id].dishName,
          total_mass_g: rows[o.id].totalMass,
        })),
        aggregated_daily_ingredients: result.aggregated_daily_ingredients,
        estimated_daily_kcal: result.estimated_daily_kcal,
      };
      sessionStorage.setItem('recall_24h_payload', JSON.stringify(payload));
    } catch {
      // sessionStorage may fail in private mode; harmless — the score
      // pages still work standalone.
    }
    window.location.href = target.path + '?from=recall24h';
  }

  // --- render ------------------------------------------------------------

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Stepper */}
      <ol className="flex items-center justify-between border-b pb-3 text-sm">
        {[
          { n: 1, label: 'Occasions' },
          { n: 2, label: 'Decompose meals' },
          { n: 3, label: 'Review day' },
          { n: 4, label: 'Score' },
        ].map(s => (
          <li key={s.n} className={`flex items-center gap-1.5 ${step === s.n ? 'text-blue-700 font-semibold' : 'text-gray-500'}`}>
            <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs ${step >= s.n ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'}`}>
              {step > s.n ? <Check className="h-3 w-3" aria-hidden="true" /> : s.n}
            </span>
            {s.label}
          </li>
        ))}
      </ol>

      {/* STEP 1 — occasion picker */}
      {step === 1 && (
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <CalendarClock className="h-5 w-5 text-blue-700" aria-hidden="true" />
            <h2 className="text-lg font-semibold text-gray-900">Which occasions did you eat?</h2>
          </div>
          <p className="text-sm text-gray-600">
            Toggle the meals + snacks you had over a full 24-hour day. You can leave snacks off if you skip them — the recall handles any combination.
          </p>
          {/* WAFCT-EXTEND (2026-05-24): pick the food database upfront. The
              backend forwards this into every meal's Stage-2 ingredient
              resolution, so a 'wafct' recall stays entirely WAFCT. */}
          <div className="flex items-center gap-3 p-3 rounded-md bg-blue-50 border border-blue-100">
            <span className="text-xs text-gray-700">Food database:</span>
            <SourceFilter source={source} onChange={setSource} accent="blue" />
            <span className="text-xs text-gray-500 ml-auto">
              {source === 'wafct'
                ? 'WAFCT only — best for West African meals'
                : source === 'cnf'
                ? 'CNF only — Health Canada'
                : 'Searching both databases'}
            </span>
          </div>
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {OCCASIONS.map(o => {
              const Icon = o.icon;
              const isOn = rows[o.id].enabled;
              return (
                <li key={o.id}>
                  <label className={`flex items-center gap-3 p-3 rounded-md border cursor-pointer transition-colors ${
                    isOn ? 'border-blue-400 bg-blue-50' : 'border-gray-200 hover:bg-gray-50'
                  }`}>
                    <input
                      type="checkbox"
                      checked={isOn}
                      onChange={() => toggle(o.id)}
                      className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                    />
                    <Icon className="h-5 w-5 text-gray-600" aria-hidden={true} />
                    <span className="text-sm font-medium text-gray-900">{o.label}</span>
                  </label>
                </li>
              );
            })}
          </ul>
          <div className="flex items-center justify-between pt-3 border-t">
            <span className="text-xs text-gray-500">
              {enabledOccasions.length} occasion{enabledOccasions.length === 1 ? '' : 's'} enabled
            </span>
            <button
              type="button"
              onClick={() => setStep(2)}
              disabled={enabledOccasions.length === 0}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next: enter meals
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </section>
      )}

      {/* STEP 2 — per-occasion entry */}
      {step === 2 && (
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Sandwich className="h-5 w-5 text-blue-700" aria-hidden="true" />
            <h2 className="text-lg font-semibold text-gray-900">What did you have at each occasion?</h2>
          </div>
          <p className="text-sm text-gray-600">
            Free-text descriptions are fine — the AI handles brand names, language variation, and casual phrasing. Mass estimates can be rough; the per-meal validator flags anything that drifts more than ~4&nbsp;%.
          </p>
          <ul className="space-y-3">
            {enabledOccasions.map(o => {
              const Icon = o.icon;
              return (
                <li key={o.id} className="border rounded-lg p-4 bg-white">
                  <div className="flex items-center gap-2 mb-3">
                    <Icon className="h-4 w-4 text-gray-600" aria-hidden={true} />
                    <span className="text-sm font-semibold text-gray-900">{o.label}</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-[1fr,140px] gap-3">
                    <div>
                      <label htmlFor={`recall-dish-${o.id}`} className="block text-xs font-medium text-gray-700 mb-1">
                        Dish name
                      </label>
                      <input
                        id={`recall-dish-${o.id}`}
                        type="text"
                        value={rows[o.id].dishName}
                        onChange={e => updateRow(o.id, { dishName: e.target.value })}
                        placeholder={o.placeholder}
                        title={`${o.label} dish name`}
                        aria-label={`${o.label} dish name`}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label htmlFor={`recall-mass-${o.id}`} className="block text-xs font-medium text-gray-700 mb-1">
                        Mass (g)
                      </label>
                      <input
                        id={`recall-mass-${o.id}`}
                        type="number"
                        min={1}
                        max={5000}
                        step={10}
                        value={rows[o.id].totalMass}
                        onChange={e => updateRow(o.id, { totalMass: parseFloat(e.target.value) || 0 })}
                        title={`${o.label} total mass in grams`}
                        aria-label={`${o.label} total mass in grams`}
                        placeholder="e.g. 200"
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>

          {error && (
            <div role="alert" className="flex items-start gap-2 p-3 rounded-md bg-red-50 border-l-4 border-red-400 text-sm">
              <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
              <div>
                <div className="font-semibold text-red-900">
                  {error.status === 429 ? 'AI rate-limited'
                    : error.status === 503 ? 'AI temporarily unavailable'
                    : 'Recall failed'}
                </div>
                <div className="text-red-800 mt-0.5">{error.message}</div>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between pt-3 border-t">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm text-gray-700 hover:text-gray-900"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
              Back
            </button>
            <button
              type="button"
              onClick={handleDecomposeAll}
              disabled={loading || !canRunRecall}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading
                ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                : <Sparkles className="h-4 w-4" aria-hidden="true" />}
              {loading ? `Decomposing ${enabledOccasions.length} meal${enabledOccasions.length === 1 ? '' : 's'}… (8-15 s)` : 'Decompose all meals'}
            </button>
          </div>
        </section>
      )}

      {/* STEP 3 — review aggregated day */}
      {step === 3 && result && (
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <CalendarClock className="h-5 w-5 text-blue-700" aria-hidden="true" />
            <h2 className="text-lg font-semibold text-gray-900">Review your day</h2>
          </div>

          {/* Audience-aware top caveat */}
          {explanations && (explanations.before_you_score || explanations.mandatory_caveat) && (
            <div className="p-3 rounded-md bg-amber-50 border-l-4 border-amber-400 text-sm text-amber-900">
              <div className="font-semibold mb-1 flex items-center gap-1">
                <Info className="h-4 w-4" aria-hidden="true" />
                {(explanations.before_you_score?.title || explanations.mandatory_caveat?.title) ?? 'Note'}
              </div>
              <div>{(explanations.before_you_score?.message || explanations.mandatory_caveat?.message) ?? ''}</div>
            </div>
          )}

          {/* Aggregate totals */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm">
            <div className="p-3 rounded bg-blue-50 border border-blue-200">
              <div className="text-xs text-gray-600">Occasions</div>
              <div className="text-lg font-semibold text-gray-900">{result.occasions_count}</div>
            </div>
            <div className="p-3 rounded bg-blue-50 border border-blue-200">
              <div className="text-xs text-gray-600">Resolved mass</div>
              <div className="text-lg font-semibold text-gray-900">{result.total_resolved_mass_g.toFixed(0)} g</div>
            </div>
            <div className="p-3 rounded bg-blue-50 border border-blue-200">
              <div className="text-xs text-gray-600">Estimated kcal</div>
              <div className="text-lg font-semibold text-gray-900">{result.estimated_daily_kcal.toFixed(0)}</div>
            </div>
            <div className="p-3 rounded bg-blue-50 border border-blue-200">
              <div className="text-xs text-gray-600">CNF foods</div>
              <div className="text-lg font-semibold text-gray-900">{result.aggregated_daily_ingredients.length}</div>
            </div>
          </div>

          {/* Sanity warnings */}
          {result.aggregate_warnings.length > 0 && (
            <ul className="space-y-1.5 text-xs">
              {result.aggregate_warnings.map((w, i) => (
                <li key={i} className="flex items-start gap-1.5 text-amber-900 bg-amber-50 border-l-2 border-amber-400 px-2 py-1 rounded">
                  <AlertCircle className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" aria-hidden="true" />
                  <span>{humanWarning(w)}</span>
                </li>
              ))}
            </ul>
          )}

          {/* Per-meal breakdown */}
          <details className="border rounded-lg" open>
            <summary className="cursor-pointer px-3 py-2 text-sm font-medium text-gray-900 hover:bg-gray-50">
              Per-meal breakdown
            </summary>
            <ul className="divide-y">
              {result.meals.map(m => {
                const occ = OCCASIONS.find(x => x.id === m.occasion);
                const Icon = occ?.icon ?? Sandwich;
                return (
                  <li key={m.occasion} className="px-3 py-2 text-sm">
                    <div className="flex items-center gap-2 mb-0.5">
                      <Icon className="h-4 w-4 text-gray-500" aria-hidden={true} />
                      <span className="font-medium text-gray-900">{occ?.label ?? m.occasion}</span>
                      <span className="text-xs text-gray-500">— {m.decomposition.dish_name}</span>
                      {m.decomposition.matched
                        ? <Check className="h-3.5 w-3.5 text-green-600 ml-auto" aria-hidden="true" />
                        : <AlertCircle className="h-3.5 w-3.5 text-amber-600 ml-auto" aria-hidden="true" />}
                    </div>
                    <div className="text-xs text-gray-500 pl-6">
                      {m.decomposition.ingredients.length} ingredients · resolved {m.decomposition.resolved_mass_g.toFixed(0)} g
                      {m.decomposition.unresolved_mass_g > 0 && (
                        <> · unresolved {m.decomposition.unresolved_mass_g.toFixed(0)} g</>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          </details>

          {/* Aggregated CNF list — researcher / policy only */}
          {userType !== 'individual' && (
            <details className="border rounded-lg">
              <summary className="cursor-pointer px-3 py-2 text-sm font-medium text-gray-900 hover:bg-gray-50">
                Aggregated daily CNF list ({result.aggregated_daily_ingredients.length} foods)
              </summary>
              <ul className="divide-y text-xs">
                {result.aggregated_daily_ingredients.map(i => (
                  <li key={i.food_id} className="px-3 py-1.5 flex items-center gap-2">
                    <span className="flex-1 truncate flex items-center gap-1.5">
                      <span className="font-medium text-gray-900 truncate">{i.food_description}</span>
                      {/* WAFCT-EXTEND (2026-05-24): per-row provenance */}
                      <SourceBadge foodId={i.food_id} userType={userType} />
                      <span className="text-gray-500 truncate"> · FoodID {i.food_id} · {i.food_group}</span>
                    </span>
                    <span className="text-gray-700 tabular-nums">{i.mass_g.toFixed(0)} g</span>
                  </li>
                ))}
              </ul>
            </details>
          )}

          <div className="flex items-center justify-between pt-3 border-t">
            <button
              type="button"
              onClick={() => setStep(2)}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm text-gray-700 hover:text-gray-900"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
              Edit meals
            </button>
            <button
              type="button"
              onClick={() => setStep(4)}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md"
            >
              Next: choose a score
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </section>
      )}

      {/* STEP 4 — score routing */}
      {step === 4 && result && (
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-blue-700" aria-hidden="true" />
            <h2 className="text-lg font-semibold text-gray-900">Score your day</h2>
          </div>
          <p className="text-sm text-gray-600">
            Route your aggregated 24-h ingredient list to any of the five nutrition / sustainability indices. Each opens its calculator pre-populated with this day's CNF foods.
          </p>

          {explanations?.score_routing && (
            <details className="text-xs text-gray-600 bg-gray-50 rounded p-3">
              <summary className="cursor-pointer font-medium text-gray-700">Score-routing guidance</summary>
              <ul className="mt-2 space-y-1 pl-4 list-disc">
                {Object.entries(explanations.score_routing.message).map(([k, v]) => (
                  <li key={k}><strong>{k.toUpperCase()}:</strong> {v}</li>
                ))}
              </ul>
            </details>
          )}

          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {SCORE_BUTTONS.map(b => {
              const isHSR = b.id === 'hsr';
              const isPre = b.id === preselectScore;
              return (
                <li key={b.id}>
                  <button
                    type="button"
                    onClick={() => handleRoute(b)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      isPre
                        ? 'border-blue-500 bg-blue-50 hover:bg-blue-100'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-2xl" aria-hidden="true">{b.emoji}</span>
                      <span className="font-medium text-gray-900">{b.label}</span>
                      {isPre && (
                        <span className="ml-auto text-[10px] uppercase font-semibold text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded">recommended</span>
                      )}
                    </div>
                    {b.note && <div className="text-xs text-gray-500 mt-1">{b.note}</div>}
                    {isHSR && (
                      <div className="text-[11px] text-amber-700 mt-1 flex items-start gap-1">
                        <AlertCircle className="h-3 w-3 mt-0.5 flex-shrink-0" aria-hidden="true" />
                        HSRAC v9 is a per-product within-category rating. Daily HSR is informational only.
                      </div>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>

          <div className="flex items-center justify-between pt-3 border-t">
            <button
              type="button"
              onClick={() => setStep(3)}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm text-gray-700 hover:text-gray-900"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
              Back to review
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
