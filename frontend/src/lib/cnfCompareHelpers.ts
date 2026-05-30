import type { FoodComparison, FoodComparisonNutrientCell } from '@/lib/api';
import { percentDV } from '@/lib/cnfDailyValues';
import { LENS_NUTRIENT_PANELS } from '@/lib/cnfNutrientPanels';

export type CompareBasis = 'per_100g' | 'per_100kcal';

export const NUTRIENT_CATEGORIES: Record<string, string[]> = {
  Energy: ['ENERGY (KILOCALORIES)', 'ENERGY (KILOJOULES)'],
  Macronutrients: [
    'PROTEIN', 'FAT (TOTAL LIPIDS)', 'CARBOHYDRATE, TOTAL (BY DIFFERENCE)',
    'FIBRE, TOTAL DIETARY', 'SUGARS, TOTAL',
  ],
  Minerals: ['CALCIUM', 'IRON', 'SODIUM', 'POTASSIUM', 'MAGNESIUM', 'PHOSPHORUS', 'ZINC'],
  Vitamins: [
    'RETINOL', 'RETINOL ACTIVITY EQUIVALENTS', 'BETA CAROTENE', 'ALPHA-TOCOPHEROL',
    'VITAMIN D (INTERNATIONAL UNITS)', 'VITAMIN C', 'THIAMIN', 'RIBOFLAVIN', 'NIACIN',
    'TOTAL FOLACIN', 'VITAMIN B-12', 'VITAMIN K',
  ],
  'Fatty Acids': [
    'FATTY ACIDS, SATURATED, TOTAL', 'FATTY ACIDS, MONOUNSATURATED, TOTAL',
    'FATTY ACIDS, POLYUNSATURATED, TOTAL', 'FATTY ACIDS, TRANS, TOTAL', 'CHOLESTEROL',
  ],
};

export const COMPARE_RATIO_PRESETS: Array<{
  label: string;
  numerator_id: number;
  denominator_id: number;
  lowerIsBetter?: boolean;
}> = [
  { label: 'Sodium : Potassium', numerator_id: 307, denominator_id: 306, lowerIsBetter: true },
  { label: 'PUFA : SFA', numerator_id: 646, denominator_id: 606, lowerIsBetter: false },
];

export function findComparisonNutrientEntry(
  comparison: FoodComparison | null,
  nutrientKey: string,
) {
  if (!comparison) return null;
  const direct = comparison.nutrients[nutrientKey];
  if (direct) return { key: nutrientKey, ...direct };
  const hit = Object.entries(comparison.nutrients).find(
    ([key]) => key.toLowerCase() === nutrientKey.toLowerCase(),
  );
  if (!hit) return null;
  return { key: hit[0], ...hit[1] };
}

export function resolveLensNutrientKeys(comparison: FoodComparison): string[] {
  const patterns = [
    ...LENS_NUTRIENT_PANELS.hsr.patterns,
    ...LENS_NUTRIENT_PANELS.fcs.patterns,
  ];
  const keys: string[] = [];
  const seen = new Set<string>();
  for (const pat of patterns) {
    const hit = Object.keys(comparison.nutrients).find(k =>
      k.toUpperCase().includes(pat.toUpperCase()),
    );
    if (hit && !seen.has(hit)) {
      seen.add(hit);
      keys.push(hit);
    }
  }
  return keys;
}

export function getNutrientCell(
  comparison: FoodComparison | null,
  foodId: number,
  nutrientKey: string,
): FoodComparisonNutrientCell | null {
  const entry = findComparisonNutrientEntry(comparison, nutrientKey);
  if (!entry?.by_food_id) return null;
  return entry.by_food_id[String(foodId)] ?? null;
}

export function getValueByNutrientId(
  comparison: FoodComparison | null,
  foodId: number,
  nutrientId: number,
): number | null {
  if (!comparison) return null;
  for (const key of Object.keys(comparison.nutrients)) {
    if (comparison.nutrients[key].nutrient_id === nutrientId) {
      return comparison.nutrients[key].by_food_id?.[String(foodId)]?.value ?? null;
    }
  }
  return null;
}

export function getRaw100gByNutrientId(
  comparison: FoodComparison | null,
  foodId: number,
  nutrientId: number,
): number | null {
  if (!comparison) return null;
  for (const key of Object.keys(comparison.nutrients)) {
    if (comparison.nutrients[key].nutrient_id === nutrientId) {
      const cell = comparison.nutrients[key].by_food_id?.[String(foodId)];
      if (!cell) return null;
      return cell.value_per_100g ?? cell.value;
    }
  }
  return null;
}

export function cellPercentDV(
  comparison: FoodComparison | null,
  foodId: number,
  nutrientId: number,
): number | null {
  const raw = getRaw100gByNutrientId(comparison, foodId, nutrientId);
  if (raw == null) return null;
  return percentDV(nutrientId, raw, (otherId) => getRaw100gByNutrientId(comparison, foodId, otherId));
}

export function computeRatio(
  comparison: FoodComparison | null,
  foodId: number,
  numeratorId: number,
  denominatorId: number,
): number | null {
  const num = getValueByNutrientId(comparison, foodId, numeratorId);
  const den = getValueByNutrientId(comparison, foodId, denominatorId);
  if (num == null || den == null || den === 0) return null;
  return num / den;
}

export function nutrientKeysForCategory(
  category: string,
  comparison: FoodComparison | null,
): string[] {
  if (category === 'Lens highlights (HSR/FCS)' && comparison) {
    return resolveLensNutrientKeys(comparison);
  }
  return NUTRIENT_CATEGORIES[category] ?? [];
}

export function hasMixedDatabases(foodIds: number[], sources?: Array<'cnf' | 'wafct' | string>): boolean {
  if (sources?.length) {
    const set = new Set(sources.map(s => (s === 'wafct' ? 'wafct' : 'cnf')));
    return set.size > 1;
  }
  const hasWafct = foodIds.some(id => id >= 700_000);
  const hasCnf = foodIds.some(id => id < 700_000);
  return hasWafct && hasCnf;
}
