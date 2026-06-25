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

import type { ComponentType, SVGProps } from 'react';
import { StarIcon, GlobeAltIcon } from '@heroicons/react/24/outline';
import { Salad, Dna, Compass, Target } from 'lucide-react';
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
import { humanizeForUser } from '@/lib/humanizeCopy';

export type IconType = ComponentType<SVGProps<SVGSVGElement>>;

// Single neutral accent — the platform's scientific palette doesn't
// differentiate metric cards by color any more. Lens identity is carried
// by the icon + title (see ui-ux-pro-max color guide, 2026-06-25).
export type Accent = 'neutral';

export interface CardModel {
  metric: MetricKey;
  title: string;
  icon: IconType;
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
  icon: IconType;
  accent: Accent;
  meaningIndividual: string;
  caveatIndividual: string;
  ctaHref: string;
  ctaLabel: string;
}> = {
  hefi: {
    title: 'Healthy eating',
    icon: Salad,
    accent: 'neutral',
    meaningIndividual:
      'How closely your foods match Canada\'s Food Guide recommendations.',
    caveatIndividual:
      'Best with a full day of eating. A single meal is only a rough guide.',
    ctaHref: '/hefi/calculate?from=scorecard',
    ctaLabel: 'See healthy eating breakdown',
  },
  heni: {
    title: 'Health impact',
    icon: Dna,
    accent: 'neutral',
    meaningIndividual:
      'Estimated minutes of healthy life these foods may add or take away.',
    caveatIndividual:
      'Based on population averages, not a personal health prediction.',
    ctaHref: '/heni/calculate?from=scorecard',
    ctaLabel: 'See health impact breakdown',
  },
  hsr: {
    title: 'Star rating',
    icon: StarIcon,
    accent: 'neutral',
    meaningIndividual:
      'How healthy each product is compared with others in the same category.',
    caveatIndividual:
      'Rates products one at a time. A healthy product does not mean a healthy whole day.',
    ctaHref: '/hsr/calculate?from=scorecard',
    ctaLabel: 'See star rating breakdown',
  },
  fcs: {
    title: 'Food Compass',
    icon: Compass,
    accent: 'neutral',
    meaningIndividual:
      'How much these foods resemble diets linked to longer life in research studies.',
    caveatIndividual:
      'Based mainly on U.S. cohort data. Canadian validation is still in progress.',
    ctaHref: '/fcs/calculate?from=scorecard',
    ctaLabel: 'See Food Compass breakdown',
  },
  environmental: {
    title: 'Environment',
    icon: GlobeAltIcon,
    accent: 'neutral',
    meaningIndividual:
      'Estimated climate, land, and water needed to produce these foods.',
    caveatIndividual:
      'Covers farming and processing. Cooking and packaging are not included.',
    ctaHref: '/environmental/calculate?from=scorecard',
    ctaLabel: 'See environment breakdown',
  },
  dietary_pattern: {
    title: 'Eating style',
    icon: Target,
    accent: 'neutral',
    meaningIndividual:
      'Which familiar eating style your day most closely resembles.',
    caveatIndividual:
      'Works best with a full day and several different foods.',
    ctaHref: '/dietary-pattern?from=scorecard',
    ctaLabel: 'See eating style breakdown',
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
  } else {
    const c = explanations?.score_summary?.mandatory_caveat
      || explanations?.recall_context?.message
      || inferredMsg
      || wafctMsg;
    if (c) return humanizeForUser(c);
  }

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
  } else {
    const m = explanations?.score_summary?.interpretation
      || explanations?.score_summary?.description
      || explanations?.score_summary?.message;
    if (m) return humanizeForUser(m);
  }
  return META[metric].meaningIndividual;
}

function errorCard(metric: MetricKey, reason: string): CardModel {
  const meta = META[metric];
  return {
    metric,
    title: meta.title,
    icon: meta.icon,
    headline: 'Could not score',
    meaning: meta.meaningIndividual,
    caveat: 'Other metrics may still be available below.',
    hint: reason,
    ctaHref: meta.ctaHref,
    ctaLabel: 'Try the full scorer',
    accent: 'neutral',
    status: 'error',
  };
}

