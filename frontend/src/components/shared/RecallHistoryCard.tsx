/**
 * RecallHistoryCard — one row of /recall-history (RECALL-HISTORY-1, 2026-05-24).
 *
 * Primary actions stay visible; secondary scoring routes sit in a More menu
 * so the day list stays scannable.
 */
'use client';

import { Target, FlaskConical, Trash2, Eye, Loader2, Sparkles, Pencil, ChevronDown } from 'lucide-react';
import { stashAnalyzeDayIds, type SavedRecallDay } from '@/lib/recallHistory';
import { fromRecallAggregated, saveActiveFoodList } from '@/lib/activeFoodList';

interface RecallHistoryCardProps {
  day: SavedRecallDay;
  selected: boolean;
  onSelectChange: (selected: boolean) => void;
  onDelete: () => void;
  onEdit: () => void;
  classifying?: boolean;
}

const CONFIDENCE_PILL: Record<string, string> = {
  high:     'bg-emerald-100 text-emerald-900 border-emerald-300',
  moderate: 'bg-amber-100   text-amber-900   border-amber-300',
  low:      'bg-gray-100    text-gray-700    border-gray-300',
};

const CONFIDENCE_TOOLTIP: Record<string, string> = {
  high:
    'Strong match. One eating style clearly fits your day best.',
  moderate:
    'Reasonable match, but another style is close. Think of this as a tendency, not a firm label.',
  low:
    'Weak match. Log more days or add more foods for a clearer picture.',
};

const PATTERN_COLOR: Record<string, string> = {
  mediterranean:        'bg-green-100   text-green-900   border-green-300',
  dash:                 'bg-blue-100    text-blue-900    border-blue-300',
  western:              'bg-red-100     text-red-900     border-red-300',
  vegetarian:           'bg-lime-100    text-lime-900    border-lime-300',
  vegan:                'bg-emerald-100 text-emerald-900 border-emerald-300',
  cfg_healthy:          'bg-indigo-100  text-indigo-900  border-indigo-300',
  west_african_staple:  'bg-orange-100  text-orange-900  border-orange-300',
  eat_lancet:           'bg-teal-100    text-teal-900    border-teal-300',
};

function routeDayTo(
  day: SavedRecallDay,
  target: 'hefi' | 'heni' | 'dietary_pattern' | 'scorecard' | 'improve_product',
  path: string,
): void {
  const payload = {
    source: 'recall_24h' as const,
    user_type: day.user_type,
    captured_at: new Date().toISOString(),
    target,
    meals_meta: day.meals.map(m => ({
      occasion: m.occasion,
      dish_name: m.decomposition.dish_name,
      total_mass_g: m.decomposition.total_mass_g,
    })),
    aggregated_daily_ingredients: day.aggregated_daily_ingredients,
    estimated_daily_kcal: day.estimated_daily_kcal,
  };
  try {
    sessionStorage.setItem('recall_24h_payload', JSON.stringify(payload));
  } catch { /* sessionStorage may be unavailable */ }
  try {
    saveActiveFoodList(fromRecallAggregated(payload.aggregated_daily_ingredients, {
      user_type: day.user_type,
      estimated_daily_kcal: payload.estimated_daily_kcal,
      meals_meta: payload.meals_meta,
    }));
  } catch { /* localStorage unavailable */ }
  window.location.href = `${path}?from=recall24h`;
}

function routeDayToAnalyze(day: SavedRecallDay): void {
  stashAnalyzeDayIds([day.id]);
  window.location.href = '/recall-history/analyze';
}

