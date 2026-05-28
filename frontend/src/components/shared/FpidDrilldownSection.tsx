'use client';

/**
 * FpidDrilldownSection — researcher/policy lens: per-food "where do the food groups
 * come from?" drilldown. Lists the scored foods; expanding one lazily mounts the
 * FpidBreakdownPanel (one API call per food, on demand). Hidden for the individual
 * audience (this is an ingredient-provenance research tool).
 */
import { useState } from 'react';
import { ChevronDown, ChevronRight, Microscope } from 'lucide-react';
import { FpidBreakdownPanel } from '@/components/shared/FpidBreakdownPanel';
import type { UserType } from '@/components/shared/AudienceToggle';

interface FpidDrilldownSectionProps {
  foods: Array<{ food_id: number; mass_g: number; food_description?: string }>;
  userType: UserType;
}

export function FpidDrilldownSection({ foods, userType }: FpidDrilldownSectionProps): JSX.Element | null {
  const [expanded, setExpanded] = useState<Set<number>>(() => new Set());

  if (userType === 'individual' || foods.length === 0) return null;

  const toggle = (id: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  return (
    <section className="bg-white rounded-2xl border border-gray-200 p-5">
      <div className="flex items-center gap-2 mb-3">
        <div className="bg-teal-100 p-2 rounded-lg">
          <Microscope className="h-4 w-4 text-teal-700" aria-hidden="true" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-gray-900">Where the food groups come from</h3>
          <p className="text-xs text-gray-500">
            Ingredient-level attribution per food (USDA FPID, via each food&apos;s closest US recipe analog)
          </p>
        </div>
      </div>

      <ul className="divide-y divide-gray-100">
        {foods.map((f) => {
          const isOpen = expanded.has(f.food_id);
          return (
            <li key={f.food_id}>
              <button
                type="button"
                onClick={() => toggle(f.food_id)}
                aria-expanded={isOpen}
                className="w-full flex items-center gap-2 py-2 text-left text-sm text-gray-800 hover:text-teal-800"
              >
                {isOpen
                  ? <ChevronDown className="h-4 w-4 text-gray-400" aria-hidden="true" />
                  : <ChevronRight className="h-4 w-4 text-gray-400" aria-hidden="true" />}
                <span className="flex-1 truncate">{f.food_description ?? `Food #${f.food_id}`}</span>
                <span className="text-xs text-gray-400 tabular-nums">{Math.round(f.mass_g)} g</span>
              </button>
              {isOpen && <FpidBreakdownPanel foodId={f.food_id} massG={f.mass_g} />}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
