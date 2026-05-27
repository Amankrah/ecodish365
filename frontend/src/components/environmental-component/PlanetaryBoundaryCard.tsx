/**
 * PlanetaryBoundaryCard — renders the EAT-Lancet 2.0 Table 2 food-system
 * boundary shares for one meal/day.
 *
 * Source of truth: `backend/environmental_impact_model/src/planetary_boundaries.py`
 * (PLANETARY-1, 2026-05-27). Citation: Rockström, Thilsted, Willett et al.
 * (2025). EAT-Lancet 2.0. Lancet 406:1625-1700, Table 2 p. 1640.
 */
'use client';

import { useState } from 'react';
import {
  Leaf, Info, ChevronDown, ChevronUp, AlertTriangle,
} from 'lucide-react';
import type {
  PlanetaryBoundaryShares,
  PlanetaryBoundaryExplanations,
  PlanetaryBoundaryShareRow,
} from '@/lib/api';

interface Props {
  shares: PlanetaryBoundaryShares;
  explanations?: PlanetaryBoundaryExplanations;
  /** When true the methodology + uncovered-row section starts collapsed.
   *  Useful on dense result pages. */
  startCollapsed?: boolean;
}

/** Colour the share row by how far past the per-capita-per-day budget the
 *  meal sits. Mirrors the universal traffic-light convention. */
function shareColour(pct: number | null | undefined): {
  bar: string; chip: string; label: string;
} {
  if (pct === null || pct === undefined || !Number.isFinite(pct)) {
    return { bar: 'bg-gray-200', chip: 'bg-gray-100 text-gray-700', label: 'no data' };
  }
  if (pct <= 100) {
    return { bar: 'bg-emerald-500', chip: 'bg-emerald-100 text-emerald-800', label: 'within budget' };
  }
  if (pct <= 200) {
    return { bar: 'bg-amber-500', chip: 'bg-amber-100 text-amber-900', label: 'over budget' };
  }
  return { bar: 'bg-red-500', chip: 'bg-red-100 text-red-900', label: 'well over budget' };
}

function formatShare(pct: number | null | undefined): string {
  if (pct === null || pct === undefined || !Number.isFinite(pct)) return '—';
  if (pct >= 100) return `${pct.toFixed(0)}%`;
  if (pct >= 10) return `${pct.toFixed(1)}%`;
  return `${pct.toFixed(2)}%`;
}

function formatNumber(value: number | null | undefined, unit: string): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—';
  // Adapt precision to the magnitude so big and small numbers both read cleanly.
  const abs = Math.abs(value);
  let fixed: string;
  if (abs >= 100) fixed = value.toFixed(0);
  else if (abs >= 10) fixed = value.toFixed(1);
  else if (abs >= 1) fixed = value.toFixed(2);
  else fixed = value.toFixed(3);
  return `${fixed} ${unit}`;
}

