'use client';

// Nutrient analysis: research-grade composition page for a meal or a
// 24-hour recall. Distinct from the multi-lens scorer at /scorecard and
// from the per-lens calculators at /hefi/calculate, /heni/calculate, etc.
// This page surfaces the composition substrate (nutrients vs DRIs, FPED
// food groups, NOVA processing, AMDR macros, per-nutrient contributors)
// that the lens calculators sit on top of.
//
// Route history:
//   /research/meal-deep-dive  -> renamed 2026-06-25 (intermediate stop
//   /research/six-lens-analyzer was a naming mistake; both legacy paths
//   redirect here). Backend endpoint /api/research/meal-deep-dive/ is
//   unchanged.
//
// Builds a meal or a multi-meal day from the CNF + WAFCT catalogue,
// resolves a life-stage tuple from (age, sex, pregnancy, lactation), and
// POSTs to /api/research/meal-deep-dive/. Results render across six
// composition tabs: nutrients (with DRI flags), food groups (FPED),
// processing (NOVA), macronutrient distribution (AMDR bands),
// per-nutrient contributors, and coverage / provenance.
//
// Exports the full payload as JSON, and pulls the long-format CSV from
// the dedicated export endpoint.

import React, { Suspense, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { CNFApiService } from '@/lib/api';
import { loadActiveFoodList } from '@/lib/activeFoodList';
import { SourceFilter, type SourceChoice } from '@/components/shared/SourceFilter';
import { Utensils } from 'lucide-react';
import { ClipboardDocumentListIcon } from '@heroicons/react/24/outline';
import axios from 'axios';

const API_BASE_URL =
  process.env.NODE_ENV === 'development'
    ? 'http://localhost:8000/api'
    : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api');

type LifeStageInput = {
  age_years: number | null;
  sex: 'male' | 'female' | '';
  pregnancy_status: string;
  lactation_status: string;
};

type FoodLine = {
  food_id: number;
  food_description: string;
  mass_g: number;
};

type Meal = {
  label: string;
  foods: FoodLine[];
};

type DriBlock = {
  ear: number | null;
  rda: number | null;
  ai: number | null;
  ul: number | null;
  pct_ear: number | null;
  pct_rda: number | null;
  pct_ai: number | null;
  pct_ul: number | null;
  adequacy_flag: string;
  cdrr_value: number | null;
  cdrr_flag: string | null;
};

type NutrientRow = {
  nutrient_id: number;
  name: string;
  unit: string;
  amount: number;
  amount_per_100g_meal: number;
  n_foods_with_value: number;
  n_foods_missing_value: number;
  partially_imputed: boolean;
  dri: DriBlock | null;
};

type DeepDivePayload = {
  meta: any;
  nutrient_panel: NutrientRow[];
  macronutrient_distribution: any;
  food_groups: any;
  processing: any;
  contributions: Record<string, any[]>;
  per_meal: any[] | null;
  coverage: any;
  provenance: any;
};

const TAB_KEYS = [
  'nutrients',
  'food_groups',
  'processing',
  'macros',
  'contributions',
  'coverage',
] as const;

type TabKey = (typeof TAB_KEYS)[number];

const TAB_LABELS: Record<TabKey, string> = {
  nutrients: 'Nutrients',
  food_groups: 'Food groups',
  processing: 'Processing (NOVA)',
  macros: 'Macronutrients',
  contributions: 'Contributions',
  coverage: 'Coverage & provenance',
};

const ADEQUACY_COLOR: Record<string, string> = {
  below_ear: 'bg-red-100 text-red-800',
  below_ear_ul_breach: 'bg-red-200 text-red-900',
  between_ear_rda: 'bg-amber-100 text-amber-800',
  between_ear_rda_ul_breach: 'bg-amber-200 text-amber-900',
  at_or_above_rda: 'bg-emerald-100 text-emerald-800',
  at_or_above_rda_ul_breach: 'bg-amber-200 text-amber-900',
  below_ai: 'bg-amber-100 text-amber-800',
  at_or_above_ai: 'bg-emerald-100 text-emerald-800',
  at_or_above_ul: 'bg-red-100 text-red-800',
  no_reference: 'bg-gray-100 text-gray-600',
};

const AMDR_COLOR: Record<string, string> = {
  within_amdr: 'bg-emerald-100 text-emerald-800',
  above_amdr: 'bg-red-100 text-red-800',
  below_amdr: 'bg-amber-100 text-amber-800',
};

function newMeal(label: string): Meal {
  return { label, foods: [] };
}

// Nutrient-name presentation helpers.
//
// The CNF NUTRIENT_NAME table ships all-uppercase labels with embedded
// abbreviations (e.g. "RETINOL ACTIVITY EQUIVALENTS (RAE)",
// "NIACIN (NIACIN EQUIVALENT NE)", "FOLATE, DFE"). For research-facing
// presentation we title-case the label, keep the canonical abbreviations
// uppercase, and spell out the abbreviation glossary alongside the
// nutrient so readers do not need a separate reference.

const PRESERVE_UPPERCASE = new Set([
  'RAE', 'DFE', 'NE', 'DV', 'EAR', 'RDA', 'AI', 'UL', 'EER', 'CDRR',
  'EPA', 'DHA', 'ALA', 'CLA', 'MUFA', 'PUFA', 'SFA', 'AMDR',
  'D2', 'D3', 'B6', 'B12', 'K1', 'K2',
]);

const NUTRIENT_ABBREVIATIONS: Record<string, string> = {
  RAE: 'Retinol Activity Equivalents',
  DFE: 'Dietary Folate Equivalents',
  NE: 'Niacin Equivalents',
  DV: 'Daily Value',
  EPA: 'Eicosapentaenoic Acid',
  DHA: 'Docosahexaenoic Acid',
  ALA: 'Alpha-Linolenic Acid',
  CLA: 'Conjugated Linoleic Acid',
  MUFA: 'Monounsaturated Fatty Acids',
  PUFA: 'Polyunsaturated Fatty Acids',
  SFA: 'Saturated Fatty Acids',
};

const NUTRIENT_UNIT_DISPLAY: Record<string, string> = {
  Gram: 'g',
  Milligram: 'mg',
  Microgram: 'μg',
  kilocalorie: 'kcal',
  kilojoule: 'kJ',
  NE: 'mg NE',
};

function prettyNutrientName(name: string): string {
  if (!name) return '';
  // Split on whitespace and punctuation so we can title-case the words
  // but preserve the punctuation tokens that follow them.
  return name
    .split(/(\s+|,|\(|\)|\+|\/)/)
    .map((tok) => {
      if (!tok || /^\s+$/.test(tok)) return tok;
      if (',()+/'.includes(tok)) return tok;
      const upper = tok.toUpperCase();
      if (PRESERVE_UPPERCASE.has(upper)) return upper;
      return tok.charAt(0).toUpperCase() + tok.slice(1).toLowerCase();
    })
    .join('')
    // CNF often uses a comma instead of a space before subgroup tags.
    .replace(/\s+,/g, ',')
    .replace(/,(\S)/g, ', $1')
    .trim();
}

function prettyUnit(unit: string): string {
  return NUTRIENT_UNIT_DISPLAY[unit] || unit;
}

function nutrientAbbreviations(name: string): string[] {
  const tokens = (name || '').toUpperCase().split(/[\s(),+/]+/);
  const seen = new Set<string>();
  const out: string[] = [];
  for (const t of tokens) {
    if (NUTRIENT_ABBREVIATIONS[t] && !seen.has(t)) {
      seen.add(t);
      out.push(t);
    }
  }
  return out;
}

// One-shot hydration: when the page mounts after a handoff from the recall
// wizard, the recipe decomposer's recall path, or the CNF search page, the
// shared activeFoodList carries the preloaded ingredient list. We seed the
// meal builder from it and surface a small banner so the user knows where
// the data came from.
type HandoffSource = 'recall24h' | 'cnf_search' | 'manual';

export default function NutrientAnalysisPage() {
  // useSearchParams requires a Suspense boundary in the Next.js App Router.
  return (
    <Suspense fallback={<div className="min-h-screen bg-gray-50" />}>
      <NutrientAnalysisInner />
    </Suspense>
  );
}

function NutrientAnalysisInner() {
  const searchParams = useSearchParams();
  const fromParam = (searchParams?.get('from') || '') as string;
  const [handoffSource, setHandoffSource] = useState<HandoffSource>('manual');
  const [handoffMessage, setHandoffMessage] = useState<string>('');

  // The deep-dive treats the food list as one logical "meal" (or aggregated
  // day) keyed by a single label. Multi-occasion days arrive via the 24h
  // recall wizard and land here as one aggregated list; this page does not
  // re-offer occasion-by-occasion entry because that is exactly what the
  // /recall-24h wizard already does.
  const [meal, setMeal] = useState<Meal>(newMeal('Meal'));

  // Entry-mode picker: which input flow the user wants to use when the
  // meal is empty. `decomposer` shows the inline single-dish form;
  // `recall` is a deep-link out to the existing 24h-recall wizard.
  const [entryMode, setEntryMode] = useState<'picker' | 'decomposer'>('picker');
  const [dishName, setDishName] = useState('');
  const [dishMass, setDishMass] = useState<number>(350);
  const [decomposing, setDecomposing] = useState(false);
  const [decomposeError, setDecomposeError] = useState('');
  const [decomposeNote, setDecomposeNote] = useState('');
  // Layer 1 surface: when the decomposer returns a regional-signal warning
  // (e.g. "jollof rice" run with source=cnf) we render an inline banner with
  // a one-click "retry with WAFCT" / "retry with both" handoff so the user
  // does not have to figure out the source filter on their own.
  const [sourceWarning, setSourceWarning] = useState<string>('');
  const [recommendedSource, setRecommendedSource] = useState<SourceChoice | null>(null);
  // Researcher-facing food-database scope for the decomposer. Default to
  // `both` (CNF + WAFCT) so users do not get accidentally narrowed; they
  // opt into single-source by clicking CNF or WAFCT. The Stage-2 LLM
  // ingredient resolver then only ranks in-scope catalogue rows.
  const [decomposerSource, setDecomposerSource] = useState<SourceChoice>('both');

  const [lifeStage, setLifeStage] = useState<LifeStageInput>({
    age_years: 34,
    sex: 'female',
    pregnancy_status: 'not_pregnant',
    lactation_status: 'not_lactating',
  });

  const [scope, setScope] = useState<'meal' | 'day'>('meal');
  const [submitting, setSubmitting] = useState(false);
  const [payload, setPayload] = useState<DeepDivePayload | null>(null);
  const [error, setError] = useState<string>('');
  const [activeTab, setActiveTab] = useState<TabKey>('nutrients');

  // Hydrate the meal builder from a handoff source on first mount.
  //
  // Priority order (each source wins over the next):
  //   1. sessionStorage `recall_24h_payload`. The recall wizard sets this
  //      when routing to a target page; it carries occasion-tagged meals
  //      and the deduped daily ingredient list.
  //   2. localStorage activeFoodList. Set by the recall wizard, the CNF
  //      search "Send to deep-dive" handoff, and any future producer.
  //      Carries a flat ingredient list with no occasion metadata.
  //
  // Anything we hydrate is purely advisory; the user can edit the meal
  // builder freely before submitting.
  useEffect(() => {
    if (typeof window === 'undefined') return;

    // 1. Try the sessionStorage recall payload first. It carries per-meal
    //    decomposition with occasion labels, which is the richest shape.
    try {
      const raw = sessionStorage.getItem('recall_24h_payload');
      if (raw) {
        const payload = JSON.parse(raw);
        if (payload?.target === 'research_deep_dive'
            && Array.isArray(payload.aggregated_daily_ingredients)
            && payload.aggregated_daily_ingredients.length > 0) {
          // Use the per-meal_meta breakdown when present so each meal becomes
          // its own occasion tab; otherwise fall back to one "day" meal.
          const mealsMeta = Array.isArray(payload.meals_meta)
            ? payload.meals_meta
            : [];
          const label = mealsMeta.length > 0
            ? `Day (from 24h recall, ${mealsMeta.length} occasion${mealsMeta.length === 1 ? '' : 's'})`
            : 'Day (from 24h recall)';
          setMeal({
            label,
            foods: payload.aggregated_daily_ingredients.map((i: any) => ({
              food_id: i.food_id,
              food_description: i.food_description || `CNF FoodID ${i.food_id}`,
              mass_g: i.mass_g,
            })),
          });
          setScope('day');
          setHandoffSource('recall24h');
          setHandoffMessage(
            `Loaded ${payload.aggregated_daily_ingredients.length} foods from your 24h recall.`,
          );
          sessionStorage.removeItem('recall_24h_payload');
          return;
        }
      }
    } catch { /* sessionStorage unavailable; fall through */ }

    // 2. Fall back to the cross-page activeFoodList.
    try {
      const list = loadActiveFoodList();
      if (list && Array.isArray(list.ingredients) && list.ingredients.length > 0) {
        const isDay = list.source === 'recall_24h';
        setMeal({
          label: isDay ? 'Day (from food diary)' : 'Selected foods',
          foods: list.ingredients.map(i => ({
            food_id: i.food_id,
            food_description: i.food_description,
            mass_g: i.mass_g,
          })),
        });
        setScope(list.ingredients.length > 6 ? 'day' : 'meal');
        if (fromParam === 'cnf_search' || list.source === 'catalogue') {
          setHandoffSource('cnf_search');
          setHandoffMessage(
            `Loaded ${list.ingredients.length} food${list.ingredients.length === 1 ? '' : 's'} `
            + `from Food Search. Default mass is 100 g; edit as needed.`,
          );
        } else if (list.source === 'recall_24h') {
          setHandoffSource('recall24h');
          setHandoffMessage(
            `Loaded ${list.ingredients.length} foods from your food diary.`,
          );
        }
      }
    } catch { /* localStorage unavailable; fall through */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Run the recipe decomposer on a single dish name and replace the
  // current meal with the resolved CNF ingredient list. Mirrors the
  // recall-wizard text-occasion flow but for the deep-dive's single-meal
  // case.
  const runDecomposer = async (
    overrideSource?: SourceChoice,
  ) => {
    const name = dishName.trim();
    if (!name) {
      setDecomposeError('Enter a dish name first.');
      return;
    }
    if (!dishMass || dishMass <= 0) {
      setDecomposeError('Enter a total mass in grams.');
      return;
    }
    const useSource = overrideSource ?? decomposerSource;
    setDecomposing(true);
    setDecomposeError('');
    setDecomposeNote('');
    setSourceWarning('');
    setRecommendedSource(null);
    try {
      const result = await CNFApiService.decomposeRecipe(name, dishMass, {
        userType: 'researcher',
        source: useSource,
      });
      // Layer 1: regional-signal banner. Capture before bailing on
      // empty-ingredient so the user sees the recommendation even when
      // the CNF-only path returned nothing usable.
      if (result.source_warning) {
        setSourceWarning(result.source_warning);
        const rec = result.recommended_source;
        if (rec === 'cnf' || rec === 'wafct' || rec === 'both') {
          setRecommendedSource(rec);
        }
      }
      if (!result.ingredients || result.ingredients.length === 0) {
        setDecomposeError(
          result.fallback_reason
            ? `Decomposer returned no ingredients (${result.fallback_reason}).`
            : 'Decomposer returned no ingredients.',
        );
        return;
      }
      setMeal({
        label: result.normalised_dish_name || name,
        foods: result.ingredients.map(i => ({
          food_id: i.food_id,
          food_description: i.food_description,
          mass_g: i.mass_g,
        })),
      });
      setScope('meal');
      const confidencePct = Math.round(result.decomposition_confidence * 100);
      const unresolvedPct = result.total_mass_g > 0
        ? Math.round(result.unresolved_mass_g / result.total_mass_g * 100)
        : 0;
      const sourceLabel = useSource === 'both'
        ? 'CNF + WAFCT'
        : useSource === 'cnf' ? 'CNF only' : 'WAFCT only';
      const foldNote = result.near_duplicate_folds && result.near_duplicate_folds > 0
        ? `; folded ${result.near_duplicate_folds} near-duplicate ingredient${result.near_duplicate_folds === 1 ? '' : 's'}`
        : '';
      setDecomposeNote(
        `Decomposed ${result.ingredients.length} ingredient${result.ingredients.length === 1 ? '' : 's'} `
        + `from ${sourceLabel} at ${confidencePct}% confidence`
        + (unresolvedPct > 0 ? `; ${unresolvedPct}% mass unresolved` : '')
        + foldNote
        + (result.cache_hit ? ' (cached)' : '')
        + '.',
      );
    } catch (err: any) {
      const msg = err?.response?.data?.message || err?.message || 'decompose failed';
      setDecomposeError(msg);
    } finally {
      setDecomposing(false);
    }
  };

  // Layer 1 handoff: re-run the decomposer with the recommended source
  // (also updating the SourceFilter control so the user sees the change).
  const retryWithRecommendedSource = () => {
    if (!recommendedSource) return;
    setDecomposerSource(recommendedSource);
    setSourceWarning('');
    setRecommendedSource(null);
    runDecomposer(recommendedSource);
  };

  const updateMass = (foodIdx: number, mass: number) => {
    setMeal(prev => ({
      ...prev,
      foods: prev.foods.map((f, j) => j === foodIdx ? { ...f, mass_g: mass } : f),
    }));
  };

  const removeFood = (foodIdx: number) => {
    setMeal(prev => ({
      ...prev,
      foods: prev.foods.filter((_, j) => j !== foodIdx),
    }));
  };

  const resetMeal = () => {
    setMeal(newMeal('Meal'));
    setEntryMode('picker');
    setDishName('');
    setDishMass(350);
    setDecomposeError('');
    setDecomposeNote('');
    setSourceWarning('');
    setRecommendedSource(null);
    setHandoffSource('manual');
    setHandoffMessage('');
    setPayload(null);
  };

  const requestBody = useMemo(() => {
    return {
      scope,
      meals: meal.foods.length > 0
        ? [{
            label: meal.label,
            foods: meal.foods.map((f) => ({
              food_id: f.food_id,
              mass_g: f.mass_g,
            })),
          }]
        : [],
      life_stage:
        lifeStage.age_years && lifeStage.sex
          ? {
              age_years: lifeStage.age_years,
              sex: lifeStage.sex,
              pregnancy_status: lifeStage.pregnancy_status,
              lactation_status: lifeStage.lactation_status,
            }
          : null,
      options: {
        nutrient_set: 'research_canonical',
        include_per_meal_breakdown: false,
        include_top_contributors: true,
        top_k: 5,
      },
    };
  }, [meal, lifeStage, scope]);

  const submit = async () => {
    setSubmitting(true);
    setError('');
    try {
      const r = await axios.post(
        `${API_BASE_URL}/research/meal-deep-dive/`,
        requestBody,
        { headers: { 'Content-Type': 'application/json' } },
      );
      setPayload(r.data?.data || null);
    } catch (err: any) {
      console.error(err);
      setError(err?.response?.data?.message || err.message || 'request failed');
      setPayload(null);
    } finally {
      setSubmitting(false);
    }
  };

  const exportJson = () => {
    if (!payload) return;
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'nutrient-analysis.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportCsv = async () => {
    try {
      const r = await axios.post(
        `${API_BASE_URL}/research/meal-deep-dive/export.csv/`,
        requestBody,
        {
          headers: { 'Content-Type': 'application/json' },
          responseType: 'blob',
        },
      );
      const blob = new Blob([r.data], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'nutrient-analysis.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('csv export failed', err);
      setError('CSV export failed');
    }
  };

  const totalMass = meal.foods.reduce((s, f) => s + f.mass_g, 0);
  const totalFoods = meal.foods.length;

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6">
      <header className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">For researchers</p>
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">
          Nutrient analysis
        </h1>
        <p className="max-w-3xl text-sm text-gray-600">
          Composition assessment for a meal or a 24-hour record. The full nutrient panel with %EAR
          / %RDA / %AI / %UL against the IOM/NASEM Dietary Reference Intakes by life-stage, FPED
          food-group decomposition, NOVA processing-level breakdown, macronutrient distribution
          against the IOM AMDR bands, and per-nutrient top-contributor ranking. Substrate revisions
          and provenance are surfaced in the coverage tab. Export JSON or long-format CSV. For
          published-lens scoring on the same substrate use{' '}
          <Link href="/scorecard" className="text-blue-700 underline">All scores</Link>{' '}
          or any individual lens calculator.
        </p>
        {handoffMessage && (
          <div
            role="status"
            aria-live="polite"
            className={`rounded border px-3 py-2 text-sm ${
              handoffSource === 'recall24h'
                ? 'border-blue-200 bg-blue-50 text-blue-900'
                : 'border-emerald-200 bg-emerald-50 text-emerald-900'
            }`}
          >
            {handoffMessage}
          </div>
        )}
      </header>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* ---------- Meal source + ingredient list column ---------- */}
        <div className="space-y-4 lg:col-span-2">
          {/* Empty state: choose an entry mode (decompose a single meal,
              or jump to the 24h-recall wizard for a full day). The
              catalogue search pages handle the "look at one food" case
              already; this page is meal- and recall-scoped on purpose. */}
          {meal.foods.length === 0 && entryMode === 'picker' && (
            <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900">
                How will you build this meal?
              </h2>
              <p className="mt-1 text-sm text-gray-600">
                The analyzer runs on meals and 24-hour recalls. For
                catalogue-level questions about a single food, use{' '}
                <Link href="/cnf/search" className="text-blue-700 underline">Food Search</Link>{' '}
                or{' '}
                <Link href="/cnf/discover" className="text-blue-700 underline">Discover by Nutrient</Link>.
              </p>
              <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
                <button
                  type="button"
                  onClick={() => setEntryMode('decomposer')}
                  className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-left hover:bg-blue-100"
                >
                  <div className="flex items-center gap-2 font-semibold text-blue-900">
                    <Utensils className="w-4 h-4" aria-hidden="true" /> Decompose a meal
                  </div>
                  <p className="mt-1 text-sm text-blue-900">
                    Describe one dish in free text (pasta with tomato sauce, jollof rice,
                    scrambled eggs and toast) and we break it into CNF ingredients via the
                    decomposer.
                  </p>
                </button>
                <Link
                  href="/recall-24h?then=research_deep_dive"
                  className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-left hover:bg-emerald-100"
                >
                  <div className="flex items-center gap-2 font-semibold text-emerald-900">
                    <ClipboardDocumentListIcon className="w-4 h-4" aria-hidden="true" /> Log a 24-hour recall
                  </div>
                  <p className="mt-1 text-sm text-emerald-900">
                    Walk through up to six meal occasions for a full day; the wizard
                    aggregates the day and lands back here with the foods preloaded.
                  </p>
                </Link>
              </div>
            </div>
          )}

          {/* Decomposer form. Calls /api/recipes/decompose/ via
              CNFApiService.decomposeRecipe and replaces `meal` with the
              resolved ingredient list. */}
          {meal.foods.length === 0 && entryMode === 'decomposer' && (
            <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">Decompose a meal</h2>
                <button
                  type="button"
                  onClick={() => { setEntryMode('picker'); setDecomposeError(''); }}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  back
                </button>
              </div>
              <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                <SourceFilter
                  source={decomposerSource}
                  onChange={setDecomposerSource}
                  accent="blue"
                />
                <p className="text-xs text-gray-500">
                  Database scope for the Stage-2 ingredient resolver.
                </p>
              </div>
              <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-[1fr_140px_auto]">
                <input
                  type="text"
                  value={dishName}
                  onChange={(e) => setDishName(e.target.value)}
                  placeholder="e.g. spaghetti bolognese, jollof rice, oatmeal with berries"
                  className="rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  aria-label="Dish name"
                />
                <input
                  type="number"
                  value={dishMass}
                  onChange={(e) => setDishMass(Math.max(0, Number(e.target.value) || 0))}
                  className="rounded border border-gray-300 px-3 py-2 text-right text-sm focus:border-blue-500 focus:outline-none"
                  aria-label="Total mass in grams"
                  placeholder="grams"
                />
                <button
                  type="button"
                  onClick={() => runDecomposer()}
                  disabled={decomposing || !dishName.trim() || dishMass <= 0}
                  className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 hover:bg-blue-700"
                >
                  {decomposing ? 'decomposing…' : 'Decompose'}
                </button>
              </div>
              <p className="mt-2 text-xs text-gray-500">
                The decomposer runs at 5–15 s typically; results are cached. CNF
                ingredients then become editable below.
              </p>
              {decomposeError && (
                <p className="mt-2 text-sm text-red-600">{decomposeError}</p>
              )}
              {sourceWarning && (
                <div className="mt-3 rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                  <p>{sourceWarning}</p>
                  {recommendedSource && (
                    <button
                      type="button"
                      onClick={retryWithRecommendedSource}
                      className="mt-2 inline-flex items-center rounded bg-amber-600 px-3 py-1 text-xs font-medium text-white hover:bg-amber-700"
                    >
                      Retry with {recommendedSource === 'both' ? 'CNF + WAFCT' : recommendedSource.toUpperCase()}
                    </button>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Editable ingredient list. Same shape regardless of entry path
              (decomposer output, recall hydration, or catalogue handoff). */}
          {meal.foods.length > 0 && (
            <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">{meal.label}</h2>
                  <p className="text-xs text-gray-600">
                    {meal.foods.length} food{meal.foods.length === 1 ? '' : 's'} · {totalMass.toFixed(0)} g total
                    {decomposeNote && ` · ${decomposeNote}`}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setScope(scope === 'meal' ? 'day' : 'meal')}
                    className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50"
                    title="Scope flag attached to the deep-dive request; affects per-meal vs day-level framing in the response."
                  >
                    scope: {scope}
                  </button>
                  <button
                    type="button"
                    onClick={resetMeal}
                    className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50"
                  >
                    start over
                  </button>
                </div>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-xs text-gray-600">
                    <th className="py-1">food</th>
                    <th className="py-1 text-right font-mono tabular-nums">mass (g)</th>
                    <th className="py-1" aria-label="remove"></th>
                  </tr>
                </thead>
                <tbody>
                  {meal.foods.map((f, idx) => (
                    <tr key={`${f.food_id}-${idx}`} className="border-b border-gray-100">
                      <td className="py-1">
                        <span className="font-mono text-xs text-gray-500">{f.food_id}</span>{' '}
                        {f.food_description}
                      </td>
                      <td className="py-1 text-right font-mono tabular-nums">
                        <input
                          type="number"
                          aria-label={`Mass in grams for ${f.food_description}`}
                          placeholder="g"
                          value={f.mass_g}
                          onChange={(e) =>
                            updateMass(idx, Math.max(0, Number(e.target.value) || 0))
                          }
                          className="w-20 rounded border border-gray-300 px-2 py-0.5 text-right"
                        />
                      </td>
                      <td className="py-1 pl-2 text-right">
                        <button
                          type="button"
                          aria-label={`Remove ${f.food_description}`}
                          onClick={() => removeFood(idx)}
                          className="text-gray-400 hover:text-red-600"
                        >
                          x
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                {totalFoods} foods · {totalMass.toFixed(0)} g total
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={submit}
                  disabled={submitting || totalFoods === 0}
                  className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 hover:bg-blue-700"
                >
                  {submitting ? 'running...' : 'run nutrient analysis'}
                </button>
                {payload && (
                  <>
                    <button
                      type="button"
                      onClick={exportJson}
                      className="rounded border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50"
                    >
                      JSON
                    </button>
                    <button
                      type="button"
                      onClick={exportCsv}
                      className="rounded border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50"
                    >
                      CSV
                    </button>
                  </>
                )}
              </div>
            </div>
            {error && (
              <p className="mt-2 text-sm text-red-600">{error}</p>
            )}
          </div>
        </div>

        {/* ---------- Life-stage column ---------- */}
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-lg font-semibold text-gray-900">
            Life stage
          </h2>
          <div className="space-y-3">
            <label className="block text-sm">
              <span className="text-gray-700">age (years)</span>
              <input
                type="number"
                value={lifeStage.age_years ?? ''}
                onChange={(e) =>
                  setLifeStage({
                    ...lifeStage,
                    age_years: e.target.value === '' ? null : Number(e.target.value),
                  })
                }
                className="mt-1 w-full rounded border border-gray-300 px-2 py-1"
              />
            </label>
            <label className="block text-sm">
              <span className="text-gray-700">sex</span>
              <select
                value={lifeStage.sex}
                onChange={(e) =>
                  setLifeStage({ ...lifeStage, sex: e.target.value as any })
                }
                className="mt-1 w-full rounded border border-gray-300 px-2 py-1"
              >
                <option value="">unspecified</option>
                <option value="male">male</option>
                <option value="female">female</option>
              </select>
            </label>
            <label className="block text-sm">
              <span className="text-gray-700">pregnancy</span>
              <select
                value={lifeStage.pregnancy_status}
                onChange={(e) =>
                  setLifeStage({
                    ...lifeStage,
                    pregnancy_status: e.target.value,
                  })
                }
                className="mt-1 w-full rounded border border-gray-300 px-2 py-1"
                disabled={lifeStage.sex !== 'female'}
              >
                <option value="not_pregnant">not pregnant</option>
                <option value="pregnant_1st_trimester">pregnant (1st)</option>
                <option value="pregnant_2nd_trimester">pregnant (2nd)</option>
                <option value="pregnant_3rd_trimester">pregnant (3rd)</option>
              </select>
            </label>
            <label className="block text-sm">
              <span className="text-gray-700">lactation</span>
              <select
                value={lifeStage.lactation_status}
                onChange={(e) =>
                  setLifeStage({
                    ...lifeStage,
                    lactation_status: e.target.value,
                  })
                }
                className="mt-1 w-full rounded border border-gray-300 px-2 py-1"
                disabled={lifeStage.sex !== 'female'}
              >
                <option value="not_lactating">not lactating</option>
                <option value="exclusive_0_6m">exclusive 0-6 mo</option>
                <option value="partial_7_12m">partial 7-12 mo</option>
              </select>
            </label>
            {payload?.meta?.life_stage?.resolved_code && (
              <p className="rounded bg-blue-50 px-2 py-1 text-xs text-blue-800">
                resolved: {payload.meta.life_stage.resolved_code}
              </p>
            )}
          </div>
        </div>
      </section>

      {/* ---------- Results ---------- */}
      {payload && (
        <section className="space-y-4">
          <div className="flex flex-wrap gap-1 border-b border-gray-200">
            {TAB_KEYS.map((k) => (
              <button
                key={k}
                type="button"
                onClick={() => setActiveTab(k)}
                className={`-mb-px border-b-2 px-3 py-2 text-sm ${
                  k === activeTab
                    ? 'border-blue-600 text-blue-700'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                {TAB_LABELS[k]}
              </button>
            ))}
          </div>

          {activeTab === 'nutrients' && (
            <NutrientsTab panel={payload.nutrient_panel} />
          )}
          {activeTab === 'food_groups' && (
            <FoodGroupsTab fg={payload.food_groups} />
          )}
          {activeTab === 'processing' && (
            <ProcessingTab proc={payload.processing} />
          )}
          {activeTab === 'macros' && (
            <MacrosTab mac={payload.macronutrient_distribution} />
          )}
          {activeTab === 'contributions' && (
            <ContributionsTab
              contribs={payload.contributions}
              panel={payload.nutrient_panel}
            />
          )}
          {activeTab === 'coverage' && (
            <CoverageTab
              coverage={payload.coverage}
              provenance={payload.provenance}
              meta={payload.meta}
            />
          )}
        </section>
      )}
    </div>
  );
}

// ---------- Tab components ----------

// Plain-language definitions for the DRI table columns. Sourced from the
// IOM and NASEM DRI compendium so the tooltip reads consistently with the
// research deep-dive's reference compendium and the manuscript §3.13 prose.
const DRI_COLUMN_TOOLTIPS: Record<string, string> = {
  EAR:
    'Estimated Average Requirement. The daily intake that meets the needs of '
    + '50% of healthy individuals in this life-stage and sex group. The EAR is '
    + 'the cut-point used at the population level: %EAR below 100% counts as '
    + 'inadequate intake under the IOM (2000) cut-point method.',
  RDA:
    'Recommended Dietary Allowance. The average daily intake sufficient to '
    + 'meet the requirement of nearly all (97 to 98%) healthy individuals in '
    + 'this life-stage. Derived as EAR + 2 × CV. The standard "how much should '
    + 'I get" target.',
  AI:
    'Adequate Intake. Set when the evidence is too thin to derive an EAR. '
    + 'Believed to cover the needs of all healthy individuals in this '
    + 'life-stage. Comparison against AI is descriptive, not a prevalence '
    + 'estimator (IOM 2000).',
  UL:
    'Tolerable Upper Intake Level. The highest daily intake unlikely to cause '
    + 'adverse health effects in almost all individuals in the general '
    + 'population. Risk of adverse effects rises above the UL.',
  '%EAR':
    'Intake as a percentage of the published EAR for this life-stage. Below '
    + '100% triggers the below_ear flag (inadequate by the cut-point method).',
  '%RDA':
    'Intake as a percentage of the RDA. At or above 100% means the '
    + 'recommended level is met or exceeded.',
  '%AI':
    'Intake as a percentage of the AI. Used when the nutrient has no '
    + 'published EAR; below 100% is below_ai, at or above 100% is at_or_above_ai.',
  '%UL':
    'Intake as a percentage of the UL. At or above 100% means intake is at '
    + 'or above the tolerable upper limit and the row is flagged accordingly.',
  flag:
    'Adequacy summary distilled from the four reference comparisons. '
    + 'Categories: below_ear, between_ear_rda, at_or_above_rda (when an EAR '
    + 'is published), below_ai, at_or_above_ai (when only an AI is published), '
    + 'at_or_above_ul (UL breach, independent of the adequacy axis), '
    + 'no_reference (no DRI cell on file for this life-stage).',
  coverage:
    'Number of foods in the meal that carried a value for this nutrient over '
    + 'the total food count. Below 100% means some foods are silent on this '
    + 'nutrient in the CNF. That is no data, not a measured zero, and the '
    + 'row is marked partially imputed in the JSON export.',
};

function ColHeader({
  label,
  tooltip,
  align,
}: {
  label: string;
  tooltip: string;
  align: 'left' | 'right' | 'center';
}) {
  const alignClass =
    align === 'right' ? 'text-right' : align === 'center' ? 'text-center' : 'text-left';
  // Single tooltip source: the custom popover. We do NOT also set the HTML
  // `title` attribute, because browsers render that as a second OS-native
  // tooltip on hover and the two stack on top of each other.
  // Keyboard accessibility: the label is focusable via tabIndex=0 and the
  // popover reveals on focus-within as well as hover.
  return (
    <th scope="col" className={`group relative px-3 py-2 ${alignClass}`}>
      <span
        tabIndex={0}
        aria-describedby={`tt-${label}`}
        className="cursor-help border-b border-dotted border-gray-400 outline-none focus:ring-2 focus:ring-blue-300"
      >
        {label}
      </span>
      <span
        id={`tt-${label}`}
        role="tooltip"
        className="pointer-events-none invisible absolute left-1/2 top-full z-20 mt-1 w-64 -translate-x-1/2 whitespace-normal rounded bg-gray-900 px-3 py-2 text-left text-xs font-normal normal-case leading-snug text-white opacity-0 shadow-lg transition-opacity duration-150 group-hover:visible group-hover:opacity-100 group-focus-within:visible group-focus-within:opacity-100"
      >
        {tooltip}
      </span>
    </th>
  );
}

function NutrientsTab({ panel }: { panel: NutrientRow[] }) {
  return (
    <div className="overflow-x-auto rounded border border-gray-200 bg-white">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50 text-left text-xs text-gray-600">
          <tr>
            <th className="px-3 py-2" scope="col">nid</th>
            <th className="px-3 py-2" scope="col">nutrient</th>
            <th className="px-3 py-2 text-right" scope="col">amount</th>
            <th className="px-3 py-2 text-right" scope="col">per 100 g</th>
            <ColHeader label="EAR"      tooltip={DRI_COLUMN_TOOLTIPS.EAR}      align="right" />
            <ColHeader label="RDA"      tooltip={DRI_COLUMN_TOOLTIPS.RDA}      align="right" />
            <ColHeader label="AI"       tooltip={DRI_COLUMN_TOOLTIPS.AI}       align="right" />
            <ColHeader label="UL"       tooltip={DRI_COLUMN_TOOLTIPS.UL}       align="right" />
            <ColHeader label="%EAR"     tooltip={DRI_COLUMN_TOOLTIPS['%EAR']}  align="right" />
            <ColHeader label="%RDA"     tooltip={DRI_COLUMN_TOOLTIPS['%RDA']}  align="right" />
            <ColHeader label="%AI"      tooltip={DRI_COLUMN_TOOLTIPS['%AI']}   align="right" />
            <ColHeader label="%UL"      tooltip={DRI_COLUMN_TOOLTIPS['%UL']}   align="right" />
            <ColHeader label="flag"     tooltip={DRI_COLUMN_TOOLTIPS.flag}     align="left" />
            <ColHeader label="coverage" tooltip={DRI_COLUMN_TOOLTIPS.coverage} align="right" />
          </tr>
        </thead>
        <tbody>
          {panel.map((row) => {
            const niceName = prettyNutrientName(row.name);
            const unitDisp = prettyUnit(row.unit);
            const abbrs = nutrientAbbreviations(row.name);
            const abbrTitle = abbrs
              .map((a) => `${a} = ${NUTRIENT_ABBREVIATIONS[a]}`)
              .join('; ');
            return (
            <tr key={row.nutrient_id} className="border-t border-gray-100">
              <td className="px-3 py-1 font-mono text-xs text-gray-500">
                {row.nutrient_id}
              </td>
              <td className="px-3 py-1">
                {abbrs.length > 0 ? (
                  <span
                    title={abbrTitle}
                    className="cursor-help border-b border-dotted border-gray-300"
                  >
                    {niceName}
                  </span>
                ) : (
                  niceName
                )}
              </td>
              <td className="px-3 py-1 text-right font-mono tabular-nums">
                {row.amount.toFixed(2)} {unitDisp}
              </td>
              <td className="px-3 py-1 text-right font-mono tabular-nums">
                {row.amount_per_100g_meal.toFixed(2)}
              </td>
              <td className="px-3 py-1 text-right font-mono tabular-nums">{row.dri?.ear ?? '-'}</td>
              <td className="px-3 py-1 text-right font-mono tabular-nums">{row.dri?.rda ?? '-'}</td>
              <td className="px-3 py-1 text-right font-mono tabular-nums">{row.dri?.ai ?? '-'}</td>
              <td className="px-3 py-1 text-right font-mono tabular-nums">{row.dri?.ul ?? '-'}</td>
              <td className="px-3 py-1 text-right font-mono tabular-nums">
                {row.dri?.pct_ear != null ? row.dri.pct_ear.toFixed(1) : '-'}
              </td>
              <td className="px-3 py-1 text-right font-mono tabular-nums">
                {row.dri?.pct_rda != null ? row.dri.pct_rda.toFixed(1) : '-'}
              </td>
              <td className="px-3 py-1 text-right font-mono tabular-nums">
                {row.dri?.pct_ai != null ? row.dri.pct_ai.toFixed(1) : '-'}
              </td>
              <td className="px-3 py-1 text-right font-mono tabular-nums">
                {row.dri?.pct_ul != null ? row.dri.pct_ul.toFixed(1) : '-'}
              </td>
              <td className="px-3 py-1">
                {row.dri && (
                  <span
                    className={`rounded px-2 py-0.5 text-xs ${
                      ADEQUACY_COLOR[row.dri.adequacy_flag] ||
                      'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {row.dri.adequacy_flag.replace(/_/g, ' ')}
                  </span>
                )}
              </td>
              <td className="px-3 py-1 text-right text-xs text-gray-600">
                {row.n_foods_with_value}/
                {row.n_foods_with_value + row.n_foods_missing_value}
              </td>
            </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function FoodGroupsTab({ fg }: { fg: any }) {
  const totals: Record<string, number> = fg?.component_totals || {};
  const units: Record<string, string> = fg?.component_units || {};
  const gaps: any[] = fg?.gaps || [];
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div className="rounded border border-gray-200 bg-white p-4">
        <h3 className="mb-2 text-sm font-semibold text-gray-900">
          FPED component totals
        </h3>
        <table className="w-full text-sm">
          <tbody>
            {Object.entries(totals).map(([k, v]) => (
              <tr key={k} className="border-b border-gray-100">
                <td className="py-1 text-gray-700">{k}</td>
                <td className="py-1 text-right font-mono">
                  {Number(v).toFixed(2)} {units[k] || ''}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="rounded border border-gray-200 bg-white p-4">
        <h3 className="mb-2 text-sm font-semibold text-gray-900">
          MyPlate / Canada Food Guide gaps
        </h3>
        <table className="w-full text-sm">
          <thead className="text-xs text-gray-600">
            <tr>
              <th className="text-left">group</th>
              <th className="text-right">intake</th>
              <th className="text-right">MyPlate %</th>
              <th className="text-right">CFG %</th>
              <th className="text-left">status</th>
            </tr>
          </thead>
          <tbody>
            {gaps.map((g, i) => (
              <tr key={i} className="border-t border-gray-100">
                <td className="py-1">{g.label || g.component}</td>
                <td className="py-1 text-right font-mono tabular-nums">
                  {Number(g.intake).toFixed(2)} {g.unit}
                </td>
                <td className="py-1 text-right font-mono tabular-nums">
                  {g.myplate_pct_of_target ?? '-'}
                </td>
                <td className="py-1 text-right font-mono tabular-nums">
                  {g.cfg_pct_of_target ?? '-'}
                </td>
                <td className="py-1 text-xs text-gray-600">
                  MP {g.myplate_status} · CFG {g.cfg_status}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ProcessingTab({ proc }: { proc: any }) {
  const byMass: Record<string, number> = proc?.share_by_mass || {};
  const byEnergy: Record<string, number> = proc?.share_by_energy || {};
  const perFood: any[] = proc?.per_food || [];
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <NovaShareCard title="NOVA share by mass" shares={byMass} />
        <NovaShareCard title="NOVA share by energy" shares={byEnergy} />
      </div>
      <div className="overflow-x-auto rounded border border-gray-200 bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-600">
            <tr>
              <th className="px-3 py-2 text-left">food</th>
              <th className="px-3 py-2 text-right">mass (g)</th>
              <th className="px-3 py-2 text-right">kcal</th>
              <th className="px-3 py-2 text-center">NOVA</th>
              <th className="px-3 py-2 text-right">conf</th>
              <th className="px-3 py-2 text-left">rationale</th>
            </tr>
          </thead>
          <tbody>
            {perFood.map((f, i) => (
              <tr key={i} className="border-t border-gray-100">
                <td className="px-3 py-1">
                  <span className="font-mono text-xs text-gray-500">
                    {f.food_id}
                  </span>{' '}
                  {f.food_description}
                </td>
                <td className="px-3 py-1 text-right font-mono tabular-nums">{f.mass_g}</td>
                <td className="px-3 py-1 text-right font-mono tabular-nums">{f.energy_kcal}</td>
                <td className="px-3 py-1 text-center font-semibold">
                  {f.nova_level}
                </td>
                <td className="px-3 py-1 text-right font-mono tabular-nums">{f.nova_confidence}</td>
                <td className="px-3 py-1 text-xs text-gray-600">
                  {f.nova_rationale}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function NovaShareCard({
  title,
  shares,
}: {
  title: string;
  shares: Record<string, number>;
}) {
  const colors = ['bg-emerald-500', 'bg-amber-500', 'bg-orange-500', 'bg-red-500'];
  return (
    <div className="rounded border border-gray-200 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-900">{title}</h3>
      <div className="flex h-6 overflow-hidden rounded">
        {[1, 2, 3, 4].map((level) => {
          const v = Number(shares[String(level)] || 0);
          return (
            <div
              key={level}
              className={`${colors[level - 1]} flex items-center justify-center text-xs text-white`}
              style={{ width: `${v}%` }}
              title={`NOVA ${level}: ${v.toFixed(1)}%`}
            >
              {v >= 8 ? `${v.toFixed(0)}%` : ''}
            </div>
          );
        })}
      </div>
      <div className="mt-2 grid grid-cols-4 gap-2 text-xs">
        {[1, 2, 3, 4].map((level) => (
          <div key={level} className="text-center">
            <div className="font-semibold">NOVA {level}</div>
            <div className="text-gray-600">
              {Number(shares[String(level)] || 0).toFixed(1)}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MacrosTab({ mac }: { mac: any }) {
  if (!mac) return null;
  const grams = mac.grams || {};
  const kcal = mac.kcal_from || {};
  const pct = mac.pct_energy || {};
  const amdr = mac.amdr_status || {};
  return (
    <div className="space-y-4">
      <div className="rounded border border-gray-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-semibold text-gray-900">
          Energy distribution (Atwater)
        </h3>
        <table className="w-full text-sm">
          <thead className="text-xs text-gray-600">
            <tr>
              <th className="text-left">macronutrient</th>
              <th className="text-right">grams</th>
              <th className="text-right">kcal</th>
              <th className="text-right">% energy</th>
              <th className="text-left">AMDR</th>
            </tr>
          </thead>
          <tbody>
            {(['carbohydrate', 'protein', 'fat', 'alcohol'] as const).map((m) => (
              <tr key={m} className="border-t border-gray-100">
                <td className="py-1 capitalize">{m}</td>
                <td className="py-1 text-right font-mono tabular-nums">{grams[m]?.toFixed(2) ?? '-'}</td>
                <td className="py-1 text-right font-mono tabular-nums">{kcal[m]?.toFixed(0) ?? '-'}</td>
                <td className="py-1 text-right font-mono tabular-nums">{pct[m]?.toFixed(1) ?? '-'}%</td>
                <td className="py-1">
                  {amdr[m] && (
                    <span
                      className={`rounded px-2 py-0.5 text-xs ${
                        AMDR_COLOR[amdr[m]] || 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {amdr[m].replace(/_/g, ' ')}
                    </span>
                  )}
                </td>
              </tr>
            ))}
            <tr className="border-t border-gray-200 font-semibold">
              <td className="py-1">total</td>
              <td className="py-1"></td>
              <td className="py-1 text-right font-mono tabular-nums">
                {mac.energy_kcal_total?.toFixed(0)}
              </td>
              <td className="py-1"></td>
              <td className="py-1"></td>
            </tr>
          </tbody>
        </table>
        {mac.energy_reconciliation_note && (
          <p className="mt-3 text-xs italic text-gray-500">
            {mac.energy_reconciliation_note}
          </p>
        )}
      </div>
    </div>
  );
}

function ContributionsTab({
  contribs,
  panel,
}: {
  contribs: Record<string, any[]>;
  panel: NutrientRow[];
}) {
  // Build a {nutrient_id -> {name, unit}} dictionary from the nutrient
  // panel so contribution cards can show the readable name + canonical
  // unit instead of bare CNF NutrientIDs.
  const meta = useMemo(() => {
    const m: Record<number, { name: string; unit: string }> = {};
    for (const r of panel) m[r.nutrient_id] = { name: r.name, unit: r.unit };
    return m;
  }, [panel]);

  return (
    <div className="space-y-4">
      {Object.entries(contribs).map(([nid, rows]) => {
        const nidNum = Number(nid);
        const m = meta[nidNum];
        const niceName = m ? prettyNutrientName(m.name) : `Nutrient ID ${nid}`;
        const unit = m ? prettyUnit(m.unit) : '';
        const abbrs = m ? nutrientAbbreviations(m.name) : [];
        return (
          <div key={nid} className="rounded border border-gray-200 bg-white p-4">
            <div className="mb-2">
              <h3 className="text-sm font-semibold text-gray-900">
                {niceName}
                {unit && (
                  <span className="ml-1 font-normal text-gray-500">({unit})</span>
                )}
                <span className="ml-2 font-mono text-xs font-normal text-gray-400">
                  nid {nid}
                </span>
              </h3>
              {abbrs.length > 0 && (
                <p className="mt-0.5 text-xs italic text-gray-500">
                  {abbrs
                    .map((a) => `${a} = ${NUTRIENT_ABBREVIATIONS[a]}`)
                    .join('; ')}
                </p>
              )}
            </div>
            <table className="w-full text-sm">
              <thead className="text-xs text-gray-600">
                <tr>
                  <th className="text-left">food</th>
                  <th className="text-right">amount{unit && ` (${unit})`}</th>
                  <th className="text-right">share</th>
                  <th className="text-right">cumulative</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} className="border-t border-gray-100">
                    <td className="py-1">
                      <span className="font-mono text-xs text-gray-500">
                        {r.food_id}
                      </span>{' '}
                      {r.food_description}
                    </td>
                    <td className="py-1 text-right font-mono">
                      {r.nutrient_amount?.toFixed(2)}
                    </td>
                    <td className="py-1 text-right font-mono tabular-nums">
                      {(r.share_of_total * 100).toFixed(1)}%
                    </td>
                    <td className="py-1 text-right font-mono tabular-nums">
                      {(r.cumulative_share * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })}
    </div>
  );
}

function CoverageTab({
  coverage,
  provenance,
  meta,
}: {
  coverage: any;
  provenance: any;
  meta: any;
}) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div className="rounded border border-gray-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-semibold text-gray-900">Coverage</h3>
        <pre className="overflow-x-auto rounded bg-gray-50 p-3 text-xs text-gray-800">
          {JSON.stringify(coverage, null, 2)}
        </pre>
      </div>
      <div className="rounded border border-gray-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-semibold text-gray-900">Provenance</h3>
        <pre className="overflow-x-auto rounded bg-gray-50 p-3 text-xs text-gray-800">
          {JSON.stringify(provenance, null, 2)}
        </pre>
        <h3 className="mb-2 mt-4 text-sm font-semibold text-gray-900">
          Request meta
        </h3>
        <pre className="overflow-x-auto rounded bg-gray-50 p-3 text-xs text-gray-800">
          {JSON.stringify(meta, null, 2)}
        </pre>
      </div>
    </div>
  );
}
