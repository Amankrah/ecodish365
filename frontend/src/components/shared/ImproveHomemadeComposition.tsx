/**
 * ImproveHomemadeComposition — SUBST-1 Phase 1–2 homemade meal path.
 */
'use client';

import { Fragment, useMemo, useState } from 'react';
import { ChevronRight, Trash2 } from 'lucide-react';
import type { DecomposedIngredient, SubstitutionCompositionItem, SubstitutionSuggestion } from '@/lib/api';
import { fromRecallAggregated, saveActiveFoodList } from '@/lib/activeFoodList';
import { SubstitutionSuggestionsPanel } from './SubstitutionSuggestionsPanel';
import { FpedPanel } from './FpedPanel';
import { AIEnhancedSearch } from './AIEnhancedSearch';
import { SourceFilter, type SourceChoice } from './SourceFilter';

type UserType = 'individual' | 'researcher' | 'policy';

const SCORE_ROUTES = [
  { id: 'scorecard' as const, emoji: '✨', label: 'Full scorecard', path: '/scorecard', note: 'All six health and environment metrics' },
  { id: 'hefi' as const, emoji: '🥗', label: 'HEFI', path: '/hefi/calculate', note: 'Healthy Eating Food Index' },
  { id: 'fcs' as const, emoji: '🧭', label: 'FCS', path: '/fcs/calculate', note: 'Food Compass Score' },
];

interface Props {
  dishName: string;
  /** WAFCT recipe / cultural context hint; defaults to dishName. */
  substitutionDishName?: string;
  initialRows: Array<{
    food_id: number;
    food_description: string;
    mass_g: number;
    food_group?: string;
  }>;
  userType: UserType;
}

