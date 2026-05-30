/**
 * scorecardSession — persist scored runs (list + results + audience) for replay/export.
 */
import type { UserType } from '@/components/shared/AudienceToggle';
import type { ActiveFoodList } from '@/lib/activeFoodList';
import type { ProfileResults, MetricKey } from '@/lib/foodProfileOrchestrator';
import type { ProfileScoreMeta } from '@/lib/api';

const SESSION_KEY = 'scorecard_last_session_v1';

export interface ScorecardSession {
  schema_version: 1;
  saved_at: string;
  list: ActiveFoodList;
  user_type: UserType;
  ingredient_hash: string;
  results: ProfileResults;
  meta?: ProfileScoreMeta | null;
  selected_food_ids: number[];
}

export function saveScorecardSession(session: Omit<ScorecardSession, 'schema_version' | 'saved_at'>): boolean {
  if (typeof window === 'undefined') return false;
  try {
    const payload: ScorecardSession = {
      schema_version: 1,
      saved_at: new Date().toISOString(),
      ...session,
    };
    window.localStorage.setItem(SESSION_KEY, JSON.stringify(payload));
    return true;
  } catch {
    return false;
  }
}

export function loadScorecardSession(): ScorecardSession | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as ScorecardSession;
  } catch {
    return null;
  }
}

export function exportSessionJson(session: ScorecardSession): string {
  return JSON.stringify(session, null, 2);
}

export function sessionMetricSummary(session: ScorecardSession): Record<MetricKey, string> {
  const out = {} as Record<MetricKey, string>;
  for (const key of Object.keys(session.results) as MetricKey[]) {
    const o = session.results[key];
    out[key] = o.status === 'fulfilled' ? 'ok' : o.status === 'rejected' ? 'error' : 'skipped';
  }
  return out;
}
