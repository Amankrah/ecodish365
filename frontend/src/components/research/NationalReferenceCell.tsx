/**
 * NationalReferenceCell (PLATFORM-CODE-1.m m.D.5, 2026-06-26).
 *
 * Renders an inline national-reference summary for one food row on the
 * `/research/nutrient-analysis` page. Given the food's bridged BNS
 * subgroup + the published Canadian national distribution (median /
 * P90 / P95 / mean + SE) for the user's selected stratum, shows:
 *
 *   - Where the user's serving sits vs the national distribution
 *     (✓ within IQR, ↑ above P90, ↓ below median × 0.5).
 *   - The BNS subgroup name + code on hover.
 *   - The full distribution + bridge confidence + Health Canada suppression
 *     flag explanation on hover.
 *
 * Renders nothing (returns null) when the food is unbridged or the
 * national cell is unavailable for the stratum — never crowds the row
 * when the data isn't there.
 *
 * Lookups are batched at the parent (page) level via
 * `PopulationReferenceApiService.forFoods`; this component just renders
 * the result row passed in.
 */
'use client';

import React from 'react';

import type { NationalReferenceRow } from '@/lib/api';

interface Props {
  foodId: number;
  massG: number;
  /** The bridged row from the batched `for-foods` lookup, or null. */
  reference: NationalReferenceRow | null | undefined;
  /** Whether this serving is the entire day (single-meal mode) or part
   * of a multi-meal day — affects how we frame the comparison copy. */
  perDay?: boolean;
}

function fmt(v: number | null | undefined, nd = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return Number(v).toFixed(nd);
}

function compareToken(massG: number, ref: NationalReferenceRow): { glyph: string; tone: string; label: string } {
  const median = ref.national_median ?? 0;
  const p90 = ref.national_p90 ?? Infinity;
  if (mass_above_p90(massG, p90)) {
    return { glyph: '▲', tone: 'text-amber-700', label: 'above national P90' };
  }
  if (median > 0 && massG < median * 0.5) {
    return { glyph: '▽', tone: 'text-slate-500', label: 'below national median × 0.5' };
  }
  return { glyph: '≈', tone: 'text-teal-700', label: 'within national typical range' };
}

function mass_above_p90(massG: number, p90: number): boolean {
  return Number.isFinite(p90) && massG > p90;
}

export default function NationalReferenceCell({ foodId, massG, reference }: Props) {
  // Empty cell when nothing to show — preserves the row layout for foods
  // that legitimately have no national reference (raw ingredients, etc.).
  if (!reference) {
    return <span className="text-xs text-slate-300" title={`No Canadian national reference available for FoodID ${foodId} (food unbridged or cell suppressed by Health Canada).`}>—</span>;
  }
  const cmp = compareToken(massG, reference);
  const suppressedE = reference.suppression_flag === 'E';

  const tooltipLines: string[] = [
    `${reference.bns_code} ${reference.bns_name ?? ''} (${reference.main_group ?? 'group n/a'})`,
    '',
    `Canadian national distribution (eaters-only, per person / day):`,
    `  median ${fmt(reference.national_median)} g  (SE ${fmt(reference.se_p50, 2)})`,
    `  P90    ${fmt(reference.national_p90)} g  (SE ${fmt(reference.se_p90, 2)})`,
    `  P95    ${fmt(reference.national_p95)} g`,
    `  mean   ${fmt(reference.national_mean)} g`,
    `  n eaters ≈ ${reference.n_respondents ?? '?'}, % eaters ${fmt(reference.pct_eaters)}%`,
    '',
    `Your serving ${massG} g is ${cmp.label}.`,
    '',
    `Bridge: ${reference.bridge_source} (confidence ${fmt(reference.bridge_confidence, 2)})`,
    suppressedE ? 'CCHS-FCT flagged this cell with caution (CV 16.6–33.3%).' : '',
  ].filter(Boolean);

  return (
    <span
      className="inline-flex items-baseline gap-1.5 text-xs whitespace-nowrap"
      title={tooltipLines.join('\n')}
    >
      <span className={`font-mono ${cmp.tone}`}>{cmp.glyph}</span>
      <span className={`tabular-nums ${suppressedE ? 'text-amber-700' : 'text-slate-600'}`}>
        nat&apos;l {fmt(reference.national_median)}g
      </span>
      {suppressedE && (
        <span className="text-[10px] uppercase tracking-wide bg-amber-100 text-amber-800 px-1 rounded" title="CCHS-FCT 2015 caution flag (E): coefficient of variation 16.6–33.3%.">E</span>
      )}
    </span>
  );
}
