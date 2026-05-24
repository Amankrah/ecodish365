/**
 * AIEnhancedSearch — opt-in LLM ranking layer beside the existing basic search.
 *
 * AI-MATCH-1 (2026-05-23): drops in next to any existing search input on the
 * platform (CNF Explorer, HENI / HEFI / HSR / FCS calculate pages, FCS Compare,
 * FCS Food Profile). The basic fuzzywuzzy search stays unchanged + instant;
 * this component adds a "Find with AI" button that calls
 * /api/cnf/search/ai-enhanced/ on click and renders a single ranked result card
 * with the LLM's chosen CNF FoodID + confidence badge + top-3 alternatives.
 *
 * Audience-aware: in researcher / policy mode the LLM `justification` is
 * shown in a "Why this match?" tooltip; in individual mode the field is blank.
 *
 * Error handling: surfaces 429 (per-IP rate limit) and 503 (monthly circuit
 * breaker) with clear messaging so users always know why AI search degraded.
 */
'use client';

import { useState } from 'react';
import { Sparkles, Loader2, Info, AlertCircle, Check } from 'lucide-react';
import { CNFApiService, type CNFAIMatchResult, type CNFAlternativeMatch } from '@/lib/api';
import type { UserType } from './AudienceToggle';

interface AIEnhancedSearchProps {
  /** Current query string from the basic search input. Empty disables the button. */
  query: string;
  /** Invoked when the user picks a CNF food (the top match or an alternative). */
  onSelect: (food: { food_id: number; food_description: string; food_group?: string }) => void;
  /** Audience mode controls whether the LLM justification is shown. */
  userType: UserType;
  /** Optional accent class for the button. Defaults to blue. */
  accent?: 'blue' | 'green' | 'purple' | 'amber';
}

const ACCENT: Record<NonNullable<AIEnhancedSearchProps['accent']>, string> = {
  blue:   'bg-blue-600 hover:bg-blue-700 text-white',
  green:  'bg-green-600 hover:bg-green-700 text-white',
  purple: 'bg-purple-600 hover:bg-purple-700 text-white',
  amber:  'bg-amber-600 hover:bg-amber-700 text-white',
};

function confidenceBand(confidence: number): { label: string; color: string } {
  if (confidence >= 0.85) return { label: 'High confidence',     color: 'bg-green-100 text-green-800 border-green-200' };
  if (confidence >= 0.6)  return { label: 'Moderate confidence', color: 'bg-blue-100 text-blue-800 border-blue-200' };
  if (confidence >= 0.4)  return { label: 'Low confidence',      color: 'bg-amber-100 text-amber-800 border-amber-200' };
  return { label: 'Very low confidence', color: 'bg-red-100 text-red-800 border-red-200' };
}

interface ApiError {
  status: number;
  message: string;
}

