/**
 * metricAdapters — pure functions that map each scorer's response shape
 * into a uniform `CardModel` consumed by `<MetricCard>`. Isolates the
 * messy per-scorer response-shape handling and per-audience caveat
 * selection. Single source of truth for the scorecard's consumer copy.
 *
 * Researcher / policy modes pull caveats from the backend-emitted
 * `explanations` block (AUDIENCE-CODE-1 2026-05-23). Individual mode uses
 * static plain-English copy derived from the manuscript.
 */

import type {
  HEFIResult,
  HENIResult,
  HSRResult,
  FCSResult,
  EnvironmentalImpactResult,
  PatternClassifyResponse,
} from '@/lib/api';
import type { UserType, ExplanationsBlock } from '@/components/shared/AudienceToggle';
import type { MetricKey, MetricOutcome } from '@/lib/foodProfileOrchestrator';

export type Accent =
  | 'green' | 'purple' | 'amber' | 'blue' | 'emerald' | 'rose' | 'gray';

export interface CardModel {
  metric: MetricKey;
  title: string;
  emoji: string;
  /** Plain-text headline (e.g. "62 / 80 · Above average", "★★★½ 3.5/5") */
  headline: string;
  /** Optional secondary number / units line (small text under headline). */
  subline?: string;
  /** 1 sentence — "what this means for you." Individual mode only.
   *  Researcher mode pulls from `explanations.score_summary?.interpretation`. */
  meaning: string;
  /** 1 sentence — caveat or limitation. Audience-aware. */
  caveat: string;
  /** Optional 1-line driver/note ("Top contributor: red meat", etc.). */
  driver?: string;
  /** Where the "View full breakdown →" link goes. */
  ctaHref: string;
  /** Label for the CTA button. */
  ctaLabel: string;
  /** Colour theme for the card header chip. */
  accent: Accent;
  /** Status that drives the visual treatment of the card. */
  status: 'ok' | 'damped' | 'hint' | 'error';
  /** When status==='error' or status==='hint', the message to display
   *  in place of meaning/driver. */
  hint?: string;
}

// ---------------------------------------------------------------------------
// Static, individual-mode copy. Sourced from manuscript_call1.md Phase 1
// exploration. The wording is intentionally short and concrete.
// ---------------------------------------------------------------------------

