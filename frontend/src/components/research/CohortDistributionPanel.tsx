/**
 * CohortDistributionPanel (PLATFORM-CODE-1.b, 2026-06-26).
 *
 * Renders one card per numeric lens with a histogram + a 5-number summary
 * (min / Q1 / median / Q3 / max) + a "% meeting target" badge when the
 * lens publishes a cap or floor. Dietary-pattern (categorical) gets its
 * own panel showing pattern shares.
 *
 * Why histograms instead of box plots: histograms expose multimodality
 * and skew that a box plot hides, and they read at a glance to non-stats
 * audiences. The 5-number summary is rendered alongside so a researcher
 * still sees the quartiles for a Mann-Whitney write-up.
 *
 * Audience-aware copy: in 'individual' mode we say "Your group's typical
 * day"; in 'researcher' we keep the units (kg CO₂e / 100 kcal); in
 * 'policy' we frame around target attainment.
 */
'use client';

import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { CohortLensDistribution, CohortResult } from '@/lib/api';

type Audience = 'individual' | 'researcher' | 'policy';

interface PanelProps {
  result: CohortResult;
  audience?: Audience;
}

interface SingleLensCardProps {
  title: string;
  dist: CohortLensDistribution;
  audience: Audience;
  targetCopy?: string;
}

// Lens display order + titles. Keeping env_sustainability and env_cost out of
// the default tile sweep (they're available but the headline panel is GW).
const LENS_TITLES: Array<[string, string, string?]> = [
  ['hefi',               'HEFI-2019 total score',          '60 or higher (Brassard 2022 “good”)'],
  ['heni',               'HENI minutes / day',              'Net positive minutes added'],
  ['hsr',                'Health Star Rating',              '3.5 ★ or higher'],
  ['fcs',                'Food Compass Score',              '70 or higher (Mozaffarian 2021 “encourage”)'],
  ['env_gw',             'Global warming, kg CO₂e / 100 kcal', '0.3 or lower'],
  ['env_sustainability', 'Environmental sustainability 0-100'],
  ['env_cost',           'Monetised env. cost, USD / 100 kcal'],
  ['fped_coverage',      'FPED unmatched mass (data quality)', '10 % or lower'],
];

function fmt(v: number | null | undefined, nd = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return Number(v).toFixed(nd);
}

function SingleLensCard({ title, dist, audience, targetCopy }: SingleLensCardProps) {
  const histData = dist.histogram.map((b, i) => ({
    bin: `${b.bin_min.toFixed(2)}–${b.bin_max.toFixed(2)}`,
    count: b.count,
    idx: i,
  }));

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-baseline justify-between gap-2 flex-wrap">
          <span>{title}</span>
          <span className="text-xs text-slate-500 font-normal">n = {dist.n}{dist.n_missing > 0 ? ` · ${dist.n_missing} missing` : ''}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {histData.length > 0 ? (
          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={histData} margin={{ top: 4, right: 8, left: -16, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="bin" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
                <Tooltip
                  formatter={(v: number) => [`${v} respondents`, 'Count']}
                  labelFormatter={(label: string) => `Range ${label}`}
                  contentStyle={{ fontSize: 12 }}
                />
                {dist.median !== null && (
                  <ReferenceLine
                    x={histData.find(d => d.bin.includes(dist.median!.toFixed(2)))?.bin}
                    stroke="#0f766e"
                    strokeDasharray="2 2"
                  />
                )}
                <Bar dataKey="count" fill="#0d9488" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="text-sm text-slate-500 italic">No data for this lens.</div>
        )}

        <div className="grid grid-cols-5 gap-2 text-xs text-slate-700">
          <div><div className="text-slate-500">Min</div><div className="font-medium">{fmt(dist.min)}</div></div>
          <div><div className="text-slate-500">Q1</div><div className="font-medium">{fmt(dist.q1)}</div></div>
          <div><div className="text-slate-500">Median</div><div className="font-semibold text-teal-700">{fmt(dist.median)}</div></div>
          <div><div className="text-slate-500">Q3</div><div className="font-medium">{fmt(dist.q3)}</div></div>
          <div><div className="text-slate-500">Max</div><div className="font-medium">{fmt(dist.max)}</div></div>
        </div>

        {audience !== 'individual' && (
          <div className="text-xs text-slate-500">
            Mean {fmt(dist.mean)} · SD {fmt(dist.sd)}
          </div>
        )}

        {dist.pct_meets_target !== null && (
          <div className="flex items-center justify-between border-t border-slate-100 pt-2">
            <span className="text-xs text-slate-600">
              {targetCopy ?? 'Meeting target'}
            </span>
            <Badge variant={dist.pct_meets_target >= 50 ? 'default' : 'secondary'}>
              {fmt(dist.pct_meets_target, 1)}%
            </Badge>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function DietaryPatternCard({ dist }: { dist: CohortLensDistribution }) {
  const counts = dist.pattern_counts ?? {};
  const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;
  const rows = Object.entries(counts)
    .sort(([, a], [, b]) => b - a)
    .map(([pattern, n]) => ({ pattern, n, pct: (100 * n) / total }));

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-baseline justify-between gap-2 flex-wrap">
          <span>Top dietary pattern across the cohort</span>
          <span className="text-xs text-slate-500 font-normal">n = {dist.n}{dist.n_missing > 0 ? ` · ${dist.n_missing} missing` : ''}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {rows.length === 0 ? (
            <div className="text-sm text-slate-500 italic">No classifications.</div>
          ) : (
            rows.map(({ pattern, n, pct }) => (
              <div key={pattern}>
                <div className="flex items-baseline justify-between text-sm">
                  <span className="font-medium text-slate-700">{pattern}</span>
                  <span className="text-slate-500">{n} · {pct.toFixed(1)}%</span>
                </div>
                <div className="h-1.5 bg-slate-100 rounded">
                  <div
                    className="h-1.5 bg-teal-600 rounded"
                    style={{ width: `${Math.min(100, pct)}%` }}
                  />
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function CohortDistributionPanel({ result, audience = 'researcher' }: PanelProps) {
  const dist = result.distribution_by_lens;
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {LENS_TITLES.map(([key, title, target]) => {
        const block = dist[key];
        if (!block) return null;
        return (
          <SingleLensCard
            key={key}
            title={title}
            dist={block}
            audience={audience}
            targetCopy={target}
          />
        );
      })}
      {dist.dietary_pattern && <DietaryPatternCard dist={dist.dietary_pattern} />}
    </div>
  );
}