export function AIEnhancedSearch({
  query,
  onSelect,
  userType,
  accent = 'blue',
}: AIEnhancedSearchProps) {
  const [loading, setLoading]     = useState(false);
  const [result, setResult]       = useState<CNFAIMatchResult | null>(null);
  const [error, setError]         = useState<ApiError | null>(null);
  const [showAltsExpanded, setShowAltsExpanded] = useState(false);

  const canFire = !!query.trim() && !loading;

  async function handleClick() {
    if (!canFire) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setShowAltsExpanded(false);
    try {
      const r = await CNFApiService.searchFoodsAI(query, { userType });
      setResult(r);
    } catch (e: unknown) {
      const ax = e as { response?: { status?: number; data?: { message?: string; error?: string } } };
      const st = ax?.response?.status ?? 500;
      const msg = ax?.response?.data?.message
        || ax?.response?.data?.error
        || 'AI search failed. Try again or use basic search.';
      setError({ status: st, message: msg });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={handleClick}
          disabled={!canFire}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium
                      transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${ACCENT[accent]}`}
          title={canFire ? 'Use AI to rank the best CNF match for your query'
                         : 'Type a query first'}
        >
          {loading
            ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            : <Sparkles className="h-4 w-4" aria-hidden="true" />}
          {loading ? 'Searching with AI…' : 'Find with AI'}
        </button>
        {result && (
          <span className="text-xs text-gray-500">
            ranked in {Math.round(result.timing_ms)} ms{result.cache_hit && ' · cached'}
          </span>
        )}
      </div>

      {/* Error states */}
      {error && (
        <div role="alert" className="flex items-start gap-2 p-3 rounded-md bg-red-50 border-l-4 border-red-400 text-sm">
          <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <div className="font-semibold text-red-900">
              {error.status === 429 ? 'AI search rate-limited'
                : error.status === 503 ? 'AI search temporarily unavailable'
                : 'AI search failed'}
            </div>
            <div className="text-red-800 mt-0.5">{error.message}</div>
            <div className="text-red-700 text-xs mt-1">Basic search still works — keep typing.</div>
          </div>
        </div>
      )}

      {/* Success: result card */}
      {result && (
        <div className="border rounded-lg p-3 bg-white shadow-sm space-y-2">
          {result.matched && result.food_id !== null ? (
            <>
              <div className="flex items-start justify-between gap-3">
                <button
                  type="button"
                  onClick={() => onSelect({
                    food_id: result.food_id!,
                    food_description: result.food_description || '',
                    food_group: result.food_group || undefined,
                  })}
                  className="flex-1 text-left hover:bg-gray-50 -m-1 p-1 rounded transition-colors"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Check className="h-4 w-4 text-green-600 flex-shrink-0" aria-hidden="true" />
                    <span className="font-medium text-gray-900">{result.food_description}</span>
                  </div>
                  <div className="text-xs text-gray-500">
                    CNF FoodID {result.food_id} · {result.food_group}
                  </div>
                </button>
                <span
                  className={`text-xs font-medium px-2 py-0.5 rounded-full border whitespace-nowrap ${
                    confidenceBand(result.confidence).color
                  }`}
                  title={`AI confidence: ${(result.confidence * 100).toFixed(0)}%`}
                >
                  {(result.confidence * 100).toFixed(0)}%
                </span>
              </div>

              {/* Justification — researcher / policy only (individual mode receives blank) */}
              {userType !== 'individual' && result.justification && (
                <details className="text-xs text-gray-600 -mt-1">
                  <summary className="cursor-pointer hover:text-gray-900 flex items-center gap-1">
                    <Info className="h-3 w-3" aria-hidden="true" />
                    Why this match?
                  </summary>
                  <p className="mt-1 pl-4 italic">{result.justification}</p>
                </details>
              )}
            </>
          ) : (
            <div className="flex items-start gap-2 text-sm text-amber-900">
              <AlertCircle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
              <div>
                <div className="font-semibold">No high-confidence match found.</div>
                <div className="text-amber-800 text-xs mt-0.5">
                  {result.food_description && result.food_id !== null ? (
                    <>Closest: <em>{result.food_description}</em> (CNF FoodID {result.food_id}, {(result.confidence * 100).toFixed(0)}% confidence).
                       Try basic search or refine your query.</>
                  ) : (
                    <>The AI ranker could not find a confident match. Try basic search or rephrase.</>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Alternatives */}
          {result.alternatives.length > 0 && (
            <div className="pt-2 border-t">
              <button
                type="button"
                onClick={() => setShowAltsExpanded(s => !s)}
                className="text-xs text-gray-600 hover:text-gray-900 flex items-center gap-1"
              >
                {showAltsExpanded ? '▾' : '▸'} {showAltsExpanded ? 'Hide' : 'Show'}{' '}
                {result.alternatives.length} alternative{result.alternatives.length === 1 ? '' : 's'}
              </button>
              {showAltsExpanded && (
                <ul className="mt-2 space-y-1">
                  {result.alternatives.map((alt: CNFAlternativeMatch) => (
                    <li key={alt.food_id}>
                      <button
                        type="button"
                        onClick={() => onSelect({
                          food_id: alt.food_id,
                          food_description: alt.food_description,
                          food_group: alt.food_group,
                        })}
                        className="w-full text-left text-xs px-2 py-1.5 rounded hover:bg-gray-50 flex items-center justify-between gap-2"
                      >
                        <span>
                          <span className="font-medium text-gray-900">{alt.food_description}</span>
                          <span className="text-gray-500 ml-1">· CNF {alt.food_id}</span>
                        </span>
                        <span className="text-gray-400 text-[10px] whitespace-nowrap">
                          sim {(alt.similarity * 100).toFixed(0)}%
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
