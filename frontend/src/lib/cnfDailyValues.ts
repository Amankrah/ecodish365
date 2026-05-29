/**
 * Health Canada % Daily Value (%DV) reference, keyed by CNF NutrientID.
 *
 * The values now live in a single committed data file, cnfDailyValues.data.json,
 * which is byte-mirrored by backend/api/data/cnf_daily_values.json so the frontend
 * %DV display and the backend %DV-threshold filtering can never drift. A backend
 * parity test pins the two `values` maps equal.
 *
 * Source: Health Canada — "Nutrition labelling: Table of daily values" (canada.ca),
 * published 2022-10-20. In-force table (the 2016-12-14 version sunset 2025-12-31).
 * Adult / general-population column: Part 1 "Column 3" for macronutrients + sodium,
 * Part 2 "Column 4" ("any other case") for vitamins and minerals. Vitamin forms follow
 * Food and Drug Regulations D.01.003 (Vitamin A = RAE 320, Vitamin D = D2 + D3 µg 328,
 * Vitamin E = α-tocopherol 323, Niacin = NE 409, Folate = DFE 435).
 *
 * Deliberately NOT included: cholesterol (601, no %DV on Canadian labels), protein and
 * total carbohydrate (no Canadian %DV), iodide / chromium / molybdenum / chloride
 * (absent from CNF). See the data file's _provenance for the full note.
 *
 * %DV is computed against the per-100 g value (or per serving, if scaled upstream):
 *   %DV = nutrient_amount / daily_value × 100
 * The NutrientID fixes the unit, so the amount and the DV are always in the same unit.
 */
import dvData from './cnfDailyValues.data.json';

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

interface RawDailyValue {
  dv: number;
  unit: string;
  label: string;
  sum_with_nutrient_id?: number;
}

export const CNF_DAILY_VALUES: Record<number, CnfDailyValue> = Object.fromEntries(
  Object.entries(dvData.values as Record<string, RawDailyValue>).map(([id, v]) => [
    Number(id),
    {
      dv: v.dv,
      unit: v.unit as CnfDailyValue['unit'],
      label: v.label,
      ...(v.sum_with_nutrient_id != null ? { sumWithNutrientId: v.sum_with_nutrient_id } : {}),
    },
  ]),
);

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
