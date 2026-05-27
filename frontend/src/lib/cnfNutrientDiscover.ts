/** Preset nutrient-range queries for CNF discover / compare picker. */
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
