import type { FoodGroup } from '@/lib/api';

/** WAFCT food groups are allocated FoodGroupID 50–63 at ingest time. */
export const WAFCT_GROUP_MIN_ID = 50;
/** Upper bound (exclusive) of the WAFCT range; FDC starts at 70. */
export const WAFCT_GROUP_MAX_ID_EXCL = 70;
/** FDC food groups (FDC-INGEST, 2026-06-25) — Foundation + SR Legacy share
 *  USDA's food_category table at FoodGroupID 70–97, FNDDS uses WWEIA codes
 *  starting at FoodGroupID 100. */
export const FDC_GROUP_MIN_ID = 70;
/** Upper bound (exclusive) of the FDC range; CIQUAL starts at 300. */
export const FDC_GROUP_MAX_ID_EXCL = 300;
/** CIQUAL food groups (CIQUAL-INGEST, 2026-06-26) — 12 top-level groups at
 *  FoodGroupID 300–311. */
export const CIQUAL_GROUP_MIN_ID = 300;

export function isWafctGroup(groupId: number): boolean {
  return groupId >= WAFCT_GROUP_MIN_ID && groupId < WAFCT_GROUP_MAX_ID_EXCL;
}

export function isFdcGroup(groupId: number): boolean {
  return groupId >= FDC_GROUP_MIN_ID && groupId < FDC_GROUP_MAX_ID_EXCL;
}

export function isCiqualGroup(groupId: number): boolean {
  return groupId >= CIQUAL_GROUP_MIN_ID;
}

export function isCnfGroup(groupId: number): boolean {
  return groupId < WAFCT_GROUP_MIN_ID;
}

/** Strip the source-prefix from a group name for compact sidebar labels.
 *  - `"WAFCT — Cereals"` (FoodGroupID 50–69) → `"Cereals"`
 *  - `"FDC — Beef Products"` (FoodGroupID 70–99) → `"Beef Products"`
 *  - `"FDC FNDDS — Milk, whole"` (FoodGroupID ≥ 100) → `"Milk, whole"`
 *  - Anything else returns the input unchanged.
 *  The unicode em-dash and the ASCII hyphen variants are both honoured. */
export function formatGroupDisplayName(name: string, groupId: number): string {
  if (isWafctGroup(groupId)) {
    if (name.startsWith('WAFCT — ')) return name.slice('WAFCT — '.length);
    if (name.startsWith('WAFCT - '))     return name.slice('WAFCT - '.length);
  }
  if (isFdcGroup(groupId)) {
    if (name.startsWith('FDC FNDDS — ')) return name.slice('FDC FNDDS — '.length);
    if (name.startsWith('FDC FNDDS - '))     return name.slice('FDC FNDDS - '.length);
    if (name.startsWith('FDC — ')) return name.slice('FDC — '.length);
    if (name.startsWith('FDC - '))     return name.slice('FDC - '.length);
  }
  if (isCiqualGroup(groupId)) {
    if (name.startsWith('CIQUAL — ')) return name.slice('CIQUAL — '.length);
    if (name.startsWith('CIQUAL - '))     return name.slice('CIQUAL - '.length);
  }
  return name;
}

export interface SplitFoodGroups {
  cnf:    FoodGroup[];
  wafct:  FoodGroup[];
  fdc:    FoodGroup[];
  ciqual: FoodGroup[];
}

export function splitFoodGroups(groups: FoodGroup[]): SplitFoodGroups {
  const cnf:    FoodGroup[] = [];
  const wafct:  FoodGroup[] = [];
  const fdc:    FoodGroup[] = [];
  const ciqual: FoodGroup[] = [];
  for (const g of groups) {
    if (isCiqualGroup(g.FoodGroupID))     ciqual.push(g);
    else if (isFdcGroup(g.FoodGroupID))   fdc.push(g);
    else if (isWafctGroup(g.FoodGroupID)) wafct.push(g);
    else                                  cnf.push(g);
  }
  return { cnf, wafct, fdc, ciqual };
}

export function topGroupsByCount(
  groups: FoodGroup[],
  countById: Map<number, number>,
  limit = 6,
): Array<{ group: FoodGroup; count: number }> {
  return groups
    .map(g => ({ group: g, count: countById.get(g.FoodGroupID) ?? 0 }))
    .sort((a, b) => b.count - a.count)
    .slice(0, limit);
}

export function prepStateLabel(value: string | null | undefined): string {
  if (!value || value === 'unknown') return 'Unknown';
  return value.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
