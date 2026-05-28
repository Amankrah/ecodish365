/**
 * Health Canada % Daily Value (%DV) reference, keyed by CNF NutrientID.
 *
 * Source: Health Canada — "Nutrition labelling: Table of daily values" (canada.ca),
 * published 2022-10-20. This is the in-force table: the previous 2016-12-14 version
 * sunset on 2025-12-31. We use the adult / general-population column — Part 1
 * "Column 3" for macronutrients + sodium, and Part 2 "Column 4" ("any other case")
 * for vitamins and minerals.
 *
 * Per the table, calculations for vitamins follow Food and Drug Regulations D.01.003,
 * which fixes the form each DV is expressed in. The CNF NutrientID we map to therefore
 * matches that form: Vitamin A = Retinol Activity Equivalents (320), Vitamin D =
 * D2 + D3 in µg (328, not the IU entry 324), Vitamin E = α-tocopherol (323), Niacin =
 * niacin equivalents (409), Folate = Dietary Folate Equivalents (435, not total folacin).
 *
 * Deliberately NOT included:
 *  - Cholesterol (601): the table lists a 300 mg DV, but Canadian Nutrition Facts
 *    tables show cholesterol as an amount only, with no %DV. We follow the label.
 *  - Protein and total carbohydrate: Canada assigns no %DV to either (a carbohydrate
 *    DV exists only in the US system).
 *  - Iodide, chromium, molybdenum, chloride: the CNF does not carry these nutrients,
 *    so there is nothing to compute a %DV against.
 *
 * %DV is computed against the per-100 g value (or per serving, if scaled upstream):
 *   %DV = nutrient_amount / daily_value × 100
 * The NutrientID fixes the unit, so the amount and the DV are always in the same unit.
 */
export interface CnfDailyValue {
  /** Daily Value amount, in `unit`. */
  dv: number;
  /** Unit the DV (and the matching CNF nutrient) is expressed in. */
  unit: 'g' | 'mg' | 'µg';
  /** Short label for tooltips. */
  label: string;
  /**
   * Saturated fat's %DV is computed against the sum of saturated + trans fat.
   * On NutrientID 606 (saturated) this points to 605 (trans) so the numerator is summed.
   */
  sumWithNutrientId?: number;
}

export const CNF_DAILY_VALUES: Record<number, CnfDailyValue> = {
  // Part 1 — macronutrients + sodium (Column 3, adults)
  204: { dv: 75, unit: 'g', label: 'Fat' },
  606: { dv: 20, unit: 'g', label: 'Saturated + trans fat', sumWithNutrientId: 605 },
  291: { dv: 28, unit: 'g', label: 'Fibre' },
  269: { dv: 100, unit: 'g', label: 'Sugars' },
  307: { dv: 2300, unit: 'mg', label: 'Sodium' },
  // Part 2 — vitamins + minerals (Column 4, "any other case")
  306: { dv: 3400, unit: 'mg', label: 'Potassium' },
  301: { dv: 1300, unit: 'mg', label: 'Calcium' },
  303: { dv: 18, unit: 'mg', label: 'Iron' },
  320: { dv: 900, unit: 'µg', label: 'Vitamin A (RAE)' },
  401: { dv: 90, unit: 'mg', label: 'Vitamin C' },
  328: { dv: 20, unit: 'µg', label: 'Vitamin D' },
  323: { dv: 15, unit: 'mg', label: 'Vitamin E (α-tocopherol)' },
  430: { dv: 120, unit: 'µg', label: 'Vitamin K' },
  404: { dv: 1.2, unit: 'mg', label: 'Thiamin' },
  405: { dv: 1.3, unit: 'mg', label: 'Riboflavin' },
  409: { dv: 16, unit: 'mg', label: 'Niacin (NE)' },
  415: { dv: 1.7, unit: 'mg', label: 'Vitamin B6' },
  435: { dv: 400, unit: 'µg', label: 'Folate (DFE)' },
  418: { dv: 2.4, unit: 'µg', label: 'Vitamin B12' },
  421: { dv: 550, unit: 'mg', label: 'Choline' },
  416: { dv: 30, unit: 'µg', label: 'Biotin' },
  410: { dv: 5, unit: 'mg', label: 'Pantothenic acid' },
  305: { dv: 1250, unit: 'mg', label: 'Phosphorus' },
  304: { dv: 420, unit: 'mg', label: 'Magnesium' },
  309: { dv: 11, unit: 'mg', label: 'Zinc' },
  317: { dv: 55, unit: 'µg', label: 'Selenium' },
  312: { dv: 0.9, unit: 'mg', label: 'Copper' },
  315: { dv: 2.3, unit: 'mg', label: 'Manganese' },
};

/**
 * Compute %DV for one nutrient amount, or null when the nutrient has no Health Canada DV.
 * `lookupOtherById` supplies the trans-fat value when summing saturated + trans.
 */
export function percentDV(
  nutrientId: number,
  amount: number,
  lookupOtherById?: (nutrientId: number) => number | null,
): number | null {
  const entry = CNF_DAILY_VALUES[nutrientId];
  if (!entry || !(entry.dv > 0) || !Number.isFinite(amount)) return null;
  let numerator = amount;
  if (entry.sumWithNutrientId != null && lookupOtherById) {
    const other = lookupOtherById(entry.sumWithNutrientId);
    if (other != null && Number.isFinite(other)) numerator += other;
  }
  return (numerator / entry.dv) * 100;
}
