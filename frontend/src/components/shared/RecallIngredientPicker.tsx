/**
 * Add CNF foods to a 24-h recall occasion or day list — basic search + AI find.
 */
'use client';

import { useEffect, useState } from 'react';
import { MagnifyingGlassIcon, TrashIcon } from '@heroicons/react/24/outline';
import { CNFApiService } from '@/lib/api';
import { AIEnhancedSearch } from '@/components/shared/AIEnhancedSearch';
import { SourceBadge } from '@/components/shared/SourceBadge';
import type { UserType } from '@/components/shared/AudienceToggle';
import type { SourceChoice } from '@/components/shared/SourceFilter';
import type { RecallDirectIngredient } from '@/lib/recallDirectFood';
import { mergeRecallIngredients } from '@/lib/recallDirectFood';

interface RecallIngredientPickerProps {
  userType: UserType;
  source: SourceChoice;
  ingredients: RecallDirectIngredient[];
  onChange: (ingredients: RecallDirectIngredient[]) => void;
  /** Default grams when picking a food without a preset mass. */
  defaultMassG?: number;
  searchPlaceholder?: string;
  emptyHint?: string;
}

export function RecallIngredientPicker({
  userType,
  source,
  ingredients,
  onChange,
  defaultMassG = 100,
  searchPlaceholder = 'Search for a food…',
  emptyHint = 'Search by name or use Find with AI, then set grams for each item.',
}: RecallIngredientPickerProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Array<{ FoodID: number; FoodDescription: string }>>([]);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      setShowResults(false);
      return;
    }
    const t = setTimeout(async () => {
      setLoading(true);
      try {
        let searchResult;
        try {
          searchResult = await CNFApiService.searchFoodsEnhanced({
            query: query.trim(),
            limit: 40,
            source,
          });
        } catch {
          searchResult = await CNFApiService.searchFoods(query.trim(), 40, 0, source);
        }
        setResults(searchResult.results || []);
        setShowResults(true);
      } catch {
        setResults([]);
        setShowResults(false);
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(t);
  }, [query, source]);

  function addFood(food: {
    food_id: number;
    food_description: string;
    food_group?: string;
    mass_g?: number;
  }) {
    const next: RecallDirectIngredient = {
      food_id: food.food_id,
      food_description: food.food_description,
      food_group: food.food_group,
      mass_g: food.mass_g ?? defaultMassG,
    };
    onChange(mergeRecallIngredients([...ingredients, next]));
    setQuery('');
    setShowResults(false);
  }

  function updateMass(foodId: number, mass: number) {
    onChange(ingredients.map(i =>
      i.food_id === foodId ? { ...i, mass_g: mass } : i,
    ));
  }

  function removeFood(foodId: number) {
    onChange(ingredients.filter(i => i.food_id !== foodId));
  }

  return (
    <div className="space-y-3">
      <div className="relative">
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Add ingredients
        </label>
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder={searchPlaceholder}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm pl-9"
            aria-label="Search foods to add"
          />
          <MagnifyingGlassIcon className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" aria-hidden="true" />
        </div>
        <div className="mt-2">
          {query.trim() && (
            <AIEnhancedSearch
              query={query}
              userType={userType}
              accent="blue"
              source={source}
              onSelect={picked => addFood({
                food_id: picked.food_id,
                food_description: picked.food_description,
                food_group: picked.food_group,
              })}
            />
          )}
        </div>
        {showResults && (
          <div className="absolute z-20 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-48 overflow-y-auto">
            {loading ? (
              <div className="p-3 text-center text-sm text-gray-500">Searching…</div>
            ) : results.length > 0 ? (
              results.map(item => (
                <button
                  key={item.FoodID}
                  type="button"
                  onClick={() => addFood({
                    food_id: item.FoodID,
                    food_description: item.FoodDescription,
                  })}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                >
                  <div className="font-medium text-gray-900 truncate">{item.FoodDescription}</div>
                </button>
              ))
            ) : (
              <div className="p-3 text-center text-sm text-gray-500">No foods found</div>
            )}
          </div>
        )}
      </div>

      {ingredients.length === 0 ? (
        <p className="text-xs text-gray-500">{emptyHint}</p>
      ) : (
        <ul className="space-y-2">
          {ingredients.map(item => (
            <li
              key={item.food_id}
              className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg text-sm border border-gray-100"
            >
              <span className="flex-1 min-w-0">
                <span className="font-medium text-gray-900 truncate block">{item.food_description}</span>
                <span className="text-[10px] text-gray-500 flex items-center gap-1">
                  FoodID {item.food_id}
                  <SourceBadge foodId={item.food_id} userType={userType} />
                </span>
              </span>
              <label className="flex items-center gap-1 text-xs text-gray-600 shrink-0">
                <span>g</span>
                <input
                  type="number"
                  min={0.1}
                  step={1}
                  value={item.mass_g}
                  onChange={e => updateMass(item.food_id, parseFloat(e.target.value) || 0)}
                  className="w-16 border border-gray-300 rounded px-1.5 py-0.5 text-sm tabular-nums"
                  aria-label={`Mass in grams for ${item.food_description}`}
                />
              </label>
              <button
                type="button"
                onClick={() => removeFood(item.food_id)}
                className="p-1 text-gray-400 hover:text-red-600"
                aria-label={`Remove ${item.food_description}`}
              >
                <TrashIcon className="w-4 h-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
