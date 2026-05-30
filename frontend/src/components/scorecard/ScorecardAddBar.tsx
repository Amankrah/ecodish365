/**
 * ScorecardAddBar — inline composer for the Scorecard page. Reuses
 * production primitives (AIEnhancedSearch + RecipeDecomposerModal) and
 * adds tiny launch links for the recall wizard, saved-day picker, and
 * packaged-food scanner.
 *
 * On any successful add, writes to the active food list via
 * `saveActiveFoodList()` — the page's FoodListPanel re-renders via the
 * `ACTIVE_FOOD_LIST_EVENT`.
 */
'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import {
  Plus, ChefHat, CalendarClock, Bookmark, Camera, X,
} from 'lucide-react';
import { AIEnhancedSearch } from '@/components/shared/AIEnhancedSearch';
import { RecipeDecomposerModal } from '@/components/shared/RecipeDecomposerModal';
import type { UserType } from '@/components/shared/AudienceToggle';
import {
  loadActiveFoodList, saveActiveFoodList, fromRecallAggregated,
  type ActiveFoodList,
} from '@/lib/activeFoodList';
import {
  listSavedDays, getDay, type SavedRecallDay,
} from '@/lib/recallHistory';

interface Props {
  userType: UserType;
}

/** Merge a new ingredient into the active food list. If the food_id is
 *  already present, sum its mass; otherwise append. */
function mergeIngredient(
  current: ActiveFoodList | null,
  ing: { food_id: number; food_description: string; food_group?: string; mass_g: number },
  userType: UserType,
): ActiveFoodList {
  const existing = current?.ingredients ?? [];
  const idx = existing.findIndex(i => i.food_id === ing.food_id);
  const nextIngs = idx >= 0
    ? existing.map((i, k) => k === idx ? { ...i, mass_g: i.mass_g + ing.mass_g } : i)
    : [...existing, ing];
  return {
    schema_version: 1,
    captured_at: new Date().toISOString(),
    source: current?.source ?? 'manual',
    ingredients: nextIngs,
    estimated_daily_kcal: current?.estimated_daily_kcal,
    user_type: current?.user_type ?? userType,
    meals_meta: current?.meals_meta,
    packaged_food: current?.packaged_food,
    packaged_food_occasions: current?.packaged_food_occasions,
    multi_day: current?.multi_day,
  };
}

