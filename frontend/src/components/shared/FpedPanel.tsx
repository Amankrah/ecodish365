'use client';

/**
 * FpedPanel — USDA Food Pattern (FPED) food-group exposure for a food list.
 *
 * Turns the active food list into cup/oz/tsp equivalents and gaps vs a reference
 * plate. Audience-aware: individuals get a plain-language grouped read; the
 * researcher/policy view gets the full component table with dual MyPlate + Canada's
 * Food Guide targets. Covers any food (CNF or WAFCT) that maps to a US food-pattern
 * analog; foods without a close analog are flagged in the coverage note.
 */
import { useCallback, useEffect, useState } from 'react';
import { Loader2, Utensils, AlertCircle, Info } from 'lucide-react';
import {
  FpedApiService,
  type FpedComponentAnalysis,
  type FpedGap,
  type FpedStatus,
} from '@/lib/api';
import type { UserType } from '@/components/shared/AudienceToggle';

interface FpedPanelProps {
  foods: Array<{ food_id: number; mass_g: number }>;
  userType: UserType;
  /** Energy (kcal) in the list — scales plate targets for partial-day / single-food samples. */
  estimatedKcal?: number;
  /** Optional one-line hint shown under the panel subtitle. */
  contextHint?: string;
}

const STATUS_STYLE: Record<FpedStatus, string> = {
  short: 'text-amber-700 bg-amber-50 border-amber-200',
  over: 'text-rose-700 bg-rose-50 border-rose-200',
  met: 'text-green-700 bg-green-50 border-green-200',
};

function StatusPill({ status }: { status: FpedStatus }) {
  return (
    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${STATUS_STYLE[status]}`}>
      {status}
    </span>
  );
}

function GapsTable({ gaps }: { gaps: FpedGap[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-gray-500 border-b">
            <th className="py-2 pr-3">Food group</th>
            <th className="py-2 pr-3 text-right">Intake</th>
            <th className="py-2 pr-3 text-right">MyPlate</th>
            <th className="py-2 pr-3 text-right">CFG</th>
          </tr>
        </thead>
        <tbody>
          {gaps.map((g) => (
            <tr key={g.component} className="border-b border-gray-100">
              <td className="py-1.5 pr-3 text-gray-800">{g.label}</td>
              <td className="py-1.5 pr-3 text-right tabular-nums">
                {g.intake.toFixed(2)} <span className="text-gray-400 text-xs">{g.unit}</span>
              </td>
              <td className="py-1.5 pr-3 text-right whitespace-nowrap">
                <span className="text-gray-500 tabular-nums mr-1">{g.myplate_target}</span>
                <StatusPill status={g.myplate_status} />
              </td>
              <td className="py-1.5 pr-3 text-right whitespace-nowrap">
                <span className="text-gray-500 tabular-nums mr-1">{g.cfg_target}</span>
                <StatusPill status={g.cfg_status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function FpedPanel({ foods, userType, estimatedKcal, contextHint }: FpedPanelProps): JSX.Element | null {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<FpedComponentAnalysis | null>(null);

  const run = useCallback(async () => {
    if (foods.length === 0) { setAnalysis(null); return; }
    setLoading(true);
    setError(null);
    try {
      const rsp = await FpedApiService.analyze(foods, userType, { estimatedKcal });
      setAnalysis(rsp.analysis);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not compute food-group exposure.');
    } finally {
      setLoading(false);
    }
  }, [foods, userType, estimatedKcal]);

  useEffect(() => { void run(); }, [run]);

  if (foods.length === 0) return null;

  return (
    <section className="bg-white rounded-2xl border border-gray-200 p-5">
      <div className="flex items-center gap-2 mb-3">
        <div className="bg-teal-100 p-2 rounded-lg">
          <Utensils className="h-4 w-4 text-teal-700" aria-hidden="true" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-gray-900">
            {analysis?.title ?? 'Food-group pattern'}
          </h3>
          <p className="text-xs text-gray-500">USDA Food Pattern equivalents vs a reference plate</p>
          {contextHint && (
            <p className="text-xs text-teal-700 mt-0.5">{contextHint}</p>
          )}
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-sm text-gray-500 py-3">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          Computing food-group exposure…
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
          {/* Individual / clinician: plain-language headline + grouped chips */}
          {analysis.headline && (
            <p className="text-sm text-gray-800 leading-relaxed">{analysis.headline}</p>
          )}
          {analysis.main_contributions && analysis.main_contributions.length > 0 && (
            <div className="mt-3">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Mainly contributes</span>
              <div className="flex flex-wrap gap-1.5 mt-1">
                {analysis.main_contributions.map((g) => (
                  <span key={g} className="text-xs px-2 py-0.5 rounded-full bg-teal-50 text-teal-900 border border-teal-200">{g}</span>
                ))}
              </div>
            </div>
          )}
          {analysis.eat_more && analysis.eat_more.length > 0 && (
            <div className="mt-3">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Aim for more</span>
              <div className="flex flex-wrap gap-1.5 mt-1">
                {analysis.eat_more.map((g) => (
                  <span key={g} className="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-800 border border-green-200">{g}</span>
                ))}
              </div>
            </div>
          )}
          {analysis.eat_less && analysis.eat_less.length > 0 && (
            <div className="mt-2">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Go easier on</span>
              <div className="flex flex-wrap gap-1.5 mt-1">
                {analysis.eat_less.map((g) => (
                  <span key={g} className="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-200">{g}</span>
                ))}
              </div>
            </div>
          )}

          {/* Researcher / policy: full table */}
          {analysis.gaps && <GapsTable gaps={analysis.gaps} />}

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
