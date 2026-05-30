'use client';

import Link from 'next/link';
import { TrendingUp, TrendingDown, Minus, Users } from 'lucide-react';
import type { CardModel } from './metricAdapters';
import type { MetricKey } from '@/lib/foodProfileOrchestrator';
import type { ProfileScoreMeta } from '@/lib/api';

const METRIC_ORDER: MetricKey[] = [
  'hefi', 'heni', 'hsr', 'fcs', 'environmental', 'dietary_pattern',
];

interface ScorecardSummaryDashboardProps {
  cards: Record<MetricKey, CardModel> | null;
  meta: ProfileScoreMeta | null;
  nFoods: number;
  totalMassG: number;
  dailyKcal?: number;
  onScaleToDay?: () => void;
}

export function ScorecardSummaryDashboard({
  cards,
  meta,
  nFoods,
  totalMassG,
  dailyKcal,
  onScaleToDay,
}: ScorecardSummaryDashboardProps) {
  if (!cards) return null;

  const kcal = dailyKcal ?? meta?.estimated_kcal;
  const drivers = meta?.drivers ?? [];

  const okCount = METRIC_ORDER.filter(k => cards[k].status === 'ok').length;
  const hintCount = METRIC_ORDER.filter(k => cards[k].status === 'hint' || cards[k].status === 'damped').length;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-gray-900">Profile overview</h2>
          <p className="text-xs text-gray-600 mt-0.5">
            {nFoods} food{nFoods === 1 ? '' : 's'} · {totalMassG.toFixed(0)} g
            {kcal != null && kcal > 0 && ` · ~${kcal.toFixed(0)} kcal`}
            {' · '}{okCount}/6 metrics scored
            {hintCount > 0 && ` · ${hintCount} with caveats`}
          </p>
        </div>
        {kcal != null && kcal > 0 && kcal < 1500 && onScaleToDay && (
          <button
            type="button"
            onClick={onScaleToDay}
            className="text-xs font-medium text-blue-700 hover:text-blue-900 border border-blue-200 rounded-md px-2 py-1 bg-blue-50"
          >
            Scale portions to ~2000 kcal preview
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        {METRIC_ORDER.map(key => {
          const card = cards[key];
          const adequate = meta?.sample_adequacy?.[key]?.adequate ?? true;
          const icon = card.status === 'ok'
            ? (adequate ? <TrendingUp className="h-3 w-3 text-emerald-600" /> : <Minus className="h-3 w-3 text-amber-600" />)
            : card.status === 'error'
              ? <TrendingDown className="h-3 w-3 text-red-500" />
              : <Minus className="h-3 w-3 text-gray-400" />;
          return (
            <div
              key={key}
              className={`rounded-md border px-2 py-1.5 text-xs ${
                card.status === 'error' ? 'border-red-200 bg-red-50/50' : 'border-gray-200 bg-gray-50/80'
              }`}
            >
              <div className="flex items-center gap-1 font-medium text-gray-800">
                <span aria-hidden="true">{card.emoji}</span>
                {icon}
              </div>
              <p className="text-[11px] text-gray-600 truncate mt-0.5" title={card.headline}>
                {card.headline}
              </p>
            </div>
          );
        })}
      </div>

      {drivers.length > 0 && (
        <div className="text-xs text-gray-600 border-t pt-2">
          <span className="font-medium text-gray-800 inline-flex items-center gap-1">
            <Users className="h-3.5 w-3.5" aria-hidden="true" />
            Main contributors by mass:
          </span>
          {' '}
          {drivers.map((d, i) => (
            <span key={d.food_id}>
              {i > 0 && ', '}
              <Link href={`/cnf/foods/${d.food_id}`} className="text-blue-700 hover:underline">
                {d.food_description}
              </Link>
              {' '}({d.mass_share_pct}%)
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
