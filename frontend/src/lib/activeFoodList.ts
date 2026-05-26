/**
 * activeFoodList — localStorage-backed "current food list" that persists across
 * page navigations so users can transfer one list between scoring metrics
 * (HEFI / HENI / HSR / FCS / environmental / dietary-pattern) without
 * re-entering or re-decomposing.
 *
 * Companion to `useRecall24hReceiver` (which is sessionStorage + URL-marker
 * one-shot delivery). After the receiver fires on a scorer page, the active
 * list is mirrored here so the user can later cross-transfer.
 *
 * Storage shape (versioned for forward compatibility):
 *
 *   {
 *     schema_version: 1,
 *     captured_at: ISO,
 *     source: 'recall_24h' | 'packaged_food_inferred' | 'imported' | 'manual',
 *     ingredients: [{ food_id, food_description, food_group?, mass_g }],
 *     estimated_daily_kcal?: number,
 *     packaged_food?: { provenance: 'packaged_food_inferred', product_name, brand,
 *                       net_weight_g, decomposition_confidence, image_sha256 },
 *     packaged_food_occasions?: [{ occasion, product_name, brand, decomposition_confidence }],
 *     multi_day?: { n_days, first_date, last_date, label, day_ids },
 *     meals_meta?: [{ occasion, dish_name, total_mass_g }],
 *     user_type?: 'individual' | 'researcher' | 'policy',
 *   }
 *
 * Export format is a SUBSET of the storage shape — only fields the user
 * needs to reproduce the same scoring run. Notably the export drops the
 * sessionStorage-style routing metadata (target) and keeps food_id +
 * mass_g as the canonical exchange.
 */

import type { CNFRecall24hAggregatedIngredient, RecallOccasion } from './api';

const STORAGE_KEY = 'active_food_list_v1';
const COLLAPSED_KEY = 'active_food_list_panel_collapsed_v1';

export const ACTIVE_FOOD_LIST_SCHEMA_VERSION = 1;

export type ActiveFoodListSource =
  | 'recall_24h'
  | 'packaged_food_inferred'
  | 'imported'
  | 'manual';

export interface ActiveFoodListIngredient {
  food_id: number;
  food_description: string;
  food_group?: string;
  mass_g: number;
}

export interface ActiveFoodListPackagedMeta {
  provenance: 'packaged_food_inferred';
  product_name: string | null;
  brand: string | null;
  net_weight_g: number;
  decomposition_confidence: number;
  image_sha256: string;
}

export interface ActiveFoodListPackagedOccasion {
  occasion: string;
  product_name: string | null;
  brand: string | null;
  decomposition_confidence: number;
}

export interface ActiveFoodListMultiDay {
  n_days: number;
  first_date: string;
  last_date: string;
  label: string;
  day_ids: string[];
}

export interface ActiveFoodListMealMeta {
  occasion: string;
  dish_name: string;
  total_mass_g: number;
}

export interface ActiveFoodList {
  schema_version: number;
  captured_at: string;
  source: ActiveFoodListSource;
  ingredients: ActiveFoodListIngredient[];
  estimated_daily_kcal?: number;
  user_type?: 'individual' | 'researcher' | 'policy';
  meals_meta?: ActiveFoodListMealMeta[];
  packaged_food?: ActiveFoodListPackagedMeta;
  packaged_food_occasions?: ActiveFoodListPackagedOccasion[];
  multi_day?: ActiveFoodListMultiDay;
}

/** Custom event name emitted on window when the active list changes.
 *  Components listen to this to re-render across tabs and within the same tab. */
export const ACTIVE_FOOD_LIST_EVENT = 'active-food-list:changed';

function safeGet(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function safeSet(value: string): boolean {
  if (typeof window === 'undefined') return false;
  try {
    window.localStorage.setItem(STORAGE_KEY, value);
    return true;
  } catch {
    return false;
  }
}

function safeRemove(): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch { /* ignore */ }
}

function emitChange(next: ActiveFoodList | null): void {
  if (typeof window === 'undefined') return;
  try {
    window.dispatchEvent(new CustomEvent<ActiveFoodList | null>(
      ACTIVE_FOOD_LIST_EVENT, { detail: next },
    ));
  } catch { /* ignore */ }
}

export function loadActiveFoodList(): ActiveFoodList | null {
  const raw = safeGet();
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    return validateAndCoerce(parsed);
  } catch {
    return null;
  }
}

