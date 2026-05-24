/**
 * SourceBadge — small per-result provenance pill (WAFCT-EXTEND, 2026-05-24).
 *
 * Renders a "WAFCT" or "CNF" tag next to a food name so users know which
 * food-composition database the row came from. Audience-aware:
 *   - researcher / policy modes: always visible
 *   - individual mode: rendered only for WAFCT (so the CNF default is silent)
 *
 * Designed to render inline inside search-result rows + selected-foods lists
 * + the recall wizard's per-meal and aggregated lists. Compact (12-14 px
 * height) so it fits next to any text without breaking layout.
 */
'use client';

import type { UserType } from './AudienceToggle';

/** Derive the food-database source from a FoodID. WAFCT-EXTEND allocates
 *  FoodIDs ≥ 700,000 to WAFCT-ingested rows; CNF tops out around 503,381
 *  with ~200 k of clean headroom (guarded at ingest time in
 *  `backend/api/services/etl/wafct_ingest.py:CNF_MAX_FOOD_ID_GUARD`).
 *  Lets call sites flag provenance without an extra API field on every
 *  search-result row — basic search responses already carry the FoodID. */
export function sourceForFoodId(foodId: number | null | undefined): 'cnf' | 'wafct' | null {
  if (foodId === null || foodId === undefined) return null;
  return foodId >= 700_000 ? 'wafct' : 'cnf';
}

interface SourceBadgeProps {
  source?: 'cnf' | 'wafct' | null;
  /** Alternative to `source` — derives provenance from the FoodID directly.
   *  Convenience for call sites that have the food ID but no source field. */
  foodId?: number | null;
  userType?: UserType;
  className?: string;
}

export function SourceBadge({
  source,
  foodId,
  userType = 'individual',
  className = '',
}: SourceBadgeProps) {
  const resolved: 'cnf' | 'wafct' | null = source ?? sourceForFoodId(foodId);
  if (!resolved) return null;
  // In individual mode, only the WAFCT tag is shown — CNF is the implicit
  // default and surfacing "CNF" everywhere would be visual noise.
  if (userType === 'individual' && resolved === 'cnf') return null;
  const isWAFCT = resolved === 'wafct';
  const styles = isWAFCT
    ? 'bg-amber-100 text-amber-800 border-amber-200'
    : 'bg-gray-100 text-gray-700 border-gray-200';
  const label = isWAFCT ? 'WAFCT' : 'CNF';
  const title = isWAFCT
    ? 'From FAO/INFOODS West African Food Composition Table 2019'
    : 'From Health Canada Canadian Nutrient File';
  return (
    <span
      title={title}
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border whitespace-nowrap ${styles} ${className}`}
    >
      {label}
    </span>
  );
}
