/**
 * Client-side cohort persistence (PLATFORM-CODE-1.b, 2026-06-26).
 *
 * Researchers should not have to re-upload the same NHANES file every time
 * they want to compare cohorts. This module persists scored cohorts to
 * localStorage with LRU eviction at MAX_SAVED — enough that a typical
 * comparison workflow (baseline + variant) fits comfortably, while keeping
 * the bundle of stored payloads under most browsers' ~5-10 MB localStorage
 * cap. No server-side persistence and no auth changes — by design.
 *
 * The cohort id is a short hash of `(timestamp + n_recalls + first_respondent_id)`
 * so it's stable enough to use in a URL but readable enough that a user can
 * tell two cohorts apart in a list.
 */
import type { CohortResult, CohortRecallInput } from './api';

const STORAGE_KEY = 'savedCohorts.v1';
const MAX_SAVED = 5;

export interface SavedCohort {
  id: string;
  name: string;
  createdAt: number;             // unix ms — used for LRU eviction
  source: string;                // e.g. 'NHANES DR1IFF_J' or 'CSV upload'
  formatDetected: string;        // 'nhanes_dr1iff' | 'generic_csv' | ...
  lensesRun: string[];
  nRecalls: number;
  nRespondents: number;
  result: CohortResult;
  /** Optional — keep the raw recalls so the user can re-run with different
   * lenses without re-uploading the source file. */
  recalls?: CohortRecallInput[];
}

function safeReadAll(): SavedCohort[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed as SavedCohort[];
  } catch {
    return [];
  }
}

function safeWriteAll(list: SavedCohort[]): boolean {
  if (typeof window === 'undefined') return false;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    return true;
  } catch {
    // QuotaExceeded — drop the oldest entry and retry once. If still failing,
    // the caller will get a falsy and can warn the user.
    if (list.length > 1) {
      const trimmed = [...list].sort((a, b) => b.createdAt - a.createdAt).slice(0, list.length - 1);
      try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
        return true;
      } catch {
        return false;
      }
    }
    return false;
  }
}

function makeId(seed: SavedCohort): string {
  const firstResp = seed.result.per_respondent[0]?.respondent_id ?? 'none';
  const raw = `${seed.createdAt}-${seed.nRecalls}-${firstResp}`;
  // Simple hash — readable, collision-resistant enough for ≤5 saved entries.
  let h = 0;
  for (let i = 0; i < raw.length; i += 1) {
    h = ((h << 5) - h) + raw.charCodeAt(i);
    h |= 0;
  }
  const slug = Math.abs(h).toString(36).slice(0, 6);
  return `c_${slug}`;
}

export function listSavedCohorts(): SavedCohort[] {
  return safeReadAll().sort((a, b) => b.createdAt - a.createdAt);
}

export function getSavedCohort(id: string): SavedCohort | null {
  return safeReadAll().find(c => c.id === id) ?? null;
}

export interface SaveCohortInput {
  name: string;
  source: string;
  formatDetected: string;
  lensesRun: string[];
  result: CohortResult;
  recalls?: CohortRecallInput[];
}

export function saveCohort(input: SaveCohortInput): SavedCohort | null {
  const createdAt = Date.now();
  const seed: SavedCohort = {
    id: '',
    name: input.name.trim() || 'Untitled cohort',
    createdAt,
    source: input.source,
    formatDetected: input.formatDetected,
    lensesRun: input.lensesRun,
    nRecalls: input.result.meta.n_recalls,
    nRespondents: input.result.meta.n_respondents,
    result: input.result,
    recalls: input.recalls,
  };
  seed.id = makeId(seed);

  const existing = safeReadAll();
  const filtered = existing.filter(c => c.id !== seed.id);
  filtered.push(seed);
  // LRU eviction by createdAt
  filtered.sort((a, b) => b.createdAt - a.createdAt);
  const trimmed = filtered.slice(0, MAX_SAVED);
  if (!safeWriteAll(trimmed)) {
    return null;
  }
  return seed;
}

export function deleteCohort(id: string): boolean {
  const existing = safeReadAll();
  const next = existing.filter(c => c.id !== id);
  return safeWriteAll(next);
}

export function renameCohort(id: string, name: string): SavedCohort | null {
  const existing = safeReadAll();
  const idx = existing.findIndex(c => c.id === id);
  if (idx < 0) return null;
  existing[idx] = { ...existing[idx], name: name.trim() || existing[idx].name };
  return safeWriteAll(existing) ? existing[idx] : null;
}

export const SAVED_COHORTS_MAX = MAX_SAVED;