function AvailableRow({ row }: { row: PlanetaryBoundaryShareRow }): JSX.Element {
  const pct = row.share_of_daily_budget_pct ?? null;
  const colour = shareColour(pct);
  // Cap visual bar at 250 % so a 700 % beef-heavy day still shows a finite bar.
  const barFill = Math.min(250, Math.max(0, pct ?? 0)) / 250 * 100;
  return (
    <li className="bg-white border border-gray-200 rounded-lg p-3">
      <div className="flex items-baseline justify-between gap-2 mb-1">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-900">{row.label}</p>
          <p className="text-[11px] text-gray-500 truncate">{row.control_variable}</p>
        </div>
        <div className="text-right">
          <p className="text-lg font-bold leading-tight text-gray-900">{formatShare(pct)}</p>
          <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${colour.chip}`}>
            {colour.label}
          </span>
        </div>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden mb-1.5">
        <div
          className={`h-full ${colour.bar} transition-all`}
          style={{ width: `${barFill}%` }}
          aria-label={`Bar showing ${formatShare(pct)} of daily budget (visual cap at 250%)`}
        />
      </div>
      <div className="flex items-center justify-between text-[11px] text-gray-600">
        <span>This meal: <strong>{formatNumber(row.meal_value ?? null, row.unit)}</strong></span>
        <span className="text-gray-500">
          Daily budget: {formatNumber(row.per_capita_daily_budget ?? null, row.unit)}/person
        </span>
      </div>
      {row.reason && (
        <p className="text-[11px] text-amber-700 mt-1">{row.reason}</p>
      )}
    </li>
  );
}

function UnavailableRow({ row }: { row: PlanetaryBoundaryShareRow }): JSX.Element {
  return (
    <li className="bg-gray-50 border border-dashed border-gray-300 rounded-lg p-3">
      <div className="flex items-start gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-700">{row.label}</p>
          <p className="text-[11px] text-gray-500 mt-0.5">
            EAT-Lancet 2.0 boundary: <strong>{row.global_boundary_source}</strong>
          </p>
          <p className="text-[11px] text-gray-600 mt-1 italic">{row.reason}</p>
        </div>
        <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-gray-200 text-gray-600 flex-shrink-0">
          v2 follow-up
        </span>
      </div>
    </li>
  );
}

export function PlanetaryBoundaryCard({
  shares, explanations, startCollapsed = false,
}: Props): JSX.Element {
  const [showMethodology, setShowMethodology] = useState(!startCollapsed);

  const covered = shares.shares.filter(r => r.available);
  const uncovered = shares.shares.filter(r => !r.available);

  return (
    <div className="bg-white border border-emerald-200 rounded-2xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-50 to-blue-50 px-5 py-4 border-b border-emerald-100">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-blue-500 flex items-center justify-center flex-shrink-0">
            <Leaf className="h-5 w-5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-bold text-gray-900">
              Planetary food-system boundary share
            </h3>
            <p className="text-xs text-gray-600 mt-0.5">
              EAT-Lancet 2.0 Table 2 · {shares.n_covered} of {shares.n_total} boundaries scored in v1
            </p>
          </div>
        </div>
        {explanations?.headline && (
          <p className="text-sm text-gray-800 mt-3 font-medium">
            {explanations.headline}
          </p>
        )}
        {explanations?.message && (
          <p className="text-xs text-gray-600 mt-2 leading-snug">{explanations.message}</p>
        )}
      </div>

      {/* Covered rows */}
      <div className="p-5">
        <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wide mb-2">
          Scored in v1 ({covered.length})
        </p>
        <ul className="space-y-2">
          {covered.map(row => <AvailableRow key={row.key} row={row} />)}
        </ul>

        {/* Caveat */}
        {explanations?.mandatory_caveat && (
          <div className="mt-4 flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-md p-3">
            <AlertTriangle className="h-4 w-4 text-amber-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <p className="text-[11px] text-amber-900 leading-snug">
              {explanations.mandatory_caveat}
            </p>
          </div>
        )}

        {/* Uncovered rows + methodology disclosure */}
        <button
          type="button"
          onClick={() => setShowMethodology(v => !v)}
          aria-expanded={showMethodology ? 'true' : 'false'}
          className="w-full flex items-center justify-between mt-4 px-3 py-2 bg-gray-50 hover:bg-gray-100 rounded-md text-xs font-medium text-gray-700"
        >
          <span className="flex items-center gap-1.5">
            <Info className="h-3.5 w-3.5" aria-hidden="true" />
            Show the 6 boundaries we don&apos;t yet score + methodology
          </span>
          {showMethodology
            ? <ChevronUp className="h-3.5 w-3.5" aria-hidden="true" />
            : <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />}
        </button>

        {showMethodology && (
          <div className="mt-3 space-y-3">
            <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wide">
              Not scored in v1 ({uncovered.length})
            </p>
            <ul className="space-y-2">
              {uncovered.map(row => <UnavailableRow key={row.key} row={row} />)}
            </ul>

            <div className="text-[11px] text-gray-600 bg-gray-50 border border-gray-200 rounded-md p-3 leading-relaxed">
              <p className="font-semibold text-gray-800 mb-1">Method</p>
              <p>{shares.method_note}</p>
              <p className="mt-2">
                Per-capita-per-day = global food-system boundary ÷ world population
                ({shares.population_assumption.toLocaleString()}) ÷ {shares.days_per_year} days.
              </p>
            </div>

            <div className="text-[11px] text-gray-600 bg-blue-50 border border-blue-200 rounded-md p-3 leading-relaxed">
              <p className="font-semibold text-blue-900 mb-1">Citation</p>
              <p>{shares.citation.citation}</p>
              <p className="mt-1 text-blue-800">
                <span className="font-medium">Table:</span> {shares.citation.table}
                <span className="mx-1">·</span>
                <span className="font-medium">DOI:</span> {shares.citation.doi}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
