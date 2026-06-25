'use client';

import React, { useMemo, useState, type ComponentType, type SVGProps } from 'react';
import { ChevronRightIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import {
  Milk, Beef, Drumstick, Fish, Carrot, Apple, Wheat, Croissant,
  Sprout, Droplet, Cake, CupSoda, Leaf, Soup, Utensils, Cookie, Nut,
} from 'lucide-react';
import type { FoodGroup } from '@/lib/api';
import { formatGroupDisplayName, splitFoodGroups } from '@/lib/cnfGroupDisplay';

type IconType = ComponentType<SVGProps<SVGSVGElement>>;

interface GroupSidebarProps {
  groups: FoodGroup[];
  countById: Map<number, number>;
  selectedId: number | null;
  onSelect: (group: FoodGroup) => void;
}

function getFoodGroupIcon(groupName: string): IconType {
  const iconMap: Record<string, IconType> = {
    dairy: Milk, meat: Beef, poultry: Drumstick, fish: Fish, seafood: Fish,
    vegetable: Carrot, fruit: Apple, grain: Wheat, cereal: Soup, bread: Croissant,
    legume: Sprout, bean: Sprout, nut: Nut, oil: Droplet, fat: Droplet,
    sugar: Cookie, sweet: Cake, beverage: CupSoda, spice: Sprout, herb: Leaf,
    starchy: Wheat, milk: Milk, soup: Soup, misc: Utensils,
  };
  const lower = groupName.toLowerCase();
  for (const [key, icon] of Object.entries(iconMap)) {
    if (lower.includes(key)) return icon;
  }
  return Utensils;
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
        {(() => {
          const Icon = getFoodGroupIcon(display);
          return <Icon className="w-4 h-4 shrink-0 mt-0.5 text-gray-600" aria-hidden="true" />;
        })()}
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

interface SectionProps {
  title:       string;
  badge:       string;
  badgeClass:  string;
  visible:     FoodGroup[];
  emptyLabel:  string;
  countById:   Map<number, number>;
  selectedId:  number | null;
  onSelect:    (group: FoodGroup) => void;
  totalInSource: number;
}

function SidebarSection({
  title, badge, badgeClass, visible, emptyLabel, countById, selectedId, onSelect, totalInSource,
}: SectionProps) {
  if (totalInSource === 0) return null;
  return (
    <section>
      <div className="flex items-center gap-2 mb-2 px-1">
        <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">{title}</span>
        <span className={`text-[10px] px-1.5 py-0.5 rounded border ${badgeClass}`}>{badge}</span>
        <span className="text-[10px] text-gray-400 ml-auto tabular-nums">{totalInSource}</span>
      </div>
      <div className="space-y-1">
        {visible.length === 0 ? (
          <p className="text-xs text-gray-400 px-2 py-1">{emptyLabel}</p>
        ) : visible.map(group => (
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
  );
}

export function GroupSidebar({ groups, countById, selectedId, onSelect }: GroupSidebarProps) {
  const [query, setQuery] = useState('');
  // FDC-INGEST (2026-06-25): three-way split (CNF / WAFCT / FDC). Each
  // section gets its own divider chip so the three sources stay visually
  // separated in the 237-group sidebar.
  const { cnf, wafct, fdc } = useMemo(() => splitFoodGroups(groups), [groups]);

  const filterGroups = (list: FoodGroup[]) => {
    if (!query.trim()) return list;
    const needle = query.trim().toLowerCase();
    return list.filter(g =>
      g.FoodGroupName.toLowerCase().includes(needle)
      || formatGroupDisplayName(g.FoodGroupName, g.FoodGroupID).toLowerCase().includes(needle),
    );
  };

  const cnfFiltered   = filterGroups(cnf);
  const wafctFiltered = filterGroups(wafct);
  const fdcFiltered   = filterGroups(fdc);

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
        <SidebarSection
          title="CNF"
          badge="Health Canada"
          badgeClass="bg-gray-100 text-gray-600 border-gray-200"
          visible={cnfFiltered}
          emptyLabel="No matching CNF groups"
          countById={countById}
          selectedId={selectedId}
          onSelect={onSelect}
          totalInSource={cnf.length}
        />
        <SidebarSection
          title="WAFCT"
          badge="FAO/INFOODS 2019"
          badgeClass="bg-amber-100 text-amber-800 border-amber-200"
          visible={wafctFiltered}
          emptyLabel="No matching WAFCT groups"
          countById={countById}
          selectedId={selectedId}
          onSelect={onSelect}
          totalInSource={wafct.length}
        />
        <SidebarSection
          title="FDC"
          badge="USDA FoodData Central"
          badgeClass="bg-sky-100 text-sky-800 border-sky-200"
          visible={fdcFiltered}
          emptyLabel="No matching FDC groups"
          countById={countById}
          selectedId={selectedId}
          onSelect={onSelect}
          totalInSource={fdc.length}
        />
      </div>
    </div>
  );
}

export { getFoodGroupIcon };
