'use client';

import Link from 'next/link';
import { XMarkIcon } from '@heroicons/react/24/outline';
import type { CompareFoodSummary } from '@/lib/api';
import { SourceBadge } from '@/components/shared/SourceBadge';
import type { UserType } from '@/components/shared/AudienceToggle';
import { prepStateLabel } from '@/lib/cnfGroupDisplay';

function PrepChip({ label }: { label: string }) {
  return (
    <span className="inline-flex px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700 border border-slate-200">
      {label}
    </span>
  );
}

interface CompareFoodStripProps {
  foods: CompareFoodSummary[];
  userType: UserType;
  groupLabel: (food: CompareFoodSummary) => string;
  portionMass: Record<number, number>;
  onPortionChange: (foodId: number, mass: number) => void;
  onRemove: (foodId: number) => void;
  onViewProfile: (foodId: number) => void;
}

export function CompareFoodStrip({
  foods,
  userType,
  groupLabel,
  portionMass,
  onPortionChange,
  onRemove,
  onViewProfile,
}: CompareFoodStripProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-gray-900">
          Comparing {foods.length} food{foods.length === 1 ? '' : 's'}
        </h2>
      </div>
      <div className="flex gap-3 overflow-x-auto pb-1">
        {foods.map(food => {
          const mass = portionMass[food.FoodID] ?? 100;
          const src = food.source === 'wafct' ? 'wafct' : food.source === 'cnf' ? 'cnf' : undefined;
          return (
            <div
              key={food.FoodID}
              className="relative shrink-0 w-64 min-w-[14rem] border border-gray-200 rounded-lg p-3 bg-gray-50/80"
            >
              <button
                type="button"
                onClick={() => onRemove(food.FoodID)}
                className="absolute top-2 right-2 p-0.5 text-gray-400 hover:text-red-500"
                title="Remove"
              >
                <XMarkIcon className="w-4 h-4" />
              </button>
              <div className="pr-5">
                <Link
                  href={`/cnf/foods/${food.FoodID}`}
                  className="text-sm font-medium text-gray-900 hover:text-primary-700 line-clamp-2 leading-snug"
                  title={food.FoodDescription}
                >
                  {food.FoodDescription}
                </Link>
                <div className="flex flex-wrap items-center gap-1 mt-1.5">
                  <SourceBadge source={src} foodId={food.FoodID} userType={userType} />
                  {food.food_type && <PrepChip label={food.food_type} />}
                  {food.thermal_state && food.thermal_state !== 'unknown' && (
                    <PrepChip label={prepStateLabel(food.thermal_state)} />
                  )}
                </div>
                <p className="text-[11px] text-gray-500 mt-1 line-clamp-1">
                  {groupLabel(food)}
                </p>
                <div className="flex flex-wrap gap-x-2 gap-y-0.5 text-[11px] text-gray-600 mt-1.5 tabular-nums">
                  {food.energy_kcal != null && <span>{food.energy_kcal.toFixed(0)} kcal</span>}
                  {food.protein_g != null && <span>{food.protein_g.toFixed(1)} g protein</span>}
                  {food.fibre_g != null && <span>{food.fibre_g.toFixed(1)} g fibre</span>}
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <label className="text-[10px] text-gray-500 shrink-0" htmlFor={`mass-${food.FoodID}`}>
                    Scorecard g
                  </label>
                  <input
                    id={`mass-${food.FoodID}`}
                    type="number"
                    min={1}
                    max={2000}
                    value={mass}
                    onChange={e => onPortionChange(food.FoodID, Number(e.target.value) || 100)}
                    className="w-16 px-1.5 py-0.5 text-xs border border-gray-300 rounded"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => onViewProfile(food.FoodID)}
                  className="mt-2 text-[11px] font-medium text-blue-700 hover:text-blue-900"
                >
                  Quick profile →
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
