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
import { Target, Loader2, Sparkles } from 'lucide-react';
import {
  CNFApiService,
  type PatternClassifyResponse,
  type CNFRecall24hAggregatedIngredient,
} from '@/lib/api';
import { AudienceToggle, type UserType } from '@/components/shared/AudienceToggle';
import { DietaryPatternResult } from '@/components/shared/DietaryPatternResult';
import { useRecall24hReceiver } from '@/components/shared/useRecall24hReceiver';

interface ApiError { status: number; message: string }

function DietaryPatternPageInner() {
  const [userType,   setUserType]    = useState<UserType>('individual');
  const [loading,    setLoading]     = useState(false);
  const [data,       setData]        = useState<PatternClassifyResponse | null>(null);
  const [error,      setError]       = useState<ApiError | null>(null);
  const [foodsInput, setFoodsInput]  = useState<CNFRecall24hAggregatedIngredient[]>([]);
  const [withNarrative, setWithNarrative] = useState(false);

  // DIET-PATTERN-1: pick up aggregated daily list handed off from the
  // recall wizard via sessionStorage. Same mechanism as the 5 scoring
  // calculators.
  useRecall24hReceiver({
    target: 'dietary_pattern',
    onIngredients: (ingredients, meta) => {
      setUserType(meta.user_type);
      setFoodsInput(ingredients);
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
                Which canonical eating pattern does today&rsquo;s day-vector resemble most?
                Scored against literature-anchored prototypes (Mediterranean, DASH, Western,
                Vegetarian, Vegan, Canada&rsquo;s Food Guide, West African Staple
                {userType !== 'individual' && <>, EAT-Lancet</>}).
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Single-day snapshot. For usual-eating-pattern claims, log multiple recall days.
              </p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t flex justify-center">
            <AudienceToggle userType={userType} onChange={setUserType} accent="blue" />
          </div>
        </header>

        {/* No data yet — explain how to get here */}
        {foodsInput.length === 0 && !loading && (
          <div className="bg-white rounded-lg border p-6 shadow-sm text-sm text-gray-600 space-y-2">
            <p className="font-medium text-gray-900">
              How to score a dietary pattern
            </p>
            <ol className="list-decimal list-inside space-y-1">
              <li>Go to the <a href="/recall-24h" className="text-blue-700 underline">24-h dietary recall wizard</a>.</li>
              <li>Log your day occasion-by-occasion.</li>
              <li>On Step 4 (Score), click <span className="font-medium">🎯 Score Dietary Pattern</span>.</li>
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
