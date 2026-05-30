'use client';

import React, { useMemo, useState } from 'react';
import { ChevronRightIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import type { FoodGroup } from '@/lib/api';
import { formatGroupDisplayName, splitFoodGroups } from '@/lib/cnfGroupDisplay';

interface GroupSidebarProps {
  groups: FoodGroup[];
  countById: Map<number, number>;
  selectedId: number | null;
  onSelect: (group: FoodGroup) => void;
}

function getFoodGroupIcon(groupName: string): string {
  const iconMap: Record<string, string> = {
    dairy: '🥛', meat: '🥩', poultry: '🐔', fish: '🐟', seafood: '🦐',
    vegetable: '🥬', fruit: '🍎', grain: '🌾', cereal: '🥣', bread: '🍞',
    legume: '🫘', bean: '🫘', nut: '🥜', oil: '🫒', fat: '🧈',
    sugar: '🍯', sweet: '🍰', beverage: '🥤', spice: '🌶️', herb: '🌿',
    starchy: '🍠', milk: '🥛', soup: '🍲', misc: '🍽️',
  };
  const lower = groupName.toLowerCase();
  for (const [key, icon] of Object.entries(iconMap)) {
    if (lower.includes(key)) return icon;
  }
  return '🍽️';
}

function GroupButton({
  group,
  count,
  selected,
  onSelect,
}: {
  group: FoodGroup;
  count: number | undefined;
  selected: boolean;
  onSelect: () => void;
}) {
  const display = formatGroupDisplayName(group.FoodGroupName, group.FoodGroupID);
  return (
    <button
      type="button"
      onClick={onSelect}
      title={group.FoodGroupName}
      className={`w-full text-left p-3 rounded-lg transition-colors ${
        selected
          ? 'bg-primary-50 text-primary-700 border border-primary-200'
          : 'hover:bg-gray-50 border border-transparent'
      }`}
    >
      <div className="flex items-start gap-2.5">
        <span className="text-lg shrink-0 leading-none mt-0.5">{getFoodGroupIcon(display)}</span>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-gray-900 leading-snug line-clamp-2">
            {display}
          </div>
          <div className="text-xs text-gray-500 mt-0.5">
            {count != null ? `${count.toLocaleString()} foods` : `ID ${group.FoodGroupID}`}
          </div>
        </div>
        <ChevronRightIcon className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
      </div>
    </button>
  );
}

export function GroupSidebar({ groups, countById, selectedId, onSelect }: GroupSidebarProps) {
  const [query, setQuery] = useState('');
  const { cnf, wafct } = useMemo(() => splitFoodGroups(groups), [groups]);

  const filterGroups = (list: FoodGroup[]) => {
    if (!query.trim()) return list;
    const needle = query.trim().toLowerCase();
    return list.filter(g =>
      g.FoodGroupName.toLowerCase().includes(needle)
      || formatGroupDisplayName(g.FoodGroupName, g.FoodGroupID).toLowerCase().includes(needle),
    );
  };

  const cnfFiltered = filterGroups(cnf);
  const wafctFiltered = filterGroups(wafct);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 lg:p-5 sticky top-4">
      <h2 className="text-lg font-semibold text-gray-900 mb-3">
        Food groups ({groups.length})
      </h2>

      <div className="relative mb-4">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="search"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Filter groups…"
          aria-label="Filter food groups"
          className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      <div className="space-y-5 max-h-[calc(100vh-14rem)] overflow-y-auto pr-1">
        <section>
          <div className="flex items-center gap-2 mb-2 px-1">
            <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">CNF</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 border border-gray-200">
              Health Canada
            </span>
          </div>
          <div className="space-y-1">
            {cnfFiltered.length === 0 ? (
              <p className="text-xs text-gray-400 px-2 py-1">No matching CNF groups</p>
            ) : cnfFiltered.map(group => (
              <GroupButton
                key={group.FoodGroupID}
                group={group}
                count={countById.get(group.FoodGroupID)}
                selected={selectedId === group.FoodGroupID}
                onSelect={() => onSelect(group)}
              />
            ))}
          </div>
        </section>

        {wafct.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-2 px-1">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">WAFCT</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200">
                FAO/INFOODS 2019
              </span>
            </div>
            <div className="space-y-1">
              {wafctFiltered.length === 0 ? (
                <p className="text-xs text-gray-400 px-2 py-1">No matching WAFCT groups</p>
              ) : wafctFiltered.map(group => (
                <GroupButton
                  key={group.FoodGroupID}
                  group={group}
                  count={countById.get(group.FoodGroupID)}
                  selected={selectedId === group.FoodGroupID}
                  onSelect={() => onSelect(group)}
                />
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

export { getFoodGroupIcon };
