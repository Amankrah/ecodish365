/**
 * Recall-history storage helpers (RECALL-HISTORY-1, 2026-05-24).
 *
 * localStorage-based persistence for 24-h recall days. Per-browser, no auth,
 * no backend storage. Designed to give users a way to actually act on the
 * platform's "log multiple recall days" caveat (HEFI Brassard 2022b; FCS;
 * HENI; DIET-PATTERN-1 single-day disclaimer) without the infrastructure
 * cost of accounts + server-side persistence.
 *
 * Storage schema (versioned at the top, single key):
 *   localStorage['recall_history'] = JSON of `RecallHistoryV1`
 *
 * The data NEVER leaves the user's browser unless they explicitly:
 *   - re-score one or more days (sends `aggregated_daily_ingredients` to
 *     the scoring endpoint, same as the single-day recall wizard does);
 *   - export as JSON / CSV (browser download — local to user);
 *   - import a JSON file (round-trip).
 *
 * Two user audiences benefit:
 *   1. Individual users — see how their pattern varies across the week.
 *   2. Researchers — capture per-subject multi-day recalls, export as
 *      structured JSON/CSV for offline analysis in R / Python / SPSS.
 *
 * Out of scope (handled at the page layer or deferred):
 *   - True NCI multivariate MCMC usual-intake modelling (deferred).
 *   - Auth + backend persistence (deferred).
 *   - Cross-device sync (use export/import as the manual bridge).
 */
import type {
  CNFRecall24hMealResult,
  CNFRecall24hAggregatedIngredient,
} from './api';

export const RECALL_HISTORY_SCHEMA_VERSION = 1;
const STORAGE_KEY = 'recall_history';
// Hard cap below the typical browser quota (~5-10 MB per origin). Leaves
// headroom for other site state. Writes that would exceed this fail with
// a structured error so the UI can surface a "history full" toast.
const MAX_PAYLOAD_BYTES = 4 * 1024 * 1024;

// --- Types ---------------------------------------------------------------

export interface SavedRecallDay {
  /** Stable UUID assigned at save time. Survives label/date edits. */
  id: string;
  /** ISO 8601 date the user logged the day FOR (default: today; user-editable). */
  date: string;               // 'YYYY-MM-DD'
  /** Optional user-supplied label, e.g. 'Subject 04 / Day 2' or 'weekday'. */
  label: string;
  /** ISO timestamp the day was first saved. */
  saved_at: string;
  /** Audience mode at save time (preserved for re-routing). */
  user_type: 'individual' | 'researcher' | 'policy';
  /** Per-meal trace from the recall orchestrator's `meals` field. Includes
   *  occasion, dish_name, total_mass_g, fallback_reason, full ingredient list. */
  meals: CNFRecall24hMealResult[];
  /** The aggregated daily list that gets routed to scoring endpoints. */
  aggregated_daily_ingredients: CNFRecall24hAggregatedIngredient[];
  /** Informational. */
  estimated_daily_kcal: number;
  occasions_count: number;
  /** Optional cached top-pattern snapshot so the list view doesn't re-
   *  classify on every render. Stale if the prototype library changes;
   *  re-classification refreshes it. */
  cached_pattern?: {
    top_pattern: string;
    top_pattern_confidence: 'high' | 'moderate' | 'low';
    cached_at: string;       // ISO timestamp
  };
}

export interface RecallHistoryV1 {
  version: 1;
  exported_from: 'ecodish365';
  exported_at: string;        // ISO timestamp (refreshed on every write)
  days: SavedRecallDay[];
}

export type ImportResult = { added: number; skipped: number; errors: string[] };

// --- Internal helpers ----------------------------------------------------

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof localStorage !== 'undefined';
}

function emptyHistory(): RecallHistoryV1 {
  return {
    version: RECALL_HISTORY_SCHEMA_VERSION,
    exported_from: 'ecodish365',
    exported_at: new Date().toISOString(),
    days: [],
  };
}

