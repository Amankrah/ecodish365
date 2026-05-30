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
  type ProfileScoreMeta,
  type ProfileScoreResponse,
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
  /** When the active list came from a packaged-food decomposition, forward
   *  to all scorer endpoints for inferred-composition caveat swap. */
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

export type { ProfileScoreMeta };

export interface ProfileScoreBundle {
  results: ProfileResults;
  meta: ProfileScoreMeta | null;
}

// --- Caching --------------------------------------------------------------

// v4: bumped 2026-05-26 after PKG Phase 2.x caveat swap + HSR skip-combined path.
const CACHE_PREFIX = 'scorecard_cache_v4:';
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

function buildScorerRequests(ingredients: ScorerInput[], opts: RunOptions) {
  const enableLca = opts.enableLcaMatcher ?? true;
  const userType = opts.userType;
  const decompProv = opts.decompositionProvenance;
  return {
    hefiReq: {
      foods: ingredients.map(i => ({ food_id: i.food_id, amount_g: i.mass_g })),
      user_type: userType,
      ...(decompProv ? { decomposition_provenance: decompProv } : {}),
    },
    heniReq: {
      meal: ingredients.map(i => ({ food_id: i.food_id, amount: i.mass_g, unit: 'g' })),
      user_type: userType,
      ...(decompProv ? { decomposition_provenance: decompProv } : {}),
    },
    hsrReq: {
      food_ids: ingredients.map(i => i.food_id),
      serving_sizes: ingredients.map(i => i.mass_g),
      analysis_level: 'detailed' as const,
      include_alternatives: false,
      include_meal_insights: true,
      from_recall24h: ingredients.length > 1,
      user_type: userType,
      ...(decompProv ? { decomposition_provenance: decompProv } : {}),
    },
    fcsReq: {
      food_ids: ingredients.map(i => i.food_id),
      food_names: ingredients.map(i => i.food_description),
      serving_sizes: ingredients.map(i => i.mass_g),
      user_type: userType,
      ...(decompProv ? { decomposition_provenance: decompProv } : {}),
    },
    envReq: {
      foods: ingredients.map(i => ({ food_id: i.food_id, quantity: i.mass_g })),
      user_type: userType,
      enable_lca_matcher: enableLca,
      ...(decompProv ? { decomposition_provenance: decompProv } : {}),
    },
    patternFoods: ingredients.map(i => ({ food_id: i.food_id, mass_g: i.mass_g })),
    patternOpts: {
      userType,
      includeNarrative: userType !== 'individual',
      metaLabel: opts.multiDayLabel,
      decompositionProvenance: opts.decompositionProvenance,
    },
  };
}

async function runSingleScorer(
  metric: MetricKey,
  ingredients: ScorerInput[],
  opts: RunOptions,
): Promise<MetricOutcome<unknown>> {
  const req = buildScorerRequests(ingredients, opts);
  const cachedAt = nowIso();
  try {
    let result: unknown;
    switch (metric) {
      case 'hefi':
        result = await HEFIApiService.calculateHEFI(req.hefiReq);
        break;
      case 'heni':
        result = await HENIApiService.calculateHENI(req.heniReq);
        break;
      case 'hsr':
        result = await HSRApiService.calculateHSR(req.hsrReq);
        break;
      case 'fcs':
        result = await FCSApiService.calculateFCS(req.fcsReq);
        break;
      case 'environmental':
        result = await EnvironmentalImpactApiService.analyzeMealEnvironmentalImpact(req.envReq);
        break;
      case 'dietary_pattern':
        result = await CNFApiService.classifyDietaryPattern(req.patternFoods, req.patternOpts);
        break;
      default:
        throw new Error(`Unknown metric: ${metric}`);
    }
    return {
      status: 'fulfilled',
      metric,
      result,
      explanations: extractExplanations(result),
      cachedAt,
    };
  } catch (err) {
    return {
      status: 'rejected',
      metric,
      reason: asReason(err),
      cachedAt,
    };
  }
}

