/**
 * SourceBadge — small per-result provenance pill
 * (WAFCT-EXTEND 2026-05-24, FDC-INGEST 2026-06-25).
 *
 * Renders a "CNF" / "WAFCT" / "FDC" tag next to a food name so users
 * know which food-composition database the row came from. Audience-aware:
 *   - researcher / policy modes: always visible
 *   - individual mode: rendered only for non-CNF sources (so the CNF
 *     default is silent)
 *
 * Designed to render inline inside search-result rows + selected-foods lists
 * + the recall wizard's per-meal and aggregated lists. Compact (12-14 px
 * height) so it fits next to any text without breaking layout.
 */
'use client';

import type { UserType } from './AudienceToggle';

export type FoodSource = 'cnf' | 'wafct' | 'fdc';

/** Derive the food-database source from a FoodID. Offsets mirror the
 *  backend allocation in `backend/api/services/etl/*_ingest.py`:
 *    - CNF        1 –        503,381   (guarded ≤ 600,000)
 *    - WAFCT      700,000 –  701,027
 *    - FDC        800,000 –  ~825,431  (Foundation 800k / SR Legacy 810k /
 *                                       FNDDS 820k)
 *  Lets call sites flag provenance without an extra API field on every
 *  search-result row — basic search responses already carry the FoodID. */
export function sourceForFoodId(foodId: number | null | undefined): FoodSource | null {
  if (foodId === null || foodId === undefined) return null;
  if (foodId >= 800_000) return 'fdc';
  if (foodId >= 700_000) return 'wafct';
  return 'cnf';
}

interface SourceBadgeProps {
  source?: FoodSource | null;
  /** Alternative to `source` — derives provenance from the FoodID directly.
   *  Convenience for call sites that have the food ID but no source field. */
  foodId?: number | null;
  userType?: UserType;
  className?: string;
}

const SOURCE_META: Record<FoodSource, { label: string; styles: string; title: string }> = {
  cnf: {
    label:  'CNF',
    styles: 'bg-gray-100 text-gray-700 border-gray-200',
    title:  'From Health Canada Canadian Nutrient File',
  },
  wafct: {
    label:  'WAFCT',
    styles: 'bg-amber-100 text-amber-800 border-amber-200',
    title:  'From FAO/INFOODS West African Food Composition Table 2019',
  },
  fdc: {
    label:  'FDC',
    styles: 'bg-sky-100 text-sky-800 border-sky-200',
    title:  'From USDA FoodData Central (Foundation / SR Legacy / FNDDS)',
  },
};

export function SourceBadge({
  source,
  foodId,
  userType = 'individual',
  className = '',
}: SourceBadgeProps) {
  const resolved: FoodSource | null = source ?? sourceForFoodId(foodId);
  if (!resolved) return null;
  // In individual mode, only non-CNF tags are shown — CNF is the implicit
  // default and surfacing "CNF" everywhere would be visual noise.
  if (userType === 'individual' && resolved === 'cnf') return null;
  const { label, styles, title } = SOURCE_META[resolved];
  return (
    <span
      title={title}
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border whitespace-nowrap ${styles} ${className}`}
    >
      {label}
    </span>
  );
}