export function ScorecardAddBar({ userType }: Props): JSX.Element {
  const [query, setQuery] = useState('');
  const [pendingMass, setPendingMass] = useState<number>(100);
  const [decomposerOpen, setDecomposerOpen] = useState(false);
  const [savedPickerOpen, setSavedPickerOpen] = useState(false);

  const savedDays: SavedRecallDay[] = useMemo(
    () => savedPickerOpen ? listSavedDays() : [],
    [savedPickerOpen],
  );

  function addOneFood(food: { food_id: number; food_description: string; food_group?: string }): void {
    if (!Number.isFinite(pendingMass) || pendingMass <= 0) {
      setPendingMass(100);
      return;
    }
    const current = loadActiveFoodList();
    const next = mergeIngredient(current, { ...food, mass_g: pendingMass }, userType);
    saveActiveFoodList(next);
    setQuery('');
    setPendingMass(100);
  }

  function handleDecomposed(
    ingredients: Array<{ food_id: number; food_description: string; mass_g: number }>,
  ): void {
    let current = loadActiveFoodList();
    for (const ing of ingredients) {
      current = mergeIngredient(current, ing, userType);
    }
    if (current) saveActiveFoodList(current);
    setDecomposerOpen(false);
  }

  function loadSavedDay(id: string): void {
    const day = getDay(id);
    if (!day) return;
    const list = fromRecallAggregated(day.aggregated_daily_ingredients, {
      estimated_daily_kcal: day.estimated_daily_kcal,
      user_type: day.user_type,
      meals_meta: day.meals.map(m => ({
        occasion: m.occasion,
        dish_name: m.decomposition.dish_name,
        total_mass_g: m.decomposition.total_mass_g,
      })),
    });
    saveActiveFoodList(list);
    setSavedPickerOpen(false);
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
      <div className="flex flex-wrap items-end gap-2">
        <div className="flex-1 min-w-[240px]">
          <label htmlFor="scorecard-food-search" className="block text-xs font-medium text-gray-700 mb-1">
            Search a food
          </label>
          <input
            id="scorecard-food-search"
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="e.g. apple, salmon, fonio, baobab"
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
        </div>
        <div>
          <label htmlFor="scorecard-mass" className="block text-xs font-medium text-gray-700 mb-1">
            Grams
          </label>
          <input
            id="scorecard-mass"
            type="number"
            min={1}
            max={5000}
            value={pendingMass}
            onChange={e => setPendingMass(parseFloat(e.target.value) || 0)}
            className="w-24 px-2 py-2 border border-gray-300 rounded-md text-sm text-right"
          />
        </div>
      </div>

      {query.trim().length >= 2 && (
        <div className="border-t pt-2">
          <p className="text-[11px] text-gray-600 mb-1">Pick a match (or use AI ranker):</p>
          <AIEnhancedSearch
            query={query}
            userType={userType}
            accent="blue"
            onSelect={addOneFood}
          />
        </div>
      )}

      <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-100">
        <button
          type="button"
          onClick={() => setDecomposerOpen(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-purple-700 border border-purple-300 bg-white rounded-md hover:bg-purple-50"
        >
          <ChefHat className="h-3.5 w-3.5" aria-hidden="true" />
          Decompose a homemade dish
        </button>
        <Link
          href="/recall-24h"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-green-700 border border-green-300 bg-white rounded-md hover:bg-green-50"
        >
          <CalendarClock className="h-3.5 w-3.5" aria-hidden="true" />
          {userType === 'individual' ? 'Log a food diary day' : 'Log a 24-h recall'}
        </Link>
        <button
          type="button"
          onClick={() => setSavedPickerOpen(v => !v)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-violet-700 border border-violet-300 bg-white rounded-md hover:bg-violet-50"
        >
          <Bookmark className="h-3.5 w-3.5" aria-hidden="true" />
          Load a saved day
        </button>
        <Link
          href="/scan-product"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-amber-700 border border-amber-300 bg-white rounded-md hover:bg-amber-50"
        >
          <Camera className="h-3.5 w-3.5" aria-hidden="true" />
          Scan a product
        </Link>
      </div>

      {savedPickerOpen && (
        <div className="border-t pt-2 space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium text-gray-700">Saved days</p>
            <button
              type="button"
              onClick={() => setSavedPickerOpen(false)}
              className="text-xs text-gray-500 hover:text-gray-700 inline-flex items-center gap-1"
              aria-label="Close saved days picker"
            >
              <X className="h-3 w-3" aria-hidden="true" /> close
            </button>
          </div>
          {savedDays.length === 0 ? (
            <p className="text-xs text-gray-600">
              No saved days yet. Log a food diary day, then click <strong>Save to history</strong> on the review step.
            </p>
          ) : (
            <ul className="space-y-1 max-h-56 overflow-y-auto">
              {savedDays.map(day => (
                <li key={day.id}>
                  <button
                    type="button"
                    onClick={() => loadSavedDay(day.id)}
                    className="w-full text-left text-xs px-2 py-1.5 rounded hover:bg-violet-50 flex items-center gap-2"
                  >
                    <Plus className="h-3 w-3 text-violet-700" aria-hidden="true" />
                    <span className="font-medium text-gray-900">{day.date}</span>
                    {day.label && <span className="text-gray-600 truncate"> · {day.label}</span>}
                    <span className="ml-auto text-gray-500">
                      {day.aggregated_daily_ingredients.length} foods · {day.estimated_daily_kcal.toFixed(0)} kcal
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <RecipeDecomposerModal
        open={decomposerOpen}
        onClose={() => setDecomposerOpen(false)}
        onApply={handleDecomposed}
        userType={userType}
        accent="purple"
      />
    </div>
  );
}
