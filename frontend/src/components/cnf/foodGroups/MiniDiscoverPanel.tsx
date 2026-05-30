'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { BeakerIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { CNFApiService, type DiscoverResult } from '@/lib/api';
import { NUTRIENT_DISCOVER_PRESETS } from '@/lib/cnfNutrientDiscover';
import { CNF_DAILY_VALUES, percentDV } from '@/lib/cnfDailyValues';
import { SourceBadge } from '@/components/shared/SourceBadge';
import type { UserType } from '@/components/shared/AudienceToggle';

interface MiniDiscoverPanelProps {
  foodGroupId: number;
  groupName: string;
  userType: UserType;
}

/** Preset nutrients without a Canadian %DV still need a display label + unit. */
const PRESET_NUTRIENT_META: Record<number, { label: string; unit: string }> = {
  203: { label: 'Protein', unit: 'g' },
};

function nutrientMeta(nutrientId: number): { label: string; unit: string } {
  const dv = CNF_DAILY_VALUES[nutrientId];
  if (dv) return { label: dv.label, unit: dv.unit };
  return PRESET_NUTRIENT_META[nutrientId] ?? { label: `Nutrient ${nutrientId}`, unit: '' };
}

function formatNutrientAmount(value: number, unit: string): string {
  if (unit === 'g') return `${value % 1 === 0 ? value : value.toFixed(1)} g`;
  if (unit === 'mg') return `${value % 1 === 0 ? value : value.toFixed(0)} mg`;
  if (unit === 'µg') return `${value % 1 === 0 ? value : value.toFixed(0)} µg`;
  return String(value);
}

function cellDV(nutrientId: number, values: Record<string, number>): number | null {
  return percentDV(
    nutrientId,
    values[String(nutrientId)],
    (other) => values[String(other)] ?? null,
  );
}

export function MiniDiscoverPanel({ foodGroupId, groupName, userType }: MiniDiscoverPanelProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DiscoverResult | null>(null);
  const [activePreset, setActivePreset] = useState<string | null>(null);
  const [activeNutrientId, setActiveNutrientId] = useState<number | null>(null);

  const runPreset = async (preset: typeof NUTRIENT_DISCOVER_PRESETS[0]) => {
    setLoading(true);
    setActivePreset(preset.label);
    setActiveNutrientId(preset.nutrientId);
    try {
      const criteria = [{
        nutrient_id: preset.nutrientId,
        ...(preset.minValue != null ? { min: preset.minValue } : {}),
        ...(preset.maxValue != null ? { max: preset.maxValue } : {}),
      }];
      const data = await CNFApiService.discoverFoods({
        criteria,
        food_group_id: foodGroupId,
        sort: { key: preset.nutrientId, direction: preset.minValue != null ? 'desc' : 'asc' },
        limit: 8,
      });
      setResult(data);
    } catch {
      toast.error('Discover query failed');
    } finally {
      setLoading(false);
    }
  };

  const meta = activeNutrientId != null ? nutrientMeta(activeNutrientId) : null;

  return (
    <div className="border border-teal-200 bg-teal-50/50 rounded-xl mb-4 overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-teal-50 transition-colors"
      >
        <span className="flex items-center gap-2 text-sm font-medium text-teal-900">
          <BeakerIcon className="w-4 h-4" />
          Screen this group by nutrient
        </span>
        {open ? (
          <ChevronUpIcon className="w-4 h-4 text-teal-700" />
        ) : (
          <ChevronDownIcon className="w-4 h-4 text-teal-700" />
        )}
      </button>

      {open && (
        <div className="px-4 pb-4 border-t border-teal-100">
          <p className="text-xs text-teal-800/80 mt-3 mb-3">
            Quick presets scoped to <strong>{groupName}</strong>. For multi-criteria queries, open the full workbench.
          </p>
          <div className="flex flex-wrap gap-2 mb-3">
            {NUTRIENT_DISCOVER_PRESETS.map(preset => (
              <button
                key={preset.label}
                type="button"
                disabled={loading}
                onClick={() => runPreset(preset)}
                className={`text-xs px-2.5 py-1.5 rounded-lg border transition-colors disabled:opacity-50 ${
                  activePreset === preset.label
                    ? 'bg-teal-600 text-white border-teal-600'
                    : 'bg-white text-teal-900 border-teal-200 hover:border-teal-400'
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>

          <Link
            href={`/cnf/discover?group=${foodGroupId}`}
            className="text-xs text-teal-800 hover:text-teal-950 underline"
          >
            Open full Discover workbench for this group →
          </Link>

          {loading && (
            <p className="text-xs text-gray-500 mt-3">Searching…</p>
          )}

          {result && !loading && activeNutrientId != null && meta && (
            <div className="mt-3 bg-white rounded-lg border border-teal-100 overflow-hidden">
              <p className="text-[11px] text-gray-500 px-3 py-2 border-b border-gray-100">
                {result.count} match{result.count === 1 ? '' : 'es'} · {meta.label} per 100 g · showing up to 8
              </p>
              {result.foods.length === 0 ? (
                <p className="text-xs text-gray-500 p-3">No foods matched in this group.</p>
              ) : (
                <ul className="divide-y divide-gray-100 max-h-56 overflow-y-auto">
                  {result.foods.map(f => {
                    const raw = f.nutrient_values[String(activeNutrientId)];
                    const dv = cellDV(activeNutrientId, f.nutrient_values);
                    return (
                      <li key={f.FoodID} className="px-3 py-2 text-sm hover:bg-gray-50">
                        <Link href={`/cnf/foods/${f.FoodID}`} className="font-medium text-gray-900 hover:text-primary-700">
                          {f.FoodDescription}
                        </Link>
                        <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 mt-1 text-xs">
                          <span className="font-medium text-teal-900">
                            {meta.label}:{' '}
                            {raw != null ? formatNutrientAmount(raw, meta.unit) : '—'}
                            {dv != null && (
                              <span className="ml-1.5 text-emerald-700 font-semibold">
                                {dv.toFixed(0)}% DV
                              </span>
                            )}
                          </span>
                          {f.energy_kcal != null && (
                            <span className="text-gray-500">{f.energy_kcal} kcal / 100 g</span>
                          )}
                          <SourceBadge foodId={f.FoodID} userType={userType} />
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
              <p className="text-[10px] text-gray-400 px-3 py-1.5 border-t border-gray-100">
                %DV uses Health Canada daily values on the per-100 g amount.
                {CNF_DAILY_VALUES[activeNutrientId] == null && ' This nutrient has no Canadian %DV.'}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
