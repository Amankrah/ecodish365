'use client';

// Research-grade meal and 24h-recall deep-dive page.
//
// Builds a meal or a multi-meal day from the CNF food search, resolves a
// life-stage tuple from (age, sex, pregnancy, lactation), and POSTs to
// /api/research/meal-deep-dive/. Results render across six tabs:
// nutrients (with DRI flags), food groups (FPED), processing (NOVA),
// macronutrient distribution (AMDR bands), per-nutrient contributors,
// and coverage / provenance.
//
// Exports the full payload as JSON, and pulls the long-format CSV from
// the dedicated export endpoint.

import React, { useEffect, useMemo, useState } from 'react';
import { CNFApiService } from '@/lib/api';
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

export default function ResearchMealDeepDivePage() {
  const [meals, setMeals] = useState<Meal[]>([newMeal('breakfast')]);
  const [activeMealIdx, setActiveMealIdx] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Array<{
    FoodID: number;
    FoodDescription: string;
    relevance?: number;
  }>>([]);
  const [searchLoading, setSearchLoading] = useState(false);

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

  // Food search.
  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setSearchResults([]);
      return;
    }
    const handle = setTimeout(async () => {
      try {
        setSearchLoading(true);
        const r = await CNFApiService.searchFoodsEnhanced({
          query: searchQuery,
          limit: 25,
        });
        setSearchResults(
          (r.results || []).map((f) => ({
            FoodID: f.FoodID,
            FoodDescription: f.FoodDescription,
            relevance: f.relevance,
          })),
        );
      } catch (err) {
        console.error('search error', err);
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 200);
    return () => clearTimeout(handle);
  }, [searchQuery]);

  const addFood = (food: { FoodID: number; FoodDescription: string }) => {
    setMeals((prev) => {
      const next = prev.map((m, i) =>
        i === activeMealIdx
          ? {
              ...m,
              foods: [
                ...m.foods,
                {
                  food_id: food.FoodID,
                  food_description: food.FoodDescription,
                  mass_g: 100,
                },
              ],
            }
          : m,
      );
      return next;
    });
  };

  const updateMass = (mealIdx: number, foodIdx: number, mass: number) => {
    setMeals((prev) =>
      prev.map((m, i) =>
        i === mealIdx
          ? {
              ...m,
              foods: m.foods.map((f, j) =>
                j === foodIdx ? { ...f, mass_g: mass } : f,
              ),
            }
          : m,
      ),
    );
  };

  const removeFood = (mealIdx: number, foodIdx: number) => {
    setMeals((prev) =>
      prev.map((m, i) =>
        i === mealIdx
          ? { ...m, foods: m.foods.filter((_, j) => j !== foodIdx) }
          : m,
      ),
    );
  };

  const addMeal = () => {
    const presets = ['breakfast', 'lunch', 'dinner', 'snack 1', 'snack 2'];
    const label =
      presets[meals.length] || `meal ${meals.length + 1}`;
    setMeals((prev) => [...prev, newMeal(label)]);
    setActiveMealIdx(meals.length);
    setScope('day');
  };

  const removeMeal = (idx: number) => {
    if (meals.length === 1) return;
    setMeals((prev) => prev.filter((_, i) => i !== idx));
    setActiveMealIdx((cur) => Math.max(0, Math.min(cur, meals.length - 2)));
    if (meals.length - 1 === 1) setScope('meal');
  };

  const requestBody = useMemo(() => {
    return {
      scope,
      meals: meals
        .filter((m) => m.foods.length > 0)
        .map((m) => ({
          label: m.label,
          foods: m.foods.map((f) => ({
            food_id: f.food_id,
            mass_g: f.mass_g,
          })),
        })),
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
        include_per_meal_breakdown: true,
        include_top_contributors: true,
        top_k: 5,
      },
    };
  }, [meals, lifeStage, scope]);

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
    a.download = 'meal-deep-dive.json';
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
      a.download = 'meal-deep-dive.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('csv export failed', err);
      setError('CSV export failed');
    }
  };

  const currentMeal = meals[activeMealIdx];
  const totalMass = meals.reduce(
    (sum, m) => sum + m.foods.reduce((s, f) => s + f.mass_g, 0),
    0,
  );
  const totalFoods = meals.reduce((sum, m) => sum + m.foods.length, 0);

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-gray-900">
          Research deep-dive: meal and 24h-recall composition
        </h1>
        <p className="max-w-3xl text-sm text-gray-600">
          Build a meal or a 24h recall from the Canadian Nutrient File. The
          deep-dive returns the full nutrient panel with %EAR / %RDA / %AI
          / %UL against the IOM/NASEM Dietary Reference Intakes by
          life-stage, FPED food-group decomposition, NOVA processing-level
          breakdown, macronutrient distribution against the IOM AMDR
          bands, and per-nutrient top-contributor ranking. Substrate
          revisions and provenance are surfaced in the coverage tab.
        </p>
      </header>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* ---------- Meal builder column ---------- */}
        <div className="space-y-4 lg:col-span-2">
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                Meal builder
              </h2>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setScope(scope === 'meal' ? 'day' : 'meal')}
                  className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50"
                >
                  scope: {scope}
                </button>
                <button
                  onClick={addMeal}
                  className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50"
                >
                  + meal
                </button>
              </div>
            </div>

            {/* Meal tabs */}
            {meals.length > 1 && (
              <div className="mb-3 flex flex-wrap gap-1">
                {meals.map((m, idx) => (
                  <button
                    key={idx}
                    onClick={() => setActiveMealIdx(idx)}
                    className={`rounded px-3 py-1 text-sm ${
                      idx === activeMealIdx
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {m.label} ({m.foods.length})
                    {meals.length > 1 && (
                      <span
                        onClick={(e) => {
                          e.stopPropagation();
                          removeMeal(idx);
                        }}
                        className="ml-2 text-gray-400 hover:text-red-600"
                      >
                        x
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}

            {/* Food search */}
            <div className="space-y-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search CNF foods (e.g. apple, broiled chicken, whole wheat bread)"
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              />
              {searchLoading && (
                <p className="text-xs text-gray-500">searching...</p>
              )}
              {searchResults.length > 0 && (
                <div className="max-h-48 overflow-y-auto rounded border border-gray-200">
                  {searchResults.slice(0, 12).map((r) => (
                    <button
                      key={r.FoodID}
                      onClick={() => addFood(r)}
                      className="block w-full border-b border-gray-100 px-3 py-2 text-left text-sm hover:bg-blue-50"
                    >
                      <span className="font-mono text-xs text-gray-500">
                        {r.FoodID}
                      </span>{' '}
                      {r.FoodDescription}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Current meal contents */}
            <div className="mt-4">
              <h3 className="mb-2 text-sm font-medium text-gray-700">
                {currentMeal.label} ({currentMeal.foods.length} foods, total{' '}
                {currentMeal.foods.reduce((s, f) => s + f.mass_g, 0).toFixed(0)} g)
              </h3>
              {currentMeal.foods.length === 0 ? (
                <p className="text-sm italic text-gray-500">no foods yet</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 text-left text-xs text-gray-600">
                      <th className="py-1">food</th>
                      <th className="py-1 text-right">mass (g)</th>
                      <th className="py-1"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentMeal.foods.map((f, idx) => (
                      <tr key={idx} className="border-b border-gray-100">
                        <td className="py-1">
                          <span className="font-mono text-xs text-gray-500">
                            {f.food_id}
                          </span>{' '}
                          {f.food_description}
                        </td>
                        <td className="py-1 text-right">
                          <input
                            type="number"
                            aria-label={`Mass in grams for ${f.food_description}`}
                            placeholder="g"
                            value={f.mass_g}
                            onChange={(e) =>
                              updateMass(
                                activeMealIdx,
                                idx,
                                Math.max(0, Number(e.target.value) || 0),
                              )
                            }
                            className="w-20 rounded border border-gray-300 px-2 py-0.5 text-right"
                          />
                        </td>
                        <td className="py-1 pl-2 text-right">
                          <button
                            type="button"
                            aria-label={`Remove ${f.food_description}`}
                            onClick={() => removeFood(activeMealIdx, idx)}
                            className="text-gray-400 hover:text-red-600"
                          >
                            x
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

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
                  {submitting ? 'running...' : 'compute deep-dive'}
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
            <ContributionsTab contribs={payload.contributions} />
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

function NutrientsTab({ panel }: { panel: NutrientRow[] }) {
  return (
    <div className="overflow-x-auto rounded border border-gray-200 bg-white">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50 text-left text-xs text-gray-600">
          <tr>
            <th className="px-3 py-2">nid</th>
            <th className="px-3 py-2">nutrient</th>
            <th className="px-3 py-2 text-right">amount</th>
            <th className="px-3 py-2 text-right">per 100 g</th>
            <th className="px-3 py-2 text-right">EAR</th>
            <th className="px-3 py-2 text-right">RDA</th>
            <th className="px-3 py-2 text-right">AI</th>
            <th className="px-3 py-2 text-right">UL</th>
            <th className="px-3 py-2 text-right">%EAR</th>
            <th className="px-3 py-2 text-right">%RDA</th>
            <th className="px-3 py-2 text-right">%AI</th>
            <th className="px-3 py-2 text-right">%UL</th>
            <th className="px-3 py-2">flag</th>
            <th className="px-3 py-2 text-right">coverage</th>
          </tr>
        </thead>
        <tbody>
          {panel.map((row) => (
            <tr key={row.nutrient_id} className="border-t border-gray-100">
              <td className="px-3 py-1 font-mono text-xs text-gray-500">
                {row.nutrient_id}
              </td>
              <td className="px-3 py-1">{row.name}</td>
              <td className="px-3 py-1 text-right">
                {row.amount.toFixed(2)} {row.unit}
              </td>
              <td className="px-3 py-1 text-right">
                {row.amount_per_100g_meal.toFixed(2)}
              </td>
              <td className="px-3 py-1 text-right">{row.dri?.ear ?? '-'}</td>
              <td className="px-3 py-1 text-right">{row.dri?.rda ?? '-'}</td>
              <td className="px-3 py-1 text-right">{row.dri?.ai ?? '-'}</td>
              <td className="px-3 py-1 text-right">{row.dri?.ul ?? '-'}</td>
              <td className="px-3 py-1 text-right">
                {row.dri?.pct_ear != null ? row.dri.pct_ear.toFixed(1) : '-'}
              </td>
              <td className="px-3 py-1 text-right">
                {row.dri?.pct_rda != null ? row.dri.pct_rda.toFixed(1) : '-'}
              </td>
              <td className="px-3 py-1 text-right">
                {row.dri?.pct_ai != null ? row.dri.pct_ai.toFixed(1) : '-'}
              </td>
              <td className="px-3 py-1 text-right">
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
          ))}
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
                <td className="py-1 text-right">
                  {Number(g.intake).toFixed(2)} {g.unit}
                </td>
                <td className="py-1 text-right">
                  {g.myplate_pct_of_target ?? '-'}
                </td>
                <td className="py-1 text-right">
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
                <td className="px-3 py-1 text-right">{f.mass_g}</td>
                <td className="px-3 py-1 text-right">{f.energy_kcal}</td>
                <td className="px-3 py-1 text-center font-semibold">
                  {f.nova_level}
                </td>
                <td className="px-3 py-1 text-right">{f.nova_confidence}</td>
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
                <td className="py-1 text-right">{grams[m]?.toFixed(2) ?? '-'}</td>
                <td className="py-1 text-right">{kcal[m]?.toFixed(0) ?? '-'}</td>
                <td className="py-1 text-right">{pct[m]?.toFixed(1) ?? '-'}%</td>
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
              <td className="py-1 text-right">
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

function ContributionsTab({ contribs }: { contribs: Record<string, any[]> }) {
  return (
    <div className="space-y-4">
      {Object.entries(contribs).map(([nid, rows]) => (
        <div key={nid} className="rounded border border-gray-200 bg-white p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">
            Nutrient ID {nid}
          </h3>
          <table className="w-full text-sm">
            <thead className="text-xs text-gray-600">
              <tr>
                <th className="text-left">food</th>
                <th className="text-right">amount</th>
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
                  <td className="py-1 text-right">
                    {(r.share_of_total * 100).toFixed(1)}%
                  </td>
                  <td className="py-1 text-right">
                    {(r.cumulative_share * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
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
