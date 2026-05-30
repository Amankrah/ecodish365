import type { ActiveFoodList } from '@/lib/activeFoodList';

/** Human-readable label for the saved food list header. */
export function provenanceLabel(list: ActiveFoodList): string {
  if (list.multi_day?.label) return list.multi_day.label;
  if (list.multi_day) return `${list.multi_day.n_days}-day average`;
  if (list.source === 'packaged_food_inferred') return 'Scanned product (estimated)';
  if (list.source === 'imported') return 'Imported list';
  if (list.source === 'catalogue_compare') return 'From food comparison';
  if (list.source === 'catalogue') return 'From food catalogue';
  if (list.list_label) return list.list_label;
  if (list.source === 'manual') return 'Manual selection';
  if (list.source === 'recall_24h') return 'Food diary day';
  return 'Saved food list';
}

export type ScorecardMode = 'build' | 'review' | 'improve';

export function deriveScorecardMode(
  nFoods: number,
  hasResults: boolean,
  swapsExpanded: boolean,
): ScorecardMode {
  if (swapsExpanded && hasResults) return 'improve';
  if (hasResults) return 'review';
  return 'build';
}