export function ImproveHomemadeComposition({
  dishName, substitutionDishName, initialRows, userType,
}: Props): JSX.Element {
  const [rows, setRows] = useState<DecomposedIngredient[]>(() =>
    initialRows.map((r, i) => ({
      label_name: r.food_description,
      position: i + 1,
      food_id: r.food_id,
      food_description: r.food_description,
      food_group: r.food_group ?? null,
      mass_g: r.mass_g,
      confidence: 0.75,
      mass_source: 'position_inferred' as const,
    })),
  );
  const [routing, setRouting] = useState<string | null>(null);
  const [swappingIdx, setSwappingIdx] = useState<number | null>(null);
  const [swapQuery, setSwapQuery] = useState('');
  const [swapSource, setSwapSource] = useState<SourceChoice>('both');

  const totalMass = useMemo(() => rows.reduce((s, r) => s + r.mass_g, 0), [rows]);

  const fpedFoods = useMemo(
    () => rows.map(r => ({ food_id: r.food_id, mass_g: r.mass_g })),
    [rows],
  );

  function setMass(idx: number, value: string): void {
    const n = parseFloat(value);
    setRows(r => {
      const next = [...r];
      next[idx] = { ...next[idx], mass_g: Number.isFinite(n) && n >= 0 ? n : 0 };
      return next;
    });
  }

  function applySubstitution(
    modified: SubstitutionCompositionItem[],
    _suggestion: SubstitutionSuggestion,
  ): void {
    setRows(prev => modified.map((m, i) => ({
      label_name: m.label_name ?? prev[i]?.label_name ?? m.food_description ?? '',
      position: m.position ?? i + 1,
      food_id: m.food_id,
      food_description: m.food_description ?? `Food ID ${m.food_id}`,
      food_group: m.food_group ?? null,
      mass_g: m.mass_g,
      confidence: prev[i]?.confidence ?? 0.75,
      mass_source: prev[i]?.mass_source ?? 'position_inferred',
    })));
  }

  function manualSwap(
    idx: number,
    picked: { food_id: number; food_description: string; food_group?: string },
  ): void {
    setRows(r => {
      const next = [...r];
      next[idx] = {
        ...next[idx],
        food_id: picked.food_id,
        food_description: picked.food_description,
        food_group: picked.food_group ?? next[idx].food_group,
      };
      return next;
    });
    setSwappingIdx(null);
    setSwapQuery('');
  }

  const compositionForSubstitution: SubstitutionCompositionItem[] = rows.map(r => ({
    food_id: r.food_id,
    mass_g: r.mass_g,
    food_description: r.food_description,
    food_group: r.food_group ?? undefined,
    label_name: r.label_name,
    position: r.position,
  }));

  function routeTo(route: typeof SCORE_ROUTES[number]): void {
    setRouting(route.id);
    const payload = {
      source: 'recall_24h' as const,
      user_type: userType,
      captured_at: new Date().toISOString(),
      target: route.id,
      meals_meta: [{ occasion: 'homemade', dish_name: dishName, total_mass_g: totalMass }],
      aggregated_daily_ingredients: rows.map(r => ({
        food_id: r.food_id,
        food_description: r.food_description,
        food_group: r.food_group || '',
        mass_g: r.mass_g,
        occasions: { homemade: r.mass_g },
      })),
      estimated_daily_kcal: 0,
    };
    try {
      sessionStorage.setItem('recall_24h_payload', JSON.stringify(payload));
      saveActiveFoodList(fromRecallAggregated(payload.aggregated_daily_ingredients, {
        user_type: userType,
        estimated_daily_kcal: 0,
        meals_meta: payload.meals_meta,
      }));
    } catch { /* non-fatal */ }
    window.location.href = route.path + '?from=recall24h';
  }

  return (
    <div className="space-y-4">
      <div className="border rounded-md bg-white overflow-hidden">
        <div className="px-3 py-2 bg-gray-50 border-b text-xs font-semibold text-gray-700 uppercase tracking-wide">
          {dishName} — {rows.length} ingredients ({totalMass.toFixed(0)} g)
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-600">
            <tr>
              <th className="px-2 py-1.5 text-left">CNF food</th>
              <th className="px-2 py-1.5 text-right w-24">Mass (g)</th>
              <th className="px-2 py-1.5 text-right w-24">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, idx) => (
              <Fragment key={idx}>
              <tr className="border-t">
                <td className="px-2 py-1.5">{r.food_description}</td>
                <td className="px-2 py-1.5 text-right">
                  <input
                    type="number"
                    step="1"
                    min="0"
                    value={r.mass_g}
                    onChange={e => setMass(idx, e.target.value)}
                    aria-label={`Mass in grams for ${r.food_description}`}
                    className="w-20 border border-gray-300 rounded px-1.5 py-0.5 text-sm text-right"
                  />
                </td>
                <td className="px-2 py-1.5 text-right space-x-2">
                  <button
                    type="button"
                    onClick={() => { setSwappingIdx(idx); setSwapQuery(r.food_description); }}
                    className="text-xs text-violet-700 hover:underline"
                  >
                    Swap
                  </button>
                  <button
                    type="button"
                    onClick={() => setRows(prev => prev.filter((_, i) => i !== idx))}
                    aria-label={`Remove ${r.food_description}`}
                    className="text-gray-400 hover:text-red-600 inline-flex"
                  >
                    <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                  </button>
                </td>
              </tr>
              {swappingIdx === idx && (
                <tr className="bg-violet-50/30">
                  <td colSpan={3} className="px-3 py-3">
                    <SourceFilter source={swapSource} onChange={setSwapSource} accent="purple" />
                    <input
                      type="text"
                      value={swapQuery}
                      onChange={e => setSwapQuery(e.target.value)}
                      className="w-full mt-2 mb-2 border rounded px-2 py-1.5 text-sm"
                      aria-label={`Search replacement for ${r.food_description}`}
                    />
                    <AIEnhancedSearch
                      query={swapQuery}
                      userType={userType}
                      accent="purple"
                      source={swapSource}
                      onSelect={picked => manualSwap(idx, picked)}
                    />
                    <button type="button" onClick={() => setSwappingIdx(null)} className="mt-2 text-xs text-gray-500">
                      Cancel
                    </button>
                  </td>
                </tr>
              )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {rows.length > 0 && (
        <FpedPanel
          foods={fpedFoods}
          userType={userType}
          contextHint="Updates when you edit masses or apply a swap."
        />
      )}

      <SubstitutionSuggestionsPanel
        composition={compositionForSubstitution}
        onApply={applySubstitution}
        userType={userType}
        dishName={substitutionDishName ?? dishName}
      />

      <div className="border-t pt-3">
        <h3 className="text-sm font-semibold text-gray-900 mb-1">See the full picture</h3>
        <p className="text-xs text-gray-500 mb-2">
          Send your updated ingredient list to a scorecard or individual calculator.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {SCORE_ROUTES.map(route => (
            <button
              key={route.id}
              type="button"
              onClick={() => routeTo(route)}
              disabled={routing !== null || rows.length === 0}
              className="flex items-start gap-2 p-3 border rounded-md hover:bg-blue-50 disabled:opacity-50 text-left"
            >
              <span className="text-xl" aria-hidden="true">{route.emoji}</span>
              <div className="flex-1">
                <p className="text-sm font-medium">{route.label}</p>
                <p className="text-xs text-gray-500">{route.note}</p>
              </div>
              <ChevronRight className="h-4 w-4 text-gray-400" aria-hidden="true" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