function profileResponseToResults(
  metrics: ProfileScoreResponse['metrics'],
  cachedAt: string,
): ProfileResults {
  function map<T>(key: MetricKey): MetricOutcome<T> {
    const hit = metrics[key];
    if (!hit) {
      return { status: 'skipped', metric: key, reason: 'Not requested' };
    }
    if (hit.status === 'fulfilled' && hit.result != null) {
      return {
        status: 'fulfilled',
        metric: key,
        result: hit.result as T,
        explanations: extractExplanations(hit.result),
        cachedAt,
      };
    }
    return {
      status: 'rejected',
      metric: key,
      reason: hit.reason ?? 'Unknown error',
      cachedAt,
    };
  }
  return {
    hefi: map<HEFIResult>('hefi'),
    heni: map<HENIResult>('heni'),
    hsr: map<HSRResult>('hsr'),
    fcs: map<{ data: FCSResult }>('fcs'),
    environmental: map<EnvironmentalImpactResult>('environmental'),
    dietary_pattern: map<PatternClassifyResponse>('dietary_pattern'),
  };
}

/** Server-side unified profile score (single round trip). */
export async function runProfileScoreBackend(
  ingredients: ScorerInput[],
  opts: RunOptions,
  { useCache = true }: { useCache?: boolean } = {},
): Promise<ProfileScoreBundle> {
  if (ingredients.length === 0) {
    throw new Error('runProfileScoreBackend: ingredients array is empty');
  }
  const hash = hashInputs(ingredients, opts);
  if (useCache) {
    const cached = loadCache(hash);
    if (cached) {
      return { results: cached, meta: null };
    }
  }
  const cachedAt = nowIso();
  const resp = await CNFApiService.scoreProfile(
    ingredients.map(i => ({
      food_id: i.food_id,
      mass_g: i.mass_g,
      food_description: i.food_description,
    })),
    {
      userType: opts.userType,
      decompositionProvenance: opts.decompositionProvenance,
      multiDayLabel: opts.multiDayLabel,
      enableLcaMatcher: opts.enableLcaMatcher,
    },
  );
  const results = profileResponseToResults(resp.metrics, cachedAt);
  saveCache(hash, results);
  return { results, meta: resp.meta };
}

/** Progressive scoring — updates UI as each metric completes. */
export async function runAllScorersProgressive(
  ingredients: ScorerInput[],
  opts: RunOptions,
  onUpdate: (partial: Partial<ProfileResults>, meta: ProfileScoreMeta | null) => void,
  { useCache = true, preferBackend = true }: { useCache?: boolean; preferBackend?: boolean } = {},
): Promise<ProfileScoreBundle> {
  if (ingredients.length === 0) {
    throw new Error('runAllScorersProgressive: ingredients array is empty');
  }
  const hash = hashInputs(ingredients, opts);
  if (useCache) {
    const cached = loadCache(hash);
    if (cached) {
      onUpdate(cached, null);
      return { results: cached, meta: null };
    }
  }

  if (preferBackend) {
    try {
      const bundle = await runProfileScoreBackend(ingredients, opts, { useCache: false });
      onUpdate(bundle.results, bundle.meta);
      return bundle;
    } catch {
      /* fall through to client fan-out */
    }
  }

  const keys: MetricKey[] = ['hefi', 'heni', 'hsr', 'fcs', 'environmental', 'dietary_pattern'];
  const partial: Partial<ProfileResults> = {};
  await Promise.all(keys.map(async key => {
    const outcome = await runSingleScorer(key, ingredients, opts);
    Object.assign(partial, { [key]: outcome });
    onUpdate({ ...partial }, null);
  }));
  const results = partial as ProfileResults;
  saveCache(hash, results);
  return { results, meta: null };
}

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

/** Run all 6 scorers — prefers unified backend endpoint, falls back to client fan-out. */
export async function runAllScorers(
  ingredients: ScorerInput[],
  opts: RunOptions,
  { useCache = true }: { useCache?: boolean } = {},
): Promise<ProfileResults> {
  const bundle = await runAllScorersProgressive(
    ingredients,
    opts,
    () => {},
    { useCache, preferBackend: true },
  );
  return bundle.results;
}

/** Re-run ONE metric that failed earlier. Merges into cache when present. */
export async function retryOneMetric(
  metric: MetricKey,
  ingredients: ScorerInput[],
  opts: RunOptions,
): Promise<MetricOutcome<unknown>> {
  const fresh = await runSingleScorer(metric, ingredients, opts);
  const hash = hashInputs(ingredients, opts);
  const cached = loadCache(hash);
  if (cached) {
    const merged = { ...cached, [metric]: fresh } as ProfileResults;
    saveCache(hash, merged);
  }
  return fresh;
}
