import type { FoodGroup } from '@/lib/api';

/** WAFCT food groups are allocated FoodGroupID 50–63 at ingest time. */
export const WAFCT_GROUP_MIN_ID = 50;

export function isWafctGroup(groupId: number): boolean {
  return groupId >= WAFCT_GROUP_MIN_ID;
}

/** Strip the repeated "WAFCT — " prefix for compact sidebar labels. */
export function formatGroupDisplayName(name: string, groupId: number): string {
  if (isWafctGroup(groupId) && name.startsWith('WAFCT — ')) {
    return name.slice('WAFCT — '.length);
  }
  if (isWafctGroup(groupId) && name.startsWith('WAFCT - ')) {
    return name.slice('WAFCT - '.length);
  }
  return name;
}

export interface SplitFoodGroups {
  cnf: FoodGroup[];
  wafct: FoodGroup[];
}

export function splitFoodGroups(groups: FoodGroup[]): SplitFoodGroups {
  const cnf: FoodGroup[] = [];
  const wafct: FoodGroup[] = [];
  for (const g of groups) {
    if (isWafctGroup(g.FoodGroupID)) wafct.push(g);
    else cnf.push(g);
  }
  return { cnf, wafct };
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
