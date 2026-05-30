'use client';

import React, { useMemo, useState } from 'react';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import type { Food, FoodComparison, Nutrient } from '@/lib/api';
import type { UserType } from '@/components/shared/AudienceToggle';
import { SourceBadge } from '@/components/shared/SourceBadge';
import {
  cellPercentDV,
  COMPARE_RATIO_PRESETS,
  computeRatio,
  findComparisonNutrientEntry,
  getNutrientCell,
  nutrientKeysForCategory,
  type CompareBasis,
} from '@/lib/cnfCompareHelpers';

interface CompareNutrientTableProps {
  foods: Food[];
  comparison: FoodComparison;
  userType: UserType;
  basis: CompareBasis;
  showDelta: boolean;
  diffOnly: boolean;
  transposed: boolean;
  customNutrientIds: number[];
  nutrients: Nutrient[];
  onAddCustomNutrient: (nutrientId: number) => void;
}

export function CompareNutrientTable({
  foods,
  comparison,
  userType,
  basis,
  showDelta,
  diffOnly,
  transposed,
  customNutrientIds,
  nutrients,
  onAddCustomNutrient,
}: CompareNutrientTableProps) {
  const [selectedCategory, setSelectedCategory] = useState('Macronutrients');
  const [pickerId, setPickerId] = useState<number | ''>('');

  const categoryOptions = useMemo(() => {
    const base = ['Energy', 'Macronutrients', 'Minerals', 'Vitamins', 'Fatty Acids'];
    if (userType === 'researcher') base.push('Lens highlights (HSR/FCS)');
    if (customNutrientIds.length) base.push('Custom nutrients');
    return base;
  }, [userType, customNutrientIds.length]);

  const customKeys = useMemo(() => {
    const keys: string[] = [];
    for (const nid of customNutrientIds) {
      const hit = Object.entries(comparison.nutrients).find(([, v]) => v.nutrient_id === nid);
      if (hit) keys.push(hit[0]);
    }
    return keys;
  }, [comparison, customNutrientIds]);

  const rowKeys = useMemo(() => {
    let keys = selectedCategory === 'Custom nutrients'
      ? customKeys
      : nutrientKeysForCategory(selectedCategory, comparison);
    keys = keys.filter(k =>
      foods.some(f => getNutrientCell(comparison, f.FoodID, k)?.value != null),
    );
    if (diffOnly) {
      keys = keys.filter(k => {
        const vals = foods
          .map(f => getNutrientCell(comparison, f.FoodID, k)?.value)
          .filter((v): v is number => v != null);
        if (vals.length < 2) return true;
        const first = vals[0];
        return vals.some(v => Math.abs(v - first) > 0.001);
      });
    }
    return keys;
  }, [selectedCategory, comparison, foods, diffOnly, customKeys]);

  const baselineId = foods[0]?.FoodID;

  const getHighest = (nutrientKey: string): number => {
    const vals = foods.map(f => getNutrientCell(comparison, f.FoodID, nutrientKey)?.value ?? 0);
    return Math.max(...vals);
  };

  const renderCell = (foodId: number, nutrientKey: string, maxValue: number) => {
    const cell = getNutrientCell(comparison, foodId, nutrientKey);
    const entry = findComparisonNutrientEntry(comparison, nutrientKey);
    const value = cell?.value ?? null;
    const unit = cell?.unit;
    const isHighest = value === maxValue && value != null && value > 0;
    const pdv = entry ? cellPercentDV(comparison, foodId, entry.nutrient_id) : null;
    const sourceTitle = cell?.nutrient_source
      ? `${cell.database?.toUpperCase() ?? 'CNF'} · ${cell.nutrient_source}`
      : undefined;

    let delta: number | null = null;
    if (showDelta && baselineId != null && foodId !== baselineId && value != null) {
      const base = getNutrientCell(comparison, baselineId, nutrientKey)?.value;
      if (base != null) delta = value - base;
    }

    if (value === null) {
      return (
        <div className="flex items-center text-gray-400 text-sm">
          <ExclamationTriangleIcon className="w-3.5 h-3.5 mr-1" />
          N/A
        </div>
      );
    }

    const pct = maxValue > 0 ? (value / maxValue) * 100 : 0;

    return (
      <div className="space-y-1 min-w-[7rem]" title={sourceTitle}>
        <div className="flex items-start justify-between gap-1">
          <span className={`text-sm font-medium tabular-nums ${isHighest ? 'text-green-700' : 'text-gray-900'}`}>
            {value.toFixed(2)}
            {unit && <span className="text-xs font-normal text-gray-500 ml-0.5">{unit}</span>}
          </span>
          {isHighest && <CheckCircleIcon className="w-4 h-4 text-green-500 shrink-0" />}
        </div>
        <div className="w-full bg-gray-200 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full ${isHighest ? 'bg-green-500' : 'bg-primary-500'}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        {pdv != null && (
          <div className="text-[11px] font-semibold text-emerald-700 tabular-nums">{Math.round(pdv)}% DV</div>
        )}
        {delta != null && (
          <div className={`text-[10px] tabular-nums ${delta >= 0 ? 'text-blue-700' : 'text-orange-700'}`}>
            {delta >= 0 ? '+' : ''}{delta.toFixed(2)} vs first
          </div>
        )}
        {userType === 'researcher' && cell?.database && (
          <SourceBadge source={cell.database === 'wafct' ? 'wafct' : 'cnf'} userType={userType} className="mt-0.5" />
        )}
      </div>
    );
  };

  const ratioRows = COMPARE_RATIO_PRESETS.map(preset => {
    const values = foods.map(f => ({
      foodId: f.FoodID,
      ratio: computeRatio(comparison, f.FoodID, preset.numerator_id, preset.denominator_id),
    }));
    const nums = values.map(v => v.ratio).filter((v): v is number => v != null);
    const best = preset.lowerIsBetter ? Math.min(...nums) : Math.max(...nums);
    return { preset, values, best: Number.isFinite(best) ? best : null };
  }).filter(r => r.values.some(v => v.ratio != null));

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
          <h2 className="text-lg font-semibold text-gray-900">Nutritional comparison</h2>
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <InformationCircleIcon className="w-4 h-4 shrink-0" />
            <span>
              {basis === 'per_100kcal' ? 'Values per 100 kcal' : 'Values per 100 g'}
              {' · '}%DV always from per-100 g amount
            </span>
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5 mb-3">
          {categoryOptions.map(cat => (
            <button
              key={cat}
              type="button"
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                selectedCategory === cat
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <div>
            <label htmlFor="compare-add-nutrient" className="block text-[10px] font-medium text-gray-600 mb-0.5">
              Add nutrient row
            </label>
            <select
              id="compare-add-nutrient"
              value={pickerId}
              onChange={e => setPickerId(e.target.value ? Number(e.target.value) : '')}
              className="text-xs px-2 py-1.5 border border-gray-300 rounded-lg bg-white min-w-[12rem]"
            >
              <option value="">Select nutrient…</option>
              {nutrients.map(n => (
                <option key={n.NutrientID} value={n.NutrientID}>{n.NutrientName}</option>
              ))}
            </select>
          </div>
          <button
            type="button"
            disabled={pickerId === ''}
            onClick={() => {
              if (pickerId !== '') {
                onAddCustomNutrient(Number(pickerId));
                setPickerId('');
                setSelectedCategory('Custom nutrients');
              }
            }}
            className="text-xs px-2.5 py-1.5 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50"
          >
            Add row
          </button>
        </div>
      </div>

      {rowKeys.length === 0 ? (
        <div className="px-6 py-10 text-center text-gray-500 text-sm">
          No nutrient rows match the current filters for this category.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px]">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-700 sticky left-0 bg-gray-50">
                  {transposed ? 'Food' : 'Nutrient'}
                </th>
                {(transposed ? rowKeys : foods.map(f => f.FoodDescription)).map((label, i) => (
                  <th
                    key={transposed ? String(label) : foods[i].FoodID}
                    className="text-left px-3 py-2 text-xs font-medium text-gray-700 max-w-[9rem]"
                  >
                    <span className="line-clamp-2" title={String(label)}>
                      {transposed
                        ? String(label).length > 28 ? `${String(label).slice(0, 28)}…` : label
                        : foods[i].FoodDescription.length > 28
                          ? `${foods[i].FoodDescription.slice(0, 28)}…`
                          : foods[i].FoodDescription}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            {transposed ? (
              <tbody className="divide-y divide-gray-100">
                {foods.map(food => (
                  <tr key={food.FoodID} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900 sticky left-0 bg-white min-w-[10rem]">
                      <div className="line-clamp-2" title={food.FoodDescription}>{food.FoodDescription}</div>
                    </td>
                    {rowKeys.map(key => {
                      const max = getHighest(key);
                      return (
                        <td key={key} className="px-3 py-3 align-top text-xs">
                          <div className="text-[10px] text-gray-500 mb-1 max-w-[8rem] truncate" title={key}>{key}</div>
                          {renderCell(food.FoodID, key, max)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            ) : (
              <tbody className="divide-y divide-gray-200">
                {rowKeys.map(nutrientKey => {
                  const entry = findComparisonNutrientEntry(comparison, nutrientKey);
                  const maxValue = getHighest(nutrientKey);
                  return (
                    <tr key={nutrientKey} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900 font-medium sticky left-0 bg-white">
                        <div>{entry?.key ?? nutrientKey}</div>
                        {entry?.unit && (
                          <div className="text-xs font-normal text-gray-500 mt-0.5">
                            {basis === 'per_100kcal' ? 'per 100 kcal' : 'per 100 g'} · {entry.unit}
                          </div>
                        )}
                      </td>
                      {foods.map(food => (
                        <td key={food.FoodID} className="px-3 py-3 align-top">
                          {renderCell(food.FoodID, nutrientKey, maxValue)}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            )}
          </table>
        </div>
      )}

      {ratioRows.length > 0 && (
        <div className="px-4 py-3 border-t border-gray-200 bg-slate-50">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-600 mb-2">Clinical ratios</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {ratioRows.map(({ preset, values, best }) => (
              <div key={preset.label} className="bg-white rounded-lg border border-gray-200 p-3">
                <p className="text-xs font-medium text-gray-800 mb-2">{preset.label}</p>
                <ul className="space-y-1">
                  {values.map(({ foodId, ratio }) => {
                    const food = foods.find(f => f.FoodID === foodId);
                    const isBest = ratio != null && best != null && ratio === best;
                    return (
                      <li key={foodId} className="flex justify-between text-xs gap-2">
                        <span className="text-gray-600 truncate" title={food?.FoodDescription}>
                          {food?.FoodDescription.slice(0, 24)}{(food?.FoodDescription.length ?? 0) > 24 ? '…' : ''}
                        </span>
                        <span className={`tabular-nums font-medium shrink-0 ${isBest ? 'text-green-700' : 'text-gray-900'}`}>
                          {ratio != null ? ratio.toFixed(3) : '—'}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="px-4 py-2 border-t border-gray-200 text-[11px] text-gray-500 leading-relaxed">
        <strong>% DV</strong> uses Health Canada Daily Values on the per-100 g amount (not affected by the
        per-100 kcal view). Energy has no %DV. Protein and total carbohydrate carry no Canadian %DV.
        {selectedCategory === 'Energy' && (
          <span className="text-gray-600"> Switch to Minerals or Vitamins to see %DV columns.</span>
        )}
      </div>
    </div>
  );
}
