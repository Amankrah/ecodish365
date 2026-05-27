/**
 * foodProfileOrchestrator — client-side fan-out over the 6 existing scorer
 * endpoints. The Scorecard page calls `runAllScorers(ingredients, opts)`
 * once on the user's explicit "Score all" click, the orchestrator fires
 * all six API services in parallel via `Promise.allSettled`, and returns
 * a keyed object with one `MetricOutcome` per metric.
 *
 * No backend code — the per-scorer endpoints remain the single source of
 * truth. Caching is per-input (FNV-1a hash of {sorted (food_id, rounded
 * mass_g), userType, decompositionProvenance, multiDayLabel}) and mirrored
 * to sessionStorage so a bounce to /hefi/calculate and back doesn't re-bill.
 */

import {
  CNFApiService,
  HEFIApiService,
  HENIApiService,
  HSRApiService,
  FCSApiService,
  EnvironmentalImpactApiService,
  type HEFIResult,
  type HENIResult,
  type HSRResult,
  type FCSResult,
  type EnvironmentalImpactResult,
  type PatternClassifyResponse,
} from './api';
import type { UserType, ExplanationsBlock } from '@/components/shared/AudienceToggle';

export type MetricKey =
  | 'hefi'
  | 'heni'
  | 'hsr'
  | 'fcs'
  | 'environmental'
  | 'dietary_pattern';

export interface ScorerInput {
  food_id: number;
  mass_g: number;
  food_description: string;
}

export interface RunOptions {
  userType: UserType;
  /** When the active list came from a packaged-food decomposition, the
   *  dietary-pattern endpoint swaps its caveat language. Forwarded only
   *  to the dietary-pattern call. */
  decompositionProvenance?: 'packaged_food_inferred';
  /** N-day average label (e.g. "5-day average, 2026-05-17 to 2026-05-21").
   *  Same dietary-pattern caveat swap as above. */
  multiDayLabel?: string;
  /** Mirror the /environmental/calculate page default. */
  enableLcaMatcher?: boolean;
}

export type MetricOutcome<T> =
  | {
      status: 'fulfilled';
      metric: MetricKey;
      result: T;
      explanations?: ExplanationsBlock;
      cachedAt: string;
    }
  | {
      status: 'rejected';
      metric: MetricKey;
      reason: string;
      cachedAt: string;
    }
  | {
      status: 'skipped';
      metric: MetricKey;
      reason: string;
    };

export interface ProfileResults {
  hefi: MetricOutcome<HEFIResult>;
  heni: MetricOutcome<HENIResult>;
  hsr: MetricOutcome<HSRResult>;
  fcs: MetricOutcome<{ data: FCSResult }>;
  environmental: MetricOutcome<EnvironmentalImpactResult>;
  dietary_pattern: MetricOutcome<PatternClassifyResponse>;
}

// --- Caching --------------------------------------------------------------

// v3: bumped 2026-05-26 after FCS multi-food aggregation + adapter parse fix.
const CACHE_PREFIX = 'scorecard_cache_v3:';
const memoryCache = new Map<string, ProfileResults>();

/** FNV-1a 32-bit hash, hex-encoded. Tiny, dependency-free, sufficient for
 *  cache-key collision avoidance over short inputs. */
function fnv1a(input: string): string {
  let h = 0x811c9dc5;
  for (let i = 0; i < input.length; i += 1) {
    h ^= input.charCodeAt(i);
    h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) >>> 0;
  }
  return h.toString(16).padStart(8, '0');
}

function hashInputs(ingredients: ScorerInput[], opts: RunOptions): string {
  const norm = ingredients
    .map(i => [Number(i.food_id), Math.round(Number(i.mass_g))])
    .filter(([id, m]) => Number.isFinite(id) && id > 0 && Number.isFinite(m) && m >= 0)
    .sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const payload = JSON.stringify({
    n: norm,
    u: opts.userType,
    p: opts.decompositionProvenance ?? null,
    m: opts.multiDayLabel ?? null,
    e: opts.enableLcaMatcher ?? true,
  });
  return fnv1a(payload);
}

