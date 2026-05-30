/**
 * SubstitutionScorecardDelta — SUBST-1 Phase 3 six-metric delta strip.
 */
'use client';

import { TrendingDown, TrendingUp } from 'lucide-react';
import type { SubstitutionScorecardDeltaMap } from '@/lib/api';
import { friendlyMetricLabel } from '@/lib/humanizeCopy';

const METRIC_LABELS: Record<string, string> = {
  hefi: 'Healthy eating',
  heni: 'Health impact',
  hsr: 'Product rating',
  fcs: 'Diet quality',
  environmental: 'Environment',
  dietary_pattern: 'Eating style',
};

interface Props {
  deltas: SubstitutionScorecardDeltaMap;
  compact?: boolean;
}

function DeltaChip({
  metric,
  delta,
  compact,
}: {
  metric: string;
  delta: SubstitutionScorecardDeltaMap[string];
  compact?: boolean;
}): JSX.Element | null {
  if (delta.delta == null) return null;
  const improved = delta.improved;
  const neutral = improved == null;
  const Icon = improved ? TrendingUp : TrendingDown;
  const color = neutral
    ? 'text-gray-600 bg-gray-100'
    : improved
      ? 'text-emerald-800 bg-emerald-100'
      : 'text-red-800 bg-red-100';

  const unit = metric === 'hsr' ? '★' : metric === 'heni' ? ' min' : '';
  const sign = delta.delta >= 0 ? '+' : '';

  return (
    <span
      className={`inline-flex items-center gap-0.5 rounded ${compact ? 'text-[10px] px-1 py-0.5' : 'text-xs px-1.5 py-0.5'} ${color}`}
      title={`${friendlyMetricLabel(metric)}: ${delta.before ?? 'n/a'} to ${delta.after ?? 'n/a'}`}
    >
      {!neutral && <Icon className="h-3 w-3" aria-hidden="true" />}
      <span className="font-medium">{friendlyMetricLabel(metric)}</span>
      {sign}{delta.delta.toFixed(metric === 'hsr' ? 2 : 1)}{unit}
    </span>
  );
}

export function SubstitutionScorecardDelta({ deltas, compact = false }: Props): JSX.Element | null {
  const keys = Object.keys(METRIC_LABELS).filter(k => deltas[k]?.delta != null);
  if (keys.length === 0) return null;

  return (
    <div className={`flex flex-wrap gap-1 ${compact ? 'mt-2' : 'mt-3'}`}>
      {keys.map(k => (
        <DeltaChip key={k} metric={k} delta={deltas[k]} compact={compact} />
      ))}
    </div>
  );
}
