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
  // RECALL-HISTORY-1 (2026-05-24) — when set, this stash represents a
  // multi-day average across N saved recalls (mass-weighted concatenation),
  // not a single day. The receiving page should use this to drive the
  // softened multi-day caveat + "N-day average" framing.
  multi_day?: {
    n_days: number;
    first_date: string;          // ISO YYYY-MM-DD
    last_date: string;           // ISO YYYY-MM-DD
    label: string;               // "5-day average, 2026-05-17 to 2026-05-21"
    day_ids: string[];           // for traceability
  };
  // PKG-IMG-1 Phase 2 (2026-05-26) — when set, the aggregated_daily_ingredients
  // came from a packaged-food label decomposition (NF panel + ingredient
  // list → CNF composition), NOT from a recall. Receiving pages forward this
  // to the backend (e.g. as `decomposition_provenance: 'packaged_food_inferred'`)
  // so the caveat language can swap to the inferred-composition variant.
  packaged_food?: {
    provenance: 'packaged_food_inferred';
    product_name: string | null;
    brand: string | null;
    net_weight_g: number;
    decomposition_confidence: number;
    image_sha256: string;
  };
  /** PKG-RECALL-1: one or more recall occasions entered via label scan. */
  packaged_food_occasions?: Array<{
    occasion: string;
    product_name: string | null;
    brand: string | null;
    decomposition_confidence: number;
  }>;
}

interface UseRecall24hReceiverOptions {
  /** Which target this page represents. Hook only fires if the stash agrees. */
  target: Target;
  /** Invoked once on mount with the aggregated ingredient list. */
  onIngredients: (ingredients: CNFRecall24hAggregatedIngredient[], meta: {
    user_type: RecallStash['user_type'];
    estimated_daily_kcal: number;
    meals_meta: RecallStash['meals_meta'];
    /** Present when the recall-history page routed an N-day average. */
    multi_day?: RecallStash['multi_day'];
    /** Present when /scan-product routed an inferred-composition product. */
    packaged_food?: RecallStash['packaged_food'];
    /** Present when recall included scanned packaged-food occasion(s). */
    packaged_food_occasions?: RecallStash['packaged_food_occasions'];
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
      multi_day: stash.multi_day,
      packaged_food: stash.packaged_food,
      packaged_food_occasions: stash.packaged_food_occasions,
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
