'use client';

/**
 * FpedCohortPanel — food-group exposure distribution across N recalls (days).
 *
 * Sends each saved day as one recall to /api/fped/cohort/ and renders the population
 * read: per food group the median + IQR of intake and the % of days meeting the
 * MyPlate / CFG target. Audience-aware — individuals get a plain-language adherence
 * read; researchers/policy get the full distribution table.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Loader2, Users, AlertCircle, Info } from 'lucide-react';
import {
  FpedApiService,
  type FpedCohortResponse,
  type FpedCohortComponent,
} from '@/lib/api';
import type { UserType } from '@/components/shared/AudienceToggle';

interface FpedCohortPanelProps {
  recalls: Array<Array<{ food_id: number; mass_g: number }>>;
  userType: UserType;
}

function pctColor(pct: number): string {
  if (pct >= 67) return 'text-green-700';
  if (pct >= 34) return 'text-amber-700';
  return 'text-rose-700';
}

function DistributionTable({ components }: { components: FpedCohortComponent[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-gray-500 border-b">
            <th className="py-2 pr-3">Food group</th>
            <th className="py-2 pr-3 text-right">Median [IQR]</th>
            <th className="py-2 pr-3 text-right">MyPlate</th>
            <th className="py-2 pr-3 text-right">% met</th>
            <th className="py-2 pr-3 text-right">CFG</th>
            <th className="py-2 pr-3 text-right">% met</th>
          </tr>
        </thead>
        <tbody>
          {components.map((c) => (
            <tr key={c.component} className="border-b border-gray-100">
              <td className="py-1.5 pr-3 text-gray-800">{c.label}</td>
              <td className="py-1.5 pr-3 text-right tabular-nums">
                {c.median.toFixed(2)}{' '}
                <span className="text-gray-400 text-xs">[{c.q1.toFixed(2)}–{c.q3.toFixed(2)}] {c.unit}</span>
              </td>
              <td className="py-1.5 pr-3 text-right tabular-nums text-gray-500">{c.myplate_target}</td>
              <td className={`py-1.5 pr-3 text-right tabular-nums font-medium ${pctColor(c.pct_meeting_myplate)}`}>
                {c.pct_meeting_myplate.toFixed(0)}%
              </td>
              <td className="py-1.5 pr-3 text-right tabular-nums text-gray-500">{c.cfg_target}</td>
              <td className={`py-1.5 pr-3 text-right tabular-nums font-medium ${pctColor(c.pct_meeting_cfg)}`}>
                {c.pct_meeting_cfg.toFixed(0)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function FpedCohortPanel({ recalls, userType }: FpedCohortPanelProps): JSX.Element | null {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<FpedCohortResponse | null>(null);

  // Stable key so we only refetch when the recall set or audience actually changes.
  const recallsKey = useMemo(
    () => `${userType}|${recalls.map(r => r.map(f => `${f.food_id}:${Math.round(f.mass_g)}`).join(',')).join(';')}`,
    [recalls, userType],
  );

  const run = useCallback(async () => {
    const valid = recalls.filter(r => r.length > 0);
    if (valid.length === 0) { setData(null); return; }
    setLoading(true);
    setError(null);
    try {
      setData(await FpedApiService.cohort(valid, userType));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not compute cohort food-group exposure.');
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recallsKey]);

  useEffect(() => { void run(); }, [run]);

  if (recalls.filter(r => r.length > 0).length === 0) return null;

  const analysis = data?.analysis;
  const components = data?.result.components ?? [];
  const showTable = userType !== 'individual';

  return (
    <section className="bg-white rounded-2xl border border-gray-200 p-5">
      <div className="flex items-center gap-2 mb-3">
        <div className="bg-teal-100 p-2 rounded-lg">
          <Users className="h-4 w-4 text-teal-700" aria-hidden="true" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-gray-900">
            {analysis?.title ?? 'Food groups across your days'}
          </h3>
          <p className="text-xs text-gray-500">
            Distribution + target adherence across {data?.result.n_recalls ?? recalls.length} saved days
          </p>
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-sm text-gray-500 py-3">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          Computing food-group exposure across days…
        </div>
      )}

      {error && (
        <div role="alert" className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-900">
          <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {!loading && !error && analysis && (
        <>
          {analysis.headline && (
            <p className="text-sm text-gray-800 leading-relaxed">{analysis.headline}</p>
          )}

          {/* Individual: per-group adherence bars */}
          {!showTable && analysis.adherence && analysis.adherence.length > 0 && (
            <ul className="mt-3 space-y-1.5">
              {analysis.adherence.map((a) => (
                <li key={a.label} className="flex items-center gap-2 text-sm">
                  <span className="w-28 text-gray-700 capitalize shrink-0">{a.label}</span>
                  <span className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <span
                      className={`block h-full rounded-full ${a.pct_meeting >= 67 ? 'bg-green-400' : a.pct_meeting >= 34 ? 'bg-amber-400' : 'bg-rose-400'}`}
                      style={{ width: `${Math.max(2, a.pct_meeting)}%` }}
                    />
                  </span>
                  <span className={`w-32 text-right text-xs tabular-nums ${pctColor(a.pct_meeting)}`}>
                    {a.goal === 'less' ? 'within limit' : 'met'} {a.pct_meeting.toFixed(0)}% of days
                  </span>
                </li>
              ))}
            </ul>
          )}

          {/* Researcher / policy: full distribution table */}
          {showTable && components.length > 0 && <DistributionTable components={components} />}

          {analysis.coverage_note && (
            <div className="mt-3 flex items-start gap-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-md p-2">
              <Info className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" aria-hidden="true" />
              <span>{analysis.coverage_note}</span>
            </div>
          )}

          <p className="mt-3 text-xs text-gray-400 leading-relaxed">
            {analysis.caveat ?? analysis.methodology}
          </p>
        </>
      )}
    </section>
  );
}