function hintCard(metric: MetricKey, hint: string): CardModel {
  const meta = META[metric];
  return {
    metric,
    title: meta.title,
    icon: meta.icon,
    headline: '—',
    meaning: meta.meaningIndividual,
    caveat: meta.caveatIndividual,
    hint,
    ctaHref: meta.ctaHref,
    ctaLabel: meta.ctaLabel,
    accent: 'neutral',
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
    icon: meta.icon,
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
    icon: meta.icon,
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
      icon: meta.icon,
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
      icon: meta.icon,
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
    ? `From ${summary.min.toFixed(1)} to ${summary.max.toFixed(1)} stars. Best: ${trunc(high.food_name)}. Weakest: ${trunc(low.food_name)}.`
    : `Star ratings range from ${summary.min.toFixed(1)} to ${summary.max.toFixed(1)}.`;
  const dist = summary.distribution;
  const goodOrBetter = dist.excellent + dist.good;
  const multiMeaning = 'Each product is rated within its own category, then averaged across your list.';
  return {
    metric: 'hsr',
    title: meta.title,
    icon: meta.icon,
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
  // Food Compass is a single 1-100 scale: 70+ encourage, 31-69 moderate, 30 or below limit.
  // The same scale is used whether you score one food or a whole day's worth.
  const headline = fcs === null ? '—' : `${fcs.toFixed(0)} / 100`;
  let band: string | undefined;
  if (fcs !== null) {
    if (fcs >= 70) band = 'Encourage';
    else if (fcs >= 31) band = 'Moderate';
    else band = 'Limit';
  }
  const novaPretty = nova ? nova.replace(/_/g, ' ').toLowerCase() : undefined;
  const subline = [band, novaPretty].filter(Boolean).join(' · ') || undefined;
  return {
    metric: 'fcs',
    title: meta.title,
    icon: meta.icon,
    headline,
    subline,
    meaning: pickMeaning('fcs', userType, outcome.explanations),
    caveat: pickCaveat('fcs', userType, outcome.explanations),
    ctaHref: meta.ctaHref,
    ctaLabel: meta.ctaLabel,
    accent: meta.accent,
    status: fcs === null ? 'hint' : 'ok',
    hint: fcs === null
      ? 'Food Compass could not score this combination. Open the full breakdown for details.'
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

  // PLANETARY-1 (2026-05-27): prefer the EAT-Lancet 2.0 Table 2 share line as
  // the driver — it's more interpretable than raw CO₂e uncertainty for a
  // consumer audience. Falls back to the CO₂e band line when the backend
  // doesn't emit the planetary block (older deploys).
  const planetary = outcome.result?.data?.meal_analysis?.planetary_boundary_shares;
  let driver: string | undefined;
  if (planetary && planetary.n_covered > 0) {
    const byKey = new Map(planetary.shares.map(r => [r.key, r]));
    const climatePct = byKey.get('climate_change')?.share_of_daily_budget_pct;
    const landPct = byKey.get('land_use')?.share_of_daily_budget_pct;
    const waterPct = byKey.get('water_consumption')?.share_of_daily_budget_pct;
    const fmt = (p: number | null | undefined): string => {
      if (p === null || p === undefined || !Number.isFinite(p)) return '—';
      if (p >= 100) return `${p.toFixed(0)} %`;
      if (p >= 10) return `${p.toFixed(1)} %`;
      return `${p.toFixed(2)} %`;
    };
    driver = `Uses about ${fmt(climatePct)} of a daily climate budget, ${fmt(landPct)} for land, and ${fmt(waterPct)} for water.`;
  } else {
    const co2Band = bands['Global warming'];
    driver = co2Band && typeof co2Band.low === 'number' && typeof co2Band.high === 'number'
      ? `Climate impact estimate ranges from ${co2Band.low.toFixed(2)} to ${co2Band.high.toFixed(2)} kg CO₂e.`
      : undefined;
  }
  return {
    metric: 'environmental',
    title: meta.title,
    icon: meta.icon,
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
        `Add more foods for a reliable pattern match. You have ${nFoods}; we suggest at least 5.`),
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
    icon: meta.icon,
    headline,
    subline,
    meaning: userType === 'individual'
      ? (humanizeForUser(explanations?.plain_summary?.message) || pickMeaning('dietary_pattern', userType, outcome.explanations))
      : (explanations?.plain_summary?.message || pickMeaning('dietary_pattern', userType, outcome.explanations)),
    caveat: userType === 'individual'
      ? (humanizeForUser(explanations?.mandatory_caveat?.message) || pickCaveat('dietary_pattern', userType, outcome.explanations))
      : (explanations?.mandatory_caveat?.message || pickCaveat('dietary_pattern', userType, outcome.explanations)),
    ctaHref: meta.ctaHref,
    ctaLabel: meta.ctaLabel,
    accent: meta.accent,
    status: confidence === 'low' ? 'damped' : 'ok',
  };
}

/** Accent → Tailwind class lookup. Exported so MetricCard + MetricSkeleton
 *  share the same palette. */
export const ACCENT_CLASSES: Record<Accent, { chip: string; border: string; bar: string }> = {
  neutral: { chip: 'bg-slate-100 text-slate-700', border: 'border-slate-200', bar: 'bg-primary-500' },
};