const META: Record<MetricKey, {
  title: string;
  emoji: string;
  accent: Accent;
  meaningIndividual: string;
  caveatIndividual: string;
  ctaHref: string;
  ctaLabel: string;
}> = {
  hefi: {
    title: 'HEFI-2019',
    emoji: '🥗',
    accent: 'green',
    meaningIndividual:
      "How well your eating aligns with Canada's Food Guide today.",
    caveatIndividual:
      'Designed for a full day of foods — single meals are a rough estimate.',
    ctaHref: '/hefi/calculate?from=scorecard',
    ctaLabel: 'View full HEFI breakdown',
  },
  heni: {
    title: 'HENI',
    emoji: '🧬',
    accent: 'purple',
    meaningIndividual:
      'Estimated minutes of healthy life your foods add or subtract.',
    caveatIndividual:
      'Population-marginal estimate, not a personal prediction.',
    ctaHref: '/heni/calculate?from=scorecard',
    ctaLabel: 'View full HENI breakdown',
  },
  hsr: {
    title: 'HSR',
    emoji: '⭐',
    accent: 'amber',
    meaningIndividual:
      "How healthy your products are compared to others in their category.",
    caveatIndividual:
      'Per-product comparison. A healthy product is not a healthy day.',
    ctaHref: '/hsr/calculate?from=scorecard',
    ctaLabel: 'View full HSR breakdown',
  },
  fcs: {
    title: 'FCS',
    emoji: '🧭',
    accent: 'blue',
    meaningIndividual:
      'How much your foods resemble those linked to longer life in cohort studies.',
    caveatIndividual:
      'Anchored to US cohorts; Canadian validation is pending.',
    ctaHref: '/fcs/calculate?from=scorecard',
    ctaLabel: 'View full FCS breakdown',
  },
  environmental: {
    title: 'Environmental',
    emoji: '🌍',
    accent: 'emerald',
    meaningIndividual:
      'Climate, land, and water cost of producing this food.',
    caveatIndividual:
      'Production-stage only — does not cover preparation or end-of-life.',
    ctaHref: '/environmental/calculate?from=scorecard',
    ctaLabel: 'View full environmental breakdown',
  },
  dietary_pattern: {
    title: 'Dietary pattern',
    emoji: '🎯',
    accent: 'rose',
    meaningIndividual:
      'Which canonical eating pattern your day most resembles.',
    caveatIndividual:
      'Needs several foods over a full day to be meaningful.',
    ctaHref: '/dietary-pattern?from=scorecard',
    ctaLabel: 'View full pattern breakdown',
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Audience-aware caveat picker — researcher/policy uses the backend's
 *  audience-aware `explanations.score_summary.mandatory_caveat` if present,
 *  individual uses the static copy above. */
function pickCaveat(
  metric: MetricKey,
  userType: UserType,
  explanations: ExplanationsBlock | undefined,
): string {
  const inferredMsg = explanations?.inferred_composition_caveat?.message;
  const wafctMsg = explanations?.wafct_caveat?.message;

  if (userType !== 'individual') {
    const c = explanations?.score_summary?.mandatory_caveat
      || explanations?.recall_context?.message
      || inferredMsg
      || wafctMsg;
    if (c) return c;
  }

  if (inferredMsg) return inferredMsg;
  if (wafctMsg) return wafctMsg;

  return META[metric].caveatIndividual;
}

function pickMeaning(
  metric: MetricKey,
  userType: UserType,
  explanations: ExplanationsBlock | undefined,
): string {
  if (userType !== 'individual') {
    const m = explanations?.score_summary?.interpretation
      || explanations?.score_summary?.description
      || explanations?.score_summary?.message
      || explanations?.recall_context?.message;
    if (m) return m;
  }
  return META[metric].meaningIndividual;
}

function errorCard(metric: MetricKey, reason: string): CardModel {
  const meta = META[metric];
  return {
    metric,
    title: meta.title,
    emoji: meta.emoji,
    headline: 'Could not score',
    meaning: meta.meaningIndividual,
    caveat: 'Other metrics may still be available below.',
    hint: reason,
    ctaHref: meta.ctaHref,
    ctaLabel: 'Try the full scorer',
    accent: 'gray',
    status: 'error',
  };
}

function hintCard(metric: MetricKey, hint: string): CardModel {
  const meta = META[metric];
  return {
    metric,
    title: meta.title,
    emoji: meta.emoji,
    headline: '—',
    meaning: meta.meaningIndividual,
    caveat: meta.caveatIndividual,
    hint,
    ctaHref: meta.ctaHref,
    ctaLabel: meta.ctaLabel,
    accent: 'gray',
    status: 'hint',
  };
}

// ---------------------------------------------------------------------------
// Per-metric adapters
// ---------------------------------------------------------------------------

/** HEFI `notes` strings that read as researcher-jargon when surfaced as
 *  the consumer driver line. Substring-matched, case-insensitive. */
const HEFI_DRIVER_NOISE_PATTERNS = [
  'no official grading',
  'population-based',
  'descriptive',
  'percentile',
  'reference amounts',
  'brassard',
  'apnm',
];

function isAwkwardForIndividual(note: string): boolean {
  const lower = note.toLowerCase();
  return HEFI_DRIVER_NOISE_PATTERNS.some(p => lower.includes(p));
}

export function toHefiCard(
  outcome: MetricOutcome<HEFIResult>,
  userType: UserType,
): CardModel {
  if (outcome.status !== 'fulfilled') {
    return errorCard('hefi', outcome.status === 'rejected' ? outcome.reason : 'Skipped');
  }
  const data = outcome.result?.data;
  const total = data?.total_score ?? 0;
  const max = data?.max_total_score ?? 80;
  const interp = (data as Record<string, unknown>)?.hefi_interpretation as
    | { category?: string; ui_color?: string; notes?: string[] }
    | undefined;
  const category = interp?.category ?? 'Score computed';
  const headline = `${total.toFixed(0)} / ${max} · ${category}`;
  // Researcher / policy: surface the first note as-is (it's tuned for them).
  // Individual: filter out audit-trail caveats that read as jargon, and
  // prefer a note that doesn't match the noise patterns. Drop entirely if
  // none survive — better silence than awkward.
  const notes = interp?.notes ?? [];
  let driver: string | undefined;
  if (userType === 'individual') {
    driver = notes.find(n => !isAwkwardForIndividual(n));
  } else {
    driver = notes[0];
  }
  const meta = META.hefi;
  return {
    metric: 'hefi',
    title: meta.title,
    emoji: meta.emoji,
    headline,
    meaning: pickMeaning('hefi', userType, outcome.explanations),
    caveat: pickCaveat('hefi', userType, outcome.explanations),
    driver,
    ctaHref: meta.ctaHref,
    ctaLabel: meta.ctaLabel,
    accent: meta.accent,
    status: 'ok',
  };
}

export function toHeniCard(
  outcome: MetricOutcome<HENIResult>,
  userType: UserType,
): CardModel {
  if (outcome.status !== 'fulfilled') {
    return errorCard('heni', outcome.status === 'rejected' ? outcome.reason : 'Skipped');
  }
  const data = outcome.result?.data;
  const minutes = data?.health_impact?.health_impact_minutes ?? 0;
  const sign = minutes >= 0 ? '+' : '−';
  const abs = Math.abs(minutes);
  const headline = `${sign}${abs.toFixed(1)} min`;
  const subline = minutes >= 0 ? 'added to your healthy life' : 'subtracted from your healthy life';
  const meta = META.heni;
  return {
    metric: 'heni',
    title: meta.title,
    emoji: meta.emoji,
    headline,
    subline,
    meaning: pickMeaning('heni', userType, outcome.explanations),
    caveat: pickCaveat('heni', userType, outcome.explanations),
    ctaHref: meta.ctaHref,
    ctaLabel: meta.ctaLabel,
    accent: meta.accent,
    status: 'ok',
  };
}

export function toHsrCard(
  outcome: MetricOutcome<HSRResult>,
  userType: UserType,
  nFoods: number,
): CardModel {
  if (outcome.status !== 'fulfilled') {
    return errorCard('hsr', outcome.status === 'rejected' ? outcome.reason : 'Skipped');
  }
  const meta = META.hsr;
  const multiFood = nFoods >= 2;

  // n = 1 — keep the standard per-product star rating; this is HSR's
  // native unit of analysis.
  if (!multiFood) {
    const rating = outcome.result?.hsr_result?.rating?.star_rating ?? 0;
    const level = outcome.result?.hsr_result?.rating?.level;
    const stars = '★'.repeat(Math.floor(rating))
      + (rating % 1 >= 0.5 ? '½' : '')
      + '☆'.repeat(Math.max(0, 5 - Math.ceil(rating)));
    return {
      metric: 'hsr',
      title: meta.title,
      emoji: meta.emoji,
      headline: `${stars} · ${rating.toFixed(1)} / 5`,
      subline: level ? level.replace(/_/g, ' ') : undefined,
      meaning: pickMeaning('hsr', userType, outcome.explanations),
      caveat: pickCaveat('hsr', userType, outcome.explanations),
      ctaHref: meta.ctaHref,
      ctaLabel: meta.ctaLabel,
      accent: meta.accent,
      status: 'ok',
    };
  }

  // n ≥ 2 — use the per-food summary from the SCORECARD-1 backend
  // extension. This avoids the misleading "combined-meal star treated as
  // a day score" framing; instead we show within-category comparison
  // anchors: energy-weighted average, range, and the best/worst items.
  const summary = outcome.result?.per_food_summary;
  if (!summary?.available) {
    // Backend did not emit per-food summary (older deployment, or all
    // per-food calls failed). Honest fallback: show a hint card pointing
    // the user to the compare tool.
    return {
      metric: 'hsr',
      title: meta.title,
      emoji: meta.emoji,
      headline: 'Per-product compare unavailable',
      meaning: META.hsr.meaningIndividual,
      caveat: 'HSR compares products within the same category, not whole days.',
      ctaHref: '/hsr/compare?from=scorecard',
      ctaLabel: 'Open HSR compare',
      accent: meta.accent,
      status: 'hint',
      hint: 'Open HSR compare to score each product individually.',
    };
  }
  const wAvg = summary.energy_weighted_avg;
  const high = summary.highest;
  const low = summary.lowest;
  // Truncate long food names so the driver line stays one short sentence.
  const trunc = (s: string, n = 32) => s.length > n ? `${s.slice(0, n - 1)}…` : s;
  const driver = high && low && high.food_id !== low.food_id
    ? `Range ${summary.min.toFixed(1)}–${summary.max.toFixed(1)}★ · strongest: ${trunc(high.food_name)} · weakest: ${trunc(low.food_name)}`
    : `Range ${summary.min.toFixed(1)}–${summary.max.toFixed(1)}★`;
  const dist = summary.distribution;
  const goodOrBetter = dist.excellent + dist.good;
  const multiMeaning = 'How healthy each individual product is within its own category — averaged across your list.';
  return {
    metric: 'hsr',
    title: meta.title,
    emoji: meta.emoji,
    headline: `~${wAvg.toFixed(1)}★ weighted avg · ${summary.n_foods} products`,
    subline: `${goodOrBetter} of ${summary.n_foods} items ≥ 3.5★`,
    meaning: pickMeaning('hsr', userType, outcome.explanations) || multiMeaning,
    caveat: pickCaveat('hsr', userType, outcome.explanations),
    driver,
    ctaHref: '/hsr/compare?from=scorecard',
    ctaLabel: 'Compare products',
    accent: meta.accent,
    status: 'damped',
  };
}

function extractFcsScore(raw: unknown): number | null {
  const stack: unknown[] = [];
  const visit = (node: unknown, depth = 0): void => {
    if (!node || typeof node !== 'object' || depth > 4) return;
    stack.push(node);
    const o = node as Record<string, unknown>;
    if (o.data && typeof o.data === 'object') visit(o.data, depth + 1);
  };
  visit(raw);
  for (const layer of stack) {
    const fcs = Number((layer as Record<string, unknown>).fcs);
    if (Number.isFinite(fcs) && fcs >= 1) return fcs;
  }
  return null;
}

export function toFcsCard(
  outcome: MetricOutcome<{ data: FCSResult }>,
  userType: UserType,
  nFoods: number,
): CardModel {
  if (outcome.status !== 'fulfilled') {
    return errorCard('fcs', outcome.status === 'rejected' ? outcome.reason : 'Skipped');
  }
  const fcs = extractFcsScore(outcome.result);
  const raw = (outcome.result ?? {}) as Record<string, unknown>;
  const dataLayer = (raw.data && typeof raw.data === 'object')
    ? raw.data as Record<string, unknown>
    : raw;
  const nova = typeof dataLayer.nova_category === 'string' ? dataLayer.nova_category : undefined;
  const meta = META.fcs;
  const isDayScale = nFoods >= 2;
  const headline = fcs === null ? '—' : `${fcs.toFixed(0)} / 100`;
  const subline = nova
    ? nova.replace(/_/g, ' ').toLowerCase()
    : undefined;
  return {
    metric: 'fcs',
    title: meta.title,
    emoji: meta.emoji,
    headline,
    subline,
    meaning: pickMeaning('fcs', userType, outcome.explanations),
    caveat: isDayScale
      ? 'Combined-meal FCS uses energy-weighted nutrients and ingredient flags. For a full breakdown, open the FCS calculator.'
      : pickCaveat('fcs', userType, outcome.explanations),
    ctaHref: meta.ctaHref,
    ctaLabel: meta.ctaLabel,
    accent: meta.accent,
    status: fcs === null ? 'hint' : 'ok',
    hint: fcs === null
      ? 'FCS could not score this combination. Open the full FCS breakdown for details.'
      : undefined,
  };
}

export function toEnvironmentalCard(
  outcome: MetricOutcome<EnvironmentalImpactResult>,
  userType: UserType,
): CardModel {
  if (outcome.status !== 'fulfilled') {
    return errorCard('environmental', outcome.status === 'rejected' ? outcome.reason : 'Skipped');
  }
  const lca = outcome.result?.data?.meal_analysis?.lca_results ?? {};
  const bands = outcome.result?.data?.meal_analysis?.lca_results_bands ?? {};
  const co2 = lca['Global warming'];
  const land = lca['Land use'];
  const water = lca['Water consumption'];
  const meta = META.environmental;
  const parts: string[] = [];
  if (typeof co2 === 'number') parts.push(`${co2.toFixed(2)} kg CO₂e`);
  if (typeof land === 'number') parts.push(`${land.toFixed(2)} m²·yr`);
  if (typeof water === 'number') parts.push(`${water.toFixed(2)} m³ water`);
  const headline = parts.join(' · ') || 'Computed';
  const co2Band = bands['Global warming'];
  const driver = co2Band && typeof co2Band.low === 'number' && typeof co2Band.high === 'number'
    ? `CO₂e uncertainty: ${co2Band.low.toFixed(2)}–${co2Band.high.toFixed(2)} kg`
    : undefined;
  return {
    metric: 'environmental',
    title: meta.title,
    emoji: meta.emoji,
    headline,
    meaning: pickMeaning('environmental', userType, outcome.explanations),
    caveat: pickCaveat('environmental', userType, outcome.explanations),
    driver,
    ctaHref: meta.ctaHref,
    ctaLabel: meta.ctaLabel,
    accent: meta.accent,
    status: 'ok',
  };
}

export function toDietaryPatternCard(
  outcome: MetricOutcome<PatternClassifyResponse>,
  userType: UserType,
  nFoods: number,
): CardModel {
  if (outcome.status !== 'fulfilled') {
    return errorCard('dietary_pattern', outcome.status === 'rejected' ? outcome.reason : 'Skipped');
  }
  if (nFoods < 5) {
    return {
      ...hintCard('dietary_pattern',
        `Pattern resemblance needs at least 5 foods for a confident match (you have ${nFoods}).`),
    };
  }
  const result = outcome.result?.result;
  const top = result?.top_pattern;
  const confidence = result?.top_pattern_confidence;
  const meta = META.dietary_pattern;
  if (!top) {
    return hintCard('dietary_pattern', 'No clear pattern match.');
  }
  const niceName = top.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  const headline = `Looks most like ${niceName}`;
  const subline = confidence ? `${confidence} confidence` : undefined;
  const explanations = outcome.explanations as unknown as {
    plain_summary?: { message?: string };
    mandatory_caveat?: { message?: string };
  } | undefined;
  return {
    metric: 'dietary_pattern',
    title: meta.title,
    emoji: meta.emoji,
    headline,
    subline,
    meaning: explanations?.plain_summary?.message
      || pickMeaning('dietary_pattern', userType, outcome.explanations),
    caveat: explanations?.mandatory_caveat?.message
      || pickCaveat('dietary_pattern', userType, outcome.explanations),
    ctaHref: meta.ctaHref,
    ctaLabel: meta.ctaLabel,
    accent: meta.accent,
    status: confidence === 'low' ? 'damped' : 'ok',
  };
}

/** Accent → Tailwind class lookup. Exported so MetricCard + MetricSkeleton
 *  share the same palette. */
export const ACCENT_CLASSES: Record<Accent, { chip: string; border: string; bar: string }> = {
  green:   { chip: 'bg-green-100 text-green-800',     border: 'border-green-200',   bar: 'bg-green-500' },
  purple:  { chip: 'bg-purple-100 text-purple-800',   border: 'border-purple-200',  bar: 'bg-purple-500' },
  amber:   { chip: 'bg-amber-100 text-amber-900',     border: 'border-amber-200',   bar: 'bg-amber-500' },
  blue:    { chip: 'bg-blue-100 text-blue-800',       border: 'border-blue-200',    bar: 'bg-blue-500' },
  emerald: { chip: 'bg-emerald-100 text-emerald-800', border: 'border-emerald-200', bar: 'bg-emerald-500' },
  rose:    { chip: 'bg-rose-100 text-rose-800',       border: 'border-rose-200',    bar: 'bg-rose-500' },
  gray:    { chip: 'bg-gray-100 text-gray-700',       border: 'border-gray-200',    bar: 'bg-gray-400' },
};
