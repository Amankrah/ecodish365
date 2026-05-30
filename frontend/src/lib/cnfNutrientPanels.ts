import type { NutrientValue } from './api';

/** Nutrient name patterns grouped by scoring lens — used in the food detail drawer
 *  to surface what each published measure reads from composition data. */
export const LENS_NUTRIENT_PANELS = {
  hefi: {
    label: 'Healthy eating inputs',
    hint: 'Day-level adherence uses these components from Canada\'s Food Guide.',
    patterns: ['ENERGY', 'PROTEIN', 'FAT', 'CARBOHYDRATE', 'FIBRE', 'SODIUM', 'SUGARS', 'SATURATED'],
  },
  hsr: {
    label: 'Star rating inputs',
    hint: 'Packaged-product star rating draws on energy, risk nutrients, and positive nutrients.',
    patterns: ['ENERGY', 'PROTEIN', 'FIBRE', 'SODIUM', 'SUGARS', 'SATURATED', 'CALCIUM'],
  },
  fcs: {
    label: 'Food Compass attributes',
    hint: 'Longer-life eating pattern score looks at nine areas of nutrition; key items shown here.',
    patterns: ['ENERGY', 'PROTEIN', 'FIBRE', 'SODIUM', 'SUGARS', 'SATURATED', 'POTASSIUM', 'MAGNESIUM'],
  },
  heni: {
    label: 'Health impact drivers',
    hint: 'Healthy-life minutes translate diet-related risks; energy and macro profile matter.',
    patterns: ['ENERGY', 'PROTEIN', 'FAT', 'CARBOHYDRATE', 'FIBRE', 'SODIUM', 'SUGARS', 'SATURATED'],
  },
} as const;

export type LensPanelKey = keyof typeof LENS_NUTRIENT_PANELS;

function matchesPattern(name: string, pattern: string): boolean {
  return name.toUpperCase().includes(pattern.toUpperCase());
}

export function findNutrientByPatterns(
  nutrients: NutrientValue[],
  patterns: readonly string[],
): NutrientValue[] {
  const seen = new Set<string>();
  const out: NutrientValue[] = [];
  for (const pattern of patterns) {
    const hit = nutrients.find(n => matchesPattern(n.NutrientName, pattern));
    if (hit && !seen.has(hit.NutrientName)) {
      seen.add(hit.NutrientName);
      out.push(hit);
    }
  }
  return out;
}

export function getEnergyKcal(nutrients: NutrientValue[]): number | null {
  const energy = nutrients.find(n =>
    n.NutrientName.toUpperCase().includes('ENERGY') &&
    (n.NutrientUnit.toUpperCase().includes('KCAL') || n.NutrientName.toUpperCase().includes('KILOCALOR')),
  );
  return energy?.NutrientValue ?? null;
}

/** Per 100 g reference — CNF nutrient values are per 100 g edible portion. */
export const CNF_PER_100G_NOTE =
  'Nutrient values are per 100 g edible portion unless a conversion factor applies.';
