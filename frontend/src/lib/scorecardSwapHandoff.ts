import type { SubstitutionPurpose } from '@/lib/api';

export const SCORECARD_AUTORUN_SWAPS_KEY = 'ecodish365_scorecard_autorun_swaps';
export const SCORECARD_SWAP_PURPOSE_KEY = 'ecodish365_scorecard_swap_purpose';

export function stashScorecardSwapHandoff(purpose: SubstitutionPurpose): void {
  if (typeof window === 'undefined') return;
  try {
    sessionStorage.setItem(SCORECARD_AUTORUN_SWAPS_KEY, '1');
    sessionStorage.setItem(SCORECARD_SWAP_PURPOSE_KEY, purpose);
  } catch { /* private mode */ }
}

export function readScorecardSwapHandoff(): {
  autoRun: boolean;
  purpose?: SubstitutionPurpose;
} {
  if (typeof window === 'undefined') return { autoRun: false };
  try {
    const autoRun = sessionStorage.getItem(SCORECARD_AUTORUN_SWAPS_KEY) === '1';
    const purpose = sessionStorage.getItem(SCORECARD_SWAP_PURPOSE_KEY) as SubstitutionPurpose | null;
    if (autoRun) sessionStorage.removeItem(SCORECARD_AUTORUN_SWAPS_KEY);
    if (purpose) sessionStorage.removeItem(SCORECARD_SWAP_PURPOSE_KEY);
    return { autoRun, purpose: purpose ?? undefined };
  } catch {
    return { autoRun: false };
  }
}
