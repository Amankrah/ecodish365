/**
 * Logical grouping of the ~173 CNF NutrientIDs for the Discover-by-nutrient workbench.
 *
 * The flat alphabetical nutrient list is unusable for research: a dietitian scanning for
 * "the trace elements" or "the fat-soluble vitamins" should see them together. We assign
 * every nutrient to exactly one ordered group. Assignment is by explicit NutrientID set
 * for the curated groups, then by name predicate for the two large families (amino acids,
 * fatty acids and sterols), then a small bioactives / other catch-all. A completeness
 * test (frontend nutrient list vs these groups) asserts nothing is left unmapped.
 */
import type { Nutrient } from './api';

export interface NutrientGroup {
  key: string;
  label: string;
  /** One-line description for the section header / tooltip. */
  description: string;
  /** Explicit NutrientIDs that belong here (checked first, in order). */
  ids?: number[];
  /** Fallback predicate for families too large to enumerate (checked after ids). */
  match?: (id: number, upperName: string) => boolean;
}

/**
 * Ordered groups. Order is both the assignment priority and the display order, so the
 * macronutrients lead and the long fatty-acid tail sits near the end.
 */
export const NUTRIENT_GROUPS: NutrientGroup[] = [
  {
    key: 'macro',
    label: 'Energy & macronutrients',
    description: 'Energy, protein, fat, carbohydrate, fibre, water, ash, alcohol.',
    ids: [208, 268, 203, 204, 205, 291, 255, 207, 221],
  },
  {
    key: 'sugars',
    label: 'Sugars & carbohydrate detail',
    description: 'Total sugars, the individual mono- and disaccharides, sugar alcohols, and fructans.',
    ids: [269, 210, 211, 212, 213, 214, 287, 260, 261, 1001],
  },
  {
    key: 'minerals',
    label: 'Major minerals',
    description: 'Calcium, iron, magnesium, phosphorus, potassium, sodium, zinc.',
    ids: [301, 303, 304, 305, 306, 307, 309],
  },
  {
    key: 'trace',
    label: 'Trace elements',
    description: 'Copper, manganese, selenium.',
    ids: [312, 315, 317],
  },
  {
    key: 'vit_fat',
    label: 'Fat-soluble vitamins',
    description: 'Vitamin A and carotenoids, vitamin D, vitamin E (tocopherols), vitamin K.',
    ids: [319, 320, 321, 322, 334, 337, 338, 324, 325, 326, 328, 329, 330, 323, 341, 342, 343, 573, 428, 429, 430],
  },
  {
    key: 'vit_water',
    label: 'Water-soluble vitamins',
    description: 'Vitamin C, the B vitamins, folate forms, choline, betaine.',
    ids: [401, 404, 405, 406, 409, 410, 415, 416, 417, 418, 421, 431, 432, 435, 454, 578],
  },
  {
    key: 'amino',
    label: 'Amino acids',
    description: 'The individual amino acids reported by the CNF.',
    match: (id) => id >= 501 && id <= 521,
  },
  {
    key: 'fatty',
    label: 'Fatty acids & sterols',
    description: 'Saturated, mono- and polyunsaturated, and trans fatty acids; cholesterol and plant sterols.',
    match: (id, name) => id === 601 || name.startsWith('FATTY ACIDS') || name.includes('STEROL'),
  },
  {
    key: 'other',
    label: 'Other & bioactives',
    description: 'Caffeine, theobromine, and other components that fall outside the groups above.',
    // Catch-all: anything not matched above (caffeine 262, theobromine 263, aspartame 550, ...).
    match: () => true,
  },
];

const _GROUP_BY_KEY: Record<string, NutrientGroup> =
  Object.fromEntries(NUTRIENT_GROUPS.map((g) => [g.key, g]));

/** Group key for a single nutrient (first matching group in NUTRIENT_GROUPS order). */
export function groupKeyForNutrient(n: Pick<Nutrient, 'NutrientID' | 'NutrientName'>): string {
  const id = n.NutrientID;
  const upper = (n.NutrientName || '').toUpperCase();
  for (const g of NUTRIENT_GROUPS) {
    if (g.ids && g.ids.includes(id)) return g.key;
    if (g.match && g.match(id, upper)) return g.key;
  }
  return 'other';
}

export interface GroupedNutrients {
  group: NutrientGroup;
  nutrients: Nutrient[];
}

/**
 * Partition a nutrient list into the ordered groups, dropping empty groups. Within each
 * group, nutrients keep the order they were assigned (explicit-id groups follow the id
 * order; predicate groups follow the input order).
 */
export function groupNutrients(nutrients: Nutrient[]): GroupedNutrients[] {
  const buckets: Record<string, Nutrient[]> = {};
  for (const g of NUTRIENT_GROUPS) buckets[g.key] = [];
  for (const n of nutrients) buckets[groupKeyForNutrient(n)].push(n);
  // For explicit-id groups, sort members by their position in the id list so the picker
  // reads in a sensible nutritional order (energy first, then protein, fat, ...).
  for (const g of NUTRIENT_GROUPS) {
    if (g.ids) {
      const order = new Map(g.ids.map((id, i) => [id, i]));
      buckets[g.key].sort((a, b) => (order.get(a.NutrientID) ?? 999) - (order.get(b.NutrientID) ?? 999));
    }
  }
  return NUTRIENT_GROUPS
    .filter((g) => buckets[g.key].length > 0)
    .map((g) => ({ group: g, nutrients: buckets[g.key] }));
}

export function groupLabel(key: string): string {
  return _GROUP_BY_KEY[key]?.label ?? 'Other';
}
