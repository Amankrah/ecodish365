/**
 * /dietary-pattern — descriptive dietary-pattern resemblance for an
 * individual's day (DIET-PATTERN-1, 2026-05-24).
 *
 * Receives an aggregated daily ingredient list via sessionStorage (handed
 * off from the 24-h recall wizard's Step 4 score-routing button) AND
 * supports a self-contained no-recall path where the user pastes a JSON
 * food list directly (researcher convenience).
 *
 * Computes resemblance vs the 7 (+1 optional) literature-anchored
 * prototype patterns from /api/dietary-pattern/classify/, renders the
 * top-3 with horizontal cosine bars, the mandatory single-day caveat,
 * and (when opt-in) an LLM-generated narrative paragraph.
 */
'use client';

import { Suspense, useEffect, useState } from 'react';
import { Target, Loader2, Sparkles, CalendarDays, Package } from 'lucide-react';
import {
  CNFApiService,
  type PatternClassifyResponse,
  type CNFRecall24hAggregatedIngredient,
} from '@/lib/api';
import { AudienceToggle, type UserType } from '@/components/shared/AudienceToggle';
import { DietaryPatternResult } from '@/components/shared/DietaryPatternResult';
import { useRecall24hReceiver } from '@/components/shared/useRecall24hReceiver';
import { FoodListPanel } from '@/components/shared/FoodListPanel';

interface ApiError { status: number; message: string }

// RECALL-HISTORY-1 (2026-05-24) — multi-day average metadata passed in
// from /recall-history via the receiver hook. When set, drives the
// "N-day average resembles..." headline + softened caveat.
interface MultiDayMeta {
  n_days: number;
  first_date: string;
  last_date: string;
  label: string;
  day_ids: string[];
}

// PKG-IMG-1 Phase 2 (2026-05-26) — packaged-food provenance passed in
// from /scan-product via the receiver hook. When set, drives the
// "packaged product — inferred composition" framing + caveat swap.
interface PackagedFoodMeta {
  provenance: 'packaged_food_inferred';
  product_name: string | null;
  brand: string | null;
  net_weight_g: number;
  decomposition_confidence: number;
  image_sha256: string;
}

