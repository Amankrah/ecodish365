'use client';

import React from 'react';
import type { GroupSummary } from '@/lib/api';
import { prepStateLabel } from '@/lib/cnfGroupDisplay';

interface GroupSummaryCardProps {
  summary: GroupSummary;
  totalInCatalog: number;
  filteredCount: number;
}

function BarRow({ label, count, total }: { label: string; count: number; total: number }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-24 shrink-0 text-gray-600 truncate" title={label}>{label}</span>
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className="h-full bg-primary-500 rounded-full" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-10 text-right text-gray-500 tabular-nums">{count}</span>
    </div>
  );
}

export function GroupSummaryCard({ summary, totalInCatalog, filteredCount }: GroupSummaryCardProps) {
  const ftTotal = summary.food_type.single + summary.food_type.mixed + summary.food_type.unknown;
  const topThermal = Object.entries(summary.thermal_state).slice(0, 5);
  const topPreservation = Object.entries(summary.preservation_state).slice(0, 5);

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 mb-4">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">Group overview</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            {totalInCatalog.toLocaleString()} foods in catalogue
            {filteredCount !== totalInCatalog && (
              <> · {filteredCount.toLocaleString()} match current filters</>
            )}
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-[11px]">
          <span className="px-2 py-0.5 rounded-full bg-white border border-gray-200 text-gray-700">
            CNF {summary.cnf_count}
          </span>
          {summary.wafct_count > 0 && (
            <span className="px-2 py-0.5 rounded-full bg-amber-50 border border-amber-200 text-amber-800">
              WAFCT {summary.wafct_count}
            </span>
          )}
          <span className="px-2 py-0.5 rounded-full bg-white border border-gray-200 text-gray-700">
            Prep tagged {summary.prep_both_known_pct}%
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-500 mb-2">Food type</p>
          <div className="space-y-1.5">
            <BarRow label="Single" count={summary.food_type.single} total={ftTotal} />
            <BarRow label="Mixed" count={summary.food_type.mixed} total={ftTotal} />
            <BarRow label="Unknown" count={summary.food_type.unknown} total={ftTotal} />
          </div>
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-500 mb-2">Thermal state</p>
          <div className="space-y-1.5">
            {topThermal.length === 0 ? (
              <p className="text-xs text-gray-400">No labels</p>
            ) : topThermal.map(([k, v]) => (
              <BarRow key={k} label={prepStateLabel(k)} count={v} total={summary.total_in_group} />
            ))}
          </div>
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-500 mb-2">Preservation</p>
          <div className="space-y-1.5">
            {topPreservation.length === 0 ? (
              <p className="text-xs text-gray-400">No labels</p>
            ) : topPreservation.map(([k, v]) => (
              <BarRow key={k} label={prepStateLabel(k)} count={v} total={summary.total_in_group} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
