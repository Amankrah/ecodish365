/**
 * ScorerFoodInput — shared food-picker for calculate / compare scorer pages.
 * Bundles FoodListPanel, recall handoff, AI search, source filter, filters,
 * and optional recipe decomposer so compare pages stay in sync with calculate.
 */
'use client';

import { useCallback, useEffect, useState, type ReactNode } from 'react';
import {
  PlusIcon,
  TrashIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import { CNFApiService, type FilterOptions, type SearchResult } from '@/lib/api';
import { AIEnhancedSearch } from '@/components/shared/AIEnhancedSearch';
import { RecipeDecomposerModal } from '@/components/shared/RecipeDecomposerModal';
import { SourceFilter, type SourceChoice } from '@/components/shared/SourceFilter';
import { FoodListPanel, type ScoreTargetId } from '@/components/shared/FoodListPanel';
import { useRecall24hReceiver } from '@/components/shared/useRecall24hReceiver';
import type { UserType } from '@/components/shared/AudienceToggle';

export type ScorerFoodAccent = 'amber' | 'green' | 'purple' | 'blue';

export interface ScorerFoodSlot {
  id: string;
  food_id: number;
  food_name: string;
  serving_size?: number;
}

export interface ScorerFoodPoolItem {
  food_id: number;
  food_name: string;
  amount_g: number;
}

interface SearchState {
  query: string;
  results: SearchResult['results'];
  isLoading: boolean;
  showResults: boolean;
}

function nextId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

interface BaseProps {
  target: ScoreTargetId;
  accent: ScorerFoodAccent;
  userType: UserType;
  onUserTypeChange?: (u: UserType) => void;
  showDecomposer?: boolean;
  showRecallLink?: boolean;
  /** Content rendered below the food list (e.g. compare settings). */
  children?: ReactNode;
}

interface SlotsProps extends BaseProps {
  mode: 'slots';
  slots: ScorerFoodSlot[];
  onSlotsChange: (slots: ScorerFoodSlot[]) => void;
  minSlots?: number;
  maxSlots?: number;
  initialEmptySlots?: number;
  showServingPerSlot?: boolean;
  defaultServingG?: number;
}

interface PoolProps extends BaseProps {
  mode: 'pool';
  pool: ScorerFoodPoolItem[];
  onPoolChange: (pool: ScorerFoodPoolItem[]) => void;
  poolSearchLabel?: string;
  dedupePool?: boolean;
}

export type ScorerFoodInputProps = SlotsProps | PoolProps;

export function ScorerFoodInput(props: ScorerFoodInputProps): JSX.Element {
  const {
    target,
    accent,
    userType,
    onUserTypeChange,
    showDecomposer = true,
    showRecallLink = true,
    children,
  } = props;

  const [filters, setFilters] = useState<FilterOptions | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedMethod, setSelectedMethod] = useState('');
  const [sourceFilter, setSourceFilter] = useState<SourceChoice>('both');
  const [search, setSearch] = useState<SearchState>({
    query: '',
    results: [],
    isLoading: false,
    showResults: false,
  });
  const [activeSearch, setActiveSearch] = useState<string>('pool');
  const [recipeModalOpen, setRecipeModalOpen] = useState(false);

  useEffect(() => {
    CNFApiService.getFoodFilters()
      .then(setFilters)
      .catch(() => { /* non-fatal */ });
  }, []);

  useRecall24hReceiver({
    target,
    onIngredients: (ingredients, meta) => {
      onUserTypeChange?.(meta.user_type);
      if (props.mode === 'slots') {
        props.onSlotsChange(ingredients.map((i, idx) => ({
          id: String(idx + 1),
          food_id: i.food_id,
          food_name: i.food_description,
          serving_size: i.mass_g,
        })));
      } else {
        props.onPoolChange(ingredients.map(i => ({
          food_id: i.food_id,
          food_name: i.food_description,
          amount_g: i.mass_g,
        })));
      }
    },
  });

  useEffect(() => {
    if (search.query.length < 2) {
      setSearch(prev => ({ ...prev, results: [], showResults: false }));
      return;
    }
    const t = setTimeout(async () => {
      setSearch(prev => ({ ...prev, isLoading: true }));
      try {
        let searchResult;
        try {
          searchResult = await CNFApiService.searchFoodsEnhanced({
            query: search.query,
            limit: 50,
            category: selectedCategory || undefined,
            method: selectedMethod || undefined,
            source: sourceFilter,
          });
        } catch {
          searchResult = await CNFApiService.searchFoods(
            search.query, 50, 0, sourceFilter,
          );
        }
        setSearch(prev => ({
          ...prev,
          results: searchResult.results || [],
          isLoading: false,
          showResults: true,
        }));
      } catch {
        setSearch(prev => ({ ...prev, isLoading: false, showResults: false }));
      }
    }, 300);
    return () => clearTimeout(t);
  }, [search.query, selectedCategory, selectedMethod, sourceFilter]);

  const pickFromSearch = useCallback((
    food: { food_id: number; food_description: string; mass_g?: number },
    slotId?: string,
  ) => {
    if (props.mode === 'slots') {
      const sid = slotId ?? activeSearch;
      props.onSlotsChange(props.slots.map(s =>
        s.id === sid
          ? {
              ...s,
              food_id: food.food_id,
              food_name: food.food_description,
              serving_size: food.mass_g ?? s.serving_size ?? props.defaultServingG ?? 100,
            }
          : s,
      ));
    } else {
      const dedupe = props.dedupePool !== false;
      if (dedupe && props.pool.some(p => p.food_id === food.food_id)) {
        setSearch(prev => ({ ...prev, query: '', showResults: false }));
        return;
      }
      props.onPoolChange([
        ...props.pool,
        {
          food_id: food.food_id,
          food_name: food.food_description,
          amount_g: food.mass_g ?? 100,
        },
      ]);
    }
    setSearch(prev => ({ ...prev, query: '', showResults: false }));
    setActiveSearch(props.mode === 'pool' ? 'pool' : '');
  }, [activeSearch, props]);

  const handleDecomposeApply = useCallback((ingredients: Array<{
    food_id: number;
    food_description: string;
    mass_g: number;
  }>) => {
    if (props.mode === 'slots') {
      const filled = props.slots.filter(s => s.food_id > 0);
      const additions: ScorerFoodSlot[] = ingredients
        .filter(i => !filled.some(f => f.food_id === i.food_id))
        .map(i => ({
          id: nextId(),
          food_id: i.food_id,
          food_name: i.food_description,
          serving_size: i.mass_g,
        }));
      const max = props.maxSlots ?? 20;
      props.onSlotsChange([...filled, ...additions].slice(0, max));
    } else {
      const dedupe = props.dedupePool !== false;
      const next = [...props.pool];
      for (const i of ingredients) {
        if (dedupe && next.some(p => p.food_id === i.food_id)) continue;
        next.push({
          food_id: i.food_id,
          food_name: i.food_description,
          amount_g: i.mass_g,
        });
      }
      props.onPoolChange(next);
    }
  }, [props]);

  const syncFromFoodList = useCallback((list: Parameters<
    NonNullable<React.ComponentProps<typeof FoodListPanel>['onChange']>
  >[0]) => {
    if (!list) {
      if (props.mode === 'slots') {
        props.onSlotsChange([]);
      } else {
        props.onPoolChange([]);
      }
      return;
    }
    if (props.mode === 'slots') {
      props.onSlotsChange(list.ingredients.map((i, idx) => ({
        id: String(idx + 1),
        food_id: i.food_id,
        food_name: i.food_description,
        serving_size: i.mass_g,
      })));
    } else {
      props.onPoolChange(list.ingredients.map(i => ({
        food_id: i.food_id,
        food_name: i.food_description,
        amount_g: i.mass_g,
      })));
    }
  }, [props]);

  const filterBlock = filters ? (
    <div className="mb-4 space-y-3 border-b pb-4">
      <h3 className="text-sm font-medium text-gray-700">Search filters</h3>
      <div className="grid grid-cols-1 gap-3">
        <select
          value={selectedCategory}
          onChange={e => setSelectedCategory(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          aria-label="Food category filter"
        >
          <option value="">All categories</option>
          {filters.categories.map(c => (
            <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
          ))}
        </select>
        <select
          value={selectedMethod}
          onChange={e => setSelectedMethod(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          aria-label="Cooking method filter"
        >
          <option value="">All methods</option>
          {filters.methods.map(m => (
            <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>
          ))}
        </select>
      </div>
      {(selectedCategory || selectedMethod) && (
        <button
          type="button"
          onClick={() => { setSelectedCategory(''); setSelectedMethod(''); }}
          className="text-xs text-blue-600 hover:text-blue-800"
        >
          Clear filters
        </button>
      )}
    </div>
  ) : null;

  const searchExtras = (slotKey: string) => (
    <>
      <SourceFilter source={sourceFilter} onChange={setSourceFilter} accent={accent} />
      {search.query.trim() && (
        <AIEnhancedSearch
          query={search.query}
          userType={userType}
          accent={accent}
          source={sourceFilter}
          onSelect={picked => pickFromSearch({
            food_id: picked.food_id,
            food_description: picked.food_description,
          }, slotKey === 'pool' ? undefined : slotKey)}
        />
      )}
    </>
  );

  const searchResultsDropdown = (slotKey: string) => (
    activeSearch === slotKey && search.showResults ? (
      <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-48 overflow-y-auto">
        {search.isLoading ? (
          <div className="p-3 text-center text-sm text-gray-500">Searching…</div>
        ) : search.results.length > 0 ? (
          search.results.map(item => (
            <button
              key={item.FoodID}
              type="button"
              onClick={() => pickFromSearch({
                food_id: item.FoodID,
                food_description: item.FoodDescription,
              }, slotKey === 'pool' ? undefined : slotKey)}
              className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
            >
              <div className="font-medium text-gray-900 truncate">{item.FoodDescription}</div>
            </button>
          ))
        ) : (
          <div className="p-3 text-center text-sm text-gray-500">No foods found</div>
        )}
      </div>
    ) : null
  );

  return (
    <div className="space-y-4">
      <FoodListPanel currentTarget={target} onChange={syncFromFoodList} />

      {filterBlock}

      {props.mode === 'pool' ? (
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            {props.poolSearchLabel ?? 'Search foods to add'}
          </label>
          <div className="relative">
            <input
              type="text"
              value={activeSearch === 'pool' ? search.query : ''}
              onChange={e => {
                setActiveSearch('pool');
                setSearch(prev => ({ ...prev, query: e.target.value }));
              }}
              placeholder="Search for a food…"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm pl-10"
            />
            <MagnifyingGlassIcon className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
            <div className="mt-2 space-y-2">{searchExtras('pool')}</div>
            {searchResultsDropdown('pool')}
          </div>

          <div className="mt-3 space-y-2">
            {props.pool.map(item => (
              <div key={item.food_id} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg text-sm">
                <span className="flex-1 min-w-0 truncate font-medium">{item.food_name}</span>
                <label className="flex items-center gap-1 text-xs text-gray-600">
                  <span>g</span>
                  <input
                    type="number"
                    min={0.1}
                    step={1}
                    value={item.amount_g}
                    onChange={e => props.onPoolChange(props.pool.map(p =>
                      p.food_id === item.food_id
                        ? { ...p, amount_g: Math.max(0.1, parseFloat(e.target.value) || 0.1) }
                        : p,
                    ))}
                    className="w-20 px-2 py-1 border border-gray-300 rounded text-xs"
                    aria-label={`Grams for ${item.food_name}`}
                  />
                </label>
                <button
                  type="button"
                  onClick={() => props.onPoolChange(props.pool.filter(p => p.food_id !== item.food_id))}
                  className="text-red-500 hover:text-red-700"
                  aria-label={`Remove ${item.food_name}`}
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {props.slots.map((slot, index) => (
              <div key={slot.id} className="border border-gray-200 rounded-md p-3">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">Food {index + 1}</span>
                  {props.slots.length > (props.minSlots ?? 2) && (
                    <button
                      type="button"
                      onClick={() => props.onSlotsChange(props.slots.filter(s => s.id !== slot.id))}
                      className="text-red-500 hover:text-red-700"
                      aria-label={`Remove food ${index + 1}`}
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  )}
                </div>
                <div className="relative">
                  <input
                    type="text"
                    value={activeSearch === slot.id ? search.query : slot.food_name}
                    onChange={e => {
                      setActiveSearch(slot.id);
                      setSearch(prev => ({ ...prev, query: e.target.value }));
                    }}
                    placeholder="Search for a food…"
                    className="w-full border border-gray-300 rounded-md pl-10 pr-3 py-2 text-sm"
                  />
                  <MagnifyingGlassIcon className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                  {activeSearch === slot.id && (
                    <div className="mt-2 space-y-2">{searchExtras(slot.id)}</div>
                  )}
                  {searchResultsDropdown(slot.id)}
                </div>
                {props.showServingPerSlot && (
                  <div className="mt-2">
                    <label className="text-xs text-gray-600">Serving (g)</label>
                    <input
                      type="number"
                      min={1}
                      max={2000}
                      value={slot.serving_size ?? props.defaultServingG ?? 100}
                      onChange={e => props.onSlotsChange(props.slots.map(s =>
                        s.id === slot.id ? { ...s, serving_size: Number(e.target.value) } : s,
                      ))}
                      className="w-full mt-1 border border-gray-300 rounded-md px-2 py-1 text-sm"
                      aria-label={`Serving size for food ${index + 1}`}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={() => {
              const max = props.maxSlots ?? 20;
              if (props.slots.length >= max) {
                alert(`Maximum ${max} foods.`);
                return;
              }
              props.onSlotsChange([
                ...props.slots,
                {
                  id: nextId(),
                  food_id: 0,
                  food_name: '',
                  serving_size: props.defaultServingG ?? 100,
                },
              ]);
            }}
            className="w-full flex items-center justify-center px-3 py-2 border border-dashed border-gray-300 rounded-md text-sm text-gray-600 hover:border-gray-400"
          >
            <PlusIcon className="w-4 h-4 mr-1" />
            Add another food
          </button>
        </>
      )}

      {showDecomposer && (
        <button
          type="button"
          onClick={() => setRecipeModalOpen(true)}
          className="w-full text-sm text-gray-700 hover:text-gray-900 hover:underline text-left"
        >
          🍳 Break down a homemade dish
        </button>
      )}

      {showRecallLink && (
        <a
          href={`/recall-24h?then=${target}`}
          className="block text-sm text-gray-700 hover:text-gray-900 hover:underline"
        >
          🍽️ Log a full food diary day instead
        </a>
      )}

      {children}

      <RecipeDecomposerModal
        open={recipeModalOpen}
        onClose={() => setRecipeModalOpen(false)}
        userType={userType}
        accent={accent}
        initialSource={sourceFilter}
        onApply={handleDecomposeApply}
      />
    </div>
  );
}

/** Ensure at least `min` slot rows exist. */
export function ensureMinSlots(
  slots: ScorerFoodSlot[],
  min: number,
  defaultServingG = 100,
): ScorerFoodSlot[] {
  if (slots.length >= min) return slots;
  const out = [...slots];
  while (out.length < min) {
    out.push({
      id: nextId(),
      food_id: 0,
      food_name: '',
      serving_size: defaultServingG,
    });
  }
  return out;
}
