/**
 * SourceFilter — 5-button segmented control for picking which food database
 * a search box draws from (WAFCT-EXTEND 2026-05-24, FDC-INGEST 2026-06-25,
 * CIQUAL-INGEST 2026-06-26).
 *
 * Drops in above any food-search input on the 5 calculator pages
 * (HEFI / HENI / HSR / FCS / Environmental) plus the CNF Explorer.
 * Default selection is 'both' — users opt into single-source filtering;
 * they never get accidentally narrowed.
 *
 * Backend wiring: the chosen value is passed via the `source` query param
 * to `/api/cnf/search/` (basic search) and as the `source` body field to
 * `/api/cnf/search/ai-enhanced/` (LLM-ranked search). All four sources
 * (CNF, WAFCT, FDC, CIQUAL) live in the same in-memory schema; the filter
 * just narrows the post-retrieval candidate list.
 */
'use client';

import { Globe, Leaf, MapPin, Flag, Wine, type LucideIcon } from 'lucide-react';

/** Same shape as the API-side `SourceFilter` type in `@/lib/api` — re-
 *  exported here under a component-friendly name so callers don't have to
 *  cross-import. */
export type SourceChoice = 'both' | 'cnf' | 'wafct' | 'fdc' | 'ciqual';

interface SourceFilterProps {
  source: SourceChoice;
  onChange: (next: SourceChoice) => void;
  /** Hidden when only one source is available in the deployment (set true
   *  if WAFCT_2019.xlsx is absent in some installations). */
  visible?: boolean;
  /** Optional accent matches each calculator's primary colour. */
  accent?: 'blue' | 'green' | 'purple' | 'amber';
}

const ACCENT_ACTIVE: Record<NonNullable<SourceFilterProps['accent']>, string> = {
  blue:   'bg-blue-100 text-blue-700',
  green:  'bg-green-100 text-green-700',
  purple: 'bg-purple-100 text-purple-700',
  amber:  'bg-amber-100 text-amber-700',
};

const OPTIONS: Array<{
  value: SourceChoice;
  label: string;
  Icon: LucideIcon;
  title: string;
}> = [
  { value: 'both',   label: 'All',    Icon: Globe,  title: 'Search all food databases (CNF, WAFCT, FDC, CIQUAL)' },
  { value: 'cnf',    label: 'CNF',    Icon: Leaf,   title: 'Search Canadian Nutrient File only (5,993 foods)' },
  { value: 'wafct',  label: 'WAFCT',  Icon: MapPin, title: 'Search FAO/INFOODS West African Food Composition Table 2019 only (1,028 foods)' },
  { value: 'fdc',    label: 'FDC',    Icon: Flag,   title: 'Search USDA FoodData Central only (~13,620 foods: Foundation + SR Legacy + FNDDS)' },
  { value: 'ciqual', label: 'CIQUAL', Icon: Wine,   title: 'Search ANSES CIQUAL 2025 (French nutrition database) only (~3,484 foods)' },
];

export function SourceFilter({
  source,
  onChange,
  visible = true,
  accent = 'blue',
}: SourceFilterProps) {
  if (!visible) return null;
  const activeClass = ACCENT_ACTIVE[accent];
  return (
    <div className="inline-flex items-center gap-2">
      <span className="text-xs font-medium text-gray-500">Source:</span>
      <fieldset className="bg-white rounded-md border p-0.5 shadow-sm m-0 inline-flex">
        <legend className="sr-only">Food database source</legend>
        {OPTIONS.map(({ value, label, Icon, title }) => (
          <label
            key={value}
            title={title}
            className={`px-2.5 py-1 rounded text-xs font-medium transition-colors flex items-center gap-1 cursor-pointer ${
              source === value ? `${activeClass} shadow-sm` : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            <input
              type="radio"
              name="food-source-filter"
              value={value}
              checked={source === value}
              onChange={() => onChange(value)}
              className="sr-only"
              aria-label={title}
            />
            <Icon className="h-3 w-3" aria-hidden={true} />
            {label}
          </label>
        ))}
      </fieldset>
    </div>
  );
}
