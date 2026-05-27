'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { BeakerIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { CNFApiService, type Food, type Nutrient } from '@/lib/api';
import { SourceBadge } from '@/components/shared/SourceBadge';
import type { UserType } from '@/components/shared/AudienceToggle';
import { NUTRIENT_DISCOVER_PRESETS } from '@/lib/cnfNutrientDiscover';

interface NutrientDiscoverPanelProps {
  userType: UserType;
  resolveGroupName: (groupId: number, fallback?: string) => string;
  /** Embed in compare modal: show Add buttons and call this. */
  onAddFood?: (foodId: number) => void;
  /** Food IDs already in the comparison list. */
  excludeFoodIds?: number[];
  /** Tighter layout for modal embedding. */
  compact?: boolean;
  /** Full-page discover: open profile drawer. */
  onQuickView?: (food: Food) => void;
}

export function NutrientDiscoverPanel({
  userType,
  resolveGroupName,
  onAddFood,
  excludeFoodIds = [],
  compact = false,
  onQuickView,
}: NutrientDiscoverPanelProps) {
  const [nutrients, setNutrients] = useState<Nutrient[]>([]);
  const [nutrientQuery, setNutrientQuery] = useState('');
  const [selectedNutrientId, setSelectedNutrientId] = useState<number | null>(null);
  const [minValue, setMinValue] = useState('');
  const [maxValue, setMaxValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Food[]>([]);
  const [criteriaLabel, setCriteriaLabel] = useState('');

  const excludeSet = useMemo(() => new Set(excludeFoodIds), [excludeFoodIds]);

  useEffect(() => {
    CNFApiService.getNutrients()
      .then(setNutrients)
      .catch(() => toast.error('Failed to load nutrient list'));
  }, []);

  const filteredNutrients = useMemo(() => {
    const q = nutrientQuery.trim().toLowerCase();
    if (!q) return nutrients.slice(0, compact ? 40 : 80);
    return nutrients.filter(n => n.NutrientName.toLowerCase().includes(q)).slice(0, compact ? 40 : 80);
  }, [nutrients, nutrientQuery, compact]);

  const selectedNutrient = nutrients.find(n => n.NutrientID === selectedNutrientId);

  const runSearch = useCallback(async (
    nutrientId: number,
    min?: number,
    max?: number,
    label?: string,
  ) => {
    setLoading(true);
    setSelectedNutrientId(nutrientId);
    try {
      const data = await CNFApiService.searchFoodsByNutrient(nutrientId, min, max, 50);
      setResults(data.foods);
      const nutrientName = nutrients.find(n => n.NutrientID === nutrientId)?.NutrientName ?? `Nutrient ${nutrientId}`;
      const parts = [nutrientName];
      if (min != null) parts.push(`≥ ${min}`);
      if (max != null) parts.push(`≤ ${max}`);
      setCriteriaLabel(label ?? parts.join(' '));
    } catch {
      toast.error('Nutrient search failed');
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [nutrients]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedNutrientId) {
      toast.error('Select a nutrient');
      return;
    }
    const min = minValue.trim() ? parseFloat(minValue) : undefined;
    const max = maxValue.trim() ? parseFloat(maxValue) : undefined;
    if (minValue.trim() && !Number.isFinite(min!)) {
      toast.error('Invalid minimum value');
      return;
    }
    if (maxValue.trim() && !Number.isFinite(max!)) {
      toast.error('Invalid maximum value');
      return;
    }
    runSearch(selectedNutrientId, min, max);
  };

  const applyPreset = (preset: (typeof NUTRIENT_DISCOVER_PRESETS)[number]) => {
    setMinValue(preset.minValue != null ? String(preset.minValue) : '');
    setMaxValue(preset.maxValue != null ? String(preset.maxValue) : '');
    runSearch(preset.nutrientId, preset.minValue, preset.maxValue, preset.label);
  };

  const selectSize = compact ? Math.min(4, Math.max(3, filteredNutrients.length)) : Math.min(6, Math.max(3, filteredNutrients.length));

  return (
    <div className={compact ? 'space-y-3' : 'space-y-4'}>
      <div>
        <h3 className={`font-semibold text-gray-900 flex items-center gap-2 ${compact ? 'text-xs mb-2' : 'text-sm mb-3'}`}>
          <BeakerIcon className="w-4 h-4 text-primary-600" aria-hidden="true" />
          Quick presets
        </h3>
        <div className="flex flex-wrap gap-2">
          {NUTRIENT_DISCOVER_PRESETS.map(p => (
            <button
              key={p.label}
              type="button"
              onClick={() => applyPreset(p)}
              className="px-3 py-1.5 text-xs font-medium rounded-full bg-gray-100 text-gray-800 hover:bg-primary-100 hover:text-primary-800 transition"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label htmlFor={compact ? 'modal-nutrient-search' : 'nutrient-search'} className="block text-sm font-medium text-gray-700 mb-1">
            Filter nutrients
          </label>
          <input
            id={compact ? 'modal-nutrient-search' : 'nutrient-search'}
            type="text"
            placeholder="e.g. iron, sodium, fibre…"
            value={nutrientQuery}
            onChange={(e) => setNutrientQuery(e.target.value)}
            className="w-full mb-2 px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
          <label htmlFor={compact ? 'modal-nutrient-select' : 'nutrient-select'} className="block text-sm font-medium text-gray-700 mb-1">
            Select from list
          </label>
          <select
            id={compact ? 'modal-nutrient-select' : 'nutrient-select'}
            value={selectedNutrientId ?? ''}
            onChange={(e) => setSelectedNutrientId(e.target.value ? Number(e.target.value) : null)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            size={selectSize}
          >
            <option value="">Select a nutrient…</option>
            {filteredNutrients.map(n => (
              <option key={n.NutrientID} value={n.NutrientID}>
                {n.NutrientName}{n.NutrientUnit ? ` (${n.NutrientUnit})` : ''}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor={compact ? 'modal-min-val' : 'min-val'} className="block text-xs font-medium text-gray-700 mb-1">
              Min (per 100 g)
            </label>
            <input
              id={compact ? 'modal-min-val' : 'min-val'}
              type="number"
              step="any"
              value={minValue}
              onChange={(e) => setMinValue(e.target.value)}
              placeholder="Optional"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
          <div>
            <label htmlFor={compact ? 'modal-max-val' : 'max-val'} className="block text-xs font-medium text-gray-700 mb-1">
              Max (per 100 g)
            </label>
            <input
              id={compact ? 'modal-max-val' : 'max-val'}
              type="number"
              step="any"
              value={maxValue}
              onChange={(e) => setMaxValue(e.target.value)}
              placeholder="Optional"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !selectedNutrientId}
          className="btn-primary inline-flex items-center text-sm disabled:opacity-50"
        >
          <MagnifyingGlassIcon className="w-4 h-4 mr-2" aria-hidden="true" />
          {loading ? 'Searching…' : 'Find foods'}
        </button>
      </form>

      {criteriaLabel && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="px-3 py-2 bg-gray-50 border-b border-gray-100">
            <p className="text-xs text-gray-600">
              {results.length} foods · {criteriaLabel}
            </p>
          </div>
          {results.length === 0 ? (
            <p className="p-4 text-center text-sm text-gray-500">No foods matched.</p>
          ) : (
            <ul className={`divide-y divide-gray-100 ${compact ? 'max-h-52' : 'max-h-96'} overflow-y-auto`}>
              {results.map(food => {
                const isAdded = excludeSet.has(food.FoodID);
                return (
                  <li key={food.FoodID} className={`px-3 py-2.5 ${isAdded ? 'opacity-50 bg-gray-50' : 'hover:bg-gray-50'}`}>
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        {onAddFood ? (
                          <span className="text-sm font-medium text-gray-900">{food.FoodDescription}</span>
                        ) : (
                          <Link href={`/cnf/foods/${food.FoodID}`} className="text-sm font-medium text-gray-900 hover:text-primary-700">
                            {food.FoodDescription}
                          </Link>
                        )}
                        <div className="mt-0.5 flex flex-wrap items-center gap-1.5 text-xs text-gray-500">
                          <SourceBadge foodId={food.FoodID} userType={userType} />
                          <span>{resolveGroupName(food.FoodGroupID, food.FoodGroupName)}</span>
                          {food.queried_nutrient_value != null && (
                            <span className="font-medium text-emerald-700">
                              {food.queried_nutrient_value.toFixed(2)} / 100 g
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex shrink-0 gap-1.5">
                        {onQuickView && (
                          <button
                            type="button"
                            onClick={() => onQuickView(food)}
                            className="text-xs font-medium text-blue-700 hover:text-blue-900"
                          >
                            View
                          </button>
                        )}
                        {onAddFood ? (
                          <button
                            type="button"
                            onClick={() => onAddFood(food.FoodID)}
                            disabled={isAdded}
                            className="btn-primary text-xs py-1 px-2.5 disabled:opacity-50"
                          >
                            {isAdded ? 'Added' : 'Add'}
                          </button>
                        ) : (
                          <Link href={`/cnf/foods/${food.FoodID}`} className="text-xs text-gray-500 hover:text-gray-700">
                            Open →
                          </Link>
                        )}
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
