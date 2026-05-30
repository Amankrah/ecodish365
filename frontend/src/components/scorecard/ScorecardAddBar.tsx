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

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  Plus, ChefHat, CalendarClock, Bookmark, Camera, X, Check,
} from 'lucide-react';
import { AIEnhancedSearch } from '@/components/shared/AIEnhancedSearch';
import { RecipeDecomposerModal } from '@/components/shared/RecipeDecomposerModal';
import { SourceFilter, type SourceChoice } from '@/components/shared/SourceFilter';
import type { UserType } from '@/components/shared/AudienceToggle';
import {
  loadActiveFoodList, saveActiveFoodList, fromRecallAggregated,
  type ActiveFoodList,
} from '@/lib/activeFoodList';
import {
  listSavedDays, getDay, type SavedRecallDay,
} from '@/lib/recallHistory';
import { CNFApiService } from '@/lib/api';
import type { SearchResult } from '@/lib/api';

interface Props {
  userType: UserType;
  decomposerOpen?: boolean;
  onDecomposerOpenChange?: (open: boolean) => void;
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

export function ScorecardAddBar({
  userType,
  decomposerOpen: decomposerOpenProp,
  onDecomposerOpenChange,
}: Props): JSX.Element {
  const [query, setQuery] = useState('');
  const [pendingMass, setPendingMass] = useState<number>(100);
  const [decomposerOpenLocal, setDecomposerOpenLocal] = useState(false);
  const [savedPickerOpen, setSavedPickerOpen] = useState(false);
  const [searchSource, setSearchSource] = useState<SourceChoice>('both');
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [selectedFoodIds, setSelectedFoodIds] = useState<Set<number>>(() => new Set());

  const decomposerOpen = decomposerOpenProp ?? decomposerOpenLocal;
  const setDecomposerOpen = onDecomposerOpenChange ?? setDecomposerOpenLocal;

  const savedDays: SavedRecallDay[] = useMemo(
    () => savedPickerOpen ? listSavedDays() : [],
    [savedPickerOpen],
  );

  const existingFoodIds = useMemo(() => {
    const list = loadActiveFoodList();
    return new Set(list?.ingredients.map(i => i.food_id) ?? []);
  }, [query, searchResults]);

  const searchFoods = useCallback(async (q: string) => {
    const trimmed = q.trim();
    if (trimmed.length < 2) {
      setSearchResults(null);
      setSelectedFoodIds(new Set());
      return;
    }
    setSearchLoading(true);
    try {
      const results = await CNFApiService.searchFoods(trimmed, 20, 0, searchSource);
      setSearchResults(results);
      setSelectedFoodIds(new Set());
    } catch {
      setSearchResults(null);
    } finally {
      setSearchLoading(false);
    }
  }, [searchSource]);

  useEffect(() => {
    const t = window.setTimeout(() => {
      if (query.trim().length >= 2) searchFoods(query);
      else {
        setSearchResults(null);
        setSelectedFoodIds(new Set());
      }
    }, 300);
    return () => window.clearTimeout(t);
  }, [query, searchFoods]);

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
    setSearchResults(null);
    setSelectedFoodIds(new Set());
  }

  function addSelectedFoods(): void {
    if (!searchResults || selectedFoodIds.size === 0) return;
    let current = loadActiveFoodList();
    for (const food of searchResults.results) {
      if (!selectedFoodIds.has(food.FoodID)) continue;
      current = mergeIngredient(current, {
        food_id: food.FoodID,
        food_description: food.FoodDescription,
        mass_g: pendingMass,
      }, userType);
    }
    if (current) saveActiveFoodList(current);
    setQuery('');
    setSearchResults(null);
    setSelectedFoodIds(new Set());
  }

  function toggleSelection(foodId: number): void {
    setSelectedFoodIds(prev => {
      const next = new Set(prev);
      if (next.has(foodId)) next.delete(foodId);
      else next.add(foodId);
      return next;
    });
  }

  function selectAllVisible(): void {
    if (!searchResults) return;
    const available = searchResults.results.filter(f => !existingFoodIds.has(f.FoodID));
    const allSelected = available.every(f => selectedFoodIds.has(f.FoodID));
    if (allSelected) {
      setSelectedFoodIds(new Set());
    } else {
      setSelectedFoodIds(new Set(available.map(f => f.FoodID)));
    }
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
            Search foods to add
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
            Grams (each)
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
        <div className="border-t pt-2 space-y-2">
          <SourceFilter source={searchSource} onChange={setSearchSource} accent="blue" />
          <p className="text-[11px] text-gray-600">Pick a match (or use AI ranker):</p>
          <AIEnhancedSearch
            query={query}
            userType={userType}
            accent="blue"
            source={searchSource}
            onSelect={addOneFood}
          />

          {searchLoading && (
            <p className="text-xs text-gray-500 py-2">Searching…</p>
          )}

          {searchResults && searchResults.results.length > 0 && (
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-3 p-2 bg-gray-50 rounded-md text-xs">
                <button type="button" onClick={selectAllVisible} className="text-blue-700 hover:underline">
                  Select all
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedFoodIds(new Set())}
                  className="text-gray-600 hover:underline"
                >
                  Clear
                </button>
                <span className="text-gray-600">{selectedFoodIds.size} selected</span>
                {selectedFoodIds.size > 0 && (
                  <button
                    type="button"
                    onClick={addSelectedFoods}
                    className="ml-auto inline-flex items-center gap-1 px-2 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    <Plus className="h-3 w-3" aria-hidden="true" />
                    Add selected ({selectedFoodIds.size})
                  </button>
                )}
              </div>
              <ul className="max-h-48 overflow-y-auto space-y-1 border rounded-md divide-y">
                {searchResults.results.map(food => {
                  const alreadyInList = existingFoodIds.has(food.FoodID);
                  const isSelected = selectedFoodIds.has(food.FoodID);
                  return (
                    <li key={food.FoodID}>
                      <label
                        className={`flex items-center gap-2 px-2 py-1.5 text-xs cursor-pointer hover:bg-gray-50 ${
                          alreadyInList ? 'opacity-60' : ''
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          disabled={alreadyInList}
                          onChange={() => toggleSelection(food.FoodID)}
                          className="rounded border-gray-300"
                        />
                        <span className="flex-1 min-w-0">
                          <span className="font-medium text-gray-900">{food.FoodDescription}</span>
                        </span>
                        {alreadyInList && (
                          <span className="text-[10px] text-gray-500 shrink-0">In list</span>
                        )}
                        {isSelected && !alreadyInList && (
                          <Check className="h-3.5 w-3.5 text-blue-600 shrink-0" aria-hidden="true" />
                        )}
                      </label>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
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