export function saveActiveFoodList(list: ActiveFoodList): boolean {
  const coerced: ActiveFoodList = {
    ...list,
    schema_version: ACTIVE_FOOD_LIST_SCHEMA_VERSION,
    captured_at: list.captured_at || new Date().toISOString(),
    ingredients: list.ingredients.map(i => ({
      food_id: Number(i.food_id),
      food_description: String(i.food_description),
      food_group: i.food_group,
      mass_g: Math.max(0, Number(i.mass_g) || 0),
    })),
  };
  const ok = safeSet(JSON.stringify(coerced));
  if (ok) emitChange(coerced);
  return ok;
}

export function clearActiveFoodList(): void {
  safeRemove();
  emitChange(null);
}

export function updateIngredientMass(food_id: number, mass_g: number): ActiveFoodList | null {
  const current = loadActiveFoodList();
  if (!current) return null;
  const next: ActiveFoodList = {
    ...current,
    ingredients: current.ingredients.map(i =>
      i.food_id === food_id ? { ...i, mass_g: Math.max(0, mass_g) } : i,
    ),
  };
  saveActiveFoodList(next);
  return next;
}

export function removeIngredient(food_id: number): ActiveFoodList | null {
  const current = loadActiveFoodList();
  if (!current) return null;
  const next: ActiveFoodList = {
    ...current,
    ingredients: current.ingredients.filter(i => i.food_id !== food_id),
  };
  if (next.ingredients.length === 0) {
    clearActiveFoodList();
    return null;
  }
  saveActiveFoodList(next);
  return next;
}

/** Minimal shape the helper actually reads off each ingredient. Loose enough
 *  to accept the recall-24h aggregated shape AND the packaged-food
 *  composition shape (which uses a non-RecallOccasion key in `occasions`). */
interface IngredientLike {
  food_id: number;
  food_description: string;
  food_group?: string;
  mass_g: number;
}

/** Build an active list from a recall-24h aggregated payload (the canonical
 *  upstream shape). Used by the receiver hook and the wizard route handler. */
export function fromRecallAggregated(
  ingredients: IngredientLike[],
  opts: {
    estimated_daily_kcal?: number;
    user_type?: ActiveFoodList['user_type'];
    meals_meta?: Array<{ occasion: RecallOccasion | string; dish_name: string; total_mass_g: number }>;
    packaged_food?: ActiveFoodListPackagedMeta;
    packaged_food_occasions?: ActiveFoodListPackagedOccasion[];
    multi_day?: ActiveFoodListMultiDay;
  } = {},
): ActiveFoodList {
  return {
    schema_version: ACTIVE_FOOD_LIST_SCHEMA_VERSION,
    captured_at: new Date().toISOString(),
    source: opts.packaged_food ? 'packaged_food_inferred' : 'recall_24h',
    ingredients: ingredients.map(i => ({
      food_id: i.food_id,
      food_description: i.food_description,
      food_group: i.food_group,
      mass_g: i.mass_g,
    })),
    estimated_daily_kcal: opts.estimated_daily_kcal,
    user_type: opts.user_type,
    meals_meta: opts.meals_meta?.map(m => ({
      occasion: String(m.occasion),
      dish_name: m.dish_name,
      total_mass_g: m.total_mass_g,
    })),
    packaged_food: opts.packaged_food,
    packaged_food_occasions: opts.packaged_food_occasions,
    multi_day: opts.multi_day,
  };
}

/** Reshape the active list back into the aggregated-ingredient shape the
 *  scorer pages and `useRecall24hReceiver` already consume. */
export function toAggregatedIngredients(
  list: ActiveFoodList,
): CNFRecall24hAggregatedIngredient[] {
  return list.ingredients.map(i => ({
    food_id: i.food_id,
    food_description: i.food_description,
    food_group: i.food_group ?? '',
    mass_g: i.mass_g,
    occasions: {},
  }));
}

// --- Export / Import ------------------------------------------------------

export interface ExportedFoodList {
  schema_version: number;
  captured_at: string;
  source: ActiveFoodListSource;
  // Quantities are in grams (mass_g) — the canonical CNF unit; all scorers
  // accept this regardless of metric.
  ingredients: ActiveFoodListIngredient[];
  estimated_daily_kcal?: number;
  packaged_food?: ActiveFoodListPackagedMeta;
  packaged_food_occasions?: ActiveFoodListPackagedOccasion[];
  multi_day?: ActiveFoodListMultiDay;
  meals_meta?: ActiveFoodListMealMeta[];
  // Note: user_type is intentionally OMITTED on export — a saved list is
  // not specific to one audience mode, and importing into a different mode
  // should be honored.
  exported_by: 'ecodish365';
  exported_at: string;
}

