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

import { useState, useMemo, useEffect } from 'react';
import {
  CalendarClock, Coffee, Sandwich, Soup, Apple, Cookie, Pizza,
  Loader2, AlertCircle, Check, Info, Sparkles, ChevronRight, ChevronLeft,
  Camera, Type, Search,
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
import { PackagedFoodOccasionEntry } from './PackagedFoodOccasionEntry';
import { RecallIngredientPicker } from './RecallIngredientPicker';
import {
  buildRecallMealFromPackaged,
  type PackagedOccasionState,
} from '@/lib/recallPackagedFood';
import {
  aggregatedToDirect,
  buildRecallMealFromDirect,
  directDishName,
  directToAggregated,
  type RecallDirectIngredient,
} from '@/lib/recallDirectFood';
import type { UserType } from './AudienceToggle';
// RECALL-HISTORY-1 (2026-05-24): opt-in localStorage save on Step 3.
import {
  saveDay,
  countDays,
  QuotaExceededError,
  type SavedRecallDay,
} from '@/lib/recallHistory';
// FOOD-LIST-PANEL (2026-05-26): mirror the aggregated list into the
// cross-page active food list so the user can score with multiple
// metrics without re-running the wizard.
import { fromRecallAggregated, saveActiveFoodList } from '@/lib/activeFoodList';

interface Recall24hWizardProps {
  userType: UserType;
  /** When set, pre-highlights one score-routing button on step 4. */
  preselectScore?: 'hefi' | 'heni' | 'hsr' | 'fcs' | 'environmental' | 'dietary_pattern' | 'scorecard' | 'planetary' | 'improve_product';
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
  id: 'hefi' | 'heni' | 'hsr' | 'fcs' | 'environmental' | 'dietary_pattern' | 'scorecard' | 'planetary' | 'improve_product';
  emoji: string;
  label: string;
  path: string;
  note?: string;
}> = [
  // SCORECARD-1 (2026-05-26): one-click consumer view across all six lenses.
  { id: 'scorecard',       emoji: '✨', label: 'All scores',            path: '/scorecard',              note: 'Every measure in one view' },
  { id: 'improve_product', emoji: '🔄', label: 'Try ingredient swaps',  path: '/improve-product',        note: 'Find healthier substitutes for foods in this day' },
  { id: 'hefi',            emoji: '🥗', label: 'Healthy eating',        path: '/hefi/calculate',          note: 'How well your day matches Canada\'s Food Guide' },
  { id: 'heni',            emoji: '🧬', label: 'Health impact',         path: '/heni/calculate',          note: 'Healthy-life minutes across the day' },
  { id: 'hsr',             emoji: '⭐', label: 'Star rating',           path: '/hsr/calculate',           note: 'Rough snapshot only. Stars rate products, not whole days.' },
  { id: 'fcs',             emoji: '🧭', label: 'Food Compass',          path: '/fcs/calculate',           note: 'One score from 1 to 100 for the whole day' },
  { id: 'environmental',   emoji: '🌍', label: 'Environment',           path: '/environmental/calculate', note: 'Climate, land, and water footprint' },
  { id: 'dietary_pattern', emoji: '🎯', label: 'Eating style',          path: '/dietary-pattern',        note: 'Which familiar pattern your day resembles' },
  { id: 'planetary',       emoji: '🪐', label: 'Planet budget',         path: '/planetary',              note: 'Your share of a daily planet budget for food' },
];

interface MealRow {
  enabled: boolean;
  entryMode: 'text' | 'packaged' | 'direct';
  dishName: string;
  totalMass: number;
  /** Set when entryMode === 'packaged' and scan+decompose succeeded. */
  packaged?: PackagedOccasionState | null;
  /** User-picked CNF foods when entryMode === 'direct'. */
  directIngredients?: RecallDirectIngredient[];
}

interface ApiError { status: number; message: string }

function humanWarning(code: string): string {
  // Translate backend warning codes into plain English.
  if (code.startsWith('no_breakfast')) return 'No breakfast logged.';
  if (code.startsWith('no_lunch'))     return 'No lunch logged.';
  if (code.startsWith('no_dinner'))    return 'No dinner logged.';
  if (code.startsWith('daily_kcal_below_')) return 'Daily calories look low. Did you forget a meal?';
  if (code.startsWith('daily_kcal_above_')) return 'Daily calories look high. You may have counted something twice.';
  if (code === 'single_occasion_day_aggregation_unreliable') return 'Only one meal logged, so daily totals may not be reliable.';
  if (code.includes('_resolved_only_partially')) return code.split('_')[0] + ' meal(s) resolved only partially.';
  if (code.includes('_failed_to_decompose'))     return code.split('_')[0] + ' meal(s) failed to decompose.';
  if (code.startsWith('packaged_food_inferred_at_')) {
    return 'One or more meals came from a scanned label. Ingredient amounts were estimated, not weighed.';
  }
  if (code.startsWith('direct_food_entry')) {
    return 'One or more meals used foods you picked directly from search.';
  }
  return code;
}

export function Recall24hWizard({ userType, preselectScore }: Recall24hWizardProps) {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [rows, setRows] = useState<Record<RecallOccasion, MealRow>>(() => {
    const out = {} as Record<RecallOccasion, MealRow>;
    for (const o of OCCASIONS) {
      out[o.id] = {
        enabled: o.defaultEnabled,
        entryMode: 'text',
        dishName: '',
        totalMass: o.defaultMass,
        packaged: null,
        directIngredients: [],
      };
    }
    return out;
  });
  const [dayIngredients, setDayIngredients] = useState<RecallDirectIngredient[]>([]);
  const [ingredientsEdited, setIngredientsEdited] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<ApiError | null>(null);
  const [result, setResult]   = useState<CNFRecall24hResult | null>(null);
  const [explanations, setExplanations] = useState<CNFRecall24hExplanations | null>(null);
  // WAFCT-EXTEND (2026-05-24): food-database scope. Forwarded into every
  // meal's Stage-2 ingredient resolution so a 'wafct' recall stays
  // entirely within WAFCT FoodIDs.
  const [source, setSource]   = useState<SourceChoice>('both');
  // RECALL-HISTORY-1 (2026-05-24): "Save this day" panel on Step 3.
  // `saveDate` defaults to today on first render; user can edit. `saveLabel`
  // is optional researcher annotation. `savedDay` flips to the SavedRecallDay
  // after a successful save so re-saves update in place rather than creating
  // duplicates. `saveError` surfaces quota-exceeded.
  const [saveDate, setSaveDate]   = useState<string>(() => new Date().toISOString().slice(0, 10));
  const [saveLabel, setSaveLabel] = useState<string>('');
  const [savedDay, setSavedDay]   = useState<SavedRecallDay | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [historyCount, setHistoryCount] = useState<number>(() => countDays());

  const enabledOccasions = useMemo(
    () => OCCASIONS.filter(o => rows[o.id].enabled),
    [rows],
  );
  const canRunRecall = useMemo(
    () => enabledOccasions.length > 0
       && enabledOccasions.every(o => {
         const row = rows[o.id];
         if (row.entryMode === 'packaged') {
           return row.packaged != null && row.packaged.decomposition.decomposition_succeeded;
         }
         if (row.entryMode === 'direct') {
           return (row.directIngredients?.length ?? 0) > 0
             && (row.directIngredients ?? []).every(i => i.mass_g > 0);
         }
         return row.dishName.trim().length > 0 && row.totalMass > 0;
       }),
    [enabledOccasions, rows],
  );

  const needsLlmDecompose = useMemo(
    () => enabledOccasions.some(o => rows[o.id].entryMode === 'text'),
    [enabledOccasions, rows],
  );

  useEffect(() => {
    if (result) {
      setDayIngredients(aggregatedToDirect(result.aggregated_daily_ingredients));
      setIngredientsEdited(false);
    }
  }, [result]);

  function effectiveAggregatedIngredients() {
    return directToAggregated(dayIngredients);
  }

  function updateDayIngredients(next: RecallDirectIngredient[]) {
    setDayIngredients(next);
    setIngredientsEdited(true);
  }

  const hasPackagedOccasions = useMemo(
    () => enabledOccasions.some(o => rows[o.id].entryMode === 'packaged' && rows[o.id].packaged),
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
    const meals: RecallMealInput[] = enabledOccasions.map(o => {
      const row = rows[o.id];
      if (row.entryMode === 'packaged' && row.packaged) {
        return buildRecallMealFromPackaged(o.id, row.packaged);
      }
      if (row.entryMode === 'direct' && row.directIngredients?.length) {
        const dish = directDishName(o.label, row.directIngredients);
        return buildRecallMealFromDirect(o.id, dish, row.directIngredients);
      }
      return {
        occasion: o.id,
        dish_name: row.dishName.trim(),
        total_mass_g: row.totalMass,
        entry_type: 'text',
      };
    });
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

  function handleSaveToHistory() {
    if (!result) return;
    setSaveError(null);
    try {
      const day = saveDay({
        id: savedDay?.id,
        date: saveDate,
        label: saveLabel.trim(),
        user_type: userType,
        meals: result.meals,
        aggregated_daily_ingredients: effectiveAggregatedIngredients(),
        estimated_daily_kcal: result.estimated_daily_kcal,
        occasions_count: result.occasions_count,
      });
      setSavedDay(day);
      setHistoryCount(countDays());
    } catch (e) {
      if (e instanceof QuotaExceededError) {
        setSaveError(
          'Recall history is full (4 MB limit). Export your existing history then clear it before saving more days.',
        );
      } else {
        setSaveError(`Failed to save: ${(e as Error).message}`);
      }
    }
  }

  function handleRoute(target: typeof SCORE_BUTTONS[number]) {
    if (!result) return;
    // Build the payload once, then use it for both the sessionStorage handoff
    // (consumed by the target page's useRecall24hReceiver) and the cross-page
    // active food list (consumed by FoodListPanel on every scorer page).
    const payload = {
      source: 'recall_24h',
      user_type: userType,
      captured_at: new Date().toISOString(),
      target: target.id,
      meals_meta: enabledOccasions.map(o => {
        const row = rows[o.id];
        if (row.entryMode === 'packaged' && row.packaged) {
          return {
            occasion: o.id,
            dish_name: row.packaged.dishName,
            total_mass_g: row.packaged.totalMass,
            entry_type: 'packaged' as const,
          };
        }
        if (row.entryMode === 'direct' && row.directIngredients?.length) {
          return {
            occasion: o.id,
            dish_name: directDishName(o.label, row.directIngredients),
            total_mass_g: row.directIngredients.reduce((s, i) => s + i.mass_g, 0),
            entry_type: 'direct' as const,
          };
        }
        return {
          occasion: o.id,
          dish_name: row.dishName,
          total_mass_g: row.totalMass,
          entry_type: 'text' as const,
        };
      }),
      ...(hasPackagedOccasions ? {
        packaged_food_occasions: enabledOccasions
          .filter(o => rows[o.id].entryMode === 'packaged' && rows[o.id].packaged)
          .map(o => ({
            occasion: o.id,
            product_name: rows[o.id].packaged!.panel.product_name_visible.value,
            brand: rows[o.id].packaged!.panel.brand_visible.value,
            decomposition_confidence: rows[o.id].packaged!.decomposition.decomposition_confidence,
          })),
      } : {}),
      aggregated_daily_ingredients: effectiveAggregatedIngredients(),
      estimated_daily_kcal: result.estimated_daily_kcal,
    };
    try {
      sessionStorage.setItem('recall_24h_payload', JSON.stringify(payload));
    } catch {
      // sessionStorage may fail in private mode; harmless — the score
      // pages still work standalone.
    }
    try {
      saveActiveFoodList(fromRecallAggregated(effectiveAggregatedIngredients(), {
        user_type: userType,
        estimated_daily_kcal: result.estimated_daily_kcal,
        meals_meta: payload.meals_meta,
        packaged_food_occasions: hasPackagedOccasions
          ? payload.packaged_food_occasions : undefined,
      }));
    } catch { /* localStorage unavailable — non-fatal */ }
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
            Toggle the meals and snacks you had today. You can leave snacks off if you skipped them.
          </p>
          {/* WAFCT-EXTEND (2026-05-24): pick the food database upfront. The
              backend forwards this into every meal's Stage-2 ingredient
              resolution, so a 'wafct' recall stays entirely WAFCT. */}
          <div className="flex items-center gap-3 p-3 rounded-md bg-blue-50 border border-blue-100">
            <span className="text-xs text-gray-700">Food database:</span>
            <SourceFilter source={source} onChange={setSource} accent="blue" />
            <span className="text-xs text-gray-500 ml-auto">
              {source === 'wafct'
                ? 'West African foods only'
                : source === 'cnf'
                ? 'Canadian foods only'
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
            Describe each meal in free text, <strong>pick ingredients</strong> by search or AI,
            or <strong>scan a packaged food</strong> if you ate something with a Nutrition Facts label.
            Mass estimates can be rough for text meals; picked foods and scanned products use the grams you set.
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

                  {/* Entry mode toggle */}
                  <div className="flex flex-wrap gap-2 mb-3">
                    <button
                      type="button"
                      onClick={() => updateRow(o.id, { entryMode: 'text', packaged: null, directIngredients: [] })}
                      className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-md border ${
                        rows[o.id].entryMode === 'text'
                          ? 'border-blue-500 bg-blue-50 text-blue-800'
                          : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      <Type className="h-3.5 w-3.5" aria-hidden="true" />
                      Describe meal
                    </button>
                    <button
                      type="button"
                      onClick={() => updateRow(o.id, {
                        entryMode: 'direct',
                        dishName: '',
                        packaged: null,
                        directIngredients: rows[o.id].directIngredients ?? [],
                      })}
                      className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-md border ${
                        rows[o.id].entryMode === 'direct'
                          ? 'border-blue-500 bg-blue-50 text-blue-800'
                          : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      <Search className="h-3.5 w-3.5" aria-hidden="true" />
                      Pick ingredients
                    </button>
                    <button
                      type="button"
                      onClick={() => updateRow(o.id, { entryMode: 'packaged', dishName: '', packaged: null, directIngredients: [] })}
                      className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-md border ${
                        rows[o.id].entryMode === 'packaged'
                          ? 'border-blue-500 bg-blue-50 text-blue-800'
                          : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      <Camera className="h-3.5 w-3.5" aria-hidden="true" />
                      Scan packaged food
                    </button>
                  </div>

                  {rows[o.id].entryMode === 'text' ? (
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
                  ) : rows[o.id].entryMode === 'direct' ? (
                    <RecallIngredientPicker
                      userType={userType}
                      source={source}
                      ingredients={rows[o.id].directIngredients ?? []}
                      onChange={ings => updateRow(o.id, { directIngredients: ings })}
                      defaultMassG={Math.max(50, Math.round(o.defaultMass / 2))}
                      searchPlaceholder={`Search foods for ${o.label.toLowerCase()}…`}
                      emptyHint="Type a food name, pick from results, or use Find with AI. Set grams for each item."
                    />
                  ) : (
                    <PackagedFoodOccasionEntry
                      occasionLabel={o.label}
                      userType={userType}
                      value={rows[o.id].packaged ?? null}
                      onChange={state => updateRow(o.id, {
                        packaged: state,
                        dishName: state?.dishName ?? '',
                        totalMass: state?.totalMass ?? o.defaultMass,
                      })}
                    />
                  )}
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
              {loading
                ? (needsLlmDecompose
                  ? `Decomposing ${enabledOccasions.length} meal${enabledOccasions.length === 1 ? '' : 's'}… (8-15 s)`
                  : 'Building your day…')
                : (needsLlmDecompose ? 'Decompose all meals' : 'Build my day')}
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
              <div className="text-lg font-semibold text-gray-900">
                {dayIngredients.reduce((s, i) => s + i.mass_g, 0).toFixed(0)} g
              </div>
            </div>
            <div className="p-3 rounded bg-blue-50 border border-blue-200">
              <div className="text-xs text-gray-600">Estimated kcal</div>
              <div className="text-lg font-semibold text-gray-900">
                {result.estimated_daily_kcal.toFixed(0)}
                {ingredientsEdited && (
                  <span className="text-xs font-normal text-amber-700 ml-1" title="Kcal from decomposition; re-score to refresh after edits">
                    *
                  </span>
                )}
              </div>
            </div>
            <div className="p-3 rounded bg-blue-50 border border-blue-200">
              <div className="text-xs text-gray-600">Foods matched</div>
              <div className="text-lg font-semibold text-gray-900">{dayIngredients.length}</div>
            </div>
          </div>

          {ingredientsEdited && (
            <p className="text-xs text-amber-800 bg-amber-50 border-l-2 border-amber-400 px-2 py-1 rounded">
              You edited the ingredient list below. Mass totals update immediately; estimated kcal stays from the last decomposition until you score.
            </p>
          )}

          {/* Daily ingredients — editable for all audiences */}
          <div className="border rounded-lg p-4 bg-white space-y-3">
            <div>
              <h3 className="text-sm font-semibold text-gray-900">Daily ingredients</h3>
              <p className="text-xs text-gray-600 mt-0.5">
                Add, remove, or adjust grams. Search by name or use <strong>Find with AI</strong> for free-text foods.
              </p>
            </div>
            <RecallIngredientPicker
              userType={userType}
              source={source}
              ingredients={dayIngredients}
              onChange={updateDayIngredients}
              defaultMassG={100}
              searchPlaceholder="Add a food to your day…"
              emptyHint="No foods yet. Search or use Find with AI to build your day."
            />
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
                      {m.decomposition.fallback_reason === 'packaged_food_inferred' && (
                        <span className="text-[10px] uppercase font-semibold text-amber-700 bg-amber-100 px-1 py-0.5 rounded">
                          scanned
                        </span>
                      )}
                      {m.decomposition.fallback_reason === 'direct_food_entry' && (
                        <span className="text-[10px] uppercase font-semibold text-blue-700 bg-blue-100 px-1 py-0.5 rounded">
                          picked
                        </span>
                      )}
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

          {/* Researcher audit: raw aggregated list with occasion attribution */}
          {userType !== 'individual' && !ingredientsEdited && (
            <details className="border rounded-lg">
              <summary className="cursor-pointer px-3 py-2 text-sm font-medium text-gray-900 hover:bg-gray-50">
                Daily food list ({result.aggregated_daily_ingredients.length} foods)
              </summary>
              <ul className="divide-y text-xs">
                {result.aggregated_daily_ingredients.map(i => (
                  <li key={i.food_id} className="px-3 py-1.5 flex items-center gap-2">
                    <span className="flex-1 truncate flex items-center gap-1.5">
                      <span className="font-medium text-gray-900 truncate">{i.food_description}</span>
                      <SourceBadge foodId={i.food_id} userType={userType} />
                      <span className="text-gray-500 truncate"> · FoodID {i.food_id} · {i.food_group}</span>
                    </span>
                    <span className="text-gray-700 tabular-nums">{i.mass_g.toFixed(0)} g</span>
                  </li>
                ))}
              </ul>
            </details>
          )}

          {/* RECALL-HISTORY-1 (2026-05-24): opt-in localStorage save. Lets
              users build a multi-day history that powers the /recall-history
              page's N-day average pattern view. Data NEVER leaves the user's
              browser unless they explicitly export or re-score. */}
          <details className="border rounded-lg p-4 bg-blue-50">
            <summary className="cursor-pointer text-sm font-medium text-blue-900">
              💾 Save this day to your history (browser-local)
            </summary>
            <div className="mt-3 space-y-3 text-sm">
              <p className="text-xs text-gray-600">
                Saved days appear on the <a href="/recall-history" className="text-blue-700 underline">recall history</a> page,
                where you can compute an N-day average pattern, export as JSON / CSV
                for research analysis, or re-score any day individually.
                Stored only in this browser. Nothing is uploaded unless you choose to score it.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-[140px,1fr] gap-2 items-center">
                <label htmlFor="recall-save-date" className="text-xs font-medium text-gray-700">
                  Date this day reflects
                </label>
                <input
                  id="recall-save-date"
                  type="date"
                  value={saveDate}
                  onChange={(e) => setSaveDate(e.target.value)}
                  className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md"
                  title="ISO date the day occurred (defaults to today)"
                />
                <label htmlFor="recall-save-label" className="text-xs font-medium text-gray-700">
                  Label (optional)
                </label>
                <input
                  id="recall-save-label"
                  type="text"
                  value={saveLabel}
                  onChange={(e) => setSaveLabel(e.target.value)}
                  placeholder="e.g. 'Tuesday' or 'Subject 04 / Day 2'"
                  className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md"
                />
              </div>
              <button
                type="button"
                onClick={handleSaveToHistory}
                disabled={!saveDate || !result}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {savedDay ? '✓ Saved · update' : '💾 Save to history'}
              </button>
              {savedDay && (
                <p className="text-xs text-blue-700">
                  Saved. Your history now contains{' '}
                  <strong>{historyCount}</strong> day{historyCount === 1 ? '' : 's'}.{' '}
                  <a href="/recall-history" className="underline">Open recall history →</a>
                </p>
              )}
              {saveError && (
                <p className="text-xs text-red-700 bg-red-50 border-l-4 border-red-400 px-2 py-1">
                  {saveError}
                </p>
              )}
            </div>
          </details>

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
            Send your day to any score. Each opens with this day&apos;s foods already loaded.
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
                        Star ratings compare products within a category. A daily average is only a rough snapshot.
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