function loadCache(hash: string): ProfileResults | null {
  const mem = memoryCache.get(hash);
  if (mem) return mem;
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.sessionStorage.getItem(`${CACHE_PREFIX}${hash}`);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as ProfileResults;
    memoryCache.set(hash, parsed);
    return parsed;
  } catch {
    return null;
  }
}

function saveCache(hash: string, results: ProfileResults): void {
  memoryCache.set(hash, results);
  if (typeof window === 'undefined') return;
  try {
    window.sessionStorage.setItem(`${CACHE_PREFIX}${hash}`, JSON.stringify(results));
  } catch {
    // sessionStorage may be full or unavailable — non-fatal.
  }
}

/** Forget all cached scorecard runs. Called when the user explicitly hits
 *  "Re-score" or when the active list changes. */
export function clearScorecardCache(): void {
  memoryCache.clear();
  if (typeof window === 'undefined') return;
  try {
    const toRemove: string[] = [];
    for (let i = 0; i < window.sessionStorage.length; i += 1) {
      const k = window.sessionStorage.key(i);
      if (k && k.startsWith(CACHE_PREFIX)) toRemove.push(k);
    }
    for (const k of toRemove) window.sessionStorage.removeItem(k);
  } catch {
    // ignore
  }
}

// --- Orchestrator ---------------------------------------------------------

/** Extract the `explanations` block from a scorer response in a
 *  shape-tolerant way. Different scorers nest it slightly differently. */
function extractExplanations(payload: unknown): ExplanationsBlock | undefined {
  if (!payload || typeof payload !== 'object') return undefined;
  const obj = payload as Record<string, unknown>;
  // Top-level (HEFI, HSR, dietary-pattern)
  if (obj.explanations && typeof obj.explanations === 'object') {
    return obj.explanations as ExplanationsBlock;
  }
  // FCS calculate: { data: { fcs, explanations, ... } }
  if (obj.data && typeof obj.data === 'object') {
    const data = obj.data as Record<string, unknown>;
    if (data.explanations && typeof data.explanations === 'object') {
      return data.explanations as ExplanationsBlock;
    }
  }
  // Nested under .data (HENI, FCS)
  if (obj.data && typeof obj.data === 'object') {
    const data = obj.data as Record<string, unknown>;
    if (data.explanations && typeof data.explanations === 'object') {
      return data.explanations as ExplanationsBlock;
    }
  }
  // Nested under .hsr_result (HSR)
  if (obj.hsr_result && typeof obj.hsr_result === 'object') {
    const hr = obj.hsr_result as Record<string, unknown>;
    if (hr.explanations && typeof hr.explanations === 'object') {
      return hr.explanations as ExplanationsBlock;
    }
  }
  return undefined;
}

function nowIso(): string {
  return new Date().toISOString();
}

function asReason(err: unknown): string {
  if (err instanceof Error) return err.message;
  if (typeof err === 'string') return err;
  try {
    return JSON.stringify(err);
  } catch {
    return 'Unknown error';
  }
}

/** Run all 6 scorers in parallel. Each promise is wrapped via
 *  `Promise.allSettled` so a single failing metric never blocks the others. */