function genId(): string {
  // crypto.randomUUID is widely supported (Chrome 92+, Safari 15.4+,
  // Firefox 95+). Fallback for older browsers: timestamp + Math.random.
  try {
    return crypto.randomUUID();
  } catch {
    return `r-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
  }
}

// --- Read ----------------------------------------------------------------

export function loadHistory(): RecallHistoryV1 {
  if (!isBrowser()) return emptyHistory();
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return emptyHistory();
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== 'object') return emptyHistory();
    const p = parsed as Partial<RecallHistoryV1>;
    if (p.version !== RECALL_HISTORY_SCHEMA_VERSION) {
      // Forward-incompatible: refuse to interpret a higher-version blob
      // (we'd silently lose data); refuse to interpret a lower-version
      // blob until a migration function exists. Surface to console for
      // developer visibility; UI handles the empty state.
      console.warn(
        `[recallHistory] unknown schema version ${p.version!}; expected ` +
        `${RECALL_HISTORY_SCHEMA_VERSION}. Returning empty history. ` +
        `User should export the existing data via the import dialog ` +
        `before any data-destructive operation.`,
      );
      return emptyHistory();
    }
    if (!Array.isArray(p.days)) return emptyHistory();
    return {
      version: RECALL_HISTORY_SCHEMA_VERSION,
      exported_from: p.exported_from || 'ecodish365',
      exported_at: p.exported_at || new Date().toISOString(),
      days: p.days as SavedRecallDay[],
    };
  } catch (e) {
    console.warn('[recallHistory] failed to parse localStorage; returning empty', e);
    return emptyHistory();
  }
}

export function listSavedDays(): SavedRecallDay[] {
  // Sorted descending by date (then by saved_at as tiebreaker).
  const days = loadHistory().days;
  return [...days].sort((a, b) => {
    if (a.date !== b.date) return b.date.localeCompare(a.date);
    return b.saved_at.localeCompare(a.saved_at);
  });
}

export function getDay(id: string): SavedRecallDay | null {
  return loadHistory().days.find(d => d.id === id) ?? null;
}

export function countDays(): number {
  return loadHistory().days.length;
}

// --- Write ---------------------------------------------------------------

class QuotaExceededError extends Error {
  constructor(public payloadBytes: number) {
    super(`Recall history would exceed ${MAX_PAYLOAD_BYTES} bytes (current: ${payloadBytes} bytes). Export + clear before saving more.`);
    this.name = 'QuotaExceededError';
  }
}

function persist(history: RecallHistoryV1): void {
  if (!isBrowser()) return;
  history.exported_at = new Date().toISOString();
  const serialised = JSON.stringify(history);
  if (serialised.length > MAX_PAYLOAD_BYTES) {
    throw new QuotaExceededError(serialised.length);
  }
  localStorage.setItem(STORAGE_KEY, serialised);
}

export { QuotaExceededError };

/** Save a new day. Idempotent if a previous save in the same session
 *  registered an `id` in the input — re-saving updates in place. */
export function saveDay(
  input: Omit<SavedRecallDay, 'id' | 'saved_at'> & { id?: string },
): SavedRecallDay {
  const history = loadHistory();
  const now = new Date().toISOString();
  const existingIdx = input.id
    ? history.days.findIndex(d => d.id === input.id)
    : -1;
  const day: SavedRecallDay = {
    id: input.id ?? genId(),
    saved_at: existingIdx >= 0 ? history.days[existingIdx].saved_at : now,
    date: input.date,
    label: input.label,
    user_type: input.user_type,
    meals: input.meals,
    aggregated_daily_ingredients: input.aggregated_daily_ingredients,
    estimated_daily_kcal: input.estimated_daily_kcal,
    occasions_count: input.occasions_count,
    cached_pattern: input.cached_pattern,
  };
  if (existingIdx >= 0) {
    history.days[existingIdx] = day;
  } else {
    history.days.push(day);
  }
  persist(history);
  return day;
}

/** Update a saved day's ingredients, date, and label (clears cached pattern). */
export function updateDayFromEdit(
  id: string,
  patch: {
    date: string;
    label: string;
    ingredients: Array<{
      food_id: number;
      food_description: string;
      food_group?: string;
      mass_g: number;
    }>;
  },
): SavedRecallDay | null {
  const existing = getDay(id);
  if (!existing) return null;

  const byFood = new Map<number, CNFRecall24hAggregatedIngredient>();
  for (const ing of patch.ingredients) {
    if (ing.mass_g <= 0) continue;
    const prev = byFood.get(ing.food_id);
    if (prev) {
      prev.mass_g += ing.mass_g;
    } else {
      byFood.set(ing.food_id, {
        food_id: ing.food_id,
        food_description: ing.food_description,
        food_group: ing.food_group || '',
        mass_g: ing.mass_g,
        occasions: {},
      });
    }
  }
  const aggregated = Array.from(byFood.values()).sort((a, b) => b.mass_g - a.mass_g);
  const totalMass = aggregated.reduce((s, i) => s + i.mass_g, 0);
  const dishName = patch.label.trim() || `Edited recall — ${patch.date}`;

  const meals: CNFRecall24hMealResult[] = [{
    occasion: 'breakfast',
    decomposition: {
      dish_name: dishName,
      normalised_dish_name: dishName.toLowerCase(),
      total_mass_g: totalMass,
      matched: aggregated.length > 0,
      ingredients: aggregated.map(i => ({
        food_id: i.food_id,
        food_description: i.food_description,
        food_group: i.food_group,
        mass_g: i.mass_g,
        rationale: 'user-edited recall day',
        resolution_confidence: 1.0,
      })),
      resolved_mass_g: totalMass,
      unresolved_mass_g: 0,
      decomposition_confidence: 1.0,
      fallback_reason: 'direct_food_entry',
      cache_hit: false,
      timing_ms: 0,
      unresolved_ingredients_audit: [],
    },
  }];

  return saveDay({
    id,
    date: patch.date,
    label: patch.label,
    user_type: existing.user_type,
    meals,
    aggregated_daily_ingredients: aggregated,
    estimated_daily_kcal: existing.estimated_daily_kcal,
    occasions_count: 1,
    cached_pattern: undefined,
  });
}

export function updateDayLabel(id: string, label: string): void {
  const history = loadHistory();
  const idx = history.days.findIndex(d => d.id === id);
  if (idx < 0) return;
  history.days[idx] = { ...history.days[idx], label };
  persist(history);
}

export function updateCachedPattern(
  id: string,
  cached: SavedRecallDay['cached_pattern'],
): void {
  const history = loadHistory();
  const idx = history.days.findIndex(d => d.id === id);
  if (idx < 0) return;
  history.days[idx] = { ...history.days[idx], cached_pattern: cached };
  persist(history);
}

export function deleteDay(id: string): void {
  const history = loadHistory();
  history.days = history.days.filter(d => d.id !== id);
  persist(history);
}

export function clearAllHistory(): void {
  if (!isBrowser()) return;
  localStorage.removeItem(STORAGE_KEY);
}

// --- Multi-day aggregation ----------------------------------------------

/** Concatenate-then-dedupe-by-FoodID-with-mass-sum across N days.
 *
 *  Methodological note: this is volume-weighted across days (a 3000-kcal
 *  day contributes ~3x more to the resulting vector than a 1000-kcal day).
 *  Honest framing: the N-day-average view's caption + caveat explicitly
 *  say "N-day average" (no claim of equal weighting). Per-day-vector
 *  averaging is a v2 candidate; for now the cosine-to-prototype is
 *  interpretable either way (it captures the directional intent — what
 *  food signature your week looked like — rather than a statistical
 *  usual-intake estimate).
 */
export function combineDays(
  days: SavedRecallDay[],
): CNFRecall24hAggregatedIngredient[] {
  const byFoodId: Record<number, CNFRecall24hAggregatedIngredient> = {};
  for (const day of days) {
    for (const ing of day.aggregated_daily_ingredients) {
      const existing = byFoodId[ing.food_id];
      if (existing) {
        existing.mass_g += ing.mass_g;
        // Per-occasion attribution is dropped at the N-day level — it's
        // not meaningful across days. (A day's per-occasion attribution
        // is still preserved inside `day.meals`.)
        existing.occasions = {};
      } else {
        byFoodId[ing.food_id] = {
          ...ing,
          occasions: {},   // see comment above
        };
      }
    }
  }
  return Object.values(byFoodId).sort((a, b) => b.mass_g - a.mass_g);
}

// --- Export / import ----------------------------------------------------

export function exportAsJSON(): string {
  const history = loadHistory();
  history.exported_at = new Date().toISOString();
  return JSON.stringify(history, null, 2);
}

/** Per-ingredient flat CSV — one row per (day, meal, ingredient) tuple.
 *  RFC 4180 quoting. Suitable for pandas / R / SPSS direct import. */
export function exportAsCSV(): string {
  const days = loadHistory().days;
  const cols = [
    'day_id', 'date', 'label', 'user_type',
    'occasion', 'dish_name', 'total_mass_g',
    'food_id', 'food_description', 'food_group', 'mass_g', 'source',
  ];
  const rows: string[] = [cols.join(',')];
  const esc = (v: unknown): string => {
    const s = v === null || v === undefined ? '' : String(v);
    // RFC 4180: wrap in quotes if contains comma, quote, newline; escape quotes by doubling.
    if (/[",\r\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  };
  for (const day of days) {
    for (const meal of day.meals) {
      for (const ing of meal.decomposition.ingredients) {
        const source = ing.food_id >= 700_000 ? 'wafct' : 'cnf';
        rows.push([
          day.id, day.date, day.label, day.user_type,
          meal.occasion, meal.decomposition.dish_name, meal.decomposition.total_mass_g,
          ing.food_id, ing.food_description, ing.food_group, ing.mass_g, source,
        ].map(esc).join(','));
      }
    }
  }
  return rows.join('\r\n') + '\r\n';
}

/** Validate + merge an imported JSON blob into existing localStorage.
 *  Dedupes by (date + label) — a day with the same date AND label as an
 *  existing day is skipped (NOT overwritten). Returns counts + per-day
 *  validation errors. */
export function importFromJSON(raw: string): ImportResult {
  const result: ImportResult = { added: 0, skipped: 0, errors: [] };
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch (e) {
    result.errors.push(`JSON parse failed: ${(e as Error).message}`);
    return result;
  }
  if (!parsed || typeof parsed !== 'object') {
    result.errors.push('Top-level value is not an object.');
    return result;
  }
  const p = parsed as Partial<RecallHistoryV1>;
  if (p.version !== RECALL_HISTORY_SCHEMA_VERSION) {
    result.errors.push(
      `Schema version ${p.version} not supported (expected ${RECALL_HISTORY_SCHEMA_VERSION}).`,
    );
    return result;
  }
  if (!Array.isArray(p.days)) {
    result.errors.push('Missing or invalid "days" array.');
    return result;
  }
  const history = loadHistory();
  const existingKeys = new Set(history.days.map(d => `${d.date}::${d.label}`));
  for (let i = 0; i < p.days.length; i++) {
    const d = p.days[i] as Partial<SavedRecallDay>;
    // Minimal shape validation.
    if (!d.date || !Array.isArray(d.meals)
        || !Array.isArray(d.aggregated_daily_ingredients)) {
      result.errors.push(`Day ${i}: missing required fields (date / meals / ingredients).`);
      continue;
    }
    const key = `${d.date}::${d.label ?? ''}`;
    if (existingKeys.has(key)) {
      result.skipped += 1;
      continue;
    }
    // Re-assign id so an imported day never clashes with an existing UUID.
    history.days.push({
      id: genId(),
      saved_at: d.saved_at || new Date().toISOString(),
      date: d.date,
      label: d.label || '',
      user_type: (d.user_type as SavedRecallDay['user_type']) || 'individual',
      meals: d.meals as CNFRecall24hMealResult[],
      aggregated_daily_ingredients:
        d.aggregated_daily_ingredients as CNFRecall24hAggregatedIngredient[],
      estimated_daily_kcal: d.estimated_daily_kcal ?? 0,
      occasions_count: d.occasions_count ?? d.meals.length,
      cached_pattern: d.cached_pattern,
    });
    existingKeys.add(key);
    result.added += 1;
  }
  if (result.added > 0) {
    try {
      persist(history);
    } catch (e) {
      result.errors.push(`Quota exceeded mid-import: ${(e as Error).message}`);
    }
  }
  return result;
}

// --- Cross-tab sync -----------------------------------------------------

/** Subscribe to history changes from OTHER tabs (the browser native
 *  `storage` event only fires in tabs OTHER than the one that wrote). Returns
 *  an unsubscribe function. */
export function subscribe(listener: () => void): () => void {
  if (!isBrowser()) return () => undefined;
  const handler = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY || e.key === null) {
      listener();
    }
  };
  window.addEventListener('storage', handler);
  return () => window.removeEventListener('storage', handler);
}

// --- Display helpers (improve-product, scorecard pickers) -----------------

/** Human-readable title for a saved recall day. */
export function recallDayDisplayTitle(day: SavedRecallDay): string {
  const label = day.label?.trim();
  if (label) return label;
  const mealNames = day.meals
    .map(m => m.decomposition?.dish_name?.trim())
    .filter((n): n is string => Boolean(n));
  if (mealNames.length === 1) return mealNames[0];
  if (mealNames.length > 1) return `${day.date} · ${mealNames.length} meals`;
  return `24-h recall — ${day.date}`;
}

/** Best dish name for WAFCT/substitution context (largest meal by mass). */
export function recallDaySubstitutionDishName(day: SavedRecallDay): string {
  let best = '';
  let bestMass = -1;
  for (const m of day.meals) {
    const mass = m.decomposition?.total_mass_g ?? 0;
    const name = m.decomposition?.dish_name?.trim() ?? '';
    if (name && mass > bestMass) {
      bestMass = mass;
      best = name;
    }
  }
  return best || recallDayDisplayTitle(day);
}

/** Ingredient rows for substitution UIs. */
export function recallDayToIngredientRows(
  day: SavedRecallDay,
): Array<{ food_id: number; food_description: string; mass_g: number; food_group?: string }> {
  return day.aggregated_daily_ingredients.map(i => ({
    food_id: i.food_id,
    food_description: i.food_description,
    mass_g: i.mass_g,
    food_group: i.food_group || undefined,
  }));
}

/** Minimal recall-export blob for POST /api/substitution/improve-plan/. */
export function buildImprovePlanRecallExport(days: SavedRecallDay[]): RecallHistoryV1 {
  return {
    version: RECALL_HISTORY_SCHEMA_VERSION,
    exported_from: 'ecodish365',
    exported_at: new Date().toISOString(),
    days,
  };
}

// --- Browser download helper --------------------------------------------

/** Trigger a download of `content` as `filename` with the given MIME type.
 *  No external dependency; uses Blob + URL.createObjectURL + transient <a>. */
export function downloadFile(content: string, filename: string, mime: string): void {
  if (!isBrowser()) return;
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  // Defer revoke so Firefox finishes the download before the URL is freed.
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
