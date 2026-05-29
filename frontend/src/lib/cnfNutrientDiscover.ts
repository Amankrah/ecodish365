/** Single-nutrient presets for the compact compare-modal picker. */
export const NUTRIENT_DISCOVER_PRESETS: Array<{
  label: string;
  nutrientId: number;
  minValue?: number;
  maxValue?: number;
}> = [
  { label: 'High iron (≥ 3 mg / 100 g)', nutrientId: 303, minValue: 3 },
  { label: 'High fibre (≥ 5 g / 100 g)', nutrientId: 291, minValue: 5 },
  { label: 'Low sodium (< 50 mg / 100 g)', nutrientId: 307, maxValue: 50 },
  { label: 'High protein (≥ 15 g / 100 g)', nutrientId: 203, minValue: 15 },
  { label: 'High calcium (≥ 200 mg / 100 g)', nutrientId: 301, minValue: 200 },
];

/**
 * Multi-criteria research presets for the full Discover workbench. Each is a worked
 * example of a question that is hard to answer without the workbench: combine bounds,
 * adjust for energy, threshold on %DV, or rank by a clinical ratio.
 */
export interface DiscoverWorkbenchPreset {
  label: string;
  description: string;
  criteria: Array<{ nutrient_id: number; min?: number; max?: number }>;
  basis?: 'per_100g' | 'per_100kcal';
  ratio?: { numerator_id: number; denominator_id: number };
  dv_threshold?: { nutrient_id: number; min_pct?: number };
  sort?: { key: number | 'ratio' | 'energy'; direction?: 'asc' | 'desc' };
}

export const DISCOVER_WORKBENCH_PRESETS: DiscoverWorkbenchPreset[] = [
  {
    label: 'DASH-friendly: high potassium, low sodium',
    description: 'Potassium ≥ 300 mg AND sodium ≤ 50 mg per 100 g, ranked by potassium.',
    criteria: [{ nutrient_id: 306, min: 300 }, { nutrient_id: 307, max: 50 }],
    sort: { key: 306, direction: 'desc' },
  },
  {
    label: 'Lean protein: high protein, low saturated fat',
    description: 'Protein ≥ 20 g AND saturated fat ≤ 2 g per 100 g, ranked by protein.',
    criteria: [{ nutrient_id: 203, min: 20 }, { nutrient_id: 606, max: 2 }],
    sort: { key: 203, direction: 'desc' },
  },
  {
    label: 'Calcium per 100 kcal (density)',
    description: 'Most calcium per 100 kcal — energy-adjusted, not just absolute amount.',
    criteria: [{ nutrient_id: 301, min: 1 }],
    basis: 'per_100kcal',
    sort: { key: 301, direction: 'desc' },
  },
  {
    label: '≥ 50% Daily Value of iron',
    description: 'Foods delivering at least half the iron Daily Value per 100 g.',
    criteria: [],
    dv_threshold: { nutrient_id: 303, min_pct: 50 },
    sort: { key: 303, direction: 'desc' },
  },
  {
    label: 'Lowest sodium:potassium ratio',
    description: 'Best Na:K balance among foods with potassium ≥ 100 mg per 100 g.',
    criteria: [{ nutrient_id: 306, min: 100 }],
    ratio: { numerator_id: 307, denominator_id: 306 },
    sort: { key: 'ratio', direction: 'asc' },
  },
  {
    label: 'High fibre, low sugar',
    description: 'Fibre ≥ 6 g AND total sugars ≤ 5 g per 100 g, ranked by fibre.',
    criteria: [{ nutrient_id: 291, min: 6 }, { nutrient_id: 269, max: 5 }],
    sort: { key: 291, direction: 'desc' },
  },
];

/** Curated clinical ratio presets for the workbench ratio control. */
export const DISCOVER_RATIO_PRESETS: Array<{ label: string; numerator_id: number; denominator_id: number }> = [
  { label: 'Sodium : Potassium', numerator_id: 307, denominator_id: 306 },
  { label: 'PUFA : SFA', numerator_id: 646, denominator_id: 606 },
  { label: 'Omega-3 ALA : Linoleic (n-3:n-6)', numerator_id: 851, denominator_id: 675 },
  { label: 'Calcium : Phosphorus', numerator_id: 301, denominator_id: 305 },
];