function DietaryPatternPageInner() {
  const [userType,   setUserType]    = useState<UserType>('individual');
  const [loading,    setLoading]     = useState(false);
  const [data,       setData]        = useState<PatternClassifyResponse | null>(null);
  const [error,      setError]       = useState<ApiError | null>(null);
  const [foodsInput, setFoodsInput]  = useState<CNFRecall24hAggregatedIngredient[]>([]);
  const [multiDay,   setMultiDay]    = useState<MultiDayMeta | null>(null);
  const [packagedFood, setPackagedFood] = useState<PackagedFoodMeta | null>(null);
  const [withNarrative, setWithNarrative] = useState(false);

  // DIET-PATTERN-1: pick up aggregated daily list handed off from the
  // recall wizard via sessionStorage. Same mechanism as the 5 scoring
  // calculators.
  // RECALL-HISTORY-1: also receives optional multi_day metadata from
  // /recall-history's N-day-average action.
  // PKG-IMG-1 Phase 2: also receives optional packaged_food metadata from
  // /scan-product's "score with dietary pattern" action.
  useRecall24hReceiver({
    target: 'dietary_pattern',
    onIngredients: (ingredients, meta) => {
      setUserType(meta.user_type);
      setFoodsInput(ingredients);
      setMultiDay(meta.multi_day ?? null);
      setPackagedFood(meta.packaged_food ?? null);
    },
  });

  async function runClassify(includeNarrative: boolean) {
    if (foodsInput.length === 0) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const payload = foodsInput.map(i => ({
        food_id: i.food_id,
        mass_g:  i.mass_g,
      }));
      const r = await CNFApiService.classifyDietaryPattern(payload, {
        userType,
        includeNarrative,
        ...(multiDay ? { metaLabel: multiDay.label } : {}),
        ...(packagedFood ? { decompositionProvenance: packagedFood.provenance } : {}),
      });
      setData(r);
    } catch (e: unknown) {
      const ax = e as { response?: { status?: number; data?: { message?: string; error?: string } } };
      setError({
        status: ax?.response?.status ?? 500,
        message: ax?.response?.data?.message
          || ax?.response?.data?.error
          || 'Pattern classification failed.',
      });
    } finally {
      setLoading(false);
    }
  }

  // Auto-run on first ingredient hand-off, without narrative (cost-cheap).
  useEffect(() => {
    if (foodsInput.length > 0 && data === null && !loading) {
      runClassify(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [foodsInput]);

  return (
    <main className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto space-y-6">
        <header className="bg-white rounded-lg border p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="bg-blue-100 p-3 rounded-lg">
              <Target className="h-8 w-8 text-blue-700" aria-hidden="true" />
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">Dietary pattern resemblance</h1>
              <p className="text-sm text-gray-600 mt-1">
                {packagedFood
                  ? <>Which canonical eating pattern does this <strong>packaged product</strong> resemble most?</>
                  : multiDay
                  ? <>Which canonical eating pattern does your <strong>{multiDay.n_days}-day average</strong> day-vector resemble most?</>
                  : <>Which canonical eating pattern does today&rsquo;s day-vector resemble most?</>}
                {' '}Scored against literature-anchored prototypes (Mediterranean, DASH, Western,
                Vegetarian, Vegan, Canada&rsquo;s Food Guide, West African Staple
                {userType !== 'individual' && <>, EAT-Lancet</>}).
              </p>
              {packagedFood ? (
                <p className="text-xs text-gray-600 mt-2">
                  Packaged-food inferred composition. The ingredient list was
                  AI-extracted from a product label; per-ingredient masses are
                  inferred from regulatory descending-mass-order + NF panel
                  macros (not measured). Interpret as a property of the product.
                </p>
              ) : multiDay ? (
                <p className="text-xs text-gray-600 mt-2">
                  Multi-day average across {multiDay.n_days} saved recall days
                  ({multiDay.first_date} to {multiDay.last_date}). Begins to
                  approximate usual eating but is still a limited sample &mdash;
                  not NCI MCMC usual-intake modelling.
                </p>
              ) : (
                <p className="text-xs text-gray-500 mt-2">
                  Single-day snapshot. For usual-eating-pattern claims, log multiple recall days
                  (see <a href="/recall-history" className="text-blue-700 underline">recall history</a>).
                </p>
              )}
            </div>
          </div>
          <div className="mt-4 pt-4 border-t flex justify-center">
            <AudienceToggle userType={userType} onChange={setUserType} accent="blue" />
          </div>
        </header>

        {/* FOOD-LIST-PANEL (2026-05-26): cross-metric transferable food list. */}
        <FoodListPanel
          currentTarget="dietary_pattern"
          onChange={list => {
            if (!list) {
              setFoodsInput([]);
              return;
            }
            setFoodsInput(list.ingredients.map(i => ({
              food_id: i.food_id,
              food_description: i.food_description,
              food_group: i.food_group ?? '',
              mass_g: i.mass_g,
              occasions: {},
            })));
          }}
        />

        {/* No data yet — explain how to get here */}
        {foodsInput.length === 0 && !loading && (
          <div className="bg-white rounded-lg border p-6 shadow-sm text-sm text-gray-600 space-y-2">
            <p className="font-medium text-gray-900">
              How to score an eating style
            </p>
            <ol className="list-decimal list-inside space-y-1">
              <li>Go to the <a href="/recall-24h" className="text-blue-700 underline">food diary</a>.</li>
              <li>Log your day meal by meal.</li>
              <li>On the score step, click <span className="font-medium">Eating style</span>.</li>
            </ol>
            <p className="text-xs text-gray-500 pt-2 border-t">
              The resemblance is computed against curated prototype days from
              the published nutrition literature (Trichopoulou 2003 for
              Mediterranean, Sacks 2001 for DASH, Orlich 2013 AHS-2 for
              Vegetarian / Vegan, Brassard 2022 for CFG-Healthy, Vincent 2019
              WAFCT sheet 09 for West African Staple
              {userType !== 'individual' && <>, Willett 2019 for EAT-Lancet</>}).
            </p>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="bg-white rounded-lg border p-6 shadow-sm flex items-center gap-3 text-sm text-gray-700">
            <Loader2 className="h-5 w-5 animate-spin text-blue-700" aria-hidden="true" />
            Scoring your day&rsquo;s resemblance to canonical patterns&hellip;
          </div>
        )}

        {/* Error */}
        {error && (
          <div role="alert" className="p-3 rounded-md bg-red-50 border-l-4 border-red-400 text-sm">
            <p className="font-semibold text-red-900">
              {error.status === 429 ? 'Rate-limited'
                : error.status === 503 ? 'Temporarily unavailable'
                : 'Classification failed'}
            </p>
            <p className="text-red-800 mt-0.5">{error.message}</p>
          </div>
        )}

        {/* Result */}
        {data && !loading && (
          <>
            {packagedFood && (
              <div className="bg-amber-50 border border-amber-300 rounded-lg p-4 shadow-sm flex items-start gap-3">
                <Package className="h-5 w-5 text-amber-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <div className="flex-1 text-sm">
                  <p className="font-semibold text-amber-900">
                    📦 Packaged product — inferred composition
                  </p>
                  <p className="text-amber-800 mt-0.5">
                    {packagedFood.product_name || 'Unknown product'}
                    {packagedFood.brand ? ` · ${packagedFood.brand}` : ''}
                    {' · '}{packagedFood.net_weight_g.toFixed(0)} g
                  </p>
                  <p className="text-xs text-amber-700 mt-1">
                    Decomposition confidence:{' '}
                    <strong>{(packagedFood.decomposition_confidence * 100).toFixed(0)}%</strong>.
                    Composition was inferred from the ingredient list + NF panel macros —
                    label percentages were not disclosed. The resemblance describes the
                    PRODUCT, not a day&rsquo;s eating. Re-route via{' '}
                    <a href="/scan-product" className="underline">/scan-product</a>{' '}
                    if you want to edit masses.
                  </p>
                </div>
              </div>
            )}
            {multiDay && (
              <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 shadow-sm flex items-start gap-3">
                <CalendarDays className="h-5 w-5 text-indigo-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <div className="flex-1 text-sm">
                  <p className="font-semibold text-indigo-900">
                    📅 {multiDay.n_days}-day average pattern
                  </p>
                  <p className="text-indigo-800 mt-0.5">
                    {multiDay.label}
                  </p>
                  <p className="text-xs text-indigo-700 mt-1">
                    Mass-weighted concatenation of {multiDay.n_days} saved recall
                    days &mdash; volume-weighted across days, not equal-per-day.
                    See the <a href="/recall-history" className="underline">recall history</a>{' '}
                    for per-day variation.
                  </p>
                </div>
              </div>
            )}
            <DietaryPatternResult data={data} userType={userType} />
            {/* Narrative opt-in */}
            {!data.explanations.narrative && (
              <div className="bg-white rounded-lg border p-4 shadow-sm text-sm">
                <button
                  type="button"
                  onClick={() => { setWithNarrative(true); runClassify(true); }}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md disabled:opacity-50"
                  disabled={loading || withNarrative}
                >
                  <Sparkles className="h-4 w-4" aria-hidden="true" />
                  Generate plain-language explanation
                </button>
                <p className="text-xs text-gray-500 mt-1">
                  Optional LLM-generated narrative (~1 second, +1¢ against your monthly AI quota).
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}

export default function DietaryPatternPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-gray-50" />}>
      <DietaryPatternPageInner />
    </Suspense>
  );
}