export function exportToJSONString(list: ActiveFoodList): string {
  const out: ExportedFoodList = {
    schema_version: list.schema_version,
    captured_at: list.captured_at,
    source: list.source,
    ingredients: list.ingredients,
    estimated_daily_kcal: list.estimated_daily_kcal,
    packaged_food: list.packaged_food,
    packaged_food_occasions: list.packaged_food_occasions,
    multi_day: list.multi_day,
    meals_meta: list.meals_meta,
    exported_by: 'ecodish365',
    exported_at: new Date().toISOString(),
  };
  return JSON.stringify(out, null, 2);
}

export function exportFilename(list: ActiveFoodList): string {
  const date = (list.captured_at || new Date().toISOString()).slice(0, 10);
  const kind = list.source === 'packaged_food_inferred' ? 'packaged' : 'recall';
  return `ecodish365-foodlist-${kind}-${date}.json`;
}

export interface ImportResult {
  ok: boolean;
  list?: ActiveFoodList;
  error?: string;
}

export function importFromJSONString(raw: string): ImportResult {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch (e) {
    return { ok: false, error: `Invalid JSON: ${(e as Error).message}` };
  }
  const validated = validateAndCoerce(parsed);
  if (!validated) {
    return {
      ok: false,
      error: 'Not a valid ecodish365 food list. Expected an object with an "ingredients" array of {food_id, food_description, mass_g}.',
    };
  }
  // Mark imports so the panel can show provenance.
  if (validated.source !== 'packaged_food_inferred') {
    validated.source = 'imported';
  }
  validated.captured_at = new Date().toISOString();
  return { ok: true, list: validated };
}

function validateAndCoerce(parsed: unknown): ActiveFoodList | null {
  if (!parsed || typeof parsed !== 'object') return null;
  const obj = parsed as Record<string, unknown>;
  const ingredientsRaw = obj.ingredients;
  if (!Array.isArray(ingredientsRaw) || ingredientsRaw.length === 0) return null;

  const ingredients: ActiveFoodListIngredient[] = [];
  for (const rawItem of ingredientsRaw) {
    if (!rawItem || typeof rawItem !== 'object') return null;
    const item = rawItem as Record<string, unknown>;
    const food_id = Number(item.food_id);
    const mass_g = Number(item.mass_g);
    const food_description = String(item.food_description ?? '');
    if (!Number.isFinite(food_id) || food_id <= 0) return null;
    if (!Number.isFinite(mass_g) || mass_g < 0) return null;
    if (!food_description.trim()) return null;
    ingredients.push({
      food_id,
      food_description,
      food_group: typeof item.food_group === 'string' ? item.food_group : undefined,
      mass_g,
    });
  }

  const source = typeof obj.source === 'string'
    && ['recall_24h', 'packaged_food_inferred', 'imported', 'manual'].includes(obj.source)
    ? (obj.source as ActiveFoodListSource)
    : 'imported';

  return {
    schema_version: ACTIVE_FOOD_LIST_SCHEMA_VERSION,
    captured_at: typeof obj.captured_at === 'string' ? obj.captured_at : new Date().toISOString(),
    source,
    ingredients,
    estimated_daily_kcal: typeof obj.estimated_daily_kcal === 'number'
      ? obj.estimated_daily_kcal : undefined,
    user_type: ['individual', 'researcher', 'policy'].includes(obj.user_type as string)
      ? (obj.user_type as ActiveFoodList['user_type']) : undefined,
    meals_meta: Array.isArray(obj.meals_meta) ? obj.meals_meta as ActiveFoodList['meals_meta'] : undefined,
    packaged_food: typeof obj.packaged_food === 'object' && obj.packaged_food !== null
      ? obj.packaged_food as ActiveFoodListPackagedMeta : undefined,
    packaged_food_occasions: Array.isArray(obj.packaged_food_occasions)
      ? obj.packaged_food_occasions as ActiveFoodListPackagedOccasion[] : undefined,
    multi_day: typeof obj.multi_day === 'object' && obj.multi_day !== null
      ? obj.multi_day as ActiveFoodListMultiDay : undefined,
  };
}

// --- Collapse state -------------------------------------------------------

export function loadPanelCollapsed(): boolean {
  if (typeof window === 'undefined') return false;
  try {
    return window.localStorage.getItem(COLLAPSED_KEY) === '1';
  } catch {
    return false;
  }
}

export function savePanelCollapsed(collapsed: boolean): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(COLLAPSED_KEY, collapsed ? '1' : '0');
  } catch { /* ignore */ }
}