export function RecallHistoryCard({
  day, selected, onSelectChange, onDelete, onEdit, classifying,
}: RecallHistoryCardProps): JSX.Element {
  const totalMass = day.aggregated_daily_ingredients
    .reduce((s, i) => s + i.mass_g, 0);
  const occasionList = day.meals
    .map(m => `${m.occasion} (${m.decomposition.dish_name})`)
    .join(' / ');
  const patternColor = day.cached_pattern
    ? PATTERN_COLOR[day.cached_pattern.top_pattern] || 'bg-gray-100 text-gray-800 border-gray-300'
    : '';

  return (
    <article className="bg-white rounded-lg border p-4 shadow-sm space-y-3">
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={selected}
          onChange={e => onSelectChange(e.target.checked)}
          aria-label={`Select day ${day.date}${day.label ? ' ' + day.label : ''}`}
          className="mt-1 h-4 w-4"
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-gray-900">{day.date}</span>
            {day.label && (
              <span className="text-sm text-gray-700">&middot; {day.label}</span>
            )}
            <span className="text-xs text-gray-500">&middot; {day.user_type}</span>
          </div>
          <p className="text-sm text-gray-700 mt-1 break-words">{occasionList}</p>
          <p className="text-xs text-gray-600 mt-1">
            {day.aggregated_daily_ingredients.length} foods &middot;{' '}
            {totalMass.toFixed(0)} g &middot;{' '}
            {day.estimated_daily_kcal.toFixed(0)} kcal &middot;{' '}
            {day.occasions_count} occasions
          </p>

          <div className="mt-2">
            {classifying ? (
              <span className="inline-flex items-center gap-1.5 text-xs text-gray-600">
                <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
                Scoring pattern&hellip;
              </span>
            ) : day.cached_pattern ? (
              <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full border ${patternColor}`}>
                {day.cached_pattern.top_pattern}
                <span
                  className={`px-1.5 py-0 rounded text-[10px] border cursor-help ${CONFIDENCE_PILL[day.cached_pattern.top_pattern_confidence] || ''}`}
                  title={CONFIDENCE_TOOLTIP[day.cached_pattern.top_pattern_confidence] || ''}
                >
                  {day.cached_pattern.top_pattern_confidence}
                </span>
              </span>
            ) : (
              <span className="text-xs text-gray-500">Pattern not yet scored.</span>
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 pt-2 border-t text-sm">
        <button
          type="button"
          onClick={() => routeDayTo(day, 'dietary_pattern', '/dietary-pattern')}
          className="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-medium"
        >
          <Eye className="h-3.5 w-3.5" aria-hidden="true" />
          Pattern
        </button>
        <button
          type="button"
          onClick={() => routeDayTo(day, 'scorecard', '/scorecard')}
          className="inline-flex items-center gap-1 px-2.5 py-1 bg-violet-600 hover:bg-violet-700 text-white rounded-md text-xs font-medium"
        >
          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
          All scores
        </button>
        <button
          type="button"
          onClick={() => routeDayToAnalyze(day)}
          className="inline-flex items-center gap-1 px-2.5 py-1 bg-violet-50 hover:bg-violet-100 text-violet-800 border border-violet-300 rounded-md text-xs font-medium"
        >
          <Target className="h-3.5 w-3.5" aria-hidden="true" />
          Analyze
        </button>

        <details className="relative">
          <summary className="inline-flex items-center gap-1 px-2.5 py-1 bg-white hover:bg-gray-50 text-gray-800 border border-gray-300 rounded-md text-xs font-medium cursor-pointer list-none">
            More <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
          </summary>
          <div className="absolute left-0 top-full mt-1 z-10 min-w-[10rem] rounded-md border border-gray-200 bg-white py-1 shadow-lg">
            <button
              type="button"
              onClick={onEdit}
              className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-gray-800 hover:bg-gray-50"
            >
              <Pencil className="h-3.5 w-3.5" aria-hidden="true" />
              Edit day
            </button>
            <button
              type="button"
              onClick={() => routeDayTo(day, 'hefi', '/hefi/calculate')}
              className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-gray-800 hover:bg-gray-50"
            >
              <Target className="h-3.5 w-3.5" aria-hidden="true" />
              Score HEFI
            </button>
            <button
              type="button"
              onClick={() => routeDayTo(day, 'heni', '/heni/calculate')}
              className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-gray-800 hover:bg-gray-50"
            >
              <FlaskConical className="h-3.5 w-3.5" aria-hidden="true" />
              Score HENI
            </button>
            <button
              type="button"
              onClick={() => routeDayTo(day, 'improve_product', '/improve-product')}
              className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-gray-800 hover:bg-gray-50"
            >
              Try single-meal swaps
            </button>
            <hr className="my-1 border-gray-100" />
            <button
              type="button"
              onClick={onDelete}
              className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-red-700 hover:bg-red-50"
            >
              <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
              Delete
            </button>
          </div>
        </details>
      </div>
    </article>
  );
}