export async function runAllScorers(
  ingredients: ScorerInput[],
  opts: RunOptions,
  { useCache = true }: { useCache?: boolean } = {},
): Promise<ProfileResults> {
  if (ingredients.length === 0) {
    throw new Error('runAllScorers: ingredients array is empty');
  }
  const hash = hashInputs(ingredients, opts);
  if (useCache) {
    const cached = loadCache(hash);
    if (cached) return cached;
  }

  const enableLca = opts.enableLcaMatcher ?? true;
  const userType = opts.userType;

  // Build per-scorer request bodies from the same canonical input shape.
  const hefiReq = {
    foods: ingredients.map(i => ({ food_id: i.food_id, amount_g: i.mass_g })),
    user_type: userType,
  };
  const heniReq = {
    meal: ingredients.map(i => ({ food_id: i.food_id, amount: i.mass_g, unit: 'g' })),
    user_type: userType,
  };
  const hsrReq = {
    food_ids: ingredients.map(i => i.food_id),
    serving_sizes: ingredients.map(i => i.mass_g),
    analysis_level: 'detailed' as const,
    include_alternatives: false,
    include_meal_insights: true,
    from_recall24h: ingredients.length > 1,
    user_type: userType,
  };
  const fcsReq = {
    food_ids: ingredients.map(i => i.food_id),
    food_names: ingredients.map(i => i.food_description),
    serving_sizes: ingredients.map(i => i.mass_g),
    user_type: userType,
  };
  const envReq = {
    foods: ingredients.map(i => ({ food_id: i.food_id, quantity: i.mass_g })),
    user_type: userType,
    enable_lca_matcher: enableLca,
  };

  // Dietary pattern uses CNFApiService.classifyDietaryPattern(foods, options)
  const settled = await Promise.allSettled([
    HEFIApiService.calculateHEFI(hefiReq),
    HENIApiService.calculateHENI(heniReq),
    HSRApiService.calculateHSR(hsrReq),
    FCSApiService.calculateFCS(fcsReq),
    EnvironmentalImpactApiService.analyzeMealEnvironmentalImpact(envReq),
    CNFApiService.classifyDietaryPattern(
      ingredients.map(i => ({ food_id: i.food_id, mass_g: i.mass_g })),
      {
        userType,
        includeNarrative: userType !== 'individual',
        metaLabel: opts.multiDayLabel,
        decompositionProvenance: opts.decompositionProvenance,
      },
    ),
  ]);

  const cachedAt = nowIso();

  function toOutcome<T>(
    metric: MetricKey,
    settledResult: PromiseSettledResult<T>,
  ): MetricOutcome<T> {
    if (settledResult.status === 'fulfilled') {
      return {
        status: 'fulfilled',
        metric,
        result: settledResult.value,
        explanations: extractExplanations(settledResult.value),
        cachedAt,
      };
    }
    return {
      status: 'rejected',
      metric,
      reason: asReason(settledResult.reason),
      cachedAt,
    };
  }

  const results: ProfileResults = {
    hefi: toOutcome<HEFIResult>('hefi', settled[0] as PromiseSettledResult<HEFIResult>),
    heni: toOutcome<HENIResult>('heni', settled[1] as PromiseSettledResult<HENIResult>),
    hsr: toOutcome<HSRResult>('hsr', settled[2] as PromiseSettledResult<HSRResult>),
    fcs: toOutcome<{ data: FCSResult }>(
      'fcs', settled[3] as PromiseSettledResult<{ data: FCSResult }>,
    ),
    environmental: toOutcome<EnvironmentalImpactResult>(
      'environmental',
      settled[4] as PromiseSettledResult<EnvironmentalImpactResult>,
    ),
    dietary_pattern: toOutcome<PatternClassifyResponse>(
      'dietary_pattern',
      settled[5] as PromiseSettledResult<PatternClassifyResponse>,
    ),
  };

  saveCache(hash, results);
  return results;
}

/** Re-run ONE metric that failed earlier. Used by the per-card retry button.
 *  Updates the cached `ProfileResults` in place if the previous run is cached. */
export async function retryOneMetric(
  metric: MetricKey,
  ingredients: ScorerInput[],
  opts: RunOptions,
): Promise<MetricOutcome<unknown>> {
  // Cheapest path — re-run all and pull the one out. We could be cleverer
  // and only call the targeted endpoint, but the cache is keyed on the
  // full input, so a partial retry would still need to merge into the
  // cached payload. Simpler and rare enough — just re-run.
  const all = await runAllScorers(ingredients, opts, { useCache: false });
  return all[metric];
}
