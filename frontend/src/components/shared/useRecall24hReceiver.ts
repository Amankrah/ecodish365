/**
 * useRecall24hReceiver — pick up an aggregated 24-h recall payload that
 * Recall24hWizard stashed in sessionStorage, hand it to the target page,
 * and clear the stash so a reload doesn't re-inject (AI-MATCH-2).
 *
 * Pages call:
 *
 *   useRecall24hReceiver({
 *     target: 'hefi',                    // must match the target the wizard set
 *     onIngredients: (ingredients) => {
 *       // ingredients: Array<{food_id, food_description, food_group, mass_g, occasions}>
 *       setSelectedFoods(ingredients.map(i => ({ ... your shape ... })));
 *     },
 *   });
 *
 * Fires exactly once per page mount when `?from=recall24h` is in the URL.
 * Silent no-op when the URL doesn't carry the marker or sessionStorage is
 * unavailable (private mode). The wizard sets the marker via window.location.href
 * navigation, so the target page mounts fresh and runs this hook.
 */
'use client';

import { useEffect, useRef } from 'react';
import type { CNFRecall24hAggregatedIngredient } from '@/lib/api';

type Target = 'hefi' | 'heni' | 'hsr' | 'fcs' | 'environmental' | 'dietary_pattern';

interface RecallStash {
  source: 'recall_24h';
  user_type: 'individual' | 'researcher' | 'policy';
  captured_at: string;
  target: Target;
  meals_meta: Array<{ occasion: string; dish_name: string; total_mass_g: number }>;
  aggregated_daily_ingredients: CNFRecall24hAggregatedIngredient[];
  estimated_daily_kcal: number;
}

interface UseRecall24hReceiverOptions {
  /** Which target this page represents. Hook only fires if the stash agrees. */
  target: Target;
  /** Invoked once on mount with the aggregated ingredient list. */
  onIngredients: (ingredients: CNFRecall24hAggregatedIngredient[], meta: {
    user_type: RecallStash['user_type'];
    estimated_daily_kcal: number;
    meals_meta: RecallStash['meals_meta'];
  }) => void;
}

export function useRecall24hReceiver({ target, onIngredients }: UseRecall24hReceiverOptions): void {
  const firedRef = useRef(false);

  useEffect(() => {
    if (firedRef.current) return;
    if (typeof window === 'undefined') return;
    // URL marker check — wizard sets ?from=recall24h on the destination URL.
    const params = new URLSearchParams(window.location.search);
    if (params.get('from') !== 'recall24h') return;
    let stash: RecallStash | null = null;
    try {
      const raw = sessionStorage.getItem('recall_24h_payload');
      if (!raw) return;
      stash = JSON.parse(raw) as RecallStash;
    } catch {
      return;
    }
    if (!stash || stash.source !== 'recall_24h' || stash.target !== target) return;
    if (!Array.isArray(stash.aggregated_daily_ingredients)
        || stash.aggregated_daily_ingredients.length === 0) return;
    firedRef.current = true;
    onIngredients(stash.aggregated_daily_ingredients, {
      user_type: stash.user_type,
      estimated_daily_kcal: stash.estimated_daily_kcal,
      meals_meta: stash.meals_meta,
    });
    // Clear the stash so a reload doesn't re-inject.
    try { sessionStorage.removeItem('recall_24h_payload'); } catch { /* private mode */ }
    // Strip the ?from=recall24h marker from the URL so the same effect
    // doesn't refire on history navigation back to this page.
    try {
      const url = new URL(window.location.href);
      url.searchParams.delete('from');
      window.history.replaceState({}, '', url.toString());
    } catch { /* unsupported */ }
  // onIngredients is captured at first mount via firedRef; intentionally
  // omitting it from deps so identity changes don't refire.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target]);
}
